#!/bin/bash
# Deploy updated browse files to droplet after weekly precompute.
# Usage: bash scripts/deploy_browse.sh
# Handles both state-specific and ALL-state browse files.

set -e
DROPLET="root@162.243.97.179"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"  # passphrase-free automation key (see LESSONS.md 2026-07-05)
SSH_OPTS="-i $SSH_KEY -o ConnectTimeout=20 -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
LOCAL_BROWSE="$HOME/meritgiving/precompute_output/browse"
REMOTE_BASE="/data/precompute/v1"

echo "=== Deploying browse files to droplet ==="
echo "Started: $(date)"
echo ""

# 1. Sync browse files (only changed)
echo "Step 1/2: Syncing browse files (changed only)..."
rsync -e "ssh $SSH_OPTS" -az --checksum --stats \
    "$LOCAL_BROWSE/" \
    "$DROPLET:$REMOTE_BASE/browse/" 2>&1 | grep -E "sent|received|files|speedup"

# 2. Restart the systemd-managed API to clear in-memory cache.
# 2026-07-05: /opt/daanaa/restart.sh is stale — it launches a second,
# unmanaged gunicorn on 0.0.0.0:5000 that collides with the systemd unit
# already bound to 127.0.0.1:5000, fails to bind, and silently no-ops while
# its own health check still hits the untouched old process. That left a
# freshly-deployed browse regen invisible to real traffic for ~1h before
# being caught by manual verification. Use systemctl directly instead.
echo "Step 2/2: Restarting daanaa.service to clear cache..."
ssh $SSH_OPTS "$DROPLET" "systemctl restart daanaa && sleep 4 && curl -s http://localhost:5000/health"

echo ""
echo "=== Deploy complete: $(date) ==="
echo "Verify: https://daanaa.org/api/organizations?ntee=P&page=1"
