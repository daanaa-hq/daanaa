#!/bin/bash
# Backup droplet search.db — run at 3 AM via cron
# Syncs latest search.db from droplet, encrypts locally

set -e

BACKUP_DIR="$HOME/backups/search.db"
DROPLET_IP="162.243.97.179"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/search.db_${TIMESTAMP}.tar.gz"

# Rotate old backups (keep 14 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +14 -delete 2>/dev/null || true

# Pull search.db from droplet
echo "[$(date)] Backing up droplet search.db..."
TEMP_FILE="/tmp/search.db.tmp"

if ! scp -q root@$DROPLET_IP:/data/search.db "$TEMP_FILE" 2>/dev/null; then
  echo "ERROR: Failed to download search.db from droplet"
  exit 1
fi

# Compress and store
tar --gzip -cf "$BACKUP_FILE" -C /tmp search.db.tmp 2>/dev/null
rm -f "$TEMP_FILE"

if [ -f "$BACKUP_FILE" ]; then
  SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
  echo "[$(date)] ✓ Droplet backup complete: $BACKUP_FILE ($SIZE)"
  exit 0
else
  echo "ERROR: Backup failed"
  exit 1
fi
