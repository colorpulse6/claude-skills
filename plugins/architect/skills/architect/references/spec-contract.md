# Spec contract, lanes, and briefs

## Contents
- The five-part spec contract
- Decision-completeness checklist
- Provider strengths — the evidence behind the table
- Lane table
- Balancing the two providers
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
- [ ] Have you **executed** each done-criteria command's tooling probe —
      `pytest --version`, `tsc --version`, `curl --version` — and seen it
      resolve? Check that the command *can run*, not that it passes: the
      criteria should still fail at this point, because the work doesn't
      exist yet. A passive "looks runnable" is how a missing test runner
      reaches the executor.

## Provider strengths — the evidence behind the table

**The operative routing table lives inline in `SKILL.md` Step 2**, because every
dispatch consults it and a pointer is not reliable enough for a hot path. This
section is the *why* behind each row — read it when a routing call is contested,
not on every dispatch. Do not duplicate the table here; it drifts.

- **Planning, spec-writing, premise rejection → Claude.** Wins decisively on
  decision quality and edge-case discovery; the thesis this whole skill rests on.
- **Multi-file / dependency-graph work → Claude.** The 1M window holds the
  graph. The practitioner heuristic is "12 files and the dependency graph
  matters."
- **Large real-repo tasks → Claude.** SWE-bench Pro 69.2% vs 58.6%.
- **Code a human will maintain → Claude.** Blind evaluation rated Claude's
  output cleaner in 67% of comparisons vs 25%, 8% ties.
- **Terminal-native work → Codex.** 77.3% vs 65.4% — a 12-point gap, the
  largest single divergence between the families.
- **Algorithmic / self-contained problems → Codex.** Leads LiveCodeBench and
  Terminal-Bench.
- **High-volume mechanical transforms → Codex `luna`.** ~4× fewer tokens for
  the same work.
- **Review → the family that didn't write it.** Different blind spots is the
  entire value; a same-family reviewer shares the author's errors.

The industry hybrid this converges on — *Claude generates, Codex reviews* — is
the default here too. Invert it when the work is terminal-native: Codex builds
the migration script, Claude reviews it against the schema it has in context.

## Lane table

| Lane | How | Use when | Notes |
|---|---|---|---|
| Cheap Claude subagent | Agent tool, `model: sonnet` (or `haiku` for mechanical transforms) | Default executor lane for in-repo code | Runs in-harness, tools available, background-able |
| Codex CLI executor | `codex exec -m gpt-5.6-terra --sandbox workspace-write "$(cat spec.md)" < /dev/null` | Terminal-native work; second family wanted; Claude cap under pressure | `< /dev/null` mandatory on non-TTY/backgrounded runs — the stdin probe otherwise blocks forever |
| Codex volume | `codex exec -m gpt-5.6-luna --sandbox workspace-write ... < /dev/null` | Mechanical transforms, high-volume edits | Cheapest tier; do not hand it judgment |
| Codex flagship executor | `codex exec -m gpt-5.6-sol --sandbox workspace-write ... < /dev/null` | Escalation only: the ordinary lane returned `FAILED`, or the slice needs frontier reasoning *during* implementation | Flagship rates for typing — against the thesis, so it must be justified in the report |
| Codex read-only | `codex exec -m gpt-5.6-sol --sandbox read-only ... < /dev/null` | Reviewer lane (cross-family) | Read-only sandbox; strongest reviewer diversity. Same model as the row above — only the sandbox differs, and a reviewer that can edit is not a reviewer |
| Inline (self) | Just do it | No lanes available; task below threshold | Keep spec + ladder discipline anyway |

**Model ids must be generation-qualified.** Pass the full id — `gpt-5.6-sol`,
`gpt-5.6-terra`, `gpt-5.6-luna`. The bare tier name is **not** accepted:

```
$ codex exec -m terra ...
warning: Model metadata for `terra` not found. Defaulting to fallback metadata
ERROR: 400 The 'terra' model is not supported when using Codex with a ChatGPT account.

$ codex exec -m gpt-5.6-terra ...
OK
```

Tiers are stable in *meaning* across generations — `sol` flagship, `terra` the
value default (flagship-minus at roughly half cost; 87.4% vs 88.8% on
Terminal-Bench 2.1), `luna` the speed tier — but the id carries the generation.
When a new generation ships, the prefix moves and these ids go stale: read
`model` in `~/.codex/config.toml` to see the current generation, then swap the
tier suffix for the lane you want.

Never inherit the CLI's configured default for lane choice — it is whatever the
user set for interactive work (often flagship, which is wasteful for an
executor). Pass `-m` explicitly on every lane.

Outside a git repo, `codex exec` refuses with *"Not inside a trusted directory"*
— add `--skip-git-repo-check` when dispatching into scratch directories.

Lane unavailable ⇒ report `LANE UNAVAILABLE: <which>` and pick the next lane
openly. Never silently substitute a different model and present its work as
the requested lane's.

## Balancing the two providers

**First, establish the metering regime — don't assume it.** It changes what the
second lane actually costs, and it varies by installation:

| Signal | Regime | Scarce resource |
|---|---|---|
| Codex errors mention *"with a ChatGPT account"*; `~/.codex/auth.json` holds a ChatGPT login | Subscription | Rolling-window **headroom** |
| An `OPENAI_API_KEY` is set, or config points at an API key | API-billed | **Dollars** per token |
| Claude Code running on a Max/Pro plan | Subscription | Rolling-window headroom |
| Claude Code on a console/API key | API-billed | Dollars per token |

Unknown after a quick check? Assume subscription for whichever side is
ambiguous and say so in the report — over-conserving headroom is the cheaper
error.

**Under subscription metering**, idle capacity is wasted capacity: a run that
puts everything through one family burns that cap toward its limit while the
other sits unused. When two lanes are genuinely tied on the strengths table,
take the one used less this session.

**Under API billing**, the tiebreak inverts — prefer the cheaper lane rather
than the less-used one, since there is no cap to conserve and no reason to pay
more for a tie.

**In both regimes, strength outranks balance.** Never route terminal-native
work to Claude, or dependency-graph work to Codex, to even out a ledger. A task
done worse on the "fairer" lane costs more rework than it saves in headroom or
dollars.

Track it cheaply: keep a running tally of dispatches per family and report it
at Step 5 as `Claude <n> · Codex <n>`. Exact token accounting is not the goal
and is not comparable across providers anyway — the tally exists to make a
lopsided run visible, so the next run can lean the other way.

If one provider is rate-limited or out of quota mid-run, that is a
`LANE UNAVAILABLE` — say so, re-route by the strengths table, and note in the
report that the lane choice was forced rather than chosen.

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
