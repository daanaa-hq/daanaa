#!/usr/bin/env python3
"""
Generate Monthly Newsletter

Triggered by new BMF data arrival.
Highlights the top 2-3 NTEE categories from that batch within 24 hours.

Newsletter structure:
  1. Opening: What's new this month
  2. Featured Categories: 2-3 categories with highest impact
     - Category name & description
     - # of new orgs + top revenue
     - 3-5 sample orgs (name, location, mission snippet)
  3. Closing: Explore link + call to action
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

HOME = Path.home()
PROJECT = HOME / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
LOGS = PROJECT / "logs"
LOG_FILE = LOGS / "newsletter_generation.log"

# NTEE Category descriptions (common ones)
NTEE_DESCRIPTIONS = {
    "A": "Arts, Culture & Humanities",
    "B": "Education & Research",
    "C": "Environment & Animals",
    "D": "Health & Medicine",
    "E": "Mental Health & Addiction",
    "F": "Crime & Legal Related",
    "G": "Employment & Training",
    "H": "Food, Agriculture & Nutrition",
    "I": "Housing & Shelter",
    "J": "Public Safety, Disaster Preparedness & Relief",
    "K": "Recreation & Sports",
    "L": "Youth Development",
    "M": "Voluntary & Membership Organizations",
    "N": "Philanthropy, Voluntarism & Grantmaking Foundations",
    "O": "Public & Societal Benefit",
    "P": "Religion",
    "Q": "Mutual & Membership Benefit Organizations",
    "R": "Unknown",
    "S": "Unknown",
    "T": "Unknown",
    "U": "Unknown",
    "V": "Unknown",
    "W": "Unknown",
    "X": "Unknown",
    "Y": "Unknown",
    "Z": "Unknown",
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOGS.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def find_new_data_batch():
    """Find recently added orgs (added in last 24 hours)."""
    log("=" * 70)
    log("NEWSLETTER: DETECTING NEW DATA BATCH")
    log("=" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Find orgs added in last 24 hours
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE updated_at > datetime('now', '-1 day')
        AND source = 'IRS_BMF'
    """)
    new_count = c.fetchone()[0]

    if new_count == 0:
        log("No new data in last 24 hours")
        conn.close()
        return None

    log(f"✅ Found {new_count:,} new orgs added in last 24 hours")
    return new_count

