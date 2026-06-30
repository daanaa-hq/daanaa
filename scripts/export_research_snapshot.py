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
import csv
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from registry_filters import DEDUCTIBLE_FILTER, canonical_active_count

DB_PATH = os.environ.get("MERIT_DB_PATH", "/home/akbar/meritgiving/data/merit_registry.db")
BMF_PATH = os.environ.get("MERIT_BMF_PATH", "/home/akbar/meritgiving/data/bmf.csv")
OUT_PATH = "/home/akbar/meritgiving/frontend/public/research-snapshot.json"

# IRS BMF FOUNDATION codes → 501(c)(3) sub-classification.
# 02-04 are private foundations; 10-18 are public charities (509(a)(1)-(4)).
# Anything else (00, blank) has no determination on file.
PRIVATE_FOUNDATION_CODES = {'02', '03', '04'}
PUBLIC_CHARITY_CODES = {'10', '11', '12', '13', '14', '15', '16', '17', '18'}

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
    # Count the active, tax-deductible 501(c)(3) set — the same population the
    # rest of the dashboard analyses and the public site surface. Excludes the
    # ~193K auto-revoked orgs so the headline matches the analysis below it and
    # the homepage (mirrors daanaa_api.py _DEDUCTIBILITY_FILTER).
    total_orgs = canonical_active_count(db)
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


def build_entity_types(db):
    """Public charity vs private foundation composition of the deductible set.

    Within 501(c)(3), the IRS classifies every org as either a public charity
    (509(a)(1)-(4)) or a private foundation. The distinction is donor-relevant:
    public charities are publicly supported operating orgs; private foundations
    are endowment-funded grantmakers that fund others rather than take public
    donations. The classification lives in the IRS BMF FOUNDATION code, joined
    here to the same active, deductible 501(c)(3) set the rest of the page uses.
    """
    deductible = set(
        r[0] for r in db.execute(
            f"SELECT EIN FROM registry_enriched WHERE {DEDUCTIBLE_FILTER}"
        ).fetchall()
    )
    counts = {'public_charity': 0, 'private_foundation': 0, 'unclassified': 0}
    if os.path.exists(BMF_PATH):
        with open(BMF_PATH, newline='') as f:
            reader = csv.DictReader(f)
            ein_col = next((c for c in reader.fieldnames if c.upper() == 'EIN'), None)
            fnd_col = next((c for c in reader.fieldnames if c.upper() == 'FOUNDATION'), None)
            seen = set()
            for row in reader:
                ein = (row.get(ein_col) or '').strip().zfill(9)
                if ein not in deductible or ein in seen:
                    continue
                seen.add(ein)
                code = (row.get(fnd_col) or '').strip()
                if code in PRIVATE_FOUNDATION_CODES:
                    counts['private_foundation'] += 1
                elif code in PUBLIC_CHARITY_CODES:
                    counts['public_charity'] += 1
                else:
                    counts['unclassified'] += 1
            # Orgs in the deductible set with no BMF row at all are unclassified
            counts['unclassified'] += len(deductible - seen)
    total = sum(counts.values()) or 1
    return {
        'total': total,
        'public_charity': counts['public_charity'],
        'private_foundation': counts['private_foundation'],
        'unclassified': counts['unclassified'],
        'pct_public_charity': round(counts['public_charity'] * 100 / total, 1),
        'pct_private_foundation': round(counts['private_foundation'] * 100 / total, 1),
        'pct_unclassified': round(counts['unclassified'] * 100 / total, 1),
    }


V5_BAND_ORDER = {'Micro (<$150K)': 0, 'Professional ($150K–$700K)': 1, 'Established (>$700K)': 2}
V5_ARCHETYPE_ORDER = {
    'Donation-Funded Programs': 0,
    'Fee-for-Service Operators': 1,
    'Endowment-Funded Grantmakers': 2,
}


