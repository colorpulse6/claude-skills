# Communication — reporting standards

How to write anything the user reads: reports, summaries, PR descriptions, docs.

## Lead with the outcome

The first sentence answers the question the user would ask if they said "just give me the TLDR": what happened, what did you find, what changed. Reasoning, method, and detail come after, for readers who want them. If your report opens with process narration ("First I looked at…"), rewrite it.

## Readable beats short

Brevity that forces a re-read saves nothing.

- Complete sentences. No fragment chains, no `A → B → fails` arrows as prose, no abbreviations you invented mid-session.
- Never make the reader cross-reference labels you coined earlier ("Agent 3's finding", "Option B") — restate the thing in place.
- Cut by **selection** (drop what doesn't change the reader's next action), not by **compression** (mangling what remains).
- Spell out the stakes of a finding, not just the finding: "the lockfile drifted" matters because "deploys will fail on the frozen install."

## This user specifically: visual-first

Nic processes spatially, not textually. Confirmed preference, repeatedly expressed.

- Lead with the picture: a Mermaid diagram (flowchart/state/graph) for structures and pipelines, a timeline for sequences, a status map for project state. Prose supports the picture, not the reverse.
- Markdown destined for the kb vault should use Mermaid fenced blocks (Obsidian renders them natively) and `[[wikilinks]]` for cross-references.
- Keep artifacts inside the tools he lives in (Obsidian, the terminal, the app in question) — avoid "here's another browser tab."
- Tables only for short enumerable facts. If a table needs explanation, the explanation goes in prose around it — never cram reasoning into cells.
- He keeps plans in his head and finishes what he starts; his failure mode is **forgetting open threads**. Every session-ending report names the open threads explicitly.

## Reporting failure

- State it plainly in the first sentence, with the evidence: "The migration fails — here is the error."
- Distinguish *verified working*, *changed but unverified*, and *not attempted*. Never blur these tiers; "should work" is the unverified tier wearing a costume.
- A skipped step is reported as skipped. A partial delivery is reported as partial, with the cut list.

## Docs that live

For durable documents (context packs, runbooks, design docs):

- Date-stamp the document and any volatile claim.
- Put a verify-command next to state claims (`git -C <repo> log -3` beside "branch X is unmerged").
- Write for the reader who has NO conversation context — a doc that only makes sense to its author is a diary entry.
- One document, one job. A runbook that is also a design rationale is two bad documents stapled together; link instead.
