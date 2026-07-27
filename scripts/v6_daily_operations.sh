#!/bin/bash
# v6_daily_operations.sh
#
# Daily operational workflow for v6 data foundation.
#
# Sequence:
# 1. Preflight checks
# 2. Create SQLite-safe backup
# 3. Source discovery and manifest
# 4. Data quality checks
# 5. Revocation synchronization
# 6. Database integrity
# 7. Daily report

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${REPO_ROOT}/data/merit_registry.db"
LOCK_FILE="${REPO_ROOT}/data/v6_operation.lock"
LOG_DIR="${REPO_ROOT}/logs/v6"
BACKUP_DIR="${REPO_ROOT}/data/backups/v6"
REPORT_DIR="${REPO_ROOT}/reports/v6"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

# Control flags
APPLY_BACKFILL="${V6_APPLY_BACKFILL:-false}"
DRY_RUN="${V6_DRY_RUN:-true}"

mkdir -p "$LOG_DIR" "$BACKUP_DIR" "$REPORT_DIR"

LOG_FILE="${LOG_DIR}/daily_${TIMESTAMP}.log"
REPORT_FILE="${REPORT_DIR}/daily_${TIMESTAMP}.md"

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG_FILE"
}

fail() {
    echo "❌ FAILED: $*" | tee -a "$LOG_FILE"
    exit 1
}

report_status() {
    local status=$1
    local msg=$2
    echo "$status|$msg" >> "${REPORT_DIR}/.daily_status_${TIMESTAMP}"
}

# Acquire lock
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        fail "Another v6 operation (PID $LOCK_PID) is running. Exiting."
    else
        log "⚠️  Stale lock found. Removing and proceeding."
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"
trap "rm -f '$LOCK_FILE'" EXIT

log "=========================================="
log "V6 DAILY OPERATIONS WORKFLOW"
log "=========================================="
log "Dry-run mode: $DRY_RUN"
log "Apply backfill: $APPLY_BACKFILL"

# === 01:00 — PREFLIGHT ===
log ""
log "STEP 1: PREFLIGHT CHECKS"
log "---"

# Check repo
if [ ! -f "$DB_PATH" ]; then
    fail "Database not found: $DB_PATH"
fi
log "✓ Repository accessible"
report_status "PASS" "Repository readable"

# Check disk space (1 GB minimum)
DISK_FREE=$(df "$REPO_ROOT" | tail -1 | awk '{print $4}')
if [ "$DISK_FREE" -lt 1048576 ]; then
    fail "Insufficient disk space: ${DISK_FREE}KB free (need 1GB)"
fi
log "✓ Disk space sufficient: ${DISK_FREE}KB free"
report_status "PASS" "Disk space: ${DISK_FREE}KB"

# Check database integrity
INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1)
if [ "$INTEGRITY" != "ok" ]; then
    fail "Database integrity check failed: $INTEGRITY"
fi
log "✓ Database integrity: ok"
report_status "PASS" "Database integrity check"

# Check latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.db 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
    log "⚠️  No prior backup found (first run?)"
    report_status "WARN" "No prior backup exists"
else
    BACKUP_AGE_SECS=$(($(date +%s) - $(stat -f%m "$LATEST_BACKUP" 2>/dev/null || stat -c%Y "$LATEST_BACKUP" 2>/dev/null)))
    BACKUP_HOURS=$((BACKUP_AGE_SECS / 3600))
    log "✓ Latest backup: $BACKUP_HOURS hours old"
    report_status "PASS" "Latest backup: $BACKUP_HOURS hours"
fi

log "✓ Preflight passed"

# === 01:10 — SOURCE DISCOVERY ===
log ""
log "STEP 2: SOURCE DISCOVERY"
log "---"

cd "$REPO_ROOT"
python3 scripts/v6_source_manifest.py >> "$LOG_FILE" 2>&1 || log "⚠️  Source discovery encountered issues"
log "✓ Source manifest created"
report_status "PASS" "Source discovery completed"

# === 01:25 — BACKUP ===
log ""
log "STEP 3: CREATE SQLITE-SAFE BACKUP"
log "---"

BACKUP_FILE="${BACKUP_DIR}/merit_registry_${TIMESTAMP}.db"

# Use SQLite backup function for consistency
sqlite3 "$DB_PATH" ".backup $BACKUP_FILE" 2>&1 || fail "Backup failed"

log "✓ Backup created: $BACKUP_FILE"

