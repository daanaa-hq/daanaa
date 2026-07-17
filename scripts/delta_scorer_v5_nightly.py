#!/usr/bin/env python3
"""
delta_scorer_v5_nightly.py — Score only new/unscored organizations.

Runs nightly to score orgs added since the last full refresh (e.g. by the
Monday IRS data load). Full scoring of all orgs still happens Saturday via
overnight_pipeline.py.

An org is "scorable" when total_revenue, months_of_reserve and
program_expense_pct are all present — the same requirement merit_scorer_v5_0
enforces in extract_metrics(). Orgs missing financial data are never scored
(evidence-based trust signals, STEWARDSHIP P3).

Run:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/delta_scorer_v5_nightly.py

Logs to: logs/delta_scorer_nightly.log
"""

import sqlite3
import sys
import subprocess
from pathlib import Path
from datetime import datetime

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG = Path.home() / "meritgiving/logs/delta_scorer_nightly.log"
SCORES_JSON = Path.home() / "meritgiving/logs/delta_scores_v5.json"

SCORABLE_UNSCORED_SQL = """
    SELECT COUNT(*) FROM registry_enriched
    WHERE deductibility = '1'
      AND merit_score_v5 IS NULL
      AND total_revenue IS NOT NULL
      AND months_of_reserve IS NOT NULL
      AND program_expense_pct IS NOT NULL
"""

def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, 'a') as fh:
        fh.write(line + '\n')

def count_scorable_unscored() -> int:
    try:
        conn = sqlite3.connect(DB)
        count = conn.execute(SCORABLE_UNSCORED_SQL).fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        log(f'Error counting scorable unscored orgs: {e}')
        return -1

def run_delta_score() -> bool:
    unscored = count_scorable_unscored()
    if unscored < 0:
        return False
    if unscored == 0:
        log('No scorable unscored orgs. Nothing to do.')
        return True

    log(f'Found {unscored:,} scorable unscored orgs. Running v5 scorer...')

    try:
        result = subprocess.run(
            [
                'python3',
                str(Path(__file__).parent / 'merit_scorer_v5_0.py'),
                '--output', str(SCORES_JSON),
            ],
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if result.returncode != 0:
            log(f'Scorer failed: {result.stderr[-2000:]}')
            return False

        log('Scorer completed. Loading delta scores into database...')

        result = subprocess.run(
            [
                'python3',
                str(Path(__file__).parent / 'load_v5_scores_delta.py'),
                str(SCORES_JSON),
            ],
            capture_output=True,
            text=True,
            timeout=1800,
        )
        if result.returncode != 0:
            log(f'Load failed: {result.stderr[-2000:]}')
            return False

        remaining = count_scorable_unscored()
        log(f'Delta scoring complete. Scorable unscored remaining: {remaining:,}')
        SCORES_JSON.unlink(missing_ok=True)
        return True

    except subprocess.TimeoutExpired:
        log('Delta scorer timed out')
        return False
    except Exception as e:
        log(f'Delta scorer error: {e}')
        return False

if __name__ == '__main__':
    log('Starting nightly delta scorer...')
    ok = run_delta_score()
    sys.exit(0 if ok else 1)
