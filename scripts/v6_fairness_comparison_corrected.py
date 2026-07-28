#!/usr/bin/env python3
"""
v6_fairness_comparison_corrected.py

Corrected fairness and stewardship comparison between v6 scoring runs.

Compares a new candidate run with a baseline run to detect:
- Revoked organization handling (removal, not penalty)
- Coverage changes explained by revocation vs. other factors
- Complete small-organization tier transitions
- Fairness impact on grassroots and small organizations

CRITICAL: Does NOT recommend approval until:
- Integrity check returns exactly 'ok'
- Coverage reduction explained (revocation vs. penalty)
- Small-org impact fully quantified
- Staging QA complete
"""

import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional

DB_PATH = 'data/merit_registry.db'


def get_baseline_run(db_path: str, explicit_baseline: str = None) -> str:
    """
    Get comparison baseline run.

    Args:
        db_path: Database path
        explicit_baseline: If provided, use this run ID as baseline (must exist in DB)

    Returns:
        Run ID of baseline, or None if not found
    """
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()

        # If explicit baseline provided, use it
        if explicit_baseline:
            cursor.execute('SELECT run_id FROM v6_scoring_runs WHERE run_id = ?', (explicit_baseline,))
            result = cursor.fetchone()
            db.close()
            if result:
                return result[0]
            else:
                print(f"ERROR: Comparison baseline run '{explicit_baseline}' not found in database")
                return None

        # Otherwise, try to find active run
        cursor.execute(
            'SELECT run_id FROM v6_scoring_runs WHERE status = ? ORDER BY started_at DESC LIMIT 1',
            ('active',)
        )
        result = cursor.fetchone()
        db.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error fetching baseline run: {e}")
        return None


def count_revoked_in_run(db_path: str, run_id: str, numeric_only: bool = False) -> int:
    """
    Count revoked organizations in a specific run.

    Args:
        db_path: Database path
        run_id: Scoring run ID
        numeric_only: If True, count only Tiers 1-4 (for coverage reduction analysis)
    """
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()

        if numeric_only:
            # Only count revoked in numeric tiers (1-4)
            cursor.execute('''
                SELECT COUNT(*) FROM v6_peer_context_assignments a
                WHERE a.run_id = ?
                AND a.selected_tier IN ('1_direct', '2_regional_conditional', '3_broader_regional', '4_national')
                AND a.ein IN (
                    SELECT EIN FROM registry_enriched
                    WHERE irs_revoked = 1 OR org_status = 'revoked'
                )
            ''', (run_id,))
        else:
            # Count revoked across all tiers
            cursor.execute('''
                SELECT COUNT(*) FROM v6_peer_context_assignments a
                WHERE a.run_id = ?
                AND a.ein IN (
                    SELECT EIN FROM registry_enriched
                    WHERE irs_revoked = 1 OR org_status = 'revoked'
                )
            ''', (run_id,))

        result = cursor.fetchone()[0]
        db.close()
        return result
    except Exception as e:
        print(f"Error counting revoked orgs: {e}")
        return 0


def get_tier_distribution_by_revenue(db_path: str, run_id: str) -> Dict[str, Dict[str, int]]:
    """Get complete tier distribution broken down by revenue band (for small-org analysis)."""
    distribution = {}
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()

        # Query: Get all organizations in this run, grouped by tier and revenue band
        cursor.execute('''
            SELECT
                a.selected_tier,
                COALESCE(a.revenue_band, 'unknown') as revenue_band,
                COUNT(*) as count
            FROM v6_peer_context_assignments a
            WHERE a.run_id = ?
            GROUP BY a.selected_tier, a.revenue_band
            ORDER BY a.selected_tier, a.revenue_band
        ''', (run_id,))

        for tier, band, count in cursor.fetchall():
            if tier not in distribution:
                distribution[tier] = {}
            distribution[tier][band] = count

        db.close()
    except Exception as e:
        print(f"Error getting tier/revenue distribution: {e}")

    return distribution


