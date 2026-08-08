#!/bin/bash
# Deploy updated org files + search.db to droplet after monthly similar-orgs run.
# Usage: bash scripts/deploy_similar_orgs.sh

set -e
DROPLET="root@107.170.26.8"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"  # passphrase-free automation key (see LESSONS.md 2026-07-05)
SSH_OPTS="-i $SSH_KEY -o ConnectTimeout=20 -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
LOCAL_ORGS="$HOME/meritgiving/precompute_output/orgs"
LOCAL_SEARCH_DB="$HOME/meritgiving/precompute_output/search.db"
REMOTE_BASE="/data/precompute/v1"

echo "=== Deploying similar orgs to droplet ==="
echo "Started: $(date)"
echo ""

# 1. Sync org files (only changed)
echo "Step 1/3: Syncing org files (changed only)..."
rsync -e "ssh $SSH_OPTS" -az --checksum --stats \
    "$LOCAL_ORGS/" \
    "$DROPLET:$REMOTE_BASE/orgs/" 2>&1 | grep -E "sent|received|files|speedup"

# 2. Upload search.db
echo "Step 2/3: Uploading search.db..."
scp -i "$SSH_KEY" -o ConnectTimeout=20 -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
    "$LOCAL_SEARCH_DB" "$DROPLET:$REMOTE_BASE/search.db"

# 3. Restart the systemd-managed API to clear file cache.
# 2026-07-05: /opt/daanaa/restart.sh is stale — it launches a second,
# unmanaged gunicorn on 0.0.0.0:5000 that collides with the systemd unit
# already bound to 127.0.0.1:5000, fails to bind, and silently no-ops
# (see scripts/deploy_browse.sh for the same fix + full explanation).
echo "Step 3/3: Restarting daanaa.service to clear cache..."
ssh $SSH_OPTS "$DROPLET" "systemctl restart daanaa && sleep 4 && curl -s http://localhost:5000/health"

echo ""
echo "=== Deploy complete: $(date) ==="
echo "Verify: https://daanaa.org/health"
