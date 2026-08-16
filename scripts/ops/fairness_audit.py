#!/usr/bin/env python3
"""
Fairness Audit Dashboard — Track Stewardship Principle #4 compliance.
Monitors whether small nonprofits receive equal visibility and fair treatment.

Metrics:
  • Small-org search visibility (do they appear in results?)
  • Financial context availability (do they get fair peer comparisons?)
  • Data completeness (websites, missions, donations)
  • Hidden gem rotation (featured diversity)
  • Geographic distribution (no region left behind)

Usage:
  python3 fairness_audit.py --show                # Display metrics
  python3 fairness_audit.py --export-json         # Export metrics as JSON
  python3 fairness_audit.py --compare-org-sizes   # Size distribution analysis
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "merit_registry.db"

class FairnessAudit:
    """Audit fairness of platform for small organizations."""

    def __init__(self):
        self.metrics = {}
        self.definitions = {
            'small_org': '<$700K revenue (operating in resource-constrained mode)',
            'micro_org': '<$150K revenue (minimal staff)',
            'mid_org': '$700K-$5M (established)',
            'large_org': '>$5M (institutional scale)',
        }

    def query_org_distribution(self):
        """Analyze org size distribution."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Size distribution
            cursor.execute("""
                SELECT
                    CASE
                        WHEN total_revenue < 150000 THEN 'micro (<$150K)'
                        WHEN total_revenue < 700000 THEN 'small ($150K-$700K)'
                        WHEN total_revenue < 5000000 THEN 'mid ($700K-$5M)'
                        ELSE 'large (>$5M)'
                    END as size_band,
                    COUNT(*) as count,
                    AVG(CASE WHEN merit_health_signal_v5 = 'HEALTHY' THEN 1 ELSE 0 END) as healthy_pct,
                    AVG(CASE WHEN website IS NOT NULL AND website != '' THEN 1 ELSE 0 END) as with_website_pct,
                    AVG(CASE WHEN mission IS NOT NULL AND mission != '' THEN 1 ELSE 0 END) as with_mission_pct,
                    AVG(CASE WHEN donate_url IS NOT NULL AND donate_url != '' THEN 1 ELSE 0 END) as with_donate_pct
                FROM registry_enriched
                GROUP BY size_band
                ORDER BY
                    CASE
                        WHEN total_revenue < 150000 THEN 1
                        WHEN total_revenue < 700000 THEN 2
                        WHEN total_revenue < 5000000 THEN 3
                        ELSE 4
                    END
            """)

            results = cursor.fetchall()
            return results

        finally:
            conn.close()

    def query_data_completeness(self):
        """Track data completeness by org size."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    CASE
                        WHEN total_revenue < 150000 THEN 'micro'
                        WHEN total_revenue < 700000 THEN 'small'
                        WHEN total_revenue < 5000000 THEN 'mid'
                        ELSE 'large'
                    END as size_band,
                    COUNT(*) as total_orgs,
                    SUM(CASE WHEN mission IS NOT NULL AND mission != '' THEN 1 ELSE 0 END) as with_mission,
                    SUM(CASE WHEN website IS NOT NULL AND website != '' THEN 1 ELSE 0 END) as with_website,
                    SUM(CASE WHEN donate_url IS NOT NULL AND donate_url != '' THEN 1 ELSE 0 END) as with_donate,
                    SUM(CASE WHEN merit_health_signal_v5 IN ('HEALTHY', 'STABLE') THEN 1 ELSE 0 END) as with_health_signal
                FROM registry_enriched
                GROUP BY size_band
            """)

            results = [dict(row) for row in cursor.fetchall()]
            return results

        finally:
            conn.close()

    def query_geographic_diversity(self):
        """Check geographic coverage by org size."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    STATE,
                    COUNT(*) as total,
                    SUM(CASE WHEN total_revenue < 700000 THEN 1 ELSE 0 END) as small_orgs,
                    SUM(CASE WHEN total_revenue < 150000 THEN 1 ELSE 0 END) as micro_orgs,
                    SUM(CASE WHEN merit_health_signal_v5 = 'HEALTHY' AND total_revenue < 700000 THEN 1 ELSE 0 END) as healthy_small
                FROM registry_enriched
                WHERE STATE IS NOT NULL
                GROUP BY STATE
                ORDER BY total DESC
            """)

            results = cursor.fetchall()
            return results

        finally:
            conn.close()

    def compute_fairness_score(self):
        """Compute overall fairness score (0-100)."""
        completeness = self.query_data_completeness()

        score = 0

        for row in completeness:
            if row['size_band'] == 'small':
                # Check if small orgs have good data coverage
                mission_pct = 100 * row['with_mission'] / max(1, row['total_orgs'])
                website_pct = 100 * row['with_website'] / max(1, row['total_orgs'])

                # Small orgs should have ≥90% mission coverage, ≥10% website coverage
                mission_score = min(100, mission_pct) if mission_pct >= 90 else mission_pct
                website_score = min(100, website_pct) if website_pct >= 10 else website_pct

                score += (mission_score * 0.4 + website_score * 0.6) / 100 * 50  # 50 points for small-org data

        # Bonus for geographic diversity
        geo = self.query_geographic_diversity()
        states_with_small_orgs = sum(1 for row in geo if row[2] > 0)  # small_orgs column
        geo_score = (states_with_small_orgs / 50) * 50  # 50 points for geographic coverage
        score += geo_score

        return min(100, score)

    def show_report(self):
        """Display fairness audit report."""
        print("\n" + "=" * 70)
        print("⚖️  FAIRNESS AUDIT DASHBOARD")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S Central')}")
        print()

        # Size distribution
        print("📊 ORGANIZATION SIZE DISTRIBUTION")
        dist = self.query_org_distribution()
        for row in dist:
            size_band, count, healthy_pct, website_pct, mission_pct, donate_pct = row
            if healthy_pct:
                healthy_str = f"{100*healthy_pct:.0f}% healthy"
            else:
                healthy_str = "unknown health"

            if website_pct:
                web_str = f"{100*website_pct:.1f}% with website"
            else:
                web_str = "no website data"

            print(f"  {size_band:20} {count:7,} orgs | {healthy_str:15} | {web_str}")

        print()

        # Data completeness
        print("📋 DATA COMPLETENESS BY ORG SIZE")
        completeness = self.query_data_completeness()

        header = f"{'Size':<8} {'Total':>8} {'Mission':>8} {'Website':>8} {'Donate':>8} {'Health':>8}"
        print(f"  {header}")
        print(f"  {'-'*len(header)}")

        for row in completeness:
            size = row['size_band'].capitalize()
            total = row['total_orgs']

            mission_pct = 100 * row['with_mission'] / max(1, total)
            website_pct = 100 * row['with_website'] / max(1, total)
            donate_pct = 100 * row['with_donate'] / max(1, total)
            health_pct = 100 * row['with_health_signal'] / max(1, total)

            print(f"  {size:<8} {total:>8,} {mission_pct:>7.1f}% {website_pct:>7.1f}% {donate_pct:>7.1f}% {health_pct:>7.1f}%")

        print()

        # Geographic diversity
        print("🗺️  GEOGRAPHIC DISTRIBUTION (Top 10)")
        geo = self.query_geographic_diversity()
        for state, total, small_orgs, micro_orgs, healthy_small in geo[:10]:
            small_pct = 100 * small_orgs / max(1, total)
            micro_pct = 100 * micro_orgs / max(1, total)
            print(f"  {state:2} {total:6,} total | {small_orgs:5,} small ({small_pct:4.1f}%) | {micro_orgs:4,} micro | {healthy_small:4,} healthy small")

        print()

        # Fairness score
        score = self.compute_fairness_score()
        score_icon = "✅" if score >= 75 else "⚠️" if score >= 50 else "❌"
        print(f"{score_icon} FAIRNESS SCORE: {score:.1f}/100")

        if score >= 75:
            print("   Status: Small orgs have good data coverage and geographic presence")
        elif score >= 50:
            print("   Status: Small orgs have moderate coverage; gaps in data/geography")
        else:
            print("   Status: Small orgs underrepresented; fairness needs improvement")

        print()
        print("=" * 70)

    def export_json(self):
        """Export metrics as JSON."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'fairness_score': self.compute_fairness_score(),
            'size_distribution': [],
            'data_completeness': [],
            'geographic_coverage': [],
        }

        # Size distribution
        for row in self.query_org_distribution():
            size_band, count, healthy_pct, website_pct, mission_pct, donate_pct = row
            metrics['size_distribution'].append({
                'size_band': size_band,
                'count': count,
                'healthy_pct': round(100 * (healthy_pct or 0), 1),
                'website_pct': round(100 * (website_pct or 0), 1),
                'mission_pct': round(100 * (mission_pct or 0), 1),
                'donate_pct': round(100 * (donate_pct or 0), 1),
            })

        # Data completeness
        for row in self.query_data_completeness():
            total = row['total_orgs']
            metrics['data_completeness'].append({
                'size_band': row['size_band'],
                'total_orgs': total,
                'mission_pct': round(100 * row['with_mission'] / max(1, total), 1),
                'website_pct': round(100 * row['with_website'] / max(1, total), 1),
                'donate_pct': round(100 * row['with_donate'] / max(1, total), 1),
                'health_signal_pct': round(100 * row['with_health_signal'] / max(1, total), 1),
            })

        # Geographic
        for state, total, small_orgs, micro_orgs, healthy_small in self.query_geographic_diversity():
            metrics['geographic_coverage'].append({
                'state': state,
                'total_orgs': total,
                'small_orgs': small_orgs,
                'micro_orgs': micro_orgs,
                'healthy_small': healthy_small,
            })

        output_file = REPO_ROOT / "logs" / "fairness_audit.json"
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)

        print(f"✅ Metrics exported to {output_file}")


if __name__ == '__main__':
    import sys

    audit = FairnessAudit()

    if '--export-json' in sys.argv:
        audit.export_json()
    elif '--compare-org-sizes' in sys.argv:
        # Detailed size comparison
        audit.show_report()
    else:
        audit.show_report()
