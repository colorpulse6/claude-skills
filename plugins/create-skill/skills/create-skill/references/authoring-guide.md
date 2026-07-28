# Skill Authoring Guide

Distilled from Anthropic's official skill-authoring best practices and a survey of
strong community plugins (Anthropic's `code-review`/`security-review`, superpowers,
claude-seo, wshobson/agents, and others). This is the substance Step 4 writes
against.

The invocation trade-off and completion criteria below are distilled from Matt
Pocock's `writing-great-skills` (https://aihero.dev/skills-writing-great-skills).

## Contents
- Frontmatter that matters
- Invocation: who can fire this
- Writing the description (the discovery surface)
- Progressive disclosure
- Steps and completion criteria
- Subagents (when the skill fans out)
- House conventions for THIS repo
- Anti-pattern checklist (run at Step 5)

## Frontmatter that matters

Required: `name`, `description`. This repo's skills also set `user-invocable`,
`argument-hint`, and `allowed-tools`.

- `name`: kebab-case, lowercase/numbers/hyphens, ≤ 64 chars, reads as the slash
  command. No reserved words (`anthropic`, `claude`).
- `allowed-tools`: scope to what the skill actually uses (e.g. `Bash, Read, Write,
  Glob, Grep, Agent`). Least privilege.
- `argument-hint`: a short `[...]` hint for the invocation.

## Invocation: who can fire this

Decide this **before** writing the description — it changes what the description
is for. Two options, each spending a different budget:

- **Model-invoked** (default; omit `disable-model-invocation`). The agent can fire
  it autonomously, and *other skills can reach it by name*. Cost: **context load** —
  the description sits in the window every turn, whether or not the skill fires.
- **User-invoked** (`disable-model-invocation: true`). Only the human, typing the
  name, can invoke it; no other skill can reach it. Zero context load, but it
  spends **cognitive load** — *you* become the index that has to remember it
  exists. The `description` turns human-facing: a one-line summary, trigger lists
  stripped.

Pick model-invoked only when the agent must reach the skill on its own, or when
another skill invokes it by name (check: does any `SKILL.md` reference `/<name>`?).
A skill that only ever fires by hand should be user-invoked and pay nothing.

Two consequences worth planning for:

- **Collision control.** Two skills answering to the same word only actually
  compete if both are model-invocable. Marking one user-invoked makes the clash
  disappear without deleting either.
- **Router skills.** When user-invoked skills multiply past what you can remember,
  that piled-up cognitive load is cured by a **router**: one user-invoked skill
  that names the others and says when to reach for each.

## Writing the description (the discovery surface)

Claude picks among many skills using only name + description, so this is where to
invest. A good description packs three things:

1. **What it does** — concrete, third-person or imperative ("Audits…", "Finds…").
2. **When to use it** — the situation/intent.
3. **Trigger phrases** — the literal words a user types ("Use when the user says
   'review PR 42', 'check my inbox', or invokes /pr-review").

Avoid: vague ("helps with documents"), first/second person ("I can help…"),
time-sensitive claims ("as of August…" — put dated facts in references instead).

## Progressive disclosure

Three levels, each loaded only when needed:

1. name + description — always in context (keep tight).
2. `SKILL.md` body — loaded when the skill fires. **Keep under ~500 lines.** It's
   a spine: numbered steps + output contract + error table. No essays Claude
   already knows.
3. Bundled files — loaded/executed on demand, zero cost until read.

Rules:
- **References exactly one level deep** from `SKILL.md` (no ref→ref→ref chains —
  partial reads miss nested content).
- **Any reference > ~100 lines opens with a `## Contents` TOC** so a partial read
  still shows full scope.
- Organize references by **domain** (e.g. `backend-rules.md`), not `doc1/doc2`.
- **Scripts are executed, not read** — say "Run `x.py`" (execute) vs "see `x.py`
  for the algorithm" (read). Prefer execution; it's reliable and token-cheap.

## Steps and completion criteria

Every numbered step ends on a **completion criterion** — the condition that tells
the agent the step is done. Two properties:

- **Checkable** — the agent can tell done from not-done without guessing.
- **Exhaustive where it matters** — "every changed file accounted for", not
  "produce a list of changes". A vague criterion invites **premature completion**:
  the agent does three of nine units and reports success.

Bad: "Review the diff for issues."
Good: "Every file in `git diff --name-only <base>...HEAD` appears in the findings
table or in the explicitly-skipped list, with a reason."

This binds flat reference skills too — "every rule applied" is as good a criterion
as "every step done".

## Subagents (when the skill fans out)

- **One focused job per agent**; a detailed system prompt; a `description` Claude
  can match.
- **Scope tools + model per agent.** Cheap/read-only work → Haiku/Sonnet; the
  orchestrator does the judgment. Grant only the tools it needs.
- **Prefer one parameterized agent** over N near-identical ones when they share a
  tool/model profile (pass `lens`/`ecosystem`/`shard` + a checklist).
- **Inline the payload** into the dispatch — don't make the agent re-read files.
- **Return a tight summary, not a dump** — many verbose returns re-bloat the
  orchestrator's context. Write detail to a shared `output_dir/<unit>.md`; return
  a one-line status.
- **Restrict fan-out:** the orchestrator's `tools` can allowlist
  `Agent(worker-a, worker-b)`; omit `Agent` to forbid spawning.
- Spawn all independent agents **in a single message** so they run concurrently.

## House conventions for THIS repo

- Plugin layout: `plugins/<name>/{.claude-plugin/plugin.json, skills/<name>/SKILL.md,
  agents/*.md, skills/<name>/{references,scripts}/}`.
- `plugin.json`: `name`, `description`, `author`. Register in the root
  `.claude-plugin/marketplace.json` with `category` + `source: ./plugins/<name>`.
- Document each skill in `README.md` (a `### /<name>` section + the structure tree).
- Skills use `allowed-tools` (the Claude Code plugin flavor supports it even
  though the API Agent-Skills spec omits it).
- Commit/push only when asked; develop on a branch, never push to `main` directly.

## Anti-pattern checklist (run at Step 5)

Flag and fix any of these in the new skill:

- [ ] Vague description, or first/second-person, or missing trigger phrases.
- [ ] Invocation never chosen: model-invocable by default when nothing (no user,
      no other skill) needs the agent to reach it on its own — paying context
      load for nothing.
- [ ] A step with no completion criterion, or one too vague to check.
- [ ] `SKILL.md` over ~500 lines, or over-explains things Claude already knows.
- [ ] A reference nested more than one level deep, or a >100-line reference with
      no `## Contents` TOC.
- [ ] Deterministic work (parsing/fetching/scoring) done in prose instead of a script.
- [ ] A script with an unexplained magic constant, or Windows-style backslash paths.
- [ ] `allowed-tools` missing or broader than needed.
- [ ] Orchestrator pattern used for trivial/sequential work (overhead not justified).
- [ ] Duplicated near-identical agents that should be one parameterized agent.
- [ ] Agents that return verbose dumps instead of a summary + status, or that
      aren't tool/model-scoped.
- [ ] No output contract; no error-handling table.
- [ ] No confidence/severity discipline; findings can be fabricated to look thorough
      (a clean result must be a valid result).
- [ ] Not registered in `marketplace.json` / `README.md`; `plugin.json` doesn't parse.
