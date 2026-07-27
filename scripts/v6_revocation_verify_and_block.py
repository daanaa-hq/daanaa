#!/usr/bin/env python3
"""
v6_revocation_verify_and_block.py

Revocation verification and blocking behavior for v6 financial context.

Checks:
- Both irs_revoked and org_status are consistent
- No revoked organizations in active peer groups
- Blocks activation if violations found

Blocking behavior:
- If EITHER irs_revoked=1 OR org_status='revoked', organization is excluded from:
  - Tier 1, 2, 3, 4 peer groups
  - Scoring runs
  - Visible directory

Allowed in:
- Historical records (never deleted)
- Archive/reference data
- Revocation audit trail
"""

import sqlite3
import sys
from datetime import datetime
from typing import List, Tuple

DB_PATH = 'data/merit_registry.db'


def check_revocation_consistency(db_path: str) -> Tuple[bool, List[str]]:
    """
    Verify revocation consistency between irs_revoked and org_status.

    Returns: (is_consistent, list_of_mismatches)
    """
    errors = []

    try:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        print("\n🔍 REVOCATION CONSISTENCY CHECK")
        print("=" * 60)

        # 1. Check: irs_revoked=1 but org_status<>'revoked'
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM registry_enriched
            WHERE irs_revoked = 1 AND org_status <> 'revoked'
        ''')
        mismatch1 = cursor.fetchone()['cnt']
        if mismatch1 > 0:
            errors.append(
                f"Found {mismatch1} orgs with irs_revoked=1 but org_status≠'revoked'"
            )
            print(f"⚠️  Mismatch Type A: {mismatch1} orgs")
            print("   (irs_revoked=1 but org_status is not 'revoked')")

            # Show samples
            cursor.execute('''
                SELECT EIN, organization_name, irs_revoked, org_status
                FROM registry_enriched
                WHERE irs_revoked = 1 AND org_status <> 'revoked'
                LIMIT 5
            ''')
            for row in cursor.fetchall():
                print(f"   - {row['EIN']} {row['organization_name']}")

        # 2. Check: org_status='revoked' but irs_revoked<>1
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM registry_enriched
            WHERE org_status = 'revoked' AND irs_revoked <> 1
        ''')
        mismatch2 = cursor.fetchone()['cnt']
        if mismatch2 > 0:
            errors.append(
                f"Found {mismatch2} orgs with org_status='revoked' but irs_revoked≠1"
            )
            print(f"⚠️  Mismatch Type B: {mismatch2} orgs")
            print("   (org_status='revoked' but irs_revoked is not 1)")

            # Show samples
            cursor.execute('''
                SELECT EIN, organization_name, irs_revoked, org_status
                FROM registry_enriched
                WHERE org_status = 'revoked' AND irs_revoked <> 1
                LIMIT 5
            ''')
            for row in cursor.fetchall():
                print(f"   - {row['EIN']} {row['organization_name']}")

        if not errors:
            print("✅ CONSISTENCY CHECK PASSED")
            print("   irs_revoked and org_status are perfectly aligned")

        db.close()

    except Exception as e:
        errors.append(f"Database error: {e}")

    return len(errors) == 0, errors


