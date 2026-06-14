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
│   └── session-recap/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── session-recap/
│               ├── SKILL.md
│               └── scripts/
│                   ├── build_timeline.py
│                   ├── build_digests.py
│                   └── render_html.py
└── README.md
```

## Contributing

This is a personal skills repo. Feel free to fork it and adapt to your own needs.

## License

MIT
