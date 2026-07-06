---
name: marketing-ops
description: Runs the weekly operator rhythm for an autonomous content/growth engine — automation health, queue integrity, what's rendered but unposted, product-truth enforcement, funnel status, and launch execution. Use when the user says "marketing check-in", "run marketing ops", "what should I post", "how's the engine", "launch mode", or invokes /marketing-ops.
user-invocable: true
argument-hint: "[blank for weekly check-in | 'launch <product>' | 'post' for today's posting ritual]"
allowed-tools: Read, Bash, Glob, Grep, Write
---

# Marketing Ops

The operator layer for a content engine that runs itself. The machine researches, writes, and renders autonomously; the operator's job is the four things machines shouldn't do alone: **verify health, approve truth, distribute, and decide from metrics.**

**Site map first:** on this machine the engine lives at `~/Marketing/` and its full operator reference (paths, schedules, brand configs, token costs) is `~/kb/docs/handoff/marketing-map.md`. Read that pack before the first run; the living roadmap is `~/Marketing/ROADMAP.md`.

## The weekly check-in (default mode)

Work through the five stations, then deliver one visual status brief.

### 1. Automation health
Check scheduler status files and error logs (locations in the map pack). Every scheduled run since the last check-in should show a recent, successful status. A silent scheduler is the worst failure — it drains the queue invisibly. Report: last run per job + ✅/⚠️.

### 2. Queue integrity
Run each brand's queue validator. Then the number that matters: **days of runway** = ready-to-post assets remaining ÷ posting cadence. Under one week → the weekly runner needs attention before anything else.

### 3. The unposted pile (the usual bottleneck)
List assets rendered but never posted, oldest first. Autonomous engines fail here: production compounds, distribution stalls. If the pile is growing week-over-week, the check-in's #1 recommendation is a posting session, not more production.

### 4. Product-truth gate
Diff every queued/pending asset's claims against the brand's `product-facts.json`. Anything implying a not-yet-buyable tier, an unshipped feature, or an unverified stat gets pulled — a refund request or a called-out lie costs more than a week of content earns. This gate applies doubly to hand-written copy, which skips the runners' automated gate.

### 5. Funnel + metrics pulse
Is each funnel stage wired and receiving? (capture form → freebie delivery → product page → purchase webhook). Report per-channel signal since last check-in: posts, replies/comments worth answering, clicks, captures, sales. No analytics? Then say "no data" — never infer performance from vibes.

### The brief
Mermaid status map (stations as nodes, ✅/⚠️/🔴) → the one recommended action this week → runway number → open threads list. Full reporting standards: the fable-method plugin's `communication.md`.

## Posting ritual (`post` mode)

1. Pull today's asset(s) from the queue/drip email.
2. Final eye: product-truth, typos, platform fit (aspect, length, banned characters per house rules — e.g. the em-dash guardrail).
3. Produce platform-native caption variants (hook first, hashtags per platform norms, CTA matching the funnel stage) — see `references/channel-playbooks.md`.
4. Human posts by hand. **Never auto-post, never log into accounts** — this skill prepares; the operator publishes.
5. Mark posted in the queue; note anything worth a reply-sweep in 24h.

## Launch mode (`launch <product>`)

Follow `references/launch-checklist.md` — gate checks (billing live end-to-end, legal pages, analytics, listing assets), channel sequencing (sandbox → flagship → launch platforms), and the day-of runbook. For products with an existing dated launch plan (e.g. `~/kb/docs/handoff/jobtoast-launch-plan.md`), that plan is the authority; the checklist is its generic skeleton.

## Rules

- **Prepare, don't publish.** Outward-facing sends (posts, emails, PH submissions) are staged as ready-to-paste artifacts; the human fires them.
- **Truth outranks reach.** When in doubt about a claim, cut the claim, keep the post.
- **Calibrate, don't thrash.** One variable per experiment, one week per read. Kill channels by data, not boredom; double down by data, not novelty.
- **Respect the cadence budget.** The engine's token costs are measured (map pack) — adding runs is a spend decision for the human.
