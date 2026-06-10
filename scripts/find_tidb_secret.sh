#!/bin/bash
#
# find_tidb_secret.sh — Find and display the leaked TiDB credential in git history
#
# Use this to get the exact string you need to search for in Aliyun console
# to verify the credential has been rotated/disabled.
#

set -e

BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE"

echo "=== Finding TiDB DATABASE_URL in git history ==="
echo ""

# Find the commit
COMMIT=$(git log --all --full-history -S "DATABASE_URL=" --oneline -- scripts/daily_sync.sh | head -1)

if [ -z "$COMMIT" ]; then
  echo "ERROR: DATABASE_URL not found in git history"
  exit 1
fi

echo "Found in commit: $COMMIT"
echo ""

# Show the exact lines with the credential
echo "Showing the lines with credentials:"
echo "---"
git show "$COMMIT:scripts/daily_sync.sh" | grep -A2 -B2 "DATABASE_URL" || true
echo "---"
echo ""

# Extract the full connection string
echo "Full credential string (for Aliyun verification):"
git show "$COMMIT:scripts/daily_sync.sh" | grep "DATABASE_URL" | head -1
echo ""

echo "NEXT STEPS:"
echo "1. Log into Aliyun TiDB console"
echo "2. Find and verify this credential is DISABLED/REVOKED"
echo "3. Confirm a new credential is in use"
echo "4. Once verified, run: bash scripts/clean_git_history.sh"
echo ""
