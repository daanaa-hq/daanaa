#!/bin/bash
# v6_weekly_candidate_generation.sh
#
# Phase 4: Weekly Candidate Generation
#
# Generates a fresh v6 scoring candidate run with:
# - Fresh candidate run ID
# - Scoring with revocation filtering
# - Conditional context generation
# - Full validation (10 gates)
# - Revocation blocking
# - Fairness comparison
# - Comprehensive reporting
#
# Usage:
#   bash scripts/v6_weekly_candidate_generation.sh [baseline_run_id]
#
# Args:
#   baseline_run_id (optional): Explicit baseline for fairness comparison
#                               (default: v6_foundation_candidate_20260727_corrected)
#
# Exit codes:
#   0 = Candidate generated and validated successfully
#   1 = Candidate generation or validation failed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_PATH="${PROJECT_ROOT}/data/merit_registry.db"
REPORTS_DIR="${PROJECT_ROOT}/reports/v6"

# Configuration
BASELINE_RUN="${1:-v6_foundation_candidate_20260727_corrected}"
RUN_ID="v6_candidate_$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_FILE="${REPORTS_DIR}/candidate_${RUN_ID}.md"
LOG_FILE="/tmp/v6_weekly_$(date -u +%Y%m%dT%H%M%SZ).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Utilities
log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"
}

report_section() {
  echo "## $1" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
}

report_status() {
  local status="$1"
  echo "**Status:** $status" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
}

# ============================================================================
# PREFLIGHT
# ============================================================================

log "Phase 4: Weekly Candidate Generation"
echo "# V6 Weekly Candidate Report" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Date:** $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REPORT_FILE"
echo "**Candidate Run:** \`$RUN_ID\`" >> "$REPORT_FILE"
echo "**Comparison Baseline:** \`$BASELINE_RUN\`" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

report_section "Preflight"

# Database exists and is healthy
if [ ! -f "$DB_PATH" ]; then
  log "ERROR: Database not found"
  report_status "BLOCKED: Database not found"
  exit 1
fi

INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null)
if [ "$INTEGRITY" != "ok" ]; then
  log "ERROR: Database integrity check failed: $INTEGRITY"
  report_status "BLOCKED: Database integrity failed"
  exit 1
fi
log "✓ Database healthy"

# Baseline run exists
BASELINE_EXISTS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM v6_scoring_runs WHERE run_id='$BASELINE_RUN';" 2>/dev/null)
if [ "$BASELINE_EXISTS" -eq 0 ]; then
  log "ERROR: Baseline run not found: $BASELINE_RUN"
  report_status "BLOCKED: Baseline run not found"
  exit 1
fi
log "✓ Baseline run exists: $BASELINE_RUN"

echo "| Check | Result |" >> "$REPORT_FILE"
echo "|-------|--------|" >> "$REPORT_FILE"
echo "| Database integrity | ✓ |" >> "$REPORT_FILE"
echo "| Baseline exists | ✓ |" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
report_status "PASS"

# ============================================================================
# STEP 1: CREATE FRESH RUN ID
# ============================================================================

log "Step 1: Creating fresh run ID: $RUN_ID"
report_section "Step 1: Run ID"
echo "Generated fresh candidate run ID: \`$RUN_ID\`" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
report_status "PASS"

# ============================================================================
# STEP 2: RUN SCORER
# ============================================================================

log "Step 2: Running scorer..."
report_section "Step 2: Scoring"

if python3 "$SCRIPT_DIR/v6_candidate_run_from_foundation.py" \
  --db "$DB_PATH" \
  --run-id "$RUN_ID" 2>&1 | tee -a "$LOG_FILE"; then

  # Get tier distribution
  TIER_STATS=$(sqlite3 "$DB_PATH" "
    SELECT
      selected_tier,
      COUNT(*) as cnt
    FROM v6_peer_context_assignments
    WHERE run_id = '$RUN_ID'
    GROUP BY selected_tier
    ORDER BY selected_tier;
  " 2>/dev/null)

  echo "| Tier | Count |" >> "$REPORT_FILE"
  echo "|------|-------|" >> "$REPORT_FILE"
  echo "$TIER_STATS" | while read tier cnt; do
    if [ -n "$tier" ]; then
      echo "| $tier | $cnt |" >> "$REPORT_FILE"
    fi
  done
  echo "" >> "$REPORT_FILE"

  log "✓ Scoring completed"
  report_status "PASS"
else
  log "ERROR: Scoring failed"
  report_status "BLOCKED: Scoring failed"
  exit 1
fi

# ============================================================================
# STEP 3: GENERATE CONDITIONAL CONTEXT
# ============================================================================

log "Step 3: Generating conditional context..."
report_section "Step 3: Conditional Context"

if python3 "$SCRIPT_DIR/v6_populate_conditional_context.py" \
  --db "$DB_PATH" \
  --run-id "$RUN_ID" 2>&1 | tee -a "$LOG_FILE"; then

  CONDITIONAL_COUNT=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*) FROM v6_conditional_band_context
    WHERE run_id = '$RUN_ID';
  " 2>/dev/null || echo "0")

  echo "Conditional context records: $CONDITIONAL_COUNT" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"

  log "✓ Conditional context generated ($CONDITIONAL_COUNT records)"
  report_status "PASS"
