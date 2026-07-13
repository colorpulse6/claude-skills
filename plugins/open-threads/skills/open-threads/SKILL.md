---
name: open-threads
description: >-
  Cross-project forgotten-work radar. Sweeps every local git repo for
  uncommitted, unpushed, stashed, and never-pushed work, cross-references the
  context packs' open threads, and ranks what is most at risk of being
  forgotten — with one concrete first move each. Use when the user asks "what
  am I forgetting", "open threads", "loose ends", "what's at risk", "what did
  I leave hanging", or invokes /open-threads. (Distinct from /rehydrate, which
  restores ONE project's context, and /session-recap, which is a timeline of
  past sessions — this is the radar across everything.)
user-invocable: true
argument-hint: "[optional: extra scan roots]"
allowed-tools: Bash, Read, Glob, Grep
---

# Open Threads

The failure mode this exists for: **you finish what you remember.** Work
doesn't die by decision — it dies by silence: a dirty tree nobody commits, a
branch never pushed, a "Next:" line in a context pack that nothing ever reads
again. This skill is the periodic radar sweep that makes silence visible.

**Read-only.** It reports and recommends; it never commits, pushes, or edits
packs. Healing belongs to /handoff and /rehydrate — this skill tells you where
to point them.

## Step 1: Sweep the filesystem (deterministic)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/open-threads/scripts/sweep.py"
```

Add `--roots <dir> ...` if the user passed extra locations. The JSON lists
every repo with dirty files, unpushed commits, never-pushed branches, stashes,
and staleness — sorted so forgotten work comes first.

## Step 2: Read the declared threads

- Context packs: `~/kb/docs/handoff/*.md`. Extract open threads — `Next:`
  lines, "Open lane", blocker lists, threads tables — and each pack's snapshot
  date. A pack's claims are only as fresh as that date.
- The thread ledger `~/kb/wiki/_threads.md`, if it exists (planned
  intelligence-layer artifact; absence is normal — note it and move on).

## Step 3: Triage (judgment)

Apply `references/triage.md`: filter noise repos, age every thread, and
reconcile pack claims against live git state. Two evidence classes:

- **Declared threads** (a pack names it) — age from the pack's snapshot date
  and verify the claim against the sweep before repeating it.
- **Silent threads** (git shows work no pack mentions) — these are the
  dangerous ones; nothing will ever remind the user about them.

## Step 4: Report

Terminal output, this order:

1. **Top threads at risk** — at most 5, ranked. Each: thread name, where
   (repo/branch or pack), evidence (the fact, e.g. "116 unpushed commits,
   single copy on this disk"), age, and ONE first move (a command or a
   15-minute action, not a project plan).
2. **Full table** — every open thread: `thread | where | evidence | age | state`
   with state ∈ ACTIVE / COOLING / AT_RISK / COLD.
3. **Pack drift** — packs whose claims disagree with live state (thread done,
   path moved, gate cleared), each with the line to fix and the suggestion to
   run /handoff or /rehydrate to heal it.

A clean radar is a valid result: if nothing is at risk, say exactly that and
stop — do not manufacture urgency.

## Error handling

| Scenario | Action |
|----------|--------|
| `sweep.py` fails | Fall back to `git status`/`git log` on the repos named in the packs; say the sweep degraded and coverage is partial. |
| `~/kb/docs/handoff/` missing | Git-only mode: report silent threads, note that declared threads are unknown on this machine. |
| A repo hangs or errors mid-sweep | The script skips it (15s git timeout); list skipped repos so silence isn't mistaken for cleanliness. |
| Nothing at risk anywhere | Report "radar clean" with the sweep totals. That is a success, not an empty answer. |
