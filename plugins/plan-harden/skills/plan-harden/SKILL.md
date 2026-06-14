---
name: plan-harden
description: >-
  Adversarially hardens a design doc / spec / RFC BEFORE coding. Runs a
  pre-mortem (assume it already shipped and failed, enumerate why) plus parallel
  design-review lenses (problem framing, edge cases, failure handling, data
  integrity, rollout/rollback, observability, scaling, dependencies/blast-radius,
  security/STRIDE), then reconciles into a prioritized hardening report with an
  APPROVED/REVISE verdict. Use when user says "harden this plan", "review my
  design/spec/RFC", "pre-mortem this", "poke holes in this design", or invokes
  /plan-harden.
user-invocable: true
argument-hint: "[path to design doc | (default: latest spec in docs/)]"
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
---

# Plan Harden

Pressure-tests a design **before** anyone writes code — the cheapest place to fix
a flaw. It combines a **pre-mortem** (prospective hindsight surfaces ~30% more
risks than "what could go wrong?") with **parallel adversarial lenses**, each a
skeptic for one failure-class.

Stance for the whole skill: **default to skepticism; the burden of proof is on
the design.** A finding is only real if it names a **concrete failure scenario**
(input/state/outcome) — not a hypothetical. "One strong finding beats five weak
ones."

---

## Step 1: Context gate (do NOT skip)

Resolve the design: the path argument, else the newest file under `docs/`,
`docs/specs/`, or `*.md` that reads like a design/RFC. Read it.

Then confirm three things — **ask the user, one question at a time**, only for any
that the doc doesn't already answer:

1. **What is it?** (one sentence)
2. **Who/what is affected if it breaks?** (blast radius)
3. **What does success look like?** (measurable)

Without these, hardening is unanchored. If the doc answers all three, state your
understanding and proceed.

## Step 2: Pick the lenses

Default lenses (one parallel agent each), checklists in
`${CLAUDE_PLUGIN_ROOT}/skills/plan-harden/references/review-checklist.md`:

| Lens | Asks |
|------|------|
| `premortem` | "It's 6 months out, this failed in production. Write the postmortem — why?" |
| `edge-cases` | empty/null/max/duplicate/concurrent/out-of-order/partial inputs & states |
| `failure-handling` | timeouts, retries+backoff, idempotency, backpressure, degraded mode |
| `data-integrity` | consistency model, partial-write recovery, reconciliation, data loss |
| `rollout-rollback` | canary/flags, reversible migrations (expand→contract), tested rollback |
| `observability` | SLIs/SLOs, "which failures would be invisible for 48h?", alerts/runbook |
| `scaling` | load assumptions, what breaks at 10x, unbounded growth, hot keys |
| `security` | STRIDE over the data flow, trust boundaries, authz, secrets, abuse cases |
| `dependencies` | each dependency's failure mode, blast radius, SPOFs, cost |

> **TEMPLATE:** add/cut lenses per project. Each is a section in
> `review-checklist.md`; the agent is parameterized — no new agent file needed.
> Drop a lens the design genuinely doesn't touch (state which and why).

## Step 3: Fan out the lens agents — in parallel

Spawn one `design-lens` subagent **per lens, all in one message**. Give each
(inline, don't make it hunt): the **full design text**, its `lens` + `checklist`,
the Step-1 context, and `output_dir` = `./.plan-harden-out/findings/`.

Each writes `findings/<lens>.md` and returns a status line:
`<lens>: <DONE|DONE_WITH_CONCERNS|BLOCKED> — N findings (k blocking)`.

Right-size the fan-out to the design's size; don't spawn lenses for sections that
don't exist.

## Step 4: Reconcile

Read all `findings/<lens>.md`. Before accepting a finding, sanity-check it against
the doc yourself (distrust the report — a lens can over-flag). Merge into
`./.plan-harden-out/HARDENING-REPORT.md` per the contract below. De-dupe items
multiple lenses raised and label them `[CONSENSUS]` (highest confidence).

## Step 5: Verdict

Print the verdict + the single most dangerous failure mode. If `REVISE`, list the
blocking items the design must address before coding starts.

---

## Output contract — `HARDENING-REPORT.md`

1. **Verdict** — `APPROVED` (no blocking gaps) or `REVISE` (blocking gaps exist) + one-line reasoning.
2. **Five-part synthesis:** most-likely failure · most-dangerous failure · riskiest hidden assumption · concrete plan changes · a 3–5 item pre-launch checklist.
3. **Findings table** — `| Lens | Severity | Failure scenario | Assumption it rests on | Early warning sign | Fix |`. Severity: Blocking / Important / Minor. Tag `[CONSENSUS]` where lenses overlap.
4. **Per-lens detail** — each `findings/<lens>.md` verbatim under `## <lens>`.

All findings are `[PLAN_RISK]` (prospective), never `[EXISTING_DEFECT]` — this skill reviews a design, not code.

## Error handling

| Scenario | Action |
|----------|--------|
| No design doc found | Ask the user for the path or paste; don't guess. |
| Context gate unanswered | Ask one question at a time; don't proceed blind. |
| A lens agent BLOCKED / no file | Note the gap in the report; reconcile the rest. |
| Design is trivial / one-pager | Run `premortem` + `edge-cases` only; say you scoped down. |
| Lens has nothing to flag | Record "no blocking gaps" — a clean lens is a valid result. |
