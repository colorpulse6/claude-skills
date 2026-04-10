#!/bin/bash
# Scan staged files for potential secrets.
# Exit codes: 0 = clean, 1 = secrets detected

set -uo pipefail

cd "$(git rev-parse --show-toplevel)"

FAILED=0

# Patterns for filenames that shouldn't be committed
FILENAME_PATTERNS=(
  "\.env$"
  "\.env\."
  "credentials\.json"
  "\.key$"
  "\.pem$"
  "id_rsa"
  "id_ed25519"
  "\.p12$"
  "\.pfx$"
  "service-account.*\.json"
  "gcloud-service-key.*\.json"
)

STAGED=$(git diff --cached --name-only 2>/dev/null || true)

if [ -n "$STAGED" ]; then
  for pattern in "${FILENAME_PATTERNS[@]}"; do
    if matches=$(echo "$STAGED" | grep -E "$pattern" || true); then
      if [ -n "$matches" ]; then
        echo "FAIL: Potential secret file staged: $matches" >&2
        FAILED=1
      fi
    fi
  done
fi

# Patterns for secret content in staged diffs
CONTENT_PATTERNS=(
  "AKIA[0-9A-Z]{16}"                                    # AWS access key
  "aws_secret_access_key"                               # AWS secret
  "-----BEGIN (RSA|OPENSSH|DSA|EC) PRIVATE KEY-----"   # SSH keys
  "sk_live_[a-zA-Z0-9]{24,}"                          # Stripe live key
  "xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+"                   # Slack bot token
  "xoxp-[0-9]+-[0-9]+-[0-9]+-[a-f0-9]+"               # Slack user token
  "ghp_[a-zA-Z0-9]{36}"                                # GitHub personal token
  "github_pat_[a-zA-Z0-9_]{82}"                       # GitHub fine-grained token
)

if [ -n "$STAGED" ]; then
  DIFF=$(git diff --cached 2>/dev/null || true)
  for pattern in "${CONTENT_PATTERNS[@]}"; do
    if echo "$DIFF" | grep -qE "$pattern"; then
      echo "FAIL: Secret pattern detected in staged diff: $pattern" >&2
      FAILED=1
    fi
  done
fi

if [ $FAILED -eq 0 ]; then
  echo "OK: no secrets detected"
  exit 0
else
  echo "FAILED: secret scan detected issues" >&2
  echo "Remove offending files: git reset HEAD <file>" >&2
  exit 1
fi
