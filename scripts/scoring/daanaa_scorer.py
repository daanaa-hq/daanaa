#!/usr/bin/env python3
"""
MERIT Scorer v6.1 — Enhanced Tiered Peer Financial Context System

Assigns each org to one of 5 tiers based on peer group specificity:
  Tier 1 (High): NTEE2 × 5-Band × Census Region (≥25 scoreable peers)
  Tier 2 (Good): NTEE2 × 5-Band national (≥20 scoreable peers)
  Tier 3 (Moderate): NTEE2 only (≥3 scoreable peers, lowered from 5)
  Tier 3b (Moderate-Broad): NTEE1 × Band (≥5 scoreable peers, fallback)
  Tier 4 (Data Gap): Archetype-only (fallback for sparse data)

Each tier includes peer_group_size + confidence label for honest display.
Fallback logic is deterministic: if Tier N peer group too small, try Tier N+1.
Enhanced to push coverage from 29.5% → 80%+ with broader peer contexts.

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

# Revenue band thresholds, Census region mapping, and get_revenue_band()/
# get_region() moved 2026-08-16 to scripts/scoring/peer_group.py -- now the
# single shared definition used by this scorer, both API files' similar-orgs
# lookup, and precompute_similar_orgs.py, so "peer group" means the exact
# same thing everywhere it's used (see DECISIONS.md 2026-08-16). Imported
# under their original names so nothing below this line changes.
from scripts.scoring.peer_group import (
    CENSUS_REGIONS,
    STATE_TO_REGION,
    get_region,
    get_revenue_band,
)

DB_PATH = "data/merit_registry.db"

def compute_revenue_percentiles(orgs, updates):
    """Compute percentile rank (0-100) for each org within its peer group.

    Returns: {EIN: (percentile, confidence, scoreable_peer_count)}
    - percentile: 0-100 integer, or NULL if <3 scoreable peers
    - confidence: HIGH (25+), MEDIUM (3-24), LOW (<3)
    - scoreable_peer_count: count of peers with non-null revenue
    """
    from bisect import bisect_right

    groups = defaultdict(list)
    memberships = {}

    # Map each org to its peer group and collect revenues
    for org, (scoring_tier, peer_desc, size, scoreable, confidence, ein) in zip(orgs, updates):
        ntee2 = org["NTEECC"][:2] if org["NTEECC"] else None
        ntee1 = org["NTEECC"][:1] if org["NTEECC"] else None
        band = get_revenue_band(org["total_revenue"])
        region = get_region(org["STATE"])
        archetype = org["merit_archetype_v5_label"]

        if scoring_tier == "1_Full_Context" and ntee2 and band and region:
            peer_key = ("tier1", ntee2, band, region)
        elif scoring_tier == "2_Regional_Context" and ntee2 and band:
            peer_key = ("tier2", ntee2, band)
        elif scoring_tier == "3_Broad_Category" and ntee2:
            peer_key = ("tier3", ntee2)
        elif scoring_tier == "3b_Broad_Category" and ntee1 and band:
            peer_key = ("tier3b", ntee1, band)
        elif scoring_tier == "4_Archetype_Only" and archetype and band:
            peer_key = ("tier4", archetype, band)
        else:
            peer_key = None

        memberships[ein] = peer_key

        # Include only scoreable (non-null revenue + reserves) orgs for ranking
        if (peer_key is not None and
            org["months_of_reserve"] is not None and
            org["total_revenue"] is not None):
            groups[peer_key].append(org["total_revenue"])

    # Sort revenue lists
    for peer_key in groups:
        groups[peer_key] = sorted(groups[peer_key])

    # Compute percentiles
    results = {}
    for org, (scoring_tier, peer_desc, size, scoreable, confidence, ein) in zip(orgs, updates):
        peer_key = memberships[ein]
        revenues = groups.get(peer_key, [])
        peer_count = len(revenues)

        # Confidence tiers (lowered thresholds: 3 instead of 5)
        if peer_count >= 25:
            conf = "HIGH"
        elif peer_count >= 3:
            conf = "MEDIUM"
        else:
            conf = "LOW"

        # Percentile: calculate if >= 3 peers and org has revenue (lowered from 5)
        percentile = None
        if peer_count >= 3 and org["total_revenue"] is not None:
            # Rank: (count of peers with revenue < this org) / total * 100
            percentile = round(100.0 * bisect_right(revenues, org["total_revenue"]) / peer_count)

        results[ein] = (percentile, conf, peer_count)

    return results

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
    tier3b_groups = defaultdict(list)  # NTEE1 × Band fallback
    tier4_groups = defaultdict(list)   # Archetype × Band fallback

    for org in orgs:
        ntee2 = org["NTEECC"][:2] if org["NTEECC"] else None
        ntee1 = org["NTEECC"][:1] if org["NTEECC"] else None  # First letter of NTEECC
        band = get_revenue_band(org["total_revenue"])
        region = get_region(org["STATE"])
        archetype = org["merit_archetype_v5_label"]

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

        # Tier 3b: NTEE1 × Band (fallback for sparse NTEE2 matches)
        if ntee1 and band:
            key = (ntee1, band)
            tier3b_groups[key].append(org)

        # Tier 4: Archetype × Band (fallback for data-sparse)
        if archetype and band:
            key = (archetype, band)
            tier4_groups[key].append(org)

    print(f"[v6.1] Tier 1 groups: {len(tier1_groups)} (regional + band specific)")
    print(f"[v6.1] Tier 2 groups: {len(tier2_groups)} (national, band specific)")
    print(f"[v6.1] Tier 3 groups: {len(tier3_groups)} (NTEE2 only)")
    print(f"[v6.1] Tier 3b groups: {len(tier3b_groups)} (NTEE1 × Band fallback)")
    print(f"[v6.1] Tier 4 groups: {len(tier4_groups)} (Archetype × Band fallback)")

    # Compute scoreable count for each group (has reserves data)
    scoreable_t1 = {k: len([o for o in v if o["months_of_reserve"] is not None]) for k, v in tier1_groups.items()}
    scoreable_t2 = {k: len([o for o in v if o["months_of_reserve"] is not None]) for k, v in tier2_groups.items()}
    scoreable_t3 = {k: len([o for o in v if o["months_of_reserve"] is not None]) for k, v in tier3_groups.items()}
    scoreable_t3b = {k: len([o for o in v if o["months_of_reserve"] is not None]) for k, v in tier3b_groups.items()}
    scoreable_t4 = {k: len([o for o in v if o["months_of_reserve"] is not None]) for k, v in tier4_groups.items()}

    # Assign tiers to each org
    updates = []
    tier_distribution = {"1_Full_Context": 0, "2_Regional_Context": 0, "3_Broad_Category": 0, "3b_Broad_Category": 0, "4_Archetype_Only": 0}

    for org in orgs:
        ein = org["EIN"]
        ntee2 = org["NTEECC"][:2] if org["NTEECC"] else None
        ntee1 = org["NTEECC"][:1] if org["NTEECC"] else None
        band = get_revenue_band(org["total_revenue"])
        region = get_region(org["STATE"])
        archetype = org["merit_archetype_v5_label"]

        if not ntee2 or not region:
            # Try Tier 3b: NTEE1 × Band fallback
            if ntee1 and band:
                tier3b_key = (ntee1, band)
                t3b_size = len(tier3b_groups.get(tier3b_key, []))
                t3b_scoreable = scoreable_t3b.get(tier3b_key, 0)
                if t3b_scoreable >= 5:
                    peer_desc = f"{archetype or 'Organization'}, {band}, {ntee1}* category"
                    updates.append((
                        "3b_Broad_Category",
                        peer_desc,
                        t3b_size,
                        t3b_scoreable,
                        "moderate",
                        ein
                    ))
                    tier_distribution["3b_Broad_Category"] += 1
                    continue

            # Try Tier 4: Archetype × Band fallback
            if archetype and band:
                tier4_key = (archetype, band)
                t4_size = len(tier4_groups.get(tier4_key, []))
                t4_scoreable = scoreable_t4.get(tier4_key, 0)
                if t4_scoreable >= 3:
                    peer_desc = f"{archetype}, {band}, all categories"
                    updates.append((
                        "4_Archetype_Only",
                        peer_desc,
                        t4_size,
                        t4_scoreable,
                        "low",
                        ein
                    ))
                    tier_distribution["4_Archetype_Only"] += 1
                    continue

            # Tier 4 fallback: no contextualization possible
            updates.append((
                "4_Archetype_Only",
                f"Archetype-only ({archetype or 'unknown'})",
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

        # Try Tier 3: NTEE2 only (lowered threshold from 5 to 3)
        t3_size = len(tier3_groups.get(ntee2, []))
        t3_scoreable = scoreable_t3.get(ntee2, 0)
        if t3_scoreable >= 3:  # Tier 3 threshold: 3+ scoreable peers (LOWERED)
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

        # Try Tier 3b: NTEE1 × Band fallback
        if ntee1 and band:
            tier3b_key = (ntee1, band)
            t3b_size = len(tier3b_groups.get(tier3b_key, []))
            t3b_scoreable = scoreable_t3b.get(tier3b_key, 0)
            if t3b_scoreable >= 5:
                peer_desc = f"{org['merit_archetype_v5_label'] or 'Organization'}, {band}, {ntee1}* category"
                updates.append((
                    "3b_Broad_Category",
                    peer_desc,
                    t3b_size,
                    t3b_scoreable,
                    "moderate",
                    ein
                ))
                tier_distribution["3b_Broad_Category"] += 1
                continue

        # Try Tier 4: Archetype × Band fallback
        if archetype and band:
            tier4_key = (archetype, band)
            t4_size = len(tier4_groups.get(tier4_key, []))
            t4_scoreable = scoreable_t4.get(tier4_key, 0)
            if t4_scoreable >= 3:
                peer_desc = f"{archetype}, {band}, all categories"
                updates.append((
                    "4_Archetype_Only",
                    peer_desc,
                    t4_size,
                    t4_scoreable,
                    "low",
                    ein
                ))
                tier_distribution["4_Archetype_Only"] += 1
                continue

        # Final fallback: no contextualization
        updates.append((
            "4_Archetype_Only",
            f"Archetype-only ({archetype or 'unknown'})",
            None,
            None,
            "archetype_only",
            ein
        ))
        tier_distribution["4_Archetype_Only"] += 1

    # Compute percentiles for all orgs
    print(f"[v6.0] Computing revenue percentiles within peer groups...")
    percentile_data = compute_revenue_percentiles(orgs, updates)
    percentile_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for ein, (percentile, conf, count) in percentile_data.items():
        percentile_dist[conf] += 1
    print(f"  Percentile confidence: HIGH={percentile_dist['HIGH']:,}, MEDIUM={percentile_dist['MEDIUM']:,}, LOW={percentile_dist['LOW']:,}")

    # Write to database
    print(f"\n[v6.0] Writing tier assignments + percentiles...")

    # Idempotent column creation (check if exists first)
    def add_column_if_not_exists(cursor, table, column, definition):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    add_column_if_not_exists(cursor, "registry_enriched", "scoring_tier", "TEXT DEFAULT NULL")
    add_column_if_not_exists(cursor, "registry_enriched", "tier_label", "TEXT DEFAULT NULL")
    add_column_if_not_exists(cursor, "registry_enriched", "peer_group_size", "INTEGER DEFAULT NULL")
    add_column_if_not_exists(cursor, "registry_enriched", "peer_group_description", "TEXT DEFAULT NULL")
    add_column_if_not_exists(cursor, "registry_enriched", "confidence", "TEXT DEFAULT NULL")

    for scoring_tier, peer_desc, size, scoreable, confidence, ein in updates:
        percentile, percentile_confidence, percentile_peer_count = percentile_data[ein]
        cursor.execute("""
            UPDATE registry_enriched
            SET scoring_tier = ?, tier_label = ?, peer_group_size = ?,
                peer_group_description = ?, confidence = ?,
                merit_percentile_v6 = ?,
                merit_percentile_confidence_v6 = ?,
                merit_peer_count_v6_scoreable = ?
            WHERE EIN = ?
        """, (scoring_tier, peer_desc, size, peer_desc, confidence, percentile, percentile_confidence, percentile_peer_count, ein))

    conn.commit()

    print(f"\n[v6.1] TIER DISTRIBUTION")
    print(f"  Tier 1 (Full Context):      {tier_distribution['1_Full_Context']:>7,} orgs ({100.0 * tier_distribution['1_Full_Context'] / len(orgs):.1f}%)")
    print(f"  Tier 2 (Regional Context):  {tier_distribution['2_Regional_Context']:>7,} orgs ({100.0 * tier_distribution['2_Regional_Context'] / len(orgs):.1f}%)")
    print(f"  Tier 3 (Broad Category):    {tier_distribution['3_Broad_Category']:>7,} orgs ({100.0 * tier_distribution['3_Broad_Category'] / len(orgs):.1f}%)")
    print(f"  Tier 3b (Category+Band):    {tier_distribution['3b_Broad_Category']:>7,} orgs ({100.0 * tier_distribution['3b_Broad_Category'] / len(orgs):.1f}%)")
    print(f"  Tier 4 (Archetype Only):    {tier_distribution['4_Archetype_Only']:>7,} orgs ({100.0 * tier_distribution['4_Archetype_Only'] / len(orgs):.1f}%)")
    print(f"  ─────────────────────────────────────────")
    print(f"  TOTAL:                      {len(orgs):>7,} orgs")

    print(f"\n[v6.1] Scoring complete. Enhanced percentile coverage (target 80%+). Ready for API integration + display layer.")
    conn.close()

if __name__ == "__main__":
    main()
