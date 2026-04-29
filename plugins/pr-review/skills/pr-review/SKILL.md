---
name: pr-review
description: >-
  AI-powered PR review with contract verification, frontend and backend rules,
  inbox mode, and incremental re-review. Auto-detects project type and applies
  relevant rules. Use when user says "review PR 42", "review my PRs", "check
  my PR inbox", "pr review", or invokes /pr-review.
user-invocable: true
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Agent
---

# PR Review

PR review for any GitHub repo. Runs a reviewer subagent with rules tailored to the project's stack, performs contract verification, and posts findings to the PR via the GitHub reviews API.

> **CRITICAL — POSTING IS MANDATORY, NOT OPTIONAL:**
> - All review output MUST end with a successful `POST /repos/{owner}/{repo}/pulls/{number}/reviews` call (Step 10).
> - All non-summary findings MUST be inline comments anchored to a `path` + `line` on the new-file side of the diff.
> - NEVER stop after rendering the review in chat. NEVER post code feedback as a general issue comment. If you produced a finding and did not post it, that is a defect — submit before ending the turn.

> **DEFAULT MODE — AUTONOMOUS:**
> When invoked with a single PR reference (number, URL, or branch name) and no `walk` / `interactive` token, run **non-interactive**:
> 1. Generate the review.
> 2. Render the summary box (Step 8) for the user.
> 3. Skip the per-finding walkthrough (Step 9).
> 4. Submit immediately via the reviews API (Step 10) with **all findings accepted**.
>
> Only enter the interactive walkthrough when:
> - The user appended `walk` / `interactive` / `--walk` to the invocation, OR
> - You are in **inbox mode** (no PR argument), OR
> - The user explicitly asks ("walk me through it", "review interactively", etc.)

---

## Step 1: Parse Input & Determine Mode

Two modes: **single PR mode** (argument provided) or **inbox mode** (no argument). Plus an optional **interactivity flag**.

### Interactivity Flag

If the args contain a token matching `walk`, `interactive`, `--walk`, or `--interactive` (case-insensitive), set `INTERACTIVE = true`. Otherwise `INTERACTIVE = false`.

In single-PR mode, `INTERACTIVE = false` is the default (autonomous: render summary, post immediately). In inbox mode, `INTERACTIVE = true` is the default (since the user is choosing PRs to review).

Strip the flag token from the args before parsing the PR reference.

### Single PR Mode

Argument can be a PR number (`42`), a PR URL (`https://github.com/owner/repo/pull/42`), or a branch name. Normalize to `{NUMBER}` and `{OWNER}/{REPO}` for subsequent commands.

```bash
# If argument is a URL, parse owner/repo/number
# If argument is just a number, detect repo via:
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
```

### Inbox Mode (no argument)

Detect current repo and list PRs awaiting the user's review:

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
gh search prs --review-requested=@me --repo="$REPO" --state=open --json number,title,author,url,isDraft
```

For each PR, fetch enrichment data:

```bash
gh pr view {NUMBER} --json number,title,author,additions,deletions,isDraft,statusCheckRollup
```

Build a summary table with emoji check status:

| Emoji | Meaning |
|---|---|
| ✅ | All checks pass |
| ❌ | One or more checks failed |
| ⏳ | Checks pending / in progress |
| ➖ | No checks configured |

Mark drafts with `[DRAFT]` prefix. Example output:

```
PRs awaiting your review in owner/repo:

  #142  ✅  feat: add user export            (alice)     +240 -30
  #138  ❌  fix: race in webhook handler     (bob)       +45  -12
  #135  ⏳  [DRAFT] chore: upgrade deps      (carol)     +800 -800
  #130  ➖  docs: update README              (dave)      +15  -2

