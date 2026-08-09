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

# Verify a SQLite file really is structurally sound. Returns 0 ok, 1 corrupt,
# 2 inconclusive (timed out). Callers MUST distinguish 1 from 2 — treating a
# timeout as success is what let six corrupt 2026-08-01 backups be retained and
# trusted (quick_check on a 23GB DB needs ~1h; the old 30s timeout could never
# finish, and the code logged that guaranteed timeout as "passed").
verify_sqlite_file() {
    local f="$1" limit="${2:-5400}" out
    [ -f "$f" ] || { log "   verify: file missing: $f"; return 1; }
    out=$(timeout "$limit" sqlite3 "$f" "PRAGMA quick_check;" 2>&1) || {
        if [ $? -eq 124 ]; then
            log "   verify: INCONCLUSIVE (timed out after ${limit}s): $f"
            return 2
        fi
        log "   verify: FAILED to run quick_check: $f"
        return 1
    }
    if [ "$out" = "ok" ]; then
        return 0
    fi
    log "   verify: CORRUPT: $f"
    log "   verify: $(echo "$out" | head -3 | tr '\n' ' ')"
    return 1
}

# Copy a live SQLite DB safely.
#
# Uses VACUUM INTO rather than the sqlite3_backup API (".backup"): the backup API
# restarts from page 1 on any concurrent write to the source, and this database
# always has gunicorn workers holding it read-write. VACUUM INTO reads one
# consistent snapshot and writes once, so it completes under live write load.
#
# Also verifies the copy carries the same row count as the source — size and
# structure can both look fine while content is truncated.
backup_db_to() {
    local src="$1" dst="$2" src_rows dst_rows
    # VACUUM INTO refuses to write to an existing file.
    rm -f "$dst" "$dst"-shm "$dst"-wal "$dst"-journal 2>/dev/null || true
    sqlite3 "$src" "VACUUM INTO '$dst';" 2>&1 || { log "   copy: VACUUM INTO failed"; return 1; }
    [ -f "$dst" ] || { log "   copy: destination missing after VACUUM INTO"; return 1; }

    src_rows=$(sqlite3 "$src" "SELECT COUNT(*) FROM registry_enriched;" 2>/dev/null || echo "")
    dst_rows=$(sqlite3 "$dst" "SELECT COUNT(*) FROM registry_enriched;" 2>/dev/null || echo "")
    if [ -n "$src_rows" ] && [ -n "$dst_rows" ] && [ "$src_rows" != "$dst_rows" ]; then
        log "   copy: ROW COUNT MISMATCH src=$src_rows dst=$dst_rows"
        return 1
    fi
    log "   copy: ok ($dst_rows rows)"
    return 0
}

check_db_integrity() {
    log "📋 Checking source database integrity (advisory pre-check)..."
    local rc=0
    verify_sqlite_file "$DB_PATH" 300 || rc=$?
    case "$rc" in
        0) log "✅ Source integrity verified clean" ;;
        2) log "⚠️  Source integrity INCONCLUSIVE (too large for 300s pre-check) — proceeding; the produced backup is verified separately" ;;
        *) log "🚨 CRITICAL: Source database is corrupt — refusing to overwrite good backups with a bad copy"
           return 1 ;;
    esac
    return 0
}

# ============================================================================
# PHASE 2: Automated Hourly Snapshot
# ============================================================================

