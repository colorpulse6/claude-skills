---
name: test-gap
description: >-
  Finds the most important MISSING tests in a diff/PR/branch. Fans out
  gap-finder agents over the changed files; each traces codepaths (changed
  conditionals, error paths, boundaries) and ranks untested ones by risk =
  impact x likelihood, not raw coverage %. Optional coverage (diff-cover) and
  mutation-testing passes confirm "covered-but-unasserted" gaps. Produces a
  prioritized list of tests to add with proposed cases. Use when user says
  "test gaps", "what's untested", "what should I test", "coverage gaps", or
  invokes /test-gap.
user-invocable: true
argument-hint: "[PR number | branch | (default: working diff)]"
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
---

# Test Gap

Finds the tests worth writing — not every uncovered line. The ranking principle
is **risk = impact × likelihood**: a bug here costs a lot (impact) and is plausible
(likelihood). Coverage % is an input, not the goal — you can have 100% line
coverage at 0% mutation score, so an executed-but-unasserted path is still a gap.

---

## Step 1: Resolve the diff & map tests

Resolve the base (PR / branch / working tree). List changed **source** files and,
for each, find the likely test file (sibling `*.test.*` / `*_test.*` / `tests/`).
A changed source file with no test is the top suspect. If nothing changed, stop.

## Step 2: Optional coverage probe (cheap, if available)

Detect a coverage tool and, if present, get **patch/diff coverage** (coverage of
just the changed lines — the cleanest "newly-introduced AND untested" signal):

- JS/TS: `npx vitest run --coverage` / `jest --coverage`
- Python: `pytest --cov --cov-report=term-missing`; or `diff-cover` over an XML report
- Go: `go test -coverprofile=cover.out ./... && go tool cover -func=cover.out`
- Rust: `cargo tarpaulin`

If no tool is configured, skip — the agents still reason about gaps from the diff.

## Step 3: Fan out gap-finder agents — in parallel

Shard the changed files (≤5 shards) and spawn one `gap-finder` subagent per shard
**in one message**. Give each (inline): its file list + diffs, any patch-coverage
data, the heuristics from
`${CLAUDE_PLUGIN_ROOT}/skills/test-gap/references/test-gap-heuristics.md`, and
`output_dir` = `./.test-gap-out/findings/`.

Each traces codepaths, scores gaps, writes `findings/<shard>.md`, returns a status
line. Don't do the per-file analysis yourself.

## Step 4: Optional mutation pass (confirm weak assertions)

For the **highest-risk covered** files only, optionally run mutation testing
(Stryker / PIT / mutmut / cargo-mutants). **Surviving mutants** = code whose
behavior could change with no test failing = a precisely-located missing
assertion. Add these as `[weak-assertion]` gaps. Skip if no tool / time budget.

## Step 5: Aggregate & rank

Read all `findings/<shard>.md`. Merge into `./.test-gap-out/TEST-GAP.md`, ranked by
`priority = risk × gap` descending. **Top-N first** — readers stop after the first
handful, so order matters more than completeness.

## Step 6: Report

Print the top gaps + counts per priority tier. Done.

---

## Output contract — `TEST-GAP.md`

1. **Summary** — files changed, % with no test, top risk areas, one-line headline.
2. **Prioritized gaps (P0 → P1 → P2)** — table: `| Priority | Location (file:line) | Untested path | Failure mode | Proposed test(s) | Effort |`. Each gap carries a category code (see below) and a `file:line`.
3. **Covered-but-weak** — surviving mutants / assertion-free covered paths (if the mutation pass ran).
4. **Out of scope** — obsolete/dead code to *remove* rather than test; trivial pass-throughs deprioritized.

Category codes: `untested-branch`, `untested-error-path`, `untested-boundary`, `untested-domain-rule`, `weak-assertion`, `untested-async-failure`.

Priority tiers: **P0** (must test — money/security/data-integrity path, untested) / **P1** (should test) / **P2** (nice-to-have). Don't chase 100%; target meaningful coverage of the risky paths.

## Error handling

| Scenario | Action |
|----------|--------|
| No source files changed | Stop; say the diff had no testable source changes. |
| No coverage tool configured | Skip Step 2; reason from the diff and say coverage was unavailable. |
| No mutation tool | Skip Step 4; note weak-assertion gaps weren't machine-confirmed. |
| A gap-finder writes no file | Note the missing shard; aggregate the rest. |
| Change is pure refactor with existing tests passing | Report "no new gaps"; a clean result is valid. |
