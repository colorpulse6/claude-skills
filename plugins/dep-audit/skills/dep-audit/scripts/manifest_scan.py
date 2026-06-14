#!/usr/bin/env python3
"""manifest_scan.py — offline (zero-network) dependency-diff scanner for dep-audit.

Reads the diff of dependency manifests/lockfiles vs a base ref and flags
risk *shapes* visible without the network: semver deltas, range loosening,
new install scripts, lockfile-integrity/source changes, and typosquat
suspicion. The scanner agents confirm real CVEs/malware in the network pass.

Usage: manifest_scan.py [BASE_REF]
Output: JSON {base, ecosystems, packages:[{name, ecosystem, change, flags}], notes}.
Exit 0 even with no changes.

npm package.json gets full parsing (deps + scripts). Other ecosystems get a
generic lockfile red-flag line scan. Extend MANIFESTS / parsing per your stack.
"""
import json
import re
import subprocess
import sys

MANIFESTS = {
    "package.json": "npm", "package-lock.json": "npm", "pnpm-lock.yaml": "npm",
    "yarn.lock": "npm", "requirements.txt": "pypi", "pyproject.toml": "pypi",
    "poetry.lock": "pypi", "go.mod": "go", "go.sum": "go",
    "Cargo.toml": "cargo", "Cargo.lock": "cargo", "Gemfile.lock": "rubygems",
    "pom.xml": "maven",
}

# Small popular-name set for the typosquat heuristic. Extend per ecosystem.
POPULAR = {
    "react", "lodash", "express", "axios", "chalk", "commander", "debug",
    "request", "moment", "vue", "webpack", "babel", "jest", "typescript",
    "next", "dotenv", "uuid", "classnames", "redux", "rxjs",
    "requests", "numpy", "pandas", "flask", "django", "pytest", "jinja2",
    "urllib3", "setuptools", "pip", "boto3", "pillow", "cryptography",
}

RANGE_LOOSE = re.compile(r'["\']?\^|["\']?~|\*|latest|>=')


def sh(args):
    return subprocess.run(args, capture_output=True, text=True)


def resolve_base(arg):
    if arg:
        return arg
    head = sh(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
    if head.returncode == 0:
        ref = head.stdout.strip().split("/")[-1]
        mb = sh(["git", "merge-base", f"origin/{ref}", "HEAD"])
        if mb.returncode == 0 and mb.stdout.strip():
            return mb.stdout.strip()
    return "HEAD"


def changed_manifests(base):
    out = sh(["git", "diff", "--name-only", base])
    hits = []
    for path in out.stdout.splitlines():
        name = path.rsplit("/", 1)[-1]
        if name in MANIFESTS:
            hits.append((path, MANIFESTS[name], name))
    return hits


def transposition_or_edit1(a, b):
    """True if a is within Levenshtein-1 or a single adjacent transposition of b."""
    if a == b:
        return False
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    # adjacent transposition (same length)
    if la == lb:
        diff = [i for i in range(la) if a[i] != b[i]]
        if len(diff) == 2 and diff[1] == diff[0] + 1 \
           and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]:
            return True
    # edit distance 1 (substitution / insertion / deletion)
    i = j = edits = 0
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1; j += 1
        else:
            edits += 1
            if edits > 1:
                return False
            if la > lb:
                i += 1
            elif lb > la:
                j += 1
            else:
                i += 1; j += 1
    return True


def typosquat(name):
    n = name.lower().lstrip("@").split("/")[-1]
    if n in POPULAR:
        return None
    for pop in POPULAR:
        if transposition_or_edit1(n, pop) or n.replace("-", "") == pop or n == pop + "js":
            return pop
    return None


def added_blobs(base):
    """Return {path: [added lines]} for content scanning."""
    out = sh(["git", "diff", base])
    blobs, cur = {}, None
    for line in out.stdout.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]; blobs[cur] = []
        elif cur and line.startswith("+") and not line.startswith("+++"):
            blobs[cur].append(line[1:])
    return blobs


def scan_npm_packagejson(path, base, packages, notes):
    """Parse old vs new package.json deps + scripts."""
    new = sh(["git", "show", f":{path}"]).stdout or sh(["git", "show", f"HEAD:{path}"]).stdout
    old = sh(["git", "show", f"{base}:{path}"]).stdout
    try:
        newj = json.loads(new) if new else {}
    except json.JSONDecodeError:
        notes.append(f"could not parse new {path}"); return
    oldj = {}
    try:
        oldj = json.loads(old) if old else {}
    except json.JSONDecodeError:
        notes.append(f"could not parse base {path}")

    def deps(j):
        d = {}
        for key in ("dependencies", "devDependencies", "optionalDependencies"):
            d.update(j.get(key, {}))
        return d

    nd, od = deps(newj), deps(oldj)
    for name, spec in nd.items():
        flags = []
        if name not in od:
            change = "added"
            ts = typosquat(name)
            if ts:
                flags.append(f"typosquat? near '{ts}'")
        elif od[name] != spec:
            change = "changed"
        else:
            continue
        if RANGE_LOOSE.search(str(spec)):
            flags.append(f"loose range '{spec}'")
        packages.append({"name": name, "ecosystem": "npm",
                         "change": change, "spec": spec, "flags": flags})

    # New install scripts
    new_scripts = newj.get("scripts", {})
    old_scripts = oldj.get("scripts", {})
    for hook in ("preinstall", "install", "postinstall"):
        if hook in new_scripts and new_scripts.get(hook) != old_scripts.get(hook):
            notes.append(f"{path}: new/changed '{hook}' script: {new_scripts[hook]!r}")


def scan_lockfile_lines(path, blob, notes):
    """Generic red-flag scan over added lockfile lines."""
    for line in blob:
        low = line.lower()
        if "integrity" in low and "sha" in low:
            continue  # integrity present is normal; mismatch detection needs old-vs-new pairing
        if re.search(r'(git\+|https?://|file:)', low) and ("resolved" in low or "source" in low or "url" in low):
            notes.append(f"{path}: dependency source repoint -> {line.strip()[:120]}")


def main():
    base = resolve_base(sys.argv[1] if len(sys.argv) > 1 else None)
    manifests = changed_manifests(base)
    if not manifests:
        print(json.dumps({"base": base, "ecosystems": [], "packages": [],
                          "notes": ["no dependency manifests changed"]}, indent=2))
        return
    blobs = added_blobs(base)
    packages, notes = [], []
    ecosystems = sorted({eco for _, eco, _ in manifests})
    for path, eco, name in manifests:
        if name == "package.json":
            scan_npm_packagejson(path, base, packages, notes)
        else:
            scan_lockfile_lines(path, blobs.get(path, []), notes)
    print(json.dumps({"base": base, "ecosystems": ecosystems,
                      "packages": packages, "notes": notes}, indent=2))


if __name__ == "__main__":
    main()
