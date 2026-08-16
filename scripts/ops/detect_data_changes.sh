#!/bin/bash
#
# detect_data_changes.sh — daily check for major data updates; redeploys if found.
#
# Designed to run from cron every morning (~7 AM). Checks:
#   1. Significant org count change (IRS BMF daily watch, +100 threshold)
#   2. New merit score updates since the last deploy
#   3. Scorer log files newer than the last deploy
#
# On any hit: deploys via safe_deploy_droplet.sh (online snapshot, integrity
# gate, disk guard — never disturbs the live :5000 API). Deployment state is
# recorded only AFTER a successful deploy, so a failed deploy retries the
# next morning instead of being silently marked done.
#
# History: rewritten 2026-06-10 — the original never ran (cron line used
# `source` under /bin/sh), had a Python docstring as a bash header, passed a
# timestamp to `find -newer` (needs a file), and called the one-time launch
# flow start_same_day_deploy.sh.

set -euo pipefail

cd /home/akbar/meritgiving

LOGS=logs
DB="data/merit_registry.db"

mkdir -p "$LOGS"

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
    echo '{"last_deploy": "2026-06-10T00:00:00", "last_org_count": 0, "last_score_update": ""}' > "$STATE_FILE"
fi

LAST_DEPLOY=$(jq -r '.last_deploy' "$STATE_FILE")
LAST_ORG_COUNT=$(jq -r '.last_org_count' "$STATE_FILE")
LAST_SCORE_UPDATE=$(jq -r '.last_score_update' "$STATE_FILE")

log "Previous deployment: $LAST_DEPLOY"
log "Previous org count: $LAST_ORG_COUNT"
log "Previous score update: $LAST_SCORE_UPDATE"

REDEPLOY=0

# Check 1: org count change (IRS BMF daily watch)
CURRENT_ORG_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM registry_enriched WHERE deductibility=1 AND org_status='active'" 2>/dev/null || echo "0")
ORG_CHANGE=$((CURRENT_ORG_COUNT - LAST_ORG_COUNT))

log "Current org count: $CURRENT_ORG_COUNT (change: $ORG_CHANGE)"

if [ "$ORG_CHANGE" -gt 100 ] || [ "$ORG_CHANGE" -lt -100 ]; then
    log "✅ Significant org count change detected ($ORG_CHANGE orgs)"
    REDEPLOY=1
fi

# Check 2: new score updates
LATEST_SCORE_UPDATE=$(sqlite3 "$DB" "SELECT COALESCE(MAX(datetime(updated_at)), '') FROM registry_enriched WHERE merit_score IS NOT NULL" 2>/dev/null || echo "")

if [ -n "$LATEST_SCORE_UPDATE" ] && [ "$LATEST_SCORE_UPDATE" != "$LAST_SCORE_UPDATE" ]; then
    log "✅ New merit scores detected (latest: $LATEST_SCORE_UPDATE)"
    REDEPLOY=1
fi

# Check 3: scorer log files newer than the last deploy
RECENT_SCORE_FILES=$(find "$LOGS" -name "scorer_*.log" -newermt "$LAST_DEPLOY" 2>/dev/null | wc -l)

if [ "$RECENT_SCORE_FILES" -gt 0 ]; then
    log "✅ Recent scoring detected ($RECENT_SCORE_FILES new runs)"
    REDEPLOY=1
fi

# Decision
if [ "$REDEPLOY" = "1" ]; then
    log "========================================================================"
    log "CHANGE DETECTED — Triggering Redeployment (safe_deploy_droplet.sh)"
    log "========================================================================"

    if bash scripts/safe_deploy_droplet.sh >> "$LOG_FILE" 2>&1; then
        # Record state only on success — a failed deploy retries tomorrow
        DEPLOY_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        jq --arg time "$DEPLOY_TIME" --arg count "$CURRENT_ORG_COUNT" --arg score "$LATEST_SCORE_UPDATE" \
            '.last_deploy = $time | .last_org_count = ($count | tonumber) | .last_score_update = $score' \
            "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
        log "✅ Redeployment successful"
    else
        log "❌ Redeployment failed — state NOT updated, will retry tomorrow"
        exit 1
    fi
else
    log "No significant changes detected. No redeployment needed."
fi

log "========================================================================"
