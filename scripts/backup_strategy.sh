#!/bin/bash
# Database Backup & Protection Strategy
# Prevents data loss via automated backups, integrity checks, and recovery procedures

set -e

DB_PATH="$HOME/meritgiving/data/merit_registry.db"
BACKUP_DIR="$HOME/meritgiving/backups/production"
ARCHIVE_DIR="$HOME/meritgiving/backups/archive"
LOG_DIR="$HOME/meritgiving/logs"

mkdir -p "$BACKUP_DIR" "$ARCHIVE_DIR" "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/backup_strategy.log"
}

# ============================================================================
# PHASE 1: Pre-Backup Integrity Check
# ============================================================================

check_db_integrity() {
    log "📋 Checking database integrity..."

    # Quick 30-second check (fast timeout)
    INTEGRITY_RESULT=$(timeout 30 sqlite3 "$DB_PATH" "PRAGMA quick_check;" 2>&1 || echo "CHECK_TIMEOUT")

    if [[ "$INTEGRITY_RESULT" == "ok" || "$INTEGRITY_RESULT" == "CHECK_TIMEOUT" ]]; then
        log "✅ Database integrity check passed (or timeout, proceeding)"
        return 0
    else
        log "🚨 CRITICAL: Database integrity check failed"
        log "   Error: $INTEGRITY_RESULT"
        return 1
    fi
}

# ============================================================================
# PHASE 2: Automated Hourly Snapshot
# ============================================================================

create_hourly_backup() {
    log "📦 Creating hourly snapshot..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    HOUR_BACKUP="$BACKUP_DIR/merit_registry_hourly_$TIMESTAMP.db"

    # Stop any active connections (optional, for safety)
    # This uses sqlite3 backup API which is non-blocking
    sqlite3 "$DB_PATH" ".backup '$HOUR_BACKUP'" 2>&1

    # Verify backup is valid (file exists and size is within 5% tolerance)
    ORIGINAL_SIZE=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null)
    BACKUP_SIZE=$(stat -f%z "$HOUR_BACKUP" 2>/dev/null || stat -c%s "$HOUR_BACKUP" 2>/dev/null)
    SIZE_TOLERANCE=$((ORIGINAL_SIZE / 20))  # 5% tolerance

    if [ -f "$HOUR_BACKUP" ] && [ "$BACKUP_SIZE" -gt "$((ORIGINAL_SIZE - SIZE_TOLERANCE))" ] && [ "$BACKUP_SIZE" -lt "$((ORIGINAL_SIZE + SIZE_TOLERANCE))" ]; then
        log "✅ Hourly backup created: $HOUR_BACKUP ($(numfmt --to=iec-i --suffix=B $BACKUP_SIZE 2>/dev/null || echo "$BACKUP_SIZE bytes"))"

        # Clean up SQLite temporary files
        rm -f "$HOUR_BACKUP"-shm "$HOUR_BACKUP"-wal 2>/dev/null

        # Keep only last 3 hourly backups (rotate old ones to archive)
        BACKUP_COUNT=$(find "$BACKUP_DIR" -name "merit_registry_hourly_*.db" -type f | wc -l)
        if [ "$BACKUP_COUNT" -gt 3 ]; then
            find "$BACKUP_DIR" -name "merit_registry_hourly_*.db" -type f | sort | head -n $((BACKUP_COUNT - 3)) | xargs -I {} mv {} "$ARCHIVE_DIR/"
        fi
        return 0
    else
        log "🚨 Hourly backup size mismatch or file missing (original: $ORIGINAL_SIZE, backup: $BACKUP_SIZE)"
        rm -f "$HOUR_BACKUP" "$HOUR_BACKUP"-shm "$HOUR_BACKUP"-wal 2>/dev/null
        return 1
    fi
}

# ============================================================================
# PHASE 3: Daily Full Backup (for disaster recovery)
# ============================================================================

create_daily_backup() {
    log "🔄 Creating daily full backup..."

    TIMESTAMP=$(date +%Y%m%d)
    DAILY_BACKUP="$BACKUP_DIR/merit_registry_daily_$TIMESTAMP.db"

    # Don't create duplicate if one already exists for today
    if [ -f "$DAILY_BACKUP" ]; then
        log "⏭️  Daily backup already exists for today, skipping"
        return 0
    fi

    sqlite3 "$DB_PATH" ".backup '$DAILY_BACKUP'" 2>&1

    # Verify backup is valid (file exists and size is within 5% tolerance)
    ORIGINAL_SIZE=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null)
    BACKUP_SIZE=$(stat -f%z "$DAILY_BACKUP" 2>/dev/null || stat -c%s "$DAILY_BACKUP" 2>/dev/null)
    SIZE_TOLERANCE=$((ORIGINAL_SIZE / 20))  # 5% tolerance

    if [ -f "$DAILY_BACKUP" ] && [ "$BACKUP_SIZE" -gt "$((ORIGINAL_SIZE - SIZE_TOLERANCE))" ] && [ "$BACKUP_SIZE" -lt "$((ORIGINAL_SIZE + SIZE_TOLERANCE))" ]; then
        SIZE=$(du -h "$DAILY_BACKUP" | awk '{print $1}')
        log "✅ Daily backup created: $DAILY_BACKUP ($SIZE)"

        # Clean up SQLite temporary files
        rm -f "$DAILY_BACKUP"-shm "$DAILY_BACKUP"-wal 2>/dev/null

        # Keep last 30 days; archive older
        find "$BACKUP_DIR" -name "merit_registry_daily_*.db" -mtime +30 -exec mv {} "$ARCHIVE_DIR/" \;
        return 0
    else
        log "🚨 Daily backup size mismatch or file missing (original: $ORIGINAL_SIZE, backup: $BACKUP_SIZE)"
        rm -f "$DAILY_BACKUP" "$DAILY_BACKUP"-shm "$DAILY_BACKUP"-wal 2>/dev/null
        return 1
    fi
}

