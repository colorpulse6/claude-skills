---
name: pr-respond
description: >-
  Address review comments on your own PR via an interactive walkthrough.
  Fetches unresolved comment threads, walks through them one at a time, lets
  you choose Fix / Push back / Defer / Skip per comment, dispatches an
  implementer subagent for each Fix, batches the fixes into one commit, posts
  replies (with commit SHA for fixes, reasoning for push-backs), and resolves
  the threads. Use when the user says "respond to PR comments", "address the
  review", "respond to feedback on PR 42", or invokes /pr-respond.
user-invocable: true
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Agent, TodoWrite
---

# PR Respond

Interactive walkthrough for addressing review comments on your own PRs.

> **CRITICAL:** Never implement code changes without explicit user approval of the decision (Fix). Fully automated fixing is out of scope — this skill exists to give the author control while automating the mechanical parts (dispatching implementers, batching commits, replying, resolving).

## Arguments

- `/pr-respond 42` — respond to comments on PR #42
- `/pr-respond https://github.com/owner/repo/pull/42` — by URL
- `/pr-respond` — inbox mode: find open PRs you authored that have unresolved review comments

---

## Step 1: Parse Input & Determine Mode

### Single PR mode (argument provided)

Extract PR number from argument or URL.

### Inbox mode (no argument)

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
YOUR_LOGIN=$(gh api user --jq '.login')
gh search prs --author=@me --repo="$REPO" --state=open \
  --json number,title,url
```

For each PR, count unresolved threads via GraphQL:

```bash
gh api graphql -f query="
{
  repository(owner: \"$OWNER\", name: \"$REPO\") {
    pullRequest(number: $NUMBER) {
      reviewThreads(first: 50) {
        nodes { isResolved }
      }
    }
  }
}" --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
```

Show summary and prompt:

```
📬 Found {COUNT} of your PRs with unresolved review threads:

 #  | PR                                | Unresolved
----|-----------------------------------|------------
 1  | #{NUM} {TITLE}                    | {COUNT}

Which PR? (number / none)
```

If no PRs with unresolved threads:

```
📭 No PRs with unresolved review comments on {REPO}.
```

Stop.

---

## Step 2: Fetch PR Context & Unresolved Threads

```bash
# PR metadata
gh pr view {NUMBER} --json title,author,headRefOid,headRefName,url

