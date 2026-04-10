# Backend Review Rules

Comprehensive backend review rules for Node.js/TypeScript backends with Prisma, GraphQL/REST, and optional ClickHouse. These rules are generic and should apply to most modern backend projects. When the project has a specific convention documented in its own CLAUDE.md or contributing guide, defer to that - but these rules are the baseline.

---

## Domain-Driven Design Patterns

Many mature backends organize code into domain modules (bounded contexts). The reviewer should recognize and enforce these patterns when the project follows them.

- **Repository pattern:** All database access should go through repositories. Services and controllers should never import Prisma (or the raw DB client) directly. If you see `import { prisma } from ...` inside a service or controller, flag it unless the project explicitly allows it.
- **Services as public API:** Services are the public surface of a domain module. Repositories should be internal - other modules should call services, not repositories.
- **Mappers:** Database rows should be transformed into domain objects via mapper functions. This keeps the Prisma shape from leaking through the whole app. Flag places where raw Prisma results are returned from service boundaries.
- **Bounded context isolation:** Different bounded contexts should communicate via events, not direct imports. If module A imports something from module B's internals (not its public service), flag it.
- **Cross-context imports:** When you see an import that crosses a context boundary (e.g., `pkg-domain/briefs` importing from `pkg-domain/payments` internals), flag it unless the project docs explicitly allow it. Events are usually the correct answer.
- **Domain events:** New state transitions often warrant a domain event. If a new `update*Service` mutates important state without emitting an event, consider whether downstream systems (notifications, analytics, tracking) need to know.

## API Contracts and Schema Safety

This is one of the most common classes of silent bugs - everything type-checks but the wire format is wrong.

