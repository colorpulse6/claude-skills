# Contract Verification

This document describes the pre-review contract verification scan. This scan runs **before** the AI reviewer subagent is dispatched and attaches its findings to the review context. It catches a class of silent typo bugs that LLM review often misses because LLMs focus on what the code *says*, not on whether it *matches* what other code expects.

---

## What is Contract Verification?

Contract verification is a deterministic, grep-and-read scan that checks alignment between layers of the application. Unlike the AI review, it doesn't reason about design or style - it only verifies that A and B agree on the shape of data flowing between them.

The scan is imperfect (it uses grep, not full type analysis), but it catches the highest-impact bugs: silent field name mismatches that type-check but fail at runtime, missing migrations, field renames that left dangling references, and webhook handlers that access the wrong payload path.

When the reviewer subagent runs, the contract verification findings are included in its context as a pre-filled section. The subagent should refine these findings with additional context (file links, code snippets, proposed fixes) and include them in its final output.

## Checks to Perform

### 1. GraphQL Schema to Resolver to Service to Database

For each GraphQL schema change in the diff:

1. **Find the corresponding resolver.** It is usually in a `*.resolver.ts` file or a resolvers directory. Match by type and field name.
2. **Verify resolver arguments match the schema.** Field names, types, nullability. A resolver that takes `id: string` when the schema declares `id: ID!` is fine (GraphQL ID maps to string). A resolver that destructures `{ userId }` when the schema declares `id` is Critical.
3. **Find what service the resolver calls.** Usually one or two levels deep. Read the service signature.
4. **Verify the service accepts what the resolver passes.** If the resolver calls `createSignal({ externalId })` but the service expects `{ sourceRef }`, that is a Critical silent bug.
5. **If the service uses a repository with Prisma**, verify the fields referenced exist in `schema.prisma`. Prisma usually catches this at type-check time, but `$queryRaw` and dynamic field access can slip through.

Example grep pattern:

```bash
# Find the resolver for a newly-added mutation
grep -rn "createSignal" --include="*.resolver.ts"

# Read the resolver and follow the call chain
# Then grep the service signature
grep -rn "class CreateSignalService\|createSignal(" --include="*.service.ts"
```

### 2. REST Route Contract

For each changed REST route:

1. **Verify the route's request body matches its validation schema.** A route that does `const { name } = req.body` without passing it through a Zod schema is an Important finding on its own - but if the route is validated, make sure the validation matches what the handler actually uses.
2. **Verify the validation schema matches the service signature.** Same principle as GraphQL - the shape passed to the service must match what the service expects.
3. **Check callers.** Grep the frontend or other services for calls to this route. Do they send the right shape? Do they handle the response shape the route now returns?
4. **Status codes:** Do callers handle the status codes the route now returns? Adding a 409 where callers only check for 400 is Important.

### 3. Prisma Field Reference Check

For each file that uses Prisma:

```bash
# Extract Prisma model field references
grep -nE "prisma\.\w+\.(findMany|findUnique|findFirst|create|update|upsert|delete)" path/to/file.ts

# Then check the arguments for field names
# Cross-reference with schema.prisma
```

The check is: does every field name in `where`, `data`, `select`, `include` exist in the Prisma schema for that model? Type-checking usually catches this, but if anyone uses `as any` casts or dynamic property access, it can escape. Flag any reference that cannot be confirmed.

### 4. Field Rename Detection

When the diff shows a field rename (old name removed, new name added on the same line or nearby), sweep the codebase for stale references to the old name:

```bash
# Old name should no longer exist in non-migration code
git grep "oldFieldName" -- ':!prisma/migrations' ':!*.generated.*' ':!*.lock' ':!node_modules'
```

If matches remain in callers, tests, other services, documentation, or type definitions, flag them as Critical. A rename that left behind even one stale reference will fail at runtime in that code path.

Special cases:
- **String literals:** If the field name appears in a string (e.g., in `select: ['oldFieldName']` or in a GraphQL query string), those must also be updated.
- **Database columns:** If the underlying column was renamed, the migration must rename it, not just the Prisma model.
- **Cached data:** If the field was cached (Redis, materialized views), the cache may have stale data with the old name after deploy.

### 5. Webhook Payload Verification

For webhook handlers (Clerk, Stripe, Sentry, GitHub, Shopify, etc.):

