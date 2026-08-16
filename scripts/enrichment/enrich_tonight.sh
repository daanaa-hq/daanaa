#!/bin/bash
set -e
cd /home/akbar/meritgiving
source venv/bin/activate
export AWS_PROFILE=daanaa-enrichment

LOG_FILE="logs/enrichment-tonight-$(date +%Y%m%d).log"
BATCH=1

{
  echo "[$(date)] Continuous enrichment: Now until 8 AM CST"
  while true; do
    HOUR=$(date +%H)
    # Run if: 6-7 PM (18-19) or 8 PM-7 AM (20-23, 0-7)
    # Stop if: 8 AM-5:59 PM (8-17)
    if [ "$HOUR" -ge 8 ] && [ "$HOUR" -lt 18 ]; then
      echo "[$(date)] Daytime, stopping enrichment"
      break
    fi
    
    echo "[$(date)] Batch $BATCH..."
    python3 scripts/enrich_batch.py --workers 8 2>&1 | grep "Layer 2 complete" || true
    BATCH=$((BATCH + 1))
    sleep 1
  done
  echo "[$(date)] Enrichment session complete"
} | tee "$LOG_FILE"
