# Claude Skills

Personal Claude Code skills for PR review and quality-gated push pipelines. Works across frontend and backend projects with auto-detection - no per-project configuration needed.

## Skills

### `/pr-review`

AI-powered PR review that combines automated rule checking with interactive walkthrough.

**Features:**
- **Inbox mode** - `/pr-review` with no args discovers all PRs awaiting your review
- **Single PR mode** - `/pr-review 42` or `/pr-review <url>`
- **Incremental re-review** - only reviews new commits if you've already reviewed the PR
- **Contract verification** - checks alignment between GraphQL schema, resolvers, services, and Prisma/DB layers
- **Frontend + backend rules** - auto-detects changed file types and applies relevant rules
- **Interactive walkthrough** - finding-by-finding with Accept/Reject/Edit/Details
- **GitHub suggestion blocks** - one-click apply for simple fixes
- **Line-specific comments** - never posts code feedback as general PR comments

**Usage:**
```bash
/pr-review           # Inbox mode - pick from PRs awaiting your review
/pr-review 42        # Review PR #42 in current repo
/pr-review https://github.com/owner/repo/pull/42  # Review by URL
```

### `/pr-respond`

Interactive walkthrough for addressing review comments on your own PRs. The counterpart to `/pr-review`.

**Features:**
- **Inbox mode** - `/pr-respond` with no args finds all your open PRs with unresolved review threads
- **Single PR mode** - `/pr-respond 42` or `/pr-respond <url>`
- **Per-thread actions** - Fix / Push back / Defer / Skip each unresolved comment
- **Batched implementation** - one subagent handles all Fix items in a single pass, produces a coherent commit
- **Auto-detect type check** - finds the right command (pnpm/yarn/npm with check-types or typecheck)
- **Diff review before commit** - see the full diff before anything gets pushed
- **Smart replies** - Fix replies include commit SHA with a link to the exact line; push-back replies use your reasoning verbatim
- **Auto-resolve** - Fix and Push back threads are resolved, Defer and Skip stay open

**Usage:**
```bash
/pr-respond           # Inbox mode - pick from your PRs with unresolved threads
/pr-respond 42        # Respond to PR #42
/pr-respond https://github.com/owner/repo/pull/42  # By URL
```

### `/push`

Quality-gated push pipeline that runs checks before pushing and creates PRs automatically.

**Features:**
- **Auto-detection** - detects package manager (pnpm/yarn/npm) and available scripts
- **Parallel quality gates** - type check, lint, tests, build
- **Auto-fix loop** - retries failed gates after fixes (max 3 iterations)
- **Conventional commits** - enforces commit message format
- **Branch policy** - blocks direct push to main
- **Secret detection** - scans staged files for credentials
- **PR creation** - creates PR with summary and test plan
- **CI watch** - polls CI and auto-fixes failures (max 2 iterations)

**Usage:**
```bash
/push  # Run the full pipeline
```

### `/session-recap`

A browser-viewable HTML timeline of your recent Claude Code sessions — a dark "flight recorder" view to use as a reference point for what you worked on.

**Features:**
- **Daily or weekly** - defaults to the last 7 days; pass a number or `daily`/`weekly`/`month`
- **Timeline by day** - sessions grouped by day with project, branch, and time
- **Reference points** - PRs (clickable), commits, files touched, and active time per session
- **Key decisions** - one bounded LLM pass adds a summary + key decisions for notable sessions
- **Active time, not wall-clock** - inter-message gaps over 30 min are dropped, so resumed sessions don't show absurd spans
- **Resume from a card** - each session exposes its `claude --resume <id>` command (click to copy)
- **Filter + search** - project chips (shift-click to solo), full-text search, PRs/commits-only toggle
- **Self-contained** - one HTML file with data inlined; works offline

**Usage:**
```bash
/session-recap          # Last 7 days
/session-recap daily    # Last 24 hours
/session-recap 30       # Last 30 days
```

### `codex-second-opinion`

An independent, **separate-model** (Codex CLI / `gpt-5.5`) review of code — to complement your own Claude subagent audits with a model that has different blind spots. In practice a separate model surfaces real bugs that parallel same-model reviews all miss.

**Features:**
- **Independent findings first, then confirm/refute** - a neutral brief structure that gets genuine discovery, not a yes-man echo
- **Read-only** - `codex exec --sandbox read-only`; reads + runs read-only commands, never edits
- **Reconcile, don't paste** - convergence (high-confidence), net-new-from-Codex (verify yourself), and sharpened disagreements
- **For the risky stuff** - concurrency, process lifecycle, async timing, money/LLM spend — where same-model reasoning shares blind spots

**Usage:** ask for "a codex second opinion" / "what does Codex think" before stacking work on a just-shipped slice. Requires the Codex CLI installed.

### `/skill-starter`

