#!/bin/bash

# Pre-Deployment Validation
# Checks all prerequisites before running deploy_orchestrator.sh
# Usage: bash pre_deploy_validate.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
WARNINGS=0

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        Daanaa Pre-Deployment Validation Checker          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

check_pass() {
  echo -e "${GREEN}✅${NC} $1"
  ((PASSED++))
}

check_fail() {
  echo -e "${RED}❌${NC} $1"
  ((FAILED++))
}

check_warn() {
  echo -e "${YELLOW}⚠️ ${NC} $1"
  ((WARNINGS++))
}

# === System Prerequisites ===
echo -e "${BLUE}[1/4] System Prerequisites${NC}"

if command -v docker &> /dev/null; then
  DOCKER_VERSION=$(docker --version)
  check_pass "Docker installed: $DOCKER_VERSION"
else
  check_fail "Docker not installed. Install from: https://docs.docker.com/install/"
fi

if command -v docker-compose &> /dev/null; then
  DC_VERSION=$(docker-compose --version)
  check_pass "Docker Compose installed: $DC_VERSION"
else
  check_fail "Docker Compose not installed. Install from: https://docs.docker.com/compose/install/"
fi

if docker ps &> /dev/null; then
  check_pass "Docker daemon is running"
else
  check_fail "Docker daemon not running. Start with: sudo systemctl start docker"
fi

if [ -w /var/run/docker.sock ]; then
  check_pass "Current user can access Docker socket"
else
  check_warn "Current user may not have Docker permissions. Run: sudo usermod -aG docker \$USER"
fi

echo ""

# === Disk Space ===
echo -e "${BLUE}[2/4] Disk Space${NC}"

if [ -d "/data" ]; then
  FREE_SPACE=$(df /data 2>/dev/null | awk 'NR==2 {print $4}')
  FREE_GB=$((FREE_SPACE / 1024 / 1024))

  if [ "$FREE_GB" -ge 20 ]; then
    check_pass "/data partition has ${FREE_GB}GB free (need ≥20GB)"
  else
    check_fail "/data partition has only ${FREE_GB}GB free (need ≥20GB)"
  fi
else
  check_warn "/data directory doesn't exist. Creating..."
  mkdir -p /data || check_fail "Cannot create /data"
fi

# Check temp space
TEMP_FREE=$(df /tmp 2>/dev/null | awk 'NR==2 {print $4}' || echo "0")
TEMP_GB=$((TEMP_FREE / 1024 / 1024))
if [ "$TEMP_GB" -ge 5 ]; then
  check_pass "/tmp has ${TEMP_GB}GB free (need ≥5GB)"
else
  check_warn "/tmp has only ${TEMP_GB}GB free"
fi

echo ""

# === Port Availability ===
echo -e "${BLUE}[3/4] Port Availability${NC}"

for port in 3000 5678 5060; do
  if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
    check_warn "Port $port is already in use"
  else
    check_pass "Port $port is available"
  fi
done

echo ""

# === Configuration Files ===
echo -e "${BLUE}[4/4] Configuration Files${NC}"

# Check if directories exist
for dir in /opt/chatwoot /opt/jambonz /opt/n8n; do
  if [ -d "$dir" ]; then
    check_pass "Directory exists: $dir"
  else
    check_warn "Directory doesn't exist: $dir (will be created)"
  fi
done

# Check for templates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for template in \
  "$SCRIPT_DIR/deploy/env.chatwoot.template" \
  "$SCRIPT_DIR/deploy/env.jambonz.template" \
  "$SCRIPT_DIR/deploy/env.n8n.template"; do
  if [ -f "$template" ]; then
    check_pass "Template found: $(basename $template)"
  else
    check_warn "Template missing: $(basename $template)"
  fi
done

# Check for Docker Compose templates
for compose in \
  "$SCRIPT_DIR/deploy/docker-compose.chatwoot.yml" \
  "$SCRIPT_DIR/deploy/docker-compose.jambonz.yml" \
  "$SCRIPT_DIR/deploy/docker-compose.n8n.yml"; do
  if [ -f "$compose" ]; then
    check_pass "Docker Compose template found: $(basename $compose)"
  else
    check_warn "Docker Compose template missing: $(basename $compose) (will need to create)"
  fi
done

# Check for deployment scripts
if [ -f "$SCRIPT_DIR/scripts/deploy_orchestrator.sh" ]; then
  check_pass "Deployment orchestrator found"
else
  check_fail "Deployment orchestrator missing"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                   Validation Summary                      ║"
echo "║  Passed:  $PASSED"
echo "║  Failed:  $FAILED"
echo "║  Warnings: $WARNINGS"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

if [ $FAILED -gt 0 ]; then
  echo -e "${RED}❌ Validation failed. Fix issues above before deploying.${NC}"
  exit 1
elif [ $WARNINGS -gt 0 ]; then
  echo -e "${YELLOW}⚠️  Validation passed with warnings. Review above before deploying.${NC}"
  echo ""
  read -p "Continue with deployment? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
else
  echo -e "${GREEN}✅ All checks passed! Ready to deploy.${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Review deployment guide: docs/QUICK_START_DEPLOYMENT.md"
  echo "  2. Fill in environment files in deploy/ directory"
  echo "  3. Run deployment: bash scripts/deploy_orchestrator.sh"
fi

exit 0
