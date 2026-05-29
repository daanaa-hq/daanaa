#!/bin/bash
# Restarts ops_server.py if it's not running.
# Cron: */5 * * * * /home/akbar/meritgiving/scripts/ops_watchdog.sh

PY=/home/akbar/meritgiving/venv/bin/python3
SCRIPT=/home/akbar/meritgiving/scripts/ops_server.py
LOG=/home/akbar/meritgiving/logs/ops_server.log

if ! pgrep -f ops_server.py > /dev/null 2>&1; then
    echo "$(date): ops_server.py not running — restarting" >> "$LOG"
    nohup "$PY" "$SCRIPT" >> "$LOG" 2>&1 &
fi
