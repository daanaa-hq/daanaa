#!/usr/bin/env python3
"""
Add merit_tier column to registry_enriched and populate it.

Tier logic mirrors getTierFromOrg() in frontend/src/components/TrustBadge.tsx
so the filter and card display are always consistent.

Tiers (highest → lowest):
  Beacon  — top-quartile peer rank + mission + website + current 990 + positive
            revenue, AND (where 990 financials are known) a passing financial
            band. A known-weak band ('Mixed'/'Concerns') blocks Beacon.
  Lantern — any peer rank + mission + website + current 990 + positive revenue,
            AND (where known) a passing financial band — same gate as Beacon.
  Flame   — any peer rank + current 990 + positive revenue
  Ember   — has current 990 or any revenue on record
  Spark   — IRS BMF only, no financial detail

Guardrails added 2026-05-16 (credibility rework):
  * total_revenue must be > 0 for Beacon/Lantern/Flame — an org with zero or
    negative revenue can no longer hold a "trust" tier.
  * merit_band (from merit_scorer_v3_3, ~4.7k orgs) gates BOTH Beacon and
    Lantern where present: only the bottom band 'Concerns' (score <35) is
    blocked and demoted to Flame. 'Mixed' (mid-band) passes — since ~99% of
    orgs have NO band at all, demoting only clearly-weak financials avoids
    penalising the minority that happen to have data. NULL band is unaffected.
    Flame is intentionally NOT gated (its copy implies no financial quality).
"""

PASSING_BANDS = ('Exceptional', 'Strong', 'Solid')

import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'merit_registry.db')

TIER_SQL = """
CASE
  -- No financial data at all → Spark
  WHEN (latest_tax_year IS NULL OR latest_tax_year < 2022)
       AND (total_revenue IS NULL OR total_revenue <= 0)
  THEN 'Spark'

  -- Top-quartile rank + full profile + current 990 + positive revenue,
  -- and (where 990 financials are known) a passing financial band → Beacon
  WHEN COALESCE(peer_percentile, ntee1_percentile) >= 75
       AND (mission IS NOT NULL AND TRIM(mission) != '')
       AND (website IS NOT NULL AND TRIM(website) != '')
       AND latest_tax_year >= 2022
       AND total_revenue > 0
       AND (merit_band IS NULL OR merit_band != 'Concerns')
  THEN 'Beacon'

  -- Any rank + full profile + current 990 + positive revenue,
  -- and (where 990 financials are known) a passing financial band → Lantern
  WHEN COALESCE(peer_percentile, ntee1_percentile) IS NOT NULL
       AND (mission IS NOT NULL AND TRIM(mission) != '')
       AND (website IS NOT NULL AND TRIM(website) != '')
       AND latest_tax_year >= 2022
       AND total_revenue > 0
       AND (merit_band IS NULL OR merit_band != 'Concerns')
  THEN 'Lantern'

  -- Any rank + current 990 + positive revenue → Flame
  WHEN COALESCE(peer_percentile, ntee1_percentile) IS NOT NULL
       AND latest_tax_year >= 2022
       AND total_revenue > 0
  THEN 'Flame'

  -- Current 990 or any revenue on record → Ember
  WHEN latest_tax_year >= 2022
       OR (total_revenue IS NOT NULL AND total_revenue > 0)
  THEN 'Ember'

  ELSE 'Spark'
END
"""


def main():
    if not os.path.exists(DB_PATH):
        print(f'ERROR: Database not found at {DB_PATH}', file=sys.stderr)
        sys.exit(1)

    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA journal_mode=WAL')

    cols = [r[1] for r in db.execute('PRAGMA table_info(registry_enriched)').fetchall()]
    if 'merit_tier' not in cols:
        print('Adding merit_tier column...')
        db.execute('ALTER TABLE registry_enriched ADD COLUMN merit_tier TEXT')
    else:
        print('merit_tier column exists — re-populating...')

    print('Computing merit_tier for all orgs...')
    db.execute(f'UPDATE registry_enriched SET merit_tier = {TIER_SQL}')
    updated = db.execute('SELECT changes()').fetchone()[0]
    print(f'Updated {updated:,} rows.')

    print('\nTier distribution:')
    tiers = db.execute(
        'SELECT merit_tier, COUNT(*) as n FROM registry_enriched '
        'GROUP BY merit_tier ORDER BY n DESC'
    ).fetchall()
    total = sum(n for _, n in tiers)
    for tier, n in tiers:
        pct = 100 * n / total if total else 0
        print(f'  {(tier or "NULL"):<10} {n:>7,}  ({pct:.1f}%)')

    print('\nCreating index on merit_tier...')
    db.execute('CREATE INDEX IF NOT EXISTS idx_merit_tier ON registry_enriched(merit_tier)')

    db.commit()
    print('Migration complete.')


if __name__ == '__main__':
    main()
