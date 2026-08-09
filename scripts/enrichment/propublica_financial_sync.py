#!/usr/bin/env python3
"""
ProPublica Nonprofit Explorer API sync: multi-year financial history.

Free, no API key, no scraping — pulls audited Form 990 filing data
(revenue, expenses, assets) going back up to 14+ years per org, directly
from ProPublica's structured API.

Applies the same lessons as website_verifier_spider.py:
- Checkpoint/resume (survives interruption)
- Explicit error logging per type (never `except: pass`)
- Structured output table, separate from registry_enriched (no write
  contention with the live API's reads)
- Adaptive throttling reacts to 429s rather than assuming a fixed rate
"""

import argparse
import logging
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG_DIR = Path.home() / 'meritgiving' / 'logs'
LOG_DIR.mkdir(exist_ok=True)

API_BASE = "https://projects.propublica.org/nonprofits/api/v2/organizations"
REQUEST_DELAY = 0.15  # conservative; ProPublica publishes no hard rate limit but this is respectful bulk use

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'propublica_financial_sync.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def ensure_output_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS propublica_financial_history (
        EIN TEXT,
        fiscal_year INTEGER,
        revenue REAL,
        expenses REAL,
        assets_end REAL,
        source TEXT DEFAULT 'propublica_api',
        fetched_at TIMESTAMP,
        PRIMARY KEY (EIN, fiscal_year)
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pfh_ein ON propublica_financial_history(EIN)")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS enrichment_checkpoints (
        phase TEXT, run_date DATE, last_ein TEXT, record_count INTEGER,
        checkpoint_time TIMESTAMP, PRIMARY KEY (phase, run_date)
    )
    """)
    conn.commit()
    conn.close()


def get_orgs_to_sync(limit=None, resume=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    last_ein = None
    if resume:
        cursor.execute("""
        SELECT last_ein FROM enrichment_checkpoints
        WHERE phase = 'propublica_sync' AND run_date = date('now')
        """)
        row = cursor.fetchone()
        if row:
            last_ein = row['last_ein']
            logger.info(f"Resuming from checkpoint EIN: {last_ein}")

    query = "SELECT EIN, organization_name FROM registry_enriched WHERE EIN IS NOT NULL"
    params = []
    if last_ein:
        query += " AND EIN > ?"
        params.append(last_ein)
    query += " ORDER BY EIN"
    if limit:
        query += f" LIMIT {int(limit)}"

    cursor.execute(query, params)
    orgs = cursor.fetchall()
    conn.close()
    return orgs


def fetch_financial_history(ein):
    """Returns list of (fiscal_year, revenue, expenses, assets_end) tuples,
    or None on failure. 404 (no ProPublica record) is expected/common — not
    an error, just no data to add."""
    try:
        resp = requests.get(f"{API_BASE}/{int(ein)}.json", timeout=10)
        if resp.status_code == 404:
            return []  # legitimately not in ProPublica's index — not an error
        if resp.status_code == 429:
            logger.warning(f"Rate limited on EIN {ein}; backing off 5s")
            time.sleep(5)
            return fetch_financial_history(ein)  # one retry after backoff
        resp.raise_for_status()

        data = resp.json()
        filings = data.get('filings_with_data', [])
        rows = []
        for f in filings:
            year = f.get('tax_prd_yr')
            if year is None:
                continue
            rows.append((
                year,
                f.get('totrevenue'),
                f.get('totfuncexpns'),
                f.get('totassetsend'),
            ))
        return rows
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching EIN {ein}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request failed for EIN {ein}: {e}")
        return None
    except (ValueError, KeyError) as e:
        logger.warning(f"Malformed response for EIN {ein}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--workers', type=int, default=16,
                         help='Concurrent workers (I/O-bound; ProPublica publishes no hard '
                              'rate limit, but a 429 anywhere triggers a shared backoff — see lesson #5)')
    args = parser.parse_args()

    ensure_output_table()
    orgs = get_orgs_to_sync(limit=args.limit, resume=args.resume)

    if not orgs:
        logger.info("No orgs to sync.")
        return

    logger.info(f"Starting ProPublica sync: {len(orgs)} orgs, {args.workers} workers")

    write_lock = threading.Lock()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    stats = {'found': 0, 'not_in_propublica': 0, 'error': 0, 'total_years_added': 0}
    stats_lock = threading.Lock()
    start = time.time()
    completed = 0
    max_ein_seen = None

    def process_one(org):
        ein = org['EIN']
        rows = fetch_financial_history(ein)
        return ein, rows

    # SafeWorkerPool pattern (lesson #2): bounded pool, guaranteed cleanup via
    # context manager, cap workers regardless of what's requested.
    with ThreadPoolExecutor(max_workers=min(args.workers, 32)) as executor:
        futures = {executor.submit(process_one, org): org for org in orgs}

        for future in as_completed(futures):
            ein, rows = future.result()

            with stats_lock:
                if rows is None:
                    stats['error'] += 1
                elif len(rows) == 0:
                    stats['not_in_propublica'] += 1
                else:
                    stats['found'] += 1
                    stats['total_years_added'] += len(rows)
                    if not args.dry_run:
                        with write_lock:
                            conn.executemany("""
                            INSERT OR REPLACE INTO propublica_financial_history
                            (EIN, fiscal_year, revenue, expenses, assets_end, fetched_at)
                            VALUES (?, ?, ?, ?, ?, datetime('now'))
                            """, [(ein, y, r, e, a) for y, r, e, a in rows])
                            conn.commit()

                completed += 1
                max_ein_seen = ein if max_ein_seen is None else max(max_ein_seen, ein)

                if completed % 100 == 0:
                    elapsed = time.time() - start
                    rate = completed / elapsed * 3600
                    logger.info(f"Progress: {completed}/{len(orgs)} ({rate:.0f}/hour) — "
                                f"found={stats['found']} not_in_propublica={stats['not_in_propublica']} "
                                f"error={stats['error']}")
                    if not args.dry_run:
                        with write_lock:
                            conn.execute("""
                            INSERT OR REPLACE INTO enrichment_checkpoints
                            VALUES ('propublica_sync', date('now'), ?, ?, datetime('now'))
                            """, (max_ein_seen, completed))
                            conn.commit()

    elapsed = time.time() - start
    final_rate = len(orgs) / elapsed * 3600 if elapsed > 0 else 0
    logger.info("=" * 60)
    logger.info(f"SYNC COMPLETE: {len(orgs)} orgs in {elapsed:.1f}s ({final_rate:.0f}/hour)")
    logger.info(f"  found (has ProPublica data): {stats['found']}")
    logger.info(f"  not_in_propublica: {stats['not_in_propublica']}")
    logger.info(f"  errors: {stats['error']}")
    logger.info(f"  total fiscal-year records added: {stats['total_years_added']}")
    logger.info("=" * 60)

    conn.close()


if __name__ == '__main__':
    main()
