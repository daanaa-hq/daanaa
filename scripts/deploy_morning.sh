#!/bin/bash
# Morning deployment (8am CST = 14:00 UTC)
# Redeploys frontend + API to droplet with health checks
# Logs to: /home/akbar/meritgiving/logs/deploy-morning-YYYYMMDD.log

set -e
# Cron has no nvm PATH — without this the build dies with "npm: command not found"
# (2026-07-09 morning deploy failure).
export PATH="/home/akbar/.nvm/versions/node/v22.22.2/bin:$PATH"
REPO="/home/akbar/meritgiving"
VENV="$REPO/venv/bin/activate"
LOG_DIR="$REPO/logs"
DROPLET="root@162.243.97.179"
DROPLET_API="http://162.243.97.179"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/deploy-morning-$(date +%Y%m%d).log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== MORNING DEPLOYMENT STARTED ==="
START_TIME=$(date +%s)

# Activate venv
cd "$REPO"
source "$VENV"

# 1. Rebuild frontend
log "Building frontend..."
cd frontend
npm run build >> "$LOG_FILE" 2>&1 || {
  log "❌ Frontend build failed"
  exit 1
}
log "✅ Frontend built"

# 2. Sync to droplet
log "Syncing to droplet..."
rsync -av --delete dist/ "$DROPLET:/opt/daanaa/frontend/dist/" >> "$LOG_FILE" 2>&1 || {
  log "❌ Rsync failed"
  exit 1
}
log "✅ Frontend synced"

# 3. Restart droplet API
log "Restarting droplet API..."
ssh "$DROPLET" "systemctl restart daanaa && sleep 3" >> "$LOG_FILE" 2>&1 || {
  log "❌ Service restart failed"
  exit 1
}
log "✅ API restarted"

# 4. Smoke test: health + one org detail
log "Running smoke tests..."
HEALTH=$(curl -s "$DROPLET_API/health" 2>&1 | jq -r '.status' 2>/dev/null || echo "error")
if [ "$HEALTH" != "ok" ]; then
  log "❌ Health check failed: $HEALTH"
  log "ROLLING BACK..."
  ssh "$DROPLET" "systemctl restart daanaa" >> "$LOG_FILE" 2>&1
  exit 1
fi

ORG_RESPONSE=$(curl -s "$DROPLET_API/api/organizations/460678496" 2>&1)
if echo "$ORG_RESPONSE" | jq . >/dev/null 2>&1; then
  log "✅ Org endpoint OK"
else
  log "❌ Org endpoint failed"
  ssh "$DROPLET" "systemctl restart daanaa" >> "$LOG_FILE" 2>&1
  exit 1
fi

# 5. Summary
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
log "=== DEPLOYMENT COMPLETE (${DURATION}s) ==="
log "Frontend: $(cd dist && find assets -name "*.js" | wc -l) assets"
log "Status: ✅ All checks passed"
log ""
