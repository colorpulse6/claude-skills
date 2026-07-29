---
name: rehydrate
description: Restores working context for a project after time away by reading its dated context pack, verifying claims against live git/filesystem state, and briefing with a visual status map plus the recommended next thread. Use when the user says "what was I working on", "resume <project>", "getting back to <project>", "catch me up", "back from leave/vacation/break", or invokes /rehydrate. This restores context to resume ONE project — for a visual timeline of past sessions use /session-recap; for the cross-project forgotten-work radar use /open-threads.
user-invocable: true
argument-hint: "[project name, or blank for a full sweep]"
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

# Rehydrate

Bring a returning human (or a fresh agent) back to full context on a project — fast, verified, and visual.

**Core principle: the pack is a map, not the territory.** Context packs are dated snapshots. Every load-bearing claim gets verified against live state before it reaches the brief. A confidently-delivered stale fact is worse than no fact.

## Where packs live

`~/kb/docs/handoff/` — one pack per domain, date-stamped, each claim carrying a verify-command. Start every run by reading `projects-atlas.md` (the index). Known packs:

| Pack | Covers |
|---|---|
| `projects-atlas.md` | Every personal repo: state, next thread, paths (the index) |
| `marketing-map.md` | The ~/Marketing content engine: schedules, queues, operator rules |

The atlas is the authority, not this table — packs are discovered by reading it,
so work-specific and private packs need no entry here and should not get one.

(Adapting this skill for another machine: change the pack directory; the protocol is unchanged.)

## Protocol

### 1. Resolve the target
- Named project → its pack section (via the atlas) + its repo.
- No argument / "what was I working on" → full sweep: atlas + the freshness scan below across all listed repos.

### 2. Read the pack, note its date
The gap between the pack's date and today calibrates suspicion: days → trust mostly; weeks → verify everything load-bearing; months → treat as archaeology.

### 3. Verify before briefing
Run the pack's verify-commands (they sit next to the claims). Minimum per repo:
```bash
git -C <repo> log -5 --format='%ad %h %s' --date=short   # what actually happened since the pack
git -C <repo> status --porcelain | head -20               # uncommitted state the pack may not know
git -C <repo> branch -a --no-merged origin/HEAD 2>/dev/null | head  # open threads
```
Diff reality against the pack. Three buckets: **confirmed** (pack matches live), **advanced** (work moved on — the pack understates), **drifted** (pack contradicts live — flag loudly).

### 4. Brief — visual first
Lead with a Mermaid status map (projects as nodes, states as colors/labels), then:
- **Where you left off** — the last real thread, in one paragraph of plain sentences.
- **What changed since** — anything live state shows that the pack does not (automation ran, a PR merged, a branch appeared).
- **Landmines** — the pack's warnings that verification confirmed still apply (uncommitted WIP, unmerged stacks, port/config traps).
- **Recommended next thread** — ONE thing, with the first concrete command to run. A returning brain wants a door, not a corridor of doors.

### 5. Heal the pack
If verification found drift, offer to update the pack (edit the stale claims, bump its date-stamp). A pack that silently rots stops being trusted; a pack that heals on every use compounds.

## If no pack exists

Build one from live sources — repo README/CLAUDE.md, `git log -20`, open branches, plus the kb wiki article if one exists (`~/kb/wiki/projects/<name>.md` holds curated history with daily narratives). Save it to `~/kb/docs/handoff/`, date-stamped, claims paired with verify-commands. Then brief as above.

## Rules

- Never brief from the pack alone — verification is the skill. Skipping it produces confident stale nonsense.
- Never quote private work content (Slack, DMs, compensation, colleague specifics) into any file outside the kb vault; packs live in the vault precisely because it is local-only.
- The brief ends by naming ALL open threads (the user's failure mode is forgotten threads, not unfinished ones) — the recommendation picks one, the list preserves the rest.
