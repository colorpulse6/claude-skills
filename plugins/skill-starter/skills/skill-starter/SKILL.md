---
name: skill-starter
description: >-
  Template skill demonstrating the orchestrator -> parallel agents -> aggregate
  pattern. Splits a target (file glob or directory) into chunks, runs one
  worker subagent per chunk in parallel, and merges their findings into a single
  report. Use when user says "skill starter", "scaffold a skill", "run the
  starter audit", or invokes /skill-starter.
user-invocable: true
argument-hint: "[target-glob-or-dir]"
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
---

# Skill Starter (Template)

A minimal but complete example of the **orchestrator pattern**: one user-invocable
skill detects what to work on, fans the work out to several parallel specialist
**subagents**, then converges their outputs into one report.

> **TEMPLATE:** Replace the "analysis" performed here with whatever your real
> skill does. The mechanics — parse input -> collect units of work -> spawn
> agents in parallel -> aggregate -> write report — stay the same.

---

## Step 1: Parse input & resolve the target

The argument is a glob or directory. If none is given, default to the current
repo's tracked text files.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/skill-starter/scripts/collect.sh" "$ARGUMENTS"
```

`collect.sh` is the **deterministic** layer: it resolves the target, lists the
units of work (one path per line), and prints them as JSON. Keep file
discovery / parsing / fetching in scripts — not in prose — so runs are
repeatable.

If the script reports zero units, stop and tell the user nothing matched.

## Step 2: Decide the work split

- Read the unit list from Step 1.
- Group units into **at most 5 batches** (one batch per worker agent). Balance
  by count so no agent is overloaded.
- Create an output directory for this run: `./.skill-starter-out/findings/`.

> **TEMPLATE:** Tune the batch count / grouping strategy to your domain. SEO-style
> plugins group by *category* (technical, content, schema); a file auditor groups
> by *path*.

## Step 3: Fan out to parallel worker agents

Spawn one `starter-worker` subagent **per batch, all in a single message** so they
run concurrently. Give each worker:

- the list of paths in its batch,
- the absolute `output_dir` (`./.skill-starter-out/findings/`),
- a unique `batch_id` (e.g. `batch-1`) for its output filename.

Each worker writes `output_dir/<batch_id>.md` and returns a one-line summary.
Do **not** do the per-unit analysis yourself — that is the worker's job.

## Step 4: Aggregate

- Read every `*.md` under `./.skill-starter-out/findings/`.
- Merge them into `./.skill-starter-out/REPORT.md` using the contract below.
- Sort findings by severity: Critical -> High -> Medium -> Low -> Info.

## Step 5: Report to the user

Print the path to `REPORT.md` plus a short summary (counts per severity). Done.

---

## Output contract

`REPORT.md` MUST contain, in order:

1. **Summary** — target, number of units, number of agents, severity counts.
2. **Findings table** — `| Unit | Severity | Finding | Recommendation |`.
3. **Per-batch detail** — each worker's section verbatim, under an `## batch-N` heading.

Each worker file (`<batch_id>.md`) MUST contain a findings table with the same
columns so aggregation is a concatenation, not a re-parse.

## Error handling

| Scenario | Action |
|----------|--------|
| No argument given | Default to repo-tracked text files; state the default used. |
| Glob matches nothing | Stop; tell the user no units matched and echo the pattern tried. |
| `collect.sh` exits non-zero | Surface stderr; do not spawn agents. |
| A worker agent fails / writes no file | Note the missing `batch_id` in the report; aggregate the rest. |
| Output dir not writable | Fall back to a temp dir and report the path used. |
