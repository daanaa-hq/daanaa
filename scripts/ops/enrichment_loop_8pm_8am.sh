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

# Fixed 2026-08-21 (LESSONS.md same date): both scripts/enrichment_preflight.py
# and scripts/enrich_batch.py below referenced stale pre-2026-08-12-migration
# paths. Confirmed via logs/enrichment-loop-20260821.log: today's 2am run
# aborted immediately at the preflight check ("No such file or directory")
# -- the entire nightly enrichment window (8pm-8am) has likely been dead
# since the migration, over a week. Found via a mechanical repo-wide sweep
# for broken scripts/X.py references, cross-checked against which callers
# are actually cron-scheduled.
#
# Pre-flight checks — exit early if infrastructure not ready (prevents wasting 8 hours on connection errors)
log ""
log "Running pre-flight checks..."
cd "$REPO"
source "$VENV"
if ! python3 scripts/core/enrichment_preflight.py --strict >> "$LOG_FILE" 2>&1; then
  log "❌ PRE-FLIGHT CHECKS FAILED — Aborting enrichment loop"
  log "Inference servers or database not ready. Check and restart manually."
  exit 1
fi
log "✅ Pre-flight checks passed"
log ""

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
  # Hard deadline: a batch started before cutoff must not RUN past it either.
  # 2026-07-18 incident: a pre-8am batch ran until 9:26am while day-mode cron
  # shut down the embedding server (9:05am) underneath it — 90 minutes of
  # connection-refused errors on every org, 45 useful rows from 1,740.
  # timeout sends TERM at the deadline; enrich_batch checkpoints as it goes,
  # so a mid-batch stop loses nothing already flushed.
  NOW_EPOCH=$(date +%s)
  CUTOFF_EPOCH=$(date -d "today ${CUTOFF_HOUR}:00" +%s)
  # If we're in the evening (before midnight), the cutoff is tomorrow morning.
  if [ "$NOW_EPOCH" -ge "$CUTOFF_EPOCH" ]; then
    CUTOFF_EPOCH=$(date -d "tomorrow ${CUTOFF_HOUR}:00" +%s)
  fi
  SECONDS_LEFT=$(( CUTOFF_EPOCH - NOW_EPOCH ))
  log "Batch deadline: ${SECONDS_LEFT}s until ${CUTOFF_HOUR}:00 cutoff"
  timeout --signal=TERM "${SECONDS_LEFT}s" \
    python3 scripts/enrichment/enrich_batch.py --workers 8 2>&1 | tee -a "$LOG_FILE"
  BATCH_STATUS=${PIPESTATUS[0]}
  if [ "$BATCH_STATUS" = "124" ]; then
    log "=== BATCH KILLED AT CUTOFF (deadline reached — this is by design) ==="
  fi
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
