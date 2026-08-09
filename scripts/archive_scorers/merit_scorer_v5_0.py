#!/usr/bin/env python3
"""
MERIT Score Engine v5.0 — Financial Operating Model + Revenue Band Taxonomy

Universe: deductibility='1' (tax-deductible 501(c)(3) only)
Peer cells: 5 financial archetypes × 3 revenue bands = 15 cells
Scoring: Percentile rank within peer group (same archetype + band)

Key features:
  - 5 financial archetypes (Donation-Funded, Fee-for-Service, Endowment, Membership, Mutual-Benefit)
  - 3 revenue bands: Micro (<$150K), Professional ($150K-$700K), Established (>$700K)
  - Empirically grounded in 1.75M org-years of IRS 990 data
  - 92.5% year-over-year cluster stability
  - Percentile-rank scoring within peer groups
  - Donor-facing copy generation

Run:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/merit_scorer_v5_0.py --output scores_v5_0.json [--dry-run] [--limit N]
"""

import sqlite3
import json
import argparse
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import statistics

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG = Path.home() / "meritgiving/logs/scorer_v5.log"

SCORER_VERSION = "v5.0"

# ── 5 Financial Archetypes ────────────────────────────────────────────────────
# Based on cluster analysis of 1.75M org-years: 10-dimensional financial behavior space
# Stable at 92.5% year-over-year cohesion (k=5 is the optimal clustering solution)
ARCHETYPES = {
    'donation_funded': {
        'id': 0,
        'name': 'Donation-Funded Programs',
        'description': 'Primary revenue from donations, grants, contributions',
        'pct_sector': 52,
    },
    'fee_for_service': {
        'id': 1,
        'name': 'Fee-for-Service Operators',
        'description': 'Primary revenue from earned revenue (fees, tuition, billing)',
        'pct_sector': 37,
    },
    'endowment': {
        'id': 2,
        'name': 'Endowment-Funded Grantmakers',
        'description': 'Primary revenue from endowment/investment income',
        'pct_sector': 9,
    },
    'membership': {
        'id': 3,
        'name': 'Membership Dues Organizations',
        'description': 'Primary revenue from membership dues',
        'pct_sector': 1,
    },
    'mutual_benefit': {
        'id': 4,
        'name': 'Mutual-Benefit Payers',
        'description': 'Primary revenue from earned + member benefits',
        'pct_sector': 1,
    },
}

# ── 3 Revenue Bands ────────────────────────────────────────────────────────────
# Based on analysis of sub-$1M orgs: reveals professionalization inflection at $150K
# - Micro: volunteer-heavy, high reserves, no staff
# - Professional: first hiring wave, reserves drop, financial stress peaks
# - Established: mature, staff-intensive, stable reserves
REVENUE_BANDS = {
    'micro': {'id': 0, 'min': 0, 'max': 150000, 'label': 'Micro (<$150K)'},
    'professional': {'id': 1, 'min': 150000, 'max': 700000, 'label': 'Professional ($150K–$700K)'},
    'established': {'id': 2, 'min': 700000, 'max': float('inf'), 'label': 'Established (>$700K)'},
}

# ── NTEE → Archetype Mapping ──────────────────────────────────────────────────
# All 27 NTEE1 codes mapped to archetypes based on empirical composition analysis
# 13 Clean (≥60% one archetype), 5 Medium-risk (45-59%), 7 High-risk (genuinely split)
NTEE_TO_ARCHETYPE = {
    # Clean categories
    'D': 'donation_funded',  # Religion
    'F': 'donation_funded',  # Social Services
    'G': 'donation_funded',  # Environment
    'H': 'donation_funded',  # Mental Health/Dev
    'O': 'donation_funded',  # Civil Rights
    'P': 'donation_funded',  # Legal Services
    'Q': 'donation_funded',  # Science
    'R': 'donation_funded',  # International
    'V': 'donation_funded',  # Research
    'W': 'donation_funded',  # Policy
    'X': 'donation_funded',  # Religious
    'I': 'donation_funded',  # Community/Education
    'Z': 'donation_funded',  # Unclassified

    'Y': 'endowment',  # Foundations

    'J': 'fee_for_service',  # Higher Education

    # Medium-risk (default to primary, can be questioned)
    'A': 'donation_funded',  # Arts (61% DF, 35% FFS)
    'K': 'donation_funded',  # Education (66% DF, 34% FFS)
    'M': 'donation_funded',  # Hospitals (68% DF, 32% FFS)
    'T': 'donation_funded',  # Advocacy (55% DF, 35% FFS)

    # High-risk (MUST ASK for clarification)
    'B': 'donation_funded',  # Civic/Mutual (44% DF, 44% MB) — default DF, ask
    'C': 'donation_funded',  # Healthcare (70% DF, 30% FFS) — default DF, ask
    'E': 'fee_for_service',  # Mental Health (28% DF, 52% FFS) — default FFS, ask
    'L': 'donation_funded',  # Animals (52% DF, 52% FFS) — split, ask
    'N': 'fee_for_service',  # Youth (25% DF, 58% FFS) — default FFS, ask
    'S': 'donation_funded',  # Civic/Social (52% DF, 48% MB) — default DF, ask
    'U': 'endowment',  # Grantmaking (44% END, 44% DF) — default END, ask
}

