#!/bin/bash
# Preflight checks for the push skill.
# Verifies gh CLI, git state, branch policy.
# Exit codes: 0 = success, 1 = gh issue, 2 = git issue, 3 = branch policy

set -euo pipefail

# 1. gh CLI installed
if ! command -v gh &>/dev/null; then
  echo "ERROR: gh CLI not installed. Install from https://cli.github.com/" >&2
  exit 1
fi

# 2. gh authenticated
if ! gh auth status &>/dev/null 2>&1; then
  echo "ERROR: gh CLI is not authenticated. Run: gh auth login" >&2
  exit 1
fi

# 3. In a git repo
if ! git rev-parse --git-dir &>/dev/null; then
  echo "ERROR: Not in a git repository." >&2
  exit 2
fi

# 4. Not detached HEAD
BRANCH=$(git branch --show-current)
if [ -z "$BRANCH" ]; then
  echo "ERROR: Detached HEAD state. Checkout a branch first." >&2
  exit 2
fi

# 5. Branch policy - not main/master
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "ERROR: Direct push to $BRANCH is blocked. Create a feature branch." >&2
  echo "Run: git checkout -b feat/<your-feature>" >&2
  exit 3
fi

echo "OK: branch=$BRANCH"
exit 0
