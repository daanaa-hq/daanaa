#!/usr/bin/env bash
# launch_phase4_bg.sh — Launch Phase 4 in background with health checks
# Polls for embed server, then starts phase4_semantic_verification.py
# Logs to /tmp/phase4_progress.log + syslog
# Usage: bash launch_phase4_bg.sh [--limit 50000] [--workers 16]

set -u

VENV="/home/akbar/meritgiving/venv/bin/python3"
SCRIPT="/home/akbar/meritgiving/scripts/phase4_semantic_verification.py"
PROGRESS_LOG="/tmp/phase4_progress.log"
PID_FILE="/tmp/phase4.pid"

# Parse args
LIMIT=10000
WORKERS=8
DRY_RUN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit) LIMIT="$2"; shift 2 ;;
        --workers) WORKERS="$2"; shift 2 ;;
        --dry-run) DRY_RUN="--dry-run"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

ts() { date '+%Y-%m-%d %H:%M:%S'; }

log() {
    msg="$1"
    echo "[$(ts)] $msg" | tee -a "$PROGRESS_LOG"
}

# Check if already running
if [ -f "$PID_FILE" ]; then
    old_pid=$(cat "$PID_FILE")
    if kill -0 "$old_pid" 2>/dev/null; then
        log "Phase 4 already running (PID: $old_pid)"
        exit 0
    else
        log "Stale PID file; removing"
        rm -f "$PID_FILE"
    fi
fi

# Clear old log
> "$PROGRESS_LOG"
log "Phase 4 launcher started"

# Wait for embed server
log "Waiting for embed server on :11436..."
TIMEOUT=300
START_TIME=$(date +%s)
while true; do
    if curl -s "http://127.0.0.1:11436/health" 2>/dev/null | grep -q '"status":"ok"'; then
        log "✓ Embed server healthy"
        break
    fi

    ELAPSED=$(($(date +%s) - START_TIME))
    if [ $ELAPSED -ge $TIMEOUT ]; then
        log "✗ Embed server failed to start within ${TIMEOUT}s"
        exit 1
    fi

    sleep 2
done

# Launch in background
log "Starting Phase 4 (limit=$LIMIT, workers=$WORKERS)..."
nohup "$VENV" "$SCRIPT" --limit "$LIMIT" --workers "$WORKERS" $DRY_RUN >> "$PROGRESS_LOG" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

log "Phase 4 launched in background (PID: $PID)"
log "Progress: tail -f $PROGRESS_LOG"

# Brief monitoring (first 5 minutes)
for i in {1..30}; do
    sleep 10
    if ! kill -0 "$PID" 2>/dev/null; then
        EXIT_CODE=$?
        log "Phase 4 exited with code $EXIT_CODE"
        rm -f "$PID_FILE"
        exit $EXIT_CODE
    fi
    tail -1 "$PROGRESS_LOG"
done

log "Phase 4 still running; detaching monitor"
exit 0
