#!/bin/bash
# Safe deployment to droplet with automatic rollback
#
# Deploys frontend + API changes to production with:
#   1. Health check before deploy
#   2. Backup current state (snapshots deployed commit)
#   3. Deploy new code
#   4. Verify new version is live
#   5. Auto-rollback if checks fail

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DROPLET_IP="162.243.97.179"
DEPLOY_USER="root"
DEPLOY_LOG="/tmp/deploy_$(date +%s).log"

echo "═══════════════════════════════════════════════════════════════"
echo "  SAFE DEPLOYMENT TO PRODUCTION"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Log: $DEPLOY_LOG"
echo ""

# 0. Pre-deployment checks
echo "[0/5] Running pre-deployment checks..."
if ! bash infrastructure/deployment/pre_deploy_checks.sh >> "$DEPLOY_LOG" 2>&1; then
  echo -e "${RED}Pre-deployment checks failed${NC}"
  exit 1
fi
echo -e "${GREEN}✅ Checks passed${NC}"
echo ""

# 1. Capture current state (for rollback)
echo "[1/5] Snapshotting current production state..."
SNAPSHOT_DIR="/tmp/deploy_snapshot_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SNAPSHOT_DIR"
cat > "$SNAPSHOT_DIR/manifest.json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit_before": "$(git rev-parse HEAD)",
  "branch": "$(git branch --show-current)"
}
EOF

# Backup droplet state
ssh "$DEPLOY_USER@$DROPLET_IP" "
  echo '$(git rev-parse HEAD)' > /tmp/rollback_commit.txt
  tar -czf /tmp/frontend_backup.tar.gz /opt/daanaa/frontend/dist/ 2>/dev/null || true
" >> "$DEPLOY_LOG" 2>&1

scp "$DEPLOY_USER@$DROPLET_IP:/tmp/rollback_commit.txt" "$SNAPSHOT_DIR/" >> "$DEPLOY_LOG" 2>&1
scp "$DEPLOY_USER@$DROPLET_IP:/tmp/frontend_backup.tar.gz" "$SNAPSHOT_DIR/" >> "$DEPLOY_LOG" 2>&1

ROLLBACK_COMMIT=$(cat "$SNAPSHOT_DIR/rollback_commit.txt" 2>/dev/null || echo "unknown")
echo -e "${GREEN}✅ Snapshot created${NC} (rollback: $ROLLBACK_COMMIT)"
echo ""

# 2. Deploy frontend
echo "[2/5] Deploying frontend assets..."
if rsync -avz --delete frontend/dist/ "$DEPLOY_USER@$DROPLET_IP:/opt/daanaa/frontend/dist/" >> "$DEPLOY_LOG" 2>&1; then
  echo -e "${GREEN}✅ Frontend synced${NC}"
else
  echo -e "${RED}❌ Frontend sync failed${NC}"
  exit 1
fi
echo ""

# 3. Deploy API (if changed)
echo "[3/5] Checking for API changes..."
if git diff HEAD~1 HEAD --name-only | grep -q "scripts/droplet_api.py"; then
  echo "Deploying API..."
  scp scripts/droplet_api.py "$DEPLOY_USER@$DROPLET_IP:/opt/daanaa/scripts/" >> "$DEPLOY_LOG" 2>&1
  echo -e "${GREEN}✅ API updated${NC}"
else
  echo -e "${YELLOW}⊘ API unchanged, skipping${NC}"
fi
echo ""

# 4. Restart services
echo "[4/5] Restarting services..."
ssh "$DEPLOY_USER@$DROPLET_IP" "
  systemctl restart gunicorn >> /dev/null 2>&1
  sleep 2
  systemctl is-active gunicorn >/dev/null
" >> "$DEPLOY_LOG" 2>&1

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ Services restarted${NC}"
else
  echo -e "${RED}❌ Service restart failed — ROLLBACK INITIATED${NC}"
  bash infrastructure/deployment/rollback.sh "$SNAPSHOT_DIR"
  exit 1
fi
echo ""

# 5. Verify deployment
echo "[5/5] Verifying production health..."
HEALTH_CHECKS_PASSED=0
HEALTH_CHECKS_TOTAL=3

# Check API responds
if curl -s -o /dev/null -w "%{http_code}" "https://daanaa.org/health" | grep -q "200"; then
  echo -e "${GREEN}✅${NC} API responding"
  ((HEALTH_CHECKS_PASSED++))
else
  echo -e "${RED}❌${NC} API not responding"
fi

# Check homepage loads
if curl -s "https://daanaa.org/" | grep -q "Explore"; then
  echo -e "${GREEN}✅${NC} Homepage loads"
  ((HEALTH_CHECKS_PASSED++))
else
  echo -e "${RED}❌${NC} Homepage broken"
fi

# Check directory page
if curl -s "https://daanaa.org/directory" | grep -q "organization"; then
  echo -e "${GREEN}✅${NC} Directory page loads"
  ((HEALTH_CHECKS_PASSED++))
else
  echo -e "${RED}❌${NC} Directory page broken"
fi

echo ""

# Summary
if [ $HEALTH_CHECKS_PASSED -eq $HEALTH_CHECKS_TOTAL ]; then
  echo "═══════════════════════════════════════════════════════════════"
  echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL${NC}"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  echo "Deployed at: $(date)"
  echo "Commit: $(git rev-parse HEAD | cut -c1-8)"
  echo "Rollback available: $ROLLBACK_COMMIT"
  echo ""

  # Clean up old snapshots (keep last 5)
  find /tmp/deploy_snapshot_* -maxdepth 0 -type d | sort -r | tail -n +6 | xargs rm -rf

  exit 0
else
  echo "═══════════════════════════════════════════════════════════════"
  echo -e "${RED}❌ DEPLOYMENT FAILED — ROLLING BACK${NC}"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  bash infrastructure/deployment/rollback.sh "$SNAPSHOT_DIR"
  exit 1
fi
