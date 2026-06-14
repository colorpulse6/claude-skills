---
name: codex-second-opinion
description: Get an independent, separate-model (Codex / gpt-5.5) review of code — a just-shipped feature, a risky change, or a substrate you're about to build on. Use to complement your own Claude subagent audits with a genuinely different model that has different blind spots. A separate model catches what same-model reviewers miss.
user-invocable: true
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
---

# Codex Second Opinion

Run a **separate model** (Codex CLI, `gpt-5.5`) as an independent reviewer of code in this repo, then reconcile its findings against your own. The value is *model diversity*: in practice Codex has surfaced real bugs that three parallel Claude subagent audits all missed (e.g. a process-layer async-timing bug that made a feature silently inert in production) — because a different model has different blind spots. Use it *with* your Claude audits, not instead of them.

## When to use

- A feature just shipped (or is about to) and you want a high-confidence check before stacking more on top.
- You're about to build slice N+1 on a substrate slice N just laid down — verify N first.
- A change touches concurrency, process lifecycle, async timing, or money/LLM spend — areas where same-model reasoning tends to share the same blind spots.
- The user asks for "a separate opinion," "a second model," "what does Codex think," or hands you an external review to reconcile.

Don't reach for it for trivial/mechanical changes — it's a heavyweight `xhigh`-reasoning run (minutes, and large token spend).

## Prerequisite

Codex CLI must be installed: `which codex` (this repo has had `codex-cli` ≥ 0.137). If absent, say so and fall back to Claude-only subagent audits.

## The workflow

### 1. Write a NEUTRAL review brief (this is what makes it a real second opinion, not an echo)

Save a self-contained brief to `/tmp/codex-<feature>-review-brief.md`. The brief MUST:

- **Ask for independent findings FIRST, then a confirm/refute pass on your specific claims.** This is the key structure — it gets genuine independent discovery *and* an adversarial cross-check of what you already believe, instead of a yes-man echo. End the brief with: *"Return a ranked list: independent findings first (severity + file:line + fix), then a confirm/refute verdict on each numbered claim with evidence."*
- State **what the feature is** in a few sentences (the mental model, the default-on/off flags, the data flow).
- Give a **file map** — exact paths + line hints for every relevant file, so it doesn't waste the run hunting.
- List the **invariants the team claims hold** and ask it to verify they actually do.
- List **your own top findings as numbered claims** to confirm/refute (don't lead with your conclusions in the prose — keep them in the cross-check list so independent discovery stays uncontaminated).
- Say **read-only, do not edit.**

A neutral brief that hides your conclusions until the cross-check section is what produced the independent catch. If you front-load "here's what's wrong," you get agreement, not discovery.

### 2. Run Codex read-only from the repo root

```bash
cd <repo-root>
codex exec --sandbox read-only "$(cat /tmp/codex-<feature>-review-brief.md)" 2>&1
```

- `--sandbox read-only` = it can read + run read-only commands, never edits. `exec` = non-interactive (`approval: never`), so it won't block on prompts.
- It runs in the repo's working dir by default, so its file:line citations line up.
- Use a long timeout (it's an `xhigh` reasoning run; budget several minutes). If it might exceed your tool's max, run it backgrounded and poll.

### 3. Read the final answer

The raw output is large (mostly the reasoning trace) and your harness will persist it to a file. Don't try to read it all — jump to the **last `codex` message** (the final synthesis). Locate it with:

```bash
awk '/^codex$/{last=NR} END{print last}' <persisted-output-file>
```

then read from there. That block has the ranked independent findings + the confirm/refute verdicts.

### 4. Reconcile — don't just paste

Build one table: each finding × {your audits, Codex} × {severity, your own verification}. Call out:

- **Convergence** — items both you and Codex flag independently are high-confidence; lead with those.
- **Net-new from Codex** — what it caught that you missed (the whole point). *Verify these yourself in the code* before accepting — a separate model is a strong signal, not gospel.
- **Disagreements / "partly confirmed"** — read its evidence; it often sharpens a claim (e.g. "true, but only on the `.failed` terminal, not all errors").

Then present the reconciled verdict to the user and proceed (usually into a fix slice).

## Notes

- Keep the brief in `/tmp` (throwaway artifact) unless the user wants it tracked.
- This pairs naturally with `superpowers:dispatching-parallel-agents` (run your own 2–3 Claude lens-audits in parallel *while* Codex runs) and feeds a `superpowers:brainstorming` → spec → plan hardening slice.
- Other models work too (the brief is model-agnostic) — but `codex exec` is the path wired up here.
