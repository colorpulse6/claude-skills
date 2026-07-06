# AGENTS.md — for Codex and every non-Claude-Code agent

You are reading the entry point for agents operating WITHOUT the Claude Code plugin loader. Everything in this marketplace works from here: skills are markdown instructions, not code — read them and follow them.

## How to use a skill from this repo

1. Skills live at `plugins/<name>/skills/<name>/SKILL.md`. The YAML frontmatter's `description` tells you when it applies; the body is the procedure.
2. Load `references/` files only when the SKILL.md points you to them (they are the depth layer, kept out of your context until needed).
3. Treat "the user invokes `/<name>`" as equivalent to the user asking for that skill by name.
4. Tool names in older plugins are Claude Code's (Read/Write/Edit/Bash/Grep/Agent). Mapping table + degraded-harness rules: `plugins/fable-method/skills/fable-method/references/codex-adaptation.md`. The four newest plugins (below) are written tool-agnostically.

## Start here

**`plugins/fable-method/skills/fable-method/SKILL.md`** — the operating method itself: the evidence-first loop, calibration rules (act vs ask vs stop), and communication standards. Load it at the start of any substantial task. Everything else assumes it.

## The skill index

| Skill | Use when | Notes for non-CC harnesses |
|---|---|---|
| `fable-method` | Starting any substantial/ambiguous task | Fully tool-agnostic |
| `rehydrate` | "What was I working on", resuming a project, back from a break | Needs shell + file read; packs live in `~/kb/docs/handoff/` |
| `handoff` | Ending a session with anything unfinished | Uses `~/kb/scripts/kblog` (plain shell script) |
| `marketing-ops` | Weekly marketing check-in, posting ritual, launches | Prepare-only: never publishes anything itself |
| `session-recap` | HTML timeline of recent Claude Code sessions | CC-specific (reads CC transcripts) — skip on other harnesses |
| `pr-review`, `pr-respond`, `push` | PR review / respond / quality-gated push | CC tool names; translate via the mapping table |
| `review-board`, `codex-second-opinion`, `risk-gate` | Multi-model / risk-gated review | These *invoke Codex as the second model*; from Codex, invert: run your own review, then get Claude's via `claude -p` |
| `plan-harden` | Adversarial design-doc review before building | Agent fan-out → run lenses sequentially with written checkpoints |
| `dep-audit`, `test-gap` | Dependency / missing-test audits | Same sequential translation |
| `create-skill`, `marketplace-lint`, `skill-starter` | Authoring/validating plugins in THIS repo | `marketplace-lint.py` runs anywhere Python does |

## House rules for working in this repo

- Develop on a branch; never push `main`. Register every new plugin in **three** places: `.claude-plugin/marketplace.json`, the README skill section, and the README structure tree. Run `python3 plugins/marketplace-lint/skills/marketplace-lint/scripts/marketplace-lint.py` before pushing.
- New skills follow the authoring guide at `plugins/create-skill/skills/create-skill/references/authoring-guide.md` (frontmatter rules, <500-line SKILL.md, `## Contents` TOC on references >100 lines).

## This machine's private layer

Skills here are public and hold **methods only**. The **facts** — project states, work context, brand data — live in dated context packs at `~/kb/docs/handoff/` (a local-only vault; never push it anywhere). The `rehydrate` skill is the bridge: it reads a pack, verifies it against live git state, and briefs. If you are an agent on this machine starting real work: `fable-method` first, then `rehydrate <project>`.
