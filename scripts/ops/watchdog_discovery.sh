#!/bin/bash
# Watchdog for discovery_daemon.py (donation-link discovery, NOT
# website_discovery_engine.py -- separate pipeline).
#
# 2026-08-18 rewrite: the daemon was down since 2026-08-16T00:04:29 because
# three files disagreed on the health-file path -- this watchdog checked
# /tmp/discovery_daemon_daemon.health.json, discovery_daemon_health.py
# checked /tmp/discovery_daemon.health.json, and discovery_daemon.py itself
# writes to logs/discovery_daemon_state.json. None of the three matched, so
# the health check always read "missing", and the old logic's only action on
# "missing" was pkill -- it never had a START branch at all. Every 5-minute
# cron tick killed a process that was never running, forever. Found by a
# Codex diagnostic pass (2026-08-17), fixed here: point at the real state
# file the daemon actually writes, and add the missing start step. The
# daemon has its own flock-based singleton guard (logs/discovery_daemon.lock)
# so a redundant start attempt here is safe -- it just exits immediately.
#
# See docs/DAEMON_HEALTH_STANDARD.md: verify real behavior, not process
# existence alone -- this checks last_updated_at freshness, not just "is a
# PID running".

STATE_FILE="/home/akbar/meritgiving/logs/discovery_daemon_state.json"
LOG_FILE="/home/akbar/meritgiving/logs/discovery_daemon.log"
MAX_AGE_SECONDS=900  # 15 minutes
BASE="/home/akbar/meritgiving"

start_daemon() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting discovery_daemon..."
    cd "$BASE" || exit 1
    # PYTHONPATH required: discovery_daemon.py does
    # `from scripts.discovery.website_discovery_comprehensive import ...`,
    # a repo-root-qualified import. Without this, python3's sys.path[0] is
    # scripts/discovery/ (the script's own dir), not the repo root, and the
    # import fails with "No module named 'scripts'" -- this crashed a
    # previously-healthy run at iteration 335 (discovered=17,783) before this
    # fix. Same bug class as safe_deploy_droplet.sh, fixed earlier tonight.
    PYTHONPATH="$BASE" nohup venv/bin/python3 scripts/discovery/discovery_daemon.py 100 0.5 5 8 \
        >> "$LOG_FILE" 2>&1 &
}

if [ ! -f "$STATE_FILE" ]; then
    echo "State file missing -- daemon has never reported in, starting..."
    start_daemon
    exit 0
fi

PID=$(jq -r '.pid // empty' "$STATE_FILE" 2>/dev/null)
LAST_UPDATED=$(jq -r '.last_updated_at // empty' "$STATE_FILE" 2>/dev/null)

if [ -z "$PID" ] || ! kill -0 "$PID" 2>/dev/null; then
    echo "State file's PID ($PID) is not alive, restarting..."
    start_daemon
    exit 0
fi

if [ -z "$LAST_UPDATED" ]; then
    echo "State file has no last_updated_at, treating as unhealthy, restarting..."
    kill "$PID" 2>/dev/null
    start_daemon
    exit 0
fi

LAST_EPOCH=$(date -d "$LAST_UPDATED" +%s 2>/dev/null)
NOW_EPOCH=$(date +%s)
if [ -z "$LAST_EPOCH" ]; then
    echo "Could not parse last_updated_at ($LAST_UPDATED), restarting..."
    kill "$PID" 2>/dev/null
    start_daemon
    exit 0
fi

AGE=$((NOW_EPOCH - LAST_EPOCH))
if [ "$AGE" -gt "$MAX_AGE_SECONDS" ]; then
    echo "State stale (${AGE}s > ${MAX_AGE_SECONDS}s), daemon likely hung. Restarting..."
    kill "$PID" 2>/dev/null
    start_daemon
    exit 0
fi

# Healthy: PID alive, state fresh. Nothing to do.
exit 0
