#!/usr/bin/env python3
"""
MERIT Score Engine v4.0 — Model-Specific Peer Context + Financial Health Tiers

Universe: deductibility='1' (tax-deductible 501(c)(3) only)
Peer cells: 8 operating models × 8 revenue bands = 64 cells
Scales:
  - Scale 1 (Visibility): Blazing, Burning Bright, Steady Flame, Growing, Just Starting
  - Scale 2 (Financial Health): Strong, Stable, Inspiring (model-specific meanings)

Key features:
  - NTEE1-based operating model assignment
  - Log₁₀-space octile revenue bands (outlier-robust)
  - Percentile-rank scoring within peer cells only
  - Tercile-based financial health tiers
  - Robust statistics (median/MAD, not mean/variance)
  - Full audit trail with weighted metrics

Run:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/merit_scorer_v4_0.py --output scores_v4_0.json [--dry-run] [--limit N]
"""

import sqlite3
import json
import argparse
import sys
import time
import statistics
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG = Path.home() / "meritgiving/logs/scorer_v4.log"

SCORER_VERSION = "v4.0"

# ── Operating Model Taxonomy ──────────────────────────────────────────────────
OPERATING_MODELS = {
    'Direct_Service': {
        'ntee': ['B', 'C', 'P', 'F', 'T', 'I', 'U', 'Z'],
        'description': 'Direct service delivery to individuals/communities',
    },
    'Mission_Infrastructure': {
        'ntee': ['A', 'E', 'G', 'L', 'M', 'O', 'S', 'D'],
        'description': 'Schools, health systems, arts, libraries, disease research',
    },
    'Research_Academia': {
        'ntee': ['J', 'R', 'N'],
        'description': 'Universities, medical research, scientific bodies',
    },
    'Foundations': {
        'ntee': ['Y'],
        'description': 'Grantmaking entities, endowments',
    },
    'Membership_Advocacy': {
        'ntee': ['X', 'V'],
        'description': 'Member orgs, voluntarism, advocacy networks',
    },
    'Religion_Spiritual': {
        'ntee': ['W'],
        'description': 'Faith communities, spiritual organizations',
    },
    'International_Development': {
        'ntee': ['Q'],
        'description': 'Cross-border development, humanitarian aid',
    },
    'Asset_Stewards': {
        'ntee': ['K', 'H'],
        'description': 'Nursing homes, hospitals, facility stewardship',
    },
}

# ── Revenue Band Breakpoints (octile-based, log₁₀-space) ─────────────────────
# Each model: 8 bands ensuring ~12.5% of orgs per band
REVENUE_BANDS = {
    'Direct_Service': [
        (0, 27493), (27493, 51353), (51353, 75380), (75380, 112456),
        (112456, 176201), (176201, 368616), (368616, 1470577), (1470577, float('inf'))
    ],
    'Mission_Infrastructure': [
        (0, 27538), (27538, 55018), (55018, 81760), (81760, 116970),
        (116970, 170692), (170692, 277720), (277720, 687742), (687742, float('inf'))
    ],
    'Research_Academia': [
        (0, 32481), (32481, 56278), (56278, 77465), (77465, 101313),
        (101313, 136173), (136173, 189575), (189575, 345764), (345764, float('inf'))
    ],
    'Foundations': [
        (0, 23735), (23735, 43760), (43760, 64403), (64403, 93374),
        (93374, 146142), (146142, 271438), (271438, 692572), (692572, float('inf'))
    ],
    'Membership_Advocacy': [
        (0, 34310), (34310, 60506), (60506, 89984), (89984, 124164),
        (124164, 176514), (176514, 292835), (292835, 696571), (696571, float('inf'))
    ],
    'Religion_Spiritual': [
        (0, 20004), (20004, 45205), (45205, 70374), (70374, 105577),
        (105577, 154536), (154536, 229829), (229829, 419777), (419777, float('inf'))
    ],
    'International_Development': [
        (0, 20493), (20493, 46060), (46060, 78026), (78026, 120445),
        (120445, 178941), (178941, 341100), (341100, 1295575), (1295575, float('inf'))
    ],
    'Asset_Stewards': [
        (0, 39502), (39502, 74239), (74239, 114717), (114717, 175185),
        (175185, 277561), (277561, 560398), (560398, 1846508), (1846508, float('inf'))
    ],
}