A **template plugin** you copy to start a new skill. It's a complete, working example of the orchestrator pattern: one user-invocable skill resolves a target, fans the work out to parallel specialist subagents, and aggregates their findings into a single report.

**Demonstrates:**
- **`plugin.json` + `SKILL.md` frontmatter** - the minimum to make a skill discoverable and user-invocable
- **Deterministic script layer** - `scripts/collect.sh` resolves units of work as JSON; judgment stays in markdown
- **Parallel subagents** - spawns one `starter-worker` agent per batch (tool- and model-scoped) in a single message so they run concurrently
- **Aggregation + output contract** - workers write `findings/<batch_id>.md`, the skill merges them into `REPORT.md`
- **Error-handling table** - predictable behavior for empty matches, failed workers, unwritable output

`TEMPLATE:` markers throughout show exactly where to swap in your own logic.

**Usage:**
```bash
/skill-starter                  # default: audit repo-tracked text files
/skill-starter "src/**/*.ts"    # audit a glob
/skill-starter ./docs           # audit a directory
```

### `/review-board`

A multi-lens, multi-model code review conductor — the "parent" that composes parallel agents with `codex-second-opinion`.

**What it does:** on a diff / PR / branch, it spawns several **scoped Claude review agents in parallel** (each hunting one failure-class) **while** a **separate model** (Codex) reviews independently, then reconciles everything into one ranked, cross-model verdict.

**Two kinds of diversity at once:**
- **Lens diversity** - `security`, `concurrency`, `performance`, `contract` lenses each tunnel-vision on one bug class, so nothing gets averaged away
- **Model diversity** - Codex runs concurrently (its latency hides behind the lens work) and catches what same-model reasoning misses

**Output:** `REVIEW-BOARD.md` with a verdict, a cross-model table, **convergence** (high-confidence), **net-new-from-Codex** (verify yourself), and sharpened disagreements. Falls back to Claude-only if the Codex CLI isn't installed.

**Customize:** lenses live in `references/lenses.md` (one section each) and the agent is parameterized — add a lens without writing a new agent.

**Usage:**
```bash
/review-board           # review the working diff
/review-board 42        # review PR #42
/review-board my-branch # diff against the merge base
```

### `/risk-gate`

Triage-then-escalate: scores a diff cheaply, sends only the risky parts to deep review.

**What it does:** a deterministic scorer (`risk_score.py`) rates each changed file on `risk = likelihood × blast-radius` (danger paths like auth/payments/migrations, churn, added control flow), buckets them Low/Medium/High, and escalates **only HIGH-risk files** to `review-board` (or `codex-second-opinion`). Spends the expensive model-diversity where it pays.

**Usage:**
```bash
/risk-gate            # triage the working diff
/risk-gate 42         # triage PR #42
```

### `/plan-harden`

Adversarially review a design doc / spec / RFC **before** you build it — the cheapest place to fix a flaw.

