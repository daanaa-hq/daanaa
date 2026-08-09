#!/bin/bash
# Weekly hidden gems reshuffling (Monday 02:00 UTC)
# Regenerates precomputed files with new ISO-week seed, syncs to droplet

cd /home/akbar/meritgiving

# Generate this week's gems (reuses precompute_hidden_gems.py)
python3 scripts/precompute_hidden_gems.py 2>&1 | tail -5

# Sync to droplet
rsync -avz precompute_output/browse/hidden_gems/ root@107.170.26.8:/data/precompute/v1/browse/hidden_gems/ --delete

echo "Hidden gems rotated $(date)" >> /home/akbar/.logs/gems_rotation.log
