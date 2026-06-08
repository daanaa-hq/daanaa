#!/bin/bash
# Deploy updated org files + search.db to droplet after monthly similar-orgs run.
# Usage: bash scripts/deploy_similar_orgs.sh

set -e
DROPLET="root@162.243.97.179"
LOCAL_ORGS="$HOME/meritgiving/precompute_output/orgs"
LOCAL_SEARCH_DB="$HOME/meritgiving/precompute_output/search.db"
REMOTE_BASE="/data/precompute/v1"

echo "=== Deploying similar orgs to droplet ==="
echo "Started: $(date)"
echo ""

# 1. Sync org files (only changed)
echo "Step 1/3: Syncing org files (changed only)..."
rsync -az --checksum --stats \
    "$LOCAL_ORGS/" \
    "$DROPLET:$REMOTE_BASE/orgs/" 2>&1 | grep -E "sent|received|files|speedup"

# 2. Upload search.db
echo "Step 2/3: Uploading search.db..."
scp "$LOCAL_SEARCH_DB" "$DROPLET:$REMOTE_BASE/search.db"

# 3. Restart API to clear file cache
echo "Step 3/3: Restarting API to clear cache..."
ssh "$DROPLET" "bash /opt/daanaa/restart.sh" | tail -2

echo ""
echo "=== Deploy complete: $(date) ==="
echo "Verify: https://daanaa.org/health"