# Unresolved review threads via GraphQL
gh api graphql -f query="
{
  repository(owner: \"$OWNER\", name: \"$REPO\") {
    pullRequest(number: $NUMBER) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 10) {
            nodes {
              id
              databaseId
              body
              path
              line
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}"
```

Filter to threads where `isResolved == false`. For each thread, the **first comment** is the original review comment. Subsequent comments are the reply chain.

### Ownership check

If the PR's `author.login !== $YOUR_LOGIN`:

```
⚠️ This PR is not yours. Use /pr-review to review someone else's PR.
```

Stop unless user insists.

### Self-authored thread filter

Exclude threads where the first comment's author is you — those are usually your own replies, not things to address. Keep threads where the first comment is from another reviewer (human or bot).

If there are **zero** unresolved external threads:

```
✅ PR #{NUMBER} has no unresolved review comments to address.
```

Stop.

---

## Step 3: Pre-flight Git State Check

Before starting the walkthrough, verify the working tree is clean:

```bash
git status --short
git branch --show-current
```

If there are uncommitted changes:

```
⚠️ Working tree has uncommitted changes:
{LIST}

Options:
  (S)tash    — stash changes, continue, unstash at end
  (A)bort    — stop and let you handle it
```

If the current branch doesn't match the PR's `headRefName`:

```
⚠️ Current branch is {CURRENT}, but PR #{NUMBER} is on {PR_BRANCH}.

(C)heckout {PR_BRANCH} / (A)bort?
```

---

## Step 4: Present Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR #{NUMBER} — {TITLE}
Branch: {HEAD_REF}
Unresolved threads: {COUNT}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 #  | Severity | File:Line                       | Summary
----|----------|---------------------------------|-------------------------
 1  | 🔴       | {PATH}:{LINE}                   | {FIRST_LINE}
 2  | 🟡       | {PATH}:{LINE}                   | {FIRST_LINE}

Walk through each thread? (y/n)
```

**Severity detection:** Parse the first line of the comment body. If it starts with a severity emoji (🔴 🟡 ⚪) or a keyword (`Critical`, `Important`, `Minor`), use that. Otherwise default to ⚪ Minor (conservative — the user sees the full body anyway and can escalate via Fix).

If **n**, stop.

---

## Step 5: Finding-by-Finding Walkthrough

Use TodoWrite to track progress if there are 5+ threads.

For each unresolved thread, present:

```
[{INDEX}/{TOTAL}] {SEVERITY_EMOJI} {TITLE}
File: {PATH}:{LINE}
Author: {REVIEWER}

{COMMENT_BODY}

What do you want to do?
  (F)ix        — dispatch implementer subagent to address this
  (P)ush back  — reply with your reasoning, resolve thread
  (D)efer      — reply with "deferred", leave thread open
  (S)kip       — leave thread as-is, no reply, no resolve
  (E)xplain    — show surrounding file context, keep asking
```

**Actions:**

- **Fix (f):** Queue this thread for fixing. Do NOT dispatch the implementer yet — batch all fixes and dispatch them in Step 6. Store the thread id, file, line, comment body, and the full comment for context.

- **Push back (p):** Ask for the reasoning text:
  ```
  Enter your reply (multi-line ok, empty line to finish):
  ```
  Queue a reply with the user's text, and mark the thread for resolution.

- **Defer (d):** Ask for an optional reason (TODO link, blocker, etc.). Queue a reply with `⏸️ Deferred: {reason}`, do NOT resolve.

- **Skip (s):** No-op. Do not reply, do not resolve. Log it so the final summary can show which threads were skipped.

- **Explain (e):** Read the file around `{LINE}` (20 lines of context), show it, then re-prompt for the action.

**Progress indicator:**
```
✓ 1/7 — Fix queued
✓ 2/7 — Push back queued
→ 3/7 — Current
○ 4/7 — Pending
```

---

## Step 6: Batch Implementation (Fix threads)

If at least one thread was marked Fix, dispatch **one implementer subagent** with all queued fixes. Do not dispatch one per fix — a single subagent implementing multiple related fixes produces a cleaner commit and lets the subagent spot cross-file duplication.

### Auto-detect type check command

Before dispatching, detect the type check command:

```bash
# Find package manager
if [ -f "pnpm-lock.yaml" ]; then PKG="pnpm"
elif [ -f "yarn.lock" ]; then PKG="yarn"
elif [ -f "package-lock.json" ]; then PKG="npm"
fi

# Detect available scripts
if [ -f "package.json" ]; then
  if grep -q '"check-types"' package.json; then TC_CMD="$PKG run check-types"
  elif grep -q '"typecheck"' package.json; then TC_CMD="$PKG run typecheck"
  elif grep -q '"type-check"' package.json; then TC_CMD="$PKG run type-check"
  else
    # Fall back to finding tsconfig.json at root
    [ -f "tsconfig.json" ] && TC_CMD="$PKG exec tsc --noEmit"
  fi
fi
```

Also detect the test command similarly (`test` script in package.json).

### Dispatch format

```
You are implementing PR review fixes for branch {BRANCH}.

Working directory: {REPO_ROOT}
Branch: {BRANCH}

The PR author accepted the following review findings. Implement each fix.

## Finding 1

**Reviewer:** {AUTHOR}
**File:** {PATH}:{LINE}
**Comment:**
{COMMENT_BODY}

## Finding 2
...

## Constraints

- Read each file before editing it
- Follow the project's existing code style and conventions
- Use the project's lint/format tools if configured
- Run `{TC_CMD}` after implementing all fixes to verify types are clean
- Do NOT commit — the parent controller will batch the commit after verification

Report back with:
- **Status:** DONE | BLOCKED
- What you implemented per finding
- Files changed
- Any findings you could not address (with reason)
```

### After implementer returns

- If any finding reported as BLOCKED, surface to the user and ask whether to Push back or Defer instead.
- Run type check: `{TC_CMD}`. If it fails, show the error and ask the user:
  1. Re-dispatch with error context
  2. Abort all fixes and `git reset --hard {PREV_SHA}`
  3. Proceed anyway (strongly discouraged)

---

## Step 7: Review Diff Before Commit

Before committing, show the user the staged diff:

```bash
git add -A
git diff --cached --stat
```

Then ask:

```
Review the full diff? (y/n/show-file <path>)
```

- `y` → `git diff --cached` (paginated if large)
- `n` → proceed to commit
- `show-file <path>` → `git diff --cached -- {path}` for a specific file

After review:

```
Proceed with commit? (Y/n)
```

If **n**, ask whether to:
1. Re-dispatch the implementer with feedback
2. Abort and `git reset` (uncommit the staging)

---

## Step 8: Batch Commit

Create a single commit with an AI-generated message summarizing the fixes.

```bash
git commit -m "$(cat <<'EOF'
fix: address PR review findings

{BULLET_PER_FIX}

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

Each bullet is one sentence describing the fix. Order by severity: Critical → Important → Minor.

Then push:

```bash
git push
```

Capture the new commit SHA:

```bash
NEW_SHA=$(git rev-parse HEAD)
```

---

## Step 9: Post Replies

For each thread, post a reply to the original comment thread. Use the REST API's `in_reply_to` field.

### Reply templates

**Fix reply (default):**

````markdown
Fixed in {NEW_SHA_SHORT}. {IMPLEMENTATION_NOTE}

See [{FILE}:{LINE}](https://github.com/{OWNER}/{REPO}/blob/{NEW_SHA}/{FILE}#L{LINE}).
````

- `{NEW_SHA_SHORT}` is the first 7 characters of the SHA
- `{IMPLEMENTATION_NOTE}` is a 1-2 sentence summary of what the fix does, based on the implementer's report
- Include a link to the specific line in the new commit so the reviewer can jump straight to the fix

Before posting each Fix reply, offer customization:

```
Reply preview:
  {PREVIEW}

(P)ost as-is / (C)ustomize / (S)kip reply?
```

- **Customize:** let the user rewrite the reply text (keeping the SHA link at the bottom)
- **Skip reply:** still resolves the thread but doesn't post anything

**Push back reply:**

````markdown
{USER_REASONING}
````

- Use the user's text verbatim. No skill-authored preamble.

**Defer reply:**

````markdown
⏸️ Deferred: {USER_REASON}
````

### Posting

```bash
gh api repos/{OWNER}/{REPO}/pulls/{NUMBER}/comments \
  --method POST \
  --field body="{REPLY_BODY}" \
  --field in_reply_to={ORIGINAL_COMMENT_ID}
```

The `in_reply_to` is the `databaseId` of the **first comment** in the thread (not the thread node ID). These are different IDs — use the numeric REST ID.

---

## Step 10: Resolve Threads

For each thread marked Fix or Push back (NOT Defer or Skip), resolve it:

```bash
gh api graphql -f query="
mutation {
  resolveReviewThread(input: { threadId: \"{THREAD_NODE_ID}\" }) {
    thread { id isResolved }
  }
}"
```

**Resolution rules:**
- **Fix:** resolve (the fix is in the branch)
- **Push back:** resolve (the reviewer's concern was addressed via discussion)
- **Defer:** leave open (there's still outstanding work)
- **Skip:** leave open (no action taken)

---

## Step 11: Session Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PR #{NUMBER} review response complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 #  | Action         | File:Line                | Status
----|----------------|--------------------------|---------
 1  | ✅ Fixed        | {PATH}:{LINE}            | Resolved
 2  | 💬 Pushed back  | {PATH}:{LINE}            | Resolved
 3  | ⏸️  Deferred    | {PATH}:{LINE}            | Open
 4  | ⏭️  Skipped     | {PATH}:{LINE}            | Open

Commit: {NEW_SHA_SHORT} — {NEW_SHA}
URL: {PR_URL}
```

If changes were stashed in Step 3, restore them now:

```bash
git stash pop
```

---

## Edge Cases

1. **PR has uncommitted changes on the working tree before you start.** Step 3 handles this — stash or abort.

2. **Push fails (rebased, conflict).** Surface the error, show `git status`, ask the user how to proceed. Do not force-push.

3. **Type check fails after fix.** Show errors, ask: (1) re-dispatch implementer with error context, (2) abort all fixes and revert, (3) proceed anyway (strongly discouraged).

4. **Thread has multiple comments already (chain of replies).** The skill still posts a new reply to the chain using `in_reply_to` on the original comment. Do not try to reply to nested replies — GitHub's API threads all replies off the original comment.

5. **Comment body is empty or unparseable.** Default severity to ⚪, use "Review comment" as the title, show the raw body in the walkthrough.

6. **Multi-package monorepo with multiple tsconfigs.** The auto-detected type check command might not cover all packages. If the implementer touches files outside the default tsconfig scope, run `turbo run check-types` or equivalent if available.

7. **Branch checkout in Step 3 fails because of conflicts.** Abort and let the user resolve manually.

---

## Common Mistakes to Avoid

1. **Implementing fixes before the user accepts them in the walkthrough.** Always queue, never execute during Step 5.
2. **Using `in_reply_to` with the thread node ID instead of the first comment's `databaseId`.** These are different IDs — use the numeric REST ID.
3. **Resolving Defer or Skip threads.** The whole point of those actions is to leave the thread visible for future work.
4. **Force-pushing to the PR branch.** Never. If push fails, ask the user.
5. **Dispatching one implementer per fix.** Always batch into one implementer call per session so the subagent can spot cross-file patterns and produce a single coherent commit.
6. **Replying with "Fixed in HEAD" or a branch name.** Use the absolute commit SHA so the reviewer's link is stable forever.
7. **Skipping the ownership check.** This skill is for your own PRs — if someone else is the author, point them at `/pr-review` and stop.
8. **Skipping the diff review (Step 7).** The user should see what's being committed before it lands on the remote.
