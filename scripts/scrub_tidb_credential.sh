#!/bin/bash
#
# scrub_tidb_credential.sh — Verify TiDB credential rotation and scrub git history
#
# Step 1: Find the leaked credential in git history
# Step 2: Manually verify rotation in Aliyun console (this script shows you what to look for)
# Step 3: Run this script to rewrite git history and remove the secret
#
# SAFETY: Creates a backup branch before rewriting history. Requires explicit confirmation.
#

set -e

BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== TiDB Credential Scrubbing Workflow ===${NC}"
echo ""

# ============================================================
# STEP 1: Find and display the leaked credential
# ============================================================
echo -e "${YELLOW}STEP 1: Searching git history for DATABASE_URL...${NC}"
echo ""

# Find the commit with the secret
COMMIT=$(git log --all --full-history -S "DATABASE_URL=" --oneline -- scripts/daily_sync.sh | head -1 | awk '{print $1}')

if [ -z "$COMMIT" ]; then
  echo -e "${RED}ERROR: Could not find DATABASE_URL in git history${NC}"
  exit 1
fi

echo "Found in commit: $COMMIT"
echo ""

# Show the actual line with the credential
echo "The leaked line is:"
git show "$COMMIT:scripts/daily_sync.sh" | grep -n "DATABASE_URL" || true
echo ""

# Extract just the URL value for Aliyun verification
LEAKED_URL=$(git show "$COMMIT:scripts/daily_sync.sh" | grep "export DATABASE_URL" | sed -E 's/.*DATABASE_URL="([^"]+)".*/\1/' || echo "NOT_FOUND")

if [ "$LEAKED_URL" = "NOT_FOUND" ]; then
  LEAKED_URL=$(git show "$COMMIT:scripts/daily_sync.sh" | grep "DATABASE_URL" | head -1)
fi

echo -e "${YELLOW}Leaked credential (for Aliyun verification):${NC}"
echo "$LEAKED_URL"
echo ""

# ============================================================
# STEP 2: Instructions for manual verification
# ============================================================
echo -e "${YELLOW}STEP 2: Manual verification in Aliyun TiDB console${NC}"
echo ""
echo "Before proceeding, you MUST:"
echo ""
echo "1. Log into Aliyun console (https://console.aliyun.com/)"
echo "2. Navigate to TiDB credentials/API keys"
echo "3. Verify that the credential above is DISABLED or REVOKED"
echo "4. Confirm a NEW credential has been issued and is in use"
echo ""
echo -e "${RED}⚠️  If the old credential is still ACTIVE, DO NOT PROCEED${NC}"
echo "The git rewrite will be wasted if the secret is still valid."
echo ""

read -p "Have you verified the credential is DISABLED in Aliyun? (yes/no): " VERIFIED

if [ "$VERIFIED" != "yes" ]; then
  echo "Aborting. Please verify credential rotation first."
  exit 1
fi

echo ""
echo -e "${GREEN}✓ Credential rotation verified${NC}"
echo ""

# ============================================================
# STEP 3: Backup and rewrite git history
# ============================================================
echo -e "${YELLOW}STEP 3: Backing up and rewriting git history${NC}"
echo ""

# Create a backup branch before rewriting
BACKUP_BRANCH="backup-before-scrub-$(date +%s)"
echo "Creating backup branch: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH"

echo ""
echo -e "${YELLOW}Running git-filter-repo to remove credential...${NC}"

# Install git-filter-repo if not present
if ! command -v git-filter-repo &> /dev/null; then
  echo "Installing git-filter-repo..."
  python3 -m pip install git-filter-repo >/dev/null 2>&1 || {
    echo -e "${RED}ERROR: Could not install git-filter-repo${NC}"
    echo "Install manually: pip install git-filter-repo"
    exit 1
  }
fi

# Create a filter spec to redact the credential
FILTER_SPEC=$(mktemp)
cat > "$FILTER_SPEC" << 'EOF'
def filter_commit(commit):
    # Remove/redact any lines containing DATABASE_URL with actual credentials
    commit.message = commit.message.replace(b'DATABASE_URL=', b'DATABASE_URL=***REDACTED***')
    for blob in commit.file_changes:
        if blob.type == b'blob':
            if b'DATABASE_URL=' in blob.contents:
                blob.contents = blob.contents.replace(
                    b'export DATABASE_URL="',
                    b'export DATABASE_URL="***REDACTED_IN_GIT_HISTORY*** # '
                )
EOF

# Use git-filter-repo to remove the credential
# This rewrites history to replace all instances of the exposed URL with a placeholder
git filter-repo \
  --path scripts/daily_sync.sh \
  --replace-text <(echo "export DATABASE_URL=\"$LEAKED_URL\"==>export DATABASE_URL=\"***REDACTED_ROTATED_CREDENTIAL***\"") \
  --force \
  2>&1 | grep -v "Rewriting commits" | head -20

rm -f "$FILTER_SPEC"

echo ""
echo -e "${GREEN}✓ Git history rewritten${NC}"
echo ""

# ============================================================
# STEP 4: Cleanup and verification
# ============================================================
echo -e "${YELLOW}STEP 4: Verification${NC}"
echo ""

echo "Checking that credential is no longer in git:"
if git log -p --all -- scripts/daily_sync.sh | grep -q "$LEAKED_URL"; then
  echo -e "${RED}ERROR: Credential still in git history!${NC}"
  echo "Restore from backup: git reset --hard $BACKUP_BRANCH"
  exit 1
fi

echo -e "${GREEN}✓ Credential successfully removed from git history${NC}"
echo ""

echo "Old backup branch saved as: $BACKUP_BRANCH"
echo "If you need to undo: git reset --hard $BACKUP_BRANCH"
echo ""
echo "The rewritten history is local only. To force-push to remote (DANGEROUS):"
echo "  git push origin master --force-with-lease"
echo ""
echo -e "${GREEN}=== Credential scrubbing complete ===${NC}"
