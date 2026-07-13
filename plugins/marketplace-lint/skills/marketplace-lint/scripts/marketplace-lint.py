#!/usr/bin/env python3
"""marketplace-lint.py — validate plugin structure + registration in this repo.

Scans plugins/<name>/ and cross-checks the root marketplace.json and README.md.
Usage: marketplace-lint.py [plugin-name]   (no arg = all plugins)
Output: JSON {plugins, findings:[{plugin, level, check, detail}], summary}.
Exit 1 if any error-level finding; 0 otherwise.
"""
import json
import os
import re
import subprocess
import sys

ERROR, WARN = "error", "warn"


def repo_root():
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else os.getcwd()


def frontmatter(skill_md):
    """Return the YAML-ish frontmatter block as a dict of top-level scalar keys."""
    text = skill_md
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block, out = text[3:end], {}
    for line in block.splitlines():
        m = re.match(r"^([a-zA-Z0-9_-]+):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def lint_plugin(root, name, marketplace_names, marketplace_sources, readme):
    f = []  # findings for this plugin
    pdir = os.path.join(root, "plugins", name)

    # plugin.json
    pj_path = os.path.join(pdir, ".claude-plugin", "plugin.json")
    if not os.path.isfile(pj_path):
        f.append((ERROR, "plugin.json", "missing .claude-plugin/plugin.json"))
    else:
        try:
            pj = json.load(open(pj_path))
            if "name" not in pj:
                f.append((ERROR, "plugin.json", "missing 'name' field"))
            elif pj["name"] != name:
                f.append((ERROR, "plugin.json",
                          f"name '{pj['name']}' != directory '{name}'"))
        except json.JSONDecodeError as e:
            f.append((ERROR, "plugin.json", f"invalid JSON: {e}"))

    # registration
    if name not in marketplace_names:
        f.append((ERROR, "registration", "not listed in marketplace.json"))
    elif f"./plugins/{name}" not in marketplace_sources:
        f.append((WARN, "registration",
                  "marketplace.json source != ./plugins/<name>"))
    # Use delimiter-bound forms (install ref `name@`, command `/name`, backticked)
    # so short names like 'push' don't match incidental prose ("git push").
    if not any(tok in readme for tok in (f"{name}@", f"/{name}", f"`{name}`")):
        f.append((WARN, "registration", "not mentioned in README.md"))

    # SKILL.md (find any under skills/)
    skills = []
    sk_dir = os.path.join(pdir, "skills")
    for dp, _, fns in os.walk(sk_dir):
        skills += [os.path.join(dp, fn) for fn in fns if fn == "SKILL.md"]
    if not skills:
        f.append((ERROR, "SKILL.md", "no SKILL.md found under skills/"))
    for sk in skills:
        text = open(sk).read()
        fm = frontmatter(text)
        rel = os.path.relpath(sk, root)
        if fm is None:
            f.append((ERROR, "SKILL.md", f"{rel}: missing/!malformed frontmatter"))
            continue
        for key in ("name", "description"):
            if not fm.get(key):
                f.append((ERROR, "SKILL.md", f"{rel}: frontmatter missing '{key}'"))
        skill_dir = os.path.basename(os.path.dirname(sk))
        if fm.get("name") and fm["name"] != skill_dir:
            f.append((WARN, "SKILL.md",
                      f"{rel}: frontmatter name '{fm['name']}' != skill dir '{skill_dir}'"))
        # Pre-plugin-era script paths break when the plugin runs installed
        # (there is no .claude/skills/ in the plugin cache).
        if re.search(r"\$\{?CLAUDE_PROJECT_DIR\}?\"?/\.claude/skills/", text):
            f.append((ERROR, "SKILL.md",
                      f"{rel}: $CLAUDE_PROJECT_DIR/.claude/skills path — use ${{CLAUDE_PLUGIN_ROOT}}/skills/..."))
        # Progressive-disclosure rule: the spine stays under ~500 lines.
        n_lines = len(text.splitlines())
        if n_lines > 500:
            f.append((WARN, "SKILL.md",
                      f"{rel}: {n_lines} lines (> 500) — move detail to references/"))

    # scripts: executable + python compiles
    for dp, _, fns in os.walk(pdir):
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root)
            if fn.endswith((".sh", ".py")):
                if not os.access(p, os.X_OK):
                    f.append((WARN, "scripts", f"{rel}: not executable (chmod +x)"))
            if fn.endswith(".py"):
                r = subprocess.run([sys.executable, "-m", "py_compile", p],
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    f.append((ERROR, "scripts", f"{rel}: does not compile"))

    # references >100 lines need a Contents TOC near the top
    for dp, _, fns in os.walk(pdir):
        if os.path.basename(dp) != "references":
            continue
        for fn in fns:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dp, fn)
            lines = open(p).read().splitlines()
            rel = os.path.relpath(p, root)
            if len(lines) > 100 and not any(
                    l.strip().lower() == "## contents" for l in lines[:15]):
                f.append((WARN, "references",
                          f"{rel}: {len(lines)} lines, no '## Contents' TOC"))
    return [(name, lvl, chk, det) for (lvl, chk, det) in f]


def main():
    root = repo_root()
    only = sys.argv[1] if len(sys.argv) > 1 else None
    plugins_dir = os.path.join(root, "plugins")
    if not os.path.isdir(plugins_dir):
        print(json.dumps({"error": f"no plugins/ dir at {root}"}))
        sys.exit(1)

    mk_names, mk_sources = set(), set()
    mk_path = os.path.join(root, ".claude-plugin", "marketplace.json")
    top = []
    try:
        mk = json.load(open(mk_path))
        for p in mk.get("plugins", []):
            mk_names.add(p.get("name"))
            mk_sources.add(p.get("source"))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        top.append(("(marketplace)", ERROR, "marketplace.json", f"unreadable: {e}"))

    readme = ""
    rp = os.path.join(root, "README.md")
    if os.path.isfile(rp):
        readme = open(rp).read()

    names = sorted(d for d in os.listdir(plugins_dir)
                   if os.path.isdir(os.path.join(plugins_dir, d)))
    if only:
        if only not in names:
            print(json.dumps({"error": f"plugin '{only}' not found"}))
            sys.exit(1)
        names = [only]

    findings = list(top)
    for n in names:
        findings += lint_plugin(root, n, mk_names, mk_sources, readme)

    summary = {
        "error": sum(1 for _, lvl, *_ in findings if lvl == ERROR),
        "warn": sum(1 for _, lvl, *_ in findings if lvl == WARN),
        "plugins_checked": len(names),
    }
    print(json.dumps({
        "plugins": names,
        "findings": [{"plugin": p, "level": l, "check": c, "detail": d}
                     for (p, l, c, d) in findings],
        "summary": summary,
    }, indent=2))
    sys.exit(1 if summary["error"] else 0)


if __name__ == "__main__":
    main()
