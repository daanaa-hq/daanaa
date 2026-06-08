#!/bin/bash
# Deploy updated browse files to droplet after weekly precompute.
# Usage: bash scripts/deploy_browse.sh
# Handles both state-specific and ALL-state browse files.

set -e
DROPLET="root@162.243.97.179"
LOCAL_BROWSE="$HOME/meritgiving/precompute_output/browse"
REMOTE_BASE="/data/precompute/v1"

echo "=== Deploying browse files to droplet ==="
echo "Started: $(date)"
echo ""

# 1. Sync browse files (only changed)
echo "Step 1/2: Syncing browse files (changed only)..."
rsync -az --checksum --stats \
    "$LOCAL_BROWSE/" \
    "$DROPLET:$REMOTE_BASE/browse/" 2>&1 | grep -E "sent|received|files|speedup"

# 2. Restart API to clear in-memory cache (multi_cache)
echo "Step 2/2: Restarting API to clear cache..."
ssh "$DROPLET" "bash /opt/daanaa/restart.sh" | tail -2

echo ""
echo "=== Deploy complete: $(date) ==="
echo "Verify: https://daanaa.org/api/organizations?ntee=P&page=1"
