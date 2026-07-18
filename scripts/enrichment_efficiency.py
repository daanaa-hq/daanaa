#!/usr/bin/env python3
"""
Enrichment Efficiency Tracker — Measure ROI on enrichment work.
Tracks: websites discovered, missions generated, donation links verified, and coverage growth.

Usage:
  python3 enrichment_efficiency.py --show         # Show current efficiency metrics
  python3 enrichment_efficiency.py --log-run      # Log a pipeline run (for cron)
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "merit_registry.db"
METRICS_DIR = REPO_ROOT / "logs" / "enrichment_metrics"
METRICS_DIR.mkdir(exist_ok=True)

def get_db_metrics():
    """Query database for current enrichment state."""
    if not DB_PATH.exists():
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Count orgs with each enrichment field
        cursor.execute("""
            SELECT
                COUNT(*) as total_orgs,
                SUM(CASE WHEN website IS NOT NULL AND website != '' THEN 1 ELSE 0 END) as with_website,
                SUM(CASE WHEN mission IS NOT NULL AND mission != '' THEN 1 ELSE 0 END) as with_mission,
                SUM(CASE WHEN donate_url IS NOT NULL AND donate_url != '' THEN 1 ELSE 0 END) as with_donate_url,
                SUM(CASE WHEN website_status = 'active' THEN 1 ELSE 0 END) as active_websites,
                SUM(CASE WHEN donate_confidence >= 90 THEN 1 ELSE 0 END) as verified_donate_links
            FROM registry_enriched
        """)
        return dict(cursor.fetchone())
    except Exception as e:
        print(f"❌ DB query failed: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def load_run_history():
    """Load historical metrics from disk."""
    history = []
    for f in sorted(METRICS_DIR.glob("*.json")):
        try:
            with open(f) as fp:
                history.append(json.load(fp))
        except:
            pass
    return history

def compute_delta(current, previous):
    """Compute growth since last run."""
    if not previous:
        return {}

    delta = {}
    for key in ['with_website', 'with_mission', 'with_donate_url', 'active_websites', 'verified_donate_links']:
        if key in current and key in previous:
            delta[key] = current[key] - previous[key]

    return delta

def show_metrics():
    """Display efficiency metrics."""
    metrics = get_db_metrics()
    if not metrics:
        print("❌ Could not query database")
        return

    history = load_run_history()
    prev = history[-1] if history else None

    print("\n" + "=" * 70)
    print("📊 ENRICHMENT EFFICIENCY — Coverage & Quality Growth")
    print("=" * 70)
    print()

    print(f"Total Active Orgs: {metrics['total_orgs']:,}")
    print()

    # Website enrichment
    print("🌐 WEBSITES")
    pct = 100 * metrics['with_website'] / metrics['total_orgs'] if metrics['total_orgs'] else 0
    delta = ""
    if prev and 'with_website' in prev:
        growth = metrics['with_website'] - prev['with_website']
        delta = f" (+{growth:,} since last run)" if growth > 0 else ""
    print(f"  Discovered: {metrics['with_website']:,} orgs ({pct:.1f}%){delta}")
    print(f"  Active: {metrics['active_websites']:,}")

    print()

    # Mission enrichment
    print("💭 MISSIONS")
    pct = 100 * metrics['with_mission'] / metrics['total_orgs'] if metrics['total_orgs'] else 0
    delta = ""
    if prev and 'with_mission' in prev:
        growth = metrics['with_mission'] - prev['with_mission']
        delta = f" (+{growth:,} since last run)" if growth > 0 else ""
    print(f"  Generated: {metrics['with_mission']:,} orgs ({pct:.1f}%){delta}")

    print()

    # Donation links
    print("💳 DONATION LINKS")
    pct = 100 * metrics['with_donate_url'] / metrics['total_orgs'] if metrics['total_orgs'] else 0
    delta = ""
    if prev and 'with_donate_url' in prev:
        growth = metrics['with_donate_url'] - prev['with_donate_url']
        delta = f" (+{growth:,} since last run)" if growth > 0 else ""
    print(f"  Discovered: {metrics['with_donate_url']:,} orgs ({pct:.1f}%){delta}")

    verified_pct = 100 * metrics['verified_donate_links'] / metrics['with_donate_url'] if metrics['with_donate_url'] else 0
    print(f"  Verified (≥90% confidence): {metrics['verified_donate_links']:,} ({verified_pct:.1f}%)")

    print()

    # Coverage summary
    print("📈 ENRICHMENT COVERAGE")
    fields = [
        ('Website', metrics['with_website']),
        ('Mission', metrics['with_mission']),
        ('Donation Link', metrics['with_donate_url']),
    ]
    for name, count in sorted(fields, key=lambda x: x[1], reverse=True):
        pct = 100 * count / metrics['total_orgs'] if metrics['total_orgs'] else 0
        bar = "█" * int(pct / 2.5)
        print(f"  {name:15} {bar:20} {pct:5.1f}%")

    print()
    print("=" * 70)

def log_run():
    """Save current metrics snapshot for trend tracking."""
    metrics = get_db_metrics()
    if not metrics:
        return

    metrics['timestamp'] = datetime.now().isoformat()
    filename = METRICS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Metrics logged to {filename.name}")

if __name__ == '__main__':
    if '--log-run' in sys.argv:
        log_run()
    else:
        show_metrics()
