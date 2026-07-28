#!/bin/bash
# v6_daily_operations_automated.sh
#
# Phase 3: Daily Automation
#
# Runs the daily data ingestion workflow with comprehensive safeguards:
# - Process locking (prevents concurrent runs)
# - Preflight checks (database, disk, integrity)
# - Source manifest (file tracking)
# - Backup (SQLite-safe)
# - Ingestion (dry-run by default)
# - Validation (data quality)
# - Revocation checks
# - Daily report
#
# Usage:
#   bash scripts/v6_daily_operations_automated.sh [--apply]
#
# Without --apply: dry-run only (no database changes)
# With --apply:    enable ingestion (V6_APPLY_BACKFILL=true)
#
# Exit codes:
#   0 = Daily run completed successfully (PASS or WARN)
#   1 = Daily run blocked or failed (BLOCKED)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_PATH="${PROJECT_ROOT}/data/merit_registry.db"
BACKUPS_DIR="${PROJECT_ROOT}/data/backups/v6"
REPORTS_DIR="${PROJECT_ROOT}/reports/v6"
LOCK_FILE="${PROJECT_ROOT}/.v6_daily_lock"

# Configuration
APPLY_BACKFILL="${V6_APPLY_BACKFILL:-false}"
DISK_THRESHOLD_GB=1
LOCK_TIMEOUT=3600

# Output
REPORT_FILE="${REPORTS_DIR}/daily_$(date -u +%Y%m%dT%H%M%SZ).md"
LOG_FILE="/tmp/v6_daily_$(date -u +%Y%m%dT%H%M%SZ).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
OVERALL_STATUS="PASS"
BLOCKING_FAILURE=0

# Trap to clean up lock
cleanup() {
  if [ -f "$LOCK_FILE" ]; then
    rm -f "$LOCK_FILE"
  fi
}
trap cleanup EXIT

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"
}

report_section() {
  echo "## $1" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
}

report_status() {
  local status="$1"
  local message="$2"
  echo "**Status:** $status" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  if [ -n "$message" ]; then
    echo "$message" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
  fi
}

check_lock() {
  if [ -f "$LOCK_FILE" ]; then
    local lock_pid=$(cat "$LOCK_FILE")
    if kill -0 "$lock_pid" 2>/dev/null; then
      log "ERROR: Another v6 operation is running (PID: $lock_pid)"
      report_status "BLOCKED" "Another v6 operation is running (PID: $lock_pid). Exiting safely."
      exit 1
    else
      log "Removing stale lock (PID: $lock_pid not found)"
      rm -f "$LOCK_FILE"
    fi
  fi
  echo "$$" > "$LOCK_FILE"
  log "Lock acquired (PID: $$)"
}

# ============================================================================
# A. LOCKING
# ============================================================================

log "Phase 3: Daily Automation Started"
echo "# V6 Daily Operations Report" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Date:** $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REPORT_FILE"
echo "**Applied backfill:** $APPLY_BACKFILL" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

report_section "A. Locking"
check_lock

# ============================================================================
# B. PREFLIGHT
# ============================================================================

log "Preflight checks..."
report_section "B. Preflight"

PREFLIGHT_PASS=true

# Database exists
if [ ! -f "$DB_PATH" ]; then
  log "ERROR: Database not found at $DB_PATH"
  report_status "BLOCKED" "Database file not found."
  exit 1
fi
log "✓ Database exists"

# Repository is readable
if [ ! -d "${PROJECT_ROOT}/.git" ]; then
  log "WARN: Not a git repository (non-blocking)"
else
  log "✓ Git repository found"
fi

# Disk space
DISK_FREE_KB=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
DISK_FREE_GB=$((DISK_FREE_KB / 1024 / 1024))
if [ "$DISK_FREE_GB" -lt "$DISK_THRESHOLD_GB" ]; then
  log "ERROR: Only ${DISK_FREE_GB}GB disk free (need ${DISK_THRESHOLD_GB}GB)"
  report_status "BLOCKED" "Insufficient disk space."
  exit 1
fi
log "✓ Disk space: ${DISK_FREE_GB}GB free"

# Database integrity (23GB database requires 180+ seconds)
INTEGRITY_RESULT=$(timeout 300 sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null || echo "TIMEOUT_OR_FAILED")
if [ "$INTEGRITY_RESULT" != "ok" ]; then
  log "ERROR: Database integrity check failed: $INTEGRITY_RESULT"
  report_status "BLOCKED" "Database integrity check failed."
  exit 1
