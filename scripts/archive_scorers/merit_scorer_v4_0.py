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

# ── Operating Models ─────────────────────────────────────────────────────────
# Defined by HOW an org operates financially — revenue source, expense structure,
# reserve pattern — not by topic. 26 NTEE1 codes → 9 financially coherent models.
# Validated against actual ratio distributions from 130K+ scored orgs.
OPERATING_MODELS = {
    'Clinical_Reimbursement': {
        'ntee': ['E', 'F', 'G', 'H'],
        'description': 'Insurance/Medicaid revenue, clinical staff costs, reimbursement lag',
    },
    'Direct_Delivery': {
        'ntee': ['I', 'J', 'L'],
        'description': 'Grant/contract-funded, highest program ratios, outcomes-driven delivery',
    },
    'Activity_Programming': {
        'ntee': ['A', 'B', 'N'],
        'description': 'Fee + donation mix, curriculum or facility-based programming',
    },
    'Community_Human_Services': {
        'ntee': ['O', 'P', 'S'],
        'description': 'Donation/grant-funded, broad community mission, thin reserves',
    },
    'Emergency_Logistics': {
        'ntee': ['K', 'M'],
        'description': 'Reserve-holding, material distribution, disaster/food supply chain',
    },
    'Cause_Advocacy_Research': {
        'ntee': ['C', 'D', 'Q', 'R', 'U', 'V'],
        'description': 'Donation-driven, advocacy overhead, campaign or knowledge output',
    },
    'Intermediary_Public_Benefit': {
        'ntee': ['T', 'W'],
        'description': 'Grantmaking, pass-through, holds assets for redistribution',
    },
    'Faith_Community': {
        'ntee': ['X'],
        'description': 'Tithing/offering revenue, building-anchored, spiritual and community services',
    },
    'Membership_Mutual_Benefit': {
        'ntee': ['Y', 'Z'],
        'description': 'Dues-based revenue, member-governed, exceptionally high reserves',
    },
}

