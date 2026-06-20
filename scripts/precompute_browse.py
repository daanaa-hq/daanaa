#!/usr/bin/env python3
"""
Pre-compute browse results for all category/state combinations.
Runs on home server weekly; outputs ~100MB gzipped.
"""

import sqlite3
import json
import gzip
import os
import sys
from pathlib import Path
from datetime import datetime

# Pull in shared v5 context builder (same function used by precompute_orgs.py)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from enrich_api_responses import build_v5_context
except ImportError:
    build_v5_context = None

DB_PATH = os.environ.get("MERIT_DB_PATH", "data/merit_registry.db")
OUTPUT_DIR = os.path.join(os.environ.get("PRECOMPUTE_OUT", "precompute_output"), "browse")
PAGE_SIZE = 25

# NTEE categories from frontend
CATEGORIES = [
    ('A', 'Arts, Culture & Humanities'),
    ('B', 'Educational Institutions & Related Activities'),
    ('C', 'Environmental Quality, Protection & Beautification'),
    ('D', 'Animal-Related'),
    ('E', 'Health - General and Rehabilitative'),
    ('F', 'Mental Health, Crisis Intervention'),
    ('G', 'Voluntary Health Associations & Medical Research Institutes'),
    ('H', 'Diseases, Disorders, Medical Disciplines'),
    ('I', 'Medical Specialty Hospitals, Treatment Centers'),
    ('J', 'Nursing, Custodial Care, Hospices'),
    ('K', 'Mental Health & Crisis Intervention'),
    ('L', 'Public Safety, Disaster Preparedness & Relief'),
    ('M', 'Recreation & Sports'),
    ('N', 'Youth Development'),
    ('O', 'Human Services - Multipurpose & Other'),
    ('P', 'Human Services - Multipurpose'),
    ('Q', 'International, Foreign Affairs & Related Organizations'),
    ('R', 'Civil Rights, Social Action & Advocacy'),
    ('S', 'Community Improvement & Capacity Building'),
    ('T', 'Philanthropy, Voluntarism & Grantmaking Foundations'),
    ('U', 'Science and Technology Research Institutes, Services'),
    ('V', 'Social Sciences Research Institutes, Services'),
    ('W', 'Public & Societal Benefit'),
    ('X', 'Religion-Related, Spiritual Development'),
    ('Y', 'Mutual & Membership Benefit Organizations, Other'),
    ('Z', 'Unknown'),
]

# All US states + territories + military codes
US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC', 'PR', 'AS', 'GU', 'MP', 'VI', 'AA', 'AE', 'AP'
]


def org_to_dict(row):
    """Convert database row to API response dict."""
    return {
        'EIN': row[0],
        'organization_name': row[1],
        'NTEE1': row[2],
        'NTEECC': row[3],
        'CITY': row[4],
        'STATE': row[5],
        'total_revenue': row[6],
        'total_revenue_formatted': f"${row[6]:,.0f}" if row[6] else None,
        'ntee1_percentile': row[7],
        'ntee1_total_orgs': row[8],
        'source': row[9],
        'revenue_band': row[10],
        'peer_percentile': row[11],
        'peer_rank': row[12],
        'peer_total': row[13],
        'peer_group': row[14],
        'latest_tax_year': row[15],
        'data_source': row[16],
        'updated_at': row[17],
        'merit_tier': row[18],
        'merit_score': row[19],
        'merit_band': row[20],
        'financial_health': row[21],
        'months_of_reserve': row[22],
        'net_assets': row[23],
        'total_expenses': row[24],
        'employee_count': row[25],
        'program_expense_pct': row[26],
        'mission': row[27],
        'mission_source': row[28],
        'website': row[29],
        'website_status': row[30],
        'cause_tags': json.loads(row[31]) if row[31] else None,
        'is_hidden_gem': bool(row[40]) if row[40] is not None else False,
        # donate_* fields intentionally not emitted (2026-06-10): no donation
        # links on public surfaces — data stays internal for the claim flow.
        'v5_context': _build_v5(row),
    }


