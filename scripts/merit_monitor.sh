#!/bin/bash
echo "=========================================="
echo "MERITGIVING PIPELINE MONITOR"
echo "=========================================="
echo ""
echo "[SCREEN SESSIONS]"
screen -ls 2>/dev/null || echo "  No active screens."
echo ""
echo "[WORKER A — ProPublica Collector]"
PID=$(pgrep -f "merit_worker_a.py" || echo "")
if [ -n "$PID" ]; then
    echo "  Status: RUNNING (PID: $PID)"
    UP=$(ps -o etime= -p "$PID" 2>/dev/null | tr -d ' ')
    echo "  Uptime: $UP"
else
    echo "  Status: NOT RUNNING"
fi
LOG=~/meritgiving/logs/worker_a.log
if [ -f "$LOG" ]; then
    echo ""
    echo "[LATEST LOG ENTRIES]"
    tail -6 "$LOG" | sed 's/^/  /'
fi
DB=~/meritgiving/data/merit_state.db
if [ -f "$DB" ]; then
    echo ""
    echo "[QUEUE STATS]"
    sqlite3 "$DB" <<SQL | sed 's/^/  /'
SELECT 
    (SELECT COUNT(*) FROM propublica_queue WHERE status='pending') AS pending,
    (SELECT COUNT(*) FROM propublica_queue WHERE status='done') AS completed,
    (SELECT COUNT(*) FROM propublica_queue WHERE status='failed') AS failed,
    (SELECT COUNT(*) FROM propublica_queue) AS total;
SQL
fi
RAW=~/meritgiving/data/raw/orgs_raw.jsonl
if [ -f "$RAW" ]; then
    LINES=$(wc -l < "$RAW" 2>/dev/null | tr -d ' ')
    SIZE=$(du -h "$RAW" 2>/dev/null | cut -f1)
    echo ""
    echo "[RAW OUTPUT]"
    echo "  Records: ${LINES:-0}"
    echo "  Size: $SIZE"
fi
DONE=$(sqlite3 "$DB" "SELECT COUNT(*) FROM propublica_queue WHERE status='done';" 2>/dev/null || echo "0")
TOTAL=$(sqlite3 "$DB" "SELECT COUNT(*) FROM propublica_queue;" 2>/dev/null || echo "623694")
if [ "$DONE" -gt 0 ] 2>/dev/null; then
    REMAINING=$((TOTAL - DONE))
    HOURS=$(echo "scale=1; $REMAINING * 1.1 / 3600" | bc 2>/dev/null || echo "?")
    echo ""
    echo "[ETA]"
    echo "  Completed: $DONE / $TOTAL"
    echo "  Remaining: ~$REMAINING EINs"
    echo "  Est. time: ~${HOURS} hours"
fi
echo ""
echo "=========================================="
echo "Monitor commands:"
echo "  tail -f ~/meritgiving/logs/worker_a.log"
echo "  screen -r merit_a"
echo "=========================================="
