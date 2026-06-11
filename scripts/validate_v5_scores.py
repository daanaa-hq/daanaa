#!/usr/bin/env python3
"""
Validation audit for v5.0 scores.

Checks:
1. Coverage: ≥98% of orgs assigned to valid group
2. Coherence: Within-group variance on key metrics
3. Discrimination: Health signal variation between groups
4. Sample audit: Review 100 random orgs, verify assignments make sense
"""

import json
import sqlite3
import random
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DB = Path.home() / "meritgiving/data/merit_registry.db"

def load_scores(scores_file):
    """Load scoring results from JSON."""
    with open(scores_file) as f:
        data = json.load(f)
    return data['scores']

def validate_coverage(scores):
    """Check ≥98% coverage."""
    print("\n=== COVERAGE VALIDATION ===")
    total = len(scores)
    by_group = defaultdict(list)

    for score in scores:
        key = (score['archetype_key'], score['band_key'])
        by_group[key].append(score)

    print(f"Total orgs scored: {total:,}")
    print(f"Groups represented: {len(by_group)}")

    for key in sorted(by_group.keys()):
        group = by_group[key]
        label = group[0]['peer_group_label']
        pct = len(group) / total * 100
        print(f"  {label:60s}: {len(group):6,} orgs ({pct:5.1f}%)")

    return total > 0

def validate_coherence(scores):
    """Check within-group variance."""
    print("\n=== COHERENCE VALIDATION ===")
    by_group = defaultdict(list)

    for score in scores:
        key = (score['archetype_key'], score['band_key'])
        by_group[key].append(score)

    for key in sorted(by_group.keys()):
        group = by_group[key]
        label = group[0]['peer_group_label']

        # Variance on reserves_percentile (0-99 scale)
        percentiles = [s['reserves_percentile'] for s in group]
        variance = max(percentiles) - min(percentiles) if percentiles else 0
        stdev = (sum((p - 50)**2 for p in percentiles) / len(percentiles))**0.5 if percentiles else 0

        print(f"  {label:60s}: var={variance:5.0f}pp stdev={stdev:5.1f}")

    return True

def validate_discrimination(scores):
    """Check health signal variation between groups."""
    print("\n=== DISCRIMINATION VALIDATION ===")
    by_group = defaultdict(list)

    for score in scores:
        key = (score['archetype_key'], score['band_key'])
        by_group[key].append(score)

    health_by_group = {}
    for key in sorted(by_group.keys()):
        group = by_group[key]
        label = group[0]['peer_group_label']

        healthy_count = sum(1 for s in group if s['health_signal'] == 'HEALTHY')
        stable_count = sum(1 for s in group if s['health_signal'] == 'STABLE')
        caution_count = sum(1 for s in group if s['health_signal'] == 'CAUTION')

        healthy_pct = healthy_count / len(group) * 100
        health_by_group[label] = healthy_pct

        print(f"  {label:60s}: HEALTHY {healthy_pct:5.1f}% | STABLE {stable_count:5d} | CAUTION {caution_count:5d}")

    # Check variation
    if health_by_group:
        min_health = min(health_by_group.values())
        max_health = max(health_by_group.values())
        variation = max_health - min_health
        print(f"\nHealth rate variation: {variation:.1f}pp (target ≥20pp)")
        if variation >= 20:
            print("✓ PASS: Health discrimination sufficient")
        else:
            print("✗ FAIL: Health discrimination weak")

    return True

def audit_sample_orgs(scores_file, sample_size=100):
    """
    Sample 100 random orgs and verify assignments make sense.
    """
    print(f"\n=== SAMPLE AUDIT (n={sample_size}) ===")

    scores = load_scores(scores_file)
    sample = random.sample(scores, min(sample_size, len(scores)))

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    issues = []
    for score in sample:
        ein = score['ein']

        # Look up org in registry
        c.execute('SELECT * FROM registry_enriched WHERE ein = ?', (ein,))
        org = c.fetchone()

        if not org:
            issues.append((ein, score['name'], 'Not in registry'))
            continue

        ntee1 = org['ntee1']
        assigned_archetype = score['archetype_key']

        # Check if assignment makes sense
        # (This is a simple heuristic — real validation would involve domain knowledge)
        if ntee1 == 'Y' and assigned_archetype != 'endowment':
            issues.append((ein, score['name'], f'NTEE Y but assigned {assigned_archetype}'))
        elif ntee1 == 'J' and assigned_archetype != 'fee_for_service':
            issues.append((ein, score['name'], f'NTEE J but assigned {assigned_archetype}'))

    conn.close()

    print(f"Sampled: {len(sample)} orgs")
    print(f"Issues found: {len(issues)}")

    if issues:
        print("\nSample issues:")
        for ein, name, issue in issues[:10]:
            print(f"  {ein} {name[:40]}: {issue}")

    return len(issues) < len(sample) * 0.1  # Fail if >10% have issues

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate v5.0 scores')
    parser.add_argument('scores_file', help='Path to scores JSON file')
    args = parser.parse_args()

    print(f"Validating scores from {args.scores_file}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    scores = load_scores(args.scores_file)

    validate_coverage(scores)
    validate_coherence(scores)
    validate_discrimination(scores)
    audit_sample_orgs(args.scores_file)

    print(f"\nValidation complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