# ── Benchmarks: 15 Groups × Metrics ────────────────────────────────────────────
# Each group: (min_orgs, P50_reserves, P50_labor%, healthy_rate%)
# Data from 2024 snapshot of 1.75M org-years, stratified by archetype + band
BENCHMARKS = {
    ('donation_funded', 'micro'): {
        'label': 'Donation-Funded Programs, Micro (<$150K)',
        'org_count': 29000,
        'reserves_p50': 20.0,
        'reserves_p25': 16.0,
        'reserves_p75': 37.0,
        'labor_pct_p50': 0,
        'labor_pct_p25': 0,
        'labor_pct_p75': 5,
        'healthy_rate': 65,
    },
    ('donation_funded', 'professional'): {
        'label': 'Donation-Funded Programs, Professional ($150K–$700K)',
        'org_count': 77000,
        'reserves_p50': 11.0,
        'reserves_p25': 7.2,
        'reserves_p75': 16.2,
        'labor_pct_p50': 15,
        'labor_pct_p25': 8,
        'labor_pct_p75': 22,
        'healthy_rate': 51,
    },
    ('donation_funded', 'established'): {
        'label': 'Donation-Funded Programs, Established (>$700K)',
        'org_count': 62000,
        'reserves_p50': 11.0,
        'reserves_p25': 10.0,
        'reserves_p75': 13.0,
        'labor_pct_p50': 38,
        'labor_pct_p25': 30,
        'labor_pct_p75': 45,
        'healthy_rate': 47,
    },
    ('fee_for_service', 'micro'): {
        'label': 'Fee-for-Service Operators, Micro (<$150K)',
        'org_count': 9000,
        'reserves_p50': 21.0,
        'reserves_p25': 18.0,
        'reserves_p75': 25.0,
        'labor_pct_p50': 0,
        'labor_pct_p25': 0,
        'labor_pct_p75': 5,
        'healthy_rate': 60,
    },
    ('fee_for_service', 'professional'): {
        'label': 'Fee-for-Service Operators, Professional ($150K–$700K)',
        'org_count': 43000,
        'reserves_p50': 9.7,
        'reserves_p25': 8.0,
        'reserves_p75': 12.0,
        'labor_pct_p50': 12,
        'labor_pct_p25': 8,
        'labor_pct_p75': 15,
        'healthy_rate': 42,
    },
    ('fee_for_service', 'established'): {
        'label': 'Fee-for-Service Operators, Established (>$700K)',
        'org_count': 62000,
        'reserves_p50': 8.8,
        'reserves_p25': 7.0,
        'reserves_p75': 11.0,
        'labor_pct_p50': 51,
        'labor_pct_p25': 45,
        'labor_pct_p75': 60,
        'healthy_rate': 42,
    },
    ('endowment', 'micro'): {
        'label': 'Endowment-Funded Grantmakers, Micro (<$150K)',
        'org_count': 12000,
        'reserves_p50': 120.0,
        'reserves_p25': 120.0,
        'reserves_p75': 120.0,
        'labor_pct_p50': 0,
        'labor_pct_p25': 0,
        'labor_pct_p75': 10,
        'healthy_rate': 98,
    },
    ('endowment', 'professional'): {
        'label': 'Endowment-Funded Grantmakers, Professional ($150K–$700K)',
        'org_count': 9000,
        'reserves_p50': 120.0,
        'reserves_p25': 120.0,
        'reserves_p75': 120.0,
        'labor_pct_p50': 29,
        'labor_pct_p25': 20,
        'labor_pct_p75': 40,
        'healthy_rate': 99,
    },
    ('endowment', 'established'): {
        'label': 'Endowment-Funded Grantmakers, Established (>$700K)',
        'org_count': 8000,
        'reserves_p50': 120.0,
        'reserves_p25': 120.0,
        'reserves_p75': 120.0,
        'labor_pct_p50': 72,
        'labor_pct_p25': 60,
        'labor_pct_p75': 80,
        'healthy_rate': 99,
    },
    ('membership', 'micro'): {
        'label': 'Membership Dues Organizations, Micro (<$150K)',
        'org_count': 174,
        'reserves_p50': 46.0,
        'reserves_p25': 35.0,
        'reserves_p75': 60.0,
        'labor_pct_p50': 97,
        'labor_pct_p25': 90,
        'labor_pct_p75': 100,
        'healthy_rate': 92,
    },
    ('membership', 'professional'): {
        'label': 'Membership Dues Organizations, Professional ($150K–$700K)',
        'org_count': 524,
        'reserves_p50': 37.0,
        'reserves_p25': 25.0,
        'reserves_p75': 50.0,
        'labor_pct_p50': 98,
        'labor_pct_p25': 92,
        'labor_pct_p75': 100,
        'healthy_rate': 89,
    },
    ('membership', 'established'): {
        'label': 'Membership Dues Organizations, Established (>$700K)',
        'org_count': 1300,
        'reserves_p50': 14.0,
        'reserves_p25': 10.0,
        'reserves_p75': 20.0,
        'labor_pct_p50': 98,
        'labor_pct_p25': 95,
        'labor_pct_p75': 100,
        'healthy_rate': 78,
    },
    ('mutual_benefit', 'micro'): {
        'label': 'Mutual-Benefit Payers, Micro (<$150K)',
        'org_count': 527,
        'reserves_p50': 81.0,
        'reserves_p25': 60.0,
        'reserves_p75': 100.0,
        'labor_pct_p50': 7,
        'labor_pct_p25': 0,
        'labor_pct_p75': 15,
        'healthy_rate': 81,
    },
    ('mutual_benefit', 'professional'): {
        'label': 'Mutual-Benefit Payers, Professional ($150K–$700K)',
        'org_count': 1100,
        'reserves_p50': 16.0,
        'reserves_p25': 12.0,
        'reserves_p75': 25.0,
        'labor_pct_p50': 84,
        'labor_pct_p25': 70,
        'labor_pct_p75': 95,
        'healthy_rate': 59,
    },
    ('mutual_benefit', 'established'): {
        'label': 'Mutual-Benefit Payers, Established (>$700K)',
        'org_count': 3300,
        'reserves_p50': 11.0,
        'reserves_p25': 8.0,
        'reserves_p75': 15.0,
        'labor_pct_p50': 97,
        'labor_pct_p25': 90,
        'labor_pct_p75': 100,
        'healthy_rate': 53,
    },
}

