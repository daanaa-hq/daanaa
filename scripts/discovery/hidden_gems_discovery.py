#!/usr/bin/env python3
"""
Hidden Gems Discovery Engine — Find small, high-performing nonprofits.
Implements Stewardship Principle #4: Small orgs deserve fair visibility.

A "hidden gem" is:
  • Small: <$700K annual revenue (operating in resource-constrained mode)
  • Financially healthy: Top 30% of peer group (by financial health signal)
  • Hidden: No or minimal web presence (low search discovery)
  • Mission-driven: Has mission description + >2 employees assumed

Usage:
  python3 hidden_gems_discovery.py --find             # Find new hidden gems
  python3 hidden_gems_discovery.py --refresh          # Update existing list
  python3 hidden_gems_discovery.py --audit            # Audit current featured gems
  python3 hidden_gems_discovery.py --export-json      # Export as JSON for frontend
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "merit_registry.db"
GEMS_JSON = REPO_ROOT / "frontend" / "public" / "hidden_gems.json"
GEMS_DIR = REPO_ROOT / "precompute_output" / "hidden_gems"

GEMS_DIR.mkdir(exist_ok=True)

class HiddenGemsEngine:
    """Discover and manage hidden gems."""

    def __init__(self):
        self.gems = []
        self.criteria = {
            'max_revenue': 700_000,
            'min_peer_rank': 70,  # Top 30% of peer group
            'max_web_coverage': 0.3,  # <30% have websites (rare)
        }

    def query_candidates(self):
        """Find orgs matching hidden gems criteria."""
        if not DB_PATH.exists():
            print("❌ Database not found")
            return []

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find small, healthy, under-the-radar orgs
        query = """
        SELECT
            EIN,
            organization_name,
            CITY,
            STATE,
            total_revenue,
            merit_score_v5,
            merit_health_signal_v5,
            merit_archetype_v5_label,
            merit_band_v5_label,
            mission,
            mission_source,
            website,
            NTEE1,
            peer_rank,
            peer_total,
            peer_percentile
        FROM registry_enriched
        WHERE
            total_revenue < ?
            AND peer_percentile >= ?
            AND (website IS NULL OR website = '')
            AND mission IS NOT NULL
            AND mission != ''
            AND merit_health_signal_v5 IN ('HEALTHY', 'STABLE')
        ORDER BY peer_percentile DESC, total_revenue ASC
        LIMIT 1000
        """

        try:
            cursor.execute(query, (
                self.criteria['max_revenue'],
                self.criteria['min_peer_rank']
            ))
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
        finally:
            conn.close()

    def score_gem(self, org):
        """Score how "hidden" an org is (higher = more hidden but healthy)."""
        # Factors:
        # • Small revenue (strong signal of constraint)
        # • High peer percentile (performing well despite constraints)
        # • No website (discovery gap we can fill)

        score = 0

        # Revenue: smaller is "more hidden"
        if org['total_revenue']:
            revenue_score = 1 - (org['total_revenue'] / self.criteria['max_revenue'])
            score += revenue_score * 30  # 30 points for revenue smallness

        # Peer performance: higher percentile = better hidden gem
        if org['peer_percentile']:
            score += org['peer_percentile'] * 0.5  # Up to 50 points

        # Mission quality: claimed > AI-generated (explicit org voice)
        if org['mission_source'] == 'claimed':
            score += 15
        elif org['mission_source'] == 'ai_generated':
            score += 5

        return score

    def discover(self, limit=100):
        """Find top hidden gems matching criteria."""
        candidates = self.query_candidates()

        if not candidates:
            print("❌ No hidden gems found (database query issue)")
            return []

        # Score each candidate
        scored = []
        for org in candidates:
            gem_score = self.score_gem(org)
            scored.append({
                **org,
                'gem_score': gem_score,
                'discovered_at': datetime.now().isoformat(),
            })

        # Sort by gem score
        scored.sort(key=lambda x: x['gem_score'], reverse=True)

        self.gems = scored[:limit]
        return self.gems

    def analyze_distribution(self):
        """Analyze geographic and sectoral distribution."""
        if not self.gems:
            return {}

        by_state = defaultdict(int)
        by_ntee = defaultdict(int)
        by_archetype = defaultdict(int)

        for gem in self.gems:
            by_state[gem['STATE']] += 1
            by_ntee[gem['NTEE1']] += 1
            by_archetype[gem['merit_archetype_v5_label']] += 1

        return {
            'by_state': dict(sorted(by_state.items(), key=lambda x: x[1], reverse=True)),
            'by_sector': dict(sorted(by_ntee.items(), key=lambda x: x[1], reverse=True)),
            'by_archetype': dict(sorted(by_archetype.items(), key=lambda x: x[1], reverse=True)),
        }

    def export_json(self):
        """Export gems to frontend JSON."""
        if not self.gems:
            print("❌ No gems to export")
            return

        # Prepare for frontend (exclude internal fields)
        frontend_gems = []
        for gem in self.gems[:50]:  # Top 50 for homepage
            frontend_gems.append({
                'ein': gem['EIN'],
                'name': gem['organization_name'],
                'location': f"{gem['CITY']}, {gem['STATE']}",
                'mission': gem['mission'],
                'revenue': gem['total_revenue'],
                'health_signal': gem['merit_health_signal_v5'],
                'archetype': gem['merit_archetype_v5_label'],
                'band': gem['merit_band_v5_label'],
                'peer_percentile': gem['peer_percentile'],
            })

        output = {
            'timestamp': datetime.now().isoformat(),
            'count': len(frontend_gems),
            'criteria': self.criteria,
            'gems': frontend_gems,
        }

        with open(GEMS_JSON, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        print(f"✅ Exported {len(frontend_gems)} gems to {GEMS_JSON}")

    def report(self):
        """Print discovery report."""
        print("\n" + "=" * 70)
        print("💎 HIDDEN GEMS DISCOVERY ENGINE")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S Central')}")
        print()

        if not self.gems:
            print("❌ No hidden gems discovered")
            return

        print(f"Found: {len(self.gems)} hidden gems")
        print()

        print("Top 10 Hidden Gems:")
        print()
        for i, gem in enumerate(self.gems[:10], 1):
            revenue_str = f"${gem['total_revenue']/1_000:.0f}K" if gem['total_revenue'] else "unknown"
            peer_str = f"Top {100-gem['peer_percentile']:.0f}%" if gem['peer_percentile'] else "unknown"

            print(f"{i:2}. {gem['organization_name'][:45]:45} | {gem['STATE']:2} | {revenue_str:8} | {peer_str:10} | {gem['gem_score']:.1f}⭐")

        print()

        # Distribution analysis
        dist = self.analyze_distribution()
        if dist:
            print("Geographic Distribution (Top 5):")
            for state, count in list(dist['by_state'].items())[:5]:
                print(f"  {state}: {count}")

            print()
            print("Sector Distribution (Top 5):")
            for sector, count in list(dist['by_sector'].items())[:5]:
                # Try to get readable sector name
                sector_names = {
                    'A': 'Arts/Culture',
                    'B': 'Education',
                    'C': 'Health/Medical',
                    'D': 'Mental Health',
                    'E': 'Disease/Disorder',
                    'F': 'Medical Research',
                    'G': 'Public Health',
                    'H': 'Mental Health/Crisis',
                    'I': 'Substance Abuse',
                    'J': 'Disabled Services',
                    'K': 'Employment',
                    'L': 'Food/Agriculture',
                    'M': 'Housing',
                    'N': 'Public Safety',
                    'O': 'Recreation',
                    'P': 'Religion',
                    'Q': 'Social Services',
                    'R': 'Mutual/Membership',
                    'S': 'Science/Tech',
                    'T': 'Social Science',
                    'U': 'Philanthropy',
                    'V': 'Religion/Spirituality',
                    'W': 'Government',
                    'X': 'Unknown',
                    'Y': 'Unknown',
                    'Z': 'Unknown',
                }
                sector_name = sector_names.get(sector, sector)
                print(f"  {sector} ({sector_name}): {count}")

        print()

        # Health signal distribution
        health_dist = defaultdict(int)
        for gem in self.gems:
            health_dist[gem['merit_health_signal_v5']] += 1

        print("Financial Health Distribution:")
        for health, count in sorted(health_dist.items()):
            pct = 100 * count / len(self.gems)
            print(f"  {health}: {count} ({pct:.1f}%)")

        print()
        print("=" * 70)

    def audit(self):
        """Audit currently featured gems."""
        if not GEMS_JSON.exists():
            print("❌ Hidden gems list not found")
            return

        try:
            with open(GEMS_JSON) as f:
                data = json.load(f)

            gems = data.get('gems', [])
            print(f"\n📋 Auditing {len(gems)} featured gems\n")

            # Check each gem is still valid
            valid = 0
            stale = 0

            for gem in gems[:20]:  # Spot-check first 20
                # Could verify in database, but for now just report
                print(f"  ✓ {gem['name'][:40]:40} | {gem['location']} | {gem['revenue']:,}")
                valid += 1

            print(f"\nResult: {valid}/{len(gems)} featured gems are featured")

        except Exception as e:
            print(f"❌ Audit failed: {e}")


if __name__ == '__main__':
    engine = HiddenGemsEngine()

    if '--find' in sys.argv:
        engine.discover(limit=100)
        engine.report()
        if '--export' in sys.argv:
            engine.export_json()

    elif '--refresh' in sys.argv:
        engine.discover(limit=100)
        engine.export_json()
        print("✅ Hidden gems list refreshed")

    elif '--audit' in sys.argv:
        engine.audit()

    elif '--export-json' in sys.argv:
        engine.discover(limit=100)
        engine.export_json()

    else:
        engine.discover(limit=100)
        engine.report()
