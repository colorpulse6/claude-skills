#!/usr/bin/env bash
# collect.sh — deterministic unit collector for the skill-starter template.
#
# Usage: collect.sh [target-glob-or-dir]
#   - no arg:        list git-tracked text files in the repo
#   - a directory:   list files under it (recursively)
#   - a glob/path:   expand it
#
# Output: JSON { "target": "...", "count": N, "units": ["path", ...] } on stdout.
# Exit 0 even when count is 0 (the orchestrator decides what to do with empty).
set -euo pipefail

target="${1:-}"

emit_json() {
  # $1 = target label; remaining stdin = newline-separated paths
  local label="$1"
  local -a paths=()
  while IFS= read -r line; do
    [ -n "$line" ] && paths+=("$line")
  done
  local esc_label=${label//\\/\\\\}; esc_label=${esc_label//\"/\\\"}
  printf '{\n  "target": "%s",\n  "count": %d,\n  "units": [' "$esc_label" "${#paths[@]}"
  local first=1
  for p in "${paths[@]:-}"; do
    [ -z "$p" ] && continue
    if [ "$first" -eq 1 ]; then first=0; else printf ','; fi
    local esc=${p//\\/\\\\}; esc=${esc//\"/\\\"}
    printf '\n    "%s"' "$esc"
  done
  [ "${#paths[@]}" -gt 0 ] && printf '\n  '
  printf ']\n}\n'
}

if [ -z "$target" ]; then
  # Default: git-tracked files, skipping obvious binaries.
  git ls-files 2>/dev/null \
    | grep -Ev '\.(png|jpg|jpeg|gif|webp|ico|pdf|zip|gz|woff2?|ttf|mp4|mov)$' \
    | emit_json "git-tracked text files"
elif [ -d "$target" ]; then
  find "$target" -type f 2>/dev/null | emit_json "$target"
else
  # Treat as a glob/path; let the shell expand it.
  # shellcheck disable=SC2086
  ls -1 $target 2>/dev/null | emit_json "$target"
fi
