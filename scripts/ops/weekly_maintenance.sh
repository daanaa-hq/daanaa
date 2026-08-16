#!/bin/bash
#
# Weekly maintenance: clean old logs + temp files
# Runs: Sunday 2am
# Backup: Sunday 11am-3pm (Digital Ocean automated)
#
# This script keeps the droplet lean:
# - Deletes logs older than 3 days
# - Deletes backup files older than 1 day (remote backup covers us)
# - Compresses old logs to save space
# - Logs all actions to maintenance.log
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MERITGIVING_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$MERITGIVING_DIR/data"
LOG_DIR="$MERITGIVING_DIR/logs"
MAINT_LOG="$LOG_DIR/maintenance.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Helper to log with timestamp
log_action() {
    local msg="$1"
    local ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] $msg" | tee -a "$MAINT_LOG"
}

# Get disk usage (before)
get_disk_usage() {
    du -sh "$DATA_DIR" 2>/dev/null | awk '{print $1}'
}

log_action "========== WEEKLY MAINTENANCE START =========="
DISK_BEFORE=$(get_disk_usage)
log_action "Disk usage before cleanup: $DISK_BEFORE"

# ── 1. Compress logs older than 2 days ────────────────────────────────────
log_action "Compressing logs older than 2 days..."
find "$LOG_DIR" -maxdepth 1 -name "*.log" -type f -mtime +2 ! -name "maintenance.log" -exec bash -c '
    file="$1"
    if [[ ! "$file" =~ .gz$ ]]; then
        gzip "$file" && echo "Compressed: $(basename "$file")" | tee -a "'$MAINT_LOG'"
    fi
' _ {} \;

# ── 2. Delete backup files older than 1 day ────────────────────────────────
# (Digital Ocean handles weekly snapshots, so we only need 1 day fallback)
log_action "Deleting backup files older than 1 day..."
find "$DATA_DIR" -maxdepth 1 -name "*.bak*" -type f -mtime +1 -exec bash -c '
    file="$1"
    rm -f "$file"
    echo "Deleted: $(basename "$file")" | tee -a "'$MAINT_LOG'"
' _ {} \;

# ── 3. Delete .gz archives (redundant, home server has originals) ───────────
log_action "Deleting .gz compressed archives (redundant)..."
find "$DATA_DIR" -maxdepth 1 -name "*.db.gz" -type f -exec bash -c '
    file="$1"
    rm -f "$file"
    echo "Deleted: $(basename "$file")" | tee -a "'$MAINT_LOG'"
' _ {} \;

# ── 4. Delete legacy/unused databases ──────────────────────────────────────
# Only if they exist and haven't been modified recently (safe to delete)
for legacy_db in "$DATA_DIR/meritgiving.db" "$DATA_DIR/merit_state.db"; do
    if [[ -f "$legacy_db" ]]; then
        # Check if modified in last 30 days (if not, it's stale)
        if ! find "$legacy_db" -type f -mtime -30 | grep -q .; then
            rm -f "$legacy_db"
            log_action "Deleted stale database: $(basename "$legacy_db")"
        fi
    fi
done

# ── 5. Verify database integrity ───────────────────────────────────────────
log_action "Verifying database integrity..."
LIVE_DB="$DATA_DIR/merit_registry.db"
if [[ -f "$LIVE_DB" ]]; then
    # Quick integrity check (PRAGMA quick_check is faster than full CHECK)
    if sqlite3 "$LIVE_DB" "PRAGMA quick_check;" | grep -q "ok"; then
        log_action "✅ Database integrity: PASS"
    else
        log_action "⚠️ Database integrity: FAILED — stopping cleanup to prevent data loss"
        log_action "========== WEEKLY MAINTENANCE FAILED =========="
        exit 1
    fi
else
    log_action "⚠️ Live database not found at $LIVE_DB"
    exit 1
fi

# ── 6. Report final state ──────────────────────────────────────────────────
DISK_AFTER=$(get_disk_usage)
log_action "Disk usage after cleanup: $DISK_AFTER"
log_action "========== WEEKLY MAINTENANCE COMPLETE =========="
log_action ""

# Optional: Alert if still above 75% (adjust 1000G to your disk size)
DISK_PERCENT=$(df "$DATA_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $DISK_PERCENT -gt 75 ]]; then
    log_action "⚠️ WARNING: Disk usage is $DISK_PERCENT% (above 75% threshold)"
fi

exit 0
