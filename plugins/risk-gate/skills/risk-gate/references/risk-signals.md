# Risk Signals & Scoring

How `risk_score.py` scores each changed file. `risk = likelihood × impact`; these
signals approximate both. **All weights are heuristic defaults — tune to your
codebase's real incident history.** No signal is a magic constant: each is
justified below.

## Contents
- Impact signals (where the change lands)
- Likelihood signals (how much / how complex)
- Bucketing thresholds
- How to tune

## Impact signals — *where* the change lands (high blast radius)

Path/content keyword matches. Each category that fires adds weight because a bug
here hurts more.

| Signal | Weight | Why |
|--------|--------|-----|
| Auth / authz (`auth`, `login`, `password`, `session`, `token`, `permission`, `rbac`) | +3 | Bug = account takeover / data exposure. |
| Money (`payment`, `billing`, `charge`, `invoice`, `refund`, `price`, `checkout`) | +3 | Bug = financial loss, hard to claw back. |
| LLM/API spend (`openai`, `anthropic`, `claude`, `completion`, `embedding`, `model`) | +2 | Bug = runaway cost / silent inert feature. |
| Crypto / secrets (`crypto`, `encrypt`, `secret`, `apikey`, `private_key`, `signature`) | +3 | Subtle bugs, severe consequences. |
| Migrations / schema (`migration`, `schema`, `alter table`, `prisma`, `ddl`) | +3 | Often irreversible; affects persisted data. |
| Concurrency (`async`, `await`, `thread`, `lock`, `mutex`, `queue`, `worker`, `goroutine`) | +2 | Shared blind spot; races escape review. |
| Infra / deploy (`Dockerfile`, `.github/`, `*.tf`, `k8s`, `helm`, `deploy`) | +2 | Bug = outage / blast radius beyond one request. |
| Public API / contract (`*.graphql`, `openapi`, `proto`, `routes`, `controller`) | +2 | Breaks downstream consumers. |
| Dependency manifest (`package.json`, lockfiles, `requirements.txt`, `go.mod`, `Cargo.toml`) | +2 | Supply-chain + transitive risk (see `dep-audit`). |

## Likelihood signals — *how much / how complex* the change is

| Signal | Weight | Why |
|--------|--------|-----|
| Churn > 200 changed lines | +3 | Large diffs hide more bugs; review fatigue. |
| Churn 50–200 changed lines | +2 | Moderate. |
| Churn 10–50 changed lines | +1 | Small. |
| Has deletions | +1 | Removing code/guards risks regressions. |
| Added control flow (new `if`/`for`/`while`/`switch`/`catch`/`?:` on added lines) | +1 per up to +3 | New branches = new untested paths (see `test-gap`). |

> Hotspot note: churn × complexity × ownership-concentration is the strongest
> empirical bug predictor (~4–8% of files hold most defects). `risk_score.py`
> approximates churn and complexity from the diff; if you keep a `git log`
> hotspot map, fold it in here.

## Bucketing thresholds

- `high`  → score ≥ 6  (escalate to deep review)
- `medium`→ score 3–5  (standard review)
- `low`   → score < 3  (skip deep review)

These are deliberately conservative (favor escalating a borderline file over
missing a risky one). Lower the `high` threshold if you want more escalations.

## How to tune

1. Add domain keywords for *your* danger zones to the impact table + the script's
   keyword groups.
2. Adjust thresholds based on how often escalations turn out worthwhile.
3. If escalations are mostly false alarms, raise the `high` cutoff; if real bugs
   slip through as `medium`, lower it.
