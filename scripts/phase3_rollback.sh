#!/bin/bash
# Phase 3 Rollback Script
# Restores database to pre-Phase3 state and restarts API

set -e

BACKUP_PATH="backups/merit_registry_phase3_pre_2026_07_28.db"
DB_PATH="data/merit_registry.db"

echo "[$(date)] === Phase 3 Rollback ==="

# Step 1: Verify backup exists
if [ ! -f "$BACKUP_PATH" ]; then
    echo "✗ Backup not found: $BACKUP_PATH"
    exit 1
fi

# Step 2: Restore database
echo "[$(date)] Restoring database from backup..."
cp "$BACKUP_PATH" "$DB_PATH"
echo "[$(date)] ✓ Database restored"

# Step 3: Restart API
echo "[$(date)] Restarting API..."
bash restart_api.sh

# Step 4: Verify
echo "[$(date)] Verifying restoration..."
curl -s http://localhost:5000/health | python3 -m json.tool

echo "[$(date)] ✓ Rollback complete — database at pre-Phase3 state"
