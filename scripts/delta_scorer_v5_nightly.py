#!/usr/bin/env python3
"""
delta_scorer_v5_nightly.py — Score only new/unscored organizations.

This runs nightly to score organizations added since the last full refresh.
Full scoring (all orgs) still happens Saturday.

Run:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/delta_scorer_v5_nightly.py

Logs to: logs/delta_scorer_nightly.log
"""

import sqlite3
import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG = Path.home() / "meritgiving/logs/delta_scorer_nightly.log"

def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, 'a') as fh:
        fh.write(line + '\n')

def count_unscored() -> int:
    """Count orgs with merit_score_v5 IS NULL"""
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE deductibility = '1' AND merit_score_v5 IS NULL
        """)
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        log(f'Error counting unscored orgs: {e}')
        return 0

def run_delta_score():
    """Run v5 scorer on unscored orgs only"""
    unscored = count_unscored()

    if unscored == 0:
        log('✅ No new orgs to score. Exiting.')
        return True

    log(f'Found {unscored:,} unscored orgs. Starting delta scoring...')

    # Run the full scorer but with a filter for unscored orgs
    # The merit_scorer_v5_0.py will hit the DB and score everything;
    # we'll filter in the load step
    try:
        # Run full scorer to get scores
        result = subprocess.run(
            [
                'python3',
                str(Path(__file__).parent / 'merit_scorer_v5_0.py'),
                '--output', '/tmp/delta_scores_v5.json',
            ],
            capture_output=True,
            text=True,
            timeout=3600,
        )

        if result.returncode != 0:
            log(f'Scorer failed: {result.stderr}')
            return False

        log(f'Scorer completed. Loading scores into database...')

        # Load scores, filtering for unscored orgs only
        result = subprocess.run(
            [
                'python3',
                str(Path(__file__).parent / 'load_v5_scores_delta.py'),
                '/tmp/delta_scores_v5.json',
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            log(f'Load failed: {result.stderr}')
            return False

        log(f'✅ Delta scoring complete.')
        return True

    except subprocess.TimeoutExpired:
        log(f'Delta scorer timed out after 1 hour')
        return False
    except Exception as e:
        log(f'Delta scorer error: {e}')
        return False

if __name__ == '__main__':
    log('Starting nightly delta scorer...')
    success = run_delta_score()
    sys.exit(0 if success else 1)
