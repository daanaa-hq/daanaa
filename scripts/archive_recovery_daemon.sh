#!/bin/bash
# Archive recovery daemon — monitor the dead-pool scan and auto-promote on completion.
# Runs continuously; handles state via lockfile.

set -euo pipefail

REPO="$HOME/meritgiving"
VENV="$REPO/venv/bin/activate"
LOCK="/tmp/archive_recovery_daemon.lock"
LOG="$REPO/logs/archive_finder/daemon.log"
PID_FILE="/tmp/archive_recovery_daemon.pid"

mkdir -p "$(dirname "$LOG")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

trap 'log "daemon stopped"; rm -f "$LOCK" "$PID_FILE"' EXIT INT TERM

# Single-instance guard
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log "daemon already running (PID $OLD_PID)"
        exit 0
    fi
fi
echo "$$" > "$PID_FILE"

log "=== ARCHIVE RECOVERY DAEMON STARTED ==="

# State: track which phases have completed
STATE_FILE="/tmp/archive_recovery_state.json"

promote_phase() {
    log "Phase: Promotion (archive candidates → registry update)"
    cd "$REPO"
    source "$VENV"
    python3 scripts/archive_recovery_automation.py --promote --recency-days 180 2>&1 | tee -a "$LOG" || {
        log "ERROR: promotion phase failed"
        return 1
    }
}

unchecked_phase() {
    log "Phase: Unchecked pool scan (32K orgs with no website_status)"
    cd "$REPO"
    source "$VENV"
    python3 scripts/archive_recovery_automation.py --run-unchecked 2>&1 | tee -a "$LOG" || {
        log "ERROR: unchecked-pool launch failed"
        return 1
    }
}

main_loop() {
    log "Entering main loop (monitoring PID 3730466)..."

    while true; do
        if ! ps -p 3730466 > /dev/null 2>&1; then
            log "Dead-pool scan (PID 3730466) has completed"
            break
        fi
        sleep 60
    done

    log "Scan complete. Running automation pipeline..."

    # Run the full automation: retry + promote + unchecked
    cd "$REPO"
    source "$VENV"
    python3 scripts/archive_recovery_automation.py --monitor 2>&1 | tee -a "$LOG" || {
        log "ERROR: automation pipeline failed"
        return 1
    }

    log "=== ARCHIVE RECOVERY COMPLETE ==="
    log "Outcomes logged to DECISIONS.md"
    return 0
}

main_loop
