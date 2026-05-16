#!/bin/bash
echo "=========================================="
echo "MERITGIVING — ALL AGENTS STATUS"
echo "Updated: $(date)"
echo "=========================================="

echo ""
echo "[AGENT A — ProPublica Collector]"
if pgrep -f "merit_worker_a.py" > /dev/null; then
    PID=$(pgrep -f "merit_worker_a.py" | head -1)
    UP=$(ps -o etime= -p "$PID" 2>/dev/null | tr -d ' ')
    echo "  Status: RUNNING (PID: $PID, Uptime: $UP)"
else
    echo "  Status: STOPPED"
fi
if [ -f ~/meritgiving/logs/worker_a.log ]; then
    tail -1 ~/meritgiving/logs/worker_a.log | sed 's/^/  Last: /'
fi

echo ""
echo "[AGENT C — CPU Analytics]"
if pgrep -f "merit_worker_c.py" > /dev/null; then
    echo "  Status: RUNNING"
else
    echo "  Status: IDLE"
fi
if [ -f ~/meritgiving/logs/worker_c.log ]; then
    tail -1 ~/meritgiving/logs/worker_c.log | sed 's/^/  Last: /'
fi

echo ""
echo "[AGENT D — GPU NTEE Classifier]"
if pgrep -f "merit_worker_d.py" > /dev/null; then
    echo "  Status: RUNNING"
else
    echo "  Status: IDLE"
fi
if [ -f ~/meritgiving/logs/worker_d.log ]; then
    tail -1 ~/meritgiving/logs/worker_d.log | sed 's/^/  Last: /'
fi

DB=~/meritgiving/data/merit_state.db
if [ -f "$DB" ]; then
    echo ""
    echo "[QUEUE — Worker A]"
    sqlite3 "$DB" "SELECT '  Done: '||COUNT(*) FROM propublica_queue WHERE status='done';" 2>/dev/null
    sqlite3 "$DB" "SELECT '  Left: '||COUNT(*) FROM propublica_queue WHERE status='pending';" 2>/dev/null
    sqlite3 "$DB" "SELECT '  Failed: '||COUNT(*) FROM propublica_queue WHERE status='failed';" 2>/dev/null
fi

echo ""
echo "=========================================="
echo "Attach commands:"
echo "  screen -r merit_a   # ProPublica"
echo "  screen -r merit_c   # Analytics"
echo "  screen -r merit_d   # GPU Classifier"
echo "=========================================="
