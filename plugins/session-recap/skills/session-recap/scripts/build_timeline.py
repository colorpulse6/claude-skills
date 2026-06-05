#!/usr/bin/env python3
"""Parse Claude Code session transcripts into structured timeline data.

Pure extraction — no LLM, fast and free. Walks ~/.claude/projects/*/*.jsonl
(top-level session files only; subagent transcripts in subagents/ are ignored),
keeps sessions touched within the last N days, and emits sessions.json.

Usage:
  build_timeline.py --days 7 --out ~/.claude/recaps
"""
import argparse, glob, json, os, re
from datetime import datetime, timedelta, timezone

PROJECTS_DIR = os.path.expanduser("~/.claude/projects")

PR_URL_RE = re.compile(r"https?://github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)")
PR_CREATE_RE = re.compile(r"\bgh\s+pr\s+create\b")
COMMIT_RE = re.compile(r"\bgit\s+commit\b")
IDLE_CAP = 30 * 60  # gaps longer than this don't count as active time


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def clean_prompt(text):
    if not text:
        return ""
    text = re.sub(r"<command-[^>]*>.*?</command-[^>]*>", "", text, flags=re.S)
    text = re.sub(r"<command-[^>]*/?>", "", text)
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    text = re.sub(r"<bash-[^>]*>.*?</bash-[^>]*>", "", text, flags=re.S)
    text = re.sub(r"<local-command[^>]*>.*?</local-command[^>]*>", "", text, flags=re.S)
    return text.strip()


def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def is_real_user_prompt(o):
    if o.get("type") != "user" or o.get("isMeta") or o.get("isSidechain"):
        return None
    msg = o.get("message")
    if not isinstance(msg, dict):
        return None
    content = msg.get("content")
    if isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None
        text = extract_text(content)
    else:
        text = content if isinstance(content, str) else ""
    cleaned = clean_prompt(text)
    if not cleaned or cleaned.startswith("/"):
        return None
    return cleaned


def parse_session(path):
    title = first_prompt = cwd = branch = None
    prompt_count = assistant_count = commits = 0
    ts_first = ts_last = None
    all_ts = []
    tool_counts = {}
    files = set()
    pr_set = set()
    pr_create = False

    try:
        fh = open(path, "r", errors="replace")
    except Exception:
        return None
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            if t == "ai-title":
                title = o.get("aiTitle") or title
                continue
            if cwd is None and o.get("cwd"):
                cwd = o.get("cwd")
            if o.get("gitBranch"):
                branch = o.get("gitBranch")
            ts = parse_ts(o.get("timestamp"))
            if ts:
                all_ts.append(ts)
                if ts_first is None or ts < ts_first:
                    ts_first = ts
                if ts_last is None or ts > ts_last:
                    ts_last = ts

            if t == "user":
                p = is_real_user_prompt(o)
                if p is not None:
                    prompt_count += 1
                    if first_prompt is None:
                        first_prompt = p
                msg = o.get("message")
                if isinstance(msg, dict) and isinstance(msg.get("content"), list):
                    for b in msg["content"]:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            rc = b.get("content")
                            txt = rc if isinstance(rc, str) else (
                                extract_text(rc) if isinstance(rc, list) else "")
                            for m in PR_URL_RE.finditer(txt or ""):
                                pr_set.add((m.group(1), m.group(2)))

            elif t == "assistant":
                msg = o.get("message")
                if isinstance(msg, dict) and isinstance(msg.get("content"), list):
                    has_block = False
                    for blk in msg["content"]:
                        if not isinstance(blk, dict):
                            continue
                        bt = blk.get("type")
                        if bt == "text":
                            has_block = True
                            for m in PR_URL_RE.finditer(blk.get("text", "")):
                                pr_set.add((m.group(1), m.group(2)))
                        elif bt == "tool_use":
                            has_block = True
                            name = blk.get("name", "?")
                            tool_counts[name] = tool_counts.get(name, 0) + 1
                            inp = blk.get("input", {}) or {}
                            if name in ("Edit", "Write", "NotebookEdit"):
                                fp = inp.get("file_path") or inp.get("notebook_path")
                                if fp:
                                    files.add(fp)
                            if name == "Bash":
                                cmd = inp.get("command", "") or ""
                                commits += len(COMMIT_RE.findall(cmd))
                                if PR_CREATE_RE.search(cmd):
                                    pr_create = True
                                for m in PR_URL_RE.finditer(cmd):
                                    pr_set.add((m.group(1), m.group(2)))
                    if has_block:
                        assistant_count += 1

    if first_prompt is None and assistant_count == 0:
        return None
    if ts_first is None:
        return None

    span_min = round((ts_last - ts_first).total_seconds() / 60) if ts_last else 0
    all_ts.sort()
    active_sec = sum(min((b - a).total_seconds(), IDLE_CAP)
                     for a, b in zip(all_ts, all_ts[1:])
                     if 0 < (b - a).total_seconds() <= IDLE_CAP)
    active_min = round(active_sec / 60)

    proj = "unknown"
    if cwd:
        proj = os.path.basename(cwd.rstrip("/")) or cwd
        if ".claude-worktrees" in cwd or "worktree" in cwd.lower():
            proj += " ⑂"

    prs = [{"repo": r, "num": n, "url": f"https://github.com/{r}/pull/{n}"}
           for (r, n) in sorted(pr_set, key=lambda x: (x[0], int(x[1])))]

    return {
        "id": os.path.splitext(os.path.basename(path))[0],
        "title": title or (first_prompt[:80] if first_prompt else "(untitled session)"),
        "project": proj,
        "cwd": cwd or "",
        "branch": branch or "",
        "start": ts_first.astimezone().isoformat(),
        "end": ts_last.astimezone().isoformat() if ts_last else None,
        "duration_min": active_min,
        "span_min": span_min,
        "prompt_count": prompt_count,
        "assistant_count": assistant_count,
        "first_prompt": (first_prompt or "")[:600],
        "files": sorted(files),
        "file_count": len(files),
        "commits": commits,
        "prs": prs,
        "pr_create": pr_create,
        "tools": tool_counts,
        "path": path,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="look back this many days")
    ap.add_argument("--out", default="~/.claude/recaps", help="output directory")
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp()
    paths = [p for p in glob.glob(os.path.join(PROJECTS_DIR, "*", "*.jsonl"))
             if _mtime_ok(p, cutoff)]

    sessions = [s for s in (parse_session(p) for p in paths) if s]
    sessions.sort(key=lambda s: s["start"], reverse=True)
    for s in sessions:
        s["notable"] = bool(
            s["prs"] or s["commits"] or s["file_count"] >= 3
            or s["assistant_count"] >= 25 or s["duration_min"] >= 20)

    data = {
        "generated": datetime.now().astimezone().isoformat(),
        "days": args.days,
        "session_count": len(sessions),
        "notable_count": sum(1 for s in sessions if s["notable"]),
        "sessions": sessions,
    }
    with open(os.path.join(out, "sessions.json"), "w") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"parsed {len(sessions)} sessions ({data['notable_count']} notable) "
          f"over {args.days}d -> {os.path.join(out, 'sessions.json')}")


def _mtime_ok(p, cutoff):
    try:
        return os.path.getmtime(p) >= cutoff
    except OSError:
        return False


if __name__ == "__main__":
    main()
