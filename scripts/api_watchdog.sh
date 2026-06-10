#!/bin/bash
# API watchdog — restarts the gunicorn daanaa API if /health stops answering.
# Replaces the old cron line that pgrep'd merit_api.py (deleted in the daanaa
# rename), which left the real API unguarded. Runs every 15 min from cron.
BASE="$HOME/meritgiving"
LOG="$BASE/autodev/logs/watchdog.log"
mkdir -p "$(dirname "$LOG")"

if curl -sf --max-time 10 http://localhost:5000/health > /dev/null 2>&1; then
    exit 0
fi

# One retry after a short pause — don't restart over a transient blip.
sleep 5
if curl -sf --max-time 10 http://localhost:5000/health > /dev/null 2>&1; then
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] health check failed twice — restarting API" >> "$LOG"
cd "$BASE" && ./restart_api.sh >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] restart issued" >> "$LOG"
