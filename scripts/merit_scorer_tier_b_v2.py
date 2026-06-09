#!/usr/bin/env python3
"""
Tier B Scorer v2 — Expand v4 scoring to 268K partial-data orgs (registry_enriched)

Tier A: 369,091 complete-fingerprint orgs (all 5 metrics, via merit_scorer_v4_0.py)
Tier B: ~268K additional orgs with revenue + expenses (derive program_pct from NTEE defaults)

Uses same peer grouping as Tier A (9 operating models, model-specific revenue bands).
Program expense ratio derived from available data with NTEE-level defaults.

Scores on 2 core metrics:
  - Revenue percentile (65% weight): sustainability proxy
  - Program percentile (35% weight): mission efficiency proxy

Writes directly to registry_enriched (merit_score, financial_health, operating_model, revenue_band).

Efficiency: batch load, no API calls, local inference only. ~2 minutes for 268K orgs.
"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"

# NTEE-level program spend defaults (if individual org data missing)
NTEE_PROGRAM_DEFAULTS = {
    'A': 0.85, 'B': 0.88, 'C': 0.82, 'D': 0.80, 'E': 0.75, 'F': 0.80,
    'G': 0.78, 'H': 0.85, 'I': 0.70, 'J': 0.80, 'K': 0.85, 'L': 0.75,
    'M': 0.80, 'N': 0.80, 'O': 0.85, 'P': 0.75, 'Q': 0.80, 'R': 0.75,
    'S': 0.80, 'T': 0.30, 'U': 0.85, 'V': 0.85, 'W': 0.75, 'X': 0.70,
    'Y': 0.50, 'Z': 0.50,
}

# Same 9 models + revenue bands as v4.0
OPERATING_MODELS = {
    'Clinical_Reimbursement': ['E', 'F', 'G', 'H'],
    'Direct_Delivery': ['I', 'J', 'L'],
    'Activity_Programming': ['A', 'B', 'N'],
    'Community_Human_Services': ['O', 'P', 'S'],
    'Emergency_Logistics': ['K', 'M'],
    'Cause_Advocacy_Research': ['C', 'D', 'Q', 'R', 'U', 'V'],
    'Intermediary_Public_Benefit': ['T', 'W'],
    'Faith_Community': ['X'],
    'Membership_Mutual_Benefit': ['Y', 'Z'],
}

REVENUE_BANDS = {
    'Clinical_Reimbursement': [
        (0, 57574), (57574, 137822), (137822, 356219), (356219, 1859828),
        (1859828, float('inf'))
    ],
    'Direct_Delivery': [
        (0, 46941), (46941, 83998), (83998, 134978), (134978, 228936),
        (228936, 416113), (416113, 903911), (903911, 2255466), (2255466, float('inf'))
    ],
    'Activity_Programming': [
        (0, 27249), (27249, 52819), (52819, 76834), (76834, 110281),
        (110281, 165472), (165472, 284527), (284527, 828352), (828352, float('inf'))
    ],
    'Community_Human_Services': [
        (0, 31190), (31190, 61908), (61908, 100883), (100883, 162333),
        (162333, 271640), (271640, 514120), (514120, 1382545), (1382545, float('inf'))
    ],
    'Emergency_Logistics': [
        (0, 60297), (60297, 106948), (106948, 187162), (187162, 459258),
        (459258, float('inf'))
    ],
    'Cause_Advocacy_Research': [
        (0, 42742), (42742, 91647), (91647, 173159), (173159, 460190),
        (460190, float('inf'))
    ],
    'Intermediary_Public_Benefit': [
        (0, 50310), (50310, 117090), (117090, 278734), (278734, 1335713),
        (1335713, float('inf'))
    ],
    'Faith_Community': [
        (0, 47539), (47539, 92415), (92415, 157757), (157757, 373778),
        (373778, float('inf'))
    ],
    'Membership_Mutual_Benefit': [
        (0, 45548), (45548, 100165), (100165, 258066), (258066, 1540726),
        (1540726, float('inf'))
    ],
}

FINANCIAL_HEALTH_MEANINGS = {
    'Clinical_Reimbursement': {'Strong': 'Strong reimbursement coverage', 'Stable': 'Consistent patient revenue', 'Inspiring': 'Care within tight margins'},
    'Direct_Delivery': {'Strong': 'Solid program efficiency', 'Stable': 'Reliable service delivery', 'Inspiring': 'Impact within constraints'},
    'Activity_Programming': {'Strong': 'Broad programming reach', 'Stable': 'Consistent activity base', 'Inspiring': 'Vibrant with lean means'},
    'Community_Human_Services': {'Strong': 'Program efficiency and resilience', 'Stable': 'Reliable community delivery', 'Inspiring': 'Service within constraints'},
    'Emergency_Logistics': {'Strong': 'Strong surge capacity', 'Stable': 'Reliable response readiness', 'Inspiring': 'Committed response with limited reserves'},
    'Cause_Advocacy_Research': {'Strong': 'Well-resourced mission', 'Stable': 'Consistent advocacy funding', 'Inspiring': 'Impact within lean resources'},
    'Intermediary_Public_Benefit': {'Strong': 'Effective deployment', 'Stable': 'Consistent intermediary function', 'Inspiring': 'High-leverage work with constraints'},
    'Faith_Community': {'Strong': 'Sustained congregational giving', 'Stable': 'Steady congregational support', 'Inspiring': 'Growing mission within constraints'},
    'Membership_Mutual_Benefit': {'Strong': 'Active member revenue and reserves', 'Stable': 'Stable membership base', 'Inspiring': 'Growing member community'},
}

def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

def get_model_by_ntee(ntee1: str) -> str:
    ntee1 = (ntee1 or 'U').upper()
    for model, codes in OPERATING_MODELS.items():
        if ntee1 in codes:
            return model
    return 'Community_Human_Services'

def get_revenue_band(revenue: float, model: str) -> int:
    bands = REVENUE_BANDS.get(model, REVENUE_BANDS['Community_Human_Services'])
    for i, (low, high) in enumerate(bands):
        if low <= revenue < high:
            return i
    return len(bands) - 1

def derive_program_pct(org: dict) -> float:
    """Derive program expense % from org data or NTEE default."""
    if org.get('program_expense_pct') and org['program_expense_pct'] > 0:
        return org['program_expense_pct']

    # Use NTEE default
    ntee1 = org.get('NTEE1', 'U')
    default = NTEE_PROGRAM_DEFAULTS.get(ntee1, 0.75)
    return default * 100

def percentile_rank(value: float, values: list) -> float:
    """Percentile rank of value in sorted list."""
    if not values or len(values) < 2:
        return 50.0
    sorted_vals = sorted([v for v in values if v is not None])
    if not sorted_vals:
        return 50.0
    below = sum(1 for v in sorted_vals if v < value)
    equal = sum(1 for v in sorted_vals if v == value)
    pct = (below + equal / 2.0) / len(sorted_vals) * 100.0
    return max(1.0, min(99.0, pct))

def score_to_health(composite: float) -> str:
    """Map composite score to financial health tier."""
    if composite >= 67:
        return 'Strong'
    elif composite >= 33:
        return 'Stable'
    else:
        return 'Inspiring'

def score_to_visibility(score: float) -> str:
    """Map 0-100 score to visibility tier."""
    if score >= 85:
        return 'Blazing'
    elif score >= 70:
        return 'Burning Bright'
    elif score >= 55:
        return 'Steady Flame'
    elif score >= 35:
        return 'Growing'
    else:
        return 'Just Starting'

def main():
    parser = argparse.ArgumentParser(description='Tier B Scorer v2 — Partial-data expansion')
    parser.add_argument('--dry-run', action='store_true', help='Compute but do not write to DB')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of orgs (0=all)')
    args = parser.parse_args()

    log('=' * 70)
    log('Tier B Scorer v2 starting')
    log(f'dry_run={args.dry_run}  limit={args.limit or "all"}')
    log('=' * 70)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Load unscored orgs with revenue + expenses
    log('Loading Tier B candidates (revenue + expenses, no merit_score yet)...')
    limit_clause = f'LIMIT {args.limit}' if args.limit else ''
    rows = conn.execute(f"""
        SELECT
            EIN, NTEE1, total_revenue, total_expenses,
            program_expense_pct
        FROM registry_enriched
        WHERE deductibility = '1'
          AND org_status = 'active'
          AND total_revenue > 0
          AND total_expenses > 0
          AND merit_score IS NULL
        {limit_clause}
    """).fetchall()

    orgs = [dict(row) for row in rows]
    log(f'Loaded {len(orgs):,} Tier B candidates')

    # Build peer cells
    log('Building peer cells...')
    peer_cells = {}
    model_counts = {}

    for org in orgs:
        model = get_model_by_ntee(org['NTEE1'])
        band = get_revenue_band(org['total_revenue'], model)
        cell_key = f"{model}|{band}"

        if cell_key not in peer_cells:
            peer_cells[cell_key] = []
        peer_cells[cell_key].append(org)

        model_counts[model] = model_counts.get(model, 0) + 1

    log(f'Built {len(peer_cells)} peer cells')
    for model in sorted(model_counts.keys()):
        log(f'  {model:<30s} {model_counts[model]:>8,} orgs')

    # Score each peer cell
    log('Scoring peer cells...')
    updates = []
    scored_count = 0

    for cell_key, cell_orgs in peer_cells.items():
        model, band = cell_key.split('|')
        band = int(band)

        # Compute percentiles within peer cell
        revenues = [o['total_revenue'] for o in cell_orgs if o['total_revenue']]
        programs = [derive_program_pct(o) for o in cell_orgs]

        for org in cell_orgs:
            # 2-metric composite: revenue (65%) + program pct (35%)
            rev_pct = percentile_rank(org['total_revenue'], revenues)
            prog_pct = percentile_rank(derive_program_pct(org), programs)

            composite = (rev_pct * 0.65) + (prog_pct * 0.35)
            composite = max(0.0, min(100.0, composite))

            merit_band = score_to_visibility(composite)
            health = score_to_health(composite)

            updates.append((
                round(composite, 1),
                str(band),
                health,
                merit_band,
                org['EIN'],
            ))
            scored_count += 1

    # Write to DB
    if not args.dry_run:
        log(f'Writing {scored_count:,} scores to registry_enriched...')
        t_start = datetime.now()
        conn.executemany("""
            UPDATE registry_enriched SET
                merit_score = ?,
                revenue_band = ?,
                financial_health = ?,
                merit_band = ?
            WHERE EIN = ?
        """, updates)
        conn.commit()
        elapsed = (datetime.now() - t_start).total_seconds()
        log(f'DB write complete: {scored_count:,} rows in {elapsed:.1f}s')
    else:
        log(f'dry-run: skipping DB write of {scored_count:,} rows')

    log(f'Score distribution:')
    log(f'  Total scored: {scored_count:,}')
    log(f'  Tier A (from v4.0): 369,091')
    log(f'  Tier B (this run): {scored_count:,}')
    log(f'  Combined coverage: {369091 + scored_count:,} orgs')

    log('=' * 70)
    log('Tier B Scorer v2 complete')
    log('=' * 70)

    conn.close()

if __name__ == '__main__':
    main()
