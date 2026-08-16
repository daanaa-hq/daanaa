#!/bin/bash
# Monitor enrichment pipeline during 8pm-9am window
# Runs as: /loop 8pm-9am "bash scripts/monitor_enrichment_window.sh"

LOG_DIR="/home/akbar/meritgiving/logs"
ENRICH_LOG="$LOG_DIR/enrich_nightly.log"
GPU_LOG="$LOG_DIR/gpu_night.log"

# Get current hour (0-23), strip leading zeros to avoid octal interpretation
HOUR=$(date +%H | sed 's/^0//')

# Check if we're in the 8pm-9am window (20:00-09:00)
if [ "$HOUR" -ge 20 ] || [ "$HOUR" -lt 9 ]; then
  STATUS="🌙 Night window (enrichment active)"

  # Check enrichment process status
  if pgrep -f "enrich_batch.py" > /dev/null; then
    ENRICH_STATUS="✅ Enrichment batch running"
  else
    ENRICH_STATUS="⏸️  Enrichment batch idle"
  fi

  # Check GPU processes
  GPU_JOBS=$(pgrep -f "llama-server|generate_missions|reembed" | wc -l)
  if [ $GPU_JOBS -gt 0 ]; then
    GPU_STATUS="✅ GPU jobs: $GPU_JOBS processes"
  else
    GPU_STATUS="⏸️  GPU idle"
  fi

  # Get recent log activity
  ENRICH_RECENT=$(tail -1 "$ENRICH_LOG" 2>/dev/null | grep -o "FAILED\|completed\|Starting" || echo "—")
  GPU_RECENT=$(tail -1 "$GPU_LOG" 2>/dev/null | grep -o "FAILED\|complete\|starting\|stopped" || echo "—")

  echo "[$STATUS]"
  echo "  $ENRICH_STATUS (last: $ENRICH_RECENT)"
  echo "  $GPU_STATUS (last: $GPU_RECENT)"

else
  STATUS="☀️  Day window (enrichment paused)"
  echo "[$STATUS] Enrichment will resume at 8pm (20:00)"

  # Show daily summary
  YESTERDAY=$(date -d yesterday +%Y%m%d)
  ENRICH_YESTERDAY="$LOG_DIR/enrich_batch_$YESTERDAY.log"
  if [ -f "$ENRICH_YESTERDAY" ]; then
    LINES=$(wc -l < "$ENRICH_YESTERDAY")
    echo "  Last night: $LINES log lines"
  fi
fi
