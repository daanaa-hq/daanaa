#!/bin/bash
# Watchdog for discovery daemon (migrated to daemon_health_lib.py 2026-08-10)
# No longer greps log text; reads daemon's published state instead.

HEALTH_FILE="/tmp/discovery_daemon.health.json"
PID_FILE="/tmp/discovery_daemon.pid"
STARTUP_GRACE_PERIOD=30

# If health file is missing/stale, assume something is wrong
if [ ! -f "$HEALTH_FILE" ]; then
    echo "[$(date)] No health file; daemon may have crashed"
    # Read actual PID, kill if stale process
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null; then
            echo "[$(date)] Killing stale process $OLD_PID"
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
    fi
    exit 1
fi

# Parse health state (JSON)
STATUS=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)
LAST_RUN=$(jq -r '.last_updated_at // ""' "$HEALTH_FILE" 2>/dev/null)

# If status is "failed", restart immediately
if [ "$STATUS" = "failed" ]; then
    echo "[$(date)] Status=failed; restarting daemon"
    exit 1
fi

# If last_run is >15 min old, daemon is stuck
if [ -n "$LAST_RUN" ]; then
    LAST_RUN_EPOCH=$(date -d "$LAST_RUN" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(date +%s)
    AGE=$((NOW_EPOCH - LAST_RUN_EPOCH))

    if [ "$AGE" -gt 900 ]; then  # 900s = 15 min
        echo "[$(date)] Last run was $AGE seconds ago (>900s); daemon stuck"
        exit 1
    fi
fi

# If we get here, daemon is healthy
echo "[$(date)] Discovery daemon healthy (status=$STATUS, age=${AGE:-startup}s)"
exit 0
