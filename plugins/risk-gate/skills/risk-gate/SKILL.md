---
name: risk-gate
description: >-
  Triages a diff/PR/branch by change risk and escalates only the risky parts to
  deeper review. Runs a cheap deterministic scoring pass (danger paths like
  auth/payments/migrations, change size, blast radius, churn) to bucket changed
  files Low/Medium/High, then escalates only HIGH-risk files to a heavyweight
  separate-model review (review-board or codex-second-opinion). Use when user
  says "risk gate", "what's risky here", "triage this diff", "is this safe to
  merge", or invokes /risk-gate.
user-invocable: true
argument-hint: "[PR number | branch | (default: working diff)]"
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
---

# Risk Gate

A **triage-then-escalate** conductor. Most changes are low-risk and don't need a
heavyweight multi-model audit; a few are dangerous and deserve everything you've
got. Risk Gate spends the expensive review **only where it pays** by scoring the
diff cheaply first.

`risk = likelihood-of-failure × impact-of-failure`. The score approximates both:
*impact* from where the change lands (auth, payments, migrations, money/LLM
spend), *likelihood* from how much/complex the change is (churn, size, blast
radius).

---

## Step 1: Resolve the target & score it (cheap, deterministic)

Resolve the diff base (PR / branch / working tree — see `review-board` for the
same resolution), then run the scorer:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/risk-gate/scripts/risk_score.py" [BASE_REF]
```

It emits JSON: per changed file an `added`/`removed` count, a `score`, a `bucket`
(`high`/`medium`/`low`), and the `reasons` that fired. The signals and their
weights are documented in
`${CLAUDE_PLUGIN_ROOT}/skills/risk-gate/references/risk-signals.md` — read it if
you need to explain or tune a score. **Weights are heuristic defaults, not law:**
treat the buckets as a starting point and apply judgment in Step 2.

If there are no changes, stop and say so.

## Step 2: Confirm the buckets (judgment pass)

The script is keyword/size based and will mis-rank some files. Skim the diff for
each `medium`/`high` file and adjust:

- Promote a `low`/`medium` file to `high` if it touches an invariant, a security
  boundary, or irreversible state the keywords missed.
- Demote a `high` file that's a rename, comment, generated artifact, or pure test
  churn.

State the final bucketing and *why anything moved*.

## Step 3: Escalate ONLY the high-risk set

- **No `high` files** → no escalation. Report the risk map, recommend a normal
  review, stop. (This is a valid, common outcome — don't manufacture risk.)
- **Some `high` files** → escalate **just those files** to deep review. Prefer,
  in order of availability:
  1. The `review-board` skill (multi-lens + Codex), scoped to the high-risk files.
  2. Else, the `codex-second-opinion` skill (separate-model) if the Codex CLI is present.
  3. Else, spawn your own parallel Claude lens audit over the high-risk files.

  Pass the deep reviewer **only the high-risk file list** so it doesn't waste the
  expensive run on trivia.

> **TEMPLATE / TUNING:** the escalation threshold and which deep reviewer to call
> are the two knobs you'll adjust. Default threshold = any `high` file.

## Step 4: Report

Write `./.risk-gate-out/RISK-REPORT.md`:

1. **Risk map** — table: `| File | Bucket | Score | Why |`, sorted high→low.
2. **Escalated** — which files went to deep review and the reviewer's verdict.
3. **Gate decision** — one line: `proceed` / `review-then-proceed` / `block until fixed`.

Print the map + decision to the user.

## Error handling

| Scenario | Action |
|----------|--------|
| No changes | Stop; report empty diff. |
| `risk_score.py` errors | Surface stderr; fall back to a manual skim and say the score was unavailable. |
| No deep reviewer available (no review-board / Codex) | Do the Claude lens audit yourself; note reduced model diversity. |
| Deep review finds nothing on a high-risk file | Keep it flagged `review-then-proceed`; a clean deep review lowers, not erases, risk. |
