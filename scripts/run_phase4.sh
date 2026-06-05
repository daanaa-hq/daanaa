#!/usr/bin/env bash
# run_phase4.sh — Run Phase 4 semantic verification, waiting for embed server first.
# This ensures the embedding service (port 11436) is healthy before Phase 4 starts.
# Usage: bash run_phase4.sh [timeout_seconds]

set -u

TIMEOUT="${1:-300}"  # Wait up to 5 minutes for embed server
VENV="/home/akbar/meritgiving/venv/bin/python3"
SCRIPT="/home/akbar/meritgiving/scripts/web_finder_agent.py"
LOG_DIR="/home/akbar/meritgiving/logs"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

log() {
  msg="$1"
  echo "[$(ts)] $msg"
}

# Wait for embed server to be healthy
log "Waiting for embed server on :11436 (timeout: ${TIMEOUT}s)..."
start_time=$(date +%s)
while true; do
  if curl -s "http://127.0.0.1:11436/health" 2>/dev/null | grep -q '"status":"ok"'; then
    log "✓ Embed server healthy"
    break
  fi

  elapsed=$(($(date +%s) - start_time))
  if [ $elapsed -ge "$TIMEOUT" ]; then
    log "✗ Embed server failed to start within ${TIMEOUT}s"
    log "Cannot proceed with Phase 4 — skipping"
    exit 1
  fi

  sleep 2
done

# Run Phase 4
log "Starting Phase 4 semantic verification..."
"$VENV" "$SCRIPT" >> "$LOG_DIR/phase4.log" 2>&1
exit_code=$?

if [ $exit_code -eq 0 ]; then
  log "Phase 4 completed successfully"
else
  log "Phase 4 exited with code $exit_code"
fi

exit $exit_code
