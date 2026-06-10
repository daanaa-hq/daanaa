#!/usr/bin/env python3
"""
Tier B Scorer — Expand v4 scoring to 379K partial-data orgs

Tier A: 71,473 complete-fingerprint orgs (all 4 metrics)
Tier B: 307,517 additional orgs with revenue + expenses (derive program_pct)

Uses same peer grouping as Tier A (8 models, revenue bands).
Program expense ratio derived from available data with NTEE-level defaults.

Efficiency: batch load, no API calls, local inference only.
"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"

# NTEE-level program spend defaults (if individual org data missing)
NTEE_PROGRAM_DEFAULTS = {
    'A': 0.85,  # Arts: 85% program
    'B': 0.88,  # Education: 88%
    'C': 0.82,  # Environment: 82%
    'D': 0.80,  # Animal welfare: 80%
    'E': 0.75,  # Health: 75%
    'F': 0.80,  # Mental health: 80%
    'G': 0.78,  # Disease/medical: 78%
    'H': 0.85,  # Medical research: 85%
    'I': 0.70,  # Crime/legal: 70%
    'J': 0.80,  # Employment: 80%
    'K': 0.85,  # Food: 85%
    'L': 0.75,  # Housing: 75%
    'M': 0.80,  # Disaster relief: 80%
    'N': 0.80,  # Recreation: 80%
    'O': 0.85,  # Youth: 85%
    'P': 0.75,  # Human services: 75%
    'Q': 0.80,  # International: 80%
    'R': 0.75,  # Civil rights: 75%
    'S': 0.80,  # Community dev: 80%
    'T': 0.30,  # Philanthropy: 30%
    'U': 0.85,  # Science/tech: 85%
    'V': 0.85,  # Social science: 85%
    'W': 0.75,  # Public benefit: 75%
    'X': 0.70,  # Faith: 70%
    'Y': 0.50,  # Mutual benefit: 50%
}

# Same 8 models + revenue bands as Tier A
OPERATING_MODELS = {
    'Direct_Service': ['E', 'F', 'G', 'J', 'K', 'L', 'M', 'N', 'O', 'P'],
    'Mission_Infrastructure': ['A', 'B', 'C', 'D', 'H', 'I', 'R', 'S', 'U', 'V'],
    'Research_Academia': ['H', 'U', 'V'],
    'Foundations': ['T'],
    'Membership_Advocacy': ['J', 'R', 'S'],
    'Religion_Spiritual': ['X'],
    'International_Development': ['Q'],
    'Asset_Stewards': ['C', 'W'],
}

REVENUE_BANDS = {
    'Direct_Service': [0, 100000, 250000, 500000, 1000000, 2500000, 5000000, 10000000],
    'Mission_Infrastructure': [0, 250000, 500000, 1000000, 2500000, 5000000, 10000000, 25000000],
    'Research_Academia': [0, 500000, 1000000, 2500000, 5000000, 10000000, 25000000, 50000000],
    'Foundations': [0, 1000000, 2500000, 5000000, 10000000, 25000000, 50000000, 100000000],
    'Membership_Advocacy': [0, 100000, 250000, 500000, 1000000, 2500000, 5000000, 10000000],
    'Religion_Spiritual': [0, 50000, 100000, 250000, 500000, 1000000, 2500000, 5000000],
    'International_Development': [0, 250000, 500000, 1000000, 2500000, 5000000, 10000000, 25000000],
    'Asset_Stewards': [0, 100000, 500000, 1000000, 2500000, 5000000, 10000000, 25000000],
}

def get_ntee1(nteecc):
    """Extract NTEE1 from NTEECC."""
    return nteecc[0] if nteecc else None

def derive_program_pct(row):
    """Derive program expense % from available data or NTEE default."""
    if row['program_expense_pct'] and row['program_expense_pct'] > 0:
        return row['program_expense_pct']

    # Try to calculate from expenses
    if row['total_expenses'] and row['total_expenses'] > 0:
        # Use NTEE default for this org
        ntee1 = get_ntee1(row['NTEECC'])
        default = NTEE_PROGRAM_DEFAULTS.get(ntee1, 0.75)
        return default * 100  # Return as percentage (0-100)

    return None

def percentile_rank(value, values):
    """Return percentile rank of value in list."""
    if not values or len(values) < 2:
        return 50.0
    sorted_vals = sorted(values)
    rank = sum(1 for v in sorted_vals if v <= value) / len(sorted_vals) * 100
    return max(1, min(99, rank))

def score_tier_b():
    """Score Tier B orgs with revenue + expenses."""
    print(f"[{datetime.now().isoformat()}] Tier B Scorer starting")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Fetch Tier B candidates: revenue + expenses, NOT already in v4_scores
    rows = conn.execute("""
        SELECT r.EIN, r.organization_name, r.NTEE1, r.NTEECC,
               r.total_revenue, r.total_expenses, r.net_assets,
               r.program_expense_pct, r.months_of_reserve
        FROM registry_enriched r
        WHERE r.deductibility = '1'
          AND r.total_revenue > 0
          AND r.total_expenses > 0
          AND r.EIN NOT IN (SELECT EIN FROM v4_scores)
        LIMIT 500000
    """).fetchall()

    print(f"[{datetime.now().isoformat()}] Loaded {len(rows)} Tier B candidates")

    # Group by model + band to compute peer percentiles
    peer_groups = {}
    orgs_by_group = {}

    for row in rows:
        row_dict = dict(row)
        ntee1 = get_ntee1(row['NTEECC'])

        # Find operating model
        model = None
        for m, ntee_codes in OPERATING_MODELS.items():
            if ntee1 in ntee_codes:
                model = m
                break

        if not model:
            model = 'Direct_Service'  # Default fallback

        # Find revenue band
        bands = REVENUE_BANDS[model]
        band_idx = 0
        for i, threshold in enumerate(bands[1:], 1):
            if row['total_revenue'] < threshold:
                band_idx = i - 1
                break
        else:
            band_idx = len(bands) - 1

        row_dict['operating_model'] = model
        row_dict['revenue_band'] = band_idx
        row_dict['program_expense_pct'] = derive_program_pct(row_dict)

        group_key = (model, band_idx)
        if group_key not in orgs_by_group:
            orgs_by_group[group_key] = []
        orgs_by_group[group_key].append(row_dict)

    # Score each peer group
    print(f"[{datetime.now().isoformat()}] Scoring {len(orgs_by_group)} peer groups")
    scored = 0

    for (model, band_idx), orgs in orgs_by_group.items():
        # Compute metrics for percentile ranking
        revenues = [o['total_revenue'] for o in orgs if o['total_revenue']]
        program_pcts = [o['program_expense_pct'] for o in orgs if o['program_expense_pct']]

        for org in orgs:
            # Percentile ranking
            rev_pct = percentile_rank(org['total_revenue'], revenues)
            prog_pct = percentile_rank(org['program_expense_pct'] or 50, program_pcts)

            # Financial health tercile
            composite = (rev_pct * 0.65) + (prog_pct * 0.35)
            if composite >= 67:
                health = 'Strong'
            elif composite >= 33:
                health = 'Stable'
            else:
                health = 'Inspiring'

            # Insert to tier_b_scores
            conn.execute("""
                INSERT OR REPLACE INTO v4_scores (
                    EIN, merit_score, visibility_tier, financial_health,
                    operating_model, revenue_band, peer_cell_size, metrics_json
                ) VALUES (?, ?, 'Tier_B', ?, ?, ?, ?, ?)
            """, (
                org['EIN'],
                round(composite),
                health,
                model,
                band_idx,
                len(orgs),
                json.dumps({
                    'revenue_percentile': round(rev_pct),
                    'program_percentile': round(prog_pct),
                    'tier': 'B',
                })
            ))
            scored += 1

    conn.commit()
    print(f"[{datetime.now().isoformat()}] ✓ Scored {scored} Tier B orgs")
    print(f"[{datetime.now().isoformat()}] Total v4 coverage: 71,473 (Tier A) + {scored} (Tier B) = {71473 + scored}")
    conn.close()

if __name__ == '__main__':
    score_tier_b()
