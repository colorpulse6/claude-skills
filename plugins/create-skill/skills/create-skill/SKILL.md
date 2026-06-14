---
name: create-skill
description: >-
  Authors a new Claude Code skill/plugin in this marketplace, the right way.
  Interviews for intent and trigger phrases, decides the shape (inline skill vs
  orchestrator + parallel specialist agents), scaffolds the files, writes them
  against a distilled authoring guide, self-reviews against an anti-pattern
  checklist, and registers the plugin in the marketplace + README. Use when the
  user says "create a skill", "scaffold a plugin", "new skill", "add a skill to
  the marketplace", or invokes /create-skill.
user-invocable: true
argument-hint: "[skill name or one-line intent]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Create Skill

Builds a new skill/plugin for this repo, applying the authoring research behind
its existing plugins. Two bundled references hold the substance — read them when
you reach the step that needs them, not before:

- `${CLAUDE_PLUGIN_ROOT}/skills/create-skill/references/authoring-guide.md` —
  frontmatter, descriptions, progressive disclosure, anti-patterns.
- `${CLAUDE_PLUGIN_ROOT}/skills/create-skill/references/patterns.md` —
  inline-vs-agents decision, the parameterized-agent pattern, scripts-for-
  determinism, and the shared quality conventions (severity / confidence /
  status enum / falsifiability).

---

## Step 1: Understand the need (interview)

Establish four things. If the argument doesn't answer them, **ask the user one
question at a time** (don't dump a survey):

1. **What does the skill do?** (one sentence)
2. **When should it fire?** — the concrete trigger phrases a user would type.
3. **Inputs & outputs** — what it consumes (a diff? a URL? a doc?) and what it
   produces (a report file? edits? a PR comment?).
4. **Determinism** — what parts must be repeatable (parsing, fetching, scoring)?
   Those belong in a script, not in prose.

State your understanding back before building. **YAGNI** — don't design for
needs the user didn't state.

## Step 2: Pick the shape

Use the decision rubric in `patterns.md`. The short version:

- **Inline skill** (just a `SKILL.md`) — work is small, sequential, or needs
  back-and-forth. This is the default; prefer it.
- **Orchestrator + parallel agents** — work splits into *independent* units that
  are slow/voluminous enough that parallelism and context-isolation pay for the
  coordination overhead (e.g. per-file, per-lens, per-ecosystem).
- Add a **script** whenever there's deterministic mechanical work.
- Add **`references/`** for any lookup tables / checklists / knowledge.

State the chosen shape and *why* (one line). Don't reach for agents by reflex —
the overhead isn't free.

## Step 3: Scaffold

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/create-skill/scripts/scaffold.sh" <plugin-name> [--agent] [--script] [--reference]
```

Creates `plugins/<plugin-name>/` with `.claude-plugin/plugin.json`,
`skills/<plugin-name>/SKILL.md`, and the optional `agents/` / `scripts/` /
`references/` you asked for — each a stub with `TODO:` markers. Pick a
kebab-case name that reads as the slash command.

## Step 4: Write the files

Open `authoring-guide.md` and write the skill against it. Non-negotiables:

- **Description** = third-person/imperative *what it does* + *when to use it* +
  literal trigger phrases. This is the discovery surface — invest here first.
- **`SKILL.md` stays a thin spine** (< 500 lines): numbered steps, an output
  contract, an error-handling table. Push detail into `references/` (one level
  deep; any reference > 100 lines opens with a `## Contents` TOC).
- **`allowed-tools`** scoped to what the skill needs (this repo's convention).
- **Scripts do the deterministic work**; justify any magic constant; forward
  slashes only.
- If agents: one **parameterized** agent over many near-identical lenses (don't
  duplicate); `model`/`maxTurns`/least-privilege `tools` per agent; return a
  **tight summary + status enum**, write detail to a shared `output_dir`.
- Apply the shared quality conventions from `patterns.md` (confidence-gate,
  falsifiability, "a clean result is valid").

## Step 5: Self-review

Run the new skill against the **anti-pattern checklist** at the bottom of
`authoring-guide.md`. Fix anything it flags. Then `py_compile` any Python and
`python3 -c 'import json; json.load(...)'` the `plugin.json`.

## Step 6: Register & verify

- Add the plugin to `.claude-plugin/marketplace.json` (match the existing entry
  shape: name, description, `category`, `source: ./plugins/<name>`, author,
  homepage).
- Add a `### /<name>` section to `README.md` (features + usage) and the repo-
  structure tree.
- `chmod +x` any scripts. Validate all JSON parses. Report what you built.

> Commit/push only when the user asks (this repo branches off `main`).

## Error handling

| Scenario | Action |
|----------|--------|
| Intent unclear after the argument | Ask the 4 interview questions one at a time; don't guess and build the wrong thing. |
| Name collides with an existing plugin | Stop; propose an alternative name. |
| User wants agents for trivial/sequential work | Recommend inline instead; explain the overhead. Build agents only if they insist. |
| `scaffold.sh` target dir exists | Refuse to overwrite; report the path. |
| Skill duplicates an existing plugin | Flag the overlap; ask whether to extend the existing one instead. |
