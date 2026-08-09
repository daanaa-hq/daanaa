#!/usr/bin/env python3
"""
Daanaa V6 Comprehensive Performance Audit

Profiles database queries, API endpoints, and scoring pipeline.
Generates baseline and identifies optimization opportunities.

Run: python3 scripts/performance_audit_comprehensive.py
"""

import sqlite3
import time
import statistics
import json
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

class PerformanceAudit:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "database": str(db_path),
            "queries": {}
        }

    def connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def run_query(self, name, query, iterations=5):
        """Profile a query multiple times."""
        times = []

        for i in range(iterations):
            start = time.time()
            cursor = self.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
            cursor.close()

        stats = {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "iterations": iterations,
            "result_count": len(results) if results else 0,
            "times_ms": times,
            "min_ms": min(times),
            "max_ms": max(times),
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }

        self.results["queries"][name] = stats
        return stats

    def audit_basic_queries(self):
        """Profile basic queries."""
        print("Profiling basic queries...")

        self.run_query(
            "count_all_orgs",
            "SELECT COUNT(*) FROM registry_enriched"
        )

        self.run_query(
            "fetch_100_orgs",
            "SELECT * FROM registry_enriched LIMIT 100",
            iterations=3
        )

        self.run_query(
            "fetch_by_ein",
            "SELECT * FROM registry_enriched WHERE EIN = '391855543'",
            iterations=10
        )

    def audit_search_queries(self):
        """Profile FTS search queries."""
        print("Profiling search queries...")

        # Check if FTS is available
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='org_fts'")
        has_fts = cursor.fetchone() is not None

        if not has_fts:
            print("  FTS5 index not available, skipping search audit")
            return

        self.run_query(
            "fts_search_health",
            "SELECT ein FROM org_fts WHERE org_fts MATCH 'health' LIMIT 2000",
            iterations=5
        )

        self.run_query(
            "fts_search_nonprofit",
            "SELECT ein FROM org_fts WHERE org_fts MATCH 'nonprofit' LIMIT 2000",
            iterations=5
        )

    def audit_scoring_queries(self):
        """Profile scoring-related queries."""
        print("Profiling scoring queries...")

        self.run_query(
            "count_scored_orgs",
            "SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL",
            iterations=3
        )

        self.run_query(
            "filter_by_ntee",
            "SELECT COUNT(*) FROM registry_enriched WHERE NTEE1 = 'D'",
            iterations=3
        )

        self.run_query(
            "top_100_by_score",
            "SELECT EIN, organization_name, merit_score FROM registry_enriched WHERE merit_score IS NOT NULL ORDER BY merit_score DESC LIMIT 100",
            iterations=3
        )

    def audit_peer_group_queries(self):
        """Profile peer group comparison queries."""
        print("Profiling peer group queries...")

        self.run_query(
            "peer_group_stats",
            """
            SELECT
                NTEE1,
                COUNT(*) as count,
                AVG(merit_score) as avg_score,
                MIN(merit_score) as min_score,
                MAX(merit_score) as max_score
            FROM registry_enriched
            WHERE merit_score IS NOT NULL
            GROUP BY NTEE1
            """,
            iterations=3
        )

    def audit_index_coverage(self):
        """Check what indexes exist."""
        print("Analyzing index coverage...")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, sql FROM sqlite_master
            WHERE type='index' AND tbl_name='registry_enriched'
            ORDER BY name
        """)

        indexes = cursor.fetchall()
        self.results["indexes"] = [
            {"name": idx[0], "sql": idx[1]} for idx in indexes
        ]

        print(f"  Found {len(indexes)} indexes on registry_enriched")
        for idx in indexes:
            print(f"    - {idx[0]}")

    def analyze_table_stats(self):
        """Get table statistics."""
        print("Gathering table statistics...")

        cursor = self.conn.cursor()
        cursor.execute("SELECT page_count * page_size as size_bytes FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM registry_enriched")
        org_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT
                COUNT(CASE WHEN merit_score IS NOT NULL THEN 1 END) as scored,
                COUNT(CASE WHEN merit_score_v5 IS NOT NULL THEN 1 END) as scored_v5,
                COUNT(CASE WHEN website IS NOT NULL THEN 1 END) as with_website,
                COUNT(CASE WHEN donate_url IS NOT NULL THEN 1 END) as with_donate_url
            FROM registry_enriched
        """)

        coverage = cursor.fetchone()

        self.results["table_stats"] = {
            "db_size_mb": db_size / (1024 * 1024),
            "total_orgs": org_count,
            "v4_scored": coverage[0],
            "v5_scored": coverage[1],
            "with_website": coverage[2],
            "with_donate_url": coverage[3],
        }

        print(f"  Database size: {db_size / (1024*1024):.1f} MB")
        print(f"  Total orgs: {org_count}")
        print(f"  V4 scored: {coverage[0]}")
        print(f"  V5 scored: {coverage[1]}")

    def run_audit(self):
        """Execute full audit."""
        try:
            self.connect()

            print("=" * 60)
            print("DAANAA V6 PERFORMANCE AUDIT")
            print("=" * 60)

            self.audit_index_coverage()
            self.analyze_table_stats()
            self.audit_basic_queries()
            self.audit_search_queries()
            self.audit_scoring_queries()
            self.audit_peer_group_queries()

            self.close()
            return self.results

        except Exception as e:
            print(f"ERROR: {e}")
            raise

    def close(self):
        """Close connection."""
        if self.conn:
            self.conn.close()

    def print_summary(self):
        """Print summary report."""
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)

        print("\nQuery Performance (ms):")
        for name, stats in self.results["queries"].items():
            print(f"  {name}:")
            print(f"    Mean: {stats['mean_ms']:.2f}ms")
            print(f"    Median: {stats['median_ms']:.2f}ms")
            print(f"    Range: {stats['min_ms']:.2f}-{stats['max_ms']:.2f}ms")
            print(f"    Results: {stats['result_count']}")

        print("\nTable Statistics:")
        for stat_name, stat_value in self.results["table_stats"].items():
            print(f"  {stat_name}: {stat_value}")

    def save_results(self, output_path="docs/performance_baseline_v6.json"):
        """Save results to JSON."""
        path = Path(output_path)
        with open(path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to {output_path}")
        return path

if __name__ == "__main__":
    audit = PerformanceAudit(DB_PATH)
    results = audit.run_audit()
    audit.print_summary()
    audit.save_results()
