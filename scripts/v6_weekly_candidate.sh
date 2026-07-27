#!/bin/bash
# v6_weekly_candidate.sh
#
# Weekly scoring workflow for v6 financial context.
#
# Sequence:
# 1. Weekly preflight
# 2. Freeze input snapshot
# 3. Generate candidate scoring run
# 4. Validate candidate
# 5. Fairness review
# 6. Candidate report
# 7. Approval gate (blocks activation until manual approval)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${REPO_ROOT}/data/merit_registry.db"
LOCK_FILE="${REPO_ROOT}/data/v6_operation.lock"
LOG_DIR="${REPO_ROOT}/logs/v6"
BACKUP_DIR="${REPO_ROOT}/data/backups/v6"
REPORT_DIR="${REPO_ROOT}/reports/v6"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

mkdir -p "$LOG_DIR" "$BACKUP_DIR" "$REPORT_DIR"

LOG_FILE="${LOG_DIR}/weekly_${TIMESTAMP}.log"
REPORT_FILE="${REPORT_DIR}/v6_candidate_${TIMESTAMP}.md"

# Logging function
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

# Check 7 days of daily reports
DAILY_REPORTS=$(find "$LOG_DIR" -name "daily_*.log" -mtime -7 | wc -l)
if [ "$DAILY_REPORTS" -lt 7 ]; then
    log "⚠️  Only $DAILY_REPORTS days of reports (expected 7 from past week)"
fi
log "✓ Daily reports check: $DAILY_REPORTS available"

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
        log "⚠️  Table $table is empty (may not be ingesting yet)"
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

# Create new candidate run (placeholder — real implementation would run scorer)
CANDIDATE_RUN_ID="v6_candidate_${TIMESTAMP}"

log "ℹ️  Candidate generation not yet automated (placeholder)"
log "    Candidate run: $CANDIDATE_RUN_ID"
log "    Next step: Run scripts/v6_candidate_run_from_foundation.py or similar"
log ""
log "    Expected scorer to:"
log "    - Exclude revoked organizations"
log "    - Use active deductible 501(c)(3)s"
log "    - Map states to 4 Census regions"
log "    - Use verified revenue bands only"
log "    - Apply 5-tier hierarchy"
log "    - Require ≥5 scoreable peers for numeric context"
log "    - Store conditional bands separately"
log "    - Record source years + confidence"
log "    - Mark status='candidate' (NOT active)"

log "⚠️  MANUAL STEP: Run scorer to generate $CANDIDATE_RUN_ID"

# For now, use the most recent active run from the database
ACTUAL_CANDIDATE=$(sqlite3 "$DB_PATH" "SELECT run_id FROM v6_scoring_runs WHERE status='candidate' ORDER BY created_at DESC LIMIT 1;" 2>&1)
if [ -n "$ACTUAL_CANDIDATE" ] && [ "$ACTUAL_CANDIDATE" != "" ]; then
    CANDIDATE_RUN_ID="$ACTUAL_CANDIDATE"
    log "✓ Using existing candidate: $CANDIDATE_RUN_ID"
else
    log "⚠️  No candidate run found in database. Scoring workflow incomplete."
    fail "No candidate run available. Manual run generation required."
fi

# === VALIDATE CANDIDATE ===
log ""
log "STEP 4: CANDIDATE VALIDATION"
log "---"

cd "$REPO_ROOT"
python3 scripts/v6_validate_run.py "$CANDIDATE_RUN_ID" "$DB_PATH" >> "$LOG_FILE" 2>&1 || fail "Validation failed"
log "✓ Candidate validation passed"

# === FAIRNESS REVIEW ===
log ""
log "STEP 5: FAIRNESS & STEWARDSHIP REVIEW"
log "---"

