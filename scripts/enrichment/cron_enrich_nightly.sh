#!/bin/bash
# Nightly enrichment batch — exclusive GPU access during initial backlog clear.
# Cron: 0 20 * * * /home/akbar/meritgiving/scripts/cron_enrich_nightly.sh

BASE_DIR="/home/akbar/meritgiving"
LOG_FILE="$BASE_DIR/logs/enrich_batch_$(date +'%Y%m%d').log"
VENV="$BASE_DIR/venv/bin/python3"

{
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Starting enrichment batch (exclusive GPU mode)"

  cd "$BASE_DIR"
  bash scripts/gpu_night.sh start_exclusive

  source venv/bin/activate
  $VENV scripts/enrich_batch.py --workers 4 --batch-size 20

  if [ $? -eq 0 ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Enrichment batch completed"
  else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Enrichment batch FAILED"
  fi

} >> "$LOG_FILE" 2>&1
