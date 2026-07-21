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
    #
    # 2026-07-21 refinement: a fixed 100-log-line window is NOT a reliable
    # "recent" window — each iteration only emits a few lines (worker
    # results + one progress line), so stale ✅ lines from well before the
    # daemon actually got stuck can still sit inside the last 100 lines,
    # making RECENT_SUCCESS falsely nonzero and suppressing the restart for
    # a long time (observed: 9 consecutive 100%-timeout iterations, 112
    # threads, before this check would have fired). Progress counters
    # (discovered=/verified=) are cumulative and monotonic, so instead check
    # whether the verified count in the last progress line is IDENTICAL to
    # the verified count several progress lines back — if so, nothing has
    # succeeded in that whole span regardless of what's elsewhere in the log.
    #
    # 2026-07-21, same session, second bug: the log file is append-only
    # across restarts. Right after ANY restart (manual or watchdog-driven),
    # the tail of the file can still be dominated by the PREVIOUS process's
    # frozen progress lines, since the fresh process hasn't logged 6 new
    # ones yet — this caused a live false-positive restart of a daemon that
    # was 3 minutes old and perfectly healthy (24 threads). Fix: scope all
    # analysis to lines AFTER the current process's own startup banner, so
    # a fresh restart always reads as "insufficient data yet", never "stuck".
    STARTUP_LINE=$(grep -n "CONTINUOUS DISCOVERY DAEMON STARTED" "$DAEMON_LOG" 2>/dev/null | tail -1 | cut -d: -f1)
    if [ -n "$STARTUP_LINE" ]; then
        CURRENT_LOG=$(tail -n +"$STARTUP_LINE" "$DAEMON_LOG" 2>/dev/null | tail -n 500)
    else
        CURRENT_LOG=""
    fi
    RECENT_TIMEOUTS=$(echo "$CURRENT_LOG" | tail -n 100 | grep -c "Batch timeout (600s): abandoning 50 stuck")
    PROGRESS_LINES=$(echo "$CURRENT_LOG" | grep "Progress: discovered=" | tail -n 6)
    STUCK_BY_COUNTER=0
    if [ "$(echo "$PROGRESS_LINES" | grep -c '^')" -ge 6 ]; then
        FIRST_VERIFIED=$(echo "$PROGRESS_LINES" | head -1 | grep -oE 'verified=[0-9]+' | cut -d= -f2)
        LAST_VERIFIED=$(echo "$PROGRESS_LINES" | tail -1 | grep -oE 'verified=[0-9]+' | cut -d= -f2)
        if [ -n "$FIRST_VERIFIED" ] && [ -n "$LAST_VERIFIED" ] && [ "$FIRST_VERIFIED" = "$LAST_VERIFIED" ]; then
            STUCK_BY_COUNTER=1
        fi
    fi
    THREAD_COUNT=0
    DAEMON_PID=$(pgrep -f "discovery_daemon.py" | head -1)
    if [ -n "$DAEMON_PID" ] && [ -r "/proc/$DAEMON_PID/status" ]; then
        THREAD_COUNT=$(awk '/^Threads:/{print $2}' "/proc/$DAEMON_PID/status" 2>/dev/null || echo 0)
    fi

    if [ "$RECENT_TIMEOUTS" -ge 4 ] && [ "$STUCK_BY_COUNTER" -eq 1 ]; then
        log_msg "🚨 Daemon STUCK (thread leak): ${RECENT_TIMEOUTS} full-batch timeouts, verified counter unchanged across last 6 iterations, ${THREAD_COUNT} threads (PID $DAEMON_PID). Killing + restarting."
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
