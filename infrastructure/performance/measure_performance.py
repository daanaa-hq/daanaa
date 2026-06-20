#!/usr/bin/env python3
"""
Performance profiler for Daanaa — measures query latency, cache effectiveness, and bottlenecks.

Benchmarks:
  - API endpoints (directory, org detail, search)
  - Database queries (indexed vs unindexed)
  - Search index (FTS5 and embeddings)
  - Cache hit rates (response cache)

Generates:
  - Latency percentiles (p50, p95, p99)
  - Throughput (requests/sec)
  - Cache effectiveness
  - Hotspot identification

Usage:
  python3 infrastructure/performance/measure_performance.py [--profile-queries]
"""

import time
import sqlite3
import subprocess
import json
import statistics
from datetime import datetime
from typing import List, Tuple

DB_PATH = "data/merit_registry.db"
API_BASE = "http://localhost:5000"

class PerformanceProfiler:
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "api": {},
            "database": {},
            "cache": {},
        }

    def benchmark_api_endpoint(self, path: str, name: str, iterations: int = 10):
        """Measure API endpoint latency."""
        times = []

        for _ in range(iterations):
            start = time.time()
            try:
                subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", f"{API_BASE}{path}"],
                    timeout=30,
                    capture_output=True
                )
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            except:
                pass

        if times:
            self.results["api"][name] = {
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2),
                "mean_ms": round(statistics.mean(times), 2),
                "median_ms": round(statistics.median(times), 2),
                "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 2) if len(times) > 20 else None,
                "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 2) if len(times) > 100 else None,
                "iterations": len(times),
            }

    def benchmark_db_queries(self):
        """Measure common database query patterns."""
        conn = sqlite3.connect(DB_PATH)

        queries = {
            "count_orgs": "SELECT COUNT(*) FROM registry_enriched",
            "top_10_revenue": "SELECT organization_name, total_revenue FROM registry_enriched ORDER BY total_revenue DESC LIMIT 10",
            "search_by_name": "SELECT * FROM registry_enriched WHERE organization_name LIKE '%cancer%' LIMIT 100",
            "category_filter": "SELECT * FROM registry_enriched WHERE NTEE1 = 'E' LIMIT 100",
            "scored_orgs": "SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL",
            "fts_search": "SELECT * FROM org_fts WHERE org_fts MATCH 'cancer*' LIMIT 100",
            "percentile_calc": "SELECT PERCENTILE(merit_score) FROM registry_enriched WHERE NTEE1 = 'E'",
        }

        for name, sql in queries.items():
            times = []
            for _ in range(5):
                start = time.time()
                try:
                    conn.execute(sql).fetchall()
                    elapsed = (time.time() - start) * 1000
                    times.append(elapsed)
                except:
                    pass

            if times:
                self.results["database"][name] = {
                    "min_ms": round(min(times), 3),
                    "max_ms": round(max(times), 3),
                    "mean_ms": round(statistics.mean(times), 3),
                    "iterations": len(times),
                }

        conn.close()

    def analyze_cache_effectiveness(self):
        """Check if response cache is working."""
        # Make the same request twice and compare times
        times = []

        for i in range(2):
            start = time.time()
            subprocess.run(
                ["curl", "-s", "-o", "/dev/null",
                 f"{API_BASE}/api/organizations?page=1&per_page=25"],
                timeout=30,
                capture_output=True
            )
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        # Second request should be faster (cached)
        if len(times) == 2:
            speedup = times[0] / times[1] if times[1] > 0 else 0
            self.results["cache"]["directory_cache_speedup"] = round(speedup, 2)

            if speedup > 1.2:
                self.results["cache"]["status"] = "working"
            else:
                self.results["cache"]["status"] = "check_response_cache"

    def generate_report(self):
        """Print formatted performance report."""
        print("\n" + "="*70)
        print("  PERFORMANCE BASELINE REPORT")
        print("="*70 + "\n")

        print("API ENDPOINT LATENCY (ms)")
        print("-" * 70)
        for name, metrics in self.results["api"].items():
            print(f"\n{name}:")
            print(f"  Mean:   {metrics['mean_ms']} ms")
            print(f"  Median: {metrics['median_ms']} ms")
            if metrics.get('p95_ms'):
                print(f"  P95:    {metrics['p95_ms']} ms")
            if metrics.get('p99_ms'):
                print(f"  P99:    {metrics['p99_ms']} ms")

        print("\n\nDATABASE QUERY LATENCY (ms)")
        print("-" * 70)
        for name, metrics in self.results["database"].items():
            print(f"{name:30s}: {metrics['mean_ms']:8.3f} ms (min: {metrics['min_ms']}, max: {metrics['max_ms']})")

        print("\n\nCACHE EFFECTIVENESS")
        print("-" * 70)
        if self.results["cache"].get("directory_cache_speedup"):
            print(f"Directory cache speedup: {self.results['cache']['directory_cache_speedup']}x")
        print(f"Status: {self.results['cache'].get('status', 'unknown')}")

        print("\n" + "="*70 + "\n")

        # Save to JSON for trending
        with open("/tmp/daanaa_performance_baseline.json", "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"Full results saved to: /tmp/daanaa_performance_baseline.json")

    def run(self):
        """Run all performance benchmarks."""
        print("\nRunning performance benchmarks...")
        print("(This takes ~2 minutes)\n")

        print("[1/3] API endpoints...")
        self.benchmark_api_endpoint("/api/stats", "api_stats", iterations=5)
        self.benchmark_api_endpoint("/api/organizations?page=1&per_page=25", "directory_landing", iterations=5)
        self.benchmark_api_endpoint("/api/organizations?hidden_gem=1&page=1", "hidden_gems", iterations=5)
        self.benchmark_api_endpoint("/directory", "spa_directory", iterations=3)

        print("[2/3] Database queries...")
        self.benchmark_db_queries()

        print("[3/3] Cache effectiveness...")
        self.analyze_cache_effectiveness()

        self.generate_report()


if __name__ == "__main__":
    profiler = PerformanceProfiler()
    profiler.run()
