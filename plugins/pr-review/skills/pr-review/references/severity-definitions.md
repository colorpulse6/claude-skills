# Severity Definitions

This document defines the three severity levels used by the PR review skill. Every finding produced by the reviewer subagent must be tagged with one of these severities. When in doubt, err on the side of the more serious category - it is better to flag a borderline issue as Important than to bury a real bug as Minor.

## Critical

Bugs, security issues, data loss, broken functionality. Blocks the merge. A Critical finding means "this will break something in production, leak data, or corrupt state". The reviewer should be confident the issue is real before tagging it Critical.

**Backend examples:**
- SQL injection (unparameterized queries with user input)
- Missing authentication on protected routes
- Missing workspace/tenant scoping on database queries (cross-tenant data leak)
- Race conditions in auth/token refresh flows
- Null dereference on required data
- Infinite loop or unbounded recursion
- Hardcoded production secrets or credentials
- Empty catch blocks swallowing errors silently
- Field name mismatches between API caller and handler (silent data loss)
- Unhandled promise rejections in async code
- Missing HMAC verification on webhook handlers
- Direct database writes bypassing repository/service layer when that's the pattern
- Prisma schema changed but no corresponding migration committed
- Transaction boundary missing around multi-step writes that must be atomic
- Sending PII or secrets to logs, analytics, or third-party services
- CORS misconfiguration exposing the API to untrusted origins
- File upload handlers without size limits or content-type validation

**Frontend examples:**
- XSS vulnerability (`dangerouslySetInnerHTML` with user input, or unsafe DOM manipulation)
- Exposed API keys or secrets in client code
- Missing authentication redirect on protected pages
- State corruption (mutating state directly instead of `setState`)
- Memory leaks (unregistered event listeners, timers not cleaned up)
- Broken user flows (form submission without validation, infinite loading states)
- Accessibility blockers (no keyboard navigation for critical actions)
- Infinite render loops (`useEffect` without dependency array updating state)
- Token or session stored in `localStorage` without the project's standard handling
- Unsanitized URLs in `href` or `src` that could be `javascript:` links
- Breaking a public API contract that downstream apps consume

## Important

Architecture problems, missing error handling, test gaps on critical paths. Should be addressed before merge but not always blocking. An Important finding means "this is a real problem that could bite us, but not an immediate production break".

**Backend examples:**
- `any` type used without clear justification
- `@ts-ignore` or `@ts-expect-error` comment without explanation
- N+1 query patterns in loops
- Missing error handling in async operations (no try/catch, no `.catch`)
- Repository imported outside its domain boundary (violates encapsulation)
- Cross-context imports when events should be used
- Missing test coverage on a new service method
- Large function (>50 lines) without clear separation
- Duplicated logic that should be extracted
- Missing null/undefined checks on nullable values
- Hand-written types where they should be inferred from validation schemas
- Missing index on a new column that will be queried frequently
- Logging at wrong level (errors logged as info, debug noise in production)
- Inconsistent error shape across endpoints
- Missing pagination on list endpoints that could grow unbounded
- Background job without retry policy or dead-letter handling
- Webhook handler that doesn't return 200 quickly (heavy work should be async)

**Frontend examples:**
- Missing `key` prop on list items
- `useEffect` with incorrect dependency array
- Direct DOM manipulation in React (`querySelector`, `document.getElementById`)
- Inline event handlers causing unnecessary re-renders in hot paths
- Missing loading or error states on async UI
- Accessibility issues that aren't blockers (missing alt text, `aria-label` where helpful)
- Hardcoded strings that should be i18n
- `any` type on component props
- Expensive computations without memoization in frequently-rendered components
- State updates that could be batched but aren't
- Prop drilling more than 3 levels deep without context or composition
- Fetching server state with `useState` + `useEffect` instead of the project's data layer
- Non-semantic HTML for interactive elements (`<div onClick>` instead of `<button>`)
- Forms without client-side validation feedback
- Large component files (>300 lines) mixing many concerns

## Minor

Style, naming, small optimizations, docs. Optional improvements. A Minor finding is "this would be nicer, but shipping without it is fine".

**Both frontend and backend:**
- Verbose variable names that could be clearer
- Missing JSDoc on public APIs
- Unused imports or variables (should be caught by lint, but flag if present)
- Inconsistent formatting (if not caught by formatter)
- Magic numbers that could be constants
- Comments that describe what instead of why
- Opportunities for optional chaining (`?.`) or nullish coalescing (`??`)
- Slightly clearer conditional logic
- Small refactoring opportunities
- `console.log`/debug statements (flag but not blocking)
- TODO comments added in PR (track but don't block)
- Typos in identifier names, comments, or user-facing strings
- Import ordering or grouping inconsistencies
- Minor dead code that could be removed
- A test that could assert more precisely
- Readme or doc drift from the actual behavior

## Guidelines for the Reviewer

- Every finding must have exactly one severity tag
- If you cannot decide between Critical and Important, default to Important and explain the uncertainty
- Do not inflate severity to get attention - trust that Important findings will be read
- Do not downplay Critical findings to avoid blocking - if it will break production, say so
- A finding with uncertainty should state what would need to be verified to confirm it
