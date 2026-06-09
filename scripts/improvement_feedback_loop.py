#!/usr/bin/env python3
"""
Continuous Improvement Feedback Loop

System learns from outcomes. Measure what matters:
  • Which orgs get clicked (traffic signal)
  • Which enrichments lead to donations (true impact)
  • Which categories users care about (priority signal)
  • Geographic coverage gaps (expansion opportunity)

Feedback loop:
  1. Enrich → Push to frontend
  2. Track: page views, clicks, donations
  3. Measure: enrichment quality by outcome
  4. Adjust: prioritize what works
  5. Repeat: continuous improvement

Metrics to track:
  • Click-through rate by category (CTR)
  • Donation rate by category (conversion)
  • Average donation amount (impact)
  • Search visibility by completion % (missions/tags)
  • Geographic coverage (# orgs per state)
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

HOME = Path.home()
PROJECT = HOME / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
LOGS = PROJECT / "logs"
LOG_FILE = LOGS / "improvement_feedback.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOGS.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def suggest_improvements():
    """Suggest next optimizations based on data."""
    log("=" * 70)
    log("SYSTEM IMPROVEMENT ANALYSIS")
    log("=" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # What's complete vs incomplete
    c.execute("""
        SELECT
            NTEE1,
            COUNT(*) as total,
            SUM(CASE WHEN mission IS NOT NULL AND mission != '' THEN 1 ELSE 0 END) as have_mission,
            SUM(CASE WHEN cause_tags IS NOT NULL THEN 1 ELSE 0 END) as have_tags,
            SUM(CASE WHEN total_revenue IS NOT NULL THEN 1 ELSE 0 END) as have_revenue
        FROM registry_enriched
        WHERE org_status = 'active'
        GROUP BY NTEE1
        ORDER BY total DESC
    """)

    categories = c.fetchall()

    print("\n✅ COMPLETION STATUS BY CATEGORY:")
    print("-" * 70)

    for ntee, total, mission, tags, revenue in categories[:10]:
        mission_pct = (mission / total * 100) if total else 0
        tags_pct = (tags / total * 100) if total else 0
        revenue_pct = (revenue / total * 100) if total else 0

        if tags_pct < 70:
            gap = "🔴 NEEDS TAGS"
        elif mission_pct < 90:
            gap = "🟡 NEEDS MISSIONS"
        else:
            gap = "🟢 COMPLETE"

        print(f"{ntee}: {total:,} orgs | Mission: {mission_pct:.0f}% | Tags: {tags_pct:.0f}% | {gap}")

    print("\n✅ SUGGESTED IMPROVEMENTS:")
    print("-" * 70)

    improvements = [
        {
            "priority": 1,
            "action": "Focus GPU on high-revenue categories with low tag completion",
            "impact": "Higher search relevance for high-value orgs",
            "effort": "Medium (just reorder queue)",
        },
        {
            "priority": 2,
            "action": "Implement click tracking on org detail pages",
            "impact": "Measure which enrichments actually help users",
            "effort": "Low (add analytics event)",
        },
        {
            "priority": 3,
            "action": "Add geographic coverage dashboard",
            "impact": "Identify states/regions needing more orgs",
            "effort": "Low (SQL + UI)",
        },
        {
            "priority": 4,
            "action": "Track donation outcomes by org",
            "impact": "True measure of success (donations, not just clicks)",
            "effort": "Medium (integrate with payment system)",
        },
        {
            "priority": 5,
            "action": "Build feedback loop: outcomes → priority adjustment",
            "impact": "System gets smarter over time",
            "effort": "High (ML/scoring)",
        },
    ]

    for imp in improvements:
        print(f"\nP{imp['priority']}: {imp['action']}")
        print(f"     Impact: {imp['impact']}")
        print(f"     Effort: {imp['effort']}")

    conn.close()

def main():
    log("IMPROVEMENT FEEDBACK SYSTEM")
    suggest_improvements()

    print("\n" + "=" * 70)
    print("STRATEGIC PRINCIPLES:")
    print("=" * 70)
    print("""
1. ALWAYS MEASURE
   → What gets measured gets managed
   → Track: clicks, donations, geography

2. OPTIMIZE FOR IMPACT, NOT VANITY METRICS
   → Donations > Clicks > Views
   → Real money > Page views

3. REVENUE-WEIGHTED
   → $100M org enrichment > $100K org enrichment
   → High-value first = biggest impact per GPU hour

4. FEEDBACK-DRIVEN
   → Learn from what works
   → Adjust weights based on outcomes
   → Never stop improving

5. STRATEGIC PATIENCE
   → Some enrichments take time to pay off
   → Track long-term outcomes
   → Don't just optimize for short-term gains
""")

    return 0

if __name__ == '__main__':
    main()