**What it does:** a context gate (what is it / who's affected / success), a **pre-mortem** ("it's 6 months out and this failed — why?"), and parallel `design-lens` agents (edge-cases, failure-handling, data-integrity, rollout-rollback, observability, scaling, security/STRIDE, dependencies). Reconciles into a five-part hardening report + an `APPROVED`/`REVISE` verdict. All findings are `[PLAN_RISK]` (prospective).

**Usage:**
```bash
/plan-harden                 # newest design doc in docs/
/plan-harden docs/rfc.md     # a specific doc
```

### `/dep-audit`

Audit dependency-manifest / lockfile changes in two passes — cheap offline signal, then real tools.

**What it does:** an offline pass (`manifest_scan.py`, zero network) flags semver deltas, range loosening, lockfile-integrity changes, new install scripts, and typosquats; then per-ecosystem `dep-scanner` agents run the real tools (`osv-scanner`, `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`) plus maintainer-health checks, scoring each package on four axes (security / license / maintenance / breaking-change) with a Block/Warn/Monitor/Ignore verdict. Honest about offline limits.

**Usage:**
```bash
/dep-audit            # audit the working diff's dependency changes
/dep-audit 42         # audit PR #42
```

### `/test-gap`

Find the most important **missing** tests in a change — ranked by risk, not coverage %.

**What it does:** fans out `gap-finder` agents over the changed files; each traces codepaths (changed branches, error paths, boundaries) and ranks untested ones by `risk = impact × likelihood`, using the surviving-mutant test to catch covered-but-unasserted code. Optional coverage (`diff-cover`) and mutation (`Stryker`/`PIT`/`mutmut`/`cargo-mutants`) passes confirm gaps. Outputs prioritized tests-to-add (P0→P2) with proposed cases.

**Usage:**
```bash
/test-gap             # find gaps in the working diff
/test-gap 42          # PR #42
```

## Installation

### Via Plugin Marketplace

```bash
# In Claude Code
/plugin marketplace add colorpulse6/claude-skills

# Install the plugins you want
/plugin install pr-review@colorpulse6-skills
/plugin install pr-respond@colorpulse6-skills
/plugin install push@colorpulse6-skills
/plugin install session-recap@colorpulse6-skills
/plugin install codex-second-opinion@colorpulse6-skills
/plugin install skill-starter@colorpulse6-skills
/plugin install review-board@colorpulse6-skills
/plugin install risk-gate@colorpulse6-skills
/plugin install plan-harden@colorpulse6-skills
/plugin install dep-audit@colorpulse6-skills
/plugin install test-gap@colorpulse6-skills
```

Once installed, the skills are available in any project on your machine.

## How It Works

### Project Detection

The skills auto-detect project characteristics by looking at:

| Signal | Indicates |
|--------|-----------|
| `pnpm-lock.yaml` | pnpm package manager |
| `yarn.lock` | yarn package manager |
| `package-lock.json` | npm package manager |
| `tsconfig.json` | TypeScript project |
| `prisma/schema.prisma` | Prisma ORM |
| `*.graphql` files | GraphQL schema |
| `.tsx` / `.jsx` files | React frontend |
| `apps/api/`, `services/`, `server/` | Backend code |
| `package.json` scripts | Available commands (test, lint, check-types, build) |

Commands that don't exist are skipped gracefully.

### Review Rule Selection

When reviewing a PR, the skill inspects the changed files and conditionally loads rules:

- **Frontend files changed** → loads `frontend-rules.md`
- **Backend files changed** → loads `backend-rules.md`
- **Both** → loads both sets

Universal rules (secrets, `any` types, error handling) always apply.

### Local Overrides

If a project has its own `.claude/skills/pr-review/` or `.claude/skills/push/` directory, it takes precedence over the global skill. This lets you keep project-specific rules (e.g., custom terminology, domain-specific checks) separate from the generic skills.

## Repo Structure

```
claude-skills/
├── .claude-plugin/
│   └── marketplace.json           # Marketplace manifest listing all plugins
├── plugins/
│   ├── pr-review/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json        # Plugin manifest
│   │   └── skills/
│   │       └── pr-review/
│   │           ├── SKILL.md
│   │           ├── review-lens.md
│   │           ├── output-contract.md
│   │           └── references/
│   │               ├── backend-rules.md
│   │               ├── frontend-rules.md
│   │               ├── contract-verification.md
│   │               └── severity-definitions.md
│   ├── pr-respond/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── pr-respond/
│   │           └── SKILL.md
│   ├── push/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── push/
│   │           ├── SKILL.md
│   │           └── scripts/
│   │               ├── preflight.sh
│   │               └── secret-scan.sh
│   ├── session-recap/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── session-recap/
│   │           ├── SKILL.md
│   │           └── scripts/
│   │               ├── build_timeline.py
│   │               ├── build_digests.py
│   │               └── render_html.py
│   ├── skill-starter/                 # template plugin (orchestrator + parallel agents)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   └── starter-worker.md      # parallel specialist subagent
│   │   └── skills/
│   │       └── skill-starter/
│   │           ├── SKILL.md
│   │           └── scripts/
│   │               └── collect.sh     # deterministic unit collector
│   ├── review-board/                  # multi-lens + multi-model review conductor
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   └── review-lens.md         # parameterized single-lens reviewer (parallel)
│   │   └── skills/
│   │       └── review-board/
│   │           ├── SKILL.md
│   │           └── references/
│   │               └── lenses.md      # per-lens checklists (add a lens here)
│   ├── risk-gate/                     # triage a diff, escalate only risky parts
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/risk-gate/
│   │       ├── SKILL.md
│   │       ├── references/risk-signals.md
│   │       └── scripts/risk_score.py  # deterministic per-file risk scorer
│   ├── plan-harden/                   # adversarial pre-build design review
│   │   ├── .claude-plugin/plugin.json
│   │   ├── agents/design-lens.md      # parameterized adversarial lens (parallel)
│   │   └── skills/plan-harden/
│   │       ├── SKILL.md
│   │       └── references/review-checklist.md
│   ├── dep-audit/                     # dependency-change audit (offline + tools)
│   │   ├── .claude-plugin/plugin.json
│   │   ├── agents/dep-scanner.md      # per-ecosystem scanner (parallel)
│   │   └── skills/dep-audit/
│   │       ├── SKILL.md
│   │       ├── references/dep-checklist.md
│   │       └── scripts/manifest_scan.py  # offline diff scanner
│   └── test-gap/                      # find the most important missing tests
│       ├── .claude-plugin/plugin.json
│       ├── agents/gap-finder.md       # per-shard gap finder (parallel)
│       └── skills/test-gap/
│           ├── SKILL.md
│           └── references/test-gap-heuristics.md
└── README.md
```

## Contributing

This is a personal skills repo. Feel free to fork it and adapt to your own needs.

## License

MIT
