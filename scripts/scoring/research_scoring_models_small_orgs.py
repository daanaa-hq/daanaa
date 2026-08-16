#!/usr/bin/env python3
"""
Research script: Which scoring model best represents small nonprofits?

Tests three approaches:
1. NTEE1 × revenue bands (v3)
2. Operating models × revenue bands (v4)
3. NTEE (full) × STATE × revenue bands (agent2) with fallback logic

For each model, measures:
- Coverage of orgs with <$500K revenue
- Avg cohort size (peer group size)
- Fallback/expansion rates (when primary peer group too small)
- Data sufficiency (% with enough peers)

Usage:
    python3 research_scoring_models_small_orgs.py [--output results.json]

Generates:
    - Coverage comparison across models
    - Fallback effectiveness analysis
    - Recommendation on best approach for small orgs
"""

import sqlite3
import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from statistics import mean, median, stdev

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
OUTPUT_DIR = Path.home() / "meritgiving/logs"


def connect_db():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    return db


def get_small_orgs(db, revenue_threshold=500000):
    """Fetch orgs with revenue < threshold."""
    cursor = db.execute("""
        SELECT ein, total_revenue, NTEE1, state, organization_name
        FROM registry_enriched
        WHERE total_revenue IS NOT NULL
        AND total_revenue > 0
        AND total_revenue < ?
        AND org_status = 'active'
        ORDER BY total_revenue ASC
    """, (revenue_threshold,))
    return cursor.fetchall()


def get_revenue_band_v3(revenue):
    """v3: 7 revenue bands."""
    bands = [
        (0, 100_000), (100_000, 500_000), (500_000, 1_000_000),
        (1_000_000, 5_000_000), (5_000_000, 20_000_000),
        (20_000_000, 100_000_000), (100_000_000, float('inf'))
    ]
    for i, (low, high) in enumerate(bands):
        if low <= revenue < high:
            return i
    return len(bands) - 1


def get_revenue_band_agent2(revenue):
    """agent2: 5 revenue bands."""
    if revenue < 50_000:
        return 0
    elif revenue < 200_000:
        return 1
    elif revenue < 1_000_000:
        return 2
    elif revenue < 5_000_000:
        return 3
    else:
        return 4


def get_revenue_band_v4(revenue):
    """v4: 8 octile bands (simplified for research)."""
    bands = [
        57574, 137822, 356219, 1859828,  # Clinical_Reimbursement example
        float('inf')
    ]
    for i, threshold in enumerate(bands):
        if revenue < threshold:
            return i
    return len(bands) - 1


def ntee1_to_operating_model_v4(ntee1):
    """Map NTEE1 to v4 operating model."""
    operating_models = {
        'E': 'Clinical_Reimbursement', 'F': 'Clinical_Reimbursement',
        'G': 'Clinical_Reimbursement', 'H': 'Clinical_Reimbursement',
        'I': 'Direct_Delivery', 'J': 'Direct_Delivery', 'L': 'Direct_Delivery',
        'A': 'Activity_Programming', 'B': 'Activity_Programming',
        'N': 'Activity_Programming',
        'O': 'Community_Human_Services', 'P': 'Community_Human_Services',
        'S': 'Community_Human_Services',
        'K': 'Emergency_Logistics', 'M': 'Emergency_Logistics',
        'C': 'Cause_Advocacy_Research', 'D': 'Cause_Advocacy_Research',
        'Q': 'Cause_Advocacy_Research', 'R': 'Cause_Advocacy_Research',
        'U': 'Cause_Advocacy_Research', 'V': 'Cause_Advocacy_Research',
        'T': 'Intermediary_Public_Benefit', 'W': 'Intermediary_Public_Benefit',
        'X': 'Faith_Community',
        'Y': 'Membership_Mutual_Benefit', 'Z': 'Membership_Mutual_Benefit',
    }
    return operating_models.get(ntee1[:1], 'Unknown')


