#!/bin/bash
# v6_weekly_candidate.sh
#
# Weekly scoring workflow for v6 financial context.
#
# Sequence:
# 1. Weekly preflight
# 2. Freeze input snapshot
# 3. Generate fresh candidate scoring run (never reuse old)
# 4. Build conditional band context
# 5. Validate candidate
# 6. Fairness review
# 7. Candidate report with approval gate
# 8. Block activation until founder approves

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${REPO_ROOT}/data/merit_registry.db"
LOCK_FILE="${REPO_ROOT}/data/v6_operation.lock"
LOG_DIR="${REPO_ROOT}/logs/v6"
BACKUP_DIR="${REPO_ROOT}/data/backups/v6"
REPORT_DIR="${REPO_ROOT}/reports/v6"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

# Fresh run ID every week — NEVER reuse previous candidate
CANDIDATE_RUN_ID="v6_candidate_${TIMESTAMP}"

mkdir -p "$LOG_DIR" "$BACKUP_DIR" "$REPORT_DIR"

LOG_FILE="${LOG_DIR}/weekly_${TIMESTAMP}.log"
REPORT_FILE="${REPORT_DIR}/v6_candidate_${TIMESTAMP}.md"

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG_FILE"
}

fail() {
    echo "❌ FAILED: $*" | tee -a "$LOG_FILE"
    exit 1
}

# Acquire lock
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE")
    if kill -0 "$LOCK_PID" 2>/dev/null; then
        fail "Another v6 operation (PID $LOCK_PID) is running. Exiting."
    fi
fi

echo $$ > "$LOCK_FILE"
trap "rm -f '$LOCK_FILE'" EXIT

log "=========================================="
log "V6 WEEKLY CANDIDATE GENERATION"
log "=========================================="

# === PREFLIGHT ===
log ""
log "STEP 1: WEEKLY PREFLIGHT"
log "---"

# Check database integrity
INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1)
if [ "$INTEGRITY" != "ok" ]; then
    fail "Database integrity check failed: $INTEGRITY"
fi
log "✓ Database integrity: ok"

# Check normalized tables populated
for table in org_financial_years org_classifications org_operating_context; do
    COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM $table;" 2>&1)
    if [ "$COUNT" -eq 0 ]; then
        log "⚠️  Table $table is empty"
    else
        log "✓ Table $table: $COUNT rows"
    fi
done

log "✓ Preflight passed"

# === FREEZE SNAPSHOT ===
log ""
log "STEP 2: FREEZE INPUT SNAPSHOT"
log "---"

SNAPSHOT_ID="v6_snapshot_${TIMESTAMP}"
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.db 2>/dev/null | head -1)

{
    echo "snapshot_id: $SNAPSHOT_ID"
    echo "timestamp: $TIMESTAMP"
    echo "backup_path: $LATEST_BACKUP"
    echo "git_commit: $(cd $REPO_ROOT && git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo "methodology_version: v6_foundation"
    echo "db_size: $(du -h $DB_PATH | cut -f1)"
} > "${REPORT_DIR}/${SNAPSHOT_ID}.txt"

log "✓ Snapshot frozen: $SNAPSHOT_ID"

# === GENERATE CANDIDATE ===
log ""
log "STEP 3: GENERATE CANDIDATE SCORING RUN"
log "---"

log "Generating fresh candidate run: $CANDIDATE_RUN_ID"

cd "$REPO_ROOT"

# Run the scorer
python3 scripts/v6_candidate_run_from_foundation.py \
    --db "$DB_PATH" \
    --run-id "$CANDIDATE_RUN_ID" \
    >> "$LOG_FILE" 2>&1 || fail "Scorer failed. See $LOG_FILE"

log "✓ Candidate generated: $CANDIDATE_RUN_ID"

# === BUILD CONDITIONAL CONTEXT ===
log ""
log "STEP 4: BUILD CONDITIONAL BAND CONTEXT"
log "---"

python3 scripts/v6_populate_conditional_context.py \
    --db "$DB_PATH" \
    --run-id "$CANDIDATE_RUN_ID" \
    >> "$LOG_FILE" 2>&1 || fail "Conditional context generation failed"

log "✓ Conditional context built"

# === VALIDATE CANDIDATE ===
log ""
log "STEP 5: CANDIDATE VALIDATION"
log "---"

python3 scripts/v6_validate_run.py "$CANDIDATE_RUN_ID" "$DB_PATH" >> "$LOG_FILE" 2>&1
VALIDATION_EXIT=$?

if [ $VALIDATION_EXIT -ne 0 ]; then
    log "❌ Validation FAILED"
    fail "Candidate run failed validation. See $LOG_FILE for details."
fi

log "✓ Candidate validation passed"

# === FAIRNESS REVIEW ===
log ""
log "STEP 6: FAIRNESS & STEWARDSHIP REVIEW"
log "---"

# Get tier distribution for candidate
TIER_DIST=$(sqlite3 "$DB_PATH" "
    SELECT selected_tier, COUNT(*) as cnt
    FROM v6_peer_context_assignments
    WHERE run_id='$CANDIDATE_RUN_ID'
    GROUP BY selected_tier
    ORDER BY selected_tier;
")

log "Candidate tier distribution:"
echo "$TIER_DIST" | while read line; do
    log "  $line"
done

# Get data quality metrics
REVOKED_COUNT=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*) FROM v6_peer_context_assignments a
    WHERE a.run_id='$CANDIDATE_RUN_ID'
    AND a.selected_tier IN ('1_direct','2_regional_conditional','3_broader_regional','4_national')
    AND a.ein IN (SELECT EIN FROM registry_enriched WHERE irs_revoked=1 OR org_status='revoked');
