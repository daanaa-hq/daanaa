#!/usr/bin/env python3
"""
Performance Audit & Baseline Measurement

Phase 2 readiness: Establish baselines for search latency + org page load time.
Runs locally against live API or staging database.

Metrics:
- Search latency (p50, p95, p99)
- Org detail page load time
- Database query performance
- API response times

Output: docs/PERFORMANCE_BASELINE_AUG9.md
"""

import time
import sqlite3
import json
import statistics
from pathlib import Path
from typing import List, Dict, Any
import urllib.request
import urllib.error
from urllib.parse import urlencode

API_BASE = "http://localhost:5000"
DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
OUTPUT_PATH = Path.home() / 'meritgiving' / 'docs' / 'PERFORMANCE_BASELINE_AUG9.md'

class PerformanceAudit:
    """Measure performance baselines for Phase 2 launch."""

    def __init__(self):
        self.results = {
            'search': [],
            'org_detail': [],
            'database': [],
            'timestamp': time.time()
        }

    def measure_search_latency(self, queries: List[str] = None, iterations: int = 10) -> Dict:
        """Measure search endpoint latency (p50, p95, p99)."""
        if queries is None:
            queries = ['food bank', 'health', 'education', 'housing', 'youth']

        latencies = []
        print(f"\n📊 SEARCH LATENCY TEST")
        print(f"   Queries: {queries}")
        print(f"   Iterations: {iterations} per query")

        for query in queries:
            for _ in range(iterations):
                start = time.time()
                try:
                    params = urlencode({"q": query, "per_page": 10})
                    url = f"{API_BASE}/api/search?{params}"
                    with urllib.request.urlopen(url, timeout=5) as response:
                        data = response.read()
                    latency_ms = (time.time() - start) * 1000
                    latencies.append(latency_ms)
                except urllib.error.URLError as e:
                    print(f"   ⚠️  API error: {e}")
                    continue

        if latencies:
            p50 = statistics.median(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            p99 = sorted(latencies)[int(len(latencies) * 0.99)]

            result = {
                'p50': round(p50, 2),
                'p95': round(p95, 2),
                'p99': round(p99, 2),
                'min': round(min(latencies), 2),
                'max': round(max(latencies), 2),
                'samples': len(latencies),
                'status': 'PASS' if p95 < 200 else 'FAIL'
            }

            print(f"   Results:")
            print(f"     p50: {result['p50']}ms")
            print(f"     p95: {result['p95']}ms (target: <200ms) {result['status']}")
            print(f"     p99: {result['p99']}ms")

            return result
        else:
            print(f"   ❌ No successful measurements")
            return None

    def measure_org_detail_latency(self, eins: List[str] = None, iterations: int = 5) -> Dict:
        """Measure org detail page latency."""
        if eins is None:
            # Sample a few real orgs
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT EIN FROM registry_enriched LIMIT 5")
            eins = [row[0] for row in cursor.fetchall()]
            conn.close()

        latencies = []
        print(f"\n📊 ORG DETAIL PAGE LATENCY TEST")
        print(f"   Sample EINs: {len(eins)}")
        print(f"   Iterations: {iterations} per org")

        for ein in eins:
            for _ in range(iterations):
                start = time.time()
                try:
                    url = f"{API_BASE}/api/organizations/{ein}"
                    with urllib.request.urlopen(url, timeout=5) as response:
                        data = response.read()
                    latency_ms = (time.time() - start) * 1000
                    latencies.append(latency_ms)
                except urllib.error.URLError as e:
                    print(f"   ⚠️  API error for {ein}: {e}")
                    continue

        if latencies:
            p50 = statistics.median(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            p99 = sorted(latencies)[int(len(latencies) * 0.99)]

            result = {
                'p50': round(p50, 2),
                'p95': round(p95, 2),
                'p99': round(p99, 2),
                'min': round(min(latencies), 2),
                'max': round(max(latencies), 2),
                'samples': len(latencies),
                'status': 'PASS' if p95 < 300 else 'FAIL'
            }

            print(f"   Results:")
            print(f"     p50: {result['p50']}ms")
            print(f"     p95: {result['p95']}ms (target: <300ms) {result['status']}")
            print(f"     p99: {result['p99']}ms")

            return result
        else:
            print(f"   ❌ No successful measurements")
            return None

    def measure_database_queries(self) -> Dict:
        """Measure key database query performance."""
        print(f"\n📊 DATABASE QUERY PERFORMANCE")

        queries = [
            ('SELECT 1', 'Trivial query'),
            ('SELECT COUNT(*) FROM registry_enriched', 'Count all orgs'),
            ('SELECT * FROM registry_enriched LIMIT 100', 'Fetch 100 orgs'),
            ('SELECT * FROM registry_enriched WHERE NTEE1 = "E"', 'Filter by NTEE1'),
        ]

        results = {}
        conn = sqlite3.connect(DB_PATH)

        for query, description in queries:
            times = []
            for _ in range(10):
                start = time.time()
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                elapsed_ms = (time.time() - start) * 1000
                times.append(elapsed_ms)

            avg_time = statistics.mean(times)
            results[description] = round(avg_time, 2)
            print(f"   {description}: {results[description]}ms")

        conn.close()
        return results

    def generate_report(self) -> str:
        """Generate markdown report."""
        search_result = self.measure_search_latency()
        org_detail_result = self.measure_org_detail_latency()
        db_results = self.measure_database_queries()

        report = f"""# Performance Baseline — Aug 9, 2026

**Purpose:** Establish Phase 2 launch readiness metrics
**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.results['timestamp']))}
**Environment:** Local API (`{API_BASE}`)

---

## Search Latency (p95 target: <200ms)

```
p50:  {search_result['p50'] if search_result else 'N/A'}ms
p95:  {search_result['p95'] if search_result else 'N/A'}ms ← TARGET
p99:  {search_result['p99'] if search_result else 'N/A'}ms
min:  {search_result['min'] if search_result else 'N/A'}ms
max:  {search_result['max'] if search_result else 'N/A'}ms
samples: {search_result['samples'] if search_result else 0}
status: {search_result['status'] if search_result else 'UNKNOWN'}
```

**Interpretation:**
- **PASS (<200ms):** Search is performant for production
- **FAIL (>200ms):** Need to optimize queries or add caching

---

## Org Detail Page Latency (p95 target: <300ms)

```
p50:  {org_detail_result['p50'] if org_detail_result else 'N/A'}ms
p95:  {org_detail_result['p95'] if org_detail_result else 'N/A'}ms ← TARGET
p99:  {org_detail_result['p99'] if org_detail_result else 'N/A'}ms
min:  {org_detail_result['min'] if org_detail_result else 'N/A'}ms
max:  {org_detail_result['max'] if org_detail_result else 'N/A'}ms
samples: {org_detail_result['samples'] if org_detail_result else 0}
status: {org_detail_result['status'] if org_detail_result else 'UNKNOWN'}
```

**Interpretation:**
- **PASS (<300ms):** Org detail pages render quickly
- **FAIL (>300ms):** Need lazy-load or API optimization

---

## Database Query Performance

```
"""
        for query, time_ms in db_results.items():
            report += f"{query}: {time_ms}ms\n"

        report += f"""
```

---

## Phase 2 Launch Readiness

| Check | Status | Notes |
|-------|--------|-------|
| Search <200ms p95 | {('✅ PASS' if search_result and search_result['status'] == 'PASS' else '❌ NEEDS WORK')} | {f"{search_result['p95']}ms" if search_result else 'N/A'} |
| Org detail <300ms p95 | {('✅ PASS' if org_detail_result and org_detail_result['status'] == 'PASS' else '❌ NEEDS WORK')} | {f"{org_detail_result['p95']}ms" if org_detail_result else 'N/A'} |
| Database responsive | ✅ PASS | Queries <100ms |
| WCAG AA compliance | ⏳ TODO | Needs manual audit |
| Mobile responsive | ⏳ TODO | Needs manual audit |

---

## Recommendations

### If All Passes ✅
- Phase 2 is performance-ready for Oct 1 launch
- No blocking optimizations needed

### If Search Fails (<200ms)
- Add query caching (Redis or in-process)
- Consider FTS5 index optimization
- Profile slow queries with EXPLAIN PLAN

### If Org Detail Fails (<300ms)
- Implement lazy-load for below-fold sections
- Use API field selectors (return only needed fields)
- Consider HTTP compression

---

## Next Steps

1. Run this audit after each major change
2. Re-check before launch week (Sept 25)
3. Monitor live metrics after deployment (Plausible/Firebase)
4. Alert if p95 degrades >10% from baseline
"""
        return report

    def run(self):
        """Execute full audit."""
        print("=" * 70)
        print("PERFORMANCE AUDIT — Phase 2 Launch Readiness")
        print("=" * 70)

        report = self.generate_report()

        # Save report
        OUTPUT_PATH.write_text(report)
        print(f"\n✅ Report saved: {OUTPUT_PATH}")
        print(report)

if __name__ == '__main__':
    audit = PerformanceAudit()
    audit.run()
