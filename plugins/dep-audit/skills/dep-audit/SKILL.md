---
name: dep-audit
description: >-
  Audits dependency-manifest / lockfile changes in a diff/PR/branch. Runs a
  zero-network offline pass over the diff (semver delta classification, pin/range
  loosening, lockfile-integrity changes, newly-added install scripts,
  typosquatting, transitive blast radius), then fans out per-ecosystem scanner
  agents that run the real tools (osv-scanner, npm audit, pip-audit, cargo audit,
  govulncheck) and maintainer-health checks, and reconciles a verdict per changed
  package. Use when user says "audit dependencies", "check this lockfile",
  "review these package bumps", "supply chain check", or invokes /dep-audit.
user-invocable: true
argument-hint: "[PR number | branch | (default: working diff)]"
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
---

# Dep Audit

Reviews dependency changes in two passes — **cheap offline signal first, real tools
second** — because most risk is visible in the diff itself and the rest needs the
network.

> **Honest limit (state this in the report):** the offline pass does NOT detect
> live CVEs or malware — it flags *shapes* of risk. Real vulnerability data comes
> from the scanner pass. Never claim a dependency is "safe" from the offline pass
> alone.

---

## Step 1: Find the dependency changes

Resolve the diff base (PR / branch / working tree). Identify changed manifests /
lockfiles: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`,
`requirements.txt`, `pyproject.toml`, `poetry.lock`, `go.mod`/`go.sum`,
`Cargo.toml`/`Cargo.lock`, `Gemfile.lock`, `pom.xml`. If none changed, stop and
say so. Note the ecosystem(s) involved.

## Step 2: Offline pass (zero network, deterministic)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/dep-audit/scripts/manifest_scan.py" [BASE_REF]
```

Emits JSON of changed packages with `change` (added/removed/bump-major|minor|patch),
and `flags` such as: range loosening (`1.2.3`→`^`/`~`/`*`/`latest`), `resolved`/
registry repoint off the public registry, integrity-hash change without a version
change, newly-added `preinstall`/`postinstall`/`install` script, typosquat
suspicion (Levenshtein-1 / transposition / hyphen-permutation vs a popular-name
list), and large transitive blast radius (one manifest line pulling in many
lockfile entries). The full rubric — including the **capability-delta-on-upgrade**
check (a version bump that *newly* adds install-script/network/shell/env access is
the single highest-value supply-chain signal) — is in
`${CLAUDE_PLUGIN_ROOT}/skills/dep-audit/references/dep-checklist.md`.

## Step 3: Scanner pass (network / tools) — fan out per ecosystem

If the network/tools are available, spawn one `dep-scanner` subagent **per
ecosystem, in parallel**. Give each (inline): its `ecosystem`, the changed-package
list + offline flags for that ecosystem, the relevant checklist section, and
`output_dir` = `./.dep-audit-out/findings/`.

Each scanner runs the right tools and the four-axis rubric, then writes
`findings/<ecosystem>.md` and returns a status line. Tool cheat-sheet (in the
checklist): `osv-scanner scan -L <lockfile>`, `npm audit --json`,
`pip-audit -r requirements.txt`, `cargo audit`, `govulncheck ./...`; maintainer
health via OSSF Scorecard / registry metadata for newly-added or
maintainer-changed packages only.

If a tool or the network is unavailable, the scanner records what it could not
check (don't fail) — and the report's verdict is downgraded to "offline-only".

## Step 4: Reconcile

Read all `findings/<ecosystem>.md` + the offline JSON. For each changed package,
combine signals into one verdict. **Drop findings below confidence 0.7** (a
suspected-but-unconfirmed pattern is a `Monitor`, not a `Block`). Write
`./.dep-audit-out/DEP-AUDIT.md` per the contract below.

## Step 5: Report

Print the gate decision + any `Block` packages. Done.

---

## Output contract — `DEP-AUDIT.md`

1. **Gate** — `pass` / `review` / `block`. Block if any package is `Block` or has a confirmed Critical/High CVE. Note if the run was offline-only.
2. **Per-package table** — `| Package | Change | Verdict | Severity | Signals | Confidence | Remediation |`. Verdict per package: **Block / Warn / Monitor / Ignore**.
3. **Confirmed vulnerabilities** — CVEs/advisories from the scanner pass with IDs, severity, fixed version.
4. **Supply-chain flags** — typosquat / install-script / maintainer-change / capability-delta items, each with the evidence that triggered it.
5. **Limits** — what wasn't checked (offline-only ecosystems, missing tools, no network).

The four axes each finding maps to: **security** (CVEs, malware signals), **license** (Safe / Review / Copyleft / None), **maintenance** (archived, >2yr stale, <2 maintainers, <90 days old), **breaking-change** (semver delta; never auto-merge a major).

## Error handling

| Scenario | Action |
|----------|--------|
| No dependency files changed | Stop; say the diff had no manifest changes. |
| `manifest_scan.py` errors on a format | Note the unparsed file; still run scanners on it. |
| No network / scanner tools | Run offline-only; mark the gate "offline-only" and list what was skipped. |
| A scanner agent BLOCKED / no file | Note the missing ecosystem; reconcile the rest. |
| Lockfile-only change (no manifest) | Still audit — it's a transitive resolution shift; diff resolved versions + integrity. |
