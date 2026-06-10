#!/bin/bash
#
# clean_git_history.sh — Remove TiDB credential from git history using git-filter-repo
#
# PREREQUISITES:
#   1. Verified the TiDB credential has been DISABLED in Aliyun console
#   2. Confirmed a NEW credential is in use
#   3. Run: bash scripts/find_tidb_secret.sh (to see what will be removed)
#
# This script will:
#   - Create a backup branch (restore point if needed)
#   - Rewrite git history to replace the exposed credential
#   - Clean up git internals to prevent recovery
#

set -e

BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Git History Credential Cleanup ===${NC}"
echo ""

# ============================================================
# Check prerequisites
# ============================================================
echo "Checking prerequisites..."

if [ -z "$1" ]; then
  echo -e "${RED}ERROR: Must pass the old DATABASE_URL string as argument${NC}"
  echo ""
  echo "Usage: bash scripts/clean_git_history.sh 'old_credential_string'"
  echo ""
  echo "To find the old credential, run: bash scripts/find_tidb_secret.sh"
  exit 1
fi

OLD_CRED="$1"

if ! command -v git-filter-repo &> /dev/null; then
  echo "Installing git-filter-repo..."
  python3 -m pip install git-filter-repo >/dev/null 2>&1 || {
    echo -e "${RED}ERROR: Could not install git-filter-repo${NC}"
    echo "Install manually: pip install git-filter-repo"
    exit 1
  }
fi

echo -e "${GREEN}✓ git-filter-repo available${NC}"
echo ""

# ============================================================
# Confirmation
# ============================================================
echo -e "${YELLOW}CONFIRMATION:${NC}"
echo "This will remove the following string from git history:"
echo "  $OLD_CRED"
echo ""
echo "A backup branch will be created: backup-$(date +%s)"
echo ""
read -p "Proceed with git history rewrite? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

echo ""

# ============================================================
# Backup branch
# ============================================================
echo -e "${YELLOW}Creating backup branch...${NC}"
BACKUP_BRANCH="backup-before-scrub-$(date +%s)"
git branch "$BACKUP_BRANCH"
echo -e "${GREEN}✓ Backup: $BACKUP_BRANCH${NC}"
echo ""

# ============================================================
# Rewrite history
# ============================================================
echo -e "${YELLOW}Rewriting git history...${NC}"

git filter-repo \
  --path scripts/daily_sync.sh \
  --replace-text <(echo "$OLD_CRED==>***REDACTED_ROTATED_CREDENTIAL***") \
  --force

echo -e "${GREEN}✓ History rewritten${NC}"
echo ""

# ============================================================
# Verify removal
# ============================================================
echo -e "${YELLOW}Verifying credential is removed...${NC}"

if git log -p --all -- scripts/daily_sync.sh | grep -q "$OLD_CRED"; then
  echo -e "${RED}ERROR: Credential still present in history!${NC}"
  echo "Restore from backup: git reset --hard $BACKUP_BRANCH"
  exit 1
fi

echo -e "${GREEN}✓ Credential successfully removed${NC}"
echo ""

# ============================================================
# Summary
# ============================================================
echo -e "${GREEN}=== Cleanup Complete ===${NC}"
echo ""
echo "Summary:"
echo "  - Old credential removed from git history"
echo "  - Backup branch created: $BACKUP_BRANCH"
echo "  - Local changes only (not yet pushed to remote)"
echo ""
echo "Next steps:"
echo "  1. Test the deployment locally: git log --oneline | head"
echo "  2. If satisfied, force-push to remote: git push origin master --force-with-lease"
echo "  3. If issues, restore: git reset --hard $BACKUP_BRANCH"
echo ""
echo -e "${YELLOW}Note:${NC} Keep the backup branch until you confirm everything works."
echo ""
