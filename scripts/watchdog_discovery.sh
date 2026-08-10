#!/bin/bash
# Watchdog for discovery daemon.
# Monitors daemon and auto-restarts if crashed OR stuck (thread-leaked/zombie).
# Run via cron: */5 * * * * /home/akbar/meritgiving/scripts/watchdog_discovery.sh

LOG="/home/akbar/meritgiving/logs/watchdog_discovery.log"
DAEMON_LOG="/home/akbar/meritgiving/logs/discovery_daemon.log"
STATE_FILE="/home/akbar/meritgiving/logs/discovery_daemon_state.json"
HEALTH_SCRIPT="/home/akbar/meritgiving/scripts/discovery_daemon_health.py"
PYTHON="/home/akbar/meritgiving/venv/bin/python3"

check_daemon() {
    pgrep -f "discovery_daemon.py" > /dev/null 2>&1
    return $?
}

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

restart_daemon() {
    local reason="$1"
    cd /home/akbar/meritgiving
    nohup python3 scripts/discovery_daemon.py 100 >> logs/discovery_daemon.log 2>&1 &
    sleep 2
    if check_daemon; then
        log_msg "✅ Daemon restarted successfully (reason: ${reason})"
    else
        log_msg "❌ Failed to restart daemon (reason: ${reason})"
    fi
}

# Legacy log-text fallback (2026-08-10 fixed: was hardcoded to a stale batch
# size, silently dead for ~15.4 days — see governance/LESSONS.md). Kept ONLY
# as a fallback for when the daemon's own state file (below) is missing or
# doesn't belong to the currently running PID — e.g. right after this
# instrumentation is first deployed, before the daemon has written a
# snapshot. This is NOT the primary detection path anymore.
legacy_log_based_check() {
    local daemon_pid="$1"
    local thread_count="$2"

    STARTUP_LINE=$(grep -n "CONTINUOUS DISCOVERY DAEMON STARTED" "$DAEMON_LOG" 2>/dev/null | tail -1 | cut -d: -f1)
    if [ -n "$STARTUP_LINE" ]; then
        CURRENT_LOG=$(tail -n +"$STARTUP_LINE" "$DAEMON_LOG" 2>/dev/null | tail -n 500)
    else
        CURRENT_LOG=""
    fi
    RECENT_TIMEOUTS=$(echo "$CURRENT_LOG" | tail -n 100 | grep -cE "Batch timeout \(600s\): abandoning [0-9]+ stuck")
    PROGRESS_LINES=$(echo "$CURRENT_LOG" | grep "Progress: discovered=" | tail -n 6)
    STUCK_BY_COUNTER=0
    if [ "$(echo "$PROGRESS_LINES" | grep -c '^')" -ge 6 ]; then
        FIRST_VERIFIED=$(echo "$PROGRESS_LINES" | head -1 | grep -oE 'verified=[0-9]+' | cut -d= -f2)
        LAST_VERIFIED=$(echo "$PROGRESS_LINES" | tail -1 | grep -oE 'verified=[0-9]+' | cut -d= -f2)
        if [ -n "$FIRST_VERIFIED" ] && [ -n "$LAST_VERIFIED" ] && [ "$FIRST_VERIFIED" = "$LAST_VERIFIED" ]; then
            STUCK_BY_COUNTER=1
        fi
    fi

    if [ "$RECENT_TIMEOUTS" -ge 4 ] && [ "$STUCK_BY_COUNTER" -eq 1 ]; then
        log_msg "🚨 [fallback/log-based] Daemon STUCK: ${RECENT_TIMEOUTS} full-batch timeouts, verified counter frozen, ${thread_count} threads (PID ${daemon_pid}). Killing + restarting."
        kill -TERM "$daemon_pid" 2>/dev/null
        sleep 3
        kill -0 "$daemon_pid" 2>/dev/null && kill -9 "$daemon_pid" 2>/dev/null
        restart_daemon "fallback: log-based stuck detection"
    else
        log_msg "✅ Daemon running (${thread_count} threads, no state file yet — using log-based fallback, no stuck pattern found)"
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

    DAEMON_PID=$(pgrep -f "discovery_daemon.py" | head -1)
    THREAD_COUNT=0
    if [ -n "$DAEMON_PID" ] && [ -r "/proc/$DAEMON_PID/status" ]; then
        THREAD_COUNT=$(awk '/^Threads:/{print $2}' "/proc/$DAEMON_PID/status" 2>/dev/null || echo 0)
    fi

    # 2026-08-10: primary health decision now comes from the daemon's own
    # published state (scripts/discovery_daemon_health.py), not from this
    # script reverse-engineering health via log-text grepping. See
    # governance/LESSONS.md 2026-08-10 for why the old approach silently
    # broke for ~15.4 days and governance/DECISIONS.md for the redesign.
    if [ -x "$PYTHON" ] && [ -f "$HEALTH_SCRIPT" ]; then
        DECISION=$("$PYTHON" "$HEALTH_SCRIPT" --state-file "$STATE_FILE" --pid "$DAEMON_PID" --pid-alive true 2>>"$LOG")
        ACTION=$(echo "$DECISION" | grep -oE '"action": *"[a-z_]+"' | sed -E 's/.*"([a-z_]+)"$/\1/')
        REASON=$(echo "$DECISION" | grep -oE '"reason": *"[^"]*"' | sed -E 's/.*"([^"]*)"$/\1/')

        case "$ACTION" in
            restart)
                log_msg "🚨 [state-based] Daemon STUCK: ${REASON} (${THREAD_COUNT} threads, PID ${DAEMON_PID}). Killing + restarting."
                kill -TERM "$DAEMON_PID" 2>/dev/null
                sleep 3
                kill -0 "$DAEMON_PID" 2>/dev/null && kill -9 "$DAEMON_PID" 2>/dev/null
                restart_daemon "state-based: ${REASON}"
                ;;
            ok)
                if [ "$THREAD_COUNT" -gt 150 ]; then
                    log_msg "⚠️ Daemon thread count high (${THREAD_COUNT}) but state file confirms productive — watching, not restarting."
                fi
                log_msg "✅ Daemon running (${THREAD_COUNT} threads, state: ok)"
                ;;
            unknown_no_state|unknown_stale_pid|"")
                # No trustworthy state yet (fresh instrumentation, or a
                # restart just happened and the new process hasn't written
                # its first snapshot). Fall back to the log-based check
                # rather than assuming healthy.
                legacy_log_based_check "$DAEMON_PID" "$THREAD_COUNT"
                ;;
            *)
                log_msg "⚠️ Unrecognized health decision output, falling back to log-based check: ${DECISION}"
                legacy_log_based_check "$DAEMON_PID" "$THREAD_COUNT"
                ;;
        esac
    else
        log_msg "⚠️ Health script or venv python unavailable, using log-based fallback."
        legacy_log_based_check "$DAEMON_PID" "$THREAD_COUNT"
    fi
else
    log_msg "🚨 Daemon crashed, restarting..."
    restart_daemon "process not found"
fi
