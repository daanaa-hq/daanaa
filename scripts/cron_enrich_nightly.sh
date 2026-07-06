#!/bin/bash
# Nightly enrichment batch cron job (Task 8)
#
# Runs at 8 PM each night to enrich 1000+ organizations with cause tags and websites.
# Uses the EnrichmentBatch orchestrator from scripts/enrich_batch.py with 4 workers.
#
# Installation (manual, not automated):
#   crontab -e
#   0 20 * * * /home/akbar/meritgiving/scripts/cron_enrich_nightly.sh >> /home/akbar/meritgiving/logs/enrich_batch_$(date +'%Y%m%d').log 2>&1
#
# Environment:
#   - Requires llama-server on port 11437 (Qwen2.5-32B)
#   - Requires llama-server on port 11436 (mxbai-embed-large)
#   - Requires ~/meritgiving/venv activated
#
# Logs:
#   - Output: /home/akbar/meritgiving/logs/enrich_batch_<YYYYMMDD>.log

BASE_DIR="/home/akbar/meritgiving"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/enrich_batch_$(date +'%Y%m%d').log"
VENV="$BASE_DIR/venv/bin/python3"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

{
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Starting enrichment batch"

  cd "$BASE_DIR"
  source venv/bin/activate

  $VENV scripts/enrich_batch.py --workers 4 --batch-size 20

  if [ $? -eq 0 ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✓ Enrichment batch completed"
  else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✗ Enrichment batch FAILED"
    exit 1
  fi

} >> "$LOG_FILE" 2>&1
