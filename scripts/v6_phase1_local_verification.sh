#!/bin/bash
# v6_phase1_local_verification.sh
#
# Phase 1: Complete Local Verification
#
# Runs all local checks before proceeding to quiet-window verification:
# - Fairness comparison report
# - Test suite (24 tests)
# - Privacy validation
# - Shell syntax checks
# - Candidate status verification
#
# Usage: bash scripts/v6_phase1_local_verification.sh
#
# Exit codes:
#   0 = All checks passed, ready for Phase 2
#   1 = At least one check failed, review output above

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_PATH="${PROJECT_ROOT}/data/merit_registry.db"
PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Tracking
PHASE1_PASSED=0
PHASE1_FAILED=0

echo "======================================"
echo "V6 Phase 1: Local Verification"
echo "======================================"
echo ""

# ======================================
# CHECK 1: Fairness Comparison Report
# ======================================
echo "CHECK 1: Fairness Comparison Report"
echo "---"

if "$PYTHON_BIN" "$SCRIPT_DIR/v6_fairness_comparison_corrected.py" \
  v6_foundation_candidate_20260728_revised \
  v6_foundation_candidate_20260727_corrected \
  "$DB_PATH" > /tmp/fairness_check.log 2>&1; then

  # Check for validation errors in output
  if grep -q "BLOCKED — Cannot proceed" /tmp/fairness_check.log; then
    echo -e "${RED}✗ FAILED${NC}: Fairness report has validation errors"
    cat /tmp/fairness_check.log | grep -A 10 "VALIDATION ERRORS" || true
  PHASE1_FAILED=$((PHASE1_FAILED + 1))
  else
    echo -e "${GREEN}✓ PASSED${NC}: Fairness comparison generated successfully"
    # Show key metrics
    echo ""
    echo "Key findings:"
    grep "Revoked in baseline (Tiers 1-4)" /tmp/fairness_check.log | head -1 || true
    grep "Coverage reduction explained by revocation" /tmp/fairness_check.log | head -1 || true
    grep "Grassroots/small organizations remaining in the candidate" /tmp/fairness_check.log | head -1 || true
    echo ""
  PHASE1_PASSED=$((PHASE1_PASSED + 1))
  fi
else
  echo -e "${RED}✗ FAILED${NC}: Fairness comparison script error"
  cat /tmp/fairness_check.log
  PHASE1_FAILED=$((PHASE1_FAILED + 1))
fi

echo ""

# ======================================
# CHECK 2: Test Suite
# ======================================
echo "CHECK 2: Test Suite (24 tests)"
echo "---"

if "$PYTHON_BIN" -m pytest -q \
  tests/test_v6_implementation.py \
  tests/test_v6_edge_cases.py 2>&1 | tee /tmp/pytest_check.log; then

  # Extract pass count
  PASS_COUNT=$(grep -oE "^[0-9]+ passed" /tmp/pytest_check.log | grep -oE "[0-9]+")
  if [ "$PASS_COUNT" = "24" ]; then
    echo -e "${GREEN}✓ PASSED${NC}: All 24 tests passed"
  PHASE1_PASSED=$((PHASE1_PASSED + 1))
  else
    echo -e "${RED}✗ FAILED${NC}: Only $PASS_COUNT tests passed (expected 24)"
  PHASE1_FAILED=$((PHASE1_FAILED + 1))
  fi
else
  echo -e "${RED}✗ FAILED${NC}: Test suite encountered errors"
  tail -20 /tmp/pytest_check.log
  PHASE1_FAILED=$((PHASE1_FAILED + 1))
fi

echo ""

# ======================================
# CHECK 3: Privacy Validation
# ======================================
echo "CHECK 3: Privacy Validation"
echo "---"

if bash "$SCRIPT_DIR/privacy_check.sh" > /tmp/privacy_check.log 2>&1; then
  echo -e "${GREEN}✓ PASSED${NC}: Privacy checks (8/8 gates)"
  PHASE1_PASSED=$((PHASE1_PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC}: Privacy validation failed"
  cat /tmp/privacy_check.log | tail -20
  PHASE1_FAILED=$((PHASE1_FAILED + 1))
fi

echo ""

# ======================================
# CHECK 4: Shell Syntax
# ======================================
echo "CHECK 4: Shell Syntax Checks"
echo "---"
SYNTAX_ERRORS=0

if bash -n "$SCRIPT_DIR/v6_daily_operations.sh" 2>/dev/null; then
  echo -e "${GREEN}✓${NC} v6_daily_operations.sh"
else
  echo -e "${RED}✗${NC} v6_daily_operations.sh"
  bash -n "$SCRIPT_DIR/v6_daily_operations.sh"
  SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
fi

if bash -n "$SCRIPT_DIR/v6_weekly_candidate.sh" 2>/dev/null; then
  echo -e "${GREEN}✓${NC} v6_weekly_candidate.sh"
else
  echo -e "${RED}✗${NC} v6_weekly_candidate.sh"
  bash -n "$SCRIPT_DIR/v6_weekly_candidate.sh"
  SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
fi

if [ "$SYNTAX_ERRORS" -eq 0 ]; then
  echo -e "${GREEN}✓ PASSED${NC}: Shell syntax checks"
  PHASE1_PASSED=$((PHASE1_PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC}: $SYNTAX_ERRORS shell syntax errors"
  PHASE1_FAILED=$((PHASE1_FAILED + 1))
fi

echo ""

# ======================================
# CHECK 5: Candidate Status
# ======================================
echo "CHECK 5: Candidate Status Verification"
echo "---"

CANDIDATE_STATUS=$(sqlite3 "$DB_PATH" \
  "SELECT status FROM v6_scoring_runs WHERE run_id='v6_foundation_candidate_20260728_revised';" 2>/dev/null || echo "MISSING")

if [ "$CANDIDATE_STATUS" = "candidate" ]; then
  echo -e "${GREEN}✓ PASSED${NC}: Candidate status is 'candidate' (not active)"
  PHASE1_PASSED=$((PHASE1_PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC}: Candidate status is '$CANDIDATE_STATUS' (expected 'candidate')"
  PHASE1_FAILED=$((PHASE1_FAILED + 1))
fi

echo ""

# ======================================
# Summary
# ======================================
echo "======================================"
echo "Phase 1 Summary"
echo "======================================"
echo ""
echo "Passed: $PHASE1_PASSED"
echo "Failed: $PHASE1_FAILED"
echo ""

if [ "$PHASE1_FAILED" -eq 0 ]; then
  echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
  echo ""
  echo "Ready for Phase 2: Quiet-Window Database Verification"
  echo "See: docs/V6_QUIET_WINDOW_INTEGRITY_CHECK.md"
  echo ""
  exit 0
else
  echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
  echo ""
  echo "Review the errors above and fix before proceeding to Phase 2."
  echo ""
  exit 1
fi