# ── Revenue Band Breakpoints (octile-based, log₁₀-space) ─────────────────────
# Each model: 8 bands ensuring ~12.5% of orgs per band. Computed from live DB.
REVENUE_BANDS = {
    # Models with >10K orgs get 8 bands; smaller models get 5 bands
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

# ── Financial Health Scale: Model-Specific Meanings ──────────────────────────
FINANCIAL_HEALTH_MEANINGS = {
    'Clinical_Reimbursement': {
        'Strong': 'Strong reimbursement coverage and healthy operating reserves',
        'Stable': 'Consistent patient revenue, steady program delivery',
        'Inspiring': 'Committed to care within tight reimbursement margins',
    },
    'Direct_Delivery': {
        'Strong': 'Solid program efficiency and financial runway for the mission',
        'Stable': 'Reliable service delivery with predictable funding',
        'Inspiring': 'High-impact direct service within resource constraints',
    },
    'Activity_Programming': {
        'Strong': 'Broad programming reach, strong participation-driven revenue',
        'Stable': 'Consistent activity base, steady community engagement',
        'Inspiring': 'Vibrant programming with lean operational means',
    },
    'Community_Human_Services': {
        'Strong': 'Program efficiency, financial resilience across service lines',
        'Stable': 'Reliable community delivery, predictable operational base',
        'Inspiring': 'Remarkable community service within tight constraints',
    },
    'Emergency_Logistics': {
        'Strong': 'Strong surge capacity and reserve depth for response cycles',
        'Stable': 'Reliable response readiness, steady logistics funding',
        'Inspiring': 'Committed frontline response with limited reserves',
    },
    'Cause_Advocacy_Research': {
        'Strong': 'Well-resourced mission and strong organizational staying power',
        'Stable': 'Consistent advocacy funding, steady research operations',
        'Inspiring': 'Impactful advocacy and research within lean resources',
    },
    'Intermediary_Public_Benefit': {
        'Strong': 'Effective grant deployment with strong organizational reserves',
        'Stable': 'Consistent intermediary function, reliable grant flow',
        'Inspiring': 'High-leverage public benefit work with constrained capital',
    },
    'Faith_Community': {
        'Strong': 'Mission vitality supported by sustained congregational giving',
        'Stable': 'Steady congregational support, predictable ministry funding',
        'Inspiring': 'Growing faith mission within meaningful financial constraints',
    },
    'Membership_Mutual_Benefit': {
        'Strong': 'Active member-driven revenue and long-term reserve depth',
        'Stable': 'Stable membership base, consistent mutual support model',
        'Inspiring': 'Growing member community building toward long-term stability',
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

# ── Metric Weights ────────────────────────────────────────────────────────────
# program_ratio: mission delivery efficiency (program spend / total spend)
# reserves_ratio: operational resilience (months of cash runway)
# revenue_ratio: sustainability (3yr avg revenue / expenses; smooths grant cycles)
# asset_intensity: asset base relative to operations (total_assets / revenue)
# net_assets_ratio: solvency, operating-model-relative (net assets / total assets)
#                   captures what liabilities do to an org's financial position
WEIGHTS = {
    'program_ratio':    0.30,
    'reserves_ratio':   0.25,
    'revenue_ratio':    0.15,
    'asset_intensity':  0.15,
    'net_assets_ratio': 0.15,
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
    return 'Community_Human_Services'  # Safe default

def get_revenue_band(revenue: float, model: str) -> int:
    """Find which revenue band this org falls into (0-7)."""
    bands = REVENUE_BANDS.get(model, REVENUE_BANDS['Community_Human_Services'])
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
        reserves_mo = float(org.get('months_of_reserve', 0))
        total_assets_val = org.get('total_assets')
        total_assets = float(total_assets_val) if total_assets_val is not None else None
        # 3-year avg revenue when available; fall back to single-year
        rev3_val = org.get('revenue_3yr_avg')
        revenue_smoothed = float(rev3_val) if rev3_val is not None else revenue
        liab_val = org.get('total_liabilities')
        total_liabilities = float(liab_val) if liab_val is not None else None
    except (ValueError, TypeError):
        return None

    # Program ratio (0-100 scale, already a percentage)
    metrics['program_ratio'] = program_exp if program_exp > 0 else None

    # Reserves ratio (months of reserve, capped at 100 to reduce outlier influence)
    metrics['reserves_ratio'] = min(reserves_mo, 100) if reserves_mo and reserves_mo > 0 else None

    # Revenue ratio: 3yr smoothed revenue / expenses — reduces grant-cycle volatility
    metrics['revenue_ratio'] = revenue_smoothed / expenses if expenses > 0 and revenue_smoothed > 0 else None

    # Asset intensity: total_assets / revenue, capped at 100
    if total_assets is not None and total_assets > 0 and revenue > 0:
        metrics['asset_intensity'] = min(total_assets / revenue, 100)
    else:
        metrics['asset_intensity'] = None

    # Net assets ratio: (assets - liabilities) / assets — solvency, higher = less encumbered
    # Meaningful only relative to operating model peers (hospitals vs. community orgs differ structurally)
    if total_assets is not None and total_liabilities is not None and total_assets > 0:
        metrics['net_assets_ratio'] = (total_assets - total_liabilities) / total_assets
    else:
        metrics['net_assets_ratio'] = None

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

def score_to_health(score: float) -> str:
    """Assign financial health tier from composite score (0–100).
    Thresholds are absolute (not forced thirds) so the label reflects
    actual financial context, not rank-by-construction.
    Natural distribution: ~18% Strong, ~66% Stable, ~18% Inspiring.
    """
    if score >= 67:
        return 'Strong'
    elif score >= 33:
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
    """Score all orgs and return results. O(n log n) via per-cell precompute."""
    results = {}
    METRICS = list(WEIGHTS.keys())

    # Precompute per-cell distributions and sorted arrays once
    cell_sorted = {}  # cell_key -> {metric: sorted np.array}
    for cell_key, cell_orgs in peer_cells.items():
        cell_sorted[cell_key] = {}
        for metric in METRICS:
            vals = []
            for o in cell_orgs:
                m = extract_metrics(o)
                if m:
                    v = m.get(metric)
                    if v is not None:
                        vals.append(v)
            cell_sorted[cell_key][metric] = np.array(sorted(vals), dtype=np.float32) if vals else np.array([], dtype=np.float32)

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

        # Compute percentile ranks using precomputed sorted arrays
        sorted_arrays = cell_sorted.get(cell_key, {})
        percentiles = {}
        for metric in METRICS:
            my_val = my_metrics.get(metric)
            arr = sorted_arrays.get(metric, np.array([]))
            n = len(arr)
            if my_val is not None and n >= 2:
                below = int(np.searchsorted(arr, my_val, side='left'))
                above = n - int(np.searchsorted(arr, my_val, side='right'))
                equal = n - below - above
                pct = round((below + equal / 2.0) / n * 100, 1)
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
            composite = weighted_sum / total_weight
            composite = max(0.0, min(100.0, composite))
        else:
            composite = None

        cell_size = len(peers)
        results[ein] = {
            '_composite': composite,    # temporary; replaced by rank percentile below
            'merit_score': None,        # set in second pass
            'visibility_tier': None,    # set in second pass
            'financial_health': None,   # set in second pass
            'financial_health_meaning': '',
            'operating_model': model,
            'revenue_band': band,
            'peer_group': cell_key,
            'peer_total': cell_size,
            'peer_rank': None,          # set in second pass
            'peer_cell_size': cell_size,
            'metrics': my_metrics,
            'percentiles': percentiles,
            'version': SCORER_VERSION,
        }

    # Second pass: convert each org's composite to a true within-cell rank percentile.
    # This makes merit_score genuinely "where do you rank among your peers" — uniform
    # 0–100 within every cell — so 33/67 thresholds naturally produce equal thirds.
    cell_composites = defaultdict(list)  # cell_key -> [(ein, composite)]
    for ein, r in results.items():
        if r['_composite'] is not None:
            cell_composites[r['peer_group']].append((ein, r['_composite']))

    for cell_key, ein_score_pairs in cell_composites.items():
        scores_arr = np.array([s for _, s in ein_score_pairs], dtype=np.float32)
        sorted_arr = np.sort(scores_arr)
        n = len(sorted_arr)
        for ein, composite in ein_score_pairs:
            below = int(np.searchsorted(sorted_arr, composite, side='left'))
            above = n - int(np.searchsorted(sorted_arr, composite, side='right'))
            equal = n - below - above
            rank_pct = round((below + equal / 2.0) / n * 100, 1)

            r = results[ein]
            r['merit_score'] = rank_pct
            r['visibility_tier'] = score_to_visibility(rank_pct)
            health = score_to_health(composite)  # composite reflects real context; rank_pct stays for peer comparison
            r['financial_health'] = health
            r['financial_health_meaning'] = FINANCIAL_HEALTH_MEANINGS.get(
                r['operating_model'], {}).get(health, '')
            r['peer_rank'] = max(1, round((100 - rank_pct) / 100 * n))

    # Clean up temp key
    for r in results.values():
        r.pop('_composite', None)
        if r['financial_health'] is None:
            r['financial_health'] = 'Inspiring'

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
            revenue_3yr_avg, total_liabilities,
            deductibility
        FROM registry_enriched
        WHERE deductibility = '1'
          AND total_revenue > 0
          AND total_expenses > 0
          AND program_expense_pct IS NOT NULL
          AND program_expense_pct > 0
          AND months_of_reserve IS NOT NULL
          AND net_assets IS NOT NULL
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

    # Write output JSON
    log(f'Writing results to {args.output}...')
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    # Write to DB
    if not args.dry_run:
        log('Writing scores to registry_enriched...')
        t_db = time.time()
        rows = [
            (
                r['merit_score'],
                str(r['revenue_band']),
                r['financial_health'],
                r['merit_score'],        # ntee1_percentile = merit_score (within-cell pct)
                r['merit_score'],        # peer_percentile
                r.get('peer_rank'),
                r.get('peer_total'),
                r['peer_group'],
                ein,
            )
            for ein, r in results.items()
            if r['merit_score'] is not None
        ]
        conn.executemany("""
            UPDATE registry_enriched SET
                merit_score      = ?,
                revenue_band     = ?,
                financial_health = ?,
                ntee1_percentile = ?,
                peer_percentile  = ?,
                peer_rank        = ?,
                peer_total       = ?,
                peer_group       = ?
            WHERE EIN = ?
        """, rows)
        conn.commit()
        log(f'DB write: {len(rows):,} rows in {time.time()-t_db:.1f}s')
    else:
        log('dry-run: skipping DB write')

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
