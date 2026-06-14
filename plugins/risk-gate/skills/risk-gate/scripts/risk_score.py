#!/usr/bin/env python3
"""risk_score.py — deterministic per-file change-risk scorer for the risk-gate skill.

risk = likelihood-of-defect x blast-radius. We approximate blast-radius from WHERE
the change lands (sensitive-path keywords) and likelihood from HOW MUCH/COMPLEX it
is (churn + added control flow). Weights are heuristic defaults documented in
references/risk-signals.md — tune them to your codebase's incident history.

Usage: risk_score.py [BASE_REF]
  BASE_REF: diff base. Default: merge-base with origin's default branch, else HEAD.

Output: JSON to stdout — {base, files:[{path, added, removed, score, bucket, reasons}], summary}.
Exit 0 even with zero changed files (the orchestrator decides what to do).
"""
import json
import re
import subprocess
import sys

# --- Impact signals: (label, weight, regex over the file path OR added content) ---
# Each category that fires contributes its weight once. Justifications in the reference.
IMPACT_SIGNALS = [
    ("auth/authz",        3, r"auth|login|logout|session|\btoken\b|password|permission|rbac|acl|oauth|jwt"),
    ("money",             3, r"payment|billing|charge|invoice|refund|\bprice\b|checkout|ledger|stripe|paypal"),
    ("crypto/secrets",    3, r"crypto|cipher|encrypt|decrypt|secret|apikey|api_key|private_key|signature|\.pem|\.key"),
    ("migration/schema",  3, r"migration|/migrations/|schema|alter table|\.sql\b|prisma|ddl"),
    ("llm/api-spend",     2, r"openai|anthropic|\bclaude\b|completion|embedding|\bllm\b"),
    ("concurrency",       2, r"async|await|thread|mutex|\block\b|semaphore|queue|worker|goroutine|concurren"),
    ("infra/deploy",      2, r"dockerfile|\.tf\b|\.tfvars|/k8s/|helm|/\.github/workflows/|jenkinsfile|\.circleci"),
    ("public-api",        2, r"\.graphql|\.proto\b|openapi|swagger|/routes|/controller|/api/"),
    ("dep-manifest",      2, r"package\.json|package-lock|pnpm-lock|yarn\.lock|requirements\.txt|go\.mod|cargo\.toml|pyproject\.toml|gemfile|pom\.xml"),
    ("shared/core",       2, r"/common/|/core/|/shared/|/lib/|/base/|/util"),
    ("config",            1, r"\.env|\.config|\.ini|\.toml|\.properties|values\.yaml|feature.?flag"),
]

# Added control-flow tokens => new (likely untested) branches. Capped contribution.
CONTROL_FLOW = re.compile(r"\b(if|else|elif|for|while|switch|case|catch|except)\b|\?.*:|&&|\|\|")


def sh(args):
    return subprocess.run(args, capture_output=True, text=True)


def resolve_base(arg):
    if arg:
        return arg
    # Try origin's default branch merge-base.
    head = sh(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
    if head.returncode == 0:
        ref = head.stdout.strip().split("/")[-1]
        mb = sh(["git", "merge-base", f"origin/{ref}", "HEAD"])
        if mb.returncode == 0 and mb.stdout.strip():
            return mb.stdout.strip()
    return "HEAD"


def numstat(base):
    """Return {path: (added, removed)} for the diff vs base (+ working tree)."""
    out = sh(["git", "diff", "--numstat", base])
    files = {}
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, r, path = parts
        added = int(a) if a.isdigit() else 0
        removed = int(r) if r.isdigit() else 0
        files[path] = (added, removed)
    return files


def added_lines(base):
    """Return {path: concatenated added-line text} for content scanning."""
    out = sh(["git", "diff", base])
    blobs, cur = {}, None
    for line in out.stdout.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
            blobs[cur] = []
        elif cur and line.startswith("+") and not line.startswith("+++"):
            blobs[cur].append(line[1:])
    return {p: "\n".join(ls) for p, ls in blobs.items()}


def score_file(path, added, removed, content):
    reasons, score = [], 0
    hay = (path + "\n" + content).lower()
    for label, weight, pat in IMPACT_SIGNALS:
        if re.search(pat, hay):
            score += weight
            reasons.append(f"{label} (+{weight})")
    # Likelihood: churn.
    churn = added + removed
    if churn > 200:
        score += 3; reasons.append("churn>200 (+3)")
    elif churn > 50:
        score += 2; reasons.append("churn 50-200 (+2)")
    elif churn > 10:
        score += 1; reasons.append("churn 10-50 (+1)")
    if removed > 0:
        score += 1; reasons.append("has deletions (+1)")
    # Likelihood: new control flow on added lines (capped at +3).
    cf = len(CONTROL_FLOW.findall(content))
    if cf:
        bonus = min(cf, 3)
        score += bonus; reasons.append(f"added control-flow x{cf} (+{bonus})")
    bucket = "high" if score >= 6 else "medium" if score >= 3 else "low"
    return {"path": path, "added": added, "removed": removed,
            "score": score, "bucket": bucket, "reasons": reasons}


def main():
    base = resolve_base(sys.argv[1] if len(sys.argv) > 1 else None)
    stats = numstat(base)
    content = added_lines(base)
    files = [score_file(p, a, r, content.get(p, "")) for p, (a, r) in stats.items()]
    files.sort(key=lambda f: f["score"], reverse=True)
    summary = {b: sum(1 for f in files if f["bucket"] == b) for b in ("high", "medium", "low")}
    print(json.dumps({"base": base, "files": files, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
