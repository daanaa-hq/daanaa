#!/bin/bash
"""
start_same_day_deploy.sh

Immediate deployment: Score current public data → precompute → deploy to droplet.
Runs to completion (~5-6 hours). Can be resumed if interrupted.

This is the entry point for same-day deployments triggered by:
1. Manual kick-off (now, for today's launch)
2. Auto-detection of new data (daily check)
3. Phase 2 enrichment completion

Usage:
    bash scripts/start_same_day_deploy.sh
"""

set -e

cd /home/akbar/meritgiving
source venv/bin/activate

SCRIPTS=scripts
LOGS=logs
DATA=data

mkdir -p $LOGS

LOG_FILE="$LOGS/same_day_deploy.log"

log() {
    msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log "========================================================================"
log "Same-Day Deployment Started"
log "========================================================================"

# Run the optimized post-phase2 workflow with current data
# (It's called "post_phase2" but it's the same process for any redeployment)
bash "$SCRIPTS/post_phase2_workflow.sh" 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "========================================================================"
    log "✅ Same-Day Deployment Complete"
    log "========================================================================"
    log "Droplet is LIVE at https://daanaa.org"
    log "Verify: curl https://daanaa.org/api/stats"
else
    log "❌ Deployment failed — check $LOG_FILE"
    exit 1
fi
