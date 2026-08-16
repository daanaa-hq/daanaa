#!/bin/bash
# Auto-deploy when donation link count reaches 5K milestones
# Runs in background, monitors discovery progress

DEPLOY_SCRIPT="scripts/safe_deploy_droplet.sh"
DB_PATH="data/merit_registry.db"
LAST_MILESTONE=0

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a logs/milestone_deploys.log
}

get_donate_count() {
  sqlite3 -readonly "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL AND donate_url != '';" 2>/dev/null || echo "0"
}

log "Milestone monitor started. Watching for 5K increments..."
log "Current: $(get_donate_count) donation links"

while true; do
  CURRENT=$(get_donate_count)
  MILESTONE=$((CURRENT / 5000 * 5000))
  
  if [ "$MILESTONE" -gt "$LAST_MILESTONE" ] && [ "$MILESTONE" -ge 25000 ]; then
    log "🚀 MILESTONE: $MILESTONE donation links reached!"
    log "Deploying to droplet..."
    
    if bash "$DEPLOY_SCRIPT" 2>&1 | tee -a logs/milestone_deploys.log | tail -20; then
      log "✅ Deployment complete at $MILESTONE links"
      LAST_MILESTONE="$MILESTONE"
    else
      log "⚠️ Deployment failed at $MILESTONE, will retry"
    fi
  fi
  
  sleep 300  # Check every 5 minutes
done
