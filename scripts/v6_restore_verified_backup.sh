#!/bin/bash
# v6_restore_verified_backup.sh
#
# Restore a verified backup of the v6 database.
#
# Usage:
#   v6_restore_verified_backup.sh <backup_file> [target_db]
#
# Example:
#   v6_restore_verified_backup.sh data/backups/v6/merit_registry_20260724T120000Z.db data/merit_registry.db

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DB="${2:-${REPO_ROOT}/data/merit_registry.db}"
BACKUP_FILE="${1:-}"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOG_DIR="${REPO_ROOT}/logs/v6"
REPORT_DIR="${REPO_ROOT}/reports/v6"

mkdir -p "$LOG_DIR" "$REPORT_DIR"

LOG_FILE="${LOG_DIR}/restore_${TIMESTAMP}.log"
REPORT_FILE="${REPORT_DIR}/restore_${TIMESTAMP}.md"

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG_FILE"
}

fail() {
    echo "❌ FAILED: $*" | tee -a "$LOG_FILE"
    exit 1
}

# === USAGE ===
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file> [target_db]"
    echo ""
    echo "Example:"
    echo "  $0 data/backups/v6/merit_registry_20260724T120000Z.db"
    echo "  $0 data/backups/v6/merit_registry_20260724T120000Z.db /tmp/test.db"
    echo ""
    echo "Available backups:"
    ls -lh "${REPO_ROOT}/data/backups/v6/"*.db 2>/dev/null || echo "  (none)"
    exit 1
fi

log "=========================================="
log "V6 DATABASE RESTORE"
log "=========================================="

# === VERIFY INPUTS ===
log ""
log "STEP 1: VERIFY INPUTS"
log "---"

if [ ! -f "$BACKUP_FILE" ]; then
    fail "Backup file not found: $BACKUP_FILE"
fi
log "✓ Backup file exists: $BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "  Size: $BACKUP_SIZE"

BACKUP_MTIME=$(stat -f%Sm -t "%Y-%m-%d %H:%M:%S UTC" "$BACKUP_FILE" 2>/dev/null || stat -c%y "$BACKUP_FILE" 2>/dev/null | cut -d' ' -f1-2)
log "  Modified: $BACKUP_MTIME"

# === VERIFY BACKUP INTEGRITY ===
log ""
log "STEP 2: VERIFY BACKUP INTEGRITY"
log "---"

INTEGRITY=$(sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" 2>&1)
if [ "$INTEGRITY" != "ok" ]; then
    fail "Backup integrity check failed: $INTEGRITY"
fi
log "✓ Backup integrity: ok"

# Verify schema
TABLES=$(sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>&1)
log "✓ Tables: $TABLES"

# Verify data
for table in registry_enriched v6_scoring_runs v6_peer_context_assignments; do
    COUNT=$(sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM $table;" 2>&1)
    log "  $table: $COUNT rows"
done

# === BACKUP CURRENT DB ===
log ""
log "STEP 3: BACKUP CURRENT DATABASE"
log "---"

if [ -f "$TARGET_DB" ]; then
    PRIOR_BACKUP="${TARGET_DB}.pre_restore_${TIMESTAMP}"
    cp "$TARGET_DB" "$PRIOR_BACKUP"
    log "✓ Current database backed up: $PRIOR_BACKUP"
else
    log "ℹ️  Target database does not exist (clean restore)"
fi

# === RESTORE ===
log ""
log "STEP 4: RESTORE FROM BACKUP"
log "---"

cp "$BACKUP_FILE" "$TARGET_DB"
log "✓ Backup restored to: $TARGET_DB"

# === VERIFY RESTORATION ===
log ""
log "STEP 5: VERIFY RESTORATION"
log "---"

RESTORED_INTEGRITY=$(sqlite3 "$TARGET_DB" "PRAGMA integrity_check;" 2>&1)
if [ "$RESTORED_INTEGRITY" != "ok" ]; then
    fail "Restored database integrity check failed: $RESTORED_INTEGRITY"
fi
log "✓ Restored database integrity: ok"

# Verify data
for table in registry_enriched v6_scoring_runs v6_peer_context_assignments; do
    COUNT=$(sqlite3 "$TARGET_DB" "SELECT COUNT(*) FROM $table;" 2>&1)
    log "  $table: $COUNT rows"
done

# === REPORT ===
log ""
log "STEP 6: WRITE REPORT"
log "---"

{
    echo "# V6 Database Restore"
    echo ""
    echo "**Timestamp:** $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo ""
    echo "## Summary"
    echo ""
    echo "✅ Database successfully restored from backup"
    echo ""
    echo "## Details"
    echo ""
    echo "- Source backup: \`$BACKUP_FILE\`"
    echo "- Target database: \`$TARGET_DB\`"
    echo "- Backup size: $BACKUP_SIZE"
    echo "- Backup modified: $BACKUP_MTIME"
    echo ""
    echo "## Verification"
    echo ""
    echo "- Backup integrity: ✅ ok"
    echo "- Restored integrity: ✅ ok"
    echo ""
    echo "## Data Status"
    echo ""
    for table in registry_enriched v6_scoring_runs v6_peer_context_assignments; do
        COUNT=$(sqlite3 "$TARGET_DB" "SELECT COUNT(*) FROM $table;" 2>&1)
        echo "- $table: $COUNT rows"
    done
    echo ""
    echo "## Prior Database"
    echo ""
    if [ -f "$PRIOR_BACKUP" ]; then
        echo "- Backed up to: \`$PRIOR_BACKUP\`"
        echo "- Review this backup before deleting"
    else
        echo "- (no prior database)"
    fi
    echo ""
    echo "## Next Steps"
    echo ""
    echo "1. Verify database queries work: \`sqlite3 $TARGET_DB 'SELECT COUNT(*) FROM registry_enriched;'\`"
    echo "2. Restart API server: \`./restart_api.sh\`"
    echo "3. Test affected endpoints"
    echo "4. Monitor error logs"
    echo ""
    echo "---"
    echo ""
    echo "Log: \`$LOG_FILE\`"
    echo ""
} > "$REPORT_FILE"

log "✓ Report written: $REPORT_FILE"

# === SUMMARY ===
log ""
log "=========================================="
log "✅ DATABASE RESTORE COMPLETED"
log "=========================================="
log "Target: $TARGET_DB"
log "Source: $BACKUP_FILE"
log "Report: $REPORT_FILE"
log "Log: $LOG_FILE"
log ""
log "✅ Next: Restart API and test endpoints"
log ""

exit 0
