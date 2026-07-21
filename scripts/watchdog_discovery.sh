#!/bin/bash
# Watchdog for discovery daemon.
# Monitors daemon and auto-restarts if crashed OR stuck (thread-leaked/zombie).
# Run via cron: */5 * * * * /home/akbar/meritgiving/scripts/watchdog_discovery.sh

LOG="/home/akbar/meritgiving/logs/watchdog_discovery.log"
DAEMON_LOG="/home/akbar/meritgiving/logs/discovery_daemon.log"

check_daemon() {
    pgrep -f "discovery_daemon.py" > /dev/null 2>&1
    return $?
}

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

restart_daemon() {
    cd /home/akbar/meritgiving
    nohup python3 scripts/discovery_daemon.py 100 >> logs/discovery_daemon.log 2>&1 &
    sleep 2
    if check_daemon; then
        log_msg "✅ Daemon restarted successfully"
    else
        log_msg "❌ Failed to restart daemon"
    fi
}

# Check if daemon is running
if check_daemon; then
    # A daemon in T (stopped) state passes pgrep but does no work. The deploy
    # quiesce SIGSTOPs it briefly; if the deploy died before its CONT trap
    # fired, the daemon would stay frozen forever. Any stopped daemon seen by
    # a 5-minute watchdog tick has outlived the seconds-long snapshot window.
    STOPPED_PIDS=$(pgrep -f "discovery_daemon.py" | xargs -r ps -o pid=,stat= -p 2>/dev/null | awk '$2 ~ /^T/ {print $1}')
    if [ -n "$STOPPED_PIDS" ]; then
        log_msg "⚠️ Daemon stopped (T state) — resuming PID(s): $STOPPED_PIDS"
        # shellcheck disable=SC2086
        kill -CONT $STOPPED_PIDS 2>/dev/null
    fi

    # Productivity check (2026-07-20 incident): pgrep sees the process as
    # "running" even when a thread leak has left it 100% timing out on every
    # batch. Root cause: pool.shutdown(wait=False, cancel_futures=True) on a
    # batch timeout cancels pending futures but cannot kill threads already
    # stuck mid-request — those threads leak forever. After enough consecutive
    # timeouts the daemon accumulates hundreds of zombie threads contending for
    # CPU/GIL, which starves every subsequent batch too (self-reinforcing).
    # Detect via the last 8 log lines: if every recent "batch complete" line
    # shows zero successful verifications, the daemon is alive but stuck.
    RECENT_TIMEOUTS=$(tail -n 100 "$DAEMON_LOG" 2>/dev/null | grep -c "Batch timeout (600s): abandoning 50 stuck")
    RECENT_SUCCESS=$(tail -n 100 "$DAEMON_LOG" 2>/dev/null | grep -c "✅.*verified")
    THREAD_COUNT=0
    DAEMON_PID=$(pgrep -f "discovery_daemon.py" | head -1)
    if [ -n "$DAEMON_PID" ] && [ -r "/proc/$DAEMON_PID/status" ]; then
        THREAD_COUNT=$(awk '/^Threads:/{print $2}' "/proc/$DAEMON_PID/status" 2>/dev/null || echo 0)
    fi

    if [ "$RECENT_TIMEOUTS" -ge 4 ] && [ "$RECENT_SUCCESS" -eq 0 ]; then
        log_msg "🚨 Daemon STUCK (thread leak): ${RECENT_TIMEOUTS} full-batch timeouts, 0 successes in last 100 log lines, ${THREAD_COUNT} threads (PID $DAEMON_PID). Killing + restarting."
        kill -TERM "$DAEMON_PID" 2>/dev/null
        sleep 3
        kill -0 "$DAEMON_PID" 2>/dev/null && kill -9 "$DAEMON_PID" 2>/dev/null
        restart_daemon
    elif [ "$THREAD_COUNT" -gt 150 ]; then
        log_msg "⚠️ Daemon thread count high (${THREAD_COUNT}) but still producing — watching, not restarting yet."
        log_msg "✅ Daemon running (${THREAD_COUNT} threads)"
    else
        log_msg "✅ Daemon running (${THREAD_COUNT} threads)"
    fi
else
    log_msg "🚨 Daemon crashed, restarting..."
    restart_daemon
fi
