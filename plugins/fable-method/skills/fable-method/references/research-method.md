# Research Method — mapping systems and delegating work

## Contents
- [Mapping an unknown system](#mapping-an-unknown-system)
- [The delegation brief](#the-delegation-brief)
- [Output contracts](#output-contracts)
- [Distrust and verify agent reports](#distrust-and-verify-agent-reports)
- [Synthesis](#synthesis)
- [The dual-review workflow](#the-dual-review-workflow)
- [Single-context fallback](#single-context-fallback)

## Mapping an unknown system

Goal: hold an accurate model of the system before touching it, at minimum cost.

1. **Entry points first.** README, CLAUDE.md/AGENTS.md, the manifest (package.json / Cargo.toml / Package.swift), the directory tree two levels deep, and `git log -10 --date=short`. Ten minutes here beats an hour of grep archaeology.
2. **Recency is signal.** `git log` tells you where the project's energy is. The freshest paths are usually where the task lives — and where the landmines are.
3. **Slice by independence, then fan out.** Cut the unknown into 2–4 areas that can be understood separately (vault content vs repo conventions vs git activity; frontend vs service boundary). One focused reader per slice, in parallel.
4. **Read the load-bearing files yourself.** Delegate breadth; keep depth for the files your decision actually hinges on. Never make a critical call purely on a summarizer's paraphrase.
5. **Stop when decisions stop changing.** Research is done when the next fact would not change what you do — not when everything is known.

## The delegation brief

Every delegated unit (subagent, second model, or a future session of yourself) gets a brief with five parts. Delegation failures are almost always brief failures.

1. **Context** — everything the worker needs and cannot discover cheaply: paths, dates ("today is …" — workers have no calendar), known facts, prior findings. Workers do not inherit your conversation; write as if to a competent stranger.
2. **Task** — numbered, concrete deliverables. "Report X, Y, Z about path P," not "look into P."
3. **Constraints** — what NOT to do: directories to skip, files not to modify, "don't quote private content," budget/effort bounds.
4. **Output contract** — see below.
5. **Done criteria** — what makes the result acceptable, so the worker can self-check before returning.

## Output contracts

Specify the return format or you will get prose soup:

- Structure: "structured markdown, ≤N words, dense bullets, absolute paths."
- Semantics: "report at metadata level, no verbatim private content" / "quote only load-bearing lines."
- Delivery: state explicitly that the final message IS the deliverable — workers otherwise summarize their own work away.
- Enums over vibes: when results feed a decision, demand fixed statuses (`DONE` / `BLOCKED` / `NEEDS_CONTEXT`) and confidence labels, not "seems fine."

## Distrust and verify agent reports

A subagent's report is a claim, not a fact.

- **Spot-check by consequence:** verify the 2–3 claims your next decision rests on (open the file, run the command). Skip verifying trivia.
- **Suspicious patterns:** round numbers, "everything looks good," reports that answer an easier question than asked, and garbage/preamble-shaped output (a mangled report means re-run, not reinterpret).
- **Adversarial pass for high-stakes findings:** before acting on a big claim ("this is the bug"), try to refute it. If a finding survives an honest attempt to kill it, act on it.
- A clean result is valid. Never pressure a worker (or yourself) into manufacturing findings; "nothing found" under a real search is information.

## Synthesis

After fan-out, the orchestrator earns its keep:

- **Reconcile conflicts explicitly.** Two readers disagreeing about the same fact means one of them (or the question) is wrong — resolve it with a direct check, don't average.
- **Separate observation from inference** in your own notes ("the log shows two timeouts" vs "the ingest prompt has probably outgrown its budget").
- **Write the map down** if the project will outlive the session — dated, with verify-commands next to volatile claims.

## The dual-review workflow

For designs and consequential changes, the strongest cheap quality lever is independent review by a *different* mind — a fresh-context subagent, or better, a different model family (different blind spots). The full ceremony, worth it for substantial builds:

```
brainstorm → spec → dual review (same-model fresh context + cross-model)
          → plan → dual review → build in slices → verify → ship
```

Rules that make it work:
- Reviewers get the artifact and the goal, NOT your reasoning — independent derivation is the point.
- Ask reviewers to falsify ("find what breaks"), not to approve.
- Reconcile findings by convergence: both reviewers flag it → almost certainly real; one flags it → verify before acting; they disagree → the disagreement is the finding.
- Scale the ceremony to stakes: a doc edit needs none of this; a billing path wants all of it.

## Single-context fallback

No subagents (Codex CLI, plain sessions)? The method survives translation:

- Fan-out becomes **sequential passes with written checkpoints**: after each research slice, append findings to a scratch file (`notes/research.md`), then start the next slice reading only that file — this simulates fresh-context isolation and keeps the final synthesis honest.
- Dual review becomes: finish the artifact, clear your context (new session or explicit "forget the journey" reread), and review it cold against the goal — or hand it to the other CLI (`claude -p` / `codex exec`) for the cross-model pass.
- Parallel tool calls become a script: batch the independent commands into one shell invocation.
