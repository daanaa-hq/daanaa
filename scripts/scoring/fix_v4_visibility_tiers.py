#!/usr/bin/env python3
"""
Fix visibility tier naming in v4_scores table.

Database currently has: Tier_B, Tier_C, Growing, Steady Flame, Burning Bright, Blazing, Just Starting
Should be: Spark, Glow, Ember, Flame, Lantern, Beacon (based on frontend expectations)

This script maps based on merit_score distribution and data completeness.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"

# Mapping logic based on merit_score and data completeness
# Frontend expects these exact names: Spark, Glow, Ember, Flame, Lantern, Beacon
TIER_MAPPING = {
    'Just Starting': 'Spark',      # 0-25 score, minimal data
    'Growing': 'Glow',              # 25-40 score, some data
    'Steady Flame': 'Flame',        # 40-60 score, moderate data
    'Burning Bright': 'Lantern',    # 60-80 score, good data
    'Blazing': 'Beacon',            # 80+ score, excellent data
    'Tier_B': 'Flame',              # Deductible but partial data
    'Tier_C': 'Glow',               # Non-deductible
}

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=" * 70)
print("V4 VISIBILITY TIER NAME FIX")
print("=" * 70)

# Check current distribution
print("\nCurrent tier distribution:")
dist = c.execute("""
    SELECT visibility_tier, COUNT(*) as cnt
    FROM v4_scores
    WHERE visibility_tier IS NOT NULL
    GROUP BY visibility_tier
    ORDER BY cnt DESC
""").fetchall()

for tier, cnt in dist:
    new_tier = TIER_MAPPING.get(tier, tier)
    print(f"  {tier:20} → {new_tier:20} ({cnt:>8,} orgs)")

# Apply fixes
print("\nApplying corrections...")
for old_tier, new_tier in TIER_MAPPING.items():
    c.execute("""
        UPDATE v4_scores
        SET visibility_tier = ?
        WHERE visibility_tier = ?
    """, (new_tier, old_tier))
    count = c.rowcount
    if count > 0:
        print(f"  ✓ {old_tier:20} → {new_tier:20} ({count:>8,} updated)")

conn.commit()

# Verify the fix
print("\nNew tier distribution:")
dist_new = c.execute("""
    SELECT visibility_tier, COUNT(*) as cnt
    FROM v4_scores
    WHERE visibility_tier IS NOT NULL
    GROUP BY visibility_tier
    ORDER BY cnt DESC
""").fetchall()

for tier, cnt in dist_new:
    print(f"  {tier:20} ({cnt:>8,} orgs)")

conn.close()

print("\n✅ V4 visibility tier names fixed!")
print("📌 Next: Restart API to load corrected data")
