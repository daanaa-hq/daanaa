#!/bin/bash
# Watchdog for llama inference server (migrated to daemon_health_lib.py 2026-08-10)

PORT=${1:-11437}
HEALTH_FILE="/tmp/llama_server.health.json"
TIMEOUT=2

# Step 1: Check published health state
if [ -f "$HEALTH_FILE" ]; then
    STATUS=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)
    LAST_RUN=$(jq -r '.last_updated_at // ""' "$HEALTH_FILE" 2>/dev/null)

    if [ "$STATUS" = "failed" ]; then
        echo "[$(date)] Status=failed in health file"
        exit 1
    fi

    if [ -n "$LAST_RUN" ]; then
        LAST_RUN_EPOCH=$(date -d "$LAST_RUN" +%s 2>/dev/null || echo 0)
        NOW_EPOCH=$(date +%s)
        AGE=$((NOW_EPOCH - LAST_RUN_EPOCH))

        if [ "$AGE" -gt 900 ]; then
            echo "[$(date)] Llama health file stale ($AGE seconds)"
            exit 1
        fi
    fi

    echo "[$(date)] Llama server healthy (status=$STATUS)"
    exit 0
fi

# Step 2: Fallback — if no health file, check port directly
if timeout "$TIMEOUT" bash -c "echo > /dev/tcp/localhost/$PORT" 2>/dev/null; then
    echo "[$(date)] Llama server port $PORT is open"
    exit 0
else
    echo "[$(date)] Llama server port $PORT is closed"
    exit 1
fi
