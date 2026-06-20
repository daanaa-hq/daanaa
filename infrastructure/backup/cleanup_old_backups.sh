#!/bin/bash
# Cleanup old backups — run weekly (Sunday 4 AM) via cron
# Enforces retention: 30 days home, 14 days droplet

HOME_BACKUP_DIR="$HOME/backups/merit_registry"
DROPLET_BACKUP_DIR="$HOME/backups/search.db"

echo "[$(date)] Cleaning up old backups..."

# Home server (30-day retention)
OLD_HOME=$(find "$HOME_BACKUP_DIR" -name "*.tar.gz" -mtime +30 2>/dev/null | wc -l)
if [ "$OLD_HOME" -gt 0 ]; then
  echo "  Removing $OLD_HOME home backups older than 30 days..."
  find "$HOME_BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
fi

# Droplet (14-day retention)
OLD_DROPLET=$(find "$DROPLET_BACKUP_DIR" -name "*.tar.gz" -mtime +14 2>/dev/null | wc -l)
if [ "$OLD_DROPLET" -gt 0 ]; then
  echo "  Removing $OLD_DROPLET droplet backups older than 14 days..."
  find "$DROPLET_BACKUP_DIR" -name "*.tar.gz" -mtime +14 -delete
fi

# Summary
HOME_COUNT=$(find "$HOME_BACKUP_DIR" -name "*.tar.gz" 2>/dev/null | wc -l)
DROPLET_COUNT=$(find "$DROPLET_BACKUP_DIR" -name "*.tar.gz" 2>/dev/null | wc -l)

echo "[$(date)] ✓ Cleanup complete"
echo "  Home backups: $HOME_COUNT (30-day retention)"
echo "  Droplet backups: $DROPLET_COUNT (14-day retention)"
