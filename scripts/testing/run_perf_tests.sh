#!/bin/bash
# Run Playwright-based performance tests
# Usage: bash scripts/testing/run_perf_tests.sh [base_url] [iterations] [browser]
# Example: bash scripts/testing/run_perf_tests.sh http://localhost:5000 5 chromium

BASE_URL="${1:-http://localhost:5000}"
ITERATIONS="${2:-3}"
BROWSER="${3:-chromium}"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        Performance Testing - Task #5 Index Impact             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Iterations: $ITERATIONS"
echo "  Browser: $BROWSER"
echo ""

# Check if playwright is installed
if ! command -v npx >/dev/null 2>&1; then
    echo "❌ npx not found (Node.js not installed)"
    exit 1
fi

# Run tests
cd ~/meritgiving
export BASE_URL="$BASE_URL"
export ITERATIONS="$ITERATIONS"

echo "Running Playwright tests..."
echo ""

npx playwright test scripts/testing/perf_test_playwright.ts \
    --project="$BROWSER" \
    --reporter=list \
    --quiet

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tests completed successfully"
    echo ""
    echo "📊 Results Summary:"
    echo "   See output above for timing details"
    echo ""
    echo "🔄 Next steps:"
    if [ "$BASE_URL" = "http://localhost:5000" ]; then
        echo "   1. Deploy Task #5 to droplet"
        echo "   2. Run: bash scripts/testing/run_perf_tests.sh https://daanaa.org 5"
        echo "   3. Compare results (should see 5-10% improvement)"
    else
        echo "   ✅ Public site tested. Compare with localhost baseline above."
    fi
else
    echo "❌ Tests failed"
    exit 1
fi