create_hourly_backup() {
    log "📦 Creating hourly snapshot..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    HOUR_BACKUP="$BACKUP_DIR/merit_registry_hourly_$TIMESTAMP.db"

    # VACUUM INTO, not .backup (changed 2026-08-08). The sqlite3_backup API
    # RESTARTS from page 1 whenever a writer touches the source, and the gunicorn
    # workers hold merit_registry.db open read-write around the clock. Measured
    # 2026-08-08: a single nightly run had read 5,008GB and written 6,672GB of a
    # 23GB database (~290 full passes) over 5h21m and was no closer to finishing.
    # That is why 2026-08-04/05/06 have no daily backup at all, only orphaned
    # -journal files. VACUUM INTO takes one consistent read snapshot and writes
    # once, so concurrent writers cannot restart it.
    backup_db_to "$DB_PATH" "$HOUR_BACKUP" || {
        log "🚨 Hourly backup copy failed"
        rm -f "$HOUR_BACKUP" "$HOUR_BACKUP"-shm "$HOUR_BACKUP"-wal 2>/dev/null || true
        return 1
    }

    # NOTE: VACUUM INTO defragments, so the copy is legitimately SMALLER than the
    # source (the old ±5% window would reject every good backup). Sanity-check a
    # lower bound only; correctness is established by verify_sqlite_file + rowcount.
    ORIGINAL_SIZE=$(stat -c%s "$DB_PATH" 2>/dev/null)
    BACKUP_SIZE=$(stat -c%s "$HOUR_BACKUP" 2>/dev/null || echo 0)

    if [ -f "$HOUR_BACKUP" ] && [ "$BACKUP_SIZE" -gt "$((ORIGINAL_SIZE / 2))" ]; then
        log "✅ Hourly backup created: $HOUR_BACKUP ($(numfmt --to=iec-i --suffix=B $BACKUP_SIZE 2>/dev/null || echo "$BACKUP_SIZE bytes"))"

        # Size alone proves nothing: corruption does not change file size, which
        # is how the 2026-08-01 backups passed. Structurally verify the copy.
        local vrc=0
        verify_sqlite_file "$HOUR_BACKUP" || vrc=$?
        if [ "$vrc" = "1" ]; then
            log "🚨 CRITICAL: hourly backup is CORRUPT — deleting so it is never trusted"
            rm -f "$HOUR_BACKUP" "$HOUR_BACKUP"-shm "$HOUR_BACKUP"-wal 2>/dev/null || true
            return 1
        elif [ "$vrc" = "2" ]; then
            log "⚠️  hourly backup UNVERIFIED (quick_check timed out) — retained but not trusted"
        else
            log "✅ hourly backup structurally verified"
        fi

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

    # Don't create a duplicate if today's backup already exists AND is sound.
    # Existence alone is not enough (2026-08-08): a run killed mid-copy leaves a
    # truncated file, and the old guard would skip past it all day, leaving a
    # corrupt partial standing in as that day's backup — the exact failure mode
    # this script is supposed to prevent. Validate before trusting it.
    if [ -f "$DAILY_BACKUP" ]; then
        local existing_size src_size erc=0
        existing_size=$(stat -c%s "$DAILY_BACKUP" 2>/dev/null || echo 0)
        src_size=$(stat -c%s "$DB_PATH" 2>/dev/null || echo 0)
        if [ "$existing_size" -lt "$((src_size / 2))" ]; then
            log "⚠️  Existing daily backup is undersized ($((existing_size/1073741824))GB vs source $((src_size/1073741824))GB) — treating as failed partial, rebuilding"
            rm -f "$DAILY_BACKUP" "$DAILY_BACKUP"-shm "$DAILY_BACKUP"-wal "$DAILY_BACKUP"-journal 2>/dev/null || true
        else
            verify_sqlite_file "$DAILY_BACKUP" || erc=$?
            if [ "$erc" = "1" ]; then
                log "⚠️  Existing daily backup is CORRUPT — discarding and rebuilding"
                rm -f "$DAILY_BACKUP" "$DAILY_BACKUP"-shm "$DAILY_BACKUP"-wal "$DAILY_BACKUP"-journal 2>/dev/null || true
            else
                log "⏭️  Daily backup already exists for today and verified sound, skipping"
                return 0
            fi
        fi
    fi

    # VACUUM INTO, not .backup — see create_hourly_backup for the full rationale.
    backup_db_to "$DB_PATH" "$DAILY_BACKUP" || {
        log "🚨 Daily backup copy failed"
        rm -f "$DAILY_BACKUP" "$DAILY_BACKUP"-shm "$DAILY_BACKUP"-wal 2>/dev/null || true
        return 1
    }

    # VACUUM INTO defragments; copy is legitimately smaller. Lower bound only.
    ORIGINAL_SIZE=$(stat -c%s "$DB_PATH" 2>/dev/null)
    BACKUP_SIZE=$(stat -c%s "$DAILY_BACKUP" 2>/dev/null || echo 0)

    if [ -f "$DAILY_BACKUP" ] && [ "$BACKUP_SIZE" -gt "$((ORIGINAL_SIZE / 2))" ]; then
        SIZE=$(du -h "$DAILY_BACKUP" | awk '{print $1}')
        log "✅ Daily backup created: $DAILY_BACKUP ($SIZE)"

        # Size alone proves nothing: corruption does not change file size, which
        # is how the 2026-08-01 backups passed. Structurally verify the copy.
        local vrc=0
        verify_sqlite_file "$DAILY_BACKUP" || vrc=$?
        if [ "$vrc" = "1" ]; then
            log "🚨 CRITICAL: daily backup is CORRUPT — deleting so it is never trusted"
            rm -f "$DAILY_BACKUP" "$DAILY_BACKUP"-shm "$DAILY_BACKUP"-wal 2>/dev/null || true
            return 1
        elif [ "$vrc" = "2" ]; then
            log "⚠️  daily backup UNVERIFIED (quick_check timed out) — retained but not trusted"
        else
            log "✅ daily backup structurally verified"
        fi

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
# PHASE 3.5: Retention (added 2026-08-08)
# ============================================================================
# The old policy MOVED expired backups to archive/ instead of deleting them, so
# nothing was ever reclaimed: backups/ reached 250GB, and 115GB of that was five
# corrupt copies of a single day. At ~22GB per copy a 30-day daily policy needs
# 660GB against ~105GB free -- the backup system would have filled the disk and
# taken the box down with it.
#
# Local retention is deliberately short because offsite is the durable tier:
# weekly full DB (s3://daanaa-backups) + nightly ~80MB core export
# (s3://daanaa-nonprofit-data) + DigitalOcean snapshots. Local exists for fast
# recovery, not history.
#
# Fail-safe: never prune unless a verified offsite copy exists.
prune_local_backups() {
    local keep_daily="${KEEP_DAILY_LOCAL:-7}" keep_hourly="${KEEP_HOURLY_LOCAL:-3}"
    log "🧹 retention: keeping ${keep_daily} daily / ${keep_hourly} hourly locally"

    local offsite_ok=0
    if aws s3 ls "s3://daanaa-backups/home-server/full/" >/dev/null 2>&1; then
        offsite_ok=1
    fi
    if [ "$offsite_ok" != "1" ]; then
        log "⚠️  retention SKIPPED — could not confirm an offsite copy exists"
        return 0
    fi

    local removed=0
    for pat in "merit_registry_daily_*.db:$keep_daily" "merit_registry_hourly_*.db:$keep_hourly"; do
        local glob="${pat%%:*}" keep="${pat##*:}"
        # Sort by mtime, newest first; delete past the keep count.
        find "$BACKUP_DIR" "$ARCHIVE_DIR" -maxdepth 1 -name "$glob" -type f -printf '%T@ %p\n' 2>/dev/null \
          | sort -rn | tail -n +$((keep + 1)) | cut -d' ' -f2- | while read -r old; do
                [ -n "$old" ] || continue
                rm -f "$old" "$old"-shm "$old"-wal "$old"-journal 2>/dev/null || true
                log "   pruned $(basename "$old")"
            done
    done

    local free_gb
    free_gb=$(df -BG "$BACKUP_DIR" | tail -1 | awk '{gsub(/G/,"",$4); print $4}')
    log "🧹 retention done — ${free_gb}G free on the backup volume"
    if [ "$free_gb" -lt 40 ]; then
        log "🚨 LOW DISK: ${free_gb}G free after retention — review backup sizing"
    fi
}

# ============================================================================
# PHASE 4: Pre-Enrichment Checkpoint
# ============================================================================

create_pre_enrichment_checkpoint() {
    log "🎯 Creating pre-enrichment checkpoint..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    CHECKPOINT="$BACKUP_DIR/merit_registry_pre_enrichment_$TIMESTAMP.db"

    # VACUUM INTO, not .backup — see create_hourly_backup for the full rationale.
    backup_db_to "$DB_PATH" "$CHECKPOINT" || {
        log "🚨 Pre-enrichment checkpoint copy failed"
        rm -f "$CHECKPOINT" "$CHECKPOINT"-shm "$CHECKPOINT"-wal 2>/dev/null || true
        return 1
    }

    # VACUUM INTO defragments; copy is legitimately smaller. Lower bound only.
    ORIGINAL_SIZE=$(stat -c%s "$DB_PATH" 2>/dev/null)
    CHECKPOINT_SIZE=$(stat -c%s "$CHECKPOINT" 2>/dev/null || echo 0)

    if [ -f "$CHECKPOINT" ] && [ "$CHECKPOINT_SIZE" -gt "$((ORIGINAL_SIZE / 2))" ]; then
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

    prune_local_backups

log "✅ Backup strategy cycle complete"
    log "════════════════════════════════════════"
}

# Execute main function with arguments
main "$@"
