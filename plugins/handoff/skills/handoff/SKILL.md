---
name: handoff
description: Closes a working session cleanly — repo left consistent, session logged to the knowledge base, every open thread named, context packs healed. Use at the end of any substantive session, before stepping away from unfinished work, or when the user says "wrap up", "hand off", "closing time", "done for today", or invokes /handoff.
user-invocable: true
argument-hint: "[optional: one-line summary of the session]"
allowed-tools: Read, Bash, Glob, Grep, Edit, Write
---

# Handoff

The user's failure mode is not unfinished work — it is **forgotten threads**. He keeps plans in his head, uses no todo apps, and finishes what he remembers. This skill makes sure everything survives the gap between sessions, whoever (or whatever) picks it up next.

**Core principle: the next agent starts from files, not from memory.** Anything that lives only in this conversation dies with it.

## Protocol

### 1. Inventory the session (2 min, honest)
- What changed (files, repos, systems), what was decided, what was discovered.
- What is DONE-verified vs done-but-unverified vs abandoned mid-flight. These three tiers must not blur.

### 2. Leave the repo consistent
- Work worth keeping → commit it on its branch with a message that names the thread (or, if the user hasn't authorized commits, stage nothing silently — report the dirty state loudly instead).
- Work not worth keeping → say so and offer to discard; never leave mystery dirty files for future-you to reverse-engineer. Uncommitted WIP left on a shared branch is the #1 archaeology generator.
- Half-finished experiments → a branch named `wip/<thread>` beats a stash beats silent dirt.

### 3. Log the session to the knowledge base
Append via the kb's own mechanism (works from any harness, Codex included):
```bash
~/kb/scripts/kblog "<thread>: <state>. Next: <first concrete move>. [<repo/branch>]"
```
One line per thread touched. This lands in `~/kb/raw/daily-log/` — which the kb's daily compile weights as its highest-signal source, so the session becomes part of the permanent record and tomorrow's briefing automatically.

### 4. Name EVERY open thread
In the final report, a threads table: thread → state → first move next time → where it lives (repo/branch/file). Include threads *noticed* but not touched ("saw a failing feed in the logs — not investigated"). The recommendation picks one thread; the table preserves all of them.

### 5. Heal the context packs
If this session made a pack in `~/kb/docs/handoff/` stale (project state moved, a gate cleared, a path changed), update the affected lines and bump the pack's snapshot date. Thirty seconds now; an hour of re-discovery saved later.

### 6. The closing report
Per the fable-method communication standards: outcome first, the three verification tiers kept distinct, threads table, one recommended next move. If the session failed at something, the failure is in sentence one — a clean handoff of a failure is a successful handoff.

## Anti-patterns

| Temptation | Why it burns you |
|---|---|
| "I'll remember where I was" | You won't; and the next agent certainly won't. |
| Committing everything as `wip` on the integration branch | Pollutes shared history; branch it. |
| Logging vibes ("good progress on jt3") | Log state + next move; vibes don't resume. |
| Skipping handoff because the session was short | Short sessions leave the sneakiest dirt — one edited file, zero context. |
| Updating the pack from memory | Verify against `git log` first; packs heal with evidence, not recollection. |
