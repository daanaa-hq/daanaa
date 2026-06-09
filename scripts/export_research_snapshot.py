#!/usr/bin/env python3
"""
Export the research dashboard data to a single static JSON snapshot.

The public research page (daanaa.org/research) is served as a flat static file
with no live server connection. This script regenerates the data points the page
reads. Run it whenever the underlying research summary tables change (e.g. after
the nightly pipeline / research_summary_generator.py), then rebuild + redeploy
the frontend.

Output: frontend/public/research-snapshot.json  (a few dozen KB)

The query logic here mirrors the /api/research/summary/* endpoints in
daanaa_api.py exactly, so the static page shows identical numbers to the
local API-backed version.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.environ.get("MERIT_DB_PATH", "/home/akbar/meritgiving/data/merit_registry.db")
OUT_PATH = "/home/akbar/meritgiving/frontend/public/research-snapshot.json"

VALID_MODELS = [
    'Activity_Programming',
    'Direct_Delivery',
    'Community_Human_Services',
    'Clinical_Reimbursement',
    'Emergency_Logistics',
    'Cause_Advocacy_Research',
    'Intermediary_Public_Benefit',
    'Faith_Community',
    'Membership_Mutual_Benefit',
]

# Canonical display order, mirrors the CASE ordering in daanaa_api.py
MODEL_ORDER = {m: i for i, m in enumerate(VALID_MODELS)}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _percentile(sorted_vals, q):
    """Linear-interpolation percentile (q in 0..1) on a pre-sorted list."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


def build_metadata(db):
    total_orgs = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    period = db.execute(
        "SELECT MAX(period) FROM research_operating_model_summary"
    ).fetchone()[0]
    return {
        'total_organizations': total_orgs,
        'data_period': period,
        'version': 'v1.0',
        'generated_at': datetime.now().isoformat(),
        'disclaimer': 'This dashboard reflects public data available to Daanaa at '
                      'the time of processing. It does not measure impact, quality, '
                      'worth, trust, or endorsement.',
    }


def build_revenue_bands(db):
    placeholders = ','.join(['?'] * len(VALID_MODELS))
    rows = db.execute(f"""
        SELECT operating_model, revenue_band_number, count, pct_of_total,
               avg_peer_percentile, avg_months_reserve
        FROM research_revenue_band_summary
        WHERE period = (SELECT MAX(period) FROM research_revenue_band_summary)
          AND operating_model IN ({placeholders})
        ORDER BY operating_model, revenue_band_number
    """, VALID_MODELS).fetchall()

    data = [
        {
            'operating_model': r['operating_model'],
            'revenue_band_number': r['revenue_band_number'],
            'count': r['count'],
            'pct_of_total': round(r['pct_of_total'], 2),
            'avg_peer_percentile': r['avg_peer_percentile'],
            'avg_months_reserve': r['avg_months_reserve'],
        }
        for r in rows
    ]
    # Apply canonical model order (mirrors the API CASE ordering)
    data.sort(key=lambda d: (MODEL_ORDER[d['operating_model']], d['revenue_band_number']))
    return data


def build_categories(db):
    rows = db.execute("""
        SELECT ntee1, ntee_label, count, pct_of_total, avg_revenue, avg_peer_percentile,
               pct_beacon, pct_torch, pct_candle, pct_spark
        FROM research_category_summary
        WHERE period = (SELECT MAX(period) FROM research_category_summary)
        ORDER BY count DESC
    """).fetchall()
    return [
        {
            'ntee1': r['ntee1'],
            'ntee_label': r['ntee_label'],
            'count': r['count'],
            'pct_of_total': round(r['pct_of_total'], 1),
            'avg_revenue': r['avg_revenue'],
            'avg_peer_percentile': r['avg_peer_percentile'],
            'pct_beacon': r['pct_beacon'],
            'pct_torch': r['pct_torch'],
            'pct_candle': r['pct_candle'],
            'pct_spark': r['pct_spark'],
        }
        for r in rows
    ]


def build_states(db):
    rows = db.execute("""
        SELECT state, count, pct_of_total, avg_revenue, avg_peer_percentile
        FROM research_state_summary
        WHERE period = (SELECT MAX(period) FROM research_state_summary)
        ORDER BY count DESC LIMIT 10
    """).fetchall()
    return [
        {
            'state': r['state'],
            'count': r['count'],
            'pct': round(r['pct_of_total'], 1),
            'avg_revenue': r['avg_revenue'],
            'avg_peer_percentile': r['avg_peer_percentile'],
        }
        for r in rows
    ]


def build_spending(db):
    data = []
    for model in VALID_MODELS:
        vals = [
            row['p'] for row in db.execute("""
                SELECT CAST(r.program_expense_pct AS FLOAT) as p
                FROM v4_scores v
                LEFT JOIN registry_enriched r ON v.EIN = r.EIN
                WHERE v.operating_model = ?
                  AND r.program_expense_pct IS NOT NULL
                ORDER BY r.program_expense_pct
            """, [model]).fetchall()
        ]
        if not vals:
            continue
        median = _percentile(vals, 0.5)
        p25 = _percentile(vals, 0.25)
        p75 = _percentile(vals, 0.75)
        data.append({
            'operating_model': model,
            'count': len(vals),
            'median_program_spend': round(median, 1) if median is not None else None,
            'p25_program_spend': round(p25, 1) if p25 is not None else None,
            'p75_program_spend': round(p75, 1) if p75 is not None else None,
        })
    return data


def main():
    db = get_db()
    try:
        snapshot = {
            'metadata': build_metadata(db),
            'revenue_bands': build_revenue_bands(db),
            'categories': build_categories(db),
            'states': build_states(db),
            'spending': build_spending(db),
        }
    finally:
        db.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump(snapshot, f, separators=(',', ':'))

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"✅ Wrote research snapshot → {OUT_PATH} ({size_kb:.1f} KB)")
    print(f"   period: {snapshot['metadata']['data_period']}")
    print(f"   revenue_bands: {len(snapshot['revenue_bands'])} rows")
    print(f"   categories:    {len(snapshot['categories'])} rows")
    print(f"   states:        {len(snapshot['states'])} rows")
    print(f"   spending:      {len(snapshot['spending'])} rows")


if __name__ == '__main__':
    main()
