#!/bin/bash
# Docker Phase 1 Deployment Script
# Builds and deploys Phase 1 to droplet via Docker

set -e

DROPLET="root@167.178.26.8"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"
SSH="ssh -i $SSH_KEY $DROPLET"

echo "🐳 PHASE 1 DOCKER DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Build Docker image locally
echo ""
echo "[1/4] Building Docker image..."
docker build -t daanaa-phase1:latest .

# Step 2: Tag for deployment
echo "[2/4] Tagging image..."
docker tag daanaa-phase1:latest daanaa-phase1:$(date +%Y%m%d_%H%M%S)

# Step 3: Save and transfer to droplet
echo "[3/4] Transferring to droplet..."
docker save daanaa-phase1:latest | gzip | $SSH "cat > /tmp/daanaa-phase1.tar.gz && cd /srv/daanaa && docker load < /tmp/daanaa-phase1.tar.gz && rm /tmp/daanaa-phase1.tar.gz"

# Step 4: Deploy with docker-compose
echo "[4/4] Deploying with docker-compose..."
$SSH bash -c 'cd /srv/daanaa && docker-compose down && docker-compose up -d'

# Verify
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 5
if $SSH "curl -s http://localhost:5000/health | grep -q 'ok'"; then
  echo "✅ Phase 1 LIVE via Docker!"
  echo ""
  echo "Verify at:"
  echo "  - Local: http://localhost:5000/health"
  echo "  - Live: curl -I https://daanaa.org"
else
  echo "❌ Deployment failed - check logs:"
  $SSH "docker-compose logs daanaa-api"
  exit 1
fi