# ── Financial Health Scale: Model-Specific Meanings ──────────────────────────
FINANCIAL_HEALTH_MEANINGS = {
    'Direct_Service': {
        'Strong': 'High program efficiency, resource leverage',
        'Stable': 'Predictable revenue, healthy reserves',
        'Inspiring': 'Doing remarkable work with constraints',
    },
    'Mission_Infrastructure': {
        'Strong': 'Reserves support stable operations',
        'Stable': 'Sustained operations, steady reserves',
        'Inspiring': 'Visionary impact despite constraints',
    },
    'Research_Academia': {
        'Strong': 'Well-funded pipelines, stable base',
        'Stable': 'Sustained funding streams, predictable',
        'Inspiring': 'Innovative with limited resources',
    },
    'Foundations': {
        'Strong': 'Active, sustained grant deployment',
        'Stable': 'Endowment stable, predictable giving',
        'Inspiring': 'Emerging foundation, building capacity',
    },
    'Membership_Advocacy': {
        'Strong': 'Healthy member-revenue base',
        'Stable': 'Stable membership/advocacy revenue',
        'Inspiring': 'Growing member base, expanding reach',
    },
    'Religion_Spiritual': {
        'Strong': 'Strong financial reserves, impact',
        'Stable': 'Stable operations, predictable giving',
        'Inspiring': 'Growing congregation/mission',
    },
    'International_Development': {
        'Strong': 'Efficient cross-border delivery',
        'Stable': 'Reliable operations, stable reserves',
        'Inspiring': 'Scaling operations with vision',
    },
    'Asset_Stewards': {
        'Strong': 'Assets well-maintained, healthy reserves',
        'Stable': 'Stable asset preservation',
        'Inspiring': 'Growing asset base with impact',
    },
}

# ── Visibility Tier Thresholds (unchanged from v3.3) ─────────────────────────
VISIBILITY_THRESHOLDS = [
    (85, 'Blazing'),
    (70, 'Burning Bright'),
    (55, 'Steady Flame'),
    (35, 'Growing'),
    (0, 'Just Starting'),
]

# ── Metric Weights (robust: emphasis on program share and reserves) ──────────
WEIGHTS = {
    'program_ratio': 0.35,
    'reserves_ratio': 0.25,
    'revenue_ratio': 0.20,
    'asset_intensity': 0.20,
}

