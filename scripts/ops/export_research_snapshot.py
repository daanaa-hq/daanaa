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

from scripts.registry_filters import DEDUCTIBLE_FILTER, canonical_active_count

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
    # pct_beacon/torch/candle/spark dropped from the export 2026-08-09 (lamp-tier
    # retirement, continued -- research_category_summary itself still computes
    # them, but nothing should read tier percentages out of this snapshot).
    # Not SELECTed below on purpose: if the source table's schema ever drops
    # these columns for real, that's a non-event for this file now.
    rows = db.execute("""
        SELECT ntee1, ntee_label, count, pct_of_total, avg_revenue, avg_peer_percentile
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
    """Program expense percentiles by V6 context tier.

    Was v5 archetype-grouped (Donation-Funded/Fee-for-Service/Endowment-Funded), but
    that query matched against the wrong label strings and had been silently
    returning zero rows -- the chart on the Research page was empty. Rebuilt on
    scoring_tier, the same V6 grouping the rest of this file now uses, so it can't
    drift out of sync with the tier definitions again.
    """
    data = []
    for tier in V6_TIER_ORDER:
        vals = [
            row['p'] for row in db.execute("""
                SELECT CAST(program_expense_pct AS FLOAT) as p
                FROM registry_enriched
                WHERE scoring_tier = ?
                  AND program_expense_pct IS NOT NULL
                  AND subsection = '3' AND deductibility = '1'
                  AND COALESCE(irs_revoked, 0) != 1
                  AND COALESCE(org_status, '') != 'revoked'
                ORDER BY program_expense_pct
            """, [tier]).fetchall()
        ]
        if not vals:
            continue
        median = _percentile(vals, 0.5)
        p25 = _percentile(vals, 0.25)
        p75 = _percentile(vals, 0.75)
        data.append({
            'tier': tier,
            'tier_name': V6_TIER_INFO[tier]['name'],
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


V6_TIER_ORDER = ['1_Full_Context', '2_Regional_Context', '3_Broad_Category', '4_Archetype_Only']

# Wording matches scripts/precompute_content.py's context_levels exactly, so the
# Methodology page and the Research page never disagree on what a tier means.
#
# Descriptions verified 2026-08-08 against scripts/daanaa_scorer.py (v6), the
# script that actually writes scoring_tier/tier_label/peer_group_size/confidence.
# Tier 2 is NOT "a broader regional peer group" -- the scorer drops region
# entirely at tier 2 (NTEE2 x revenue band, national). That's the opposite of
# what "Regional Context" implies, so the description below says what the tier
# actually compares, not what its name suggests. The tier *names* are the
# scorer's own vocabulary (registry_enriched.scoring_tier values) and aren't
# renamed here to avoid drifting from the DB.
V6_TIER_INFO = {
    '1_Full_Context': {
        'name': 'Full Context',
        'description': 'Compared with organizations of similar type, size, and region.',
    },
    '2_Regional_Context': {
        'name': 'Regional Context',
        'description': 'The regional group was too small, so this compares organizations of similar type and size nationally instead.',
    },
    '3_Broad_Category': {
        'name': 'Broad Category',
        'description': 'Compared across a wider category when a closer peer group was too small to be meaningful.',
    },
    '4_Archetype_Only': {
        'name': 'Archetype Only',
        'description': 'We can describe the kind of work, but the public record does not yet support a peer comparison.',
    },
}


def build_v6(db):
    """V6 financial-context taxonomy, computed from the scoring_tier column already
    in registry_enriched (written by scripts/daanaa_scorer.py). Peer group =
    NTEE category + revenue band + region, narrowing or widening one dimension at
    a time (drop region, then drop band) until the group holds enough peers with
    reserves data -- a reference-class approach (find the narrowest comparable set
    with enough data, widen it when there isn't enough) rather than a single
    universal yardstick.

    IMPORTANT: V6 assigns a comparison TIER (how specific the peer group is), not
    a percentile score. There is no per-org percentile in this pipeline -- do not
    read `peer_percentile` here, that column is written by the older, retired v4
    lamp-tier scorer under a different (NTEE1 x band, no region) grouping and has
    nothing to do with the V6 tier shown alongside it. Likewise `peer_group_size`
    (no suffix, from daanaa_scorer.py) is the real per-tier group size;
    `peer_group_size_v6`/`confidence_v6`/`scoring_tier_v6_inference` are a separate,
    largely disjoint pipeline (row-level check 2026-08-08: scoring_tier and
    scoring_tier_v6_inference agree on 58 of 2,056,834 rows) and must not be used
    here or anywhere donor-facing until that's reconciled -- see TODOS.md.

    There is no V6 health-signal bucketing (no HEALTHY/STABLE/CAUTION). V6 states
    how reliable the comparison is, not a verdict on financial health -- that
    distinction is deliberate (Stewardship P4: small orgs treated fairly; P5: no
    shame framing). Only the deductible, non-revoked set is counted.
    """
    rows = db.execute(
        """SELECT scoring_tier,
                  COUNT(*)                              AS count,
                  ROUND(AVG(peer_group_size), 0)        AS avg_peer_group_size,
                  ROUND(AVG(program_expense_pct), 1)    AS avg_program_pct,
                  ROUND(AVG(CASE WHEN months_of_reserve BETWEEN -120 AND 120
                                 THEN months_of_reserve END), 1) AS avg_months_reserve
             FROM registry_enriched
            WHERE subsection = '3' AND deductibility = '1'
              AND COALESCE(irs_revoked, 0) != 1
              AND COALESCE(org_status, '') != 'revoked'
            GROUP BY scoring_tier"""
    ).fetchall()
    by_tier = {r['scoring_tier']: dict(r) for r in rows}
    total = sum(r['count'] for r in by_tier.values()) or 1
    unscored = by_tier.get(None, {}).get('count', 0)

    tiers = []
    for key in V6_TIER_ORDER:
        r = by_tier.get(key)
        count = r['count'] if r else 0
        # Tier 4 has no peer group by definition (that's what "Archetype Only"
        # means) -- peer_group_size is NULL for those rows in the source data,
        # so avg_peer_group_size naturally comes back None for this tier.
        tiers.append({
            'key': key,
            'name': V6_TIER_INFO[key]['name'],
            'description': V6_TIER_INFO[key]['description'],
            'has_peer_comparison': key != '4_Archetype_Only',
            'count': count,
            'pct': round(count * 100 / total, 1),
            'avg_peer_group_size': r['avg_peer_group_size'] if r else None,
            'avg_program_pct': r['avg_program_pct'] if r else None,
            'avg_months_reserve': r['avg_months_reserve'] if r else None,
        })

    return {
        'total_active': total,
        'total_placed': total - unscored,
        'unscored_count': unscored,
        'placement_coverage_pct': round((total - unscored) * 100 / total, 1),
        'tiers': tiers,
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
            'v6': build_v6(db),
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
    v6 = snapshot['v6']
    print(f"   v6:            {v6['total_placed']:,} placed in a tier "
          f"({v6['placement_coverage_pct']}% of active orgs), {len(v6['tiers'])} context tiers")
    mc = snapshot['monthly_changes']
    batch_months = [m['month'] for m in mc if m['is_batch_revocation']]
    print(f"   monthly:       {len(mc)} months, batch-revocation months: {batch_months or 'none'}")


if __name__ == '__main__':
    main()
