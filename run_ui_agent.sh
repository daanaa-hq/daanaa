#!/bin/bash
# Autonomous UI Improvement Loop
# Runs every hour, only when system is idle

cd ~/meritgiving
mkdir -p logs/feedback ui_improvements ui_backups

while true; do
    # Check if it's a good time (not during heavy compute)
    LOAD=$(cat /proc/loadavg | awk '{print $1}')
    CORES=$(nproc)
    LOAD_PCT=$(echo "$LOAD $CORES" | awk '{print ($1/$2)*100}')
    
    if (( $(echo "$LOAD_PCT < 50" | bc -l) )); then
        echo "[$(date)] System idle ($LOAD_PCT% load). Running UI agent..."
        python3 ui_agent.py >> logs/ui_agent.log 2>&1
    else
        echo "[$(date)] System busy ($LOAD_PCT% load). Skipping."
    fi
    
    # Run every hour
    sleep 3600
done
