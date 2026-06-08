#!/usr/bin/env python3
"""
Weekly Summary Agent — Report on discoveries, impact, quality
Runs: Every Monday 12 AM CDT (1 AM UTC)
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG = Path.home() / "meritgiving/logs/weekly_summary.log"

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def get_week_stats():
    """Retrieve stats from past 7 days."""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    week_ago = (datetime.now() - timedelta(days=7)).isoformat()

    # New websites verified
    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE website IS NOT NULL
        AND datetime(updated_at) >= ?
    """, (week_ago,))
    new_websites = cur.fetchone()[0] or 0

    # New donation links
    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE donate_url IS NOT NULL
        AND datetime(updated_at) >= ?
    """, (week_ago,))
    new_links = cur.fetchone()[0] or 0

    # Total orgs with verified sites
    cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL")
    total_sites = cur.fetchone()[0] or 0

    # Total orgs with donation links
    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE donate_url IS NOT NULL AND donate_confidence >= 90
    """)
    total_links = cur.fetchone()[0] or 0

    # Tier distribution
    cur.execute("""
        SELECT merit_tier, COUNT(*) FROM registry_enriched
        WHERE merit_tier IS NOT NULL
        GROUP BY merit_tier
    """)
    tier_dist = dict(cur.fetchall())

    conn.close()

    return {
        "new_websites": new_websites,
        "new_links": new_links,
        "total_websites": total_sites,
        "total_links": total_links,
        "tier_distribution": tier_dist,
    }

def estimate_weekly_impact(stats):
    """Estimate dollars routed this week."""
    # Conservative: assume 1/52 of annual $ distributed
    # For each new website + link combo
    impact_orgs = stats["new_websites"]  # Newly verifiable
    estimated_weekly = impact_orgs * (100000 / 52)  # Annualized $100K avg
    return estimated_weekly

def main():
    log("═" * 80)
    log("WEEKLY SUMMARY — Week of " + (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
    log("═" * 80)

    stats = get_week_stats()

    log("\n🔍 DISCOVERY METRICS:")
    log(f"  New websites verified: {stats['new_websites']:,}")
    log(f"  New donation links: {stats['new_links']:,}")
    log(f"  Total websites: {stats['total_websites']:,}")
    log(f"  Total direct-give links: {stats['total_links']:,}")

    log("\n📊 TIER DISTRIBUTION:")
    for tier, count in sorted(stats["tier_distribution"].items()):
        pct = 100 * count / sum(stats["tier_distribution"].values())
        log(f"  {tier}: {count:,} ({pct:.1f}%)")

    impact = estimate_weekly_impact(stats)
    log(f"\n💰 ESTIMATED WEEKLY IMPACT: ${impact:,.0f}")
    log(f"   Annualized run rate: ${impact * 52:,.0f}")

    log("\n✅ QUALITY INDICATORS:")
    log(f"  Data freshness: 7-day window (rolling)")
    log(f"  Website discovery rate: {100*stats['total_websites']/1800000:.1f}% of indexed")
    log(f"  Direct-donate coverage: {100*stats['total_links']/stats['total_websites'] if stats['total_websites'] else 0:.1f}% of websites")

    log("\n" + "═" * 80)

if __name__ == "__main__":
    main()