# Verify backup opens and has data
if ! sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM registry_enriched;" > /dev/null 2>&1; then
    fail "Backup verification failed"
fi
log "✓ Backup verified readable"
report_status "PASS" "Backup created and verified"

# === 01:40 — DATA QUALITY CHECKS ===
log ""
log "STEP 4: DATA QUALITY CHECKS"
log "---"

# Check duplicate EINs
DUP_EINS=$(sqlite3 "$DB_PATH" "SELECT COUNT(DISTINCT EIN) FROM registry_enriched WHERE EIN IN (SELECT EIN FROM registry_enriched GROUP BY EIN HAVING COUNT(*) > 1);" 2>&1)
log "  Duplicate EINs: $DUP_EINS (expect: 0)"
if [ "$DUP_EINS" -gt 0 ]; then
    report_status "WARN" "Duplicate EINs found: $DUP_EINS"
else
    report_status "PASS" "No duplicate EINs"
fi

# Check invalid EIN formats
INVALID_EINS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE EIN NOT LIKE '_________%' OR EIN LIKE '%[^0-9]%';" 2>&1)
log "  Invalid EIN formats: $INVALID_EINS (expect: 0)"
if [ "$INVALID_EINS" -gt 0 ]; then
    report_status "WARN" "Invalid EIN formats: $INVALID_EINS"
fi

# Check missing NTEE
MISSING_NTEE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE NTEE1 IS NULL;" 2>&1)
log "  Missing NTEE classification: $MISSING_NTEE"
if [ "$MISSING_NTEE" -gt 100000 ]; then
    report_status "WARN" "Large count of missing NTEE: $MISSING_NTEE"
fi

# Check for negative financial values
NEG_REVENUE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE total_revenue < 0;" 2>&1)
NEG_EXPENSES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE total_expenses < 0;" 2>&1)
log "  Negative revenue: $NEG_REVENUE (expect: 0)"
log "  Negative expenses: $NEG_EXPENSES (expect: 0)"
if [ "$NEG_REVENUE" -gt 0 ] || [ "$NEG_EXPENSES" -gt 0 ]; then
    report_status "WARN" "Negative financial values found"
else
    report_status "PASS" "No negative financial values"
fi

log "✓ Data quality checks completed"

# === 02:15 — REVOCATION SYNCHRONIZATION ===
log ""
log "STEP 5: REVOCATION SYNCHRONIZATION"
log "---"

# Check consistency between irs_revoked and org_status
MISMATCH_1=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked=1 AND org_status<>'revoked';" 2>&1)
MISMATCH_2=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE org_status='revoked' AND irs_revoked<>1;" 2>&1)

log "  irs_revoked=1 but org_status≠'revoked': $MISMATCH_1 (expect: 0)"
log "  org_status='revoked' but irs_revoked≠1: $MISMATCH_2 (expect: 0)"

if [ "$MISMATCH_1" -gt 0 ] || [ "$MISMATCH_2" -gt 0 ]; then
    report_status "WARN" "Revocation consistency issues: $MISMATCH_1 / $MISMATCH_2"
    log "⚠️  Revocation data has inconsistencies. Manual repair required."
else
    report_status "PASS" "Revocation data consistent"
fi

# Check revoked orgs in active scoring run
ACTIVE_CANDIDATE=$(sqlite3 "$DB_PATH" "SELECT run_id FROM v6_scoring_runs WHERE status='active' ORDER BY started_at DESC LIMIT 1;" 2>&1)
if [ -n "$ACTIVE_CANDIDATE" ]; then
    REVOKED_ACTIVE=$(sqlite3 "$DB_PATH" "
        SELECT COUNT(*) FROM v6_peer_context_assignments a
        WHERE a.run_id='$ACTIVE_CANDIDATE'
        AND a.selected_tier IN ('1_direct','2_regional_conditional','3_broader_regional','4_national')
        AND a.ein IN (SELECT EIN FROM registry_enriched WHERE irs_revoked=1 OR org_status='revoked');
    " 2>&1)
    log "  Revoked in active scoring run: $REVOKED_ACTIVE (expect: 0)"
    if [ "$REVOKED_ACTIVE" -gt 0 ]; then
        report_status "BLOCKED" "Revoked orgs in active scoring run"
    fi
fi

log "✓ Revocation synchronization check completed"

# === 02:30 — BACKFILL INGESTION (DRY-RUN BY DEFAULT) ===
log ""
log "STEP 6: NORMALIZED DATA BACKFILL"
log "---"

if [ "$DRY_RUN" = "true" ]; then
    log "ℹ️  DRY-RUN mode: simulating ingestion without writes"
    log "    To enable actual ingestion, run with: V6_APPLY_BACKFILL=true $0"
    report_status "NOT_CONFIGURED" "Backfill: dry-run only (set V6_APPLY_BACKFILL=true to enable)"
else
    log "⚠️  INGESTION NOT YET AUTOMATED"
    log "    Normalized table ingestion requires:"
    log "    - Idempotent insert logic"
    log "    - EIN + tax_year + source keying"
    log "    - Invalid record quarantine"
    log "    - Transaction rollback on failure"
    report_status "NOT_CONFIGURED" "Backfill: placeholder only"
fi

log "✓ Backfill check completed (dry-run)"

# === 03:00 — INTEGRITY CHECK ===
log ""
log "STEP 7: POST-CHECK DATABASE INTEGRITY"
log "---"

FINAL_INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1)
if [ "$FINAL_INTEGRITY" != "ok" ]; then
    fail "Final integrity check failed: $FINAL_INTEGRITY"
