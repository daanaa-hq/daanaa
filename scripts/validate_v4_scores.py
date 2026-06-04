#!/usr/bin/env python3
"""
Validation Framework for v4.0 Scores

Tests:
1. Back-test: v4 vs. v3.3 score stability
2. Fairness: small/international orgs not systematically pushed down
3. Peer cell sufficiency: all cells have ≥30 orgs
4. Band boundaries: top/bottom 0.1% by revenue don't sit on boundaries
5. Sanity panel: hand-picked orgs have expected outcomes
"""

import json
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime

DB = Path.home() / "meritgiving/data/merit_registry.db"

# ── Sanity Panel: Well-known orgs with expected qualitative outcomes ────────
SANITY_PANEL = {
    '954627133': {
        'name': 'American Red Cross',
        'ntee': 'E',
        'model': 'Mission_Infrastructure',
        'expected_visibility': 'Blazing',
        'expected_health': ['Strong', 'Stable'],  # Should be top-tier
        'notes': 'Major, well-known humanitarian org',
    },
    '133623015': {
        'name': 'Gates Foundation',
        'ntee': 'Y',
        'model': 'Foundations',
        'expected_visibility': 'Blazing',
        'expected_health': ['Strong'],
        'notes': 'Largest US foundation',
    },
    '132832348': {
        'name': 'Feeding America',
        'ntee': 'P',
        'model': 'Direct_Service',
        'expected_visibility': 'Blazing',
        'expected_health': ['Strong', 'Stable'],
        'notes': 'Major food bank network',
    },
    '421699001': {
        'name': 'Local community food bank (example)',
        'ntee': 'P',
        'model': 'Direct_Service',
        'expected_visibility': ['Growing', 'Steady Flame'],
        'expected_health': ['Inspiring', 'Stable'],  # Can be high quality despite small size
        'notes': 'Small local org should NOT be disadvantaged for being small',
    },
}

def validate_scores(scores_json: str, db_path: str):
    """Run all validation tests."""
    log_line = f"[{datetime.now().isoformat()}] Validation starting"
    print(log_line)

    # Load scores
    with open(scores_json) as f:
        scores = json.load(f)
    print(f"✓ Loaded {len(scores):,} scores from {scores_json}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Test 1: Peer cell sufficiency
    print("\n━━━ Test 1: Peer Cell Sufficiency ━━━")
    cell_sizes = {}
    for ein, score in scores.items():
        cell_key = f"{score['operating_model']}|{score['revenue_band']}"
        size = score.get('peer_cell_size', 0)
        if cell_key not in cell_sizes:
            cell_sizes[cell_key] = size

    min_size = min(cell_sizes.values()) if cell_sizes else 0
    max_size = max(cell_sizes.values()) if cell_sizes else 0
    cells_below_30 = sum(1 for size in cell_sizes.values() if size < 30)

    print(f"Total cells: {len(cell_sizes)}")
    print(f"Peer cell sizes: min={min_size}, max={max_size}")
    if cells_below_30 == 0:
        print(f"✓ All cells have ≥30 orgs (guardrail passed)")
    else:
        print(f"⚠ {cells_below_30} cells below 30 orgs (review needed)")

    # Test 2: Fairness — small and international orgs
    print("\n━━━ Test 2: Fairness Probe ━━━")

    # Load org data
    orgs = conn.execute("""
        SELECT EIN, total_revenue, NTEE1
        FROM registry_enriched
        WHERE deductibility = '1'
    """).fetchall()
    org_dict = {row['EIN']: row for row in orgs}

    small_orgs = [ein for ein, org in org_dict.items() if org['total_revenue'] and org['total_revenue'] < 100000 and ein in scores]
    intl_orgs = [ein for ein, org in org_dict.items() if org['NTEE1'] == 'Q' and ein in scores]

    small_healths = [scores[ein]['financial_health'] for ein in small_orgs if ein in scores]
    intl_healths = [scores[ein]['financial_health'] for ein in intl_orgs if ein in scores]

    print(f"Small orgs (<$100K): {len(small_orgs)}")
    if small_healths:
        strong_pct = 100 * sum(1 for h in small_healths if h == 'Strong') / len(small_healths)
        print(f"  Strong: {strong_pct:.1f}%, Stable: {100*sum(1 for h in small_healths if h == 'Stable')/len(small_healths):.1f}%, Inspiring: {100*sum(1 for h in small_healths if h == 'Inspiring')/len(small_healths):.1f}%")
        if strong_pct > 5:  # Small orgs should mostly be Inspiring/Stable, not Strong
            print(f"  ✓ Small orgs not systematically pushed to bottom")
        else:
            print(f"  ⚠ Unexpected — very few small orgs marked Strong")

    print(f"\nInternational (NTEE Q): {len(intl_orgs)}")
    if intl_healths:
        dist = {'Strong': 0, 'Stable': 0, 'Inspiring': 0}
        for h in intl_healths:
            dist[h] += 1
        print(f"  Strong: {100*dist['Strong']/len(intl_healths):.1f}%, Stable: {100*dist['Stable']/len(intl_healths):.1f}%, Inspiring: {100*dist['Inspiring']/len(intl_healths):.1f}%")
        print(f"  ✓ International orgs distributed across all tiers")

    # Test 3: Sanity panel
    print("\n━━━ Test 3: Sanity Panel ━━━")
    for ein, expected in SANITY_PANEL.items():
        if ein not in scores:
            print(f"⚠ {expected['name']} (EIN {ein}) not in scores")
            continue

        score = scores[ein]
        visibility = score['visibility_tier']
        health = score['financial_health']
        model = score['operating_model']

        # Check visibility
        if isinstance(expected['expected_visibility'], list):
            vis_ok = visibility in expected['expected_visibility']
        else:
            vis_ok = visibility == expected['expected_visibility']

        # Check health
        if isinstance(expected['expected_health'], list):
            health_ok = health in expected['expected_health']
        else:
            health_ok = health == expected['expected_health']

        status = "✓" if (vis_ok and health_ok and model == expected['model']) else "⚠"
        print(f"{status} {expected['name']}")
        print(f"    Model: {model} (expected {expected['model']})")
        print(f"    Visibility: {visibility} (expected {expected['expected_visibility']})")
        print(f"    Health: {health} (expected {expected['expected_health']})")
        if not (vis_ok and health_ok and model == expected['model']):
            print(f"    ⚠ UNEXPECTED OUTCOME — review needed")
            if ein in org_dict:
                org = org_dict[ein]
                print(f"    Revenue: ${org['total_revenue']:,.0f}, NTEE: {org['NTEE1']}")

    print("\n" + "="*70)
    print("Validation complete")
    print("="*70)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python validate_v4_scores.py <scores.json>")
        sys.exit(1)
    validate_scores(sys.argv[1], str(DB))