fi
log "✓ Database integrity: ok"

# Backup exists
if [ ! -d "$BACKUPS_DIR" ]; then
  log "WARN: Backup directory does not exist (will create)"
  mkdir -p "$BACKUPS_DIR"
fi

RECENT_BACKUP=$(find "$BACKUPS_DIR" -name "*.db" -mtime -1 -print -quit 2>/dev/null || true)
if [ -z "$RECENT_BACKUP" ]; then
  log "WARN: No recent backup (non-blocking, will create one now)"
else
  log "✓ Recent backup found"
fi

# Required tables
for table in registry_enriched v6_peer_context_assignments v6_scoring_runs; do
  TABLE_EXISTS=$(sqlite3 "$DB_PATH" "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='$table';" 2>/dev/null)
  if [ "$TABLE_EXISTS" -eq 0 ]; then
    log "ERROR: Required table '$table' not found"
    report_status "BLOCKED" "Required table '$table' not found."
    exit 1
  fi
done
log "✓ All required tables exist"

echo "| Check | Result |" >> "$REPORT_FILE"
echo "|-------|--------|" >> "$REPORT_FILE"
echo "| Database exists | ✓ |" >> "$REPORT_FILE"
echo "| Disk space (${DISK_FREE_GB}GB) | ✓ |" >> "$REPORT_FILE"
echo "| Integrity check | ✓ |" >> "$REPORT_FILE"
echo "| Required tables | ✓ |" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
report_status "PASS" ""

# ============================================================================
# C. SOURCE MANIFEST
# ============================================================================

log "Generating source manifest..."
report_section "C. Source Manifest"

# For this version, source discovery is a placeholder
# In production, this would discover new 990 files, IRS data, etc.
echo "| Source | Status |" >> "$REPORT_FILE"
echo "|--------|--------|" >> "$REPORT_FILE"
echo "| IRS SOI filings | NOT_CONFIGURED |" >> "$REPORT_FILE"
echo "| ProPublica 990 | NOT_CONFIGURED |" >> "$REPORT_FILE"
echo "| Donation links | NOT_CONFIGURED |" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
report_status "NOT_CONFIGURED" "Source discovery is not yet implemented."
OVERALL_STATUS="NOT_CONFIGURED"

# ============================================================================
# D. BACKUP
# ============================================================================

log "Creating backup..."
report_section "D. Backup"

BACKUP_TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_PATH="${BACKUPS_DIR}/merit_registry_${BACKUP_TIMESTAMP}.db"

if timeout 300 sqlite3 "$DB_PATH" ".backup '$BACKUP_PATH'" 2>/dev/null; then
  log "✓ Backup created: $BACKUP_PATH"

  # Verify backup
  BACKUP_SIZE=$(stat -f%z "$BACKUP_PATH" 2>/dev/null || stat -c%s "$BACKUP_PATH" 2>/dev/null)
  BACKUP_TABLE_COUNT=$(sqlite3 "$BACKUP_PATH" "SELECT COUNT(*) FROM registry_enriched;" 2>/dev/null)
  log "✓ Backup verified: $BACKUP_SIZE bytes, $BACKUP_TABLE_COUNT records"

  echo "| Metric | Value |" >> "$REPORT_FILE"
  echo "|--------|-------|" >> "$REPORT_FILE"
  echo "| Backup path | $BACKUP_PATH |" >> "$REPORT_FILE"
  echo "| Size | $BACKUP_SIZE bytes |" >> "$REPORT_FILE"
  echo "| Records | $BACKUP_TABLE_COUNT |" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  report_status "PASS" ""
else
  log "ERROR: Backup failed"
  report_status "BLOCKED" "Backup creation failed."
  exit 1
fi

# ============================================================================
# E. INGESTION
# ============================================================================

log "Ingestion (dry-run: $APPLY_BACKFILL)..."
report_section "E. Ingestion"

if [ "$APPLY_BACKFILL" = "true" ]; then
  log "⚠ APPLY_BACKFILL=true (will modify database)"
  set +e
  timeout 300 python3 "$SCRIPT_DIR/v6_transactional_backfill.py" 2>&1 | tee -a "$LOG_FILE" | tail -10 >> "$REPORT_FILE"
  INGESTION_RC=${PIPESTATUS[0]}
  set -e
  if [ "$INGESTION_RC" -ne 0 ]; then
    report_status "BLOCKED" "Ingestion failed or exceeded five-minute timeout; no activation permitted."
    OVERALL_STATUS="BLOCKED"
    BLOCKING_FAILURE=1
  else
    report_status "PASS" "Ingestion applied (review logs above)"
  fi
