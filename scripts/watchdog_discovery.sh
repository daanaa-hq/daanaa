#!/bin/bash
# Watchdog for discovery daemon.
# Monitors daemon and auto-restarts if crashed.
# Run via cron: */5 * * * * /home/akbar/meritgiving/scripts/watchdog_discovery.sh

LOG="/home/akbar/meritgiving/logs/watchdog_discovery.log"

check_daemon() {
    pgrep -f "discovery_daemon.py" > /dev/null 2>&1
    return $?
}

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

# Check if daemon is running
if check_daemon; then
    log_msg "✅ Daemon running"
else
    log_msg "🚨 Daemon crashed, restarting..."
    cd /home/akbar/meritgiving
    nohup python3 scripts/discovery_daemon.py 100 >> logs/discovery_daemon.log 2>&1 &
    sleep 2
    if check_daemon; then
        log_msg "✅ Daemon restarted successfully"
    else
        log_msg "❌ Failed to restart daemon"
    fi
fi
