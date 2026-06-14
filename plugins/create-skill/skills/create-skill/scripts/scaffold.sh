#!/usr/bin/env bash
# scaffold.sh — generate a new plugin skeleton for this marketplace.
#
# Usage: scaffold.sh <plugin-name> [--agent] [--script] [--reference]
#   <plugin-name>  kebab-case; becomes the slash command and the dir name.
#   --agent        also create agents/<name>-worker.md (parameterized agent stub)
#   --script       also create skills/<name>/scripts/<name>.py (deterministic stub)
#   --reference    also create skills/<name>/references/guide.md (TOC'd stub)
#
# Creates plugins/<plugin-name>/ relative to the repo root. Refuses to overwrite.
set -euo pipefail

name="${1:-}"
if [ -z "$name" ] || [[ "$name" == --* ]]; then
  echo "error: first arg must be a kebab-case plugin name" >&2; exit 1
fi
if ! [[ "$name" =~ ^[a-z][a-z0-9-]*$ ]]; then
  echo "error: name must be lowercase kebab-case (got '$name')" >&2; exit 1
fi
shift || true
want_agent=0 want_script=0 want_reference=0
for flag in "$@"; do
  case "$flag" in
    --agent) want_agent=1 ;;
    --script) want_script=1 ;;
    --reference) want_reference=1 ;;
    *) echo "error: unknown flag '$flag'" >&2; exit 1 ;;
  esac
done

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
base="$root/plugins/$name"
[ -e "$base" ] && { echo "error: $base already exists; refusing to overwrite" >&2; exit 1; }

mkdir -p "$base/.claude-plugin" "$base/skills/$name"

cat > "$base/.claude-plugin/plugin.json" <<EOF
{
  "name": "$name",
  "description": "TODO: what it does + key features (one or two sentences).",
  "author": {
    "name": "Nichalas Barnes"
  }
}
EOF

cat > "$base/skills/$name/SKILL.md" <<EOF
---
name: $name
description: >-
  TODO: what it does + when to use it + literal trigger phrases. Use when the
  user says "...", "...", or invokes /$name.
user-invocable: true
argument-hint: "[...]"
allowed-tools: Bash, Read, Write, Glob, Grep
---

# ${name//-/ }

TODO: one-paragraph framing — what this does and the principle behind it.

## Step 1: ...

TODO: numbered steps. Push detail into references/; run scripts for determinism.

## Output contract

TODO: name the file(s) written and the exact sections/table columns.

## Error handling

| Scenario | Action |
|----------|--------|
| Empty input | TODO |
| Partial failure | TODO |
| Missing tool/input | TODO |
EOF

if [ "$want_agent" -eq 1 ]; then
  mkdir -p "$base/agents"
  cat > "$base/agents/$name-worker.md" <<EOF
---
name: $name-worker
description: >-
  TODO: single-job worker for the $name plugin. Spawned in parallel by the
  orchestrator; writes findings to output_dir/<unit>.md.
model: sonnet
maxTurns: 20
tools: Read, Bash, Glob, Grep, Write
---

# ${name//-/ } Worker

Inputs (from the orchestrator, inline): TODO.

## What to do
1. TODO.
2. Write \`output_dir/<unit>.md\` and return a status line:
   \`<unit>: DONE|DONE_WITH_CONCERNS|BLOCKED — N items\`.

## Discipline
- Cite evidence; confidence-gate at ≥ 0.7; a clean result is valid.
EOF
fi

if [ "$want_script" -eq 1 ]; then
  mkdir -p "$base/skills/$name/scripts"
  cat > "$base/skills/$name/scripts/$name.py" <<EOF
#!/usr/bin/env python3
"""$name.py — TODO: the deterministic work for the $name skill. Emits JSON."""
import json
import sys


def main():
    # TODO: do the deterministic work; print structured JSON for the skill to read.
    print(json.dumps({"todo": True}, indent=2))


if __name__ == "__main__":
    main()
EOF
  chmod +x "$base/skills/$name/scripts/$name.py"
fi

if [ "$want_reference" -eq 1 ]; then
  mkdir -p "$base/skills/$name/references"
  cat > "$base/skills/$name/references/guide.md" <<EOF
# ${name//-/ } Guide

TODO: the lookup tables / checklists / knowledge this skill cites.

## Contents
- TODO

## TODO
EOF
fi

echo "Scaffolded plugins/$name/"
find "$base" -type f | sed "s|$root/||" | sort | sed 's/^/  /'
echo
echo "Next: fill the TODOs (see ../references/authoring-guide.md), then register in"
echo ".claude-plugin/marketplace.json and README.md, and validate the JSON."
