#!/bin/bash
# Autonomous Precompute Watch — Detects agent completion, triggers rebuild
# Runs every 2 hours during the 60-hour autonomy window

LOG_FILE="/home/akbar/meritgiving/logs/precompute_auto_trigger.log"
DB_PATH="/home/akbar/meritgiving/data/merit_registry.db"
TRIGGER_FILE="/tmp/precompute_rebuild_triggered.flag"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if rebuild already triggered
if [ -f "$TRIGGER_FILE" ]; then
    log "Rebuild already triggered. Exiting."
    exit 0
fi

# Count recent website discoveries (last 36 hours)
RECENT_WEBSITES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE website_checked_at > datetime('now', '-36 hours') AND website IS NOT NULL;" 2>/dev/null || echo 0)

# Count websites with very recent timestamps (last 2 hours = sign of active agents)
ACTIVE_AGENTS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE website_checked_at > datetime('now', '-2 hours') AND website IS NOT NULL;" 2>/dev/null || echo 0)

log "Website discovery status: $RECENT_WEBSITES in last 36h, $ACTIVE_AGENTS in last 2h"

# If agents were active 2h ago but silent now = they finished
if [ "$ACTIVE_AGENTS" -eq 0 ] && [ "$RECENT_WEBSITES" -gt 100 ]; then
    log "✅ AGENTS APPEAR COMPLETE (silent for 2h, found $RECENT_WEBSITES websites)"

    # Double-check: wait 1 more hour before triggering (in case they restart)
    log "Waiting 1 hour for confirmation... (monitoring in background)"

    # Schedule a follow-up check
    sleep 3600

    STILL_SILENT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE website_checked_at > datetime('now', '-1 hour') AND website IS NOT NULL;" 2>/dev/null || echo 0)

    if [ "$STILL_SILENT" -eq 0 ]; then
        log "🚀 CONFIRMED: Agents silent for 3+ hours. Starting precompute rebuild."
        touch "$TRIGGER_FILE"

        # Trigger the rebuild
        cd /home/akbar/meritgiving || exit 1
        log "Running: bash scripts/safe_deploy_droplet.sh (full mode)"

        bash scripts/safe_deploy_droplet.sh >> "$LOG_FILE" 2>&1
        REBUILD_STATUS=$?

        if [ $REBUILD_STATUS -eq 0 ]; then
            log "✅ PRECOMPUTE REBUILD COMPLETE"
            log "📊 System ready for deployment"
            echo "REBUILD_SUCCESS" > "$TRIGGER_FILE"
        else
            log "❌ PRECOMPUTE REBUILD FAILED (exit code: $REBUILD_STATUS)"
            log "   Attempting rollback to previous precompute..."
            # Rollback handled by safe_deploy_droplet.sh itself
            echo "REBUILD_FAILED" > "$TRIGGER_FILE"
        fi
    else
        log "Agents still active ($STILL_SILENT recent). Deferring rebuild."
        rm -f "$TRIGGER_FILE"
    fi
else
    log "Agents still active or insufficient data. No action."
fi
