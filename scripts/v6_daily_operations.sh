#!/bin/bash
# v6_daily_operations.sh
#
# Daily operational workflow for v6 data foundation.
#
# Sequence:
# 1. Preflight checks
# 2. Source discovery
# 3. Backup
# 4. Ingest new records
# 5. Revocation sync
# 6. Data quality checks
# 7. Database integrity
# 8. Report and cleanup

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${REPO_ROOT}/data/merit_registry.db"
LOCK_FILE="${REPO_ROOT}/data/v6_operation.lock"
LOG_DIR="${REPO_ROOT}/logs/v6"
BACKUP_DIR="${REPO_ROOT}/data/backups/v6"
REPORT_DIR="${REPO_ROOT}/reports/v6"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

# Create directories
mkdir -p "$LOG_DIR" "$BACKUP_DIR" "$REPORT_DIR"

LOG_FILE="${LOG_DIR}/daily_${TIMESTAMP}.log"
REPORT_FILE="${REPORT_DIR}/daily_${TIMESTAMP}.md"

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
    else
        log "⚠️  Stale lock file found (PID $LOCK_PID). Requires operator review."
        fail "Stale lock file. Remove $LOCK_FILE manually after review."
    fi
fi

echo $$ > "$LOCK_FILE"
trap "rm -f '$LOCK_FILE'" EXIT

log "=========================================="
log "V6 DAILY OPERATIONS WORKFLOW"
log "=========================================="

# === 01:00 — PREFLIGHT ===
log ""
log "STEP 1: PREFLIGHT CHECKS"
log "---"

# Check repo
if [ ! -f "$DB_PATH" ]; then
    fail "Database not found: $DB_PATH"
fi
log "✓ Repository readable"

# Check disk space
DISK_FREE=$(df "$REPO_ROOT" | tail -1 | awk '{print $4}')
if [ "$DISK_FREE" -lt 1048576 ]; then  # 1 GB minimum
    fail "Insufficient disk space: ${DISK_FREE}KB free"
fi
log "✓ Disk space sufficient: ${DISK_FREE}KB free"

# Check database integrity
INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1)
if [ "$INTEGRITY" != "ok" ]; then
    fail "Database integrity check failed: $INTEGRITY"
fi
log "✓ Database integrity: ok"

# Check latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.db 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
    log "⚠️  No prior backup found"
else
    BACKUP_AGE=$(($(date +%s) - $(stat -f%m "$LATEST_BACKUP" 2>/dev/null || stat -c%Y "$LATEST_BACKUP")))
    BACKUP_HOURS=$((BACKUP_AGE / 3600))
    log "✓ Latest backup: $BACKUP_HOURS hours old"
fi

log "✓ Preflight passed"

# === 01:10 — SOURCE DISCOVERY ===
log ""
log "STEP 2: SOURCE DISCOVERY"
log "---"

cd "$REPO_ROOT"
python3 scripts/v6_source_manifest.py >> "$LOG_FILE" 2>&1 || fail "Source discovery failed"
log "✓ Source manifest created"

# === 01:25 — BACKUP ===
log ""
log "STEP 3: CREATE BACKUP"
log "---"

BACKUP_FILE="${BACKUP_DIR}/merit_registry_${TIMESTAMP}.db"
if cp --reflink=auto "$DB_PATH" "$BACKUP_FILE" 2>/dev/null || cp "$DB_PATH" "$BACKUP_FILE"; then
    log "✓ Backup created: $BACKUP_FILE"

    # Verify backup opens
    if sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM registry_enriched;" > /dev/null 2>&1; then
        log "✓ Backup verified readable"
    else
        fail "Backup verification failed"
    fi
else
    fail "Backup creation failed"
fi

# === 01:40 — INGEST (placeholder) ===
log ""
log "STEP 4: INGEST NEW RECORDS"
log "---"
log "ℹ️  Ingestion not yet automated (placeholder)"
log "    Normalized tables: org_financial_years, org_classifications, org_operating_context"
log "    See docs/V6_DAILY_WEEKLY_DATA_OPERATIONS_PLAN_2026-07-27.md for requirements"

# === 02:15 — REVOCATION SYNC (placeholder) ===
log ""
log "STEP 5: REVOCATION SYNCHRONIZATION"
log "---"
log "ℹ️  Revocation sync not yet automated (placeholder)"
log "    Target: Keep irs_revoked and org_status aligned"
log "    Validation: SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked=1 AND org_status<>'revoked'"

# === 02:30 — DATA QUALITY CHECKS (placeholder) ===
log ""
log "STEP 6: DATA QUALITY CHECKS"
log "---"
log "ℹ️  Data quality checks not yet automated (placeholder)"
log "    Track: duplicates, invalid EINs, negative values, coverage"

# === 03:00 — INTEGRITY CHECK ===
log ""
log "STEP 7: POST-INGESTION INTEGRITY"
log "---"

FINAL_INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1)
if [ "$FINAL_INTEGRITY" != "ok" ]; then
    fail "Final integrity check failed: $FINAL_INTEGRITY"
fi
log "✓ Final integrity check: ok"

DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
log "✓ Database size: $DB_SIZE"

# === 03:15 — REPORT ===
log ""
log "STEP 8: DAILY REPORT"
log "---"

{
    echo "# V6 Daily Operations — $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo ""
    echo "**Run ID:** \`${TIMESTAMP}\`"
    echo ""
    echo "## Status"
    echo "✅ Daily operations completed successfully"
    echo ""
    echo "## Summary"
    echo "- Preflight checks: ✅ PASS"
    echo "- Source discovery: ✅ Manifest created"
    echo "- Backup: ✅ Created and verified"
    echo "- Ingestion: ℹ️  Placeholder (not automated)"
    echo "- Revocation sync: ℹ️  Placeholder (not automated)"
    echo "- Data quality: ℹ️  Placeholder (not automated)"
    echo "- Database integrity: ✅ PASS"
    echo ""
    echo "## Database"
    echo "- Path: \`$DB_PATH\`"
    echo "- Size: \`$DB_SIZE\`"
    echo "- Integrity: ✅ ok"
    echo ""
    echo "## Backup"
    echo "- Path: \`$BACKUP_FILE\`"
    echo "- Verified: ✅ yes"
    echo ""
    echo "## Log"
    echo "- Path: \`$LOG_FILE\`"
    echo ""
    echo "## Next Steps"
    echo "1. Implement ingestion logic in scripts/v6_daily_operations.sh"
    echo "2. Implement revocation sync"
    echo "3. Implement data quality checks"
    echo "4. Schedule via cron: 01:00 UTC daily"
    echo ""
} > "$REPORT_FILE"

log "✓ Report written: $REPORT_FILE"

# === CLEANUP ===
log ""
log "STEP 9: CLEANUP"
log "---"

# Prune old backups (keep 14 days)
find "$BACKUP_DIR" -name "*.db" -mtime +14 -delete
KEPT_BACKUPS=$(ls "$BACKUP_DIR"/*.db 2>/dev/null | wc -l)
log "✓ Pruned old backups. Retained: $KEPT_BACKUPS"

log ""
log "=========================================="
log "✅ DAILY OPERATIONS COMPLETED"
log "=========================================="
log "Duration: $(($(date +%s) - $(date -d @0 +%s))) seconds"
log "Log: $LOG_FILE"
log "Report: $REPORT_FILE"

exit 0