def log(msg: str):
    """Log to file and stdout."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def get_archetype_by_ntee(ntee1: str) -> str:
    """Assign org to archetype based on NTEE1 code."""
    ntee1 = (ntee1 or 'Z').upper()
    return NTEE_TO_ARCHETYPE.get(ntee1, 'donation_funded')

def get_revenue_band(revenue: float) -> str:
    """Assign org to revenue band based on total revenue.
    Returns None if revenue data is missing (archetype-only context)."""
    if revenue is None or revenue == 0:
        return None
    if revenue < 150000:
        return 'micro'
    elif revenue < 700000:
        return 'professional'
    else:
        return 'established'

def get_peer_group_key(archetype: str, band: str) -> tuple:
    """Get the benchmark key for a given archetype + band."""
    return (archetype, band)

def extract_metrics(org: dict) -> dict:
    """Extract key financial metrics from org record."""
    try:
        revenue = float(org.get('total_revenue', 0)) or 0
        reserves_mo = float(org.get('months_of_reserve', 0)) or 0
        labor_pct = float(org.get('program_expense_pct', 0)) or 0

        return {
            'revenue': revenue,
            'reserves_mo': max(0, reserves_mo),  # Cap at 0
            'labor_pct': max(0, min(labor_pct, 100)),  # 0-100
        }
    except (ValueError, TypeError):
        return None

def score_org(org: dict, archetype: str, band: str) -> dict:
    """
    Score org within its peer group.
    Returns: {
        'archetype': str,
        'band': str,
        'peer_group_label': str,
        'peer_org_count': int,
        'reserves_mo': float,
        'reserves_p50': float,
        'reserves_percentile': float,
        'labor_pct': float,
        'labor_p50': float,
        'health_signal': str (CAUTION, STABLE, HEALTHY),
    }
    """
    key = get_peer_group_key(archetype, band)
    if key not in BENCHMARKS:
        return None

    bench = BENCHMARKS[key]
    metrics = extract_metrics(org)
    if not metrics:
        return None

    reserves_mo = metrics['reserves_mo']

    # Percentile rank for reserves (within peer group)
    p25 = bench['reserves_p25']
    p50 = bench['reserves_p50']
    p75 = bench['reserves_p75']

    if reserves_mo <= p25:
        reserves_percentile = 25
    elif reserves_mo <= p50:
        reserves_percentile = 25 + (reserves_mo - p25) / (p50 - p25) * 25
    elif reserves_mo <= p75:
        reserves_percentile = 50 + (reserves_mo - p50) / (p75 - p50) * 25
    else:
        reserves_percentile = min(75 + (reserves_mo - p75) / (p75) * 25, 99)

    # Health signal: compare to peer median reserves
    if reserves_mo < p25:
        health_signal = 'MAY_NEED_SUPPORT'
    elif reserves_mo < p50:
        health_signal = 'STABLE'
    else:
        health_signal = 'HEALTHY'

    return {
        'archetype': ARCHETYPES[archetype]['name'],
        'archetype_key': archetype,
        'band': REVENUE_BANDS[band]['label'],
        'band_key': band,
        'peer_group_label': bench['label'],
        'peer_org_count': bench['org_count'],
        'reserves_mo': round(reserves_mo, 1),
        'reserves_p50': bench['reserves_p50'],
        'reserves_p25': bench['reserves_p25'],
        'reserves_p75': bench['reserves_p75'],
        'reserves_percentile': round(reserves_percentile, 0),
        'labor_pct': round(metrics['labor_pct'], 1),
        'labor_p50': bench['labor_pct_p50'],
        'health_signal': health_signal,
        'healthy_rate_peer': bench['healthy_rate'],
    }

def generate_donor_copy(org: dict, score: dict) -> str:
    """
    Generate donor-facing copy for the org based on its peer group context.
    Returns: A paragraph explaining the org's financial position.
    """
    if not score:
        return None

    name = org.get('name', 'This organization')
    archetype = score['archetype']
    band = score['band']
    reserves = score['reserves_mo']
    p50 = score['reserves_p50']
    health = score['health_signal']
    peer_count = score['peer_org_count']

    # Build the copy
    lines = [
        f"{name} is a {archetype} nonprofit with a budget in the {band} range.",
        f"",
        f"Looking at its financial stability: Most organizations like this one keep about {int(p50)} months of operating costs in reserve. This one has {reserves:.1f} months."
    ]

    if health == 'HEALTHY':
        lines.append(f"That's above the typical level for similar organizations, suggesting solid financial stability.")
    elif health == 'STABLE':
        lines.append(f"That's close to the typical level for similar organizations, showing steady planning.")
    else:  # MAY_NEED_SUPPORT
        lines.append(f"That's below the typical level for similar organizations. Your support could strengthen their financial resilience.")

    lines.append(f"")
    lines.append(f"This comparison is based on public IRS 990 data from {peer_count:,} similar organizations.")

    return ' '.join(lines)

def main():
    parser = argparse.ArgumentParser(description='MERIT Score Engine v5.0')
    parser.add_argument('--output', default='scores_v5_0.json', help='Output JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no write)')
    parser.add_argument('--limit', type=int, help='Limit number of orgs to process')
    args = parser.parse_args()

    log(f"Starting MERIT Score Engine v5.0")
    log(f"Loading registry from {DB}")

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Load all orgs - select specific columns in order
    query = """
        SELECT
            EIN,
            NTEE1,
            total_revenue,
            organization_name,
            months_of_reserve,
            program_expense_pct
        FROM registry_enriched
        WHERE deductibility = '1'
        ORDER BY ein
    """
    if args.limit:
        query = query.replace("ORDER BY ein", f"ORDER BY ein LIMIT {args.limit}")

    c.execute(query)
    orgs = c.fetchall()
    conn.close()

    log(f"Loaded {len(orgs)} orgs for scoring")

    scores = []
    failures = []
    start = time.time()

    for i, org in enumerate(orgs):
        if i % 10000 == 0:
            elapsed = time.time() - start
            rate = i / elapsed if elapsed > 0 else 0
            log(f"Scoring org {i:,}/{len(orgs):,} (~{rate:.0f} orgs/sec)")

        # Extract from SQLite row
        ein = org[0]  # Column 0 is EIN
        ntee1 = org[1] or 'Z'  # Column 1 is NTEE1
        revenue_val = org[2]  # Column 2 is total_revenue
        revenue = float(revenue_val) if revenue_val else None  # Keep None for missing data

        # Build org dict for metrics extraction
        org_dict = {
            'ein': ein,
            'name': org[3] if len(org) > 3 else None,  # organization_name
            'total_revenue': revenue,
            'months_of_reserve': org[4] if len(org) > 4 else None,
            'program_expense_pct': org[5] if len(org) > 5 else None,
        }

        # Assign archetype and band
        archetype = get_archetype_by_ntee(ntee1)
        band = get_revenue_band(revenue)

        # Score: if band is None (missing revenue), store archetype-only context
        score = score_org(org_dict, archetype, band) if band else {
            'archetype': ARCHETYPES[archetype]['name'],
            'archetype_key': archetype,
            'band': None,
            'band_key': None,
            'peer_group_label': None,
            'peer_org_count': None,
            'reserves_mo': None,
            'reserves_percentile': None,
            'labor_pct': None,
            'health_signal': None,
        }

        if not score:
            failures.append((org_dict.get('ein'), 'Failed to extract metrics'))
            continue

        # Add org info
        score['ein'] = org_dict.get('ein')
        score['name'] = org_dict.get('name')
        score['ntee1'] = ntee1
        score['revenue'] = revenue

        # Add donor copy (only if band exists)
        if band:
            score['donor_copy'] = generate_donor_copy(org_dict, score)
        else:
            # Archetype-only context (no peer group benchmarks)
            score['donor_copy'] = None

        scores.append(score)

    elapsed = time.time() - start
    log(f"Scored {len(scores):,} orgs in {elapsed:.0f}s (~{len(scores)/elapsed:.0f} orgs/sec)")
    log(f"Failures: {len(failures)}")

    if failures:
        log(f"Sample failures: {failures[:5]}")

    # Write output
    if not args.dry_run:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump({
                'version': SCORER_VERSION,
                'timestamp': datetime.now().isoformat(),
                'total_scored': len(scores),
                'total_failed': len(failures),
                'scores': scores,
            }, f, indent=2)
        log(f"Wrote {len(scores)} scores to {output_path}")
    else:
        log(f"DRY RUN: Would write {len(scores)} scores")

    # Summary stats
    by_group = defaultdict(list)
    archetype_only = []
    for score in scores:
        if score['band_key'] is None:
            archetype_only.append(score)
        else:
            key = (score['archetype_key'], score['band_key'])
            by_group[key].append(score)

    log(f"\n=== Scoring Summary ===")

    # Peer groups (with band)
    for key in sorted(by_group.keys()):
        group = by_group[key]
        healthies = sum(1 for s in group if s['health_signal'] == 'HEALTHY')
        stables = sum(1 for s in group if s['health_signal'] == 'STABLE')
        cautions = sum(1 for s in group if s['health_signal'] == 'CAUTION')
        label = BENCHMARKS[key]['label']
        log(f"{label}: {len(group):6d} orgs | HEALTHY {healthies:5d} | STABLE {stables:5d} | CAUTION {cautions:5d}")

    # Archetype-only (missing revenue data)
    if archetype_only:
        log(f"\nArchetype-Only (no revenue data): {len(archetype_only):6d} orgs")
        by_archetype = defaultdict(int)
        for score in archetype_only:
            by_archetype[score['archetype']] += 1
        for arch in sorted(by_archetype.keys()):
            log(f"  {arch}: {by_archetype[arch]:6d} orgs")

if __name__ == '__main__':
    main()
