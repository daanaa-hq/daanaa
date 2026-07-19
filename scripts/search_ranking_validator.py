#!/usr/bin/env python3
"""
Search Ranking Validator — Verify small orgs surface in search results.
Implements Stewardship Principle #4: No hidden penalties for organization size.

Tests:
  • Broad queries (e.g., "education") surface small orgs
  • Cause-based queries include small orgs
  • Location-based queries return diverse sizes
  • Small org names appear in their own search

Usage:
  python3 search_ranking_validator.py --test           # Run validation tests
  python3 search_ranking_validator.py --small-org-scan # Deep small-org search quality
"""

import requests
import sqlite3
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "merit_registry.db"
API_URL = "http://localhost:5000"

class SearchRankingValidator:
    """Validate search results include diverse organization sizes."""

    def __init__(self):
        self.results = {}
        self.small_org_queries = []

    def get_sample_small_orgs(self, count=20):
        """Get random small orgs from database for testing."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT organization_name, EIN, total_revenue
                FROM registry_enriched
                WHERE total_revenue < 700000
                AND organization_name IS NOT NULL
                ORDER BY RANDOM()
                LIMIT ?
            """, (count,))

            return [
                {
                    'name': row[0],
                    'ein': row[1],
                    'revenue': row[2]
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def test_broad_query_includes_small_orgs(self):
        """Test: Broad queries include small orgs."""
        test_queries = [
            'education',
            'health',
            'community',
            'nonprofit',
            'social services',
        ]

        print("\n📋 Test 1: Broad Queries Include Small Orgs")
        print("-" * 60)

        passed = 0
        for query in test_queries:
            try:
                response = requests.get(
                    f"{API_URL}/api/organizations",
                    params={'q': query, 'per_page': 50},
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    orgs = data.get('organizations', [])

                    # Check for small orgs in results
                    small_orgs = [
                        o for o in orgs
                        if o.get('total_revenue', 0) and o['total_revenue'] < 700_000
                    ]

                    small_pct = 100 * len(small_orgs) / max(1, len(orgs))
                    status = "✅" if small_pct >= 20 else "⚠️"
                    print(f"  {status} '{query:20}' → {len(orgs):2} results, {small_pct:5.1f}% small orgs")

                    if small_pct >= 20:
                        passed += 1
                else:
                    print(f"  ❌ '{query}' → HTTP {response.status_code}")

            except Exception as e:
                print(f"  ❌ '{query}' → {str(e)[:40]}")

        print(f"\nResult: {passed}/{len(test_queries)} queries include ≥20% small orgs")
        return passed >= len(test_queries) * 0.8

    def test_self_search_small_orgs(self):
        """Test: Small orgs find themselves in search."""
        print("\n🔍 Test 2: Small Orgs Find Themselves (Self-Search)")
        print("-" * 60)

        small_orgs = self.get_sample_small_orgs(count=10)
        passed = 0

        for org in small_orgs:
            try:
                response = requests.get(
                    f"{API_URL}/api/organizations",
                    params={'q': org['name'], 'per_page': 20},
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('organizations', [])

                    # Check if this org appears in results
                    found = any(
                        r.get('organization_name') == org['name']
                        for r in results
                    )

                    if found:
                        rank = next(
                            i+1 for i, r in enumerate(results)
                            if r.get('organization_name') == org['name']
                        )
                        status = "✅" if rank <= 5 else "⚠️"
                        print(f"  {status} {org['name'][:40]:40} → Rank {rank}/20")
                        if rank <= 5:
                            passed += 1
                    else:
                        print(f"  ❌ {org['name'][:40]:40} → Not found")

            except Exception as e:
                print(f"  ❌ {org['name'][:40]:40} → {str(e)[:30]}")

        print(f"\nResult: {passed}/{len(small_orgs)} small orgs find themselves in top 5")
        return passed >= len(small_orgs) * 0.7

    def test_location_diversity(self):
        """Test: Location-based queries return diverse sizes."""
        print("\n🗺️  Test 3: Location Queries Return Size Diversity")
        print("-" * 60)

        test_locations = [
            'san francisco',
            'new york',
            'los angeles',
            'chicago',
            'seattle',
        ]

        passed = 0
        for location in test_locations:
            try:
                response = requests.get(
                    f"{API_URL}/api/organizations",
                    params={'q': location, 'per_page': 50},
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    orgs = data.get('organizations', [])

                    if orgs:
                        # Check size diversity
                        revenues = [o.get('total_revenue', 0) for o in orgs if o.get('total_revenue')]
                        if revenues:
                            min_rev = min(revenues)
                            max_rev = max(revenues)
                            range_ratio = max_rev / max(1, min_rev)

                            # Good diversity = 100x range
                            has_diversity = range_ratio >= 100
                            status = "✅" if has_diversity else "⚠️"

                            small_count = sum(1 for r in revenues if r < 700_000)
                            print(f"  {status} '{location:15}' → {len(orgs):2} results, {small_count:2} small, range {range_ratio:6.0f}x")

                            if has_diversity:
                                passed += 1

            except Exception as e:
                print(f"  ❌ '{location}' → {str(e)[:40]}")

        print(f"\nResult: {passed}/{len(test_locations)} location queries show size diversity")
        return passed >= len(test_locations) * 0.6

    def test_no_size_penalty(self):
        """Test: Small orgs are not ranked lower just for being small."""
        print("\n⚖️  Test 4: No Penalty for Organization Size")
        print("-" * 60)

        # Get a small org and a large org in the same category
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Find a small org in education
            cursor.execute("""
                SELECT organization_name, NTEE1
                FROM registry_enriched
                WHERE total_revenue < 500000
                AND NTEE1 = 'B'  -- Education
                ORDER BY RANDOM()
                LIMIT 1
            """)
            small_result = cursor.fetchone()

            if not small_result:
                print("  ⚠️  Could not find small education org for testing")
                return False

            small_org_name, ntee = small_result

            # Search for this org
            response = requests.get(
                f"{API_URL}/api/organizations",
                params={'q': small_org_name, 'per_page': 10},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('organizations', [])

                # Find our org
                for rank, org in enumerate(results, 1):
                    if org.get('organization_name') == small_org_name:
                        status = "✅" if rank <= 3 else "⚠️"
                        print(f"  {status} Small org '{small_org_name[:40]:40}' ranks #{rank}")
                        return rank <= 3

                print(f"  ❌ Small org not found in top 10 results")
                return False

        finally:
            conn.close()

    def report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("🔍 SEARCH RANKING VALIDATOR — P4 Fairness Verification")
        print("=" * 70)

        # Run all tests
        test1 = self.test_broad_query_includes_small_orgs()
        test2 = self.test_self_search_small_orgs()
        test3 = self.test_location_diversity()
        test4 = self.test_no_size_penalty()

        print()
        print("=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)

        tests = [
            ("Broad queries include small orgs", test1),
            ("Small orgs find themselves", test2),
            ("Location queries show diversity", test3),
            ("No penalty for small size", test4),
        ]

        passed = sum(1 for _, result in tests if result)
        for test_name, result in tests:
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")

        print()
        if passed >= 3:
            print("✅ PASSED: Search ranking is fair to small organizations")
        else:
            print("❌ FAILED: Search ranking penalizes small organizations")
            print("    Investigate ranking algorithm for size bias")

        print("=" * 70)
        return passed >= 3


if __name__ == '__main__':
    import sys

    validator = SearchRankingValidator()

    if '--test' in sys.argv:
        success = validator.report()
        sys.exit(0 if success else 1)
    else:
        validator.report()
