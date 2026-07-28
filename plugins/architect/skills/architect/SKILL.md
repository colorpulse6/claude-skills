---
name: architect
description: >-
  Frontier-model-plans, cheap-model-executes delegation loop across both
  Claude and Codex. The expensive model writes a decision-complete spec, then
  routes each slice by model family strength (Claude for long-context
  multi-file work, Codex for terminal-native work) and cost tier, enforces a
  cross-family implementer/reviewer split, balances load across the two
  subscriptions, and accepts work only by verified evidence — spending
  frontier tokens on judgment, not typing. Use when the user says "architect
  this", "spec it and delegate", "plan expensive execute cheap", "split this
  across Claude and Codex", "use both providers", or invokes /architect
  <task>.
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

Routing runs on **two axes, not one**. Cost tier answers *how much model*;
family answers *which model*. The families diverge sharply by task type —
Claude leads on long-context multi-file work and code quality, Codex leads on
terminal-native work by a 12-point margin — so a cheap lane in the wrong family
is a false economy. Both are subscription-metered here, which makes provider
**headroom**, not dollars, the resource actually being spent. See
`references/spec-contract.md` for the strengths table and the balance rule.

Four rules that make it work, the first three inherited from systems that ran
this at scale:

1. **The spec is decision-complete.** Every fork is decided in the spec, with
   the tradeoff named. An executor that has to make an architectural choice is
   evidence the spec failed — fix the spec, not the executor.
2. **Implementer never reviews; reviewer never implements.** Fresh contexts on
   each side. Self-review by the implementer is not review.
3. **Lanes fail loudly.** If a lane is unavailable (no Codex CLI, no cheap
   model, a provider rate-limited mid-run), say so and choose openly — never
   silently substitute.
4. **Strength picks the lane; balance breaks the tie.** Route by what the
   family is good at. Only when two lanes are genuinely tied does the
   less-used provider win — never send work to the wrong family to even out
   a ledger.

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

## Step 2: Dispatch the executor

Pick the lane in two moves, using `references/spec-contract.md`:

1. **Family, from the strengths table.** Terminal-native work (scripts, CI,
   migrations, sysadmin) → Codex. Multi-file changes where the dependency
   graph matters, or code a human will maintain → Claude. Tied → the provider
   you've dispatched to less this session.
2. **Tier, from the lane table.** Mechanical → `haiku` / `gpt-5.6-luna`.
   Ordinary implementation → `sonnet` / `gpt-5.6-terra`. Codex model ids are
   generation-qualified; the bare tier name returns a 400.

State the chosen lane and the axis that decided it, in one line, before
dispatching. The executor receives the spec file content and NOTHING else —
not your reasoning, not this conversation. It must report status as `DONE` /
`BLOCKED: <missing decision>` / `FAILED: <evidence>`, and its claim rung (see
Step 4).

Independent slices → multiple executors in a single message, one spec section
each. Slices that differ in kind (a migration script and a React component)
should go to different families by the same rule — that is the cheapest
balancing there is, since it costs nothing in quality.

**Completion criterion:** every slice in the spec has been dispatched to a
named lane, or explicitly recorded as executed inline — none left implicit.

## Step 3: Adversarial review (fresh context)

Spawn a reviewer that gets the **spec + the diff only** — never the
implementer's notes or self-assessment. Brief it to falsify: "find where this
violates the spec or breaks," not "approve this."

**The reviewer is always the family that did not write the code.** Different
blind spots is the whole value; a same-family reviewer shares the author's
errors. Claude built it → `codex exec -m gpt-5.6-sol --sandbox read-only`.
Codex built it → a fresh-context Claude subagent. A same-family fresh context
is the floor, used only when the other provider is unavailable — and say so
when that happens.

This also balances the ledger for free: whichever family executed, the other
one reviews.

For consequential changes, run two reviewers and reconcile by convergence.

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

Outcome first; then review findings and how each was resolved, the claim rung
of the final state with its evidence, and residual risks. The spec file stays
in `.architect/` as the audit trail.

Include a **balance ledger** — one line, dispatches per family:

```
lanes: Claude 3 (opus plan, sonnet ×2 impl) · Codex 2 (terra migration, sol review)
```

Its job is to make a lopsided run visible so the next one can lean the other
way. Do not attempt token or dollar accounting — the two providers don't
report comparably, and both are subscription-metered here, so the count is the
signal. If any lane was forced (rate limit, missing CLI) rather than chosen,
mark it in the ledger.

## Error handling

| Scenario | Action |
|----------|--------|
| No cheap lane available at all | Execute inline yourself, keeping the spec + review + ladder discipline. The routing is an optimization; the discipline is the point. |
| Executor returns BLOCKED | The spec was not decision-complete. Decide the missing fork, amend the spec file, re-dispatch. Never let the executor guess. |
| Same failure twice after rework | Stop the loop; re-map and re-spec. Two identical failures mean the model of the system is wrong, not unlucky. |
| Reviewer and executor disagree | The disagreement is a finding: resolve it yourself against the code, don't average. |
| Task below the threshold | Say so and do it directly — ceremony on a one-liner is waste. |
| Codex 400: "model is not supported" | The model id lost its generation prefix. Pass the full id (`gpt-5.6-terra`), not the bare tier (`terra`). Check `model` in `~/.codex/config.toml` for the current generation. |
| Codex: "Not inside a trusted directory" | `codex exec` refuses outside a git repo. Add `--skip-git-repo-check`, or dispatch from within the repo. |
| One provider rate-limited mid-run | `LANE UNAVAILABLE` — re-route by the strengths table, finish the run, and mark the forced lane in the balance ledger. Never stall waiting for a cap to reset. |
