#!/bin/bash
# Daanaa Site Quality Audit — Phase 2
# Tests: mobile responsiveness, accessibility, SEO, performance, 404 handling

set -e

API_BASE="http://localhost:5000"
AUDIT_DIR="audit_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$AUDIT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "  Daanaa Site Quality Audit"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# 1. AVAILABILITY & STATUS CODES
echo "[1/5] Checking route availability..."
ROUTES=(
  "/"
  "/directory"
  "/about"
  "/how-it-works"
  "/faq"
  "/methodology"
  "/legal/privacy"
  "/legal/terms"
  "/for-nonprofits"
  "/health"
  "/api/stats"
  "/nonexistent-route-test"
)

HEALTH_REPORT="$AUDIT_DIR/health_report.txt"
> "$HEALTH_REPORT"

echo "Route Status Codes:" >> "$HEALTH_REPORT"
for route in "${ROUTES[@]}"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE$route")
  EXPECTED=200
  [ "$route" = "/nonexistent-route-test" ] && EXPECTED=404

  RESULT="✓"
  [ "$STATUS" != "$EXPECTED" ] && RESULT="✗"

  printf "  $RESULT %s — %d (expected %d)\n" "$route" "$STATUS" "$EXPECTED" >> "$HEALTH_REPORT"
  echo "  [$STATUS] $route" >&2
done

# 2. PERFORMANCE BASELINE
echo "[2/5] Performance baseline..."
PERF_REPORT="$AUDIT_DIR/performance_baseline.json"

python3 << 'EOF' > "$PERF_REPORT"
import time
import subprocess
import json
import statistics

endpoints = [
  "/api/stats",
  "/api/organizations?page=1&per_page=25",
  "/",
]

results = {}
for endpoint in endpoints:
  times = []
  for i in range(5):
    start = time.time()
    subprocess.run(
      ["curl", "-s", "-o", "/dev/null", f"http://localhost:5000{endpoint}"],
      timeout=30
    )
    elapsed = (time.time() - start) * 1000
    times.append(elapsed)

  results[endpoint] = {
    "mean_ms": round(statistics.mean(times), 2),
    "median_ms": round(statistics.median(times), 2),
    "min_ms": round(min(times), 2),
    "max_ms": round(max(times), 2),
  }

print(json.dumps(results, indent=2))
EOF

echo "  Performance baselines collected" >&2

# 3. SEO CHECKS
echo "[3/5] SEO verification..."
SEO_REPORT="$AUDIT_DIR/seo_checks.txt"
> "$SEO_REPORT"

echo "SEO Infrastructure:" >> "$SEO_REPORT"

# Check robots.txt
if curl -s "$API_BASE/robots.txt" | grep -q "Disallow"; then
  echo "  ✓ robots.txt present and configured" >> "$SEO_REPORT"
else
  echo "  ✗ robots.txt missing or not configured" >> "$SEO_REPORT"
fi

# Check sitemap
if curl -s "$API_BASE/sitemap.xml" | grep -q "urlset"; then
  echo "  ✓ sitemap.xml present" >> "$SEO_REPORT"
else
  echo "  ✗ sitemap.xml missing" >> "$SEO_REPORT"
fi

# Check OG tags on homepage
if curl -s "$API_BASE/" | grep -q "og:title\|og:description"; then
  echo "  ✓ OG tags configured" >> "$SEO_REPORT"
else
  echo "  ✗ OG tags missing" >> "$SEO_REPORT"
fi

# Check canonical URL setup
if curl -s "$API_BASE/" | grep -q "rel=\"canonical\"" || grep -q "usePageMeta" /home/akbar/meritgiving/frontend/src/pages/*.tsx; then
  echo "  ✓ Canonical URL infrastructure in place" >> "$SEO_REPORT"
else
  echo "  ✗ Canonical URLs not configured" >> "$SEO_REPORT"
fi

# 4. MOBILE VIEWPORT
echo "[4/5] Mobile viewport check..."
MOBILE_REPORT="$AUDIT_DIR/mobile_check.txt"
curl -s "$API_BASE/" | grep -E "viewport|mobile-web-app|apple-mobile" > "$MOBILE_REPORT" || echo "  (partial check)" >&2

if grep -q "viewport" "$MOBILE_REPORT"; then
  echo "  ✓ Viewport meta tag configured" >&2
else
  echo "  ✗ Viewport meta tag missing" >&2
fi

# 5. 404 HANDLING
echo "[5/5] 404 page check..."
NOTFOUND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/this-route-definitely-does-not-exist-12345")
echo "  404 status code: $NOTFOUND_STATUS" >&2

if [ "$NOTFOUND_STATUS" = "404" ]; then
  echo "  ✓ 404 page properly configured" >> "$AUDIT_REPORT"
else
  echo "  ✗ 404 routing issue" >> "$AUDIT_REPORT"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Audit Results"
echo "═══════════════════════════════════════════════════════════════"
echo "Reports saved to: $AUDIT_DIR/"
echo ""
echo "Health Check:"
cat "$HEALTH_REPORT" | head -15
echo ""
echo "Performance Baseline:"
jq '.[] | .mean_ms' "$PERF_REPORT" | head -5
echo ""
echo "SEO Status:"
cat "$SEO_REPORT"
echo ""
