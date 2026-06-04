#!/bin/bash
# Nightly database sync: compress local database and transfer to droplet
# Run this after nightly_web_discovery_orchestrator.py completes

set -e

DROPLET_IP="162.243.97.179"
DROPLET_USER="root"
SSH_KEY="$HOME/.ssh/daanaa_do"
LOCAL_DB="$HOME/meritgiving/data/merit_registry.db"
DROPLET_DB="/opt/daanaa/data/merit_registry.db"
LOG_DIR="$HOME/meritgiving/logs"
LOG_FILE="$LOG_DIR/db_sync.log"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========== DATABASE SYNC START =========="

# Check if local database exists
if [ ! -f "$LOCAL_DB" ]; then
  log "ERROR: Local database not found at $LOCAL_DB"
  exit 1
fi

# Get local database size
LOCAL_SIZE=$(ls -lh "$LOCAL_DB" | awk '{print $5}')
log "Local database size: $LOCAL_SIZE"

# Check droplet disk space
DROPLET_FREE=$(ssh -i "$SSH_KEY" "root@$DROPLET_IP" "df / | tail -1 | awk '{print \$4}'" 2>/dev/null || echo "0")
log "Droplet free space: ${DROPLET_FREE}K"

# Compress database
log "Compressing database..."
cd "$(dirname "$LOCAL_DB")"
gzip -c "$(basename "$LOCAL_DB")" > merit_registry.db.gz.tmp
COMPRESSED_SIZE=$(ls -lh merit_registry.db.gz.tmp | awk '{print $5}')
log "Compressed size: $COMPRESSED_SIZE"
mv merit_registry.db.gz.tmp merit_registry.db.gz

# Transfer to droplet
log "Transferring to droplet..."
scp -i "$SSH_KEY" merit_registry.db.gz "root@$DROPLET_IP:/opt/daanaa/data/" || {
  log "ERROR: Transfer failed"
  rm -f merit_registry.db.gz
  exit 1
}
log "✓ Transfer complete"

# Decompress on droplet
log "Decompressing on droplet..."
ssh -i "$SSH_KEY" "root@$DROPLET_IP" "cd /opt/daanaa/data && rm -f merit_registry.db.bak && mv merit_registry.db merit_registry.db.bak 2>/dev/null; gunzip merit_registry.db.gz && ls -lh merit_registry.db" >> "$LOG_FILE" 2>&1 || {
  log "ERROR: Decompression failed on droplet"
  exit 1
}
log "✓ Database decompressed"

# Restart API
log "Restarting API on droplet..."
ssh -i "$SSH_KEY" "root@$DROPLET_IP" "pkill -f gunicorn; sleep 2; cd /opt/daanaa && /opt/daanaa/venv/bin/gunicorn -w 2 -b 0.0.0.0:80 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log daanaa_api:app &" >> "$LOG_FILE" 2>&1 || {
  log "WARNING: API restart may have failed"
}
log "✓ API restart initiated"

# Health check
log "Running health check..."
sleep 3
HEALTH=$(ssh -i "$SSH_KEY" "root@$DROPLET_IP" "curl -s http://localhost/api/stats | jq -r '.total_organizations // empty'" 2>/dev/null || echo "")
if [ -n "$HEALTH" ] && [ "$HEALTH" != "null" ]; then
  log "✓ Database sync successful (orgs: $HEALTH)"
else
  log "WARNING: Health check inconclusive"
fi

# Cleanup local compressed file
rm -f merit_registry.db.gz
log "Cleaned up local compressed file"

log "========== DATABASE SYNC SUCCESS =========="
