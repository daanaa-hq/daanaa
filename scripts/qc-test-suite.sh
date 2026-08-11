#!/bin/bash

# QC Test Suite Orchestrator
# Runs Playwright tests for Phase 1-4 blocker fixes before deployment
#
# Usage: bash scripts/qc-test-suite.sh [--verbose] [--headless]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
VERBOSE=false
HEADLESS=true

for arg in "$@"; do
  case $arg in
    --verbose)
      VERBOSE=true
      ;;
    --headed)
      HEADLESS=false
      ;;
  esac
done

echo -e "${BLUE}=== QC Test Suite: Phase 1-4 Blocker Fixes ===${NC}"
echo ""

# Step 1: Check if frontend is built
echo -e "${YELLOW}[1/4] Checking frontend build...${NC}"
if [ ! -d "frontend/dist" ]; then
  echo -e "${YELLOW}Frontend not built. Building now...${NC}"
  cd frontend
  npm run build
  cd ..
fi
echo -e "${GREEN}✓ Frontend built${NC}"
echo ""

# Step 2: Start dev server (if not already running)
echo -e "${YELLOW}[2/4] Starting dev server...${NC}"
if ! lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null; then
  echo "Dev server not running. Starting on port 5173..."
  cd frontend
  npm run dev &
  DEV_PID=$!
  sleep 3
  cd ..
  echo -e "${GREEN}✓ Dev server started (PID: $DEV_PID)${NC}"
else
  echo -e "${GREEN}✓ Dev server already running${NC}"
fi
echo ""

# Step 3: Run Playwright tests
echo -e "${YELLOW}[3/4] Running QC tests...${NC}"

# Build test command with flags
TEST_ARGS="tests/qc-blocker-fixes.spec.ts"
[ "$VERBOSE" = true ] && TEST_ARGS="$TEST_ARGS --reporter=verbose"
[ "$HEADLESS" = false ] && TEST_ARGS="$TEST_ARGS --headed"

if [ "$HEADLESS" = false ]; then
  echo -e "${YELLOW}Running in headed mode (browser visible)...${NC}"
fi

npx playwright test $TEST_ARGS

TEST_EXIT_CODE=$?
echo ""

# Step 4: Report results
echo -e "${YELLOW}[4/4] Test Results${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ ALL QC TESTS PASSED${NC}"
  echo ""
  echo -e "${GREEN}Summary:${NC}"
  echo "  ✓ Firebase Analytics removed (P2 compliance)"
  echo "  ✓ IRS status bug fixed (P3 trust signal)"
  echo "  ✓ Donation flow consistent"
  echo "  ✓ Core functionality working"
  echo "  ✓ No console errors"
  echo "  ✓ Performance baseline met"
  echo ""
  echo -e "${GREEN}Site is ready for deployment.${NC}"
else
  echo -e "${RED}❌ QC TESTS FAILED${NC}"
  echo ""
  echo "Some tests failed. Review the output above and fix issues before deploying."
  exit 1
fi

# Clean up dev server if we started it
if [ ! -z "$DEV_PID" ]; then
  echo ""
  echo -e "${YELLOW}Cleaning up dev server...${NC}"
  kill $DEV_PID 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}QC Test Suite Complete${NC}"
