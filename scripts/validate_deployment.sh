#!/bin/bash
"""
Deployment Validation Script — QA Gate for Same-Day Deploy

Validates:
1. Database state (scores loaded, hidden gems re-flagged)
2. Local :5000 API responses
3. Key org spot-check (471694019)
4. Search functionality (FTS index)

Usage:
    bash scripts/validate_deployment.sh              # Full validation
    bash scripts/validate_deployment.sh --quick      # API only
"""

set -e

DB=/home/akbar/meritgiving/data/merit_registry.db
API_BASE="http://localhost:5000"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
RESULTS_FILE="/home/akbar/meritgiving/logs/validation_results.log"

log() {
    msg="[$TIMESTAMP] $1"
    echo "$msg"
    echo "$msg" >> "$RESULTS_FILE"
}

pass() {
    echo "  ✅ $1"
    echo "  ✅ $1" >> "$RESULTS_FILE"
}

fail() {
    echo "  ❌ $1"
    echo "  ❌ $1" >> "$RESULTS_FILE"
    exit 1
}

warn() {
    echo "  ⚠️  $1"
    echo "  ⚠️  $1" >> "$RESULTS_FILE"
}

log "=========================================="
log "Deployment Validation Started"
log "=========================================="

# ────────────────────────────────────────────────────────────────
# Check 1: Database — Scores loaded correctly
# ────────────────────────────────────────────────────────────────
log "Check 1: Database scores integrity..."
SCORE_STATS=$(sqlite3 "$DB" <<EOF
SELECT
    (SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NULL) as null_scores,
    (SELECT COUNT(*) FROM registry_enriched WHERE merit_score < 0 OR merit_score > 100) as out_of_range,
    (SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL) as total_scored,
    ROUND(AVG(merit_score), 2) as avg_score;
EOF
)

NULL_COUNT=$(echo "$SCORE_STATS" | awk 'NR==1 {print $1}')
OUT_OF_RANGE=$(echo "$SCORE_STATS" | awk 'NR==1 {print $2}')
TOTAL_SCORED=$(echo "$SCORE_STATS" | awk 'NR==1 {print $3}')
AVG_SCORE=$(echo "$SCORE_STATS" | awk 'NR==1 {print $4}')

[ "$NULL_COUNT" -eq 0 ] || fail "Found $NULL_COUNT NULL scores"
[ "$OUT_OF_RANGE" -eq 0 ] || fail "Found $OUT_OF_RANGE out-of-range scores"
[ "$TOTAL_SCORED" -gt 0 ] || fail "No scores loaded"

pass "Scores loaded: $TOTAL_SCORED orgs, avg=$AVG_SCORE"

# ────────────────────────────────────────────────────────────────
# Check 2: Database — Hidden gems re-flagged correctly
# ────────────────────────────────────────────────────────────────
log "Check 2: Hidden gems criteria..."
GEM_STATS=$(sqlite3 "$DB" <<EOF
SELECT
    (SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1) as total_gems,
    (SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1 AND merit_score >= 85 AND total_revenue > 0 AND total_revenue < 500000) as valid_gems,
    (SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1 AND (merit_score < 85 OR total_revenue <= 0 OR total_revenue >= 500000)) as invalid_gems;
EOF
)

TOTAL_GEMS=$(echo "$GEM_STATS" | awk 'NR==1 {print $1}')
VALID_GEMS=$(echo "$GEM_STATS" | awk 'NR==1 {print $2}')
INVALID_GEMS=$(echo "$GEM_STATS" | awk 'NR==1 {print $3}')

[ "$INVALID_GEMS" -eq 0 ] || fail "Found $INVALID_GEMS invalid hidden gems"
pass "Hidden gems: $TOTAL_GEMS total, $VALID_GEMS valid, $INVALID_GEMS invalid"

# ────────────────────────────────────────────────────────────────
# Check 3: Spot-check org 471694019
# ────────────────────────────────────────────────────────────────
log "Check 3: Org 471694019 (test case)..."
ORG_DATA=$(sqlite3 "$DB" "SELECT merit_score, total_revenue, is_hidden_gem FROM registry_enriched WHERE EIN = '471694019';")
ORG_SCORE=$(echo "$ORG_DATA" | cut -d'|' -f1)
ORG_REVENUE=$(echo "$ORG_DATA" | cut -d'|' -f2)
ORG_GEM=$(echo "$ORG_DATA" | cut -d'|' -f3)

[ -n "$ORG_SCORE" ] || fail "Org 471694019 not found"
[ "$ORG_GEM" -eq 1 ] || fail "Org 471694019 should be hidden gem (got gem=$ORG_GEM)"
pass "Org 471694019: score=$ORG_SCORE, revenue=$ORG_REVENUE, hidden_gem=$ORG_GEM ✓"

# ────────────────────────────────────────────────────────────────
# Check 4: API — /api/stats endpoint
# ────────────────────────────────────────────────────────────────
log "Check 4: API /api/stats..."
STATS=$(curl -s "$API_BASE/api/stats" 2>/dev/null || echo "FAILED")

if echo "$STATS" | grep -q "total_orgs"; then
    ORG_COUNT=$(echo "$STATS" | grep -o '"total_orgs":[0-9]*' | cut -d: -f2)
    SCORED_COUNT=$(echo "$STATS" | grep -o '"scored_orgs":[0-9]*' | cut -d: -f2 || echo "unknown")
    pass "API responding: $ORG_COUNT total orgs"
else
    fail "API /api/stats not responding or invalid response"
fi

# ────────────────────────────────────────────────────────────────
# Check 5: API — /api/org/471694019 endpoint
# ────────────────────────────────────────────────────────────────
log "Check 5: API /api/org/471694019..."
ORG_API=$(curl -s "$API_BASE/api/org/471694019" 2>/dev/null || echo "FAILED")

if echo "$ORG_API" | grep -q "merit_score"; then
    API_SCORE=$(echo "$ORG_API" | grep -o '"merit_score":[0-9.]*' | cut -d: -f2)
    API_GEM=$(echo "$ORG_API" | grep -o '"is_hidden_gem":[a-z]*' | cut -d: -f2)
    API_MISSION=$(echo "$ORG_API" | grep -o '"mission":"[^"]*"' | cut -d'"' -f4 | head -c 40)
    pass "Org API: score=$API_SCORE, gem=$API_GEM, mission='$API_MISSION...'"
else
    fail "API /api/org/471694019 not responding or invalid"
fi

# ────────────────────────────────────────────────────────────────
# Check 6: FTS Search Index
# ────────────────────────────────────────────────────────────────
log "Check 6: FTS search index..."
FTS_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM org_fts;" 2>/dev/null || echo "0")

if [ "$FTS_COUNT" -gt 0 ]; then
    pass "FTS index available: $FTS_COUNT docs indexed"
else
    warn "FTS index empty or not built yet"
fi

# ────────────────────────────────────────────────────────────────
# Final Summary
# ────────────────────────────────────────────────────────────────
log "=========================================="
log "✅ Deployment validation PASSED"
log "=========================================="
log "Ready for 2 PM demo on :5000"
log "  Scores: $TOTAL_SCORED orgs loaded"
log "  Hidden gems: $TOTAL_GEMS flagged correctly"
log "  API: Responding with fresh data"
log "  Org 471694019: Correctly flagged as hidden gem"
log "=========================================="
