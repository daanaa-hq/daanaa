#!/bin/bash
# Automated data pipeline repair — fixes common issues
#
# Run when pipeline_health.py detects problems, or manually before major ops
#
# What it does:
#   1. Rebuild FTS5 if out of sync
#   2. Recompute stale embeddings
#   3. Trigger scorer if it hasn't run recently
#   4. Vacuum database to reclaim space
#   5. Verify repairs completed

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════════════"
echo "  Pipeline Repair Toolkit"
echo "═══════════════════════════════════════════════════════════════"
echo ""

source venv/bin/activate

REPAIRED=0
FAILED=0

repair_step() {
  local name=$1
  local cmd=$2

  echo "[*] $name..."
  if eval "$cmd" 2>/tmp/repair_error.log; then
    echo -e "${GREEN}✅${NC} $name completed"
    ((REPAIRED++))
  else
    echo -e "${RED}❌${NC} $name failed"
    tail -5 /tmp/repair_error.log | sed 's/^/   /'
    ((FAILED++))
  fi
  echo ""
}

# Check current health first
echo "[*] Checking current pipeline health..."
python3 infrastructure/pipeline/pipeline_health.py > /tmp/health_before.txt 2>&1
echo ""

# 1. Rebuild FTS5 if needed
echo "[1/4] FTS5 Index"
FTS_COUNT=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM org_fts 2>/dev/null" || echo "0")
TOTAL_COUNT=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched")

if [ "$FTS_COUNT" -ne "$TOTAL_COUNT" ]; then
  repair_step "Rebuilding FTS5" "python3 scripts/build_fts_index.py"
else
  echo -e "${GREEN}✓${NC} FTS5 in sync ($FTS_COUNT / $TOTAL_COUNT)"
  echo ""
fi

# 2. Recompute embeddings (sample the recent ones)
echo "[2/4] Embeddings Index"
EMB_COUNT=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM org_embeddings WHERE embedding IS NOT NULL 2>/dev/null" || echo "0")

if [ "$EMB_COUNT" -lt 400000 ]; then
  repair_step "Recomputing embeddings" "python3 scripts/build_org_embeddings.py"
else
  # Just handle recent
  repair_step "Updating recent embeddings" "python3 scripts/build_org_embeddings.py --recent"
fi

# 3. Check scorer and run if needed
echo "[3/4] Scorer Pipeline"
LAST_RUN=$(sqlite3 data/merit_registry.db \
  "SELECT run_date FROM score_snapshots ORDER BY run_date DESC LIMIT 1 2>/dev/null" || echo "")

if [ -z "$LAST_RUN" ]; then
  echo "No scores found. Running full scorer (this takes ~30 min)..."
  repair_step "Running merit scorer v4.0" "python3 scripts/merit_scorer_v4_0.py"
else
  # Check age
  HOURS_OLD=$(python3 -c "
from datetime import datetime
last = datetime.fromisoformat('$LAST_RUN')
hours = (datetime.utcnow() - last).total_seconds() / 3600
print(int(hours))
")

  if [ "$HOURS_OLD" -gt 24 ]; then
    echo "Scorer last ran $HOURS_OLD hours ago. Re-running..."
    repair_step "Running merit scorer v4.0" "python3 scripts/merit_scorer_v4_0.py"
  else
    echo -e "${GREEN}✓${NC} Scorer current ($HOURS_OLD hours old)"
    echo ""
  fi
fi

# 4. Vacuum database (optional, but recommended)
echo "[4/4] Database Optimization"
read -p "VACUUM database to reclaim space? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  repair_step "Vacuuming database" "sqlite3 data/merit_registry.db 'VACUUM;'"
else
  echo -e "${YELLOW}⊘${NC} Skipped VACUUM"
  echo ""
fi

# Verify repairs
echo "═══════════════════════════════════════════════════════════════"
echo "  Post-Repair Health Check"
echo "═══════════════════════════════════════════════════════════════"
echo ""

python3 infrastructure/pipeline/pipeline_health.py > /tmp/health_after.txt 2>&1

if grep -q "Status: healthy" /tmp/health_after.txt; then
  echo -e "${GREEN}✅ Pipeline healthy!${NC}"
else
  echo -e "${YELLOW}⚠ Some issues remain${NC}"
  cat /tmp/health_after.txt
fi

echo ""
echo "Summary:"
echo "  Repairs completed: $REPAIRED"
if [ $FAILED -gt 0 ]; then
  echo -e "  ${RED}Failed: $FAILED${NC}"
fi
echo ""
echo "Health check logs:"
echo "  Before: /tmp/health_before.txt"
echo "  After: /tmp/health_after.txt"
echo ""
