#!/bin/bash
# Phase 3 Rollback Script
# Restores database to pre-Phase3 state and restarts API

set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_PATH="$SCRIPT_DIR/../backups/merit_registry_phase3_pre_2026_07_28.db"
CURRENT_BACKUP="$SCRIPT_DIR/../data/backups/v6/rollback_pre_$(date +%Y%m%dT%H%M%S).db"
DB_PATH="$SCRIPT_DIR/../data/merit_registry.db"
RESTORE_PATH="${DB_PATH}.rollback.tmp"

echo "[$(date)] === Phase 3 Rollback ==="

# Step 1: Verify backup exists
if [ ! -f "$BACKUP_PATH" ]; then
    echo "✗ Backup not found: $BACKUP_PATH"
    exit 1
fi

# Step 2: Restore database
echo "[$(date)] Backing up current database to $CURRENT_BACKUP..."
sqlite3 "$DB_PATH" ".backup '$CURRENT_BACKUP'"
echo "[$(date)] Restoring database from verified backup..."
rm -f "$RESTORE_PATH"
cp "$BACKUP_PATH" "$RESTORE_PATH"
if [ "$(sqlite3 "$RESTORE_PATH" "PRAGMA integrity_check;")" != "ok" ]; then echo "✗ Restore integrity check failed"; rm -f "$RESTORE_PATH"; exit 1; fi
mv -f "$RESTORE_PATH" "$DB_PATH"
echo "[$(date)] ✓ Database restored"

# Step 3: Restart API
echo "[$(date)] Restarting API..."
bash "$SCRIPT_DIR/../restart_api.sh"

# Step 4: Verify
echo "[$(date)] Verifying restoration..."
curl -s http://localhost:5000/health | python3 -m json.tool

echo "[$(date)] ✓ Rollback complete — database at pre-Phase3 state"
