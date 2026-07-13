#!/bin/bash
# Enrichment loop: runs continuous batches from 8pm-8am CST
# Each batch processes all orgs, then restarts if time allows before 8am cutoff
# Logs to: /home/akbar/meritgiving/logs/enrichment-loop-$(date +%Y%m%d).log

set -e
REPO="/home/akbar/meritgiving"
VENV="$REPO/venv/bin/activate"
LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"

# Single-instance guard: if a loop is already running (e.g. started manually
# at 8pm), the 2am cron invocation exits instead of doubling up workers.
LOCK_FILE="/tmp/daanaa_enrichment_loop.lock"
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Another enrichment loop is already running — exiting." >> "$LOG_DIR/enrichment-loop-$(date +%Y%m%d).log"
  exit 0
fi

LOG_FILE="$LOG_DIR/enrichment-loop-$(date +%Y%m%d).log"
CUTOFF_HOUR=8  # Stop at 8am CST (stop processing new batches)

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== ENRICHMENT LOOP STARTED (8pm-8am CST window) ==="
log "Cutoff: Stop new batches at $CUTOFF_HOUR:00am CST"
log "Logs: $LOG_FILE"

BATCH_COUNT=0
while true; do
  CURRENT_HOUR=$(date +%H)
  CURRENT_MIN=$(date +%M)

  # Stop if between 8am-7:59pm CST (daytime, outside enrichment window)
  # Continue if between 8pm-7:59am CST (nighttime, in enrichment window)
  if [ "$CURRENT_HOUR" -ge "$CUTOFF_HOUR" ] && [ "$CURRENT_HOUR" -lt 20 ]; then
    log "=== CUTOFF REACHED ($CURRENT_HOUR:$CURRENT_MIN CST) ==="
    log "Stopping enrichment loop. Completed $BATCH_COUNT batches."
    break
  fi

  BATCH_COUNT=$((BATCH_COUNT + 1))
  log "--- BATCH $BATCH_COUNT START ---"

  # Run enrichment with 8 workers
  cd "$REPO"
  source "$VENV"
  export AWS_PROFILE=daanaa-enrichment

  BATCH_START=$(date +%s)
  python3 scripts/enrich_batch.py --workers 8 2>&1 | tee -a "$LOG_FILE"
  BATCH_END=$(date +%s)
  BATCH_DURATION=$(( BATCH_END - BATCH_START ))

  log "--- BATCH $BATCH_COUNT COMPLETE (${BATCH_DURATION}s) ---"
  log ""

  # Check time again before looping (8am-7:59pm = daytime cutoff)
  CURRENT_HOUR=$(date +%H)
  CURRENT_MIN=$(date +%M)
  if [ "$CURRENT_HOUR" -ge "$CUTOFF_HOUR" ] && [ "$CURRENT_HOUR" -lt 20 ]; then
    log "=== CUTOFF CHECK: $CURRENT_HOUR:$CURRENT_MIN CST (daytime) ==="
    log "Stopping loop. Completed $BATCH_COUNT batches."
    break
  fi

  log "Starting next batch..."
  sleep 2
done

log "=== ENRICHMENT LOOP ENDED ==="
log "Total batches completed: $BATCH_COUNT"
log "Session duration: $(($(date +%s) - $(date +%s -d "$(date +%H:%M:%S -d '8 hours ago')")))s"
