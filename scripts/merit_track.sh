#!/bin/bash
cd ~/meritgiving
source venv/bin/activate 2>/dev/null

DB=data/merit_state.db
LOG=logs/worker_a.log

echo "=========================================="
echo "MERITGIVING PROGRESS TRACKER"
echo "Updated: $(date)"
echo "=========================================="

# Check worker status
if pgrep -f "merit_worker_a.py" > /dev/null; then
    PID=$(pgrep -f "merit_worker_a.py" | head -1)
    UP=$(ps -o etime= -p "$PID" 2>/dev/null | tr -d ' ')
    echo ""
    echo "[PIPELINE STATUS]"
    echo "  Worker: RUNNING (PID: $PID)"
    echo "  Uptime: $UP"
else
    echo ""
    echo "[PIPELINE STATUS]"
    echo "  Worker: STOPPED"
fi

# Stats from DB with timeout/lock handling
if [ -f "$DB" ]; then
    # Use timeout to avoid hanging on locked DB
    STATS=$(timeout 5 sqlite3 "$DB" <<SQL 2>/dev/null
SELECT 
    (SELECT COUNT(*) FROM propublica_queue WHERE status='done') as done,
    (SELECT COUNT(*) FROM propublica_queue WHERE status='pending') as pending,
    (SELECT COUNT(*) FROM propublica_queue WHERE status='failed') as failed,
    (SELECT COUNT(*) FROM propublica_queue) as total;
SQL
)
    if [ -n "$STATS" ]; then
        DONE=$(echo "$STATS" | cut -d'|' -f1)
        PENDING=$(echo "$STATS" | cut -d'|' -f2)
        FAILED=$(echo "$STATS" | cut -d'|' -f3)
        TOTAL=$(echo "$STATS" | cut -d'|' -f4)
        
        # Fallback if queries return empty
        DONE=${DONE:-0}
        PENDING=${PENDING:-0}
        FAILED=${FAILED:-0}
        TOTAL=${TOTAL:-623694}
        
        echo ""
        echo "[QUEUE STATS]"
        echo "  Total:     $TOTAL"
        echo "  Completed: $DONE"
        echo "  Pending:   $PENDING"
        echo "  Failed:    $FAILED"
        
        # ETA math
        if [ "$TOTAL" -gt 0 ] 2>/dev/null && [ "$DONE" -gt 0 ] 2>/dev/null; then
            PERCENT=$(echo "scale=1; $DONE * 100 / $TOTAL" | bc 2>/dev/null || echo "0.0")
            REMAINING=$((TOTAL - DONE))
            HOURS=$(echo "scale=1; $REMAINING * 1.3 / 3600" | bc 2>/dev/null || echo "?")
            echo ""
            echo "[ETA]"
            echo "  Progress: ${PERCENT}%"
            echo "  Remaining: ~$REMAINING EINs"
            echo "  Est. time: ~${HOURS} hours"
        fi
    fi
fi

# Raw file
if [ -f data/raw/orgs_raw.jsonl ]; then
    LINES=$(wc -l < data/raw/orgs_raw.jsonl 2>/dev/null | tr -d ' ')
    SIZE=$(du -h data/raw/orgs_raw.jsonl 2>/dev/null | cut -f1)
    echo ""
    echo "[RAW OUTPUT]"
    echo "  Records: ${LINES:-0}"
    echo "  Size: $SIZE"
fi

# Last log line
if [ -f "$LOG" ]; then
    LAST=$(tail -1 "$LOG" 2>/dev/null | sed 's/^\[[^]]*\] //' || echo "no log")
    echo ""
    echo "[LAST LOG]"
    echo "  $LAST"
fi

echo ""
echo "=========================================="
