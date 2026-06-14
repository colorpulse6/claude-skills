---
name: marketplace-lint
description: >-
  Validate every plugin in this marketplace for structural + registration
  consistency — valid plugin.json, name matches its directory, registered in
  marketplace.json and the README, SKILL.md frontmatter present, scripts
  executable and compilable, and references over 100 lines carrying a Contents
  TOC. Use when the user says "lint the marketplace", "validate the plugins",
  "check the skills repo", "are all my plugins registered", or invokes
  /marketplace-lint. Run it before pushing a new or edited plugin.
user-invocable: true
argument-hint: "[plugin-name to lint just one | (default: all)]"
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# Marketplace Lint

Keeps this skills marketplace internally consistent. As the repo grows, plugins
drift: a new one isn't registered, a renamed dir no longer matches its
`plugin.json`, a script loses its `+x` bit, a reference grows past 100 lines
without a TOC. This runs the deterministic checks (the ones a maintainer
otherwise does by hand) and reports what's off.

The work is a fast, sequential filesystem scan — no subagents needed.

---

## Step 1: Run the linter

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/marketplace-lint/scripts/marketplace-lint.py" [plugin-name]
```

With no argument it lints every plugin under `plugins/`; pass a single
plugin name to scope it. It emits JSON: `{ plugins, findings: [{plugin, level,
check, detail}], summary: {error, warn, ok} }` and exits non-zero if there are
any `error`-level findings.

What it checks per plugin:

- **plugin.json** exists, parses, has a `name`, and `name` matches the directory.
- **Registration** — listed in the root `.claude-plugin/marketplace.json` with a
  `source` of `./plugins/<name>`, and mentioned in `README.md`.
- **SKILL.md** exists and has YAML frontmatter with `name` + `description`; the
  frontmatter `name` matches.
- **Scripts** under the plugin are executable (`+x`); `.py` scripts compile.
- **References** over 100 lines open with a `## Contents` TOC (within their first
  ~15 lines).

## Step 2: Triage & report

Read the JSON. Present a short summary (counts) + the `error`/`warn` findings
grouped by plugin. `error` = will break discovery/use (unregistered, invalid
JSON, name mismatch, broken script). `warn` = drift worth fixing (missing TOC,
script not `+x`, no README mention).

## Step 3: Offer to fix (only the safe, mechanical ones)

For deterministic findings, offer to fix in place: `chmod +x` a script, add a
`## Contents` TOC to a long reference, add a missing `marketplace.json`/README
entry. **Do not invent content** — if a fix needs judgment (e.g. writing a real
description), surface it for the user instead. Apply fixes only on request.

## Output contract

Print: (1) a one-line summary (`N plugins — E errors, W warnings`), (2) findings
grouped by plugin as `LEVEL  check — detail`, (3) a verdict: `clean` /
`warnings only` / `errors — fix before merge`.

## Error handling

| Scenario | Action |
|----------|--------|
| Not run from the repo root / no `plugins/` dir | Report it; the script resolves the repo root via git and errors clearly if absent. |
| Named plugin doesn't exist | Report the missing plugin; lint nothing else. |
| `marketplace.json` itself is invalid JSON | Report as a top-level error; skip the registration cross-checks. |
| All checks pass | Say so plainly — a clean marketplace is the expected steady state. |