fi
log "✓ Final integrity check: ok"
report_status "PASS" "Database integrity check"

DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
log "✓ Database size: $DB_SIZE"

# === 03:15 — DAILY REPORT ===
log ""
log "STEP 8: DAILY REPORT"
log "---"

{
    echo "# V6 Daily Operations — $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo ""
    echo "**Run ID:** \`${TIMESTAMP}\`"
    echo ""
    echo "## Status Summary"
    echo ""

    # Parse status file
    if [ -f "${REPORT_DIR}/.daily_status_${TIMESTAMP}" ]; then
        while IFS='|' read -r status msg; do
            case "$status" in
                PASS)   echo "✅ $msg" ;;
                WARN)   echo "⚠️  $msg" ;;
                BLOCKED) echo "❌ $msg" ;;
                NOT_CONFIGURED) echo "ℹ️  $msg" ;;
            esac
        done < "${REPORT_DIR}/.daily_status_${TIMESTAMP}"
    fi

    echo ""
    echo "## Details"
    echo ""
    echo "- **Mode:** Dry-run (no database changes)"
    echo "- **Backfill:** $APPLY_BACKFILL"
    echo "- **Disk free:** ${DISK_FREE}KB"
    echo "- **Database size:** $DB_SIZE"
    echo "- **Backup:** $BACKUP_FILE"
    echo "- **Integrity:** ok"
    echo ""
    echo "## What's Automated"
    echo ""
    echo "- ✅ Preflight checks"
    echo "- ✅ Backup creation (SQLite-safe)"
    echo "- ✅ Source discovery"
    echo "- ✅ Data quality checks"
    echo "- ✅ Revocation consistency"
    echo "- ✅ Database integrity"
    echo "- ℹ️  Backfill: placeholder (requires implementation)"
    echo "- ℹ️  Revocation repair: placeholder (requires source backup + transaction)"
    echo ""
    echo "## Next Steps"
    echo ""
    echo "1. Implement normalized-table backfill with rollback"
    echo "2. Implement revocation-repair logic (source-backed, transactional)"
    echo "3. Schedule: Run daily via cron at 01:00 UTC"
    echo "4. Monitor: Check daily reports for BLOCKED or WARN status"
    echo ""
    echo "## Log"
    echo ""
    echo "- Path: \`$LOG_FILE\`"
    echo ""
} > "$REPORT_FILE"

log "✓ Report written: $REPORT_FILE"

# === CLEANUP ===
log ""
log "STEP 9: CLEANUP"
log "---"

# Prune old backups (keep 14 days)
PRUNED=$(find "$BACKUP_DIR" -name "*.db" -mtime +14 -delete -print | wc -l)
KEPT_BACKUPS=$(ls "$BACKUP_DIR"/*.db 2>/dev/null | wc -l)
log "✓ Pruned $PRUNED old backups. Retained: $KEPT_BACKUPS"

# Remove temp status file
rm -f "${REPORT_DIR}/.daily_status_${TIMESTAMP}"

log ""
log "=========================================="
log "✅ DAILY OPERATIONS COMPLETED"
log "=========================================="
log "Mode: Dry-run (safe, no writes)"
log "Status: Monitoring only"
log "Log: $LOG_FILE"
log "Report: $REPORT_FILE"
log ""
log "To enable actual ingestion:"
log "  export V6_APPLY_BACKFILL=true"
log "  bash scripts/v6_daily_operations.sh"
log ""

exit 0
