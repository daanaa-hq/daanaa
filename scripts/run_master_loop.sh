#!/bin/bash
cd ~/meritgiving
while true; do
    python3 merit_master.py >> logs/master_loop.log 2>&1
    echo "[$(date)] Cycle done. Sleeping 6 hours..." >> logs/master_loop.log
    sleep 21600  # 6 hours
done
