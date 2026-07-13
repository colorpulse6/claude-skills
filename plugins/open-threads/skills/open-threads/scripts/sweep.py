#!/usr/bin/env python3
"""Sweep local git repos for forgotten work. Emits JSON; judgment stays in the skill.

Facts collected per repo: dirty file count, stash count, days since last commit,
last commit subject, current branch, wip/* branches, branches never pushed
(no upstream), unpushed commit count (ahead of upstream), and whether the repo
is local-only (zero remotes — deliberate for some repos, e.g. a private KB).

Usage:
    sweep.py [--roots DIR ...] [--max-depth N]

Defaults match this machine's layout (~/Desktop/projects, ~/Desktop, ~) but are
flags so the skill works anywhere.
"""
import argparse
import json
import os
import subprocess
import sys
import time

# Directories that never contain the user's own repos; descending into them is
# pure waste (package caches, app state, trash).
SKIP_DIRS = {
    "node_modules", "Library", "Applications", "Music", "Movies", "Pictures",
    ".Trash", ".cache", ".npm", ".nvm", ".cargo", ".rustup", "vendor",
    "dist", "build", ".venv", "venv", "__pycache__",
}

# 14 days without a commit = stale. Mirrors STALE_PROJECT_DAYS in the user's
# own KB config (~/kb/CLAUDE.md) so both systems age projects identically.
STALE_DAYS = 14


def run_git(repo, *args):
    """Run a git command; return stdout or None on failure (never raise)."""
    try:
        out = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True, text=True, timeout=15,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except (subprocess.TimeoutExpired, OSError):
        return None


def find_repos(roots, max_depth):
    """Find directories containing .git under roots, up to max_depth levels."""
    repos = []
    seen = set()
    for root in roots:
        root = os.path.expanduser(root)
        if not os.path.isdir(root):
            continue
        base_depth = root.rstrip("/").count("/")
        for dirpath, dirnames, _ in os.walk(root):
            depth = dirpath.rstrip("/").count("/") - base_depth
            # Prune noise and hidden dirs (except .git itself, checked below).
            dirnames[:] = [
                d for d in dirnames
                if d not in SKIP_DIRS and not (d.startswith(".") and d != ".git")
            ]
            if ".git" in dirnames or os.path.isdir(os.path.join(dirpath, ".git")):
                real = os.path.realpath(dirpath)
                if real not in seen:
                    seen.add(real)
                    repos.append(dirpath)
                dirnames[:] = []  # don't descend into a repo (skips submodules/worktrees noise)
                continue
            if depth >= max_depth:
                dirnames[:] = []
    return repos


def inspect(repo):
    """Collect the fact sheet for one repo."""
    status = run_git(repo, "status", "--porcelain")
    if status is None:  # not actually a usable repo (bare, corrupt, permission)
        return None
    dirty = len([l for l in status.splitlines() if l.strip()])

    last_commit = run_git(repo, "log", "-1", "--format=%ct|%cs|%s")
    if last_commit and "|" in last_commit:
        epoch, date, subject = last_commit.split("|", 2)
        days_since = int((time.time() - int(epoch)) / 86400)
    else:
        date, subject, days_since = None, None, None  # empty repo, no commits

    remotes = run_git(repo, "remote") or ""
    local_only = remotes.strip() == ""

    branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    stashes = run_git(repo, "stash", "list") or ""
    stash_count = len(stashes.splitlines())

    wip_branches, never_pushed, unpushed = [], [], 0
    fmt = "%(refname:short)|%(upstream:short)|%(upstream:track)"
    for line in (run_git(repo, "for-each-ref", "refs/heads", f"--format={fmt}") or "").splitlines():
        name, upstream, track = (line.split("|") + ["", ""])[:3]
        if name.startswith("wip/"):
            wip_branches.append(name)
        if not local_only and not upstream:
            never_pushed.append(name)
        if "ahead" in track:
            try:
                unpushed += int(track.split("ahead ")[1].split(",")[0].rstrip("]"))
            except (IndexError, ValueError):
                pass

    return {
        "path": repo.replace(os.path.expanduser("~"), "~", 1),
        "branch": branch,
        "dirty_files": dirty,
        "unpushed_commits": unpushed,
        # Lists are capped at 5 so one branch-hoarding repo can't flood the
        # report; the count fields carry the true totals.
        "never_pushed_count": len(never_pushed),
        "never_pushed_branches": never_pushed[:5],
        "wip_count": len(wip_branches),
        "wip_branches": wip_branches[:5],
        "stashes": stash_count,
        "last_commit_date": date,
        "last_commit_subject": subject,
        "days_since_commit": days_since,
        "stale": days_since is not None and days_since >= STALE_DAYS,
        "local_only": local_only,
        "has_forgotten_work": bool(
            dirty or unpushed or never_pushed or stash_count
            or (days_since is None)  # repo with zero commits ever
        ),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--roots", nargs="+",
                    default=["~/Desktop/projects", "~/Desktop", "~"])
    ap.add_argument("--max-depth", type=int, default=2,
                    help="levels below each root to search (2 covers root/org/repo)")
    args = ap.parse_args()

    repos = find_repos(args.roots, args.max_depth)
    results = [r for r in (inspect(p) for p in sorted(repos)) if r]
    # Repos carrying forgotten work first, most dirt first — the skill reads top-down.
    # Never-pushed branches contribute capped weight: 3+ of them signals the
    # same thing as 30 (an unpublished repo), and ancient branch-hoarding repos
    # shouldn't drown fresh dirt.
    results.sort(key=lambda r: (
        not r["has_forgotten_work"],
        -(r["dirty_files"] + r["unpushed_commits"] + 10 * min(r["never_pushed_count"], 3)),
    ))
    json.dump({
        "scanned_roots": args.roots,
        "repo_count": len(results),
        "stale_days_threshold": STALE_DAYS,
        "repos": results,
    }, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
