#!/usr/bin/env python3
"""Monitor website discovery progress."""
import sqlite3
from datetime import datetime

db = sqlite3.connect('/home/akbar/meritgiving/data/merit_registry.db')
c = db.cursor()

# Get recent discoveries
c.execute("""
SELECT website_status, COUNT(*) as count
FROM registry_enriched 
WHERE website_discovered_at > datetime('now', '-24 hours')
GROUP BY website_status
ORDER BY count DESC
""")

print(f"[{datetime.now().strftime('%H:%M')}] Website discoveries (last 24h):")
total = 0
for status, count in c.fetchall():
    print(f"  {status:20s}: {count:>5,}")
    total += count

if total > 0:
    c.execute("""
    SELECT COUNT(*) FROM registry_enriched
    WHERE website IS NOT NULL AND website != ''
      AND website_discovered_at > datetime('now', '-24 hours')
    """)
    found = c.fetchone()[0]
    print(f"\n  ✓ Successfully discovered: {found:,}")

# Overall coverage
c.execute("SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != ''")
total_with_sites = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM registry_enriched")
total_orgs = c.fetchone()[0]

print(f"\nOverall coverage: {total_with_sites:,} / {total_orgs:,} ({100*total_with_sites/total_orgs:.1f}%)")

db.close()