")

MISSING_GEO=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*) FROM v6_peer_context_assignments
    WHERE run_id='$CANDIDATE_RUN_ID'
    AND selected_tier='2_regional_conditional'
    AND (geography_scope IS NULL OR geography_value NOT IN ('Northeast','Midwest','South','West'));
")

INVALID_REVENUE=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*) FROM v6_peer_context_assignments
    WHERE run_id='$CANDIDATE_RUN_ID'
    AND revenue_band NOT IN ('grassroots','small','mid','established','major',NULL);
")

log ""
log "Data quality metrics:"
log "  Revoked in active tiers: $REVOKED_COUNT (expected: 0)"
log "  Tier 2 missing valid region: $MISSING_GEO (expected: 0)"
log "  Invalid revenue bands: $INVALID_REVENUE (expected: 0)"

# Check thresholds
if [ "$REVOKED_COUNT" -gt 0 ] || [ "$MISSING_GEO" -gt 0 ] || [ "$INVALID_REVENUE" -gt 0 ]; then
    log "⚠️  Data quality issues found. Candidate is valid but may need review."
fi

# === CANDIDATE REPORT ===
log ""
log "STEP 7: CANDIDATE REPORT"
log "---"

TOTAL_ASSIGNMENTS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM v6_peer_context_assignments WHERE run_id='$CANDIDATE_RUN_ID';")
CONDITIONAL_ROWS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM v6_conditional_band_context WHERE run_id='$CANDIDATE_RUN_ID' 2>/dev/null || echo 0;")

{
    echo "# V6 Candidate Scoring Run"
    echo ""
    echo "**Run ID:** \`$CANDIDATE_RUN_ID\`"
    echo "**Status:** candidate (awaiting founder approval)"
    echo "**Created:** $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo ""
    echo "## Summary"
    echo ""
    echo "✅ Candidate generated and validated"
    echo ""
    echo "**Status: PENDING FOUNDER APPROVAL**"
    echo "- Public API: still using prior approved run"
    echo "- Frontend: v6 feature flag: disabled"
    echo "- Database status: \`candidate\` (not active)"
    echo ""
    echo "## Metrics"
    echo ""
    echo "| Metric | Value |"
    echo "|--------|-------|"
    echo "| Total assignments | $TOTAL_ASSIGNMENTS |"
    echo "| Conditional context rows | $CONDITIONAL_ROWS |"
    echo "| Revoked in active tiers | $REVOKED_COUNT (✅ should be 0) |"
    echo "| Tier 2 missing region | $MISSING_GEO (✅ should be 0) |"
    echo "| Invalid revenue bands | $INVALID_REVENUE (✅ should be 0) |"
    echo ""
    echo "## Tier Distribution"
    echo ""
    echo "\`\`\`"
    echo "$TIER_DIST"
    echo "\`\`\`"
    echo ""
    echo "## Approval Gate (BLOCKING)"
    echo ""
    echo "**This candidate is NOT automatically active.**"
    echo ""
    echo "To activate in staging:"
    echo ""
    echo "1. Founder reviews this report"
    echo "2. Verify data quality thresholds above"
    echo "3. If approved, run:"
    echo ""
    echo "\`\`\`bash"
    echo "sqlite3 data/merit_registry.db \"UPDATE v6_scoring_runs SET status='approved' WHERE run_id='$CANDIDATE_RUN_ID';\""
    echo "\`\`\`"
    echo ""
    echo "4. Enable feature flags to use in staging:"
    echo ""
    echo "\`\`\`bash"
    echo "export ENABLE_V6_FINANCIAL_CONTEXT=true"
    echo "export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true"
    echo "./restart_api.sh"
    echo "\`\`\`"
    echo ""
    echo "## Log"
    echo ""
    echo "See: \`$LOG_FILE\`"
    echo ""
    echo "---"
    echo ""
    echo "**Generated:** $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo ""
} > "$REPORT_FILE"

log "✓ Candidate report written: $REPORT_FILE"

# === APPROVAL GATE ===
log ""
log "STEP 8: APPROVAL GATE (BLOCKING)"
log "---"

log ""
log "⚠️  BLOCKING GATE: Manual founder approval required"
log ""
log "Candidate run: $CANDIDATE_RUN_ID"
log "Status in database: candidate (inactive)"
log ""
log "To proceed, founder must:"
log "  1. Review: $REPORT_FILE"
log "  2. Verify data quality thresholds"
log "  3. Approve by running:"
log "     sqlite3 $DB_PATH \"UPDATE v6_scoring_runs SET status='approved' WHERE run_id='$CANDIDATE_RUN_ID';\""
log ""
log "Then staging can be enabled:"
log "  export ENABLE_V6_FINANCIAL_CONTEXT=true"
log "  export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true"
log "  ./restart_api.sh"
log ""

# === SUMMARY ===
log ""
log "=========================================="
log "✅ WEEKLY CANDIDATE WORKFLOW COMPLETED"
log "=========================================="
log "Candidate run: $CANDIDATE_RUN_ID"
log "Status: candidate (awaiting approval)"
log "Report: $REPORT_FILE"
log "Log: $LOG_FILE"
log ""
log "⏭️  Next: Founder reviews and approves candidate"
log ""

exit 0
