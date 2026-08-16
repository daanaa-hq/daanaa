#!/bin/bash
# Watchdog for discovery_daemon - reads daemon-published health state
# No grep, no hardcoded strings; pure decision logic

HEALTH_FILE="/tmp/discovery_daemon_daemon.health.json"
MAX_AGE_SECONDS=900  # 15 minutes

if [ ! -f "$HEALTH_FILE" ]; then
    echo "Health file missing, restarting discovery_daemon..."
    pkill -f discovery_daemon || true
    exit 1
fi

# Read health status
STATUS=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)
AGE=$(jq -r '.age_seconds // 9999' "$HEALTH_FILE" 2>/dev/null)

# Decision logic (pure, testable)
if [ "$STATUS" = "failed" ]; then
    echo "Daemon reported failure, restarting..."
    pkill -f discovery_daemon || true
    exit 1
fi

if [ "${AGE}" -gt "${MAX_AGE_SECONDS}" ]; then
    echo "Health file stale (>15 min), daemon likely hung..."
    pkill -f discovery_daemon || true
    exit 1
fi

exit 0