def check_revoked_in_active_tiers(db_path: str, run_id: str) -> Tuple[bool, int, List[str]]:
    """
    Check for revoked organizations in active scoring tiers.

    Returns: (is_clean, count, list_of_errors)
    """
    errors = []

    try:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        print("\n🔍 REVOKED IN ACTIVE TIERS CHECK")
        print("=" * 60)

        # Check if run exists
        cursor.execute('SELECT run_id, status FROM v6_scoring_runs WHERE run_id = ?', (run_id,))
        run = cursor.fetchone()
        if not run:
            errors.append(f"Run {run_id} not found")
            return False, 0, errors

        print(f"Run: {run_id} (status: {run['status']})")

        # Query: revoked orgs in Tier 1-4
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM v6_peer_context_assignments a
            WHERE a.run_id = ?
            AND a.selected_tier IN ('1_direct', '2_regional_conditional', '3_broader_regional', '4_national')
            AND a.ein IN (
                SELECT EIN FROM registry_enriched
                WHERE irs_revoked = 1 OR org_status = 'revoked'
            )
        ''', (run_id,))

        revoked_count = cursor.fetchone()['cnt']

        if revoked_count > 0:
            errors.append(
                f"Found {revoked_count} revoked organizations in active tiers (Tier 1-4)"
            )
            print(f"❌ VIOLATION: {revoked_count} revoked orgs in active tiers")
            print("   This blocks scoring run activation")

            # Show samples
            cursor.execute('''
                SELECT DISTINCT a.ein, r.organization_name, a.selected_tier
                FROM v6_peer_context_assignments a
                JOIN registry_enriched r ON a.ein = r.EIN
                WHERE a.run_id = ?
                AND a.selected_tier IN ('1_direct', '2_regional_conditional', '3_broader_regional', '4_national')
                AND (r.irs_revoked = 1 OR r.org_status = 'revoked')
                LIMIT 5
            ''', (run_id,))

            print("\n   Samples (first 5):")
            for row in cursor.fetchall():
                print(f"   - {row['ein']} ({row['selected_tier']}) {row['organization_name']}")

        else:
            print("✅ CLEAN: No revoked organizations in active tiers")

        # Also report Tier 5 count (should have them all)
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM v6_peer_context_assignments a
            WHERE a.run_id = ?
            AND a.selected_tier = '5_archetype_only'
            AND a.ein IN (
                SELECT EIN FROM registry_enriched
                WHERE irs_revoked = 1 OR org_status = 'revoked'
            )
        ''', (run_id,))

        revoked_tier5 = cursor.fetchone()['cnt']
        print(f"   Revoked in Tier 5 (archetype-only): {revoked_tier5} ✅ (correct)")

        db.close()

    except Exception as e:
        errors.append(f"Database error: {e}")

    return revoked_count == 0, revoked_count, errors


def block_if_violations(db_path: str, run_id: str) -> Tuple[bool, List[str]]:
    """
    Block scoring run activation if revocation violations found.

    Returns: (should_proceed, list_of_blocking_errors)
    """
    blocking_errors = []

    print("\n" + "=" * 60)
    print("REVOCATION BLOCKING GATES")
    print("=" * 60)

    # Gate 1: Consistency check
    consistent, consistency_errors = check_revocation_consistency(db_path)
    if not consistent:
        blocking_errors.extend(consistency_errors)
        print("\n❌ BLOCKED: Revocation consistency check failed")

    # Gate 2: No revoked in active tiers
    clean, count, active_errors = check_revoked_in_active_tiers(db_path, run_id)
    if not clean:
        blocking_errors.extend(active_errors)
        print("\n❌ BLOCKED: Revoked organizations found in active tiers")

    if blocking_errors:
        print("\n" + "=" * 60)
        print("ACTIVATION BLOCKED")
        print("=" * 60)
        print("Cannot activate scoring run. Violations:")
        for i, err in enumerate(blocking_errors, 1):
            print(f"  {i}. {err}")
        print("\nAction required:")
        print("  1. Investigate revocation data source")
        print("  2. Repair mismatches manually (source-backed)")
        print("  3. Regenerate scoring run")
        print("  4. Re-run this validation")
        return False, blocking_errors

    print("\n" + "=" * 60)
    print("✅ ALL REVOCATION GATES PASSED")
    print("=" * 60)
    print("Scoring run is clear for activation (pending other checks)")
    return True, []


def main():
    if len(sys.argv) < 2:
        print("Usage: v6_revocation_verify_and_block.py <run_id> [db_path]")
        print("Example: v6_revocation_verify_and_block.py v6_foundation_candidate_20260728_revised")
        sys.exit(1)

    run_id = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else DB_PATH

    print("\n" + "=" * 60)
    print("V6 REVOCATION VERIFICATION & BLOCKING")
    print("=" * 60)
    print(f"Run ID: {run_id}")
    print(f"Database: {db_path}")

    should_proceed, errors = block_if_violations(db_path, run_id)

    sys.exit(0 if should_proceed else 1)


if __name__ == '__main__':
    main()
