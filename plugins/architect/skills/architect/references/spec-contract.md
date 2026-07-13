# Spec contract, lanes, and briefs

## Contents
- The five-part spec contract
- Decision-completeness checklist
- Lane table
- Executor dispatch template
- Reviewer brief template

## The five-part spec contract

Same shape as the fable-method delegation brief — one contract across the
whole toolchain, so specs, subagent briefs, and handoffs all read alike.

1. **Context** — everything the executor cannot discover cheaply: paths,
   today's date, the *reason* behind the task (models execute better when they
   know why), relevant invariants, prior findings. Written for a competent
   stranger.
2. **Task** — numbered, concrete deliverables. Every architectural fork
   already decided, with the accepted tradeoff named in one line.
3. **Constraints** — what NOT to do: files not to touch, patterns to match
   (naming, error handling, comment density of the surrounding code),
   dependencies not to add, scope walls.
4. **Output contract** — exact files to create/modify; for each, what done
   looks like. Status enum required: `DONE` / `BLOCKED: <missing decision>` /
   `FAILED: <evidence>` — plus the claim rung (WRITTEN / RUNS / VERIFIED) with
   the evidence for it.
5. **Done criteria** — the literal commands whose passing output constitutes
   done (test command, typecheck, a curl against the changed endpoint). These
   are what the architect re-runs at acceptance.

## Decision-completeness checklist

Run before dispatch; any "no" means the spec isn't ready:

- [ ] Could a stranger execute this without asking a single question?
- [ ] Is every "or" in the spec resolved? ("use X or Y" = an undecided fork)
- [ ] Are edge cases enumerated with expected behavior, not left to taste?
- [ ] Does the executor know what to do when reality contradicts the spec?
      (Answer is always: return `BLOCKED`, never improvise.)
- [ ] Are the done-criteria commands runnable in the executor's environment?

## Lane table

| Lane | How | Use when | Cost/notes |
|---|---|---|---|
| Cheap Claude subagent | Agent tool, `model: sonnet` (or `haiku` for mechanical transforms) | Default executor lane | Runs in-harness, tools available, background-able |
| Codex CLI executor | `codex exec -m <mid-or-speed tier> --sandbox workspace-write "$(cat spec.md)" < /dev/null` | Second model family wanted as executor; Claude capacity constrained | The `< /dev/null` is mandatory on non-TTY/backgrounded runs — stdin probe otherwise blocks forever |
| Codex read-only | `codex exec -m <flagship tier> --sandbox read-only ... < /dev/null` | Reviewer lane (cross-model) | Read-only sandbox; strongest reviewer diversity |
| Inline (self) | Just do it | No lanes available; task below threshold | Keep spec + ladder discipline anyway |

**Codex tiers:** OpenAI's tier names are durable across GPT generations —
`sol` (flagship), `terra` (mid, execution-competitive with the previous
generation's flagship at roughly half the cost), `luna` (speed, for mechanical
transforms). That maps exactly onto this skill's thesis: **executor lanes take
`terra`/`luna`, the reviewer lane takes `sol`.** Don't rely on the CLI's
configured default for lane choice — the user's default may be flagship-tier
(expensive for an executor) or speed-tier (weak for a reviewer); pass `-m`
explicitly per lane, using whatever the current generation of each tier is
(check `codex --version` / config if unsure).

Lane unavailable ⇒ report `LANE UNAVAILABLE: <which>` and pick the next lane
openly. Never silently substitute a different model and present its work as
the requested lane's.

## Executor dispatch template

> You are an implementation executor. Execute this spec exactly. The spec is
> decision-complete: if you hit a decision it does not cover, or reality
> contradicts it (a file missing, an API different), STOP and return
> `BLOCKED: <what's missing>` — do not improvise architecture.
>
> [SPEC FILE CONTENT]
>
> Return: status (`DONE`/`BLOCKED`/`FAILED`), the claim rung you can defend
> (WRITTEN / RUNS / VERIFIED) with evidence (command + output for RUNS and
> up), files changed, and any constraint you could not satisfy. Your final
> message is the deliverable — report facts, not reassurance.

## Reviewer brief template

> You are reviewing a change against its spec. You did not write it. Inputs:
> the spec (below) and the diff (below). Your job is to FALSIFY: find where
> the implementation violates the spec, breaks on inputs the spec names, or
> silently exceeds scope. Do not fix anything. Do not grade generously — an
> empty findings list from a real search is a valid result, and a manufactured
> finding is worse than none.
>
> Return findings as: `file:line — claim — evidence — severity(HIGH/MED/LOW)`.
> End with `VERDICT: CLEAN` or `VERDICT: FINDINGS <n>`.
