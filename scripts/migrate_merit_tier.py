#!/usr/bin/env python3
"""
Add merit_tier column to registry_enriched and populate it.

Tier logic mirrors getTierFromOrg() in frontend/src/components/TrustBadge.tsx
so the filter and card display are always consistent.

Tiers (highest → lowest):
  Beacon  — top-quartile peer score + mission + website + current 990
  Lantern — any peer score + mission + website + current 990
  Flame   — any peer score + current 990
  Ember   — has current 990 or revenue data
  Spark   — IRS BMF only, no financial detail
"""

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

  -- Top-quartile score + full profile → Beacon
  WHEN COALESCE(peer_percentile, ntee1_percentile) >= 75
       AND (mission IS NOT NULL AND TRIM(mission) != '')
       AND (website IS NOT NULL AND TRIM(website) != '')
       AND latest_tax_year >= 2022
  THEN 'Beacon'

  -- Any score + full profile → Lantern
  WHEN COALESCE(peer_percentile, ntee1_percentile) IS NOT NULL
       AND (mission IS NOT NULL AND TRIM(mission) != '')
       AND (website IS NOT NULL AND TRIM(website) != '')
       AND latest_tax_year >= 2022
  THEN 'Lantern'

  -- Score + current 990 → Flame
  WHEN COALESCE(peer_percentile, ntee1_percentile) IS NOT NULL
       AND latest_tax_year >= 2022
  THEN 'Flame'

  -- Current 990 or revenue data → Ember
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
