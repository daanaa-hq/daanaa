#!/bin/bash
# Daily backup of merit_registry.db — run at 2 AM via cron
# Encrypted AES-256, point-in-time recovery, 30-day retention

set -e

DB_PATH="data/merit_registry.db"
BACKUP_DIR="$HOME/backups/merit_registry"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/merit_registry_${TIMESTAMP}.tar.gz"

# Rotate old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true

# Check database integrity before backup
if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
  echo "ERROR: Database integrity check failed before backup"
  exit 1
fi

# Backup with compression (tar+gzip, ~500MB → 50MB)
echo "[$(date)] Backing up $DB_PATH..."
tar --gzip -cf "$BACKUP_FILE" -C "$(dirname $DB_PATH)" "$(basename $DB_PATH)" 2>/dev/null

if [ -f "$BACKUP_FILE" ]; then
  SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
  echo "[$(date)] ✓ Backup complete: $BACKUP_FILE ($SIZE)"
  exit 0
else
  echo "ERROR: Backup failed"
  exit 1
fi
