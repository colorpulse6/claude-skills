---
name: review-board
description: >-
  Multi-lens, multi-model review conductor. Audits a diff/PR/branch by spawning
  several scoped Claude review agents in parallel (security, concurrency,
  performance, API-contract) WHILE a separate model (Codex) reviews
  independently, then reconciles every finding into one cross-model table:
  convergence (high-confidence), net-new-from-Codex (verify), and sharpened
  disagreements. Use when user says "review board", "full review", "multi-lens
  review", "audit this with all the models", or invokes /review-board.
user-invocable: true
argument-hint: "[PR number | branch | (default: working diff)]"
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
---

# Review Board

Conducts a panel review of a change: N **Claude lens agents** run in parallel,
each scoped to one failure-class, **while** a **separate model** (Codex) runs an
independent review. Their findings are reconciled into a single ranked verdict.

The value is two kinds of diversity at once: **lens diversity** (each Claude
agent only looks for one class of bug, so nothing is "averaged away") and
**model diversity** (a different model has different blind spots). Running Codex
*concurrently* with the lenses hides its latency behind work you were doing
anyway.

> Pairs with the `codex-second-opinion` plugin. If that skill / the Codex CLI is
> not present, this skill still runs Claude-only and says so.

---

## Step 1: Resolve the target & the diff

- **PR number / URL** → check it out / fetch the diff.
- **Branch name** → diff against the merge base with the default branch.
- **No argument** → review the working diff (`git diff` + staged).

Collect the changed-file list and a unified diff:

```bash
git diff --merge-base "$(git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p')" --name-only
```

Fall back to `git diff --name-only HEAD` for the working-tree case. If there are
no changes, stop and say so. Create the run dir: `./.review-board-out/findings/`.

## Step 2: Choose the lenses

Default lenses (one parallel agent each):

| Lens | Looks only for |
|------|----------------|
| `security` | injection, authz/authn gaps, secret handling, SSRF, unsafe deserialization |
| `concurrency` | races, async-timing, process lifecycle, lock/ordering, idempotency |
| `performance` | N+1s, unbounded work, allocation hotspots, blocking calls on hot paths |
| `contract` | API/schema/type drift across layers, breaking changes, nullability |

Read the full checklist for each lens from
`${CLAUDE_PLUGIN_ROOT}/skills/review-board/references/lenses.md`.

> **TEMPLATE:** Add/remove lenses for your stack (e.g. `accessibility`, `i18n`,
> `migration-safety`). Each new lens is just another section in `lenses.md` —
> no new agent file needed; the agent is parameterized.

Skip a lens if no changed file is relevant to it (e.g. skip `contract` when no
schema/type/API files changed). State which lenses you skipped and why.

## Step 3: Launch Codex (separate model) in the BACKGROUND first

So it runs concurrently with the Claude lenses:

1. Check availability: `which codex`. If absent → skip this branch, note it,
   continue to Step 4.
2. If the `codex-second-opinion` skill is installed, **follow its workflow** to
   build the neutral brief and run it. Otherwise, build the brief inline:
   write a self-contained `/tmp/review-board-codex-brief.md` that (a) describes
   the change, (b) gives a file map with line hints, (c) lists invariants to
   verify, (d) asks for **independent findings first, then confirm/refute**, and
   (e) says **read-only, do not edit**.
3. Run it backgrounded so it doesn't block the lenses:

   ```bash
   cd <repo-root>
   codex exec --sandbox read-only "$(cat /tmp/review-board-codex-brief.md)" > ./.review-board-out/codex.out 2>&1 &
   ```

Do not wait on it yet.

## Step 4: Fan out the Claude lens agents — in parallel

Spawn one `review-lens` subagent **per chosen lens, all in a single message** so
they run concurrently (and concurrently with Codex). Give each:

- `lens` — the lens name (e.g. `security`),
- `checklist` — that lens's section from `lenses.md`,
- `changed_files` + the diff,
- `output_dir` = `./.review-board-out/findings/`.

Each writes `findings/<lens>.md` (findings table) and returns a one-line summary.
Do **not** perform the lens analysis yourself — that defeats lens isolation.

## Step 5: Collect Codex, then reconcile

- Wait for the backgrounded Codex run; read only its final synthesis:
  ```bash
  awk '/^codex$/{last=NR} END{print last}' ./.review-board-out/codex.out
  ```
  then read from that line. (Skip if Codex was unavailable.)
- Read every `findings/<lens>.md`.
- Reconcile into `./.review-board-out/REVIEW-BOARD.md` per the contract below.

## Step 6: Report

Print the path to `REVIEW-BOARD.md` and the headline: convergence count, net-new
count, and the single highest-severity item. Done. (If invoked on a PR and the
user wants it posted, hand off to `pr-review` rather than posting here.)

---

## Output contract — `REVIEW-BOARD.md`

In this order:

1. **Verdict** — one paragraph: ship / fix-first / needs-discussion + why.
2. **Cross-model table** — `| Finding | Severity | Lenses (Claude) | Codex | Your verification |`.
3. **Convergence** — items flagged independently by ≥2 sources. Lead here; highest confidence.
4. **Net-new from Codex** — what only the separate model caught. **Mark each "verify in code" — a different model is a strong signal, not gospel.**
5. **Disagreements / partly-confirmed** — where sources differ; include Codex's evidence, which often *sharpens* a claim rather than negating it.
6. **Per-lens detail** — each `findings/<lens>.md` verbatim under an `## <lens>` heading.

## Error handling

| Scenario | Action |
|----------|--------|
| No changes in target | Stop; tell the user the diff was empty. |
| Codex CLI absent / `codex-second-opinion` not installed | Run Claude-only; mark the Codex column "n/a" and note model diversity was not achieved. |
| Codex run errors / times out | Note it in the verdict; reconcile the Claude lenses; don't fail the whole review. |
| A lens agent writes no file | Note the missing lens in the report; reconcile the rest. |
| A lens has no relevant changed files | Skip it; list it under "lenses skipped". |
