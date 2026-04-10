# Output Contract

Return your review as a **single JSON object** matching the schema below. No prose before or after the JSON. No markdown code fences around it. The first character of your response must be `{` and the last character must be `}`.

## Schema

```json
{
  "verdict": "approve | request-changes | comment",
  "summary": "1-3 sentence high-level summary of the PR and your overall take",
  "description_alignment": {
    "status": "aligned | drift | missing",
    "notes": "Brief explanation if drift or missing, otherwise empty string"
  },
  "strengths": [
    "Specific thing done well (reference file if relevant)",
    "Another specific strength"
  ],
  "findings": [
    {
      "severity": "critical | important | minor",
      "title": "Short title (under 60 chars)",
      "file": "path/to/file.ts",
      "line": 42,
      "line_end": 45,
      "diff_hunk": "The actual lines from the diff that contain the issue",
      "explanation": "What is wrong",
      "why": "Why it matters - impact, consequences, what could go wrong",
      "suggestion": "Prose description of the fix",
      "suggestion_code": "Optional: exact code replacement for a GitHub suggestion block. Omit if not a simple line replacement."
    }
  ]
}
```

## Field Rules

### `verdict`

One of exactly three strings:

- `"approve"` - no blocking issues, safe to merge
- `"request-changes"` - one or more Critical findings, or multiple Important findings that together warrant blocking
- `"comment"` - findings exist but none are blockers; the author should consider them

Choose based on the highest-severity finding, not the count.

### `summary`

1-3 sentences. First sentence: what the PR does. Optional second/third sentence: your overall take (e.g., "Implementation is clean but the error handling in `X` needs attention."). Do not restate the diff.

### `description_alignment`

- `status = "aligned"` if the PR description accurately describes the diff
- `status = "drift"` if the diff does something the description doesn't mention, or vice versa
- `status = "missing"` if the description is empty or absent
- `notes`: empty string if aligned; one sentence otherwise

### `strengths`

Array of 1-3 strings. Each should be a **specific** observation, not generic praise. Reference files where possible.

Good: `"Clean extraction of the retry logic into src/lib/retry.ts - nicely reusable"`
Bad: `"Good code quality"`

Empty array is allowed if nothing stands out.

### `findings`

Array of finding objects. Order by severity: all `critical` first, then `important`, then `minor`. Within a severity level, order by file path alphabetically.

**Empty array is valid and encouraged when there are no issues.** Do not pad with fake minor findings to appear thorough.

#### Finding object fields

- **`severity`**: exactly one of `"critical"`, `"important"`, `"minor"` (lowercase)
- **`title`**: short title under 60 characters, no trailing period
- **`file`**: the exact file path as it appears in the diff (e.g., `"apps/web/src/pages/Dashboard.tsx"`)
- **`line`**: line number in the **NEW** version of the file (right side of the diff). This is what GitHub uses to position the comment. NEVER use hunk offsets, array indices, or old-file line numbers.
- **`line_end`**: end line (inclusive) if the issue spans multiple lines; otherwise set equal to `line`
- **`diff_hunk`**: the actual lines from the diff containing the issue (3-10 lines of context is ideal). Include the `+`/`-`/` ` prefix as it appears in the diff.
- **`explanation`**: 1-3 sentences describing what is wrong
- **`why`**: 1-3 sentences describing why it matters - what breaks, what the consequences are, what the blast radius is
- **`suggestion`**: prose description of the fix. Always required.
- **`suggestion_code`**: optional. Include **only** when the fix is a simple, exact replacement of the lines referenced by `line`/`line_end`. This will be rendered as a GitHub suggestion block the author can apply with one click. Omit (don't include the key, or set to empty string) if the fix requires multiple non-contiguous edits, structural changes, or new files.

## Line Number Semantics

**This is the most common source of bugs in automated PR review.**

- Line numbers refer to the **NEW** file version (right side of the diff)
- They are 1-indexed line numbers in the file as it exists on the PR branch
- They are NOT hunk offsets, NOT old-file line numbers, NOT relative positions

If a finding concerns a deletion (a line that was removed and has no new equivalent), position the comment on the nearest surrounding line in the new file and mention the deletion in the `explanation`.

## Using `suggestion_code` vs Prose Suggestion

- **Use `suggestion_code`** when the fix is: "replace these exact lines with these exact lines." Examples: rename a variable, fix a typo, add a missing `await`, add a null check on one line, change an operator.
- **Use prose `suggestion` only** when the fix is: conceptual, spans multiple files, requires new abstractions, or needs the author to make design decisions.

When `suggestion_code` is provided, the prose `suggestion` should still be present and describe the change in words. The suggestion block complements, doesn't replace, the prose.

## Ordering

Within the `findings` array:

1. All `critical` findings first
2. Then all `important` findings
3. Then all `minor` findings
4. Within each severity, order alphabetically by `file`, then by `line` ascending

## Empty Findings

If the PR has no issues worth flagging:

```json
{
  "verdict": "approve",
  "summary": "...",
  "description_alignment": { "status": "aligned", "notes": "" },
  "strengths": ["..."],
  "findings": []
}
```

This is the correct response. Do not invent findings. Do not pad. A clean PR deserves a clean review.

## Final Reminders

- Return valid JSON only. No markdown fences. No prose.
- `file` and `line` must be real values from the diff - never hallucinate them.
- `line` uses the NEW file version.
- Empty `findings` is encouraged when appropriate.
- `strengths` should be specific, not generic.
