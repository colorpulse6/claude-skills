---
name: architect
description: >-
  Frontier-model-plans, cheap-model-executes delegation loop. The expensive
  model writes a decision-complete spec, dispatches implementation to a cheap
  lane (cheaper Claude subagent or Codex CLI), enforces an implementer/reviewer
  split with fresh-context adversarial review, and accepts work only by
  verified evidence — spending frontier tokens on judgment, not typing. Use
  when the user says "architect this", "spec it and delegate", "plan expensive
  execute cheap", "have the big model plan and a cheap model build", or invokes
  /architect <task>.
user-invocable: true
argument-hint: "[the task to architect and delegate]"
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
---

# Architect

The evidence behind this pattern: controlled comparisons show frontier models
win decisively at *planning* (decision quality, edge-case discovery, premise
rejection) while execution of a good spec is quality-identical on far cheaper
models. So: judgment upstairs, typing downstairs — and a review structure that
doesn't let the two blur.

Three rules that make it work, all inherited from systems that ran this at
scale:

1. **The spec is decision-complete.** Every fork is decided in the spec, with
   the tradeoff named. An executor that has to make an architectural choice is
   evidence the spec failed — fix the spec, not the executor.
2. **Implementer never reviews; reviewer never implements.** Fresh contexts on
   each side. Self-review by the implementer is not review.
3. **Lanes fail loudly.** If a lane is unavailable (no Codex CLI, no cheap
   model), say so and choose openly — never silently substitute.

## Step 0: Qualify

If the task is small (< ~30 min of implementation, one or two files), skip the
ceremony: say the task is below the delegation threshold and just do it. The
loop pays for itself on multi-file changes, migrations, and parallelizable
slices — not on one-liners.

## Step 1: Map, then write the spec

Read the load-bearing files yourself (never spec from a summary). Then write
the spec to `.architect/spec-<slug>.md` using the five-part contract in
`references/spec-contract.md` — context, task, constraints, output contract,
done criteria. Run its decision-completeness checklist before dispatch: the
test is *"could a competent stranger with no access to this conversation
execute this?"*

## Step 2: Dispatch the executor (cheap lane)

Pick a lane from the table in `references/spec-contract.md` (cheaper Claude
subagent via the Agent tool with a model override; or Codex CLI — always with
`< /dev/null` on backgrounded runs). The executor receives the spec file
content and NOTHING else — not your reasoning, not this conversation. It must
report status as `DONE` / `BLOCKED: <missing decision>` / `FAILED: <evidence>`,
and its claim rung (see Step 4).

Independent slices → multiple executors in a single message, one spec section
each.

## Step 3: Adversarial review (fresh context)

Spawn a reviewer that gets the **spec + the diff only** — never the
implementer's notes or self-assessment. Brief it to falsify: "find where this
violates the spec or breaks," not "approve this." A different model family
(Codex lane) is the strongest reviewer when available; a fresh-context Claude
subagent is the floor. For consequential changes, run two reviewers and
reconcile by convergence.

## Step 4: Accept by the claim ladder

Work is accepted at a rung, never on vibes:

- **WRITTEN** — code exists. Not evidence of anything.
- **RUNS** — executed without error. Still not correctness.
- **VERIFIED** — the done-criteria commands from the spec pass, run or
  re-run by *you*, the architect.

Only VERIFIED is acceptance. Accepting anything lower is an explicit,
stated decision with a residual-risk note. Rework loop: send spec-violation
findings back with the spec unchanged; if the same failure recurs twice,
stop — the spec is wrong somewhere. Re-enter Step 1.

## Step 5: Report

Outcome first; then what ran on which lane (and rough cost split), review
findings and how each was resolved, the claim rung of the final state with
its evidence, and residual risks. The spec file stays in `.architect/` as the
audit trail.

## Error handling

| Scenario | Action |
|----------|--------|
| No cheap lane available at all | Execute inline yourself, keeping the spec + review + ladder discipline. The routing is an optimization; the discipline is the point. |
| Executor returns BLOCKED | The spec was not decision-complete. Decide the missing fork, amend the spec file, re-dispatch. Never let the executor guess. |
| Same failure twice after rework | Stop the loop; re-map and re-spec. Two identical failures mean the model of the system is wrong, not unlucky. |
| Reviewer and executor disagree | The disagreement is a finding: resolve it yourself against the code, don't average. |
| Task below the threshold | Say so and do it directly — ceremony on a one-liner is waste. |
