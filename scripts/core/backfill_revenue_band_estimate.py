#!/usr/bin/env python3
"""
Backfill revenue_band_estimate for orgs with no reported revenue and no
full-form 990/990-EZ filing on record.

Board-reviewed 2026-08-17 (see docs/DECISIONS.md entry same date). Evidence:
- 1,341,640 orgs (65% of registry) have NULL/0 total_revenue.
- 1,337,364 of those (99.7%) have zero rows in
  irs_990_functional_expense_filings -- no full-form filing ever on record.
- IRS requires a full 990/990-EZ above the e-Postcard (990-N) gross-receipts
  threshold (currently $50,000); an org with tax-exempt status and no
  full-form filing history is consistent with -- but not directly confirmed
  as -- falling under that threshold. This is an inference from absence of
  a filing, not a verified IRS-reported figure. Stored as a clearly separate
  field per that distinction (see migrations/026_revenue_band_estimate.sql).
- Excludes BMF FILING_REQ_CD 03/07 (religious-organization exemption) --
  those orgs lack a 990 filing because of exemption category, not
  necessarily size, so inferring "under $50k" for them would be wrong.
- Does NOT touch total_revenue itself, and does NOT feed into scoring --
  confirmed before this was written that 99.0% of the affected population
  already has a scoring_tier without needing revenue at all.

Usage:
    python3 scripts/core/backfill_revenue_band_estimate.py [--dry-run]
"""
import argparse
import csv
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path('/home/akbar/meritgiving/data/merit_registry.db')
BMF_PATH = Path('/home/akbar/meritgiving/data/bmf.csv')

RELIGIOUS_EXEMPTION_CODES = {'03', '07'}
BAND_LABEL = 'under_50k'
BAND_REASON = 'no_full_form_990_filing_on_record'


def load_religious_exemption_eins():
    """EINs coded as religious-organization filing-exempt in the BMF --
    excluded because their lack of a 990 filing is about exemption
    category, not org size."""
    eins = set()
    with open(BMF_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('FILING_REQ_CD', '') in RELIGIOUS_EXEMPTION_CODES:
                ein = row.get('EIN', '').strip()
                if ein:
                    eins.add(ein)
    return eins


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true',
                         help='Report counts without writing changes')
    args = parser.parse_args()

    print("Loading religious-exemption EINs from BMF to exclude...")
    religious_eins = load_religious_exemption_eins()
    print(f"  {len(religious_eins)} EINs excluded (religious exemption, not size)")

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Candidates: no revenue reported, no full-form filing on record,
    # and currently unset (idempotent -- safe to re-run).
    c.execute("""
        SELECT r.EIN
        FROM registry_enriched r
        LEFT JOIN (SELECT DISTINCT EIN FROM irs_990_functional_expense_filings) f
          ON r.EIN = f.EIN
        WHERE (r.total_revenue IS NULL OR r.total_revenue = 0)
          AND f.EIN IS NULL
          AND r.revenue_band_estimate IS NULL
    """)
    candidates = [row[0] for row in c.fetchall()]
    print(f"Candidates before religious-exemption filter: {len(candidates)}")

    eligible = [ein for ein in candidates if ein not in religious_eins]
    excluded_count = len(candidates) - len(eligible)
    print(f"Excluded (religious exemption): {excluded_count}")
    print(f"Eligible for revenue_band_estimate: {len(eligible)}")

    if args.dry_run:
        print("\n--dry-run: no changes written.")
        conn.close()
        return

    batch_size = 1000
    updated = 0
    for i in range(0, len(eligible), batch_size):
        batch = eligible[i:i + batch_size]
        c.executemany(
            """UPDATE registry_enriched
               SET revenue_band_estimate = ?, revenue_band_estimate_reason = ?
               WHERE EIN = ?""",
            [(BAND_LABEL, BAND_REASON, ein) for ein in batch]
        )
        updated += len(batch)
        if updated % 50000 == 0:
            conn.commit()
            print(f"  ...{updated}/{len(eligible)} written")

    conn.commit()
    print(f"\nDone. {updated} orgs updated with revenue_band_estimate='{BAND_LABEL}'.")

    # Verify: confirm no accidental overlap with rows that DO have real revenue
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE revenue_band_estimate IS NOT NULL
          AND total_revenue IS NOT NULL AND total_revenue > 0
    """)
    bad_overlap = c.fetchone()[0]
    if bad_overlap > 0:
        print(f"WARNING: {bad_overlap} rows have both revenue_band_estimate AND "
              f"a real total_revenue > 0 -- this should be 0. Investigate before trusting the field.")
    else:
        print("Verified: no overlap with orgs that have real reported revenue.")

    conn.close()


if __name__ == '__main__':
    main()
