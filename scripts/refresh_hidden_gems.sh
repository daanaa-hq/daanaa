#!/bin/bash
# Weekly hidden-gems rotation: regenerate the gem browse pages with a fresh
# weekly shuffle, ship them to the droplet, and clear the API cache.
# Runs Mondays via cron. Keeps the directory landing fresh with no app changes.
# Usage: bash scripts/refresh_hidden_gems.sh

set -e
DROPLET="root@162.243.97.179"
SSH_KEY="$HOME/.ssh/daanaa_do"
LOCAL_GEMS="$HOME/meritgiving/precompute_output/browse/hidden_gems"
REMOTE_GEMS="/data/precompute/v1/browse/hidden_gems"

cd "$HOME/meritgiving"

echo "=== Hidden-gems weekly refresh: $(date) ==="

# 1. Regenerate the weekly-shuffled gem pages (CWD=repo root for DB path;
#    scripts/ is on sys.path[0] so the precompute_browse import resolves).
echo "Step 1/3: precompute..."
PYTHONPATH=scripts venv/bin/python3 scripts/precompute_hidden_gems.py

# 2. Ship the gem pages (changed only). --delete drops stale pages if the gem
#    count shrank week-over-week.
echo "Step 2/3: rsync to droplet..."
rsync -az --delete -e "ssh -i $SSH_KEY" "$LOCAL_GEMS/" "$DROPLET:$REMOTE_GEMS/"

# 3. Clear the API in-memory cache so the new week's order is served.
echo "Step 3/3: restart API..."
ssh -i "$SSH_KEY" "$DROPLET" "systemctl restart daanaa" || true

echo "=== Done: $(date) ==="
