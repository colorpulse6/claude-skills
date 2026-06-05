---
name: session-recap
description: >-
  Generates a self-contained, browser-viewable HTML timeline of your recent
  Claude Code sessions — grouped by day, with key decisions, PRs, commits,
  files touched, active time, and a resume command per session. Parses
  ~/.claude/projects transcripts; defaults to the last 7 days (pass a number or
  "daily"/"weekly" to change). Use when the user wants a daily or weekly recap,
  asks "what did I work on", "summarize my Claude sessions", "session timeline",
  or invokes /session-recap.
user-invocable: true
allowed-tools: Bash, Read, Write, Agent
---

# Session Recap

Turn your raw Claude Code transcripts into a visual weekly (or daily) recap:
a dark "flight recorder" timeline you open in the browser. Fast pure-Python
extraction does the bulk; one bounded LLM pass adds the key decisions.

`SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/session-recap/scripts"` — all commands
below assume this. If `$CLAUDE_PLUGIN_ROOT` is unset (running from source), set
`SCRIPTS` to this skill's `scripts/` directory.

Log progress as you go: `📋 step → result`.

---

## Step 0 — Resolve arguments

- **days**: default `7`. Map `daily`→1, `weekly`→7, `month`/`monthly`→30. A bare
  number in the invocation (e.g. `/session-recap 1`) is the day count.
- **out**: default `~/.claude/recaps` (a permanent dir — never `/tmp`, which is
  wiped on reboot). Honor an explicit `--out` if the user gives one.

---

## Step 1 — Parse transcripts (fast, free)

```bash
python3 "$SCRIPTS/build_timeline.py" --days <DAYS> --out <OUT>
```

Writes `<OUT>/sessions.json`. It prints `parsed N sessions (M notable) …`.
If `N == 0`, tell the user there are no sessions in that window and stop.

---

## Step 2 — Build digests for notable sessions

```bash
python3 "$SCRIPTS/build_digests.py" --out <OUT>
```

Writes `<OUT>/digests/<id>.txt` (stripped conversation prose) and
`<OUT>/digests/index.json` (the notable list with metadata). Read
`index.json` to get the list of session ids + titles to summarize.

---

## Step 3 — Summarize key decisions (the only LLM step)

Goal: produce `<OUT>/decisions.json` shaped as:

```json
{ "<session-id>": { "summary": "one factual sentence", "decisions": ["short bullet", "..."] } }
```

For each notable session, read its digest at `<OUT>/digests/<id>.txt` and write:
- `summary`: ONE concise factual sentence (≤ ~18 words) on what it accomplished.
- `decisions`: 2–4 short bullets (≤ 14 words each) — concrete choices made,
  problems solved, things shipped. If the session was trivial/abandoned, use
  0–1 bullets and say so. **Never invent decisions unsupported by the digest.**

**Pick the execution mode by count** (from `index.json`):

- **0 notable** → write `{}` to `decisions.json`. Skip to Step 4.
- **≤ 8 notable** → summarize inline yourself: Read each digest, then Write the
  merged `decisions.json`.
- **> 8 notable** → dispatch parallel subagents in batches of ~5 ids each (so a
  weekly recap is a handful of agents, not dozens). Each agent writes one
  `<OUT>/decisions/batchK.json` of the same shape. Use this prompt per batch:

  > You are summarizing Claude Code session digests for a recap. For each id in
  > [<ids>], read `<OUT>/digests/<id>.txt` and produce `summary` (one factual
  > sentence ≤18 words) and `decisions` (2–4 bullets ≤14 words; concrete choices/
  > outcomes only — never invent). Write a single JSON object
  > `{ "<id>": {"summary":..., "decisions":[...]} }` to `<OUT>/decisions/batchK.json`,
  > one entry per id. Reply only "done".

  Then merge all `decisions/batch*.json` into `<OUT>/decisions.json`:

  ```bash
  python3 - <<'PY'
  import json, glob, os
  out=os.path.expanduser("<OUT>"); m={}
  for f in sorted(glob.glob(os.path.join(out,"decisions","batch*.json"))):
      try: m.update(json.load(open(f)))
      except Exception as e: print("bad json", f, e)
  json.dump(m, open(os.path.join(out,"decisions.json"),"w"), ensure_ascii=False, indent=2)
  print("merged", len(m))
  PY
  ```

Verify `decisions.json` is valid JSON and covers every notable id before moving on.

---

## Step 4 — Render the HTML

```bash
python3 "$SCRIPTS/render_html.py" --out <OUT>
```

Writes `<OUT>/recap-YYYY-MM-DD.html` (single self-contained file, data inlined,
works offline). The script's last printed line is the file path.

---

## Step 5 — Open it

```bash
open "<PATH>"            # macOS
# xdg-open "<PATH>"      # Linux
```

Then report: day range, session count, notable count, PRs, commits, and the
file path. Keep it short — the page is the deliverable.

---

## Notes

- **Only top-level sessions count.** `~/.claude/projects/*/*.jsonl` are real
  sessions; `subagents/*.jsonl` are internal and intentionally ignored.
- **Duration is active time**, not wall-clock — inter-message gaps over 30 min
  are dropped, so resumed sessions don't show absurd multi-day spans.
- **PRs / commits / files** are pattern-detected from tool calls and output
  (PR URLs, `gh pr create`, `git commit`, Edit/Write paths) — fast and free.
- Re-running is cheap; intermediate `sessions.json` / `digests/` / `decisions/`
  stay in `<OUT>` and are overwritten next run.
