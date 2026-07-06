#!/usr/bin/env python3
"""
Monitor enrichment batch health and quality trends.

Checks whether last night's enrichment batch succeeded and reports:
- Number of enrichments generated
- Quality metrics (accuracy, trend)
- Visual summary for ops dashboard

Usage:
  python3 monitor_batch.py
  python3 monitor_batch.py --date 2026-07-05
"""
import sys
import sqlite3
import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

DB_PATH = _REPO_ROOT / "data" / "merit_registry.db"


def check_batch_health(
    db_con: sqlite3.Connection,
    check_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check enrichment batch health for a given date.

    Args:
        db_con: SQLite connection to merit_registry.db
        check_date: Date to check (YYYY-MM-DD format). If None, uses yesterday.

    Returns:
        Dict with keys:
        - batch_ran (bool): Whether any enrichments were recorded for this date
        - enrichment_count (int): Number of enrichments generated on that date
        - checked_date (str): The date that was checked (YYYY-MM-DD)
        - quality_avg (float|None): Average of recent quality metrics (past 3 days),
          or None if no metrics found
        - quality_trend (str|None): Trend indicator ('↑' up, '↓' down, '→' flat),
          or None if insufficient data
    """
    if check_date is None:
        check_date = str(date.today() - timedelta(days=1))

    cursor = db_con.cursor()

    # Check if yesterday's batch ran
    cursor.execute(
        "SELECT COUNT(*) FROM enrichment_run WHERE run_date = ?",
        (check_date,)
    )
    enrichment_count = cursor.fetchone()[0]
    batch_ran = enrichment_count > 0

    # Get quality metrics from past 3 days (including the check_date)
    check_date_obj = date.fromisoformat(check_date)
    dates = [
        str(check_date_obj - timedelta(days=i))
        for i in range(3)
    ]

    cursor.execute(
        """SELECT value FROM quality_log
           WHERE metric_type = 'cause_tag_accuracy'
           AND date IN (?, ?, ?)
           ORDER BY date DESC""",
        tuple(dates)
    )
    quality_values = [row[0] for row in cursor.fetchall()]

    quality_avg = None
    quality_trend = None

    if quality_values:
        quality_avg = sum(quality_values) / len(quality_values)

        # Determine trend from oldest to newest
        if len(quality_values) >= 2:
            newest = quality_values[0]  # Most recent (first in DESC order)
            oldest = quality_values[-1]  # Oldest (last in DESC order)

            if newest > oldest:
                quality_trend = '↑'
            elif newest < oldest:
                quality_trend = '↓'
            else:
                quality_trend = '→'
        else:
            # Only one data point, no trend
            quality_trend = '→'

    return {
        'batch_ran': batch_ran,
        'enrichment_count': enrichment_count,
        'checked_date': check_date,
        'quality_avg': quality_avg,
        'quality_trend': quality_trend
    }


def main(db_path: Optional[str] = None, check_date: Optional[str] = None):
    """
    Print human-readable batch health summary.

    Args:
        db_path: Path to merit_registry.db. Defaults to standard location.
        check_date: Date to check (YYYY-MM-DD). Defaults to yesterday.
    """
    con = sqlite3.connect(db_path or str(DB_PATH), timeout=180)
    health = check_batch_health(con, check_date=check_date)
    con.close()

    checked_date = health['checked_date']

    print(f"\n=== Enrichment Batch Health ({checked_date}) ===\n")

    if health['batch_ran']:
        print(f"✓ Batch ran: {health['enrichment_count']} enrichments")
    else:
        print(f"⚠ Batch MISSING ({checked_date})")

    if health['quality_avg'] is not None:
        trend = health['quality_trend'] or '→'
        print(f"Quality: {health['quality_avg']:.1%} {trend}")
    else:
        print("Quality: No recent metrics")

    print()
    return health


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Monitor enrichment batch health'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Date to check (YYYY-MM-DD format, defaults to yesterday)'
    )
    parser.add_argument(
        '--db',
        type=str,
        help='Path to merit_registry.db (defaults to standard location)'
    )

    args = parser.parse_args()
    main(db_path=args.db, check_date=args.date)
