# Dependency-Audit Checklist

The two-pass rubric. Bucket A is what `manifest_scan.py` computes offline from the
diff; Bucket B is what the `dep-scanner` agents confirm with real tools/network.
Each changed package gets a verdict on four axes: **security, license,
maintenance, breaking-change**.

> **TEMPLATE:** tune thresholds and add ecosystems for your stack. Signal
> taxonomy distilled from OSV/GHSA, Socket.dev's alert set, OpenSSF Scorecard,
> GuardDog, and ecosyste.ms package-health metrics.

## Contents
- Bucket A — offline diff signals (no network)
- Bucket B — network/tool signals
- The four axes
- Per-ecosystem tool cheat-sheet
- Verdict + confidence

## Bucket A — offline diff signals (no network)

- **Semver delta** per changed package: major (assume breaking) / minor / patch.
  0.x caveat: below 1.0.0 treat a *minor* bump as breaking.
- **Range loosening:** exact `1.2.3` → `^` / `~` / `*` / `latest` / `>=` widens trust.
- **Lockfile integrity:** `integrity`/`resolved`/checksum changed for an *unchanged*
  version string = tamper/re-publish red flag.
- **Source repoint:** dep moved to a git URL / tarball / alternate registry off the
  public registry = hijack/confusion red flag.
- **New install scripts:** `preinstall`/`postinstall`/`install` added in
  `package.json` (allowlist benign ones: `husky install`, `prisma generate`, `tsc …`).
- **Transitive blast radius:** one manifest line pulling in many new lockfile entries.
- **Typosquat suspicion:** added name within Levenshtein-1 (substitution/insertion/
  transposition) or a hyphen-permutation of a popular name.
- **Downgrade** of a previously-patched version (re-introduces a known-vuln version).

## Bucket B — network/tool signals

- **Known CVEs/advisories** (OSV.dev aggregates GHSA / RustSec / PyPA / Go).
- **Capability delta on upgrade (highest-value signal):** does the new version
  *newly* add install-script / network / shell / filesystem / env-var access vs the
  old version? Socket-style alert set: `installScripts`, `networkAccess`,
  `shellAccess`, `filesystemAccess`, `envVars`, `usesEval`, `obfuscatedFile`.
- **Maintainer health:** `newAuthor` / `unstableOwnership` / `missingAuthor`;
  maintainer email domain compromised/unclaimed/disposable.
- **Package age / adoption:** first published <90 days ago; <500 dependent repos;
  single version; archived.
- **Provenance:** signed releases / Sigstore attestation present?
- **OSSF Scorecard:** overall <5 warrants inspection; `Maintained`,
  `Dangerous-Workflow`, `Pinned-Dependencies`, `Signed-Releases` are the key checks.

## The four axes (assign per package)

- **security:** CVEs by severity + the supply-chain/capability signals above.
- **license:** Safe (MIT, Apache-2.0, BSD, ISC, Unlicense) / Review (LGPL, MPL-2.0) /
  Copyleft (GPL, AGPL — affects distribution) / None (not open source — do not use).
- **maintenance:** archived / >2yr since release / <2 maintainers / <90 days old /
  single version / dev-distribution <0.15 (bus-factor).
- **breaking-change:** semver delta; never auto-merge a major; major API bumps need a
  migration task + tests.

## Per-ecosystem tool cheat-sheet

| Ecosystem | Vuln scan | Notes |
|-----------|-----------|-------|
| Cross | `osv-scanner scan -L <lockfile>` (or `scan -r ./`); `--offline --download-offline-databases` for air-gapped | multi-ecosystem, OSV-backed |
| npm | `npm audit --json` (`npm audit fix`) | queries npm advisory API |
| pypi | `pip-audit -r requirements.txt` / `pip-audit --locked .` | PyPI + OSV |
| cargo | `cargo audit` (RustSec); `cargo deny check` for bans/licenses/sources | |
| go | `govulncheck ./...` | call-graph aware — only *reachable* vulns, fewer FPs |
| any | `trivy fs .` / `grype dir:.` (+ `syft` for SBOM) | OS + language deps |

Maintainer/health: OSSF Scorecard (`scorecard --npm=<pkg>` / `--pypi=` / repo),
registry metadata (`npm view <pkg>@<ver> time`, `npm owner ls <pkg>`).

## Verdict + confidence

Per-package verdict (Socket's action vocabulary): **Block** (confirmed high-impact
or malware) / **Warn** (real concern, needs a human) / **Monitor** (suspicious,
unconfirmed) / **Ignore**. Severity: Critical / High / Medium / Low.

Confidence-gate every Block/Warn at ≥ 0.7. Below that, it's a `Monitor`. A
suspected-but-unconfirmed pattern is never a Block. Every CVE needs an advisory ID;
every supply-chain flag needs the concrete trigger as evidence.
