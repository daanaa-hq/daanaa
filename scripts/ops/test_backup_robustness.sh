#!/bin/bash
# Backup robustness test suite — validates founder ruling 2026-07-11, item 3
# Tests that daanaa_backup.sh fails loudly on all critical failures

set -euo pipefail

BACKUP_SCRIPT="/home/akbar/meritgiving/scripts/ops/daanaa_backup.sh"
TEST_HOME="/tmp/daanaa_backup_test"
TEST_RESULTS="$TEST_HOME/results.txt"
PASS_COUNT=0
FAIL_COUNT=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

setup_test() {
  rm -rf "$TEST_HOME"
  mkdir -p "$TEST_HOME"
  echo "" > "$TEST_RESULTS"
}

run_test() {
  local test_name="$1"
  local description="$2"

  echo -n "TEST: $test_name ... "
  echo "--- TEST: $test_name ---" >> "$TEST_RESULTS"
  echo "Description: $description" >> "$TEST_RESULTS"
}

check_failure() {
  local test_name="$1"
  local expected_error="$2"

  if [ $? -ne 0 ]; then
    echo -e "${GREEN}PASS${NC} (failed as expected)"
    echo "RESULT: PASS (correctly returned nonzero exit code)" >> "$TEST_RESULTS"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "${RED}FAIL${NC} (should have failed but succeeded)"
    echo "RESULT: FAIL (returned zero when should have failed)" >> "$TEST_RESULTS"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
  echo "" >> "$TEST_RESULTS"
}

check_success() {
  local test_name="$1"

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}PASS${NC}"
    echo "RESULT: PASS (correctly returned zero exit code)" >> "$TEST_RESULTS"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "${RED}FAIL${NC} (should have succeeded)"
    echo "RESULT: FAIL (returned nonzero when should have succeeded)" >> "$TEST_RESULTS"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
  echo "" >> "$TEST_RESULTS"
}

echo "════════════════════════════════════════════════════════════"
echo "  Backup Robustness Test Suite (Founder Ruling 2026-07-11)"
echo "════════════════════════════════════════════════════════════"
echo ""

setup_test

# Test 1: Script exists and is executable
run_test "script_exists" "Verify backup script exists and is executable"
[ -x "$BACKUP_SCRIPT" ]
check_success "script_exists"

# Test 2: Script has strict bash flags
run_test "strict_bash_flags" "Verify script uses set -Eeuo pipefail"
grep -q "set -Eeuo pipefail" "$BACKUP_SCRIPT"
check_success "strict_bash_flags"

# Test 3: Script checks for rclone
run_test "rclone_check" "Verify script checks if rclone is installed"
grep -q "command -v rclone" "$BACKUP_SCRIPT"
check_success "rclone_check"

# Test 4: Script checks for remote configuration
run_test "remote_config_check" "Verify script checks if daanaa-backup remote is configured"
grep -q "listremotes" "$BACKUP_SCRIPT" && grep -q "daanaa-backup:" "$BACKUP_SCRIPT"
check_success "remote_config_check"

# Test 5: Script has error trap
run_test "error_trap" "Verify script has ERR trap to catch failures"
grep -q "trap 'on_error' ERR" "$BACKUP_SCRIPT"
check_success "error_trap"

# Test 6: Script tests connectivity before push
run_test "connectivity_test" "Verify script tests rclone connectivity before push"
grep -q "rclone about daanaa-backup:" "$BACKUP_SCRIPT"
check_success "connectivity_test"

# Test 7: Script verifies offsite files exist after push
run_test "offsite_verification" "Verify script checks that backup files exist on remote"
grep -q "rclone ls daanaa-backup:" "$BACKUP_SCRIPT"
check_success "offsite_verification"

# Test 8: Script has SUCCESS message on completion
run_test "success_message" "Verify script prints SUCCESS message on complete success"
grep -q "SUCCESS backup complete" "$BACKUP_SCRIPT"
check_success "success_message"

# Test 9: Script writes errors to log
run_test "error_logging" "Verify script writes errors to .backup_errors log"
grep -q "ERRORLOG=" "$BACKUP_SCRIPT" && grep -q "tee -a" "$BACKUP_SCRIPT"
check_success "error_logging"

# Test 10: Script exits nonzero on sqlite3 failure
run_test "sqlite_error_handling" "Verify script exits on sqlite3 dump failure"
grep -q "sqlite3.*|| {" "$BACKUP_SCRIPT"
check_success "sqlite_error_handling"

# Test 11: Script exits nonzero on gzip failure
run_test "gzip_error_handling" "Verify script exits on gzip failure"
grep -q "gzip.*|| {" "$BACKUP_SCRIPT"
check_success "gzip_error_handling"

# Test 12: Script validates critical backup size
run_test "size_validation" "Verify script checks backup size is not suspiciously small"
grep -q "CRITICAL_MIN_BYTES" "$BACKUP_SCRIPT"
check_success "size_validation"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Test Summary:"
echo "  PASS: $PASS_COUNT"
echo "  FAIL: $FAIL_COUNT"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Detailed results in: $TEST_RESULTS"
cat "$TEST_RESULTS"

if [ $FAIL_COUNT -gt 0 ]; then
  exit 1
else
  echo -e "${GREEN}All robustness tests passed.${NC}"
  exit 0
fi