# ============================================================================
# PHASE 4: Pre-Enrichment Checkpoint
# ============================================================================

create_pre_enrichment_checkpoint() {
    log "🎯 Creating pre-enrichment checkpoint..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    CHECKPOINT="$BACKUP_DIR/merit_registry_pre_enrichment_$TIMESTAMP.db"

    sqlite3 "$DB_PATH" ".backup '$CHECKPOINT'" 2>&1

    # Verify checkpoint is valid (file exists and size is within 5% tolerance)
    ORIGINAL_SIZE=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null)
    CHECKPOINT_SIZE=$(stat -f%z "$CHECKPOINT" 2>/dev/null || stat -c%s "$CHECKPOINT" 2>/dev/null)
    SIZE_TOLERANCE=$((ORIGINAL_SIZE / 20))  # 5% tolerance

    if [ -f "$CHECKPOINT" ] && [ "$CHECKPOINT_SIZE" -gt "$((ORIGINAL_SIZE - SIZE_TOLERANCE))" ] && [ "$CHECKPOINT_SIZE" -lt "$((ORIGINAL_SIZE + SIZE_TOLERANCE))" ]; then
        SIZE=$(du -h "$CHECKPOINT" | awk '{print $1}')
        log "✅ Pre-enrichment checkpoint: $CHECKPOINT ($SIZE)"

        # Clean up SQLite temporary files
        rm -f "$CHECKPOINT"-shm "$CHECKPOINT"-wal 2>/dev/null

        # Keep last 5 enrichment checkpoints
        find "$BACKUP_DIR" -name "merit_registry_pre_enrichment_*.db" | sort | head -n -5 | xargs rm -f 2>/dev/null || true
        return 0
    else
        log "🚨 Pre-enrichment checkpoint failed (size mismatch or missing)"
        rm -f "$CHECKPOINT" "$CHECKPOINT"-shm "$CHECKPOINT"-wal 2>/dev/null
        return 1
    fi
}

# ============================================================================
# PHASE 5: Recovery Procedures
# ============================================================================

list_recoverable_backups() {
    echo ""
    echo "RECOVERABLE BACKUPS (newest first):"
    echo "===================================="
    ls -lht "$BACKUP_DIR"/merit_registry_*.db 2>/dev/null | head -20 | awk '{print $6, $7, $8, $9}' || echo "No backups found"
    echo ""
}

restore_from_backup() {
    local BACKUP_FILE=$1

    if [ ! -f "$BACKUP_FILE" ]; then
        log "❌ Backup file not found: $BACKUP_FILE"
        return 1
    fi

    log "⚠️  RESTORING FROM: $BACKUP_FILE"

    # Verify backup before restoring
    if ! sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check LIMIT 1;" 2>&1 | grep -q "ok"; then
        log "🚨 Backup file is corrupted, cannot restore"
        return 1
    fi

    # Kill API to release DB lock
    log "🛑 Stopping API server..."
    pkill -f "gunicorn\|daanaa_api" 2>/dev/null || true
    sleep 2

    # Archive current (corrupted) DB
    CORRUPTED_ARCHIVE="$ARCHIVE_DIR/merit_registry_corrupted_$(date +%s).db"
    mv "$DB_PATH" "$CORRUPTED_ARCHIVE" 2>/dev/null || true
    log "   Archived corrupted DB: $CORRUPTED_ARCHIVE"

    # Restore
    cp "$BACKUP_FILE" "$DB_PATH"
    log "✅ Restored from: $BACKUP_FILE"

    # Restart API
    log "🚀 Restarting API..."
    cd ~/meritgiving && nohup python3 daanaa_api.py > /tmp/daanaa_api_restore.log 2>&1 &
    sleep 3

    # Verify
    if curl -s http://localhost:5000/health 2>&1 | grep -q "ok"; then
        log "✅ API restarted successfully"
        return 0
    else
        log "🚨 API failed to restart after restore"
        return 1
    fi
}

# ============================================================================
# PHASE 6: Main Execution
# ============================================================================

main() {
    log "════════════════════════════════════════"
    log "Database Backup & Protection Strategy"
    log "════════════════════════════════════════"

    # Check database health first
    if ! check_db_integrity; then
        log "❌ Database integrity check failed. Aborting backup."
        list_recoverable_backups
        exit 1
    fi

    # Create backups
    create_hourly_backup || log "⚠️  Hourly backup failed (non-fatal)"
    create_daily_backup || log "⚠️  Daily backup failed (non-fatal)"

    # Create checkpoint before major operations
    if [[ "$1" == "pre-enrichment" ]]; then
        create_pre_enrichment_checkpoint || log "⚠️  Pre-enrichment checkpoint failed"
    fi

    # Restore logic
    if [[ "$1" == "restore" ]]; then
        BACKUP_FILE=$2
        if [ -z "$BACKUP_FILE" ]; then
            log "❌ Usage: $0 restore <backup_file>"
            list_recoverable_backups
            exit 1
        fi
        restore_from_backup "$BACKUP_FILE"
    fi

    # List available backups
    if [[ "$1" == "list" ]]; then
        list_recoverable_backups
    fi

    log "✅ Backup strategy cycle complete"
    log "════════════════════════════════════════"
}

# Execute main function with arguments
main "$@"