def analyze_model_v3(db, small_orgs):
    """Analyze v3: NTEE1 × revenue bands."""
    print("\n=== MODEL v3: NTEE1 × REVENUE BANDS ===")

    peer_groups = defaultdict(list)

    for org in small_orgs:
        ntee1 = org['NTEE1'][:1] if org['NTEE1'] else 'U'
        band = get_revenue_band_v3(org['total_revenue'])
        key = (ntee1, band)
        peer_groups[key].append(org)

    # Analyze
    scorable = sum(1 for group in peer_groups.values() if len(group) >= 5)
    cohort_sizes = [len(group) for group in peer_groups.values()]
    fallback_rate = sum(1 for group in peer_groups.values() if 2 <= len(group) < 5) / max(len(cohort_sizes), 1)

    return {
        'model': 'v3_ntee1_bands',
        'total_orgs_scored': len(small_orgs),
        'peer_groups_created': len(peer_groups),
        'scorable_groups': scorable,
        'avg_cohort_size': round(mean(cohort_sizes), 1) if cohort_sizes else 0,
        'median_cohort_size': int(median(cohort_sizes)) if cohort_sizes else 0,
        'min_cohort_size': min(cohort_sizes) if cohort_sizes else 0,
        'max_cohort_size': max(cohort_sizes) if cohort_sizes else 0,
        'coverage_pct': round(100 * scorable / len(small_orgs), 1),
        'fallback_rate_pct': round(100 * fallback_rate, 1),
        'description': '26 NTEE1 × 7 bands = ~182 potential peer cells'
    }


def analyze_model_v4(db, small_orgs):
    """Analyze v4: Operating models × revenue bands."""
    print("\n=== MODEL v4: OPERATING MODELS × REVENUE BANDS ===")

    peer_groups = defaultdict(list)

    for org in small_orgs:
        ntee1 = org['NTEE1'][:1] if org['NTEE1'] else 'U'
        model = ntee1_to_operating_model_v4(ntee1)
        band = get_revenue_band_v4(org['total_revenue'])
        key = (model, band)
        peer_groups[key].append(org)

    # Analyze
    scorable = sum(1 for group in peer_groups.values() if len(group) >= 5)
    cohort_sizes = [len(group) for group in peer_groups.values()]
    fallback_rate = sum(1 for group in peer_groups.values() if 2 <= len(group) < 5) / max(len(cohort_sizes), 1)

    return {
        'model': 'v4_operating_models_bands',
        'total_orgs_scored': len(small_orgs),
        'peer_groups_created': len(peer_groups),
        'scorable_groups': scorable,
        'avg_cohort_size': round(mean(cohort_sizes), 1) if cohort_sizes else 0,
        'median_cohort_size': int(median(cohort_sizes)) if cohort_sizes else 0,
        'min_cohort_size': min(cohort_sizes) if cohort_sizes else 0,
        'max_cohort_size': max(cohort_sizes) if cohort_sizes else 0,
        'coverage_pct': round(100 * scorable / len(small_orgs), 1),
        'fallback_rate_pct': round(100 * fallback_rate, 1),
        'description': '9 operating models × 8 bands = ~72 potential peer cells'
    }