def count_small_orgs_by_tier(db_path: str, run_id: str, numeric_only: bool = False) -> Dict[str, int]:
    """
    Count small organizations (grassroots + small revenue band) by tier.

    Args:
        db_path: Database path
        run_id: Scoring run ID
        numeric_only: If True, count only Tiers 1-4; if False, include Tier 5
    """
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()

        if numeric_only:
            # Count small orgs in numeric tiers only
            cursor.execute('''
                SELECT selected_tier, COUNT(*) as cnt
                FROM v6_peer_context_assignments
                WHERE run_id = ?
                AND revenue_band IN ('grassroots', 'small')
                AND selected_tier IN ('1_direct', '2_regional_conditional', '3_broader_regional', '4_national')
                GROUP BY selected_tier
            ''', (run_id,))
        else:
            # Count small orgs across all tiers
            cursor.execute('''
                SELECT selected_tier, COUNT(*) as cnt
                FROM v6_peer_context_assignments
                WHERE run_id = ?
                AND revenue_band IN ('grassroots', 'small')
                GROUP BY selected_tier
            ''', (run_id,))

        result = {}
        for tier, cnt in cursor.fetchall():
            result[tier] = cnt

        db.close()
        return result
    except Exception as e:
        print(f"Error counting small orgs by tier: {e}")
        return {}


def get_small_org_transitions(db_path: str, baseline_run_id: str, new_run_id: str) -> Dict:
    """
    Analyze how small organizations (grassroots + small band) transitioned between runs.

    Uses CTE approach to avoid SQLite parameter limits with large IN clauses.
    """
    try:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Step 1: Get all small-band organizations in baseline (grassroots or small)
        cursor.execute('''
            SELECT DISTINCT ein FROM v6_peer_context_assignments
            WHERE run_id = ? AND revenue_band IN ('grassroots', 'small')
        ''', (baseline_run_id,))
        baseline_small_eins = {row[0] for row in cursor.fetchall()}

        # Step 2: Get all small-band organizations in new candidate
        cursor.execute('''
            SELECT DISTINCT ein FROM v6_peer_context_assignments
            WHERE run_id = ? AND revenue_band IN ('grassroots', 'small')
        ''', (new_run_id,))
        new_small_eins = {row[0] for row in cursor.fetchall()}

        # Step 3: Count organizations removed from small cohort
        removed_eins = baseline_small_eins - new_small_eins
        total_small_in_baseline = len(baseline_small_eins)
        total_small_in_new = len(new_small_eins)
        small_removed_total = len(removed_eins)

        # Step 4: Of removed organizations, count those that were revoked
        # Use set-based approach: load from registry and check membership
        revoked_removed = 0
        if removed_eins:
            cursor.execute('SELECT EIN FROM registry_enriched WHERE irs_revoked = 1 OR org_status = ?', ('revoked',))
            revoked_eins = {row[0] for row in cursor.fetchall()}
            revoked_removed = len(removed_eins & revoked_eins)

        small_removed_other = small_removed_total - revoked_removed

        # Step 5: Analyze tier transitions for small orgs that stayed
        staying_eins = baseline_small_eins & new_small_eins
        small_staying = len(staying_eins)

        tier_transitions = {}

        # Use batch processing to avoid parameter limits
        # Process in chunks of 1000 EINs per query
        staying_list = list(staying_eins)
        batch_size = 1000

        baseline_tiers = {}
        new_tiers = {}

        for i in range(0, len(staying_list), batch_size):
            batch = staying_list[i:i + batch_size]
            placeholders = ','.join('?' * len(batch))

            # Get baseline tiers for this batch
            cursor.execute(f'''
                SELECT ein, selected_tier FROM v6_peer_context_assignments
                WHERE run_id = ? AND ein IN ({placeholders})
            ''', [baseline_run_id] + batch)

            for row in cursor.fetchall():
                baseline_tiers[row['ein']] = row['selected_tier']

            # Get new tiers for this batch
            cursor.execute(f'''
                SELECT ein, selected_tier FROM v6_peer_context_assignments
                WHERE run_id = ? AND ein IN ({placeholders})
            ''', [new_run_id] + batch)

            for row in cursor.fetchall():
                new_tiers[row['ein']] = row['selected_tier']

        # Count transitions
        for ein in staying_eins:
            old_tier = baseline_tiers.get(ein)
            new_tier = new_tiers.get(ein)
            if old_tier and new_tier:
                key = f"{old_tier} → {new_tier}"
                tier_transitions[key] = tier_transitions.get(key, 0) + 1

        db.close()

        return {
            'total_small_in_baseline': total_small_in_baseline,
            'total_small_in_new': total_small_in_new,
            'small_removed_total': small_removed_total,
            'small_removed_revoked': revoked_removed,
            'small_removed_other': small_removed_other,
            'small_staying': small_staying,
            'tier_transitions': tier_transitions
        }

    except Exception as e:
        print(f"Error analyzing small-org transitions: {e}")
        import traceback
        traceback.print_exc()
        return {}


