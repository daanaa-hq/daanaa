#!/usr/bin/env python3
"""Daily quality measurement cron job (Task 8).

Runs at 6 AM to measure enrichment quality and log metrics to quality_log table.
Metrics are used by improve_prompts_cron.py to decide whether to improve prompts.

In production, this would:
  - Fetch real tag corrections from the org_claims verification system
  - Fetch real website validations from the donate_url pipeline
  - Log the metrics for the previous day's enrichment run

For now, tag_corrections and website_validations are placeholder empty dicts,
so no metrics get logged this run (this is expected until a real corrections-
fetching mechanism is wired in - see Task 8 requirements).

Usage:
  python3 measure_quality_cron.py  (uses production DB)
  python3 measure_quality_cron.py --db /path/to/test.db  (uses test DB)
"""
import sys
import sqlite3
import argparse
from datetime import date, timedelta
from pathlib import Path

# Make the repo root importable
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.quality_measurement import QualityMeasurement

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"


def main(db_path=None):
    """Measure daily quality and log metrics.

    Args:
        db_path: Path to SQLite database. If None, uses production DB at
                 ~/meritgiving/data/merit_registry.db

    Returns:
        Dict of metrics measured (empty if no data for today)
    """
    db_path = db_path or str(DB_PATH)
    con = sqlite3.connect(str(db_path), timeout=180)

    try:
        measurer = QualityMeasurement(db_con=con)

        # Placeholder: In production, fetch real corrections from claims table
        # For now, empty dicts mean no metrics get logged this run
        tag_corrections = {}
        website_validations = {}

        metrics = measurer.measure_daily_quality(
            run_date=str(date.today()),
            tag_corrections=tag_corrections,
            website_validations=website_validations
        )

        print(f"[{date.today()}] Quality measured: {metrics}")
        return metrics

    finally:
        con.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Measure daily enrichment quality and log metrics'
    )
    parser.add_argument('--db', dest='db_path', help='Path to SQLite database')
    args = parser.parse_args()

    result = main(db_path=args.db_path)
    sys.exit(0 if result is not None else 1)