def _build_v5(row):
    """Build v5_context dict from v5 columns appended to the SELECT (row[32..39])."""
    if not build_v5_context or row[32] is None:
        return None
    try:
        return build_v5_context(
            row[32], row[33], row[34], row[35],   # archetype key/label, band key/label
            row[36], row[37], row[38], row[39],   # score, health_signal, peer_group, peer_count
            row[22],                               # months_of_reserve
        )
    except Exception:
        return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    total_files = 0
    total_orgs = 0

    print(f"[{timestamp}] Pre-computing browse results...")
    print(f"Categories: {len(CATEGORIES)}, States: {len(US_STATES)}")

    for cat_code, cat_name in CATEGORIES:
        cat_dir = Path(OUTPUT_DIR) / cat_code
        cat_dir.mkdir(parents=True, exist_ok=True)

        for state in US_STATES:
            # Get all orgs for this category/state combination
            cursor.execute("""
                SELECT
                    EIN, organization_name, NTEE1, NTEECC, CITY, STATE,
                    total_revenue, ntee1_percentile, ntee1_total_orgs, source,
                    revenue_band, peer_percentile, peer_rank, peer_total, peer_group,
                    latest_tax_year, data_source, updated_at, merit_tier, merit_score,
                    merit_band, financial_health, months_of_reserve, net_assets,
                    total_expenses, employee_count, program_expense_pct,
                    mission, mission_source, website, website_status, cause_tags,
                    merit_archetype_v5, merit_archetype_v5_label, merit_band_v5,
                    merit_band_v5_label, merit_score_v5, merit_health_signal_v5,
                    merit_peer_group_v5, merit_peer_count_v5, is_hidden_gem
                FROM registry_enriched
                -- Only surface orgs where donating is currently tax-deductible:
                -- deductible 501(c)(3) AND not IRS-revoked. Fail closed on revocation.
                WHERE NTEE1 = ? AND STATE = ? AND deductibility = 1 AND org_status = 'active'
                ORDER BY
                    CASE WHEN peer_percentile IS NOT NULL THEN peer_percentile ELSE ntee1_percentile END DESC NULLS LAST,
                    total_revenue DESC NULLS LAST,
                    organization_name ASC
            """, (cat_code, state))

            all_orgs = [org_to_dict(row) for row in cursor.fetchall()]

            if not all_orgs:
                continue

            # Paginate
            num_pages = (len(all_orgs) + PAGE_SIZE - 1) // PAGE_SIZE

            for page_num in range(1, num_pages + 1):
                start_idx = (page_num - 1) * PAGE_SIZE
                end_idx = min(start_idx + PAGE_SIZE, len(all_orgs))
                page_orgs = all_orgs[start_idx:end_idx]

                response = {
                    'organizations': page_orgs,
                    'total': len(all_orgs),
                    'page': page_num,
                    'per_page': PAGE_SIZE,
                    'pages': num_pages,
                }

                # Save as .json.gz
                filename = f"{state}_{page_num}.json.gz"
                filepath = cat_dir / filename

                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    json.dump(response, f, separators=(',', ':'))

                total_files += 1
                total_orgs += len(page_orgs)

        print(f"  {cat_code}: {state} processed")

    # ── ALL-state pass: aggregate all states per category for no-state browsing ──
    print(f"\n[{datetime.now().isoformat()}] Generating ALL-state browse files...")
    all_state_files = 0
    all_state_orgs = 0

    for cat_code, cat_name in CATEGORIES:
        cat_dir = Path(OUTPUT_DIR) / cat_code
        cat_dir.mkdir(parents=True, exist_ok=True)

        cursor.execute("""
            SELECT
                EIN, organization_name, NTEE1, NTEECC, CITY, STATE,
                total_revenue, ntee1_percentile, ntee1_total_orgs, source,
                revenue_band, peer_percentile, peer_rank, peer_total, peer_group,
                latest_tax_year, data_source, updated_at, merit_tier, merit_score,
                merit_band, financial_health, months_of_reserve, net_assets,
                total_expenses, employee_count, program_expense_pct,
                mission, mission_source, website, website_status, cause_tags,
                merit_archetype_v5, merit_archetype_v5_label, merit_band_v5,
                merit_band_v5_label, merit_score_v5, merit_health_signal_v5,
                merit_peer_group_v5, merit_peer_count_v5, is_hidden_gem
            FROM registry_enriched
            -- Only surface orgs where donating is currently tax-deductible (see above).
            WHERE NTEE1 = ? AND deductibility = 1 AND org_status = 'active'
            ORDER BY
                CASE WHEN peer_percentile IS NOT NULL THEN peer_percentile ELSE ntee1_percentile END DESC NULLS LAST,
                total_revenue DESC NULLS LAST,
                organization_name ASC
        """, (cat_code,))

        all_orgs = [org_to_dict(row) for row in cursor.fetchall()]

        if not all_orgs:
            continue

        num_pages = (len(all_orgs) + PAGE_SIZE - 1) // PAGE_SIZE

        for page_num in range(1, num_pages + 1):
            start_idx = (page_num - 1) * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, len(all_orgs))
            page_orgs = all_orgs[start_idx:end_idx]

            response = {
                'organizations': page_orgs,
                'total': len(all_orgs),
                'page': page_num,
                'per_page': PAGE_SIZE,
                'pages': num_pages,
            }

            filename = f"ALL_{page_num}.json.gz"
            filepath = cat_dir / filename

            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(response, f, separators=(',', ':'))

            all_state_files += 1
            all_state_orgs += len(page_orgs)

        print(f"  {cat_code}: {len(all_orgs)} orgs → {num_pages} ALL-state pages")

    conn.close()

    # Summary
    print(f"\n[{datetime.now().isoformat()}] Browse pre-compute complete!")
    print(f"  State files: {total_files} ({total_orgs} orgs)")
    print(f"  ALL-state files: {all_state_files} ({all_state_orgs} orgs)")
    print(f"  Output: {OUTPUT_DIR}")

    # Estimate size
    total_size = sum(f.stat().st_size for f in Path(OUTPUT_DIR).rglob('*') if f.is_file())
    print(f"  Disk usage: {total_size / 1024 / 1024:.1f} MB")


if __name__ == '__main__':
    main()
