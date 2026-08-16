#!/usr/bin/env python3
"""
Enrichment Dashboard — Real-time visibility into archive recovery, link discovery, and data quality.
Generates metrics on promotion candidates, match quality, source distribution, and quality gates.

Usage:
  python3 enrichment_dashboard.py                    # Show current status + last 100 promotion candidates
  python3 enrichment_dashboard.py --hourly           # Generate hourly report (for cron)
  python3 enrichment_dashboard.py --full             # Full analytics + redteam cases
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from statistics import mean, median, stdev

REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / "logs" / "archive_finder"
CANDIDATES_FILE = LOG_DIR / "archive_promotion_candidates.json"
DEAD_POOL_LOG = LOG_DIR / "dead_pool_run.log"

def parse_promotion_candidates():
    """Load promotion candidates JSON."""
    if not CANDIDATES_FILE.exists():
        return []
    try:
        with open(CANDIDATES_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load candidates: {e}")
        return []

def parse_dead_pool_log(limit=None):
    """Parse dead_pool_run.log for scan results."""
    results = []
    if not DEAD_POOL_LOG.exists():
        return results

    pattern = r'\[([✓✗])\]\s+(.+?)\s+archived=(True|False)\s+match=([\d.]+)\s+snap=(.+?)\s+cc=(True|False)'

    try:
        with open(DEAD_POOL_LOG) as f:
            for line in f:
                m = re.search(pattern, line)
                if m:
                    results.append({
                        'status': m.group(1),
                        'name': m.group(2).strip(),
                        'archived': m.group(3) == 'True',
                        'match': float(m.group(4)),
                        'snapshot': m.group(5),
                        'common_crawl': m.group(6) == 'True',
                        'line': line.strip()
                    })
    except Exception as e:
        print(f"❌ Failed to parse log: {e}", file=sys.stderr)

    if limit:
        results = results[-limit:]
    return results

def compute_metrics(candidates, results):
    """Compute dashboard metrics."""
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'candidates_total': len(candidates),
        'scan_results_total': len(results),
    }

    # Promotion candidates breakdown
    if candidates:
        metrics['promotion'] = {
            'total_queued': len(candidates),
            'by_confidence': defaultdict(int),
            'by_source': defaultdict(int),
            'avg_match_quality': mean([c.get('match_quality', 0) for c in candidates if c.get('match_quality')]),
        }
        for c in candidates:
            conf = c.get('confidence', 'unknown')
            metrics['promotion']['by_confidence'][conf] += 1
            source = c.get('source', 'unknown')
            metrics['promotion']['by_source'][source] += 1

    # Scan results breakdown
    if results:
        successes = [r for r in results if r['status'] == '✓']
        metrics['scan'] = {
            'total': len(results),
            'promoted': len(successes),
            'success_rate': len(successes) / len(results) if results else 0,
            'with_snapshot': sum(1 for r in results if r['snapshot'] not in ['-', 'None']),
            'with_commonc_crawl': sum(1 for r in results if r['common_crawl']),
            'archived_orgs': sum(1 for r in results if r['archived']),
            'avg_match_quality': median([r['match'] for r in results if r['match'] > 0]) if results else 0,
        }

    return metrics

def print_dashboard(candidates, results):
    """Pretty-print enrichment dashboard."""
    print("\n" + "=" * 70)
    print("🎯 ENRICHMENT DASHBOARD — Archive Recovery & Link Discovery")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S Central')}")
    print()

    # Candidates summary
    if candidates:
        print("📊 PROMOTION QUEUE")
        print(f"  Total queued for promotion: {len(candidates)}")

        by_confidence = defaultdict(int)
        for c in candidates:
            by_confidence[c.get('confidence', 'unknown')] += 1

        for conf in sorted(by_confidence.keys(), key=lambda x: by_confidence[x], reverse=True):
            count = by_confidence[conf]
            pct = 100 * count / len(candidates)
            print(f"    • {conf}: {count} ({pct:.1f}%)")

    print()

    # Scan results summary
    if results:
        promoted = sum(1 for r in results if r['status'] == '✓')
        success_rate = 100 * promoted / len(results) if results else 0

        print("📈 SCAN PROGRESS")
        print(f"  Orgs scanned: {len(results):,}")
        print(f"  Promoted: {promoted:,} ({success_rate:.1f}%)")

        snapshots = sum(1 for r in results if r['snapshot'] not in ['-', 'None'])
        cc = sum(1 for r in results if r['common_crawl'])
        archived = sum(1 for r in results if r['archived'])

        print(f"  Source: Wayback {snapshots:,} | Common Crawl {cc:,} | Already archived {archived:,}")

        # Match quality distribution
        matches = [r['match'] for r in results if r['match'] > 0]
        if matches:
            print(f"  Match quality (median): {median(matches):.2f}")
            print(f"    Range: {min(matches):.2f} – {max(matches):.2f}")

    print()

    # Recent promotions (last 10)
    recent = [r for r in results if r['status'] == '✓'][-10:] if results else []
    if recent:
        print("✅ RECENT PROMOTIONS (Last 10)")
        for r in recent:
            src = "WM" if r['snapshot'] not in ['-', 'None'] else "CC"
            print(f"  • {r['name'][:50]:50} [{src} {r['match']:.2f}]")

    print()

    # Quality gates
    print("🔐 QUALITY GATES")
    if results:
        gates = {
            'Match quality ≥0.50': sum(1 for r in results if r['match'] >= 0.50),
            'Recency ≤180 days': sum(1 for r in results if r['snapshot'] not in ['-', 'None']),
            'Has snapshot or CC': sum(1 for r in results if r['snapshot'] not in ['-', 'None'] or r['common_crawl']),
        }
        for gate, count in gates.items():
            pct = 100 * count / len(results) if results else 0
            print(f"  ✓ {gate}: {count:,} ({pct:.1f}%)")

    print()
    print("=" * 70)

def hourly_report():
    """Generate lightweight hourly report for cron."""
    candidates = parse_promotion_candidates()
    results = parse_dead_pool_log(limit=1000)  # Sample last 1000 for speed
    metrics = compute_metrics(candidates, results)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"{timestamp} | Queued: {metrics['candidates_total']:,} | "
          f"Scanned: {metrics['scan_results_total']:,} | "
          f"Success: {metrics['scan'].get('success_rate', 0):.1%}")

if __name__ == '__main__':
    candidates = parse_promotion_candidates()
    results = parse_dead_pool_log()

    if '--hourly' in sys.argv:
        hourly_report()
    elif '--full' in sys.argv:
        metrics = compute_metrics(candidates, results)
        print(json.dumps(metrics, indent=2, default=str))
    else:
        print_dashboard(candidates, results)
