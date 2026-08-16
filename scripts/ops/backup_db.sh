#!/usr/bin/env bash
# Online SQLite backup for merit_registry.db.
# Safe to run while gunicorn is live — uses SQLite's .backup command which
# snapshots a consistent state without locking out writers.
#
# Usage: ./scripts/backup_db.sh
# Cron: 0 3 * * * /home/akbar/meritgiving/scripts/backup_db.sh >> /home/akbar/meritgiving/logs/backup.log 2>&1
#
# Required env vars (can be set here or in calling env):
#   BACKUP_DEST  — rsync destination, e.g. user@remote:/backups/daanaa/ or /mnt/nas/daanaa/
#                  Leave unset to skip remote sync (local backup only).
# Optional:
#   DB_PATH           — defaults to /home/akbar/meritgiving/data/merit_registry.db
#   LOCAL_BACKUP_DIR  — defaults to /home/akbar/meritgiving/backups
#   BACKUP_RETAIN_DAYS — how many days of local backups to keep (default: 7)

set -euo pipefail

DB_PATH="${DB_PATH:-/home/akbar/meritgiving/data/merit_registry.db}"
LOCAL_BACKUP_DIR="${LOCAL_BACKUP_DIR:-/home/akbar/meritgiving/backups}"
BACKUP_RETAIN_DAYS="${BACKUP_RETAIN_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$LOCAL_BACKUP_DIR/merit_registry_${TIMESTAMP}.db"
COMPRESSED="$BACKUP_FILE.gz"

mkdir -p "$LOCAL_BACKUP_DIR"

echo "[$(date -u +%FT%TZ)] Starting backup of $DB_PATH"

if [ ! -f "$DB_PATH" ]; then
    echo "[$(date -u +%FT%TZ)] ERROR: database not found at $DB_PATH" >&2
    exit 1
fi

# Online backup — consistent snapshot even under concurrent writes
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
echo "[$(date -u +%FT%TZ)] SQLite backup written: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

gzip -9 "$BACKUP_FILE"
echo "[$(date -u +%FT%TZ)] Compressed: $COMPRESSED ($(du -sh "$COMPRESSED" | cut -f1))"

# Offsite sync (skipped if BACKUP_DEST is unset)
if [ -n "${BACKUP_DEST:-}" ]; then
    rsync -az --progress "$COMPRESSED" "$BACKUP_DEST"
    echo "[$(date -u +%FT%TZ)] Synced to $BACKUP_DEST"
else
    echo "[$(date -u +%FT%TZ)] BACKUP_DEST not set — skipping remote sync (local only)"
fi

# Prune old local backups
find "$LOCAL_BACKUP_DIR" -name "merit_registry_*.db.gz" -mtime +"$BACKUP_RETAIN_DAYS" -delete
echo "[$(date -u +%FT%TZ)] Pruned backups older than $BACKUP_RETAIN_DAYS days"

echo "[$(date -u +%FT%TZ)] Backup complete: $COMPRESSED"