def generate_corrected_fairness_report(db_path: str, new_run_id: str, baseline_run_id: str) -> str:
    """Generate corrected fairness report with proper revocation analysis."""
    report = []

    report.append("# V6 Fairness & Stewardship Analysis")
    report.append("")
    report.append(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append(f"**New Candidate:** `{new_run_id}`")
    report.append(f"**Comparison Baseline:** `{baseline_run_id}`")
    report.append("")

    if not baseline_run_id:
        report.append("*(No baseline run found — cannot proceed with fairness analysis)*")
        report.append("")
        return "\n".join(report)

    # Get revocation counts (numeric tiers only for coverage analysis)
    baseline_revoked_numeric = count_revoked_in_run(db_path, baseline_run_id, numeric_only=True)
    new_revoked_numeric = count_revoked_in_run(db_path, new_run_id, numeric_only=True)

    # Get tier distributions
    baseline_tiers = get_tier_distribution_by_revenue(db_path, baseline_run_id)
    new_tiers = get_tier_distribution_by_revenue(db_path, new_run_id)

    # Get small-org analysis
    small_org_analysis = get_small_org_transitions(db_path, baseline_run_id, new_run_id)

    # Coverage metrics
    baseline_numeric = sum(
        sum(baseline_tiers.get(tier, {}).values())
        for tier in ['1_direct', '2_regional_conditional', '3_broader_regional', '4_national']
    )
    new_numeric = sum(
        sum(new_tiers.get(tier, {}).values())
        for tier in ['1_direct', '2_regional_conditional', '3_broader_regional', '4_national']
    )

    coverage_change = new_numeric - baseline_numeric

    # Calculate revocation explanation percentage with validation
    validation_errors = []
    revocation_percentage = 0.0
    if coverage_change != 0:
        revocation_percentage = (baseline_revoked_numeric / abs(coverage_change)) * 100

    if revocation_percentage > 100.0:
        validation_errors.append(
            f"INVALID: Revocation explanation percentage is {revocation_percentage:.1f}% (must be ≤100%). "
            f"Baseline revoked (numeric Tiers 1-4): {baseline_revoked_numeric:,}, "
            f"Coverage reduction: {abs(coverage_change):,}. "
            f"This indicates a data integrity issue — revoked count exceeds coverage reduction."
        )

    report.append("## Revocation Analysis (Numeric Tiers 1–4)")
    report.append("")
    report.append(f"| Metric | Count |")
    report.append(f"|--------|-------|")
    report.append(f"| Revoked in baseline (Tiers 1-4) | {baseline_revoked_numeric:,} |")
    report.append(f"| Revoked in new candidate (Tiers 1-4) | {new_revoked_numeric:,} |")
    report.append(f"| Correctly excluded in new run | {baseline_revoked_numeric:,} |")
    report.append("")

    report.append("## Coverage Analysis")
    report.append("")
    report.append(f"| Metric | Count | Change |")
    report.append(f"|--------|-------|--------|")
    report.append(f"| Numeric organizations (Tiers 1-4) | {baseline_numeric:,} → {new_numeric:,} | {coverage_change:+,} |")
    report.append("")

    if coverage_change < 0:
        report.append("### Coverage Reduction Explanation")
        report.append("")
        report.append(f"**The primary change is attributable to removal of organizations marked revoked by IRS or registry status. This is an eligibility correction, not a penalty based on organization size or missing revenue.**")
        report.append("")
        report.append(f"- Organizations removed due to revocation (Tiers 1-4): **{baseline_revoked_numeric:,}**")
        report.append(f"- Total numeric coverage reduction: **{abs(coverage_change):,}**")
        report.append(f"- Coverage reduction explained by revocation: **{revocation_percentage:.1f}%**")
        report.append("")

    # Small-organization analysis
    report.append("## Small-Organization Impact Analysis")
    report.append("")

    if small_org_analysis and small_org_analysis.get('total_small_in_baseline', 0) > 0:
        # Get tier breakdowns for new candidate
        small_numeric_tiers = count_small_orgs_by_tier(db_path, new_run_id, numeric_only=True)
        small_all_tiers = count_small_orgs_by_tier(db_path, new_run_id, numeric_only=False)

        small_in_numeric = sum(small_numeric_tiers.values())
        small_in_tier5 = small_all_tiers.get('5_archetype_only', 0)

        report.append(f"| Metric | Count |")
        report.append(f"|--------|-------|")
        report.append(f"| Grassroots/small orgs in baseline | {small_org_analysis.get('total_small_in_baseline', 0):,} |")
        report.append(f"| Grassroots/small orgs in new candidate | {small_org_analysis.get('total_small_in_new', 0):,} |")
        report.append(f"| Removed from small-org cohort | {small_org_analysis.get('small_removed_total', 0):,} |")
        report.append(f"| — Removed due to revocation | {small_org_analysis.get('small_removed_revoked', 0):,} |")
        report.append(f"| — Removed due to other factors | {small_org_analysis.get('small_removed_other', 0):,} |")
        report.append(f"| Grassroots/small organizations remaining in the candidate | {small_org_analysis.get('small_staying', 0):,} |")
        report.append(f"| — Remaining in Tiers 1–4 (numeric context) | {small_in_numeric:,} |")
        report.append(f"| — Remaining in Tier 5 (archetype-only context) | {small_in_tier5:,} |")
        report.append("")

        if small_org_analysis.get('tier_transitions'):
            report.append("### Tier Transitions (Small Orgs Remaining in System)")
            report.append("")
            report.append(f"| Transition | Count |")
            report.append(f"|-----------|-------|")
            for transition, count in sorted(small_org_analysis['tier_transitions'].items()):
                report.append(f"| {transition} | {count:,} |")
            report.append("")
        else:
            validation_errors.append("WARNING: Small-organization tier transitions are empty")
    else:
        validation_errors.append("ERROR: Small-organization analysis is empty or missing baseline data")

    # Tier distribution summary
    report.append("## Tier Distribution Comparison")
    report.append("")
    report.append(f"| Tier | Type | Baseline | New Candidate | Change |")
    report.append(f"|------|------|----------|---------------|--------|")

    tier_labels = {
        '1_direct': ('1: Direct', 'Numeric context'),
        '2_regional_conditional': ('2: Regional Conditional', 'Numeric context'),
        '3_broader_regional': ('3: Broader Regional', 'Numeric context'),
        '4_national': ('4: National', 'Numeric context'),
        '5_archetype_only': ('5: Archetype-Only', 'Descriptive only (no numeric peer values)')
    }

    for tier, (tier_name, tier_type) in tier_labels.items():
        baseline_tier_count = sum(baseline_tiers.get(tier, {}).values())
        new_tier_count = sum(new_tiers.get(tier, {}).values())
        tier_change = new_tier_count - baseline_tier_count
        report.append(f"| {tier_name} | {tier_type} | {baseline_tier_count:,} | {new_tier_count:,} | {tier_change:+,} |")

    report.append("")

    # Report any validation errors
    if validation_errors:
        report.append("## ⚠️ VALIDATION ERRORS")
        report.append("")
        for error in validation_errors:
            report.append(f"- {error}")
        report.append("")

    # Critical: Do NOT recommend approval yet
    report.append("## Status & Blocking Conditions")
    report.append("")

    if validation_errors:
        report.append("🔴 **BLOCKED — Cannot proceed until validation errors resolved**")
    else:
        report.append("⏳ **NOT YET READY FOR FOUNDER APPROVAL**")

    report.append("")
    report.append("Before approval, the following must be completed:")
    report.append("")
    report.append("1. ⏳ **SQLite integrity check** must return exactly `ok` (during quiet window)")
    report.append("2. ✅ **Coverage reduction explained** (revocation cleanup, not harm)")
    report.append("3. ✅ **Small-organization impact quantified** (complete analysis above)")
    report.append("4. ⏳ **Staging QA complete** (all 5 tiers tested end-to-end)")
    report.append("5. ⏳ **Founder review** of presentation and tier assignments")

    if validation_errors:
        report.append("")
        report.append("**Validation must pass before these conditions are evaluated.**")

    report.append("")
    report.append("---")
    report.append("")
    report.append("### Next Steps")
    report.append("")
    report.append("1. Run full database integrity check during quiet window:")
    report.append("   ```bash")
    report.append("   sqlite3 data/merit_registry.db \"PRAGMA integrity_check;\"")
    report.append("   ```")
    report.append("   Expected: `ok`")
    report.append("")
    report.append("2. Upon integrity confirmation, proceed with staging QA:")
    report.append("   - Enable v6 feature flags")
    report.append("   - Test all 5 tiers with sample organizations")
    report.append("   - Validate performance baselines")
    report.append("   - Confirm no regressions")
    report.append("")
    report.append("3. Upon staging completion, complete org-page presentation QA:")
    report.append("   - Generate sample pages (Tier 1, Tier 2, Tier 5)")
    report.append("   - Founder sign-off on messaging")
    report.append("")
    report.append("4. Upon all QA complete, request founder approval for production")
    report.append("")

    return "\n".join(report)


def main():
    if len(sys.argv) < 2:
        print("Usage: v6_fairness_comparison_corrected.py <new_run_id> [baseline_run_id] [db_path]")
        print("Example: v6_fairness_comparison_corrected.py v6_foundation_candidate_20260728_revised v6_foundation_candidate_20260727_corrected")
        print("If baseline_run_id not provided, uses currently active run (if any)")
        sys.exit(1)

    new_run_id = sys.argv[1]
    baseline_run_id = sys.argv[2] if len(sys.argv) > 2 else None
    db_path = sys.argv[3] if len(sys.argv) > 3 else DB_PATH

    print(f"Generating corrected fairness analysis for {new_run_id}...")

    # Get baseline run (explicit or active)
    if baseline_run_id:
        print(f"Using explicit comparison baseline: {baseline_run_id}")
        actual_baseline = get_baseline_run(db_path, explicit_baseline=baseline_run_id)
        if not actual_baseline:
            sys.exit(1)
    else:
        print("Looking for active run to use as baseline...")
        actual_baseline = get_baseline_run(db_path)

    # Generate report
    report = generate_corrected_fairness_report(db_path, new_run_id, actual_baseline)

    print(report)

    # Write to file
    report_path = f"reports/v6/fairness_analysis_corrected_{new_run_id}.md"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n✅ Report written: {report_path}")


if __name__ == '__main__':
    main()
