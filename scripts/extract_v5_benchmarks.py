#!/usr/bin/env python3
"""
Extract actual benchmarks from registry data for v5.0 scorer.

This computes P25, P50, P75 for reserves and labor across all 15 groups,
plus health rates and org counts.

Replaces hard-coded benchmarks with data-driven values.
"""

import sqlite3
import json
from pathlib import Path
from collections import defaultdict
import statistics

DB = Path.home() / "meritgiving/data/merit_registry.db"

NTEE_TO_ARCHETYPE = {
    'D': 'donation_funded', 'F': 'donation_funded', 'G': 'donation_funded',
    'H': 'donation_funded', 'O': 'donation_funded', 'P': 'donation_funded',
    'Q': 'donation_funded', 'R': 'donation_funded', 'V': 'donation_funded',
    'W': 'donation_funded', 'X': 'donation_funded', 'I': 'donation_funded',
    'Z': 'donation_funded',
    'Y': 'endowment',
    'J': 'fee_for_service',
    'A': 'donation_funded', 'K': 'donation_funded', 'M': 'donation_funded',
    'T': 'donation_funded',
    'B': 'donation_funded', 'C': 'donation_funded', 'E': 'fee_for_service',
    'L': 'donation_funded', 'N': 'fee_for_service', 'S': 'donation_funded',
    'U': 'endowment',
}

def get_archetype(ntee1):
    return NTEE_TO_ARCHETYPE.get((ntee1 or 'Z').upper(), 'donation_funded')

def get_band(revenue):
    if revenue < 150000:
        return 'micro'
    elif revenue < 700000:
        return 'professional'
    else:
        return 'established'

def extract_metrics(org):
    try:
        revenue = float(org[1]) or 0
        reserves_mo = float(org[2]) or 0
        labor_pct = float(org[3]) or 0
        return {
            'revenue': max(0, revenue),
            'reserves_mo': max(0, min(reserves_mo, 1000)),  # cap at 1000
            'labor_pct': max(0, min(labor_pct, 100)),
        }
    except (ValueError, TypeError):
        return None

def main():
    print("Extracting v5.0 benchmarks from registry...")

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Load all orgs: (ein, ntee1, revenue, reserves_mo, labor_pct)
    c.execute("""
        SELECT ein, ntee1, total_revenue, months_of_reserve, program_expense_pct
        FROM registry_enriched
        WHERE deductibility = '1'
    """)

    by_group = defaultdict(list)
    total_loaded = 0
    total_valid = 0

    for row in c.fetchall():
        total_loaded += 1

        ntee1 = row[1] or 'Z'
        revenue = float(row[2]) if row[2] else 0

        archetype = get_archetype(ntee1)
        band = get_band(revenue)
        key = (archetype, band)

        metrics = extract_metrics(row)
        if metrics:
            by_group[key].append(metrics)
            total_valid += 1

    conn.close()

    print(f"Loaded {total_loaded:,} orgs, {total_valid:,} with valid metrics")

    # Compute benchmarks
    benchmarks = {}

    for key in sorted(by_group.keys()):
        group = by_group[key]
        if not group:
            continue

        archetype, band = key

        # Extract reserves and labor
        reserves = sorted([m['reserves_mo'] for m in group if m['reserves_mo'] is not None])
        labor = sorted([m['labor_pct'] for m in group if m['labor_pct'] is not None])

        # Compute percentiles
        def percentile(data, p):
            if not data:
                return 0
            idx = int(len(data) * p / 100.0)
            return data[min(idx, len(data)-1)]

        # Health: orgs with reserves >= 12 months
        healthy_count = sum(1 for r in reserves if r >= 12)
        healthy_pct = healthy_count / len(reserves) * 100 if reserves else 0

        bench = {
            'label': f'{archetype.replace("_", " ").title()}, {band.title()}',
            'org_count': len(group),
            'reserves_p25': round(percentile(reserves, 25), 1),
            'reserves_p50': round(percentile(reserves, 50), 1),
            'reserves_p75': round(percentile(reserves, 75), 1),
            'labor_pct_p25': round(percentile(labor, 25), 1),
            'labor_pct_p50': round(percentile(labor, 50), 1),
            'labor_pct_p75': round(percentile(labor, 75), 1),
            'healthy_rate': round(healthy_pct, 1),
        }

        benchmarks[f"{archetype}|{band}"] = bench

        print(f"\n{bench['label']}:")
        print(f"  Orgs: {bench['org_count']:,}")
        print(f"  Reserves: P25={bench['reserves_p25']}, P50={bench['reserves_p50']}, P75={bench['reserves_p75']}")
        print(f"  Labor%: P25={bench['labor_pct_p25']}, P50={bench['labor_pct_p50']}, P75={bench['labor_pct_p75']}")
        print(f"  Healthy: {bench['healthy_rate']}%")

    # Save to JSON
    with open('/tmp/v5_benchmarks_extracted.json', 'w') as f:
        json.dump(benchmarks, f, indent=2)

    print(f"\n✓ Benchmarks saved to /tmp/v5_benchmarks_extracted.json")
    print(f"\nSummary:")
    print(f"  Total groups: {len(benchmarks)}")
    print(f"  Min group size: {min(b['org_count'] for b in benchmarks.values()):,}")
    print(f"  Max group size: {max(b['org_count'] for b in benchmarks.values()):,}")

if __name__ == '__main__':
    main()
