# Triage rubric — aging, noise, and reconciliation

## Aging thresholds

Age a thread from its last evidence of life: last commit touching it, the pack
snapshot date that declared it, or the daily-log line that mentioned it —
whichever is newest.

| State | Age | Meaning |
|---|---|---|
| ACTIVE | < 7 days | In motion; do not nag. |
| COOLING | 7–13 days | Mention in the full table only. |
| AT_RISK | 14–29 days | Candidate for the top-5. 14 days mirrors `STALE_PROJECT_DAYS` in `~/kb/CLAUDE.md` so this radar and the KB age projects identically. |
| COLD | ≥ 30 days | Only surfaces in the top-5 if the trapped work is large (e.g. an unpushed branch with real commits) — otherwise it's archaeology, not a thread. |

## Noise filters (don't report these as forgotten work)

- Repos whose name marks them retired: `(depr)`, `-old`, `-archive`, `legacy`.
- Repos > 1 year stale **and** mentioned in no pack — abandoned, not forgotten.
  One line in the full table ("N retired repos carry dirt; say 'include
  archives' to see them"), never in the top-5.
- `local_only` repos are not "unpushed" — no remote is a deliberate state for
  some repos (the KB is local-only by design). Their dirty files still count.
- Tooling/scratch checkouts (forks you never committed to, tutorial clones):
  zero user commits ⇒ skip.

## Ranking the top-5 (risk = size of loss × likelihood of forgetting)

Prefer, in order:
1. **Single-copy work** — unpushed commits or dirty files that exist on one
   disk only. Largest possible loss.
2. **Silent threads** — git evidence no pack mentions. Nothing will remind him.
3. **Declared threads gone stale** — a pack "Next:" older than 14 days.
4. **Blocked-on-a-decision threads** — cheap to unblock, expensive to forget
   (e.g. outreach stalled on a name choice).

Cap at 5. Ten "top" threads is a todo list, not a radar; the full table
carries the rest.

## Pack-drift reconciliation

For each load-bearing pack claim, check the sweep/git before repeating it:

- Pack says branch open → branch merged or gone ⇒ thread is DONE; report as
  drift, not as an open thread.
- Pack says "Next: X" → git shows commits doing X after the snapshot ⇒
  re-age from the newest commit, flag the pack line for healing.
- Pack names a path → path missing ⇒ drift; say what you searched.

Never present a pack claim you could have verified but didn't. If verification
was impossible (repo not on this machine), label the thread `[UNVERIFIED]`.

## First moves

A first move must be executable within ~15 minutes and stated concretely:
`git -C ~/x push origin main`, "reply to the Lemon Squeezy email", "pick
between the two names in sites-outreach-playbook.md". "Work on billing" is a
project, not a first move.
