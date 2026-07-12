#!/usr/bin/env python3
"""
T12 Phase 1: Search metrics analysis — zero-result rate and pattern discovery.

Queries the analytics tables to report:
1. Zero-result rate baseline (past 7/14 days)
2. Top 20 failing queries
3. Search patterns (avg query length, filter usage)

Usage:
    python3 scripts/analyze_search_metrics.py --days 7
    python3 scripts/analyze_search_metrics.py --days 14 --show-queries
"""

import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'

def analyze_zero_result_rate(days=7):
    """Analyze zero-result rate over N days."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    # Total searches
    total = db.execute(
        "SELECT SUM(COUNT(*)) as total FROM analytics_search_metrics WHERE day >= ?",
        (cutoff,)
    ).fetchone()['total'] or 0

    # Zero-result searches
    zero = db.execute(
        "SELECT COUNT(*) as count FROM analytics_search_metrics WHERE day >= ? AND zero_results = 1",
        (cutoff,)
    ).fetchone()['count'] or 0

    rate = (zero / total * 100) if total > 0 else 0
    db.close()

    return total, zero, rate

def top_failing_queries(limit=20, days=7):
    """Get top N queries that returned zero results."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    queries = db.execute(
        """SELECT query, occurrence_count, query_length, filters_applied, search_mode
           FROM analytics_zero_result_queries
           WHERE day >= ?
           ORDER BY occurrence_count DESC
           LIMIT ?""",
        (cutoff, limit)
    ).fetchall()
    db.close()

    return [(row['query'], row['occurrence_count'], row['query_length'], row['filters_applied'], row['search_mode']) for row in queries]

def search_patterns(days=7):
    """Analyze search patterns (query length, filter usage)."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    stats = db.execute(
        """SELECT
             AVG(query_length) as avg_query_length,
             MAX(query_length) as max_query_length,
             AVG(filters_applied) as avg_filters,
             COUNT(CASE WHEN filters_applied > 0 THEN 1 END) as searches_with_filters,
             COUNT(*) as total_searches
           FROM analytics_search_metrics
           WHERE day >= ?""",
        (cutoff,)
    ).fetchone()
    db.close()

    return {
        'avg_query_length': round(stats['avg_query_length'] or 0, 1),
        'max_query_length': stats['max_query_length'] or 0,
        'avg_filters': round(stats['avg_filters'] or 0, 1),
        'pct_with_filters': round(stats['searches_with_filters'] / stats['total_searches'] * 100, 1) if stats['total_searches'] > 0 else 0,
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze search metrics and zero-result patterns')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--show-queries', action='store_true', help='Show top 20 failing queries')
    args = parser.parse_args()

    print("=" * 70)
    print(f"SEARCH METRICS ANALYSIS (past {args.days} days)")
    print("=" * 70)
    print()

    total, zero, rate = analyze_zero_result_rate(args.days)
    print(f"Zero-result rate: {rate:.1f}% ({zero} of {total} searches)")
    print()

    patterns = search_patterns(args.days)
    print(f"Search patterns:")
    print(f"  Avg query length: {patterns['avg_query_length']} chars")
    print(f"  Max query length: {patterns['max_query_length']} chars")
    print(f"  Avg filters applied: {patterns['avg_filters']}")
    print(f"  Searches with filters: {patterns['pct_with_filters']}%")
    print()

    if args.show_queries:
        failing = top_failing_queries(20, args.days)
        print(f"Top 20 queries with zero results:")
        print("-" * 70)
        for query, count, qlen, filters, mode in failing:
            print(f"  '{query}' ({count}x) | len={qlen}, filters={filters}, mode={mode}")
        print()

    print("=" * 70)
    print("Next steps: Phase 2 (Typo tolerance) gates on > 90% recall")
    print("=" * 70)

if __name__ == '__main__':
    main()
