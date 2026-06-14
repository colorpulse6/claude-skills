# Skill Patterns & Quality Conventions

The structural choices and shared quality conventions behind this marketplace's
plugins. Step 2 uses the decision rubric; Step 4 applies the conventions.

## Contents
- Inline vs orchestrator + parallel agents
- The parameterized-agent pattern
- Scripts for determinism
- Shared quality conventions
- Output-contract shape

## Inline vs orchestrator + parallel agents

The orchestrator pattern (skill spawns parallel specialist agents, then
aggregates) buys **parallelism** (wall-clock speed), **context isolation** (verbose
work stays out of the main window), **least privilege** (per-agent tool/model
scope), and **failure isolation**. It costs latency overhead, more total tokens,
and coordination complexity.

| Situation | Use |
|-----------|-----|
| Work is sequential / each step needs the last | **Inline skill** — agents can't parallelize a chain |
| Small / fast (a few files, one page, a quick transform) | **Inline skill** — overhead isn't worth it |
| Many **independent** units + want speed | Orchestrator + parallel agents |
| Reading lots of data you don't want in the main context | Agents (for context isolation, even if serial) |
| Different models / tool scopes per sub-task | Agents |

Default to inline. Right-size the fan-out to the work (a handful of agents, not
dozens). Spawn all independent agents in one message.

## The parameterized-agent pattern

When a skill needs N specialists that share a tool/model profile and differ only
in *what they look for* (lenses, ecosystems, shards), write **one** agent
parameterized by `{role, checklist, inputs, output_dir}` and a per-role section in
a `references/` file — not N agent files. (Use separate agent files only when the
specialists genuinely differ in tools/model, like claude-seo's 18 agents.)

Each agent: inline payload, do the work, write `output_dir/<role>.md`, return a
status line. The orchestrator globs the findings and aggregates.

## Scripts for determinism

Anything that must be repeatable — file discovery, diff parsing, scoring, fetching
— goes in a script the skill *runs*, with judgment left to the markdown. Emit
structured output (JSON) the orchestrator reads back. Examples in this repo:
`risk_score.py` (per-file risk scoring), `manifest_scan.py` (offline dep-diff),
`collect.sh` (unit collection). Justify every constant; keep paths forward-slashed.

## Shared quality conventions

Borrowed from Anthropic's code-review/security-review and the adversarial-review
ecosystem — apply wherever a skill produces findings/recommendations:

- **Confidence-gate.** Each finding carries a confidence; only surface ≥ ~0.7.
  Reserve top severity for findings with a concrete failure scenario you can name.
- **Validation pass / distrust the report.** The orchestrator re-checks a
  subagent's claim against the source before accepting it — don't propagate
  self-reports as truth.
- **Fixed status enum.** Subagents return one of `DONE` / `DONE_WITH_CONCERNS` /
  `BLOCKED` / `NEEDS_CONTEXT`; the orchestrator branches on it.
- **Epistemic labels** when multiple sources agree: `[CONSENSUS]` (≥2 independent)
  / `[CROSS-VALIDATED]` / `[SINGLE-SOURCE]` — lead with the highest-confidence.
- **Falsifiability** (for recommendations): each carries the observation it rests
  on, its dependency on other items, a "how would we know this failed?" check, and
  a leading indicator to monitor.
- **A clean result is valid.** Never fabricate findings to look thorough — false
  positives erode trust faster than a missed nit. Say "no issues found" plainly.
- **Severity is orthogonal to confidence** — "is it real" (confidence) and "how bad
  if real" (severity) are separate axes; carry both.

## Output-contract shape

Every skill that produces output declares, in `SKILL.md`, exactly what it writes:
a named report file, an ordered set of sections, and a findings table with fixed
columns. Uniform, machine-parseable output is what makes aggregation (and any
downstream skill) trivial. Pair it with an error-handling table covering the empty
case, the partial-failure case, and the missing-tool/missing-input case.
