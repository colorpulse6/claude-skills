# Codex / non-Claude-Code adaptation

How to follow every skill in this marketplace when you are NOT running inside Claude Code (Codex CLI, a bare API agent, or a future harness). The methods are harness-independent; only the mechanics translate.

## Loading skills

No Skill tool? Read the `SKILL.md` file directly and treat its body as instructions. Skills live at `plugins/<name>/skills/<name>/SKILL.md` in this repo; their `references/` load on demand — read them when the SKILL.md points you there, not preemptively.

## Tool translation

| Claude Code concept | Generic / Codex equivalent |
|---|---|
| Read / Write / Edit tools | Your file-read/patch mechanism; same read-before-write rules apply |
| Bash tool | Your shell; same reversibility gate applies |
| Grep / Glob tools | `rg`, `grep -r`, `find` |
| Subagents (Task/Agent tool) | Sequential passes with written checkpoints (see research-method.md), or spawn `codex exec` / `claude -p` child runs where available |
| TodoWrite / task tracking | A `PLAN.md` or scratch checklist file you keep updated |
| AskUserQuestion | Ask inline and stop; one sharp question with a recommended default |
| Plan mode / ExitPlanMode | Write the plan to a file, present it, get explicit approval before editing |
| MCP servers (Slack, browser, etc.) | CLI equivalents (`gh`, `curl`), or report the capability gap instead of faking it |
| `/slash-command` invocation | The user pasting or naming the skill; treat "use the X skill" as the trigger |

## Cross-model etiquette

- **Cross-review is a feature.** Claude reviewing Codex output (and vice versa) catches more than either reviewing itself — different families, different blind spots. Invoke the other CLI read-only when available: `codex exec --sandbox read-only "review this diff for …"` or `claude -p "review …"`.
- **Shared state lives in files, not in either model's memory.** Handoffs between models go through committed code, dated notes, and the kb vault — never "as discussed."
- **Same bar, any model.** Verification-before-done and the reversibility gate are not Claude conventions; they are the job.

## Degraded-harness rules

Operating with fewer affordances (no sandbox, no parallel calls, no visual output):

1. Slower is acceptable; skipping VERIFY is not.
2. If you cannot run the code, say "unverified" in the report — the tier system in communication.md survives every harness.
3. If you cannot parallelize, sequence by value: the task's critical path first, enrichment after.
4. If you cannot render a diagram, write the structure as an indented outline — spatial intent preserved even in plain text.
