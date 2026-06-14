# Skill Authoring Guide

Distilled from Anthropic's official skill-authoring best practices and a survey of
strong community plugins (Anthropic's `code-review`/`security-review`, superpowers,
claude-seo, wshobson/agents, and others). This is the substance Step 4 writes
against.

## Contents
- Frontmatter that matters
- Writing the description (the discovery surface)
- Progressive disclosure
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