1. **Identify the provider.** Usually clear from the file name or route path.
2. **Look up the actual payload shape.** Check the provider's SDK types (`@clerk/backend`, `stripe`, `@octokit/webhooks-types`, etc.) or the provider's webhook documentation.
3. **Verify field access.** A common bug: handler accesses `data.user_id` but the actual payload is `data.public_user_data.user_id`. Nested paths are easy to get wrong.
4. **Verify event type handling.** If the handler branches on event type, make sure the types match the provider's actual event names.
5. **Verify HMAC verification.** The handler must verify the signature before parsing anything else. If not, Critical.

Common webhook provider gotchas:
- **Clerk:** User data is nested under `data.public_user_data` for some events, directly under `data` for others
- **Stripe:** `event.data.object` is the resource, and `event.data.previous_attributes` is the diff for update events
- **GitHub:** Payload shape varies widely by event type; rely on `@octokit/webhooks-types`
- **Sentry:** Installation webhooks have a different shape than issue webhooks

## How to Report Findings

The contract verification step produces a pre-filled section that is attached to the context sent to the reviewer subagent. Format:

```
## Contract Verification Findings

The following issues were detected by automated contract verification. These are high-confidence findings - the reviewer should include them in the final output unless they can be disproven.

1. **File:** apps/api/src/resolvers/signal.resolver.ts:45
   **Issue:** Resolver passes `externalId` to `CreateSignalService.execute`, but the service signature expects `sourceRef`. This mismatch will cause every call to this mutation to fail validation or write undefined to the database.
   **Severity:** Critical
   **Evidence:**
   - `signal.resolver.ts:45`: `await createSignalService.execute({ externalId, ... })`
   - `create-signal.service.ts:12`: `async execute(input: { sourceRef: string, ... })`

2. **File:** apps/api/src/webhooks/clerk.webhook.ts:67
   **Issue:** Handler accesses `data.user_id` directly, but Clerk's `user.created` event nests the user ID under `data.public_user_data.user_id`. This will throw on every event of this type.
   **Severity:** Critical
   **Evidence:**
   - `clerk.webhook.ts:67`: `const userId = payload.data.user_id`
   - Clerk docs / `@clerk/backend` types: `UserJSON` payload structure

3. **File:** apps/api/prisma/schema.prisma
   **Issue:** Added `Signal` model with new required column `workspaceId`, but no corresponding migration file exists in `prisma/migrations/`.
   **Severity:** Critical
   **Evidence:**
   - `schema.prisma`: new model `Signal` with `workspaceId String`
   - `prisma/migrations/`: no new migration directories in the diff
```

The reviewer subagent should:
- Keep all contract verification findings in its final output
- Add more context if it can (surrounding code, related files, suggested fixes)
- Only downgrade or remove a finding if it can clearly show the finding is wrong (e.g., the "mismatch" is actually fine because of a wrapper function that the scan missed)
- Flag borderline cases as Important rather than Critical if there is uncertainty

## Limitations

Contract verification is a pre-screen, not a guarantee. Known limitations:

- **Grep, not types:** It relies on text matching, not full type analysis. Complex cases (conditional imports, dynamic field access, wrapper functions, generic type parameters) can be missed.
- **Standard layouts only:** It assumes the project follows standard patterns (resolvers in `*.resolver.ts`, services in `*.service.ts`, Prisma in `schema.prisma`). Non-standard layouts may be skipped entirely.
- **False positives:** The same field name used in unrelated contexts can produce noise. The scan should include evidence so the reviewer can verify.
- **No runtime verification:** It can't catch bugs that depend on actual runtime values (e.g., a field that exists but is always null in practice).
- **No semantic understanding:** It can't tell you that `userId` and `id` are semantically the same field - only that the names don't match.

When in doubt, let the reviewer subagent make the final call. Contract verification is a hint - a high-confidence hint, but a hint. The reviewer is the authority on what gets included in the final output.

## When to Skip

Contract verification should be skipped when:
- The diff is trivial (docs only, comments only, formatting only)
- The diff has no schema, resolver, route, or Prisma changes
- The project layout doesn't match the assumed patterns (and no adaptation is available)

Skipping should be explicit - the pre-review step should note "contract verification skipped: no applicable changes" so the reviewer knows it wasn't just an error.
