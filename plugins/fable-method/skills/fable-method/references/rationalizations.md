# Rationalizations — the excuse table

Every entry is an excuse agents actually produce, what it really means, and
the required action. If you find yourself generating a paraphrase of the left
column, the right column is not optional. (Format borrowed from the Fable-era
distillation skills: verbatim excuse → rebuttal, because models argue with
principles but not with their own quoted words.)

## Verification excuses

| The excuse | What it actually means | Required action |
|---|---|---|
| "It probably works" / "this should work now" | I have not run it | Run it. Paste the output. |
| "The tests pass, so the feature works" | I verified compilation-adjacent facts, not the claim | Exercise the changed path end-to-end; a green suite is the RUNS rung, not VERIFIED. |
| "I've verified the logic by reading it" | I reread my own code and agreed with myself | Reading is not a rung on the ladder. Execute something. |
| "The remaining failures are pre-existing" | I did not check whether they are | `git stash && <test cmd>` — prove the baseline, then say it with the evidence. |
| "The test is flaky" | The test caught something I don't understand yet | Root-cause or report it as open; never silence, retry-until-green, or skip. |
| "Verification would be expensive here" | I'm about to skip it silently | Defer it *with consent*: stage the work, propose the verifying run, deliver as unverified. |

## Scope and effort excuses

| The excuse | What it actually means | Required action |
|---|---|---|
| "While I'm here, I'll also…" | I'm about to widen the diff nobody asked for | Park it in the report's threads list. One line costs nothing. |
| "This adjacent bug is quick to fix" | Two threads are about to blur into one unreviewable diff | Same: park it, name it, finish the actual task. |
| "A more robust solution would be…" | I'm gold-plating instead of solving | Smallest change that fully solves it. Note the fancier option in the report. |
| "I'll add handling for cases that might come up" | Speculative code with no observed need | YAGNI. Handle observed cases; name the unhandled ones. |
| "One more retry should do it" (no new evidence) | The approach is wrong and I'm paying the same toll twice | Two identical failures ⇒ stop, re-enter MAP. |

## Reporting excuses

| The excuse | What it actually means | Required action |
|---|---|---|
| "Done! Everything works" (no evidence cited) | Optimism formatted as a status report | Attach the rung + evidence per claim, or downgrade the claim. |
| "I'll describe what I'm about to do" (turn ends, nothing ran) | Narration substituted for action | If the last paragraph is a promise, execute it now — tool calls, not intent. |
| "This summary is close enough" | The user will have to re-ask | Rewrite: outcome first, paths, rungs, open threads, residual risk. |
| "No issues found" (after a shallow pass) | I searched until it looked fine | State exactly what was searched and how; a clean result is only valid if the search was real. |

## Context and memory excuses

| The excuse | What it actually means | Required action |
|---|---|---|
| "I remember this codebase" | I remember a snapshot of it | `git log --since` + reread the load-bearing files. |
| "The docs/comments say so" | I'm trusting prose over executable truth | Read the code; code outranks prose, live state outranks both. |
| "The pack/notes from last time say X" | X was true at snapshot time | Freshness rule: verify before relying. Packs are maps, not territory. |
| "I'm running low on context, better wrap up" | Anxiety, not evidence | The harness manages context. Finish the task; never degrade work quality to save tokens you weren't asked to save. |

## Meta

The table grows: when a *new* excuse survives long enough to cause a bad
report or a broken handoff, add it here verbatim with its rebuttal. That is
the cheapest form of self-training that persists across sessions.
