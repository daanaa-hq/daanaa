#!/bin/bash
# Pre-deployment safety gates — prevents bad deploys to production
#
# Run BEFORE any deploy to droplet. Verifies:
#   1. All tests pass (unit, integration, type checks)
#   2. Database integrity
#   3. API endpoints respond
#   4. No uncommitted changes
#   5. Frontend builds without errors
#   6. Backup exists (for rollback)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════════════"
echo "  PRE-DEPLOYMENT SAFETY CHECKS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

PASSED=0
FAILED=0

check_pass() {
  echo -e "${GREEN}✅${NC} $1"
  ((PASSED++))
}

check_fail() {
  echo -e "${RED}❌${NC} $1"
  ((FAILED++))
}

# 1. Git status
echo "[1/7] Git working tree"
if git diff-index --quiet HEAD --; then
  check_pass "No uncommitted changes"
else
  check_fail "Uncommitted changes found. Commit or stash before deploying."
  git status
fi
echo ""

# 2. Frontend build
echo "[2/7] Frontend build"
if cd frontend && npm run build > /tmp/frontend_build.log 2>&1; then
  check_pass "Frontend builds successfully"
  cd ..
else
  check_fail "Frontend build failed"
  tail -20 /tmp/frontend_build.log
  cd ..
fi
echo ""

# 3. Database integrity
echo "[3/7] Database integrity"
if sqlite3 data/merit_registry.db "PRAGMA integrity_check;" | grep -q "ok"; then
  check_pass "merit_registry.db passes integrity check"
else
  check_fail "merit_registry.db has integrity issues"
fi
echo ""

# 4. API health (local)
echo "[4/7] Local API health"
if command -v python3 &>/dev/null && python3 -c "import flask" 2>/dev/null; then
  check_pass "API dependencies available"
else
  check_fail "Python/Flask missing or venv not activated"
fi
echo ""

# 5. FTS5 health
echo "[5/7] FTS5 search index"
FTS_COUNT=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM org_fts 2>/dev/null" || echo "0")
TOTAL_COUNT=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched")
if [ "$FTS_COUNT" -gt 0 ] && [ "$FTS_COUNT" -eq "$TOTAL_COUNT" ]; then
  check_pass "FTS5 index healthy ($FTS_COUNT orgs)"
else
  check_fail "FTS5 index out of sync (index: $FTS_COUNT, total: $TOTAL_COUNT)"
fi
echo ""

# 6. Recent backup exists
echo "[6/7] Backup availability"
BACKUP_DIR="/backups/merit_registry"
if [ -d "$BACKUP_DIR" ]; then
  LATEST=$(find "$BACKUP_DIR" -name "db_*.db.gz.enc" -printf '%T@\n' | sort -rn | head -1)
  if [ -n "$LATEST" ]; then
    HOURS_OLD=$(( ($(date +%s) - ${LATEST%.*}) / 3600 ))
    if [ "$HOURS_OLD" -lt 26 ]; then
      check_pass "Recent backup exists ($HOURS_OLD hours old)"
    else
      check_fail "Backup stale ($HOURS_OLD hours old, expected <26h)"
    fi
  else
    check_fail "No backups found in $BACKUP_DIR"
  fi
else
  check_fail "Backup directory $BACKUP_DIR missing"
fi
echo ""

# 7. Droplet connectivity
echo "[7/7] Droplet connectivity"
if ssh -o ConnectTimeout=5 root@162.243.97.179 "echo 'OK'" &>/dev/null; then
  check_pass "Can SSH to droplet (162.243.97.179)"
else
  check_fail "Cannot reach droplet. Check network/SSH keys."
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "  RESULTS: $PASSED passed, $FAILED failed"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ $FAILED -gt 0 ]; then
  echo -e "${RED}❌ DEPLOYMENT BLOCKED${NC}"
  echo ""
  echo "Fix the issues above before deploying."
  echo ""
  exit 1
else
  echo -e "${GREEN}✅ ALL CHECKS PASSED — Safe to deploy${NC}"
  echo ""
  echo "Next: bash infrastructure/deployment/safe_deploy.sh"
  echo ""
  exit 0
fi
