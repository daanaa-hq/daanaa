#!/bin/bash
# Weekly hidden gems rotation (Monday 7 AM)
# Generates fresh hidden gems set for directory landing, syncs to droplet

set -e

cd ~/meritgiving
source venv/bin/activate

LOG="/tmp/gem_rotation_$(date +%Y%m%d_%H%M%S).log"
echo "[$(date)] Starting weekly gem rotation..." | tee "$LOG"

# 1. Generate fresh hidden gems for this week
echo "[$(date)] Computing hidden gems..." | tee -a "$LOG"
python3 scripts/precompute_hidden_gems.py >> "$LOG" 2>&1

# 2. Sync to droplet
echo "[$(date)] Syncing gems to droplet..." | tee -a "$LOG"
if [ -d "precompute_output/browse/hidden_gems" ]; then
  rsync -avz --delete precompute_output/browse/hidden_gems/ \
    root@107.170.26.8:/data/precompute/v1/browse/hidden_gems/ >> "$LOG" 2>&1
  echo "[$(date)] ✓ Gem rotation complete" | tee -a "$LOG"
else
  echo "[$(date)] ✗ Gems directory not found" | tee -a "$LOG"
  exit 1
fi
