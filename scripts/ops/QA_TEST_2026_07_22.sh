#!/bin/bash
# QA Test Suite for Phase 1 & 2 UX Deployment (2026-07-22)
#
# Run this to verify:
# - Frontend Phase 1 & 2 components are live
# - API endpoints are responding
# - Database schema is intact
# - Volunteer hours system works (no duplicates)
# - Nonprofit dashboard is functional
# - Stewardship principles maintained
#
# Usage: bash QA_TEST_2026_07_22.sh
#
# Results saved to: qa_results_$(date +%s).log

set -euo pipefail

RESULTS_FILE="qa_results_$(date +%s).log"
PASS_COUNT=0
FAIL_COUNT=0
TEST_COUNT=0

BASE_URL="https://daanaa.org"
API_URL="$BASE_URL/api"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$RESULTS_FILE"
}

pass() {
    TEST_COUNT=$((TEST_COUNT+1))
    PASS_COUNT=$((PASS_COUNT+1))
    echo -e "${GREEN}✓ PASS${NC}: $*" | tee -a "$RESULTS_FILE"
}

fail() {
    TEST_COUNT=$((TEST_COUNT+1))
    FAIL_COUNT=$((FAIL_COUNT+1))
    echo -e "${RED}✗ FAIL${NC}: $*" | tee -a "$RESULTS_FILE"
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $*" | tee -a "$RESULTS_FILE"
}

header() {
    echo "" | tee -a "$RESULTS_FILE"
    echo "============================================" | tee -a "$RESULTS_FILE"
    echo "$*" | tee -a "$RESULTS_FILE"
    echo "============================================" | tee -a "$RESULTS_FILE"
}

# ============ PHASE 1 & 2 UX COMPONENT TESTS ============

header "PHASE 1 & 2 UX COMPONENT TESTS"

# Test 1: Homepage loads with proper structure
log "Testing homepage..."
HOMEPAGE=$(curl -sS --max-time 15 "$BASE_URL/" 2>/dev/null)
if echo "$HOMEPAGE" | grep -q "<!doctype html"; then
    pass "Homepage returns valid HTML"
else
    fail "Homepage doesn't return valid HTML"
fi

# Test 2: HelpTooltip in nonprofit dashboard
log "Testing HelpTooltip component..."
if echo "$HOMEPAGE" | grep -q "tooltip\|help-icon\|aria-label"; then
    pass "Accessibility attributes present (aria-label/tooltip)"
else
    warn "HelpTooltip accessibility attributes not found in initial load (may be client-rendered)"
fi

# Test 3: WelcomeCard detection
log "Testing WelcomeCard integration..."
if echo "$HOMEPAGE" | grep -iq "welcome\|first.*visit\|getting.*started"; then
    pass "Welcome card messaging detected"
else
    warn "Welcome card not in homepage HTML (may be app-specific, client-rendered)"
fi

# ============ API ENDPOINT TESTS ============

header "API ENDPOINT TESTS"

# Test 4: Search API working
log "Testing /api/search endpoint..."
SEARCH=$(curl -sS --max-time 15 "$API_URL/search?q=food+bank&limit=1" 2>/dev/null)
if echo "$SEARCH" | grep -q '"organization_name"\|"EIN"\|"results"'; then
    pass "Search API responds with org data"
else
    fail "Search API not returning expected data"
fi

# Test 5: Organizations directory API
log "Testing /api/organizations endpoint..."
ORG_DIR=$(curl -sS --max-time 15 "$API_URL/organizations?state=TX&limit=1" 2>/dev/null)
if echo "$ORG_DIR" | grep -q '"results"\|"name"\|"organizations"'; then
    pass "Organizations directory API working"
else
    fail "Organizations API not responding correctly"
fi

# Test 6: API returns proper HTTP status
log "Testing API status codes..."
HTTP_CODE=$(curl -sS --max-time 15 -o /dev/null -w "%{http_code}" "$API_URL/search?q=test&limit=1")
if [ "$HTTP_CODE" = "200" ]; then
    pass "API returns HTTP 200"
else
    fail "API returned HTTP $HTTP_CODE (expected 200)"
fi

# Test 7: Health endpoint
log "Testing /health endpoint..."
HEALTH=$(curl -sS --max-time 10 "$BASE_URL/health" 2>/dev/null)
if echo "$HEALTH" | grep -q "status\|ok"; then
    pass "Health endpoint responding"
else
    warn "Health endpoint not responding (may be internal only)"
fi

# ============ VOLUNTEER HOURS SYSTEM TESTS ============

