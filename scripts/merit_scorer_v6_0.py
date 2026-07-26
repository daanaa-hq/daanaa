#!/usr/bin/env python3
"""
MERIT Scorer v6.0 — Tiered Peer Financial Context System

Assigns each org to one of 4 tiers based on peer group specificity:
  Tier 1 (High): NTEE2 × 5-Band × Census Region (≥25 scoreable peers)
  Tier 2 (Good): NTEE2 × 5-Band national (≥20 scoreable peers)
  Tier 3 (Moderate): NTEE2 only (≥5 scoreable peers)
  Tier 4 (Data Gap): Archetype-only (no reserves data to score)

Each tier includes peer_group_size + confidence label for honest display.
Fallback logic is deterministic: if Tier N peer group too small, try Tier N+1.

Aligned with:
  • IRS filing thresholds ($50K, $200K, $5M revenue bands)
  • US Census Bureau regions (Northeast, Midwest, South, West)
  • NCCS peer grouping research (NTEE granularity + geographic context)
  • Stewardship Principle #3 (trust signals evidence-based + honest confidence)
"""

import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

DB_PATH = "data/merit_registry.db"

# Revenue band thresholds (IRS-aligned)
def get_revenue_band(revenue):
    if revenue is None or revenue == 0:
        return None
    if revenue < 50000:
        return "Grassroots"
    elif revenue < 200000:
        return "Small"
    elif revenue < 500000:
        return "Mid"
    elif revenue < 5000000:
        return "Established"
    else:
        return "Major"

# Census region mapping
CENSUS_REGIONS = {
    "Northeast": ["CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"],
    "Midwest": ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"],
    "South": ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"],
    "West": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"],
}

STATE_TO_REGION = {}
for region, states in CENSUS_REGIONS.items():
    for state in states:
        STATE_TO_REGION[state] = region

