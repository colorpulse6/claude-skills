# Design-Review Lens Checklists

One section per lens. The orchestrator passes the relevant section to each
`design-lens` agent as its `checklist`. Questions are phrased so a reviewer can
answer them against the design and produce a concrete failure scenario.

> **TEMPLATE:** the file you'll edit most. Add a lens by adding a section; tune
> questions to your domain. Synthesized from STRIDE, Google SRE Production
> Readiness Review, RFC/design-doc practice, and the pre-mortem technique.

## Contents
- premortem
- edge-cases
- failure-handling
- data-integrity
- rollout-rollback
- observability
- scaling
- security
- dependencies

---

## premortem

Frame as fact, not hypothesis (prospective hindsight surfaces ~30% more risks):
**"It is 6 months from now. This shipped and failed badly in production. Write the
postmortem."** Then:

- What is the single most likely reason it failed — technically? operationally? organizationally?
- What assumption did we make that turned out false?
- What did users actually do that we didn't design for?
- What edge case took down production? Why didn't review catch it?
- Why didn't the rollback save us?
- What's the riskiest assumption, and what cheap experiment would de-risk it before full build?

For this lens, write each finding as a short failure narrative + the assumption it
exposes + an early warning sign.

## edge-cases

- Behavior on empty / null / zero / max-size / malformed input?
- Duplicate, replayed, concurrent, or out-of-order requests/events?
- Partial failure mid-operation — what state is left behind?
- Boundary conditions on every limit (counts, sizes, timeouts, pagination)?
- Which behaviors does the doc leave unspecified or mark TODO? (List the gaps.)
- Vague adjectives without measurable criteria ("fast", "scalable", "secure")?

## failure-handling

- Every synchronous remote call: timeout specified? Value justified?
- Retries bounded with exponential backoff + jitter? What prevents retry storms?
- Mutating operations idempotent (durable idempotency keys, not time-bounded cache)?
- Delivery semantics stated (at-least-once / exactly-once / at-most-once) and matched to use?
- Backpressure: bounded queues, circuit breakers, load shedding — or cascade on overload?
- Graceful-degradation behavior when a dependency is slow/down?

## data-integrity

- Consistency model (strong / eventual / read-your-writes) — acceptable for every consumer?
- Where can a failure between writes leave inconsistent state? Transaction boundary / saga / compensation?
- Can data be lost, corrupted, or duplicated under failure?
- Irreversible state changes guarded (confirmation, soft-delete, audit)?
- Reconciliation/repair path when an invariant is violated in production? RPO/RTO?

## rollout-rollback

- Incremental rollout (flags / canary / staged %)? Automatic rollback triggers + thresholds?
- **Is rollback actually possible** after this ships? Any point of no return?
- Schema/data migrations reversible and backward-compatible (expand → migrate → contract)?
- Do old and new code/schema run simultaneously mid-deploy? Correct in that mixed state?
- Has the rollback path been *tested*, not just assumed? Covers code AND data AND config?

## observability

- SLIs/SLOs defined? Which metrics/logs/traces prove them — specified *in the design*?
- "Which failures would be invisible for 48 hours?"
- New path instrumented before launch (golden signals: latency, traffic, errors, saturation)?
- Alerts actionable (not noisy)? Who's paged? Is there a runbook?
- Is core telemetry independent of the component being changed?
- Can you trace a single failed request end-to-end (correlation IDs)?

## scaling

- Expected load (peak QPS, data volume, growth) stated — and where's the number from?
- What breaks first at 2x / 10x / 100x?
- Unbounded resources (queues, caches, in-memory collections, fan-out)?
- Behavior under backpressure / overload — shed load or fall over?
- Hot keys / skew / N+1 query risks? Connection-pool / quota ceilings?

## security

Walk STRIDE over the data-flow; identify trust boundaries first:
- **S**poofing / **T**ampering / **R**epudiation / **I**nfo disclosure / **D**oS / **E**levation — exposure for each?
- Every entry point authenticated and authorized? Tenant isolation maintained?
- Permission checks at *all* entry points (not just the happy path / UI)?
- Secrets handling + rotation; tokens short-lived and scoped?
- Sensitive data (PII) classified, minimized, encrypted in transit + at rest?
- What's the abuse case — how would an attacker or a buggy client misuse this?
- What new attack surface does this add?

## dependencies

- For each dependency: behavior when it's slow, errors, or is completely down?
- Blast radius if this component fails — who else goes down? Single point of failure?
- Circular dependencies in startup/recovery ordering?
- New third-party/OSS dependency: maintenance, license, supply-chain risk (see `dep-audit`)?
- Cost (infra, per-request, egress) at expected scale? Cost ceiling/alerts?