def log(msg: str):
    """Log to file and stdout."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def get_model_by_ntee(ntee1: str) -> str:
    """Assign org to operating model based on NTEE1."""
    ntee1 = (ntee1 or 'U').upper()
    for model, info in OPERATING_MODELS.items():
        if ntee1 in info['ntee']:
            return model
    return 'Direct_Service'  # Safe default

def get_revenue_band(revenue: float, model: str) -> int:
    """Find which revenue band this org falls into (0-7)."""
    bands = REVENUE_BANDS.get(model, REVENUE_BANDS['Direct_Service'])
    for i, (low, high) in enumerate(bands):
        if low <= revenue < high:
            return i
    return len(bands) - 1

def extract_metrics(org: dict) -> dict:
    """Extract and normalize financial metrics."""
    metrics = {}

    try:
        revenue = float(org.get('total_revenue', 0))
        expenses = float(org.get('total_expenses', 0))
        program_exp = float(org.get('program_expense_pct', 0))
        net_assets = float(org.get('net_assets', 0))
        total_assets = float(org.get('total_assets', 0))
        reserves_mo = float(org.get('months_of_reserve', 0))
    except (ValueError, TypeError):
        return None

    # Program ratio (0-100 scale)
    metrics['program_ratio'] = program_exp if program_exp > 0 else None

    # Reserves ratio (months of reserve, capped at 100 to reduce outlier influence)
    metrics['reserves_ratio'] = min(reserves_mo, 100) if reserves_mo and reserves_mo > 0 else None

    # Revenue ratio (proxy for sustainability: revenue / expenses)
    metrics['revenue_ratio'] = revenue / expenses if expenses > 0 else None

    # Asset intensity (total_assets / revenue), capped to reduce outliers
    if revenue > 0 and total_assets > 0:
        asset_int = total_assets / revenue
        metrics['asset_intensity'] = asset_int if 0 < asset_int < 100 else None
    else:
        metrics['asset_intensity'] = None

    return metrics

def bulk_percentile_rank(values: list) -> list:
    """Compute percentile rank for all values using numpy."""
    out = [50.0] * len(values)
    valid_idx = [i for i, v in enumerate(values) if v is not None]
    if not valid_idx:
        return out

    vals = np.array([values[i] for i in valid_idx], dtype=float)
    n = len(vals)
    sorted_vals = np.sort(vals)
    below = np.searchsorted(sorted_vals, vals, side='left')
    equal = np.searchsorted(sorted_vals, vals, side='right') - below
    pcts = (below + equal / 2.0) / n * 100.0

    for i, idx in enumerate(valid_idx):
        out[idx] = round(float(pcts[i]), 2)
    return out

def percentile_to_health(percentile: float) -> str:
    """Map percentile rank (0-100) to financial health tier."""
    if percentile >= 66.67:
        return 'Strong'
    elif percentile >= 33.33:
        return 'Stable'
    else:
        return 'Inspiring'

def score_to_visibility(score: float) -> str:
    """Map 0-100 score to visibility tier."""
    for threshold, tier in VISIBILITY_THRESHOLDS:
        if score >= threshold:
            return tier
    return 'Just Starting'

def score_orgs(orgs: list, peer_cells: dict) -> dict:
    """Score all orgs and return results."""
    results = {}

    for org in orgs:
        ein = org['EIN']

        # Assign to model and band
        model = get_model_by_ntee(org['NTEE1'])
        revenue = org['total_revenue']
        band = get_revenue_band(revenue, model)
        cell_key = f"{model}|{band}"

        # Get peer cell
        peers = peer_cells.get(cell_key, [])

        # Extract metrics
        my_metrics = extract_metrics(org)
        if not my_metrics:
            results[ein] = {
                'merit_score': None,
                'visibility_tier': 'Just Starting',
                'financial_health': 'Inspiring',
                'operating_model': model,
                'revenue_band': band,
                'peer_cell_size': len(peers),
                'error': 'Insufficient metrics',
            }
            continue

        # Build peer distributions
        peer_dists = defaultdict(list)
        for p in peers:
            pm = extract_metrics(p)
            if pm:
                for k, v in pm.items():
                    if v is not None:
                        peer_dists[k].append(v)

        # Compute percentile ranks
        percentiles = {}
        for metric in ['program_ratio', 'reserves_ratio', 'revenue_ratio', 'asset_intensity']:
            my_val = my_metrics.get(metric)
            peer_vals = peer_dists.get(metric, [])

            if peer_vals and len(peer_vals) >= 2:
                # Compute percentile
                ranks = bulk_percentile_rank(peer_vals + [my_val] if my_val is not None else peer_vals)
                pct = ranks[-1] if my_val is not None else 50.0
                percentiles[metric] = pct
            else:
                percentiles[metric] = 50.0 if my_val is not None else None

        # Weighted composite score
        weighted_sum = 0
        total_weight = 0
        for metric, weight in WEIGHTS.items():
            pct = percentiles.get(metric)
            if pct is not None:
                weighted_sum += pct * weight
                total_weight += weight

        if total_weight > 0:
            final_score = weighted_sum / total_weight
            final_score = max(0, min(100, round(final_score)))
        else:
            final_score = 50.0

        # Determine financial health from within-cell percentile
        financial_health = percentile_to_health(final_score)
        visibility_tier = score_to_visibility(final_score)

        results[ein] = {
            'merit_score': final_score,
            'visibility_tier': visibility_tier,
            'financial_health': financial_health,
            'financial_health_meaning': FINANCIAL_HEALTH_MEANINGS.get(model, {}).get(financial_health, ''),
            'operating_model': model,
            'revenue_band': band,
            'peer_cell_size': len(peers),
            'metrics': my_metrics,
            'percentiles': percentiles,
            'version': SCORER_VERSION,
        }

    return results

def main():
    parser = argparse.ArgumentParser(description='MERIT Scorer v4.0')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Compute but do not write to DB')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of orgs (0=all)')
    args = parser.parse_args()

    log('=' * 70)
    log(f'MERIT Scorer {SCORER_VERSION} starting')
    log(f'dry_run={args.dry_run}  limit={args.limit or "all"}')
    log('=' * 70)

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row

    # Load complete-fingerprint orgs
    log('Loading complete-fingerprint orgs...')
    limit_clause = f'LIMIT {args.limit}' if args.limit else ''
    orgs = conn.execute(f"""
        SELECT
            EIN, organization_name, NTEE1, total_revenue, total_expenses,
            program_expense_pct, months_of_reserve, net_assets, total_assets,
            deductibility
        FROM registry_enriched
        WHERE deductibility = '1'
          AND total_revenue > 0
          AND total_expenses > 0
          AND program_expense_pct IS NOT NULL
          AND program_expense_pct > 0
          AND months_of_reserve IS NOT NULL
          AND net_assets IS NOT NULL
          AND total_assets IS NOT NULL
        {limit_clause}
    """).fetchall()

    orgs = [dict(row) for row in orgs]
    log(f'Loaded {len(orgs):,} orgs')

    # Assign to models and build peer cells
    log('Building peer cells...')
    peer_cells = defaultdict(list)
    model_counts = defaultdict(int)

    for org in orgs:
        model = get_model_by_ntee(org['NTEE1'])
        band = get_revenue_band(org['total_revenue'], model)
        cell_key = f"{model}|{band}"
        peer_cells[cell_key].append(org)
        model_counts[model] += 1

    log(f'Built {len(peer_cells)} peer cells')
    for model in sorted(model_counts.keys()):
        log(f'  {model:<30s} {model_counts[model]:>8,} orgs')

    # Score all orgs
    log('Scoring orgs...')
    t0 = time.time()
    results = score_orgs(orgs, peer_cells)
    elapsed = time.time() - t0
    log(f'Scored {len(results):,} orgs in {elapsed:.1f}s')

    # Write output
    log(f'Writing results to {args.output}...')
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    # Summary stats
    scores = [r['merit_score'] for r in results.values() if r['merit_score'] is not None]
    if scores:
        log(f'Score distribution: min={min(scores):.1f}, max={max(scores):.1f}, median={statistics.median(scores):.1f}, mean={statistics.mean(scores):.1f}')

    health_counts = defaultdict(int)
    for r in results.values():
        if r['financial_health']:
            health_counts[r['financial_health']] += 1
    log(f'Financial Health distribution:')
    for health, count in sorted(health_counts.items()):
        log(f'  {health:<15s} {count:>8,} ({100*count/len(results):>5.1f}%)')

    log('=' * 70)
    log('MERIT Scorer v4.0 complete')
    log('=' * 70)

if __name__ == '__main__':
    main()