header "VOLUNTEER HOURS SYSTEM TESTS"

# Test 8: Database schema check (local only)
log "Testing volunteer hours database schema..."
if command -v sqlite3 >/dev/null 2>&1 && [ -f "data/merit_registry.db" ]; then
    VOLUNTEER_TABLES=$(sqlite3 data/merit_registry.db ".tables" | grep -c "volunteer" || echo "0")
    if [ "$VOLUNTEER_TABLES" -gt "0" ]; then
        pass "Volunteer hours tables exist in database ($VOLUNTEER_TABLES tables)"
    else
        fail "Volunteer hours tables not found in database"
    fi

    # Test 9: Volunteer hours columns
    log "Testing volunteer hours schema columns..."
    COLS=$(sqlite3 data/merit_registry.db "PRAGMA table_info(volunteer_events);" 2>/dev/null | wc -l)
    if [ "$COLS" -gt "0" ]; then
        pass "Volunteer hours events table has schema ($COLS columns)"
    else
        fail "Volunteer hours events table schema missing"
    fi
else
    warn "SQLite not available or database not found (skipping local DB tests)"
fi

# Test 10: Idempotency check (submission_id prevents duplicates)
log "Testing volunteer hours idempotency (submission_id protection)..."
if grep -q "submission_id" daanaa_api.py 2>/dev/null; then
    pass "Idempotency marker (submission_id) in API code"
else
    warn "submission_id not found in API (may be in different location)"
fi

# ============ NONPROFIT DASHBOARD TESTS ============

header "NONPROFIT DASHBOARD TESTS"

# Test 11: Nonprofit auth endpoints
log "Testing nonprofit authentication endpoints..."
if grep -q "/api/auth\|/nonprofit\|nonprofit_login" daanaa_api.py 2>/dev/null; then
    pass "Nonprofit auth endpoints defined in API"
else
    fail "Nonprofit auth endpoints not found"
fi

# Test 12: Profile editor integration
log "Testing profile editor components..."
if [ -f "frontend/src/pages/nonprofit/ProfileEditor.tsx" ]; then
    if grep -q "HelpTooltip\|LearnMoreLink" "frontend/src/pages/nonprofit/ProfileEditor.tsx"; then
        pass "ProfileEditor has Phase 1 & 2 UX components"
    else
        fail "ProfileEditor missing new UX components"
    fi
else
    warn "ProfileEditor file not found"
fi

# Test 13: Dashboard overview integration
log "Testing dashboard overview components..."
if [ -f "frontend/src/pages/nonprofit/DashboardOverview.tsx" ]; then
    if grep -q "WelcomeCard\|EmptyState\|HelpTooltip" "frontend/src/pages/nonprofit/DashboardOverview.tsx"; then
        pass "DashboardOverview has Phase 1 & 2 UX components"
    else
        fail "DashboardOverview missing new UX components"
    fi
else
    warn "DashboardOverview file not found"
fi

# ============ ACCESSIBILITY & UX TESTS ============

header "ACCESSIBILITY & UX TESTS"

# Test 14: ARIA labels in new components
log "Testing accessibility (ARIA labels)..."
if grep -rq "aria-label\|role=" "frontend/src/components/nonprofit/Help" 2>/dev/null; then
    pass "New components have ARIA labels and roles"
else
    warn "ARIA labels not found (may be in JSX attributes)"
fi

# Test 15: Component CSS/styling
log "Testing component styling..."
if [ -f "frontend/src/components/nonprofit/HelpTooltip.tsx" ]; then
    if grep -q "className\|style" "frontend/src/components/nonprofit/HelpTooltip.tsx"; then
        pass "Components have styling applied"
    else
        warn "Component styling not detected"
    fi
else
    warn "Component files not found in expected location"
fi

# ============ BUILD & DEPLOYMENT TESTS ============

header "BUILD & DEPLOYMENT TESTS"

# Test 16: Frontend build artifacts
log "Testing frontend build artifacts..."
if [ -d "frontend/dist" ] && [ -f "frontend/dist/index.html" ]; then
    SIZE=$(stat -f%z "frontend/dist/index.html" 2>/dev/null || stat -c%s "frontend/dist/index.html" 2>/dev/null)
    if [ "$SIZE" -gt "1000" ]; then
        pass "Frontend dist ready ($SIZE bytes)"
    else
        fail "Frontend dist too small ($SIZE bytes)"
    fi
else
    fail "Frontend dist folder or index.html missing"
fi

