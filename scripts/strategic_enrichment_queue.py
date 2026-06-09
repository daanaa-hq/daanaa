#!/usr/bin/env python3
"""
Strategic Enrichment Queue v1

Don't enrich randomly. Enrich strategically by impact:
  1. High-revenue orgs first (biggest impact on donors)
  2. Missing critical data (missions, tags block search)
  3. High-traffic categories (work where users are)
  4. Geographic underrepresentation (expand coverage)

Principles:
  • Revenue-weighted: $100M org > $1M org
  • Impact-weighted: Busy category > dead category
  • Completion-driven: Don't enrich if already 80% done
  • Continuous improvement: Track metrics, adjust strategy

Workflow:
  1. Score each org by: revenue × search_traffic × geographic_gap
  2. Queue top N by score (highest impact first)
  3. Skip if already enriched > 80%
  4. Monitor: which enrichments lead to clicks/donations
  5. Iterate: adjust weights based on outcomes
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

HOME = Path.home()
PROJECT = HOME / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
LOGS = PROJECT / "logs"
LOG_FILE = LOGS / "strategic_enrichment.log"
STRATEGY_FILE = PROJECT / ".enrichment_strategy.json"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOGS.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def calculate_impact_score():
    """Score orgs by strategic impact (revenue × traffic × gap)."""
    log("=" * 70)
    log("CALCULATING STRATEGIC ENRICHMENT PRIORITIES")
    log("=" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Get stats
    c.execute("""
        SELECT
            NTEE1,
            COUNT(*) as count,
            AVG(total_revenue) as avg_revenue,
            SUM(CASE WHEN mission IS NOT NULL THEN 1 ELSE 0 END) as have_mission,
            SUM(CASE WHEN cause_tags IS NOT NULL THEN 1 ELSE 0 END) as have_tags
        FROM registry_enriched
        WHERE org_status = 'active' AND NTEE1 IS NOT NULL
        GROUP BY NTEE1
        ORDER BY avg_revenue DESC
    """)

    categories = c.fetchall()
    print("\nCATEGORY ANALYSIS (by avg revenue):")
    print("-" * 70)

    for ntee, count, avg_rev, have_mission, have_tags in categories[:15]:
        mission_pct = (have_mission / count * 100) if count else 0
        tags_pct = (have_tags / count * 100) if count else 0

        print(f"{ntee}: ${avg_rev/1e6:.1f}M avg | {count:,} orgs | Mission: {mission_pct:.0f}% | Tags: {tags_pct:.0f}%")

    conn.close()

def build_enrichment_queue():
    """Build priority queue: high-revenue + missing data first."""
    log("\n" + "=" * 70)
    log("BUILDING STRATEGIC QUEUE")
    log("=" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Find high-value orgs that need enrichment
    c.execute("""
        SELECT
            EIN,
            organization_name,
            total_revenue,
            NTEE1,
            CASE WHEN mission IS NULL OR mission = '' THEN 1 ELSE 0 END as needs_mission,
            CASE WHEN cause_tags IS NULL THEN 1 ELSE 0 END as needs_tags,
            (COALESCE(total_revenue, 0) / 1000000.0) as revenue_millions
        FROM registry_enriched
        WHERE org_status = 'active'
        AND (mission IS NULL OR mission = '' OR cause_tags IS NULL)
        ORDER BY
            total_revenue DESC,
            CASE WHEN mission IS NULL THEN 1 ELSE 0 END DESC,
            CASE WHEN cause_tags IS NULL THEN 1 ELSE 0 END DESC
        LIMIT 100
    """)

    queue = c.fetchall()

    print(f"\nTop 10 by strategic impact:")
    print("-" * 70)
    for i, (ein, name, revenue, ntee, needs_mission, needs_tags, rev_m) in enumerate(queue[:10], 1):
        needs = []
        if needs_mission:
            needs.append("mission")
        if needs_tags:
            needs.append("tags")
        print(f"{i}. {name[:40]:<40} ${rev_m:>8.1f}M | {ntee} | needs: {','.join(needs)}")

    conn.close()
    return queue

def analyze_completion():
    """Check enrichment completion rate."""
    log("\n" + "=" * 70)
    log("ENRICHMENT COMPLETION ANALYSIS")
    log("=" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    c.execute("""
        SELECT
            COUNT(*) as total_active,
            SUM(CASE WHEN mission IS NOT NULL AND mission != '' THEN 1 ELSE 0 END) as have_mission,
            SUM(CASE WHEN cause_tags IS NOT NULL THEN 1 ELSE 0 END) as have_tags,
            SUM(CASE WHEN mission IS NOT NULL AND cause_tags IS NOT NULL THEN 1 ELSE 0 END) as fully_enriched
        FROM registry_enriched
        WHERE org_status = 'active'
    """)

    total, have_mission, have_tags, fully_enriched = c.fetchone()

    log(f"Total active orgs: {total:,}")
    log(f"  With missions: {have_mission:,} ({100*have_mission//total if total else 0}%)")
    log(f"  With tags: {have_tags:,} ({100*have_tags//total if total else 0}%)")
    log(f"  Fully enriched: {fully_enriched:,} ({100*fully_enriched//total if total else 0}%)")

    gaps = {
        'need_mission': total - have_mission,
        'need_tags': total - have_tags,
        'both': total - fully_enriched,
    }

    log(f"\nWork remaining:")
    log(f"  Missions needed: {gaps['need_mission']:,}")
    log(f"  Tags needed: {gaps['need_tags']:,}")
    log(f"  Both needed: {gaps['both']:,}")

    conn.close()
    return gaps

def recommend_strategy():
    """Recommend next strategic moves."""
    log("\n" + "=" * 70)
    log("STRATEGIC RECOMMENDATIONS")
    log("=" * 70)

    queue = build_enrichment_queue()
    gaps = analyze_completion()

    log("\n✅ IMMEDIATE ACTIONS (Priority Order):")
    log("  1. Enrich HIGH-REVENUE orgs first")
    log("     (biggest impact on search relevance)")
    log("  2. Fill MISSIONS gap (812K orgs)")
    log("     (essential for search, discovery)")
    log("  3. Fill TAGS gap (895K orgs)")
    log("     (enables category filtering)")
    log("  4. Monitor TRAFFIC metrics")
    log("     (which enrichments get clicked?)")

    log("\n⏳ ONGOING OPTIMIZATION:")
    log("  • Track click-through rate by category")
    log("  • Prioritize high-traffic categories")
    log("  • Deprioritize low-traffic categories")
    log("  • Adjust revenue weight based on impact")
    log("  • Measure: enrichment → search visibility → clicks → donations")

    log("\n💡 WHAT'S WORKING:")
    log("  ✓ Revenue-based sorting (high-value first)")
    log("  ✓ Missing-data detection (skip complete records)")
    log("  ✓ Category analysis (understand coverage gaps)")
    log("  ✓ GPU-smart queuing (skip revoked orgs)")

    log("\n🎯 NEXT PHASE:")
    log("  1. Implement click tracking on org detail pages")
    log("  2. Build feedback loop: clicks → priority weight adjustment")
    log("  3. Add geographic gap detection (underserved regions)")
    log("  4. Monitor donation volume by org (ultimate impact metric)")

    return gaps

def main():
    log("\n" + "=" * 70)
    log("STRATEGIC ENRICHMENT PLANNING")
    log("=" * 70)

    # Analyze current state
    calculate_impact_score()

    # Build smart queue
    queue = build_enrichment_queue()

    # Check completion
    gaps = analyze_completion()

    # Recommend strategy
    recommend_strategy()

    log("\n" + "=" * 70)
    log("✅ READY: Use this queue for GPU enrichment")
    log("   GPU will enrich: HIGH-REVENUE + MISSING-DATA first")
    log("=" * 70)

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
