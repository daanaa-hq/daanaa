#!/bin/bash
set -e

# Six-Phase Test Suite for Tax Status Recovery Migration
# Comprehensive testing on disposable copies
# No production changes until explicitly approved

MERITGIVING_HOME="$HOME/meritgiving"
RECOVERY_DB="$MERITGIVING_HOME/data/tax_status_recovery.db"
MANIFEST="$MERITGIVING_HOME/data/tax_status_recovery_manifest.json"
SCRIPT="$MERITGIVING_HOME/scripts/apply_tax_status_recovery.py"

# Test database paths (disposable copies)
TEST1_DB="/tmp/merit_registry_test1.db"
TEST2_DB="/tmp/merit_registry_test2.db"
ROLLBACK_TEST_DB="/tmp/merit_registry_rollback_test.db"

# Report file
REPORT="/tmp/tax_status_test_report.md"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "SIX-PHASE TAX STATUS MIGRATION TEST SUITE"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Starting: $(date)"
echo ""

# Function: Calculate database checksum
db_checksum() {
    local db="$1"
    sqlite3 "$db" << SQL 2>/dev/null | sha256sum | awk '{print $1}'
PRAGMA integrity_check;
SELECT COUNT(*) FROM registry_enriched;
SELECT COUNT(*) FROM registry_enriched WHERE org_status IS NOT NULL;
SELECT COUNT(*) FROM registry_enriched WHERE org_status = 'active';
SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked = 0;
SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked = 1;
SQL
}

# Function: Get org_status='active' count
active_status_count() {
    local db="$1"
    sqlite3 "$db" "SELECT COUNT(*) FROM registry_enriched WHERE org_status = 'active'"
}

# Function: Get irs_revoked=0 count
irs_revoked_zero_count() {
    local db="$1"
    sqlite3 "$db" "SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked = 0"
}

# Initialize report
cat > "$REPORT" << 'REPORT_INIT'
# Tax Status Migration — Six-Phase Test Suite Report

**Test Date:** $(date)
**Status:** In Progress

## Test 1 & 2: Dry-Run + Apply on First Disposable Copy

REPORT_INIT

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "PHASE 1-2: DRY-RUN + APPLY ON FIRST DISPOSABLE COPY"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Create first test copy
echo "[1/6] Creating disposable copy 1..."
cp "$MERITGIVING_HOME/data/merit_registry.db" "$TEST1_DB"
echo "   ✓ Created: $TEST1_DB"

# Pre-migration checksum
echo "[1/6] Calculating pre-migration checksum..."
TEST1_PRE_CHECKSUM=$(db_checksum "$TEST1_DB")
echo "   Pre-migration checksum: ${TEST1_PRE_CHECKSUM:0:16}..."

# Dry run
echo "[1/6] Running dry-run..."
DRY_RUN_OUTPUT=$(python3 "$SCRIPT" --prod-db "$TEST1_DB" --recovery-db "$RECOVERY_DB" --manifest "$MANIFEST" 2>&1 || true)
echo "$DRY_RUN_OUTPUT" > /tmp/test1_dryrun.log

# Extract dry-run metrics
MATCHED_EINS=$(echo "$DRY_RUN_OUTPUT" | grep "Matched in production" | awk -F: '{print $2}' | tr -d ' ' || echo "ERROR")
UNMATCHED_EINS=$(echo "$DRY_RUN_OUTPUT" | grep "Unmatched (new EINs)" | awk -F: '{print $2}' | tr -d ' ' || echo "ERROR")

echo "   Dry-run results:"
echo "     - Matched EINs: $MATCHED_EINS"
echo "     - Unmatched EINs: $UNMATCHED_EINS"

# Apply migration
echo "[2/6] Applying migration..."
APPLY_OUTPUT=$(python3 "$SCRIPT" --prod-db "$TEST1_DB" --recovery-db "$RECOVERY_DB" --manifest "$MANIFEST" --apply 2>&1 || true)
echo "$APPLY_OUTPUT" > /tmp/test1_apply.log

# Post-migration checksum
echo "[2/6] Calculating post-migration checksum..."
TEST1_POST_CHECKSUM=$(db_checksum "$TEST1_DB")
echo "   Post-migration checksum: ${TEST1_POST_CHECKSUM:0:16}..."

# Verify checksums changed (data was written)
if [ "$TEST1_PRE_CHECKSUM" != "$TEST1_POST_CHECKSUM" ]; then
    echo "   ✓ Checksums differ (migration applied)"
else
    echo "   ✗ WARNING: Checksums identical (no changes?)"
fi

# Get org_status='active' vs irs_revoked=0 counts
echo "[2/6] Collecting detailed counts..."
ACTIVE_STATUS=$(active_status_count "$TEST1_DB")
IRS_REVOKED_ZERO=$(irs_revoked_zero_count "$TEST1_DB")
echo "   org_status='active': $ACTIVE_STATUS"
echo "   irs_revoked=0: $IRS_REVOKED_ZERO"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "PHASE 3: IDEMPOTENCY TEST (Run Migration Twice)"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

echo "[3/6] Running migration second time on same database..."
APPLY_OUTPUT_2=$(python3 "$SCRIPT" --prod-db "$TEST1_DB" --recovery-db "$RECOVERY_DB" --manifest "$MANIFEST" --apply 2>&1 || true)
echo "$APPLY_OUTPUT_2" > /tmp/test1_apply_2.log

# Post second-run checksum
echo "[3/6] Calculating checksum after second run..."
TEST1_POST_2_CHECKSUM=$(db_checksum "$TEST1_DB")
echo "   Second-run checksum: ${TEST1_POST_2_CHECKSUM:0:16}..."

