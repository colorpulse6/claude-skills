# Test-Gap Heuristics

How `gap-finder` decides what's a gap and how to rank it. Core model:
**priority = risk × gap**, where `risk = impact × likelihood` and `gap` measures
how untested a path is (uncovered > covered-but-unasserted > well-tested).

> **TEMPLATE:** tune weights/keywords to your domain. Synthesized from risk-based
> testing (Likelihood×Impact), mutation testing (surviving mutants), branch/patch
> coverage, and churn×complexity hotspot research.

## Contents
- The two axes
- Ranked priority list (what to test first)
- Codepath trace checklist
- The surviving-mutant test
- What NOT to test

## The two axes

**Impact (cost if it breaks):**
- Highest: money, security/auth, data integrity/loss, legal/compliance.
- High: a core business flow broken.
- Medium: a feature partially broken.
- Low: cosmetic / trivial.

**Likelihood (chance it's wrong):**
- Higher: complex logic (high cyclomatic complexity), new/changed code, external
  API/dependency, concurrency/state, high fan-in (many callers), churn hotspot.
- Lower: simple logic, established library behavior, trivial assignment.

A single-dependent file with **zero coverage** is more dangerous than a
high-dependent file with comprehensive tests. Never skip the coverage factor.

## Ranked priority list (what to test first)

1. **Changed lines with zero coverage** on a business-critical/security/money path.
2. **Untested branches** on changed conditionals — both directions of every new
   `if`/`else`/`switch`/`?:`/`&&`/`||`. (Branch coverage > line coverage.)
3. **Untested error paths** — new `catch`/`throw`/error return/retry/timeout/
   rollback. The most-neglected, highest-incident code.
4. **Untested guard clauses / validation** — new precondition checks; test both
   the pass and the reject case.
5. **Boundary / edge values** — off-by-one (`>` vs `>=`), 0, 1, -1, empty, null,
   max/min, first/last element, overflow.
6. **Changed public API/contract with weak assertions** — return value/shape
   asserted, not just "didn't throw".
7. **Unverified side effects** — mutations, writes, emitted events (the "delete the
   call" mutant).
8. Deprioritize: unchanged code, cosmetic/logging changes, trivial pass-throughs.

## Codepath trace checklist (per changed file)

- **Conditionals:** every `if`/`else`/`switch`/`case`/ternary/pattern match.
- **Error paths:** every `catch`/`throw`/`raise`/`return Err`/`.catch()`/rejected
  promise/nonzero exit.
- **Boundaries:** every `<`/`<=`/`>`/`>=`/`==`; null/empty/zero/max; loop empty +
  single + last element.
- **Async:** awaited-vs-fire-and-forget; failure/timeout/cancellation cases.
- **Function calls:** new calls invoked from changed code (do their failure modes
  have tests?).

## The surviving-mutant test (find weak assertions)

For a *covered* path, ask: *"If I silently corrupted this line — flip `<`→`<=`,
negate the `if`, replace the return with null/empty, delete this side-effecting
call — would any existing test fail?"* If **no**, that's a precisely-located
missing assertion (`weak-assertion`), even though coverage shows green. Mutation
operators to simulate: conditionals-boundary, negate-conditionals, math,
return-value replacement, void-method-call removal.

Tools (when a mutation pass is run): Stryker/StrykerJS (JS/TS), PIT (JVM), mutmut /
Cosmic Ray (Python), cargo-mutants (Rust). A surviving mutant with `coveredBy`
populated but `killedBy` empty = executed-but-unasserted.

## What NOT to test (avoid noise / gaming)

- Framework / ORM / library / HTTP-client behavior.
- Trivial pass-through wrappers, getters/setters.
- Assertions that only re-check a default value.
- Tests written purely to raise the coverage number without meaningful assertions.
- Obsolete/dead code — recommend **removal**, not tests.