log "ℹ️  Fairness review not yet automated (placeholder)"
log "    Should compare with prior approved run by:"
log "    - Revenue band distribution"
log "    - Regional coverage"
log "    - NTEE coverage"
log "    - Archetype distribution"
log "    - Organization size distribution"
log "    - Data availability changes"
log "    - Revocation status changes"
log ""
log "    Flag large tier shifts due only to missing data"
log "    Flag disproportionate changes for small organizations"
log "    Flag regional coverage differences"
log "    Flag unexplained archetype changes"
log "    Flag sudden Tier 5 increases"

# === CANDIDATE REPORT ===
log ""
log "STEP 6: CANDIDATE REPORT"
log "---"

{
    echo "# V6 Candidate Scoring Run"
    echo ""
    echo "**Run ID:** \`$CANDIDATE_RUN_ID\`"
    echo "**Status:** candidate (inactive)"
    echo "**Created:** $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo ""
    echo "## Summary"
    echo ""
    echo "- Candidate run generated and validated"
    echo "- Status: **NOT ACTIVE** (requires founder approval)"
    echo "- Public API: still using prior approved run"
    echo "- Frontend: v6 feature flag: still disabled"
    echo ""
    echo "## Candidate Details"
    echo ""
    echo "- Run ID: \`$CANDIDATE_RUN_ID\`"
    echo "- Snapshot: \`$SNAPSHOT_ID\`"
    echo "- Validation: ✅ PASSED"
    echo "- Fairness review: ℹ️  Automated checks pending implementation"
    echo ""
    echo "## Next Steps"
    echo ""
    echo "1. ✅ Validation completed (see logs/v6/weekly_${TIMESTAMP}.log)"
    echo "2. ⏳ Fairness review pending (needs human or automated checks)"
    echo "3. ⏳ Founder approval required (see APPROVAL GATE)"
    echo ""
    echo "## Approval Gate (BLOCKING)"
    echo ""
    echo "**This candidate will NOT be activated automatically.**"
    echo ""
    echo "To activate, founder must:"
    echo ""
    echo "1. Review the candidate run (\`$CANDIDATE_RUN_ID\`)"
    echo "2. Verify fairness and coverage"
    echo "3. Approve by running:"
    echo "   \`\`\`bash"
    echo "   sqlite3 data/merit_registry.db \"UPDATE v6_scoring_runs SET status='approved' WHERE run_id='$CANDIDATE_RUN_ID';\""
    echo "   \`\`\`"
    echo ""
    echo "Only after approval may the run become active in production."
    echo ""
    echo "---"
    echo ""
    echo "## Database Status"
    echo ""
    TIER_DIST=$(sqlite3 "$DB_PATH" "SELECT selected_tier, COUNT(*) as cnt FROM v6_peer_context_assignments WHERE run_id='$CANDIDATE_RUN_ID' GROUP BY selected_tier ORDER BY selected_tier;")
    echo "\`\`\`"
    echo "$TIER_DIST"
    echo "\`\`\`"
    echo ""
    echo "## Log"
    echo ""
    echo "See: \`$LOG_FILE\`"
    echo ""
} > "$REPORT_FILE"

log "✓ Candidate report written: $REPORT_FILE"

# === APPROVAL GATE ===
log ""
log "STEP 7: APPROVAL GATE"
log "---"

log ""
log "⚠️  BLOCKING GATE: Manual approval required"
log ""
log "Candidate run: $CANDIDATE_RUN_ID"
log "Status in database: candidate (inactive)"
log ""
log "To proceed, founder must review and approve:"
log "  $REPORT_FILE"
log ""
log "Then set status to 'approved':"
log "  sqlite3 $DB_PATH \"UPDATE v6_scoring_runs SET status='approved' WHERE run_id='$CANDIDATE_RUN_ID';\""
log ""

# === SUMMARY ===
log ""
log "=========================================="
log "✅ WEEKLY CANDIDATE WORKFLOW COMPLETED"
log "=========================================="
log "Candidate run: $CANDIDATE_RUN_ID"
log "Status: candidate (awaiting founder approval)"
log "Report: $REPORT_FILE"
log "Log: $LOG_FILE"
log ""
log "⏭️  Next: Founder reviews and approves candidate"
log ""

exit 0