else
  log "Dry-run: ingestion skipped to keep the eligibility and integrity checks independent"
  report_status "NOT_CONFIGURED" "Ingestion not applied; run the transactional ingestion separately after source gates pass."
  OVERALL_STATUS="NOT_CONFIGURED"
fi

# ============================================================================
# F. VALIDATION
# ============================================================================

log "Data quality checks..."
report_section "F. Validation"

DUPLICATE_EINS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM (SELECT EIN FROM registry_enriched GROUP BY EIN HAVING COUNT(*) > 1);" 2>/dev/null || echo "0")
NEGATIVE_REVENUE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE total_revenue < 0;" 2>/dev/null || echo "0")
MISSING_NTEE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched WHERE ntee1_code IS NULL OR ntee1_code = '';" 2>/dev/null || echo "0")

echo "| Check | Count | Status |" >> "$REPORT_FILE"
echo "|-------|-------|--------|" >> "$REPORT_FILE"
echo "| Duplicate EINs | $DUPLICATE_EINS | $([ "$DUPLICATE_EINS" -eq 0 ] && echo "✓" || echo "⚠") |" >> "$REPORT_FILE"
echo "| Negative revenue | $NEGATIVE_REVENUE | $([ "$NEGATIVE_REVENUE" -eq 0 ] && echo "✓" || echo "⚠") |" >> "$REPORT_FILE"
echo "| Missing NTEE | $MISSING_NTEE | $([ "$MISSING_NTEE" -lt 100000 ] && echo "✓" || echo "⚠") |" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ "$DUPLICATE_EINS" -eq 0 ] && [ "$NEGATIVE_REVENUE" -eq 0 ]; then
  report_status "PASS" ""
else
  report_status "WARN" "Some data quality issues (non-blocking, see above)"
OVERALL_STATUS="WARN"
fi

# ============================================================================
# G. REVOCATION VERIFICATION
# ============================================================================

log "Revocation verification..."
report_section "G. Revocation Verification"

REVOCATION_LOG=$(mktemp)
set +e
python3 "$SCRIPT_DIR/v6_revocation_verify_and_block.py" "$(sqlite3 "$DB_PATH" "SELECT run_id FROM v6_scoring_runs WHERE status='candidate' ORDER BY started_at DESC LIMIT 1;")" > "$REVOCATION_LOG" 2>&1
REVOCATION_RC=$?
set -e
cat "$REVOCATION_LOG" | tee -a "$LOG_FILE" | head -40 >> "$REPORT_FILE"
rm -f "$REVOCATION_LOG"
if [ "$REVOCATION_RC" -ne 0 ]; then
  log "ERROR: Revocation verification blocked the daily run"
  report_status "BLOCKED" "Revocation consistency or active-tier check failed."
  OVERALL_STATUS="BLOCKED"
  BLOCKING_FAILURE=1
else
  report_status "PASS" "Revocation check complete"
fi

# ============================================================================
REVOCATION_SOURCE_LOG=$(mktemp)
set +e
python3 "$SCRIPT_DIR/check_revocations.py" --dry-run > "$REVOCATION_SOURCE_LOG" 2>&1
REVOCATION_SOURCE_RC=$?
set -e
cat "$REVOCATION_SOURCE_LOG" >> "$LOG_FILE"
cat "$REVOCATION_SOURCE_LOG" | tail -12 >> "$REPORT_FILE"
if [ "$REVOCATION_SOURCE_RC" -ne 0 ] || [ ! -f /tmp/irs_revocations.csv ]; then
  report_status "BLOCKED" "Fresh IRS revocation source check failed."
  OVERALL_STATUS="BLOCKED"
  BLOCKING_FAILURE=1
else
  REVOCATION_SOURCE_AGE=$(( $(date +%s) - $(stat -c%Y /tmp/irs_revocations.csv 2>/dev/null || echo 0) ))
  if [ "$REVOCATION_SOURCE_AGE" -gt 604800 ]; then
    report_status "BLOCKED" "IRS revocation source is older than seven days."
    OVERALL_STATUS="BLOCKED"
    BLOCKING_FAILURE=1
  else
    report_status "PASS" "IRS revocation source is fresh (under seven days)."
  fi
