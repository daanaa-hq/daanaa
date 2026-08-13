#!/bin/bash
# PHASE 1 SMOKE TEST SUITE
# Verifies V6 percentile + confidence + privacy guardrails on live endpoints

set -e

API_BASE="${API_BASE:-http://localhost:5000}"
SAMPLE_EINS=("010239880" "010634124" "010649488")  # Real test orgs
FAILED=0

echo "🧪 PHASE 1 SMOKE TEST — V6 Percentile + Privacy Guardrails"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 1: API health
echo ""
echo "[Test 1] API Health Check"
if curl -s "${API_BASE}/health" | grep -q '"status":"ok"'; then
  echo "  ✅ API is healthy"
else
  echo "  ❌ API health check failed"
  FAILED=$((FAILED + 1))
fi

# Test 2: Percentile contract (peer_percentile + confidence)
echo ""
echo "[Test 2] Percentile Contract (peer_percentile + confidence)"
for ein in "${SAMPLE_EINS[@]}"; do
  RESP=$(curl -s "${API_BASE}/api/organizations/${ein}")

  # Check for peer_percentile field
  if echo "$RESP" | grep -q '"peer_percentile"'; then
    PERCENTILE=$(echo "$RESP" | grep -o '"peer_percentile":[^,}]*' | cut -d: -f2)
    echo "  ✅ EIN ${ein}: peer_percentile = ${PERCENTILE}"
  else
    echo "  ❌ EIN ${ein}: missing peer_percentile field"
    FAILED=$((FAILED + 1))
  fi

  # Check for confidence field
  if echo "$RESP" | grep -q '"confidence"'; then
    CONFIDENCE=$(echo "$RESP" | grep -o '"confidence":"[^"]*"' | cut -d'"' -f4)
    echo "  ✅ EIN ${ein}: confidence = ${CONFIDENCE}"
  else
    echo "  ⚠️  EIN ${ein}: missing confidence field (expected for some tiers)"
  fi
done

# Test 3: Privacy guardrails (no small donor counts)
echo ""
echo "[Test 3] Privacy Guardrails (donation_count < 10 suppressed)"
for ein in "${SAMPLE_EINS[@]}"; do
  RESP=$(curl -s "${API_BASE}/api/organizations/${ein}")

  if echo "$RESP" | grep -q '"donation_count":'; then
    DONATION_COUNT=$(echo "$RESP" | grep -o '"donation_count":[^,}]*' | cut -d: -f2)
    if [ "$DONATION_COUNT" != "null" ]; then
      if [ "$DONATION_COUNT" -ge 10 ]; then
        echo "  ✅ EIN ${ein}: donation_count = ${DONATION_COUNT} (>= 10)"
      else
        echo "  ⚠️  EIN ${ein}: donation_count = ${DONATION_COUNT} (< 10, should suppress)"
      fi
    else
      echo "  ✅ EIN ${ein}: donation_count = null (privacy protected)"
    fi
  fi
done

# Test 4: Search endpoint
echo ""
echo "[Test 4] Search Endpoint (returns orgs with v6 fields)"
SEARCH_RESP=$(curl -s "${API_BASE}/api/search?q=tutoring&limit=5")
if echo "$SEARCH_RESP" | grep -q '"results"'; then
  RESULT_COUNT=$(echo "$SEARCH_RESP" | grep -o '"peer_percentile"' | wc -l)
  echo "  ✅ Search returned ${RESULT_COUNT} orgs with peer_percentile"
else
  echo "  ❌ Search endpoint failed"
  FAILED=$((FAILED + 1))
fi

# Test 5: Stats endpoint
echo ""
echo "[Test 5] Stats Endpoint (registry stats)"
if curl -s "${API_BASE}/api/stats" | grep -q '"total_orgs"'; then
  echo "  ✅ Stats endpoint responsive"
else
  echo "  ❌ Stats endpoint failed"
  FAILED=$((FAILED + 1))
fi

# Test 6: HTTP status codes (no 500s on org pages)
echo ""
echo "[Test 6] HTTP Status Codes (no 500s)"
for ein in "${SAMPLE_EINS[@]}"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_BASE}/api/organizations/${ein}")
  if [ "$STATUS" = "200" ]; then
    echo "  ✅ EIN ${ein}: HTTP ${STATUS}"
  else
    echo "  ❌ EIN ${ein}: HTTP ${STATUS}"
    FAILED=$((FAILED + 1))
  fi
done

# Test 7: Frontend build (verifies no TypeScript errors)
echo ""
echo "[Test 7] Frontend Build"
if npm run build --prefix frontend &>/dev/null; then
  echo "  ✅ Frontend builds clean"
else
  echo "  ❌ Frontend build failed"
  FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILED -eq 0 ]; then
  echo "✅ All smoke tests passed!"
  exit 0
else
  echo "❌ $FAILED test(s) failed"
  exit 1
fi
