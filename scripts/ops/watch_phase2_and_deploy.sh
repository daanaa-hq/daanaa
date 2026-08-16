#!/bin/bash
"""
watch_phase2_and_deploy.sh

Monitors Phase 2 backfill progress. When complete, automatically runs
the post_phase2_workflow.sh to score, index, and deploy.

This is meant to run in the background and can be triggered via:

    bash scripts/watch_phase2_and_deploy.sh &

It will exit once Phase 2 completes and post-Phase-2 workflow finishes.
"""

set -e

cd /home/akbar/meritgiving

PHASE2_LOG="logs/phase2_financial_backfill.log"
LOG="logs/watch_phase2.log"

log() {
    msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG"
}

log "========================================================================"
log "watch_phase2_and_deploy started"
log "========================================================================"

if [ ! -f "$PHASE2_LOG" ]; then
    log "ERROR: Phase 2 log not found at $PHASE2_LOG"
    exit 1
fi

log "Monitoring Phase 2 progress at $PHASE2_LOG"
log "Will auto-trigger post_phase2_workflow.sh when complete..."

# Poll every 30 seconds for Phase 2 completion
while true; do
    tail_output=$(tail -1 "$PHASE2_LOG" 2>/dev/null || echo "")

    # Check for completion: either "245,340/245,340" or "COMPLETE" marker
    if echo "$tail_output" | grep -qE "245,340/245,340|Phase 2.*COMPLETE|Backfill.*done"; then
        log "✅ Phase 2 COMPLETE detected!"
        log "Last log line: $tail_output"
        break
    fi

    # Check for errors
    if echo "$tail_output" | grep -qE "Error|Traceback|Killed|FAILED"; then
        log "❌ Phase 2 ERROR detected!"
        log "Last log line: $tail_output"
        log "Not proceeding with post-Phase-2 workflow due to error."
        exit 1
    fi

    sleep 30
done

log "========================================================================"
log "Phase 2 complete! Triggering post_phase2_workflow.sh..."
log "========================================================================"

# Run the workflow (this will take ~3-4 hours)
bash scripts/post_phase2_workflow.sh 2>&1 | tee -a "$LOG"

log "========================================================================"
log "✅ Post-Phase-2 Workflow Complete"
log "========================================================================"
log "Verify deployment:"
log "  Local API:  curl http://localhost:5000/api/stats"
log "  Droplet:    curl https://daanaa.org/api/stats"
log "========================================================================"
