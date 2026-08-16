#!/bin/bash

# Post-Deployment Verification
# Comprehensive check that all services are working
# Usage: bash post_deploy_verify.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       Daanaa Post-Deployment Verification (Day 4)        ║"
echo "║           $(date '+%Y-%m-%d %H:%M:%S')                            ║"
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

# === Docker Containers ===
echo -e "${BLUE}[1/6] Docker Containers${NC}"

if docker ps --format "{{.Names}}" | grep -q "chatwoot"; then
  check_pass "Chatwoot container running"
else
  check_fail "Chatwoot container not running"
fi

if docker ps --format "{{.Names}}" | grep -q "n8n"; then
  check_pass "n8n container running"
else
  check_fail "n8n container not running"
fi

if docker ps --format "{{.Names}}" | grep -q "jambonz"; then
  check_pass "Jambonz container running"
else
  check_fail "Jambonz container not running"
fi

echo ""

# === Service Connectivity ===
echo -e "${BLUE}[2/6] Service Connectivity${NC}"

if curl -s http://localhost:3000 > /dev/null; then
  check_pass "Chatwoot (port 3000) responding"
else
  check_fail "Chatwoot (port 3000) not responding"
fi

if curl -s http://localhost:5678 > /dev/null; then
  check_pass "n8n (port 5678) responding"
else
  check_fail "n8n (port 5678) not responding"
fi

if netstat -tlnp 2>/dev/null | grep -q ":5060 "; then
  check_pass "Jambonz SIP (port 5060) listening"
else
  check_fail "Jambonz SIP (port 5060) not listening"
fi

echo ""

# === Database Connectivity ===
echo -e "${BLUE}[3/6] Database Connectivity${NC}"

if docker exec chatwoot_postgres_1 pg_isready 2>/dev/null | grep -q "accepting"; then
  check_pass "Chatwoot PostgreSQL responding"
else
  check_fail "Chatwoot PostgreSQL not responding"
fi

if docker exec n8n_postgres_1 pg_isready 2>/dev/null | grep -q "accepting"; then
  check_pass "n8n PostgreSQL responding"
else
  check_fail "n8n PostgreSQL not responding"
fi

echo ""

# === API Endpoints ===
echo -e "${BLUE}[4/6] API Endpoints${NC}"

# Chatwoot API
if curl -s "http://localhost:3000/api/v1/account" \
  -H "Authorization: Bearer test" 2>&1 | grep -q "error\|data"; then
  check_pass "Chatwoot API responding"
else
  check_fail "Chatwoot API not responding"
fi

# n8n API
if curl -s "http://localhost:5678/api/v1/workflows" 2>&1 | grep -q "data\|error"; then
  check_pass "n8n API responding"
else
  check_fail "n8n API not responding"
fi

echo ""

# === Data Integrity ===
echo -e "${BLUE}[5/6] Data Integrity${NC}"

# Check Chatwoot can create conversations
CONV_COUNT=$(curl -s "http://localhost:3000/api/v1/account/conversations" 2>&1 | grep -o "payload" | wc -l)
if [ "$CONV_COUNT" -gt 0 ]; then
  check_pass "Chatwoot can query conversations"
else
  check_warn "Chatwoot conversation query returned no data (may be normal)"
fi

# Check n8n has workflows
WORKFLOW_COUNT=$(curl -s "http://localhost:5678/api/v1/workflows" 2>&1 | grep -o "name" | wc -l)
if [ "$WORKFLOW_COUNT" -gt 0 ]; then
  check_pass "n8n has $WORKFLOW_COUNT workflow(s)"
else
  check_warn "n8n returned no workflows (import workflows if not done)"
fi

echo ""

# === System Resources ===
echo -e "${BLUE}[6/6] System Resources${NC}"

DISK_USAGE=$(df /data | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
  check_pass "Disk usage at ${DISK_USAGE}% (good)"
else
  check_fail "Disk usage at ${DISK_USAGE}% (>80%, cleanup needed)"
fi

MEMORY=$(free -m | awk 'NR==2 {print int($3/$2 * 100)}')
if [ "$MEMORY" -lt 80 ]; then
  check_pass "Memory usage at ${MEMORY}% (good)"
else
  check_warn "Memory usage at ${MEMORY}% (monitor)"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                 Verification Summary                      ║"
echo "║  Passed:  $PASSED/10"
echo "║  Failed:  $FAILED/10"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

if [ $FAILED -gt 0 ]; then
  echo -e "${RED}❌ Some checks failed. Investigate above.${NC}"
  echo ""
  echo "Troubleshooting:"
  echo "  - Check Docker logs: docker logs -f [container_name]"
  echo "  - See DISASTER_RECOVERY_RUNBOOKS.md for recovery steps"
  exit 1
else
  echo -e "${GREEN}✅ All checks passed! System is ready.${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Manual testing:"
  echo "     - Email: Send to daanaa@daanaa.org, wait 5 min for auto-reply"
  echo "     - Voice: Call your DID, complete IVR flow"
  echo "     - See INTEGRATION_TEST_SUITE.md for all tests"
  echo ""
  echo "  2. Go-live:"
  echo "     - Announce phone number to nonprofits"
  echo "     - Follow GO_LIVE_CHECKLIST.md for launch day"
  echo ""
  echo "  3. Ongoing:"
  echo "     - Daily: run scripts/health_check.sh"
  echo "     - Weekly: follow WEEKLY_OPERATIONS_PLAYBOOK.md"
  echo "     - On incidents: see DISASTER_RECOVERY_RUNBOOKS.md"
fi

exit 0