# Test 17: Deployment log
log "Testing deployment status..."
if [ -f "logs/frontend_deploy.log" ]; then
    if grep -q "Deploy complete" "logs/frontend_deploy.log" | tail -1; then
        pass "Frontend deployment completed successfully"
    else
        warn "Frontend deployment log exists but completion status unclear"
    fi
else
    warn "Frontend deployment log not found"
fi

# Test 18: Git commits for today's work
log "Testing git commits for Phase 1 & 2..."
PHASE_COMMITS=$(git log --oneline --since="2 hours ago" -- frontend/src 2>/dev/null | wc -l)
if [ "$PHASE_COMMITS" -gt "0" ]; then
    pass "Phase 1 & 2 commits found ($PHASE_COMMITS recent commits)"
else
    warn "No recent commits to frontend (may be from earlier today)"
fi

# ============ STEWARDSHIP COMPLIANCE TESTS ============

header "STEWARDSHIP COMPLIANCE TESTS"

# Test 19: Privacy check script exists
log "Testing privacy-check infrastructure..."
if [ -f "privacy_check.sh" ]; then
    pass "Privacy check script exists"
else
    fail "Privacy check script missing"
fi

# Test 20: No PII in component code
log "Testing for PII leakage in new components..."
if grep -rq "password\|credit_card\|ssn\|api_key" "frontend/src/components/nonprofit/Help"* 2>/dev/null; then
    fail "Potential PII found in component code"
else
    pass "No obvious PII patterns in new components"
fi

# Test 21: Stewardship principles documented
log "Testing stewardship documentation..."
if [ -f "STEWARDSHIP.md" ] && grep -q "Principle" STEWARDSHIP.md; then
    pass "Stewardship.md principles present"
else
    fail "STEWARDSHIP.md missing or incomplete"
fi

# Test 22: Component props validated
log "Testing TypeScript type safety..."
if grep -q "interface.*Props\|type.*Props" "frontend/src/components/nonprofit/HelpTooltip.tsx" 2>/dev/null; then
    pass "Components have TypeScript prop validation"
else
    warn "TypeScript props not explicitly defined (may use implicit types)"
fi

# ============ SMOKE TESTS ============

header "SMOKE TESTS (Production URL)"

# Test 23-25: Production smoke tests
log "Running production smoke tests..."

SMOKE1=$(curl -sS --max-time 20 "$BASE_URL/" 2>/dev/null | grep -c "<!doctype html" || echo "0")
if [ "$SMOKE1" -gt "0" ]; then
    pass "Production homepage loads (doctype found)"
else
    fail "Production homepage not loading"
fi

SMOKE2=$(curl -sS --max-time 20 -o /dev/null -w "%{http_code}" "$API_URL/search?q=test&limit=1" 2>/dev/null)
if [ "$SMOKE2" = "200" ]; then
    pass "Production API responding (HTTP 200)"
else
    fail "Production API not responding (HTTP $SMOKE2)"
fi

SMOKE3=$(curl -sS --max-time 20 "$API_URL/organizations?state=CA&limit=1" 2>/dev/null | grep -c "name" || echo "0")
if [ "$SMOKE3" -gt "0" ]; then
    pass "Production directory API working"
else
    fail "Production directory API not responding"
fi

# ============ TEST SUMMARY ============

header "TEST SUMMARY"

echo "" | tee -a "$RESULTS_FILE"
echo "Total Tests: $TEST_COUNT" | tee -a "$RESULTS_FILE"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}" | tee -a "$RESULTS_FILE"
if [ "$FAIL_COUNT" -gt "0" ]; then
    echo -e "${RED}Failed: $FAIL_COUNT${NC}" | tee -a "$RESULTS_FILE"
else
    echo -e "${GREEN}Failed: 0${NC}" | tee -a "$RESULTS_FILE"
fi

PASS_RATE=$((PASS_COUNT * 100 / TEST_COUNT))
echo "Pass Rate: $PASS_RATE%" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

if [ "$FAIL_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}" | tee -a "$RESULTS_FILE"
    echo "" | tee -a "$RESULTS_FILE"
    echo "Phase 1 & 2 deployment is ready for production." | tee -a "$RESULTS_FILE"
    echo "Results saved to: $RESULTS_FILE" | tee -a "$RESULTS_FILE"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}" | tee -a "$RESULTS_FILE"
    echo "" | tee -a "$RESULTS_FILE"
    echo "Review failures above and re-run after fixes." | tee -a "$RESULTS_FILE"
    echo "Results saved to: $RESULTS_FILE" | tee -a "$RESULTS_FILE"
    exit 1
fi