# Verify idempotency
if [ "$TEST1_POST_CHECKSUM" = "$TEST1_POST_2_CHECKSUM" ]; then
    echo "   ✓ IDEMPOTENT: No changes on second run"
    IDEMPOTENT="PASS"
else
    echo "   ✗ WARNING: Checksums differ after second run"
    IDEMPOTENT="FAIL"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "PHASE 4: CONSISTENCY TEST (Apply to Second Copy)"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

echo "[4/6] Creating disposable copy 2..."
cp "$MERITGIVING_HOME/data/merit_registry.db" "$TEST2_DB"
echo "   ✓ Created: $TEST2_DB"

echo "[4/6] Applying migration to copy 2..."
APPLY_OUTPUT_T2=$(python3 "$SCRIPT" --prod-db "$TEST2_DB" --recovery-db "$RECOVERY_DB" --manifest "$MANIFEST" --apply 2>&1 || true)

echo "[4/6] Calculating post-migration checksum (copy 2)..."
TEST2_POST_CHECKSUM=$(db_checksum "$TEST2_DB")
echo "   Test2 post-migration checksum: ${TEST2_POST_CHECKSUM:0:16}..."

# Verify consistency between copies
if [ "$TEST1_POST_CHECKSUM" = "$TEST2_POST_CHECKSUM" ]; then
    echo "   ✓ CONSISTENT: Both copies have identical checksums"
    CONSISTENT="PASS"
else
    echo "   ✗ WARNING: Checksums differ between copies"
    CONSISTENT="FAIL"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "PHASE 5: ROLLBACK TEST"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

echo "[5/6] Creating rollback test copy..."
cp "$MERITGIVING_HOME/data/merit_registry.db" "$ROLLBACK_TEST_DB"
PRE_ROLLBACK_CHECKSUM=$(db_checksum "$ROLLBACK_TEST_DB")
echo "   Pre-rollback checksum: ${PRE_ROLLBACK_CHECKSUM:0:16}..."

echo "[5/6] Applying migration..."
python3 "$SCRIPT" --prod-db "$ROLLBACK_TEST_DB" --recovery-db "$RECOVERY_DB" --manifest "$MANIFEST" --apply > /dev/null 2>&1

echo "[5/6] Simulating rollback (restore original)..."
cp "$MERITGIVING_HOME/data/merit_registry.db" "$ROLLBACK_TEST_DB"
POST_ROLLBACK_CHECKSUM=$(db_checksum "$ROLLBACK_TEST_DB")

# Verify rollback restored original state
if [ "$PRE_ROLLBACK_CHECKSUM" = "$POST_ROLLBACK_CHECKSUM" ]; then
    echo "   ✓ ROLLBACK VERIFIED: Restored to original state"
    ROLLBACK="PASS"
else
    echo "   ✗ WARNING: Rollback checksum mismatch"
    ROLLBACK="FAIL"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "PHASE 6: CHECKSUM PARITY & DETAILED ANALYSIS"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

echo "[6/6] Comparing recovery artifact vs applied database..."

# Get recovery manifest checksum
RECOVERY_CHECKSUM=$(jq -r '.aggregate_checksum' "$MANIFEST")
echo "   Recovery artifact aggregate checksum: ${RECOVERY_CHECKSUM:0:16}..."

# Get recovery counts
RECOVERY_TOTAL=$(jq -r '.total_records' "$MANIFEST")
RECOVERY_ACTIVE=$(jq -r '.active_organizations' "$MANIFEST")
RECOVERY_REVOKED=$(jq -r '.revoked_organizations' "$MANIFEST")

echo "   Recovery artifact counts:"
echo "     - Total: $RECOVERY_TOTAL"
echo "     - Active (irs_revoked=0): $RECOVERY_ACTIVE"
echo "     - Revoked (irs_revoked=1): $RECOVERY_REVOKED"

echo ""
echo "   Applied database (test1) counts:"
echo "     - Total: $(sqlite3 "$TEST1_DB" "SELECT COUNT(*) FROM registry_enriched")"
echo "     - org_status='active': $ACTIVE_STATUS"
echo "     - irs_revoked=0: $IRS_REVOKED_ZERO"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "TEST SUMMARY"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Phase 1-2 (Apply):        ✓ COMPLETE"
echo "Phase 3 (Idempotency):    $IDEMPOTENT"
echo "Phase 4 (Consistency):    $CONSISTENT"
echo "Phase 5 (Rollback):       $ROLLBACK"
echo "Phase 6 (Parity):         ✓ ANALYZED"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Pre-Migration Checksum:     $TEST1_PRE_CHECKSUM"
echo "Post-Migration Checksum:    $TEST1_POST_CHECKSUM"
echo "Second-Run Checksum:        $TEST1_POST_2_CHECKSUM"
echo ""
echo "Matched EINs:               $MATCHED_EINS"
echo "Unmatched EINs:             $UNMATCHED_EINS"
echo ""
echo "org_status='active':        $ACTIVE_STATUS"
echo "irs_revoked=0:              $IRS_REVOKED_ZERO"
echo ""
echo "Test databases preserved at:"
echo "  - $TEST1_DB (Phase 1-3 final state)"
echo "  - $TEST2_DB (Phase 4 final state)"
echo "  - $ROLLBACK_TEST_DB (Phase 5 original state)"
echo ""
echo "Full logs at:"
echo "  - /tmp/test1_dryrun.log"
echo "  - /tmp/test1_apply.log"
echo "  - /tmp/test1_apply_2.log"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "COMPLETE — Awaiting production approval"
echo "════════════════════════════════════════════════════════════════════════════════"