- **Input validation:** Every endpoint should validate its input with Zod (or the project's equivalent). Never trust incoming shapes. Flag routes that destructure `req.body` without validation.
- **Field name verification:** If a service sends `{ userId }` but the handler expects `{ id }`, that is a Critical silent bug. Contract verification (see `contract-verification.md`) catches these - the reviewer should double-check them.
- **Renamed fields:** If a field is renamed in a schema, grep for the old name to see if callers still use it. Old references that slipped through are Critical.
- **DTO inference:** DTOs should be inferred from validation schemas via `z.infer<>`, not hand-written. Hand-written DTOs drift from the schema over time. Flag hand-written input types.
- **Prisma field references:** Verify field names referenced in code exist in `schema.prisma`. Prisma generates types, so this usually type-checks - but raw `$queryRaw` or dynamic access can miss this.
- **Response shape changes:** If a response shape changed, check frontend or other consumers to confirm they handle the new shape.
- **Nullable vs required:** Changing a field from required to nullable (or vice versa) is a contract change. Flag it.
- **Enum changes:** Adding an enum value is usually safe; removing or renaming one is a breaking change.

## Database Safety

- **SQL injection:** Parameterized queries only. Never string interpolation with user input. `$queryRaw` with template literals is safe; `$queryRawUnsafe` with interpolation is not.
- **Tenant scoping:** Queries for tenant-scoped data must include `WHERE tenant_id = ?` (or `workspaceId`, `brandId`, etc.) at the database level. Do not fetch-then-filter in application code - that is both slow and leak-prone. This is the most common source of cross-tenant data leaks.
- **N+1 queries:** Loops that call `repository.findById` per item should be replaced with `findMany` + in-memory lookup. Flag any `for` or `.map` that awaits a single-row query.
- **Unbounded queries:** Every list query must paginate. Never `SELECT *` without a `LIMIT`. Flag `.findMany()` without `take:` on any table that could grow.
- **Migration sync:** If `schema.prisma` changed, there should be a corresponding migration in `prisma/migrations/`. A schema change without a migration is a Critical issue - the deploy will either fail or drift.
- **Index coverage:** New queries on large tables should have supporting indexes. A new `WHERE foo = ?` against a million-row table without an index will cause production pain.
- **Transactions:** Multi-step writes that must be atomic need `prisma.$transaction`. Flag any service that does two or more writes in sequence where a partial failure would leave the database inconsistent.
- **Cascading deletes:** Adding `onDelete: Cascade` is a data-loss risk. Flag it for explicit confirmation.

## Error Handling

- **Never empty catch:** `.catch(() => {})` swallows errors silently. Always log at minimum, ideally re-throw or handle meaningfully. Empty catches are a common source of silent production bugs.
- **Async operations need handling:** Every `await` inside an async function should be inside a try/catch, or the caller should clearly handle the rejection. Top-level unhandled promise rejections are Critical.
- **Custom error types:** Throw meaningful error types (e.g., `NotFoundError`, `ValidationError`, `ForbiddenError`), not generic `Error('failed')`. This lets middleware map them to appropriate HTTP statuses.
- **Error boundaries:** Services should throw; routes/controllers should catch and return appropriate HTTP status codes. Don't let Prisma errors or raw exceptions escape to the client - they often contain sensitive info.
- **Structured error logging:** Errors should be logged with enough context (user ID, request ID, relevant IDs) to debug. Bare `console.error(err)` is Important.

## Authentication & Authorization

- **Middleware changes:** Any change to auth middleware deserves extra scrutiny. Race conditions in token refresh are a common source of Critical bugs.
- **Authorization check:** Every protected route must check *permissions*, not just *authentication*. A user being logged in is not enough - they must be allowed to touch the resource.
- **Session handling:** Be careful with parallel requests that might invalidate sessions. Token rotation logic should be idempotent for the duration of any in-flight request.
- **Webhook verification:** Webhook handlers must verify HMAC signatures before processing, using a timing-safe comparison (`crypto.timingSafeEqual`). Never just parse and trust.
- **Insecure defaults:** New endpoints should be protected by default. If a route is public, it should be explicit and deliberate.
- **Privilege escalation:** Watch for endpoints that accept user-controlled IDs and use them without verifying ownership. A classic bug: `PATCH /users/:id` that doesn't check `req.user.id === params.id`.

## GraphQL Specific

- **Resolver-to-service contract:** The shape passed from a resolver to a service must match the service signature. This is the most common GraphQL silent bug. Contract verification should catch these.
- **Field resolvers and N+1:** Lazy field resolvers are fine but watch for N+1 on hot paths. DataLoader is the standard solution.
- **Workspace scoping in resolvers:** Every query resolver should scope to the authenticated workspace at the DB level. Never use fetch-then-guard patterns (fetches the row, then checks if the user can see it) - return `null` for not-found so that wrong-workspace requests don't leak existence.
- **Return types:** Prefer `null` for not-found so that wrong-workspace requests are indistinguishable from missing records. Throw for other errors (validation, server errors).
- **Mutation inputs:** GraphQL input types should be validated with Zod or similar before hitting the service. Don't rely on GraphQL type coercion alone - it doesn't cover business rules.
- **Subscription authorization:** Subscriptions need auth checks too, and often per-event filtering.

## REST Specific

- **HTTP verb correctness:** `GET` should not mutate. `POST` creates, `PUT` replaces, `PATCH` partially updates, `DELETE` removes. Flag verb mismatches.
- **Status codes:** 200 for success with body, 201 for created, 204 for no content, 400 for client validation error, 401 for unauthenticated, 403 for unauthorized, 404 for not found, 409 for conflict, 422 for unprocessable entity, 500 for server error. Flag wrong codes.
- **Idempotency:** `PUT` and `DELETE` should be idempotent. `POST` usually isn't. If a `POST` endpoint needs to be safely retryable, it should accept an idempotency key.
- **Rate limiting:** Endpoints that do expensive work should be rate limited.

## BullMQ / Background Jobs

- **Idempotency:** Jobs must be idempotent. A job may be retried, duplicated, or run out of order. If a job would cause duplicate side effects on retry, flag it.
- **Retry policy:** Failed jobs need a retry policy with exponential backoff. No retries means a single transient failure loses data.
- **Timeouts:** Long-running jobs need an explicit timeout. Without one, a hung job can pin a worker forever.
- **Resource checks:** Jobs that consume resources (AI credits, API quotas, third-party rate limits) must check availability before consuming. Failing halfway wastes resources.
- **Dead-letter queue:** Jobs that exhaust retries should go to a DLQ or raise an alert, not silently vanish.
- **Concurrency:** If a job shouldn't run in parallel with itself for the same entity, it needs a lock or a queue key that serializes it.

## ClickHouse (if detected)

- **Avoid `FINAL`:** The `FINAL` keyword triggers a full-table merge scan. For ReplacingMergeTree tables, use `argMax` CTEs to get the latest version efficiently. Flag any new query with `FINAL` unless the table is tiny.
- **INSERT column order:** ClickHouse maps INSERT columns by position, not name. An INSERT must list columns in exactly the DDL order, or the order must be explicit in the statement. Mismatches silently corrupt data.
- **Nullable avoidance:** Prefer sentinel values (0, empty string, epoch) over `Nullable` types when possible. Nullable adds a bitmap column and slows queries.
- **Materialized views:** Should be incremental (populated from inserts), not full-recompute. Full recomputes on large tables are operational pain.
- **JOIN strategy:** Filter before joining, specify the algorithm (`join_algorithm='grace_hash'` etc.) when beneficial. The default hash join can blow up memory on large inputs.
- **Partitioning:** New tables should partition by a time column (usually `toYYYYMM(created_at)`) unless they're small.
- **ORDER BY:** The `ORDER BY` in table DDL is the primary sort key. It must match the access pattern or queries will be slow.

## Testing

- **Coverage:** New services should have test coverage. Services that touch critical paths (auth, payments, data writes) must have tests.
- **Use test-kits, not mocks:** Prefer real fixtures or test-kits over mocking repositories. Mocking the DB layer means tests can pass when production is broken.
- **AAA pattern:** Arrange, Act, Assert. Each test should be clearly structured.
- **Don't mock what you own:** Mock external dependencies (APIs, clocks, random) but not your own services unless the test is explicitly a unit test of something else.
- **Happy path + edge cases:** Every new feature needs at least a happy path test and tests for obvious error cases (not found, unauthorized, validation errors).
- **Integration tests:** Critical flows should have integration tests that exercise the real router + service + DB.

## Webhooks

- **HMAC verification first:** Verify signature before parsing or doing anything with the payload. A bad signature means discard and return 401.
- **Timing-safe comparison:** Use `crypto.timingSafeEqual` - never `===` on signatures.
- **Raw body:** Most signatures verify against the raw request body, not the parsed JSON. Make sure the middleware preserves the raw body for webhook routes.
- **Idempotency:** Webhook handlers must be safe to call multiple times. Clerk, Stripe, Sentry, GitHub, and others all retry on 5xx, and sometimes deliver duplicates anyway.
- **Return 200 fast:** Respond 200 quickly, then do heavy work asynchronously (via a queue). Providers typically have aggressive timeouts (often 5-10 seconds).
- **Replay protection:** Optionally check a timestamp in the signed payload and reject events older than a few minutes, to protect against replay.

## Completeness Checks

These are bug classes the reviewer should actively look for:

- **Platform adapter siblings:** If fixing one platform adapter (Instagram), check siblings (TikTok, YouTube, Facebook, Twitter) for the same bug. Adapter bugs usually come in matched sets.
- **Route siblings:** If fixing one route, check similar routes for the same bug.
- **Field rename sweep:** If renaming a field, grep for the old name everywhere - tests, callers, other services, documentation.
- **Enum sweep:** If adding an enum value, check all `switch` and `if` statements on that enum to see if the new case needs handling.
- **Translation sweep:** If adding a user-facing string, check if the project has i18n and whether the string needs to be added to other locales.

## TypeScript

- **`type` vs `interface`:** Follow the project convention. If the project uses `type`, flag new `interface` declarations.
- **`any`:** Every `any` is suspicious. Flag it unless there is a clear reason (e.g., truly dynamic JSON from a third party) and that reason is commented.
- **`@ts-ignore` / `@ts-expect-error`:** Must have a comment explaining why. Bare suppressions are Important findings.
- **Non-null assertions (`!`):** Should be rare and deliberate. Flag new `!` operators unless the context clearly guarantees the value.
- **`unknown` is usually better than `any`:** It forces explicit narrowing.

## Logging and Observability

- **Log levels:** Errors as `error`, warnings as `warn`, normal operations as `info`, verbose debugging as `debug`. Wrong levels pollute production dashboards.
- **Structured logs:** Logs should include request ID, user ID, and other context. Bare strings are hard to filter.
- **No PII in logs:** Emails, tokens, full names, full request bodies should not be logged at `info` level. At most at `debug`, and only in dev.
- **Metrics on new features:** New features on hot paths should emit metrics so operators can see them.
- **Tracing:** Distributed traces should propagate across service boundaries. Don't drop trace headers when making downstream calls.

## Configuration and Secrets

- **No hardcoded secrets:** Secrets come from environment variables or a secret manager, never the code.
- **New env vars:** New environment variables need to be added to `.env.example`, the deploy configuration, and documented.
- **Feature flags:** Risky changes should be behind a feature flag when possible.
- **Default safety:** Default config should be safe for production. If a new config defaults to something unsafe, flag it.