def analyze_top_categories(hours=24):
    """Find top 2-3 NTEE categories by newly scored orgs."""
    log("\nANALYZING TOP CATEGORIES (BY NEWLY SCORED ORGS)")
    log("-" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Get category stats for newly scored orgs (orgs with merit_score set recently)
    # This captures orgs that were both enriched and scored in the analysis window
    c.execute(f"""
        SELECT
            NTEE1,
            COUNT(*) as org_count,
            COUNT(DISTINCT EIN) as unique_orgs,
            SUM(COALESCE(total_revenue, 0)) as total_revenue,
            AVG(COALESCE(total_revenue, 0)) as avg_revenue,
            MAX(COALESCE(total_revenue, 0)) as max_revenue,
            AVG(COALESCE(merit_score, 0)) as avg_score
        FROM registry_enriched
        WHERE (
            -- New orgs added recently (data ingest)
            (updated_at > datetime('now', '-{hours} hours') AND source = 'IRS_BMF')
            OR
            -- Or recently scored (overnight pipeline ran)
            (merit_score IS NOT NULL AND updated_at > datetime('now', '-{hours} hours'))
        )
        AND NTEE1 IS NOT NULL
        AND org_status = 'active'
        GROUP BY NTEE1
        ORDER BY org_count DESC, total_revenue DESC
        LIMIT 5
    """)

    categories = c.fetchall()

    top_categories = []
    for ntee, org_count, unique, total_rev, avg_rev, max_rev, avg_score in categories[:3]:  # Top 3
        desc = NTEE_DESCRIPTIONS.get(ntee, "Unknown")
        top_categories.append({
            "ntee": ntee,
            "name": desc,
            "org_count": org_count,
            "unique_orgs": unique,
            "total_revenue": total_rev or 0,
            "avg_revenue": avg_rev or 0,
            "max_revenue": max_rev or 0,
            "avg_score": avg_score or 0,
        })
        log(f"  {ntee} ({desc}): {org_count} orgs, ${total_rev/1e9:.2f}B, avg score {avg_score:.0f}")

    conn.close()
    return top_categories

def get_sample_orgs(ntee, limit=5):
    """Get top sample orgs from a category (recently ingested or scored)."""
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    c.execute("""
        SELECT
            organization_name,
            CITY,
            STATE,
            total_revenue,
            mission,
            merit_score,
            merit_tier,
            EIN
        FROM registry_enriched
        WHERE NTEE1 = ?
        AND (
            (updated_at > datetime('now', '-24 hours') AND source = 'IRS_BMF')
            OR merit_score IS NOT NULL
        )
        AND organization_name IS NOT NULL
        AND org_status = 'active'
        ORDER BY
            COALESCE(merit_score, 0) DESC,
            COALESCE(total_revenue, 0) DESC,
            organization_name
        LIMIT ?
    """, (ntee, limit))

    orgs = []
    for row in c.fetchall():
        name, city, state, revenue, mission, score, tier, ein = row
        orgs.append({
            "name": name,
            "location": f"{city}, {state}" if city and state else state or "Unknown",
            "revenue": revenue or 0,
            "mission": (mission[:100] + "...") if mission and len(mission) > 100 else mission,
            "score": score,
            "tier": tier,
            "ein": ein,
        })

    conn.close()
    return orgs

def render_html_newsletter(categories):
    """Render newsletter as HTML."""
    timestamp = datetime.now().strftime("%B %Y")

    category_html = ""
    for cat in categories:
        samples_html = ""
        samples = get_sample_orgs(cat["ntee"], limit=5)

        for org in samples:
            revenue_str = f"${org['revenue']/1e6:.1f}M" if org['revenue'] else "Revenue not available"
            score_str = f"Score: {int(org['score'])}/100" if org['score'] else ""
            mission_str = f"<p style='margin:4px 0; font-size:13px; color:#666;'><em>{org['mission']}</em></p>" if org['mission'] else ""

            meta_parts = [org['location'], revenue_str]
            if score_str:
                meta_parts.append(score_str)
            meta_str = " • ".join(meta_parts)

            samples_html += f"""
            <div style='margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid #eee;'>
                <strong>{org['name']}</strong><br/>
                <span style='font-size:13px; color:#666;'>{meta_str}</span>
                {mission_str}
            </div>
            """

        category_html += f"""
        <div style='margin-bottom:30px; padding:15px; background:#f9f9f9; border-left:4px solid #3b82f6;'>
            <h3 style='margin:0 0 8px 0; color:#1f2937;'>{cat['name']}</h3>
            <p style='margin:0 0 12px 0; font-size:14px; color:#666;'>
                <strong>{cat['org_count']}</strong> new organizations
                <span style='margin-left:12px;'>Largest: <strong>${cat['max_revenue']/1e6:.1f}M</strong></span>
            </p>
            {samples_html}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Daanaa Monthly Spotlight — {timestamp}</title>
</head>
<body style='font-family:system-ui,-apple-system,sans-serif; line-height:1.5; color:#333; max-width:600px; margin:0 auto; padding:20px;'>

<div style='margin-bottom:30px;'>
    <h1 style='margin:0 0 12px 0; color:#1f2937; font-size:24px;'>Daanaa Monthly Spotlight</h1>
    <p style='margin:0; color:#666; font-size:14px;'>{timestamp}</p>
</div>

<div style='margin-bottom:30px; padding:15px; background:#e0f2fe; border-radius:4px;'>
    <p style='margin:0; color:#0c4a6e;'>
        This month, we've added new organizations to Daanaa's directory.
        Here are the cause areas with the most impact this month.
    </p>
</div>

<div>
    <h2 style='margin:20px 0 15px 0; color:#1f2937; font-size:18px;'>Featured Categories</h2>
    {category_html}
</div>

<div style='margin-top:30px; padding-top:20px; border-top:1px solid #e5e7eb;'>
    <p style='margin:0 0 12px 0;'>
        <a href='https://daanaa.org' style='color:#3b82f6; text-decoration:none; font-weight:500;'>
            Explore the full directory →
        </a>
    </p>
    <p style='margin:0; font-size:13px; color:#999;'>
        Daanaa is a nonprofit discovery platform featuring data from the IRS.
    </p>
</div>

</body>
</html>"""

    return html

def save_newsletter(html, timestamp=None):
    """Save newsletter to a file."""
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d")

    news_dir = PROJECT / "newsletters"
    news_dir.mkdir(exist_ok=True)

    filepath = news_dir / f"newsletter_{timestamp}.html"
    with open(filepath, 'w') as f:
        f.write(html)

    log(f"\n✅ Newsletter saved: {filepath}")
    return filepath

def create_send_manifest(filepath):
    """Create a manifest for sending (for integration with email system)."""
    manifest = {
        "newsletter_file": str(filepath),
        "from": "hello@daanaa.org",
        "subject": f"Daanaa Monthly Spotlight — {datetime.now().strftime('%B %Y')}",
        "created_at": datetime.now().isoformat(),
        "ready_to_send": True,
    }

    manifest_path = filepath.parent / f"{filepath.stem}_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    log(f"✅ Send manifest created: {manifest_path}")
    return manifest_path

def should_generate_newsletter():
    """Check if it's time to generate a new monthly newsletter."""
    # For now, we generate if new data was added in the last 24 hours
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE updated_at > datetime('now', '-24 hours')
        AND source = 'IRS_BMF'
    """)

    new_count = c.fetchone()[0]
    conn.close()

    return new_count > 0

def main():
    log("\n" + "=" * 70)
    log("MONTHLY NEWSLETTER GENERATION")
    log("=" * 70)

    # Check if new data exists
    new_count = find_new_data_batch()
    if not new_count:
        log("Skipping newsletter — no new data detected")
        return 0

    # Analyze top categories
    categories = analyze_top_categories(hours=24)

    if not categories:
        log("⚠️  No categories found for newsletter")
        return 1

    # Generate HTML
    html = render_html_newsletter(categories)

    # Save to file
    filepath = save_newsletter(html)

    # Create send manifest
    manifest_path = create_send_manifest(filepath)

    log("\n" + "=" * 70)
    log("READY TO SEND")
    log("=" * 70)
    log(f"Newsletter: {filepath}")
    log(f"Manifest: {manifest_path}")
    log(f"From: hello@daanaa.org")
    log(f"Subject: Daanaa Monthly Spotlight — {datetime.now().strftime('%B %Y')}")
    log("=" * 70)

    return 0

if __name__ == '__main__':
    try:
        exit(main())
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        log(traceback.format_exc())
        exit(1)