else
  log "ERROR: Conditional context generation failed"
  report_status "BLOCKED: Conditional context failed"
  exit 1
fi

# ============================================================================
# STEP 4: VALIDATE CANDIDATE
# ============================================================================

log "Step 4: Validating candidate (10 gates)..."
report_section "Step 4: Validation (10 Gates)"

if python3 "$SCRIPT_DIR/v6_validate_run.py" \
  "$RUN_ID" \
  "$DB_PATH" 2>&1 | tee -a "$LOG_FILE" >> "$REPORT_FILE"; then

  log "✓ Validation passed (all 10 gates)"
  report_status "PASS"
else
  log "ERROR: Validation failed"
  report_status "BLOCKED: Validation failed"
  exit 1
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# STEP 5: REVOCATION BLOCKING
# ============================================================================

log "Step 5: Revocation verification..."
report_section "Step 5: Revocation Blocking"

if python3 "$SCRIPT_DIR/v6_revocation_verify_and_block.py" \
  "$RUN_ID" \
  "$DB_PATH" 2>&1 | tee -a "$LOG_FILE"; then

  log "✓ Revocation check passed"
  report_status "PASS"
else
  log "ERROR: Revocation blocking failed"
  report_status "BLOCKED: Revocation check failed"
  exit 1
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# STEP 6: FAIRNESS COMPARISON
# ============================================================================

log "Step 6: Fairness comparison vs. baseline..."
report_section "Step 6: Fairness Comparison"

if python3 "$SCRIPT_DIR/v6_fairness_comparison_corrected.py" \
  "$RUN_ID" \
  "$BASELINE_RUN" \
  "$DB_PATH" 2>&1 | tee -a "$LOG_FILE" >> "$REPORT_FILE"; then

  log "✓ Fairness comparison completed"
  report_status "PASS"
else
  log "ERROR: Fairness comparison failed"
  report_status "BLOCKED: Fairness comparison failed"
  exit 1
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# STEP 7: VERIFY CANDIDATE STATUS
# ============================================================================

log "Step 7: Verifying candidate status..."
report_section "Step 7: Candidate Status"

CANDIDATE_STATUS=$(sqlite3 "$DB_PATH" \
  "SELECT status FROM v6_scoring_runs WHERE run_id='$RUN_ID';" 2>/dev/null)

if [ "$CANDIDATE_STATUS" = "candidate" ]; then
  echo "Candidate status: **$CANDIDATE_STATUS** (inactive, awaiting approval)" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  log "✓ Candidate status is 'candidate' (not active)"
  report_status "PASS"
else
  log "ERROR: Candidate status is '$CANDIDATE_STATUS' (expected 'candidate')"
  echo "Candidate status: **$CANDIDATE_STATUS** (ERROR: expected 'candidate')" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  report_status "BLOCKED: Unexpected candidate status"
  exit 1
fi

# ============================================================================
# SUMMARY
# ============================================================================

log "Weekly candidate generation completed"
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## Summary" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "✓ Candidate generated: \`$RUN_ID\`" >> "$REPORT_FILE"
echo "✓ All 10 validation gates passed" >> "$REPORT_FILE"
echo "✓ Revocation check passed" >> "$REPORT_FILE"
echo "✓ Fairness comparison completed" >> "$REPORT_FILE"
echo "✓ Candidate status: candidate (not active)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Next Step:** Founder reviews fairness report and approves activation:" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "\`\`\`bash" >> "$REPORT_FILE"
echo "sqlite3 data/merit_registry.db \\" >> "$REPORT_FILE"
echo "  \"UPDATE v6_scoring_runs SET status='approved' WHERE run_id='$RUN_ID';\"" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo ""
echo -e "${GREEN}✓ Weekly candidate generation completed${NC}"
echo "Candidate:        $RUN_ID"
echo "Status:           candidate (inactive)"
echo "Baseline:         $BASELINE_RUN"
echo "Report:           $REPORT_FILE"
echo ""
echo "Next step: Founder reviews and approves the candidate for activation"
echo ""

exit 0
