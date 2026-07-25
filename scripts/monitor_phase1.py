#!/usr/bin/env python3
"""Monitor Phase 1 discovery progress."""
import sqlite3
from datetime import datetime

db = sqlite3.connect('/home/akbar/meritgiving/data/merit_registry.db')
c = db.cursor()

# Websites discovered in last 2 hours
c.execute("""
SELECT COUNT(*) as recent_finds, COUNT(DISTINCT website_status)
FROM registry_enriched 
WHERE website_status IN ('ok', 'redirect')
  AND website IS NOT NULL
  AND website != ''
""")
row = c.fetchone()
if row:
    found, statuses = row
    print(f"[{datetime.now().strftime('%H:%M')}] Phase 1 Progress:")
    print(f"  Total discovered: {found:,}")
    print(f"  Status types: {statuses}")

# Current coverage
c.execute("SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != ''")
total_with_sites = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM registry_enriched")
total_orgs = c.fetchone()[0]

coverage = 100 * total_with_sites / total_orgs if total_orgs > 0 else 0
print(f"  Current coverage: {total_with_sites:,} / {total_orgs:,} ({coverage:.1f}%)")
print(f"  Target: 45% coverage (934K websites)")

db.close()
