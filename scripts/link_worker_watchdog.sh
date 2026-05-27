#!/bin/bash
# Watchdog for donation_link_workers — restarts if stalled for > 30 min with no DB completions.
# Run via: nohup bash scripts/link_worker_watchdog.sh > logs/watchdog.log 2>&1 &

DB="$HOME/meritgiving/data/merit_registry.db"
LOG_DIR="$HOME/meritgiving/logs"
VENV="$HOME/meritgiving/venv"
SCRIPT="$HOME/meritgiving/scripts/donation_link_workers.py"
STALL_MINUTES=30

log() { echo "[$(date '+%H:%M:%S')] $*"; }

get_completed() {
  sqlite3 "$DB" "SELECT COUNT(*) FROM donate_work_queue WHERE completed_at IS NOT NULL;" 2>/dev/null
}

reset_claims() {
  sqlite3 "$DB" "UPDATE donate_work_queue SET claimed_at=NULL, claimed_by=NULL WHERE completed_at IS NULL AND claimed_at IS NOT NULL;" 2>/dev/null
  local n
  n=$(sqlite3 "$DB" "SELECT changes();" 2>/dev/null)
  [ "$n" -gt 0 ] && log "Reset $n stale claims"
}

start_workers() {
  local ts
  ts=$(date +%Y%m%d_%H%M%S)
  local logfile="$LOG_DIR/link_workers_${ts}.log"
  source "$VENV/bin/activate"
  nohup python3 "$SCRIPT" --workers 7 --threads 14 > "$logfile" 2>&1 &
  log "Started workers PID=$! log=$logfile"
}

kill_workers() {
  pkill -f "donation_link_workers" 2>/dev/null && log "Killed stalled workers"
}

log "Watchdog started — checking every 5 min, restart threshold ${STALL_MINUTES}m"

last_count=$(get_completed)
last_progress=$(date +%s)

while true; do
  sleep 300  # check every 5 minutes

  current_count=$(get_completed)
  now=$(date +%s)
  stall_secs=$(( now - last_progress ))

  if [ "$current_count" -gt "$last_count" ]; then
    log "Progress: $last_count → $current_count completed"
    last_count=$current_count
    last_progress=$now
  else
    stall_min=$(( stall_secs / 60 ))
    log "No progress for ${stall_min}m (completed=${current_count})"

    if [ "$stall_secs" -ge $(( STALL_MINUTES * 60 )) ]; then
      log "STALL DETECTED — restarting workers"
      kill_workers
      sleep 3
      reset_claims
      start_workers
      last_progress=$(date +%s)
    fi
  fi

  # Stop if queue is empty
  waiting=$(sqlite3 "$DB" "SELECT COUNT(*) FROM donate_work_queue WHERE completed_at IS NULL;" 2>/dev/null)
  if [ "$waiting" -eq 0 ]; then
    log "Queue empty — watchdog exiting"
    break
  fi
done
