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

## Installation

### Via Plugin Marketplace

```bash
# In Claude Code
/plugin marketplace add colorpulse6/claude-skills

# Install one or both plugins
/plugin install pr-review@colorpulse6-skills
/plugin install push@colorpulse6-skills
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
│   └── push/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── push/
│               ├── SKILL.md
│               └── scripts/
│                   ├── preflight.sh
│                   └── secret-scan.sh
└── README.md
```

## Contributing

This is a personal skills repo. Feel free to fork it and adapt to your own needs.

## License

MIT
