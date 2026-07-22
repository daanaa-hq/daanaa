#!/bin/bash
# Monitor the running mission-generation batch
# Usage: ./monitor_mission_batch.sh [interval_seconds]

INTERVAL=${1:-60}
LOG=$(ls -t /home/akbar/meritgiving/logs/mission_batch_qwen3_*.log 2>/dev/null | head -1)

if [ -z "$LOG" ]; then
    echo "No mission batch log found"
    exit 1
fi

echo "Monitoring: $LOG"
echo "Refresh interval: ${INTERVAL}s (Ctrl+C to exit)"
echo ""

while true; do
    clear
    echo "=== Mission Batch Progress ==="
    tail -3 "$LOG"
    echo ""
    ps aux | grep -E "[p]ython3.*generate_missions.*qwen3" | awk '{print "PID:", $2, "CPU:", $3"%, MEM:", $4"%"}'
    
    if ! pgrep -f "python3.*generate_missions.*qwen3" > /dev/null; then
        echo ""
        echo "⚠️  Job appears to have finished or crashed. Check log:"
        tail -10 "$LOG"
        exit 0
    fi
    
    sleep "$INTERVAL"
done