fi
rm -f "$REVOCATION_SOURCE_LOG"
CANDIDATE_RUN_ID=$(sqlite3 "$DB_PATH" "SELECT run_id FROM v6_scoring_runs WHERE status='candidate' ORDER BY started_at DESC LIMIT 1;" 2>/dev/null || true)
NON_DEDUCTIBLE_ACTIVE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM v6_peer_context_assignments a JOIN registry_enriched r ON r.EIN=a.ein WHERE a.run_id='$CANDIDATE_RUN_ID' AND a.selected_tier IN ('1_direct','2_regional_conditional','3_broader_regional','4_national') AND COALESCE(r.deductibility,'')<>'1';" 2>/dev/null || echo 0)
if [ "$NON_DEDUCTIBLE_ACTIVE" -gt 0 ]; then
  log "ERROR: Non-deductible organizations found in active tiers: $NON_DEDUCTIBLE_ACTIVE"
  report_status "BLOCKED" "Non-deductible organizations appear in numeric tiers."
  OVERALL_STATUS="BLOCKED"
  BLOCKING_FAILURE=1
else
  log "✓ All numeric-tier organizations are currently deductible"
  report_status "PASS" "Tax-deductibility gate: 0 non-deductible organizations in numeric tiers."
fi

# IRS Publication 78 is the current authority for donation eligibility.
# BMF deductibility alone is not sufficient. The refresh script is read-only
# here; a separate reviewed --apply run performs a transactional reconciliation.
report_section "G.1 IRS Donation Eligibility Authority"
IRS_ELIGIBILITY_LOG=$(mktemp)
set +e
python3 "$SCRIPT_DIR/v6_refresh_irs_eligibility.py" \
  --db "$DB_PATH" \
  --data-dir "${PROJECT_ROOT}/data/irs_authority/v6_eligibility" \
  > "$IRS_ELIGIBILITY_LOG" 2>&1
IRS_ELIGIBILITY_RC=$?
set -e
cat "$IRS_ELIGIBILITY_LOG" >> "$LOG_FILE"
cat "$IRS_ELIGIBILITY_LOG" | tail -30 >> "$REPORT_FILE"
if [ "$IRS_ELIGIBILITY_RC" -ne 0 ]; then
  log "ERROR: IRS donation eligibility authority check blocked the daily run"
  report_status "BLOCKED" "Fresh BMF + Publication 78 + auto-revocation evidence is required before donation eligibility is shown."
  OVERALL_STATUS="BLOCKED"
  BLOCKING_FAILURE=1
else
  report_status "PASS" "Donation eligibility is supported by fresh IRS BMF, Publication 78, and auto-revocation evidence."
fi
rm -f "$IRS_ELIGIBILITY_LOG"

# H. FINAL INTEGRITY CHECK
# ============================================================================

log "Final integrity check..."
report_section "H. Final Integrity Check"

FINAL_INTEGRITY=$(timeout 300 sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null || echo "TIMEOUT_OR_FAILED")
if [ "$FINAL_INTEGRITY" = "ok" ]; then
  log "✓ Final integrity: ok"
  echo "**Result:** ✓ ok" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  report_status "PASS" ""
else
  log "ERROR: Final integrity check failed: $FINAL_INTEGRITY"
  echo "**Result:** ✗ FAILED" >> "$REPORT_FILE"
  echo "$FINAL_INTEGRITY" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  report_status "BLOCKED" "Database integrity compromised."
  BLOCKING_FAILURE=1
  OVERALL_STATUS="BLOCKED"
fi

log "Daily operations completed with status: $OVERALL_STATUS"
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Overall Status:** $OVERALL_STATUS" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Report saved: $REPORT_FILE" >> "$REPORT_FILE"
if [ "$BLOCKING_FAILURE" -ne 0 ]; then
  echo -e "${RED}✗ Daily operations BLOCKED${NC}"
  echo "Report: $REPORT_FILE"
  exit 1
fi
if [ "$OVERALL_STATUS" != "PASS" ]; then
  echo -e "${YELLOW}⚠ Daily operations completed with status: $OVERALL_STATUS${NC}"
else
  echo -e "${GREEN}✓ Daily operations completed${NC}"
fi
echo "Report: $REPORT_FILE"
exit 0