(A)ll / (P)ick / (N)one?
```

- **All**: iterate sequentially through every PR (skip drafts unless confirmed)
- **Pick**: ask for a PR number
- **None**: exit

---

## Step 2: Fetch PR Context

```bash
gh pr view {NUMBER} --json title,author,body,additions,deletions,isDraft,baseRefName,headRefName,url,headRefOid
gh pr checks {NUMBER}
gh pr diff {NUMBER}
gh pr view {NUMBER} --json files --jq '.files[].path'
```

**Edge cases:**
- PR not found → print error, exit with guidance
- Own PR → in inbox mode, silently skip. In single mode, warn the user ("This is your own PR - review anyway? y/n")
- PR closed/merged → confirm before reviewing

---

## Step 3: Check for Prior Review (Incremental Mode)

```bash
CURRENT_USER=$(gh api user --jq '.login')
gh api repos/{OWNER}/{REPO}/pulls/{NUMBER}/reviews --jq ".[] | select(.user.login == \"$CURRENT_USER\")"
```

If prior reviews exist, get the most recent review's `submitted_at` and `commit_id`. Count new commits since that review:

```bash
gh api repos/{OWNER}/{REPO}/pulls/{NUMBER}/commits --jq '.[] | select(.commit.author.date > "{LAST_REVIEW_AT}")'
```

If new commits exist, offer:

```
You already reviewed this PR. {N} new commits since your last review.

  (F)ull re-review
  (I)ncremental (only new commits)
  (S)kip
```

**For incremental:** fetch the delta diff using the parent SHA of the first new commit:

```bash
PARENT_SHA=$(gh api repos/{OWNER}/{REPO}/commits/{FIRST_NEW_COMMIT_SHA} --jq '.parents[0].sha')
gh api repos/{OWNER}/{REPO}/compare/$PARENT_SHA...{HEAD_SHA} --jq '.files[] | {filename, patch}'
```

If the delta diff is empty (rebase detected or force-push rewrote history), print a note and fall back to full review.

---

## Step 4: Diff Management

### Filter Generated Files

Exclude these paths before counting size or sending to the subagent:

```
*.lock
*.min.js
*.min.css
*.snap
*.generated.*
package-lock.json
yarn.lock
pnpm-lock.yaml
*.g.dart
*.pb.go
*_generated.go
dist/**
build/**
src/generated/**
*.graphql.ts   (if auto-generated)
```

**Note:** Prisma migration SQL files under `prisma/migrations/**/migration.sql` are generated output and should be excluded, BUT the `schema.prisma` changes they reflect SHOULD be reviewed.

### Size Check

Count non-generated diff lines.

| Size | Strategy |
|---|---|
| `< 2000` lines | Full diff, one subagent |
| `2000-8000` lines | Ask user: full review or split by directory? |
| `> 8000` lines | Auto-split by top-level directory |

### Chunked Review

For splits:
1. Group changed files by top-level directory (`apps/web/`, `apps/api/`, `packages/*/`, etc.)
2. Dispatch one reviewer subagent per group (in parallel via multiple Agent tool calls in the same turn)
3. Merge findings, deduplicated by `{file}:{line}:{title}`

---

## Step 5: Detect Project Type & Load Rules

Inspect changed file paths to determine what rule files to include.

### Detection Logic

- **Frontend** if diff contains any of:
  - `*.tsx`, `*.jsx`
  - files under `src/components/`, `src/pages/`, `src/app/`, `pages/`, `app/`
  - `*.vue`, `*.svelte`

- **Backend** if diff contains any of:
  - files under `apps/api/`, `apps/*-api/`, `services/`, `server/`
  - files under `packages/*/src/` containing `*.service.ts`, `*.repository.ts`, `*.controller.ts`, `*.router.ts`, `*.resolver.ts`
  - `schema.prisma`, `*.sql`

- **Full-stack** if both detected.

### Load Reference Files

Read these from this skill's directory based on detection:

- **ALWAYS:** `references/severity-definitions.md`
- **ALWAYS:** `references/contract-verification.md`
- **If frontend:** `references/frontend-rules.md`
- **If backend:** `references/backend-rules.md`

Cache the contents in memory for the subagent prompt assembly in Step 7.

---

## Step 6: Contract Verification (Pre-Review Scan)

Before dispatching the reviewer subagent, perform a lightweight contract verification pass to catch silent typo bugs that AI review often misses.

Read `references/contract-verification.md` for the detailed checks. Summary:

For each changed file:
1. **GraphQL resolvers:** verify resolver input matches GraphQL schema input AND the domain service signature
2. **REST routes:** verify handler param names match the Zod/validation schema for the request body
3. **Prisma-using repositories:** verify field names referenced in `where`/`select`/`data` exist in the current `schema.prisma`
4. **Renamed fields:** if a field was renamed in this PR, grep for the old name across the whole codebase - any remaining references are findings

Collect all contract findings into a list. Attach them to the diff context before dispatching the subagent (Step 7).

---

## Step 7: Dispatch Reviewer Subagent(s)

Read these files from this skill's directory:
- `review-lens.md`
- `output-contract.md`
- The rules files detected in Step 5

### Assemble Reviewer Prompt

The prompt passed to the Agent tool is a concatenation of:

1. **`review-lens.md`** verbatim (top-level reviewer instructions)
2. **`output-contract.md`** verbatim (JSON schema the subagent must return)
3. **Relevant rule files:** `severity-definitions.md`, `contract-verification.md`, and `frontend-rules.md` and/or `backend-rules.md` based on detection
4. **Contract verification findings** from Step 6 (under a `## Pre-scan Contract Findings` heading)
5. **PR context block:**
   ```
   ## PR Context
   Title: {TITLE}
   Author: {AUTHOR}
   Base: {BASE} ← Head: {HEAD}
   CI: {STATUS}
   URL: {URL}

   ### Description
   {BODY or "(no description)"}

   ### Changed Files
   {FILE_LIST}

   ### Diff
   {FILTERED_DIFF}
   ```
