#!/bin/bash
# Evening discovery batch — 8 PM daily
# Feeds high-value orgs to discovery daemon during GPU window (10pm-6am)
# Smaller batch than morning run (500 vs 1000) to stay responsive

set -e

LOG_DIR="$HOME/meritgiving/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/evening_discovery_batch.log"

{
  echo "[$(date)] Starting evening discovery batch..."
  
  cd "$HOME/meritgiving"
  source venv/bin/activate
  
  # Run orchestrator with smaller batch size (night optimization)
  python3 scripts/nonprofit_discovery_orchestrator.py \
    --batch-size 500 \
    --limit 1500 \
    2>&1 | tee -a "$LOG_FILE"
  
  if [ $? -eq 0 ]; then
    echo "[$(date)] ✅ Evening batch complete"
  else
    echo "[$(date)] ⚠️ Evening batch warning (see logs)"
  fi
} >> "$LOG_FILE" 2>&1

