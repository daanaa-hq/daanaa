#!/bin/bash
# Monitor enrichment health — run after overnight windows (morning check)
# Verifies: systemd services healthy, logs have no errors, enrichment completed

set -u

LOG_DIR="$HOME/meritgiving/logs"
DB="$HOME/meritgiving/data/merit_registry.db"

echo "=== ENRICHMENT HEALTH CHECK ==="
echo "Date: $(date)"
echo

echo "--- Systemd Services ---"
systemctl status daanaa-embed-server.service daanaa-qwen-watchdog.service --no-pager 2>&1 | grep -E "Active:|ExecStart|Process"
echo

echo "--- Enrichment Process Health ---"
if pgrep -f "enrich_batch" >/dev/null; then
  echo "⚠ enrich_batch still running (may be normal for large batch)"
  pgrep -f "enrich_batch" | head -1 | xargs ps -p
else
  echo "✓ enrich_batch not running"
fi
echo

echo "--- Recent Enrichment Log (last 20 lines) ---"
LATEST_LOG=$(ls -t "$LOG_DIR"/enrichment-loop-*.log 2>/dev/null | head -1)
if [ -f "$LATEST_LOG" ]; then
  echo "Log: $LATEST_LOG"
  tail -20 "$LATEST_LOG"
else
  echo "No enrichment log found"
fi
echo

echo "--- Errors in Last 24h ---"
if [ -f "$LATEST_LOG" ]; then
  ERROR_COUNT=$(grep -c "ERROR" "$LATEST_LOG" 2>/dev/null || echo 0)
  if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠ $ERROR_COUNT errors found:"
    grep "ERROR" "$LATEST_LOG" | head -5
  else
    echo "✓ No errors"
  fi
else
  echo "No log to check"
fi
echo

echo "--- Last 24h Enrichment Stats ---"
sqlite3 "$DB" "
SELECT enrichment_type, COUNT(*) as count, MAX(created_at) as last_run
FROM enrichment_run
WHERE created_at > datetime('now', '-24 hours')
GROUP BY 1
ORDER BY 2 DESC;
" 2>/dev/null || echo "DB query failed"
echo

echo "--- Disk & Inference Server Health ---"
DISK_FREE=$(df ~ | tail -1 | awk '{printf "%.0f GB", $4/1024/1024}')
echo "Free disk: $DISK_FREE"
echo "Embed server (:11436): $(curl -s http://localhost:11436/health 2>/dev/null | jq '.status' || echo 'unreachable')"
echo "Qwen server (:11437): $(curl -s http://localhost:11437/health 2>/dev/null | jq '.status' || echo 'unreachable')"
echo

echo "=== END HEALTH CHECK ==="
