#!/bin/bash
# Sync database FROM droplet TO localhost (keep them in sync)
# Run at 2 AM daily (after nightly pipeline + sync completes)

set -e

DROPLET_IP="162.243.97.179"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"  # passphrase-free automation key (see LESSONS.md 2026-07-05)
DROPLET_DB="/opt/daanaa/data/merit_registry.db"
LOCAL_DB="$HOME/meritgiving/data/merit_registry.db"
LOCAL_DB_BAK="$LOCAL_DB.bak-$(date +%Y%m%d_%H%M%S)"
LOG_DIR="$HOME/meritgiving/logs"
LOG_FILE="$LOG_DIR/db_sync_from_droplet.log"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========== SYNC FROM DROPLET START =========="

# Check if local database exists, back it up
if [ -f "$LOCAL_DB" ]; then
  log "Backing up local database..."
  cp "$LOCAL_DB" "$LOCAL_DB_BAK"
  log "✓ Backup created: $(basename "$LOCAL_DB_BAK")"
fi

# Download from droplet
log "Downloading database from droplet..."
scp -i "$SSH_KEY" "root@$DROPLET_IP:$DROPLET_DB" "$LOCAL_DB" || {
  log "ERROR: Download failed, restoring backup"
  if [ -f "$LOCAL_DB_BAK" ]; then
    cp "$LOCAL_DB_BAK" "$LOCAL_DB"
  fi
  exit 1
}
log "✓ Download complete"

# Restart localhost API
log "Restarting localhost API..."
pkill -f "gunicorn.*daanaa_api" || true
sleep 2
cd ~/meritgiving
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 --preload daanaa_api:app &
sleep 3
log "✓ API restarted"

# Health check localhost
log "Health check (localhost)..."
LOCALHOST_ORGS=$(curl -s http://localhost:5000/api/stats | jq -r '.total_organizations // empty' 2>/dev/null || echo "")
LOCALHOST_DATE=$(curl -s http://localhost:5000/api/stats | jq -r '.scores_last_updated // empty' 2>/dev/null || echo "")

# Health check droplet
log "Health check (droplet)..."
DROPLET_ORGS=$(ssh -i "$SSH_KEY" "root@$DROPLET_IP" "curl -s http://localhost/api/stats | jq -r '.total_organizations // empty'" 2>/dev/null || echo "")
DROPLET_DATE=$(ssh -i "$SSH_KEY" "root@$DROPLET_IP" "curl -s http://localhost/api/stats | jq -r '.scores_last_updated // empty'" 2>/dev/null || echo "")

# Compare
if [ "$LOCALHOST_ORGS" = "$DROPLET_ORGS" ] && [ "$LOCALHOST_DATE" = "$DROPLET_DATE" ]; then
  log "✓ SYNC VERIFIED: Both sites match!"
  log "  Orgs: $LOCALHOST_ORGS | Date: $LOCALHOST_DATE"
else
  log "WARNING: Sites don't match (may need restart)"
  log "  Localhost: $LOCALHOST_ORGS ($LOCALHOST_DATE)"
  log "  Droplet:   $DROPLET_ORGS ($DROPLET_DATE)"
fi

# Cleanup old backups (keep last 7)
log "Cleaning up old backups..."
ls -t "${LOCAL_DB}.bak-"* 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true

log "========== SYNC FROM DROPLET SUCCESS =========="
