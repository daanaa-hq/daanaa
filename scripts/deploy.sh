#!/bin/bash
# Automated deployment: build frontend, sync to droplet, restart API

set -e

DROPLET_IP="162.243.97.179"
DROPLET_USER="root"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"  # passphrase-free automation key (see LESSONS.md 2026-07-05)
REPO_DIR="$HOME/meritgiving"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/deployment.log"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========== DEPLOYMENT START =========="

# Step 1: Build frontend
log "Building frontend..."
cd "$REPO_DIR/frontend"
npm run build >> "$LOG_FILE" 2>&1 || { log "ERROR: Frontend build failed"; exit 1; }
log "✓ Frontend built successfully"

# Step 2: Sync to droplet
log "Syncing to droplet ($DROPLET_IP)..."
rsync -avz -e "ssh -i $SSH_KEY" \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.env' \
  --exclude='*.db.gz' \
  --exclude='venv' \
  --exclude='data/*' \
  --exclude='logs/*' \
  --exclude='precompute_output/*' \
  --exclude='.deploy_scratch' \
  "$REPO_DIR/" "root@$DROPLET_IP:/opt/daanaa/" >> "$LOG_FILE" 2>&1 || {
  log "ERROR: Rsync to droplet failed"
  exit 1
}
log "✓ Code synced to droplet"

# Step 3: Promote updated droplet_api.py and restart via systemd
log "Restarting API on droplet (systemd)..."
ssh -i "$SSH_KEY" "root@$DROPLET_IP" \
  "cp /opt/daanaa/scripts/droplet_api.py /opt/daanaa/droplet_api.py && systemctl restart daanaa" \
  >> "$LOG_FILE" 2>&1 || {
  log "ERROR: API restart failed"
  exit 1
}
log "✓ API restarting on droplet"

# Step 4: Health check
log "Running health check..."
sleep 5
HEALTH=$(ssh -i "$SSH_KEY" "root@$DROPLET_IP" "curl -s http://localhost:5000/api/stats | jq -r '.total_organizations // empty'" 2>/dev/null || echo "")
if [ -n "$HEALTH" ] && [ "$HEALTH" != "null" ]; then
  log "✓ API health check passed (orgs: $HEALTH)"
else
  log "WARNING: Health check failed or incomplete"
fi

# Step 5: Git info
BRANCH=$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)
COMMIT=$(git -C "$REPO_DIR" rev-parse --short HEAD)
log "Deployed from: $BRANCH ($COMMIT)"

log "========== DEPLOYMENT SUCCESS =========="
