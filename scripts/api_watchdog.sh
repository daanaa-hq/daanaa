#!/bin/bash
# Watchdog for API daemon (migrated to daemon_health_lib.py 2026-08-10)

HEALTH_FILE="/tmp/droplet_api.health.json"
PORT=5000

# Step 1: Check published health state
if [ -f "$HEALTH_FILE" ]; then
    STATUS=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)

    if [ "$STATUS" = "failed" ]; then
        echo "[$(date)] API status=failed"
        exit 1
    fi

    echo "[$(date)] API daemon healthy (status=$STATUS)"
    exit 0
fi

# Step 2: Fallback — HTTP GET to /health endpoint
TIMEOUT=2
if timeout "$TIMEOUT" curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "[$(date)] API /health endpoint responding"
    exit 0
else
    echo "[$(date)] API /health endpoint not responding"
    exit 1
fi
