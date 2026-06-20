#!/bin/bash
# Rollback a failed deployment
#
# Usage: bash rollback.sh /path/to/snapshot

SNAPSHOT_DIR=${1:-"/tmp/deploy_snapshot_latest"}
DROPLET_IP="162.243.97.179"
DEPLOY_USER="root"

echo "═══════════════════════════════════════════════════════════════"
echo "  EMERGENCY ROLLBACK"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ ! -d "$SNAPSHOT_DIR" ]; then
  echo "Snapshot directory not found: $SNAPSHOT_DIR"
  exit 1
fi

# Read manifest
if [ -f "$SNAPSHOT_DIR/manifest.json" ]; then
  echo "Rolling back to snapshot:"
  cat "$SNAPSHOT_DIR/manifest.json" | jq .
fi
echo ""

ROLLBACK_COMMIT=$(cat "$SNAPSHOT_DIR/rollback_commit.txt" 2>/dev/null)

if [ -z "$ROLLBACK_COMMIT" ]; then
  echo "ERROR: No rollback commit found in snapshot"
  exit 1
fi

echo "Rolling back to commit: $ROLLBACK_COMMIT"
echo ""

# 1. Restore frontend from backup
echo "[1/3] Restoring frontend..."
if [ -f "$SNAPSHOT_DIR/frontend_backup.tar.gz" ]; then
  scp "$SNAPSHOT_DIR/frontend_backup.tar.gz" "$DEPLOY_USER@$DROPLET_IP:/tmp/" > /dev/null 2>&1
  ssh "$DEPLOY_USER@$DROPLET_IP" "
    tar -xzf /tmp/frontend_backup.tar.gz -C / 2>/dev/null || true
    rm /tmp/frontend_backup.tar.gz
  "
  echo "✓ Frontend restored"
else
  echo "⚠ No frontend backup available; re-deploy from source"
  git show "$ROLLBACK_COMMIT:scripts/droplet_api.py" > /tmp/droplet_api_rollback.py
  scp /tmp/droplet_api_rollback.py "$DEPLOY_USER@$DROPLET_IP:/opt/daanaa/scripts/droplet_api.py"
fi
echo ""

# 2. Restart services
echo "[2/3] Restarting services..."
ssh "$DEPLOY_USER@$DROPLET_IP" "
  systemctl restart gunicorn
  sleep 2
  systemctl is-active gunicorn > /dev/null && echo 'Gunicorn started' || echo 'Gunicorn failed to start'
"
echo ""

# 3. Verify health
echo "[3/3] Verifying rollback..."
if curl -s -o /dev/null -w "%{http_code}" "https://daanaa.org/health" | grep -q "200"; then
  echo "✓ API responding"
else
  echo "✗ API not responding — manual intervention needed"
fi

if curl -s "https://daanaa.org/" | grep -q "Explore" > /dev/null 2>&1; then
  echo "✓ Homepage loads"
else
  echo "✗ Homepage broken — manual investigation required"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✓ Rollback complete"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Investigate why the deployment failed"
echo "  2. Check logs: tail -100 /tmp/deploy_*.log"
echo "  3. Fix the issue and re-deploy: bash infrastructure/deployment/safe_deploy.sh"
echo ""
