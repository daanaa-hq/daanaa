#!/bin/bash
"""
detect_data_changes.sh

Daily check for major data updates. If changes detected, triggers redeployment.
Designed to run from cron every morning (~7 AM).

Checks for:
1. New IRS BMF data (daily watch)
2. Phase 2 enrichment completion
3. Recent scoring runs (new merit_score updates)
4. Significant org count changes

If any major change detected: Triggers automatic redeployment.
"""

set -e

cd /home/akbar/meritgiving
source venv/bin/activate

SCRIPTS=scripts
LOGS=logs
DATA=data
DB="$DATA/merit_registry.db"

mkdir -p $LOGS

LOG_FILE="$LOGS/data_changes.log"
STATE_FILE="$LOGS/deployment_state.json"

log() {
    msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log "========================================================================"
log "Daily Data Change Detection"
log "========================================================================"

# Initialize state file if it doesn't exist
if [ ! -f "$STATE_FILE" ]; then
    log "Initializing deployment state..."
    echo '{"last_deploy": "2026-06-09T00:00:00", "last_org_count": 0, "last_score_update": "2026-06-09T00:00:00"}' > "$STATE_FILE"
fi

LAST_DEPLOY=$(jq -r '.last_deploy' "$STATE_FILE")
LAST_ORG_COUNT=$(jq -r '.last_org_count' "$STATE_FILE")
LAST_SCORE_UPDATE=$(jq -r '.last_score_update' "$STATE_FILE")

log "Previous deployment: $LAST_DEPLOY"
log "Previous org count: $LAST_ORG_COUNT"
log "Previous score update: $LAST_SCORE_UPDATE"

# Check 1: New org count (IRS BMF daily watch)
CURRENT_ORG_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM registry_enriched WHERE deductibility=1 AND org_status='active'" 2>/dev/null || echo "0")
ORG_CHANGE=$((CURRENT_ORG_COUNT - LAST_ORG_COUNT))

log "Current org count: $CURRENT_ORG_COUNT (change: +$ORG_CHANGE)"

if [ $ORG_CHANGE -gt 100 ]; then
    log "✅ Significant org count change detected (+$ORG_CHANGE orgs)"
    REDEPLOY=1
fi

# Check 2: New score updates
LATEST_SCORE_UPDATE=$(sqlite3 "$DB" "SELECT MAX(datetime(updated_at)) FROM registry_enriched WHERE merit_score IS NOT NULL" 2>/dev/null || echo "")

if [ ! -z "$LATEST_SCORE_UPDATE" ] && [ "$LATEST_SCORE_UPDATE" != "$LAST_SCORE_UPDATE" ]; then
    log "✅ New merit scores detected (latest: $LATEST_SCORE_UPDATE)"
    REDEPLOY=1
fi

# Check 3: Phase 2 enrichment progress
PHASE2_PROGRESS=$(tail -1 "$LOGS/phase2_financial_backfill.log" 2>/dev/null | grep -oE '[0-9]+/245,340' || echo "")

if grep -q "245,340/245,340" "$LOGS/phase2_financial_backfill.log" 2>/dev/null; then
    log "✅ Phase 2 enrichment COMPLETE — triggering update with enriched data"
    REDEPLOY=1
elif [ ! -z "$PHASE2_PROGRESS" ]; then
    log "Phase 2 in progress: $PHASE2_PROGRESS"
fi

# Check 4: Check if any recent scoring runs
RECENT_SCORE_FILES=$(find "$LOGS" -name "scorer_*.log" -newer "$LAST_DEPLOY" 2>/dev/null | wc -l)

if [ $RECENT_SCORE_FILES -gt 0 ]; then
    log "✅ Recent scoring detected ($RECENT_SCORE_FILES new runs)"
    REDEPLOY=1
fi

# Decision
if [ "$REDEPLOY" = "1" ]; then
    log "========================================================================"
    log "CHANGE DETECTED — Triggering Redeployment"
    log "========================================================================"

    # Record deployment state
    DEPLOY_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq --arg time "$DEPLOY_TIME" --arg count "$CURRENT_ORG_COUNT" --arg score "$LATEST_SCORE_UPDATE" \
        '.last_deploy = $time | .last_org_count = ($count | tonumber) | .last_score_update = $score' \
        "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

    # Trigger deployment
    log "Starting redeployment..."
    bash "$SCRIPTS/start_same_day_deploy.sh" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "✅ Redeployment successful"
    else
        log "❌ Redeployment failed — check logs"
        exit 1
    fi
else
    log "No significant changes detected. No redeployment needed."
fi

log "========================================================================"