6. **If incremental:** append `## Incremental Review\nYou previously reviewed this PR at commit {OLD_SHA}. Only the following commits are new: {LIST}. Focus exclusively on the delta diff above.`

### Dispatch

Use the Agent tool with a general-purpose subagent. For chunked reviews, dispatch multiple Agent calls in parallel (same turn). Each returns a JSON object matching `output-contract.md`. Merge findings by deduplicating on `{file}:{line}:{title}`.

---

## Step 8: Present Summary

Parse the subagent's JSON response and render a summary box:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR #{NUMBER} - {TITLE} ({AUTHOR})
Checks: {CHECK_EMOJI} {STATUS} | +{ADD} -{DEL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: {EMOJI} {VERDICT}
Summary: {SUMMARY}
Description alignment: {STATUS} {NOTES}

  🔴 {N} Critical    🟡 {N} Important    ⚪ {N} Minor

Strengths:
  - {STRENGTH_1}
  - {STRENGTH_2}
```

**Verdict emoji:**
- `approve` → ✅
- `request-changes` → ❌
- `comment` → 💬

After rendering the summary:

- **If `INTERACTIVE = false`** (autonomous mode): proceed directly to Step 10 with **all findings accepted**. Do NOT ask "Walk through findings?". Do NOT stop. Submit and report.
- **If `INTERACTIVE = true`** (walkthrough mode): append `Walk through findings? (y/n/skip)` and only proceed to Step 9 if the user answers `y`. If `n`/`skip`, accept all findings and proceed to Step 10.

If `findings` is empty, skip Step 9 entirely and go directly to Step 10 (which will submit a clean review with `event: APPROVE`).

---

## Step 9: Finding-by-Finding Walkthrough (Interactive Mode Only)

> **Skip this entire step when `INTERACTIVE = false`.** All findings are auto-accepted and submitted in Step 10. Step 9 only runs when the user explicitly opted into a walkthrough (via the `walk` / `interactive` flag, inbox-mode default, or in-conversation request).

Present each finding one at a time, ordered by severity (critical → important → minor):

```
[{INDEX}/{TOTAL}] {SEVERITY_EMOJI} {SEVERITY} - {TITLE}
File: {FILE}:{LINE_RANGE}

{DIFF_HUNK}

{EXPLANATION}
Why it matters: {WHY}
Suggestion: {SUGGESTION}

(A)ccept / (R)eject / (E)dit / (D)etails?
```

### Actions

- **Accept:** queue the finding for submission. If `suggestion_code` is present, include it as a GitHub suggestion block (`` ```suggestion ... ``` ``) inside the comment body.
- **Reject:** drop the finding. Optionally ask "reason? (optional)" and store it locally for the session summary.
- **Edit:** open the comment body in the user's editor (or inline prompt) for rewriting, then queue the edited version.
- **Details:** expand with 10+ lines of surrounding file context, grep for similar patterns in the codebase, link to relevant docs/rules, then re-display the prompt for action.

Track the accepted/rejected counts for Step 10.

---

## Step 10: Submit Review (MANDATORY TERMINAL STEP)

> **You MUST execute the `gh api` POST call in this step before ending the turn.** If you reached this point and have not yet submitted, do so now. Do NOT print "review ready to submit" and stop. Do NOT summarize without posting. The review is not done until the API call returns 200 and the review URL is shown.

### Behavior by mode

- **Autonomous mode (`INTERACTIVE = false`):** all findings are auto-accepted. Skip the "Submit? (y/n)" prompt. Pick the verdict per the rules below and POST immediately.
- **Walkthrough mode (`INTERACTIVE = true`):** show the submission summary and ask `Submit? (y/n)`. On `y`, POST. On `n`, store findings locally and report.

```
Review ready to submit:
  Accepted: {N_ACCEPTED}
  Rejected: {N_REJECTED}

Recommended verdict: {VERDICT}
```

### Verdict Adjustment Rules

- All Critical findings rejected → downgrade to `comment`
- Any Critical finding accepted → keep `request-changes`
- Only Minor findings accepted → `comment`
- No findings accepted and original verdict was `approve` → `approve`
- No findings at all → `approve`

### Submit via GitHub API

Always use `--input file.json` with a JSON file (not inline `-f`) so newlines and code blocks in comment bodies are preserved.

```bash
COMMIT_ID=$(gh pr view {NUMBER} --json headRefOid --jq '.headRefOid')

# Build payload as JSON (use a small Python or jq script for safety):
cat > /tmp/pr_review_payload.json <<JSON
{
  "commit_id": "$COMMIT_ID",
  "event": "{EVENT}",
  "body": {SUMMARY_BODY_AS_JSON_STRING},
  "comments": [
    {
      "path": "{FILE}",
      "line": {LINE},
      "side": "RIGHT",
      "body": {COMMENT_BODY_AS_JSON_STRING}
    }
  ]
}
JSON

gh api repos/{OWNER}/{REPO}/pulls/{NUMBER}/reviews \
  --method POST \
  --input /tmp/pr_review_payload.json \
  --jq '{id: .id, state: .state, html_url: .html_url}'
```

**Event mapping:**
- `approve` → `APPROVE`
- `request-changes` → `REQUEST_CHANGES`
- `comment` → `COMMENT`

**Implementation tip — building the JSON payload safely:** comment bodies contain backticks, code fences, and newlines. Use Python (`json.dump`) or jq to build the payload — never shell-interpolate raw strings. Example (Python):

```python
import json
payload = {
    "commit_id": commit_id,
    "event": event,
    "body": review_body,
    "comments": [
        {"path": f["file"], "line": f["line"], "side": "RIGHT", "body": f["body"]}
        for f in accepted_findings
    ],
}
with open("/tmp/pr_review_payload.json", "w") as fp:
    json.dump(payload, fp)
```

After successful submission, print exactly:

```
✅ Review submitted: {PR_URL}#pullrequestreview-{REVIEW_ID}
   Verdict: {VERDICT}
   Inline comments: {N_ACCEPTED}
```

**If the API call fails** (4xx / 5xx): show the error, save the payload to `/tmp/pr_review_payload.json` for inspection, and prompt the user. Do NOT silently swallow the failure.

---

## Step 11: Session Summary (Inbox Mode Only)

After iterating through all selected PRs in inbox mode, print a final table:

```
Session Summary:

  PR     Verdict            Findings (C/I/M)
  ────   ────────────────   ────────────────
  #142   ✅ approve         0 / 0 / 1
  #138   ❌ request-changes 2 / 1 / 0
  #135   💬 comment         0 / 3 / 2
  #130   skipped            -
```

---

## Common Mistakes to Avoid

- **Stopping at Step 8:** the most common defect. Step 8 renders a summary; Step 10 is what actually posts. Never end the turn between them in autonomous mode.
- **Posting findings as a general PR comment instead of inline review comments:** ALWAYS use the reviews API with a `comments` array. Each finding gets a `path` + `line` anchor.
- **Line numbers from the wrong side of the diff:** GitHub expects line numbers in the NEW file version (right side of diff), not hunk offsets. The subagent's output MUST use new-file line numbers. When in doubt, fetch the file at the PR's head SHA via `gh api repos/.../contents/{path}?ref={head_sha}` and grep for the anchor.
- **Rebased branches:** incremental diff may be empty after a force-push. Always fall back to full review when delta is empty.
- **Draft PRs:** always confirm before reviewing drafts in inbox mode.
- **Reviewing generated files:** always filter them out via the Step 4 exclusion list.
- **Own PRs:** skip silently in inbox mode; warn in single-PR mode before proceeding.
- **CI failures duplicated as findings:** CI status goes in the header — only create a finding if the root cause is visible in the diff.
- **Shell-interpolating comment bodies:** code review comments contain backticks, fences, and newlines. Use Python/jq + `--input file.json`, not `gh api -f body=...`.
