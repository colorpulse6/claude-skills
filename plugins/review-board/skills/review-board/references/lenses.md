# Review Lens Checklists

One section per lens. The orchestrator passes the relevant section to each
`review-lens` agent as its `checklist`. Keep each list concrete and falsifiable —
items a reviewer can confirm against `file:line`, not vague aspirations.

> **TEMPLATE:** This is the file you'll edit most. Add a lens by adding a section;
> tune items to your stack's real recurring bugs. No code or agent changes needed.

---

## security

- Untrusted input reaching a sink: SQL/NoSQL/command/template injection, path traversal.
- AuthZ/AuthN: missing ownership checks, IDOR (object id from request used without scoping to the caller), privilege escalation, route guards removed.
- Secrets: hardcoded keys/tokens, secrets in logs or error messages, secrets committed.
- SSRF / outbound fetch on user-controlled URLs; DNS-rebinding; redirect following.
- Unsafe deserialization, `eval`-like execution, prototype pollution.
- Crypto misuse: weak/absent hashing for passwords, predictable tokens, missing constant-time compare.
- CORS / cookie flags (SameSite, HttpOnly, Secure) loosened.

## concurrency

- Data races / shared mutable state without synchronization.
- Async timing: awaited-vs-fire-and-forget mistakes; work that returns before its
  effect lands; promises not awaited; event handlers that race the thing they observe.
- Process/connection lifecycle: resources opened and not closed on all paths;
  cleanup in the wrong place; work scheduled after shutdown begins.
- Lock ordering / deadlock potential; check-then-act (TOCTOU) without atomicity.
- Idempotency: retried/duplicated operations that double-charge or double-write.
- Cancellation / timeout handling that leaves partial state.

## performance

- N+1 queries / per-iteration I/O that should be batched.
- Unbounded work: loading whole tables/collections into memory; missing pagination/limits.
- Blocking calls (sync I/O, heavy CPU) on a hot or event-loop path.
- Allocation hotspots: per-request object churn, building large strings/arrays in loops.
- Missing/incorrect indexing implied by new query shapes.
- Caching: cache stampede, unbounded cache growth, stale-cache correctness.
- Algorithmic complexity that scales badly with realistic input sizes.

## contract

- API/schema/type drift across layers (e.g. GraphQL schema ↔ resolver ↔ service ↔ DB model).
- Breaking changes to public/exported signatures, response shapes, or status codes
  without versioning.
- Nullability mismatches: a field newly nullable/non-null not reflected on consumers.
- Enum/union additions consumers don't handle.
- Serialization mismatches (date/number/id formats) between producer and consumer.
- Migration safety: column drop/rename without a backfill+deploy ordering; non-nullable
  column added without default; index built non-concurrently on a large table.
- Backward compatibility of persisted data / message formats.