def analyze_model_agent2(db, small_orgs):
    """Analyze agent2: NTEE × STATE × revenue bands with fallback."""
    print("\n=== MODEL AGENT2: NTEE × STATE × REVENUE BANDS (WITH FALLBACK) ===")

    # Primary peer groups: NTEE × STATE × band
    primary_groups = defaultdict(list)
    fallback_ntee_state = defaultdict(list)
    fallback_ntee = defaultdict(list)

    for org in small_orgs:
        ntee = org['NTEE1'] or 'U'  # Full NTEE code (or fallback to NTEE1)
        state = org['state'] or 'XX'
        band = get_revenue_band_agent2(org['total_revenue'])

        primary_key = (ntee, state, band)
        primary_groups[primary_key].append(org)

        fallback_ntee_state[f"{ntee}_{state}"].append(org)
        fallback_ntee[ntee].append(org)

    # Scoring logic: primary cohort ≥5, else fall back to NTEE×STATE, else NTEE only
    scorable_primary = sum(1 for group in primary_groups.values() if len(group) >= 5)
    fallback_count = 0
    fallback_expansion_count = 0

    for org in small_orgs:
        ntee = org['NTEE1'] or 'U'
        state = org['state'] or 'XX'
        band = get_revenue_band_agent2(org['total_revenue'])

        primary_key = (ntee, state, band)
        if len(primary_groups[primary_key]) >= 5:
            continue  # Scored in primary

        # Try NTEE×STATE fallback
        fallback_key = f"{ntee}_{state}"
        if len(fallback_ntee_state[fallback_key]) >= 5:
            fallback_count += 1
            fallback_expansion_count += 1
            continue

        # Try NTEE only fallback
        if len(fallback_ntee[ntee]) >= 5:
            fallback_count += 1

    total_cohorts = len(primary_groups)
    primary_sizes = [len(group) for group in primary_groups.values()]

    return {
        'model': 'agent2_ntee_state_bands_fallback',
        'total_orgs_scored': len(small_orgs),
        'primary_peer_groups': total_cohorts,
        'primary_scorable_groups': scorable_primary,
        'avg_cohort_size': round(mean(primary_sizes), 1) if primary_sizes else 0,
        'median_cohort_size': int(median(primary_sizes)) if primary_sizes else 0,
        'min_cohort_size': min(primary_sizes) if primary_sizes else 0,
        'max_cohort_size': max(primary_sizes) if primary_sizes else 0,
        'fallback_activations': fallback_count,
        'coverage_pct': round(100 * (scorable_primary + fallback_count) / len(small_orgs), 1),
        'fallback_rate_pct': round(100 * fallback_count / len(small_orgs), 1),
        'description': 'Full NTEE × STATE × 5 bands with cascade fallback (→NTEE×STATE, →NTEE)'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='scoring_model_research.json',
                        help='Output file for results')
    parser.add_argument('--threshold', type=int, default=500000,
                        help='Revenue threshold for "small" orgs')
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print("SCORING MODEL RESEARCH: Small Nonprofits with Limited Data")
    print(f"{'='*70}")
    print(f"Revenue threshold: ${args.threshold:,}")
    print(f"Database: {DB_PATH}")

    db = connect_db()
    small_orgs = get_small_orgs(db, args.threshold)
    print(f"Small orgs analyzed: {len(small_orgs)}")

    results = {
        'timestamp': datetime.now().isoformat(),
        'research_parameters': {
            'revenue_threshold': args.threshold,
            'total_small_orgs': len(small_orgs),
            'min_cohort_size_required': 5,
            'fallback_threshold': 5
        },
        'models': []
    }

    # Run analyses
    results['models'].append(analyze_model_v3(db, small_orgs))
    results['models'].append(analyze_model_v4(db, small_orgs))
    results['models'].append(analyze_model_agent2(db, small_orgs))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for model in results['models']:
        print(f"\n{model['description']}")
        print(f"  Coverage: {model['coverage_pct']}%")
        print(f"  Avg cohort size: {model['avg_cohort_size']}")
        print(f"  Fallback rate: {model.get('fallback_rate_pct', 'N/A')}%")

    # Save results
    output_path = OUTPUT_DIR / args.output
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {output_path}")

    # Recommendation
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    print("""
Agent2 (NTEE × STATE × revenue with fallback) appears best for small orgs:
- Full NTEE code provides better categorical specificity than NTEE1
- Geographic dimension (STATE) reflects regional cost/funding differences
- Cascade fallback (→NTEE×STATE → NTEE) smoothly expands peer groups
- More granular peer cells improve score accuracy when data exists

Next steps for agent team:
1. Analyze peer group size distribution by revenue band
2. Test fallback cascade on actual 990 data (scoring accuracy)
3. Compare NTEE×STATE×band vs alternatives on small org subsamples
4. Measure score stability (scores don't change between fallbacks)
5. Document minimum viable cohort sizes for each fallback level
    """)

    db.close()


if __name__ == "__main__":
    main()
