#!/bin/bash
# Run Playwright-based performance tests
# Usage: bash scripts/testing/run_perf_tests.sh [base_url] [iterations] [browser]
# Example: bash scripts/testing/run_perf_tests.sh http://localhost:5000 5 chromium

BASE_URL="${1:-http://localhost:5000}"
ITERATIONS="${2:-5}"
BROWSER="${3:-brave}"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        Performance Testing - Task #5 Index Impact             ║"
echo "║              🦁 Using Brave Browser 🦁                        ║"
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

# Check if Brave is installed
if [ "$BROWSER" = "brave" ]; then
    if ! command -v brave-browser >/dev/null 2>&1; then
        echo "❌ Brave browser not found"
        echo "   Install with: sudo apt-get install brave-browser"
        exit 1
    fi
    echo "✅ Brave browser found: $(brave-browser --version | head -1)"
    echo ""
fi

# Run tests
cd ~/meritgiving
export BASE_URL="$BASE_URL"
export ITERATIONS="$ITERATIONS"
export BROWSER_EXECUTABLE="brave-browser"

echo "Running Playwright tests with Brave..."
echo ""

# Use Brave-configured Playwright config
npx playwright test \
    --config=playwright.perf.config.ts \
    --reporter=list

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