def get_region(state):
    return STATE_TO_REGION.get(state)

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("[v6.0] Loading registry...")
    cursor.execute("""
        SELECT EIN, organization_name, NTEECC, STATE, total_revenue, months_of_reserve, merit_archetype_v5_label
        FROM registry_enriched
        WHERE deductibility = '1'
        AND NTEECC IS NOT NULL
        AND STATE IS NOT NULL
        ORDER BY EIN
    """)
    orgs = cursor.fetchall()
    print(f"[v6.0] Loaded {len(orgs)} orgs")

    # Build peer group index: (ntee2, band, region) -> list of orgs with reserves
    tier1_groups = defaultdict(list)
    tier2_groups = defaultdict(list)
    tier3_groups = defaultdict(list)

    for org in orgs:
        ntee2 = org["NTEECC"][:2] if org["NTEECC"] else None
        band = get_revenue_band(org["total_revenue"])
        region = get_region(org["STATE"])

        if not ntee2 or not region:
            continue

        # Tier 1: NTEE2 × Band × Region
        if band:
            key = (ntee2, band, region)
            tier1_groups[key].append(org)

        # Tier 2: NTEE2 × Band (national)
        if band:
            key = (ntee2, band)
            tier2_groups[key].append(org)

        # Tier 3: NTEE2 only
        tier3_groups[ntee2].append(org)

    print(f"[v6.0] Tier 1 groups: {len(tier1_groups)} (regional + band specific)")
    print(f"[v6.0] Tier 2 groups: {len(tier2_groups)} (national, band specific)")
    print(f"[v6.0] Tier 3 groups: {len(tier3_groups)} (NTEE only)")

    # Compute scoreable count for each group (has reserves data)
    scoreable_t1 = {k: len([o for o in v if o["months_of_reserve"] is not None]) for k, v in tier1_groups.items()}
    scoreable_t2 = {k: len([o for o in v if o["months_of_reserve"] is not None]) for k, v in tier2_groups.items()}
    scoreable_t3 = {k: len([o for o in v if o["months_of_reserve"] is not None]) for k, v in tier3_groups.items()}

    # Assign tiers to each org
    updates = []
    tier_distribution = {"1_Full_Context": 0, "2_Regional_Context": 0, "3_Broad_Category": 0, "4_Archetype_Only": 0}

    for org in orgs:
        ein = org["EIN"]
        ntee2 = org["NTEECC"][:2] if org["NTEECC"] else None
        band = get_revenue_band(org["total_revenue"])
        region = get_region(org["STATE"])

        if not ntee2 or not region:
            # Tier 4: no geographic/mission data
            updates.append((
                "4_Archetype_Only",
                f"Archetype-only ({org['merit_archetype_v5_label'] or 'unknown'})",
                None,
                None,
                "archetype_only",
                ein
            ))
            tier_distribution["4_Archetype_Only"] += 1
            continue

        # Try Tier 1: NTEE2 × Band × Region
        if band:
            tier1_key = (ntee2, band, region)
            t1_size = len(tier1_groups.get(tier1_key, []))
            t1_scoreable = scoreable_t1.get(tier1_key, 0)
            if t1_scoreable >= 25:  # Tier 1 threshold: 25+ scoreable peers
                peer_desc = f"{org['merit_archetype_v5_label'] or 'Organization'}, {band}, {region} region"
                updates.append((
                    "1_Full_Context",
                    peer_desc,
                    t1_size,
                    t1_scoreable,
                    "high",
                    ein
                ))
                tier_distribution["1_Full_Context"] += 1
                continue

        # Try Tier 2: NTEE2 × Band (national)
        if band:
            tier2_key = (ntee2, band)
            t2_size = len(tier2_groups.get(tier2_key, []))
            t2_scoreable = scoreable_t2.get(tier2_key, 0)
            if t2_scoreable >= 20:  # Tier 2 threshold: 20+ scoreable peers
                peer_desc = f"{org['merit_archetype_v5_label'] or 'Organization'}, {band}, national"
                updates.append((
                    "2_Regional_Context",
                    peer_desc,
                    t2_size,
                    t2_scoreable,
                    "good",
                    ein
                ))
                tier_distribution["2_Regional_Context"] += 1
                continue

        # Try Tier 3: NTEE2 only
        t3_size = len(tier3_groups.get(ntee2, []))
        t3_scoreable = scoreable_t3.get(ntee2, 0)
        if t3_scoreable >= 5:  # Tier 3 threshold: 5+ scoreable peers
            peer_desc = f"{org['merit_archetype_v5_label'] or 'Organization'}, all sizes"
            updates.append((
                "3_Broad_Category",
                peer_desc,
                t3_size,
                t3_scoreable,
                "moderate",
                ein
            ))
            tier_distribution["3_Broad_Category"] += 1
            continue

        # Tier 4: Fallback for sparse or no-data orgs
        updates.append((
            "4_Archetype_Only",
            f"Archetype-only ({org['merit_archetype_v5_label'] or 'unknown'})",
            None,
            None,
            "archetype_only",
            ein
        ))
        tier_distribution["4_Archetype_Only"] += 1

    # Write to database
    print(f"\n[v6.0] Writing tier assignments...")
    cursor.execute("""
        ALTER TABLE registry_enriched ADD COLUMN scoring_tier TEXT DEFAULT NULL;
    """)
    cursor.execute("""
        ALTER TABLE registry_enriched ADD COLUMN tier_label TEXT DEFAULT NULL;
    """)
    cursor.execute("""
        ALTER TABLE registry_enriched ADD COLUMN peer_group_size INTEGER DEFAULT NULL;
    """)
    cursor.execute("""
        ALTER TABLE registry_enriched ADD COLUMN peer_group_description TEXT DEFAULT NULL;
    """)
    cursor.execute("""
        ALTER TABLE registry_enriched ADD COLUMN confidence TEXT DEFAULT NULL;
    """)

    for scoring_tier, peer_desc, size, scoreable, confidence, ein in updates:
        cursor.execute("""
            UPDATE registry_enriched
            SET scoring_tier = ?, tier_label = ?, peer_group_size = ?,
                peer_group_description = ?, confidence = ?
            WHERE EIN = ?
        """, (scoring_tier, peer_desc, size, peer_desc, confidence, ein))

    conn.commit()

    print(f"\n[v6.0] TIER DISTRIBUTION")
    print(f"  Tier 1 (Full Context):      {tier_distribution['1_Full_Context']:>7,} orgs ({100.0 * tier_distribution['1_Full_Context'] / len(orgs):.1f}%)")
    print(f"  Tier 2 (Regional Context):  {tier_distribution['2_Regional_Context']:>7,} orgs ({100.0 * tier_distribution['2_Regional_Context'] / len(orgs):.1f}%)")
    print(f"  Tier 3 (Broad Category):    {tier_distribution['3_Broad_Category']:>7,} orgs ({100.0 * tier_distribution['3_Broad_Category'] / len(orgs):.1f}%)")
    print(f"  Tier 4 (Archetype Only):    {tier_distribution['4_Archetype_Only']:>7,} orgs ({100.0 * tier_distribution['4_Archetype_Only'] / len(orgs):.1f}%)")
    print(f"  ─────────────────────────────────────────")
    print(f"  TOTAL:                      {len(orgs):>7,} orgs")

    print(f"\n[v6.0] Scoring complete. Ready for API integration + display layer.")
    conn.close()

if __name__ == "__main__":
    main()
