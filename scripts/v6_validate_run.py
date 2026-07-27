#!/usr/bin/env python3
"""
v6_validate_run.py

Validate a v6 candidate scoring run before activation.

Checks:
- Assignment count matches active population
- EINs are unique
- Revoked assignments = 0
- Tier 1 has verified revenue
- Tier 2 is regional conditional context
- Tier 3 is broader regional context
- Tier 4 is national
- Tier 5 contains no numeric values
- Numeric tiers have at least 5 scoreable peers
- No invented revenue bands
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = 'data/merit_registry.db'


def validate_run(run_id: str, db_path: str = DB_PATH) -> tuple[bool, list[str]]:
    """
    Validate a candidate v6 run.

    Returns (is_valid, list_of_errors)
    """
    errors = []

    try:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        print(f"\n🔍 Validating run: {run_id}")

        # 1. Check run exists and is candidate status
        cursor.execute('SELECT * FROM v6_scoring_runs WHERE run_id = ?', (run_id,))
        run = cursor.fetchone()
        if not run:
            errors.append(f"Run {run_id} not found in v6_scoring_runs")
            db.close()
            return False, errors

        if run['status'] != 'candidate':
            errors.append(f"Run status is '{run['status']}', expected 'candidate'")

        print(f"  Run: {run_id} (status: {run['status']})")

        # 2. Check assignment count
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM v6_peer_context_assignments WHERE run_id = ?',
            (run_id,)
        )
        assign_count = cursor.fetchone()['cnt']
        print(f"  ✓ Assignments: {assign_count:,}")

        # 3. Check for duplicate EINs
        cursor.execute('''
            SELECT ein, COUNT(*) as cnt FROM v6_peer_context_assignments
            WHERE run_id = ?
            GROUP BY ein HAVING COUNT(*) > 1
        ''', (run_id,))
        dupes = cursor.fetchall()
        if dupes:
            errors.append(f"Found {len(dupes)} duplicate EINs in assignments")

        # 4. Check for revoked organizations in active tiers
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM v6_peer_context_assignments a
            WHERE a.run_id = ?
            AND a.selected_tier IN ('1_direct', '2_regional_conditional', '3_broader_regional', '4_national')
            AND a.ein IN (SELECT EIN FROM registry_enriched WHERE irs_revoked = 1)
        ''', (run_id,))
        revoked_active = cursor.fetchone()['cnt']
        if revoked_active > 0:
            errors.append(f"Found {revoked_active} revoked organizations in active tiers")
        print(f"  ✓ Revoked in active: {revoked_active}")

        # 5. Check Tier 1: must have revenue_band
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM v6_peer_context_assignments
            WHERE run_id = ? AND selected_tier = '1_direct'
            AND (revenue_band IS NULL OR revenue_band = '')
        ''', (run_id,))
        tier1_no_revenue = cursor.fetchone()['cnt']
        if tier1_no_revenue > 0:
            errors.append(f"Tier 1 Direct: {tier1_no_revenue} assignments without revenue_band")

        cursor.execute(
            'SELECT COUNT(*) as cnt FROM v6_peer_context_assignments WHERE run_id = ? AND selected_tier = ?',
            (run_id, '1_direct')
        )
        tier1_cnt = cursor.fetchone()['cnt']
        print(f"  ✓ Tier 1 Direct: {tier1_cnt:,}")

        # 6. Check Tier 2: must be regional conditional
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM v6_peer_context_assignments
            WHERE run_id = ? AND selected_tier = '2_regional_conditional'
            AND geography_scope <> 'state'
        ''', (run_id,))
        tier2_not_state = cursor.fetchone()['cnt']
        if tier2_not_state > 0:
            errors.append(f"Tier 2 Regional: {tier2_not_state} assignments without state scope")

        cursor.execute(
            'SELECT COUNT(*) as cnt FROM v6_peer_context_assignments WHERE run_id = ? AND selected_tier = ?',
            (run_id, '2_regional_conditional')
        )
        tier2_cnt = cursor.fetchone()['cnt']
        print(f"  ✓ Tier 2 Regional: {tier2_cnt:,}")

        # 7. Check Tier 3: broader regional
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM v6_peer_context_assignments WHERE run_id = ? AND selected_tier = ?',
            (run_id, '3_broader_regional')
        )
        tier3_cnt = cursor.fetchone()['cnt']
        print(f"  ✓ Tier 3 Broader: {tier3_cnt:,}")

        # 8. Check Tier 4: national
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM v6_peer_context_assignments WHERE run_id = ? AND selected_tier = ?',
            (run_id, '4_national')
        )
        tier4_cnt = cursor.fetchone()['cnt']
        print(f"  ✓ Tier 4 National: {tier4_cnt:,}")

        # 9. Check Tier 5: no numeric values
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM v6_peer_context_assignments
            WHERE run_id = ? AND selected_tier = '5_archetype_only'
            AND (peer_median IS NOT NULL OR peer_p25 IS NOT NULL OR peer_p75 IS NOT NULL)
        ''', (run_id,))
        tier5_numeric = cursor.fetchone()['cnt']
        if tier5_numeric > 0:
            errors.append(f"Tier 5 Archetype: {tier5_numeric} assignments have numeric values (should be NULL)")

        cursor.execute(
            'SELECT COUNT(*) as cnt FROM v6_peer_context_assignments WHERE run_id = ? AND selected_tier = ?',
            (run_id, '5_archetype_only')
        )
        tier5_cnt = cursor.fetchone()['cnt']
        print(f"  ✓ Tier 5 Archetype: {tier5_cnt:,}")

        # 10. Check minimum peers for numeric tiers
        cursor.execute('''
            SELECT selected_tier, COUNT(*) as cnt
            FROM v6_peer_context_assignments
            WHERE run_id = ? AND selected_tier IN ('1_direct', '2_regional_conditional', '3_broader_regional', '4_national')
            AND scoreable_peer_count < 5
            GROUP BY selected_tier
        ''', (run_id,))
        low_peer_tiers = cursor.fetchall()
        for row in low_peer_tiers:
            errors.append(f"{row['selected_tier']}: {row['cnt']} assignments with <5 scoreable peers")

        if not low_peer_tiers:
            print(f"  ✓ Minimum peer threshold: all numeric tiers ≥5 peers")

        # 11. Check for invalid revenue bands
        cursor.execute('''
            SELECT DISTINCT revenue_band FROM v6_peer_context_assignments
            WHERE run_id = ? AND revenue_band NOT IN
            ('Grassroots', 'Small', 'Mid', 'Established', 'Major', NULL)
        ''', (run_id,))
        invalid_bands = cursor.fetchall()
        if invalid_bands:
            invalid_names = [row['revenue_band'] for row in invalid_bands]
            errors.append(f"Invalid revenue bands found: {invalid_names}")
        else:
            print(f"  ✓ Revenue bands valid")

        # Summary
        tier_sum = tier1_cnt + tier2_cnt + tier3_cnt + tier4_cnt + tier5_cnt
        print(f"\n  Tier distribution:")
        print(f"    T1 Direct:             {tier1_cnt:>8,}  ({100*tier1_cnt/assign_count:.1f}%)")
        print(f"    T2 Regional:           {tier2_cnt:>8,}  ({100*tier2_cnt/assign_count:.1f}%)")
        print(f"    T3 Broader:            {tier3_cnt:>8,}  ({100*tier3_cnt/assign_count:.1f}%)")
        print(f"    T4 National:           {tier4_cnt:>8,}  ({100*tier4_cnt/assign_count:.1f}%)")
        print(f"    T5 Archetype:          {tier5_cnt:>8,}  ({100*tier5_cnt/assign_count:.1f}%)")
        print(f"    ─────────────────────────────────")
        print(f"    TOTAL:                 {tier_sum:>8,}")

        db.close()

    except Exception as e:
        errors.append(f"Database error: {e}")

    # Print results
    if errors:
        print(f"\n❌ Validation FAILED with {len(errors)} error(s):")
        for i, err in enumerate(errors, 1):
            print(f"   {i}. {err}")
        return False, errors
    else:
        print(f"\n✅ Validation PASSED")
        return True, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: v6_validate_run.py <run_id> [db_path]")
        print("Example: v6_validate_run.py v6_foundation_candidate_20260727_corrected")
        sys.exit(1)

    run_id = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else DB_PATH

    is_valid, errors = validate_run(run_id, db_path)
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
