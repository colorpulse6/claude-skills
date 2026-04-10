---
name: push
description: >-
  Quality-gated push pipeline. Auto-detects package manager (pnpm/yarn/npm) and
  runs available scripts (check-types, lint, test, build) in parallel before
  pushing. Auto-fixes failures in a retry loop, creates a PR, and polls CI.
  Use when user says "push", "push to remote", "ship it", or invokes /push.
user-invocable: true
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Agent
---

# Push

Quality-gated push pipeline. Never let broken code hit the remote.

## Verbose Logging Format

Output structured, emoji-prefixed logs throughout:

```
📋 Step N — Step Name
   ├─ ✅ Sub-step passed (details)
   ├─ ⏭️  Sub-step skipped (reason)
   ├─ ❌ Sub-step failed (error summary)
   ├─ 🔄 Retrying... (attempt N/3)
   └─ 📊 Summary: X passed, Y failed
```

Track elapsed time for each major step. Output a timing summary at the end.

---

## 🚀 Step 1 — Preflight

Run the preflight script to verify environment is ready.

```bash
"$CLAUDE_PROJECT_DIR"/.claude/skills/push/scripts/preflight.sh
```

(If running from a globally installed plugin, the path will be different - detect and use the correct location.)

Checks:
- gh CLI installed and authenticated
- In a git repository
- Not in detached HEAD state
- Branch is not main/master (blocks direct push)

If any check fails, stop and report.

---

## 🔍 Step 2 — Detect Project Setup

Auto-detect what to run based on what exists in the project.

```bash
# Package manager detection
if [ -f "pnpm-lock.yaml" ]; then
  PKG="pnpm"
elif [ -f "yarn.lock" ]; then
  PKG="yarn"
elif [ -f "package-lock.json" ]; then
  PKG="npm"
else
  PKG=""  # No Node project detected
fi
```

If no package.json exists, skip Node-specific checks but still run git operations.

Detect available scripts from package.json:
```bash
if [ -f "package.json" ]; then
  AVAILABLE_SCRIPTS=$(cat package.json | grep -oE '"(check-types|typecheck|lint|test|build)"' | tr -d '"' | tr '\n' ' ')
fi
```

Log detected setup:
```
   ├─ ✅ Package manager: {pnpm|yarn|npm|none}
   ├─ ✅ Available scripts: {list}
   └─ ✅ Project type: {Node/TS | other}
```

---

## 📊 Step 3 — Git State Check

```bash
git branch --show-current
git status --short
git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || git log --oneline -5
```

Capture branch name, uncommitted changes, commits ahead of remote.

If no commits to push AND no uncommitted changes, stop with `⏭️  Nothing to push`.

---

## 🧪 Step 4 — Quality Gates (Parallel)

Run all detected gates in parallel. Skip gates for scripts that don't exist.

Available gates (run only if the script exists in package.json):
- Type check: `$PKG run check-types` OR `$PKG run typecheck` (whichever exists)
- Lint: `$PKG run lint`
- Tests: `$PKG run test`
- Build: `$PKG run build`

Additionally, run the secret scanner regardless of project type:
```bash
"$CLAUDE_PROJECT_DIR"/.claude/skills/push/scripts/secret-scan.sh
```

Log each gate result as it completes:
```
   ├─ ✅ Type check (8.2s)
   ├─ ✅ Lint (1.1s)
   ├─ ❌ Tests failed: 2 failures
   ├─ ✅ Build (12.4s)
   └─ ✅ Secret scan
```

If ANY gate fails, proceed to Step 5 (Auto-Fix). If ALL pass, skip to Step 6.

---

## 🔧 Step 5 — Auto-Fix Loop (if gates failed)

Iterate up to 3 times.

Fix strategies:
- Type check: read error, fix types. Never use `any` or `@ts-ignore` as a shortcut
- Lint: run `$PKG run lint:fix` first (if it exists), then fix remaining errors manually
- Tests: read failure output, fix the code (not the test) unless the test is demonstrably wrong
- Build: usually follows from type fixes
- Secret scan: remove the offending file from staging

After each fix iteration, re-run ONLY the failed gates (faster than re-running everything).

If after 3 iterations there are still failures, stop and ask for human intervention.

Do NOT push if gates still fail.

---

## 💾 Step 6 — Commit Changes (if any)

If there are uncommitted changes (original or from auto-fix):

```bash
git status --short
git diff --stat
git log --oneline -5  # For commit message style reference
```

Generate a conventional commit message:
- Format: `<type>(<scope>): <subject>`
- Types: feat, fix, docs, style, refactor, test, chore, ci, build, perf
- Scope: the area affected
- Subject: imperative, lowercase, no period

Stage specific files (not `git add -A`):
```bash
git add <files>
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

<body - why, not what>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

NEVER commit files that look like secrets (.env, credentials.json, keys).

---

## 📤 Step 7 — Push to Remote

```bash
BRANCH=$(git branch --show-current)
git push -u origin "$BRANCH"
```

If push fails due to upstream changes:
```bash
git pull --rebase origin "$BRANCH"
```

Then retry. If rebase has conflicts, stop and ask the user.

---

## 🔀 Step 8 — Create or Update PR

Check if PR already exists:
```bash
gh pr view --json number,url,state 2>/dev/null
```

If exists, log the URL and skip creation. If not, create PR targeting main (or master):

```bash
gh pr create --base main --title "<title>" --body "$(cat <<'EOF'
## Summary
- <point 1>
- <point 2>

## Changes
- <change 1>
- <change 2>

## Test plan
- [ ] <verification 1>
- [ ] <verification 2>

🤖 Generated with Claude Code
EOF
)"
```

---

## ⏳ Step 9 — Watch CI

Poll GitHub Actions until all checks complete:

```bash
gh pr checks --watch
```

Update every 20 seconds.

If CI passes, proceed to Step 10.

If CI fails, auto-fix loop (max 2 iterations):
```bash
gh run view --log-failed
```

After fixing, commit and push (triggers new CI run). Loop back.

If still failing after 2 iterations, stop and report.

---

## 📊 Step 10 — Summary

Print a timing table with all step durations and statuses.

Final status line with branch, PR URL, and CI status.

---

## Rules

1. Never skip quality gates
2. Never use `--no-verify`
3. Never force push unless explicitly asked
4. Never push directly to main
5. Auto-fix with `any` or `@ts-ignore` = fail, fix properly
6. Fix the code, not the test
7. Conventional commits always
8. Max 3 auto-fix iterations on local gates
9. Max 2 auto-fix iterations on CI
10. Never commit secrets
