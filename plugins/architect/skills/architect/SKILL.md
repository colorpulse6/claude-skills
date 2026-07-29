---
name: architect
description: >-
  Frontier-model-plans, cheap-model-executes delegation loop across both
  Claude and Codex. The expensive model writes a decision-complete spec, then
  routes each slice by model family strength (Claude for long-context
  multi-file work, Codex for terminal-native work) and cost tier, enforces a
  cross-family implementer/reviewer split, balances load across providers, and
  accepts work only by verified evidence — spending frontier tokens on
  judgment, not typing. Use when the user says "architect this", "spec it and
  delegate", "plan expensive execute cheap", "split this across Claude and
  Codex", "use both providers", or invokes /architect <task>.
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
is a false economy. What the second lane *costs* depends on how each provider
is billed, which varies by installation.

**The routing tables are inline in Step 2** — that is the single source of
truth for which family and which tier. `references/spec-contract.md` holds the
evidence behind each row, the metering-detection table, and the balance rule;
reach for it when a routing call is contested, not to make a routine one.

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

Pick the lane in two moves. **Both tables are here, inline, because every
dispatch consults them** — do not dispatch from memory of what a family is
"probably" good at.

**1. Family — from strengths:**

| Work | Family |
|---|---|
| Planning, spec-writing, premise rejection | Claude |
| Multi-file changes where the dependency graph matters | Claude |
| Large real-repo tasks | Claude |
| Code a human will read and maintain | Claude |
| Terminal-native — scripts, sysadmin, CI/CD, migrations | **Codex** |
| Algorithmic / self-contained problems | **Codex** |
| High-volume mechanical transforms | **Codex** |
| Reviewing anything | whichever family did **not** write it |

Tied on the table ⇒ the provider dispatched to less this session (see the
balance rule in `references/spec-contract.md`; the tiebreak inverts under API
billing).

These rows are **directional, not measured** — secondary benchmark reports on
the previous model generation, with provenance marked per row in
`references/spec-contract.md`. The terminal-native row has the widest margin
and the most confidence; "planning → Claude" is the weakest, an inherited
assumption no source was found for. Evidence from your own runs outranks this
table the moment you have any.

**2. Tier and invocation:**

| Weight | Claude | Codex |
|---|---|---|
| Mechanical | `haiku` | `codex exec -m gpt-5.6-luna --sandbox workspace-write "$(cat ".architect/spec-<slug>.md")" < /dev/null` |
| Ordinary | `sonnet` | `codex exec -m gpt-5.6-terra --sandbox workspace-write "$(cat ".architect/spec-<slug>.md")" < /dev/null` |
| Hard (escalation) | `opus` | `codex exec -m gpt-5.6-sol --sandbox workspace-write "$(cat ".architect/spec-<slug>.md")" < /dev/null` |
| Review | fresh-context subagent | `codex exec -m gpt-5.6-sol --sandbox read-only "$(cat ".architect/review-<slice>.md")" < /dev/null` |

`<slug>` is the spec you wrote in Step 1; `<slice>` is the reviewer brief you
write in Step 3. These are the canonical paths this skill creates — substitute
the real names, and do not invent a bare `spec.md`, which nothing produces.

Note the two `sol` rows differ only in sandbox: **`workspace-write` to build,
`read-only` to review.** A reviewer that can edit is not a reviewer.

**Escalation is deliberate, never a default.** The whole thesis is that
flagship tokens buy judgment, not typing — so reach for the hard row only
when: the ordinary lane returned `FAILED` with evidence the slice exceeded it,
or the slice is known upfront to need frontier reasoning *during*
implementation (a subtle migration, an algorithm the spec can only describe).
A slice that merely has many files is not hard; that is ordinary work, and
`terra`/`sonnet` handle it. State the escalation and its trigger in the report
— an unexplained flagship executor is the cost failure this skill exists to
prevent.

Codex model ids are generation-qualified — the bare tier name (`terra`)
returns a 400. `< /dev/null` is mandatory or the stdin probe hangs. Full lane
table, failure modes, and metering detection: `references/spec-contract.md`.

**If this run dispatches only one family, say why in the report.** A run that
silently routes everything to the harness's default model has not routed at
all — that is the failure this step exists to prevent.

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
named lane — family and tier both stated, with the table row that decided the
family — or explicitly recorded as executed inline. None left implicit, and no
slice dispatched without naming its family first.

## Step 3: Adversarial review (fresh context)

Spawn a reviewer that gets the **spec + the diff only** — never the
implementer's notes or self-assessment. Brief it to falsify: "find where this
violates the spec or breaks," not "approve this."

**The reviewer is always the family that did not write the code** — different
blind spots is the whole value, and a same-family reviewer shares the author's
errors.

**Review per slice, not per diff.** When slices went to different families,
one reviewer cannot satisfy the invariant for the whole change — neither
family is foreign to all of it. Review each slice with the family that did not
write *that* slice, in parallel. Only slices sharing an author can share a
reviewer. When a slice's boundaries are unclear in the combined diff, pass the
reviewer the paths that slice owns (they're already named in the spec's output
contract).

- Claude wrote the slice → fresh-context Claude is the floor; prefer Codex:
  ```bash
  codex exec -m gpt-5.6-sol --sandbox read-only "$(cat ".architect/review-<slice>.md")" < /dev/null
  ```
  where `review-<slice>.md` is the reviewer brief from
  `references/spec-contract.md` with the spec section and that slice's diff
  inlined — the reviewer gets no other context, and the `< /dev/null` is
  mandatory or the stdin probe hangs.
- Codex wrote the slice → a fresh-context Claude subagent, same brief.

Same-family review is the floor, used only when the other provider is
unavailable — say so explicitly when it happens.

This also balances the ledger for free: whichever family executed a slice, the
other one reviews it.

For consequential changes, run two reviewers per slice and reconcile by
convergence.

**Completion criterion:** every slice has a review verdict from a family that
did not author it, or a recorded reason why that was impossible.

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
report comparably, so the count is the signal. Name the metering regime you
determined (see `references/spec-contract.md`), since it decides which way
"lean the other way" points. If any lane was forced (rate limit, quota,
missing CLI) rather than chosen, mark it in the ledger.

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