def build_v5(db):
    """v5 financial-context taxonomy, computed from the merit_*_v5 columns already
    in registry_enriched. Peer cell = archetype + revenue band; score = percentile
    rank within that cell; health signal = HEALTHY/STABLE/CAUTION. Only the
    deductible set is counted. Lamp tiers are a separate visibility layer (not v5).
    """
    rows = db.execute(
        """SELECT merit_archetype_v5_label AS archetype,
                  merit_band_v5_label      AS band,
                  COUNT(*)                 AS count,
                  ROUND(AVG(merit_score_v5), 1)        AS avg_score,
                  ROUND(AVG(program_expense_pct), 1)   AS avg_program_pct,
                  ROUND(AVG(CASE WHEN months_of_reserve BETWEEN -120 AND 120
                                 THEN months_of_reserve END), 1) AS avg_months_reserve,
                  SUM(CASE WHEN merit_health_signal_v5='HEALTHY' THEN 1 ELSE 0 END) AS healthy,
                  SUM(CASE WHEN merit_health_signal_v5='STABLE'  THEN 1 ELSE 0 END) AS stable,
                  SUM(CASE WHEN merit_health_signal_v5='CAUTION' THEN 1 ELSE 0 END) AS caution
             FROM registry_enriched
            WHERE subsection = '3' AND deductibility = '1'
              AND COALESCE(irs_revoked, 0) != 1
              AND COALESCE(org_status, '') != 'revoked'
              AND merit_archetype_v5_label IS NOT NULL
              AND merit_band_v5_label IS NOT NULL
            GROUP BY merit_archetype_v5_label, merit_band_v5_label"""
    ).fetchall()
    cells = [dict(r) for r in rows]
    cells.sort(key=lambda c: (V5_ARCHETYPE_ORDER.get(c['archetype'], 99),
                              V5_BAND_ORDER.get(c['band'], 99)))
    total = sum(c['count'] for c in cells) or 1
    # Per-archetype rollup
    arche = {}
    for c in cells:
        a = arche.setdefault(c['archetype'], {'archetype': c['archetype'], 'count': 0,
                                              'healthy': 0, 'stable': 0, 'caution': 0})
        a['count'] += c['count']
        a['healthy'] += c['healthy']; a['stable'] += c['stable']; a['caution'] += c['caution']
    archetypes = sorted(arche.values(), key=lambda a: V5_ARCHETYPE_ORDER.get(a['archetype'], 99))
    for a in archetypes:
        a['pct'] = round(a['count'] * 100 / total, 1)
    return {
        'total_scored': total,
        'cells': cells,
        'archetypes': archetypes,
        'health_totals': {
            'healthy': sum(c['healthy'] for c in cells),
            'stable': sum(c['stable'] for c in cells),
            'caution': sum(c['caution'] for c in cells),
        },
    }


def build_monthly_changes(db):
    """24 months of new registrations + revocations from IRS data.

    New registrations: ruling_date from registry_enriched (active deductible 501c3s only).
    Revocations: revocation_date from revoked_eins (format: DD-MON-YYYY).

    May spikes (~43-48K) are IRS annual batch auto-revocations — flagged in the data.
    """
    # Build 24-month window ending last complete month
    today = date.today()
    end = date(today.year, today.month, 1) - relativedelta(months=1)  # last complete month
    start = end - relativedelta(months=23)

    months = []
    cur = start
    while cur <= end:
        months.append(cur.strftime('%Y-%m'))
        cur += relativedelta(months=1)

    # New registrations by month (ruling_date is YYYYMM — 6 chars, e.g. "202407")
    # Convert to YYYY-MM for matching by inserting a hyphen after position 4.
    new_rows = db.execute("""
        SELECT substr(ruling_date,1,4) || '-' || substr(ruling_date,5,2) as yrmo,
               COUNT(*) as cnt
        FROM registry_enriched
        WHERE ruling_date IS NOT NULL AND ruling_date != ''
          AND length(ruling_date) >= 6
          AND subsection = '3' AND deductibility = '1'
          AND COALESCE(irs_revoked, 0) != 1
          AND COALESCE(org_status, '') != 'revoked'
        GROUP BY yrmo
    """).fetchall()
    new_by_month = {r[0]: r[1] for r in new_rows}

    # Revocations by month (format: DD-MON-YYYY → parse to YYYY-MM)
    rev_rows = db.execute(
        "SELECT revocation_date FROM revoked_eins WHERE revocation_date IS NOT NULL"
    ).fetchall()
    rev_by_month = {}
    for (d,) in rev_rows:
        try:
            dt = datetime.strptime(d.strip(), '%d-%b-%Y')
            key = dt.strftime('%Y-%m')
            rev_by_month[key] = rev_by_month.get(key, 0) + 1
        except Exception:
            pass

    # IRS does annual batch auto-revocations — flag months above 10K revocations
    BATCH_REVOCATION_THRESHOLD = 10000

    result = []
    for yrmo in months:
        new_count = new_by_month.get(yrmo, 0)
        rev_count = rev_by_month.get(yrmo, 0)
        is_batch = rev_count >= BATCH_REVOCATION_THRESHOLD
        result.append({
            'month': yrmo,
            'new_registrations': new_count,
            'revocations': rev_count,
            'net': new_count - rev_count,
            'is_batch_revocation': is_batch,
        })

    return result


def main():
    db = get_db()
    try:
        snapshot = {
            'metadata': build_metadata(db),
            'revenue_bands': build_revenue_bands(db),
            'categories': build_categories(db),
            'states': build_states(db),
            'spending': build_spending(db),
            'entity_types': build_entity_types(db),
            'v5': build_v5(db),
            'monthly_changes': build_monthly_changes(db),
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
    et = snapshot['entity_types']
    print(f"   entity_types:  {et['pct_public_charity']}% public charity, "
          f"{et['pct_private_foundation']}% private foundation, "
          f"{et['pct_unclassified']}% unclassified")
    v5 = snapshot['v5']
    print(f"   v5:            {v5['total_scored']:,} scored, "
          f"{len(v5['archetypes'])} archetypes, {len(v5['cells'])} cells")
    mc = snapshot['monthly_changes']
    batch_months = [m['month'] for m in mc if m['is_batch_revocation']]
    print(f"   monthly:       {len(mc)} months, batch-revocation months: {batch_months or 'none'}")


if __name__ == '__main__':
    main()
