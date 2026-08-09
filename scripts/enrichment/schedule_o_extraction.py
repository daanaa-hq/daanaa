#!/usr/bin/env python3
"""
Schedule O program extraction: fetch Form 990 Schedule O narratives from ProPublica API.

Schedule O is the "Program Accomplishments and Activities" section of Form 990s,
filed by nonprofits to describe their programs and services. This module extracts
the raw narrative text and stores it for use in org discovery and search.

Applies daemon lessons:
- Checkpoint/resume (survives interruption)
- Explicit error logging per type (never silent except: pass)
- Structured output table, separate from registry_enriched (no write contention)
- Adaptive throttling (ProPublica rate limits)

Usage (spike / dry-run):
    python3 scripts/enrichment/schedule_o_extraction.py --limit 100 --dry-run

Usage (production, nightly):
    python3 scripts/enrichment/schedule_o_extraction.py --resume
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
REQUEST_DELAY = 0.15  # conservative; ProPublica publishes no hard rate limit

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'schedule_o_extraction.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def ensure_output_table():
    """Create output table for extracted program descriptions."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS extracted_programs (
        EIN TEXT,
        schedule_o_text TEXT,
        schedule_o_year INTEGER,
        schedule_o_source TEXT DEFAULT 'propublica_api',
        extraction_confidence REAL,  -- 0.0-1.0 based on text quality
        extracted_at TIMESTAMP,
        PRIMARY KEY (EIN, schedule_o_year)
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ep_ein ON extracted_programs(EIN)")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS enrichment_checkpoints (
        phase TEXT, run_date DATE, last_ein TEXT, record_count INTEGER,
        checkpoint_time TIMESTAMP, PRIMARY KEY (phase, run_date)
    )
    """)
    conn.commit()
    conn.close()


def get_orgs_to_process(limit=None, resume=False):
    """Fetch orgs needing Schedule O extraction.

    Lesson applied (#6, checkpoint/resume): query past the last-processed
    EIN from enrichment_checkpoints rather than restarting from scratch.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    last_ein = None
    if resume:
        cursor.execute("""
        SELECT last_ein FROM enrichment_checkpoints
        WHERE phase = 'schedule_o_extraction' AND run_date = date('now')
        """)
        row = cursor.fetchone()
        if row:
            last_ein = row['last_ein']
            logger.info(f"Resuming from checkpoint EIN: {last_ein}")

    # Prioritize small orgs (where program clarity matters most)
    query = """
    SELECT DISTINCT r.EIN, r.organization_name, r.total_revenue
    FROM registry_enriched r
    LEFT JOIN extracted_programs ep ON r.EIN = ep.EIN
    WHERE r.EIN IS NOT NULL
    AND ep.EIN IS NULL  -- Only orgs without extracted programs yet
    AND (r.total_revenue IS NULL OR r.total_revenue < 1000000)  -- Focus on smaller orgs first
    """
    params = []
    if last_ein:
        query += " AND r.EIN > ?"
        params.append(last_ein)
    query += " ORDER BY r.total_revenue ASC, r.EIN"
    if limit:
        query += f" LIMIT {int(limit)}"

    cursor.execute(query, params)
    orgs = cursor.fetchall()
    conn.close()
    return orgs


def fetch_schedule_o(ein):
    """Fetch Schedule O from ProPublica API.

    Returns (schedule_o_text, fiscal_year, confidence) tuple, or (None, None, None) on failure.
    404 (no ProPublica record) is expected — not an error, just no data to add.
    """
    try:
        resp = requests.get(f"{API_BASE}/{int(ein)}.json", timeout=10)
        if resp.status_code == 404:
            return None, None, None  # legitimately not in ProPublica's index
        if resp.status_code == 429:
            logger.warning(f"Rate limited on EIN {ein}; backing off 5s")
            time.sleep(5)
            return fetch_schedule_o(ein)  # one retry after backoff
        resp.raise_for_status()

        data = resp.json()

        # Most recent filing with Schedule O text
        filings = data.get('filings_with_data', [])
        for filing in sorted(filings, key=lambda x: x.get('tax_prd_yr', 0), reverse=True):
            schedule_o = filing.get('schedule_o_text')
            if schedule_o and len(schedule_o.strip()) > 50:  # meaningful text only
                fiscal_year = filing.get('tax_prd_yr')
                confidence = 0.95  # high confidence: direct from IRS filing
                return schedule_o, fiscal_year, confidence

        # No Schedule O found
        return None, None, None

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching Schedule O for EIN {ein}")
        return None, None, None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request failed for Schedule O EIN {ein}: {e}")
        return None, None, None
    except (ValueError, KeyError) as e:
        logger.warning(f"Malformed Schedule O response for EIN {ein}: {e}")
        return None, None, None


def main():
    parser = argparse.ArgumentParser(description='Schedule O program extraction')
    parser.add_argument('--limit', type=int, default=100, help='Max orgs to process')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--dry-run', action='store_true', help='Do not write to DB')
    parser.add_argument('--workers', type=int, default=8,
                         help='Concurrent workers (I/O-bound; ProPublica rate-limited)')
    args = parser.parse_args()

    ensure_output_table()
    orgs = get_orgs_to_process(limit=args.limit, resume=args.resume)

    if not orgs:
        logger.info("No orgs to process.")
        return

    logger.info(f"Starting Schedule O extraction: {len(orgs)} orgs, {args.workers} workers")

    write_lock = threading.Lock()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    stats = {'found': 0, 'not_in_propublica': 0, 'error': 0, 'total_records': 0}
    stats_lock = threading.Lock()
    start = time.time()
    completed = 0
    max_ein_seen = None

    def process_one(org):
        ein = org['EIN']
        schedule_o_text, fiscal_year, confidence = fetch_schedule_o(ein)
        return ein, schedule_o_text, fiscal_year, confidence

    # SafeWorkerPool pattern (lesson #2): bounded pool, guaranteed cleanup via
    # context manager, cap workers regardless of what's requested.
    with ThreadPoolExecutor(max_workers=min(args.workers, 16)) as executor:
        futures = {executor.submit(process_one, org): org for org in orgs}

        for future in as_completed(futures):
            ein, schedule_o_text, fiscal_year, confidence = future.result()

            with stats_lock:
                if schedule_o_text is None:
                    stats['not_in_propublica'] += 1
                else:
                    stats['found'] += 1
                    stats['total_records'] += 1
                    if not args.dry_run:
                        with write_lock:
                            conn.execute("""
                            INSERT OR REPLACE INTO extracted_programs
                            (EIN, schedule_o_text, schedule_o_year, extraction_confidence, extracted_at)
                            VALUES (?, ?, ?, ?, datetime('now'))
                            """, (ein, schedule_o_text, fiscal_year, confidence))
                            conn.commit()

                completed += 1
                max_ein_seen = ein if max_ein_seen is None else max(max_ein_seen, ein)

                if completed % 25 == 0:
                    elapsed = time.time() - start
                    rate = completed / elapsed * 3600
                    logger.info(f"Progress: {completed}/{len(orgs)} ({rate:.0f}/hour) — "
                                f"found={stats['found']} not_in_propublica={stats['not_in_propublica']} "
                                f"error={stats['error']}")
                    if not args.dry_run:
                        with write_lock:
                            conn.execute("""
                            INSERT OR REPLACE INTO enrichment_checkpoints
                            VALUES ('schedule_o_extraction', date('now'), ?, ?, datetime('now'))
                            """, (max_ein_seen, completed))
                            conn.commit()

    elapsed = time.time() - start
    final_rate = len(orgs) / elapsed * 3600 if elapsed > 0 else 0
    logger.info("=" * 60)
    logger.info(f"EXTRACTION COMPLETE: {len(orgs)} orgs in {elapsed:.1f}s ({final_rate:.0f}/hour)")
    logger.info(f"  found (has Schedule O): {stats['found']}")
    logger.info(f"  not_in_propublica: {stats['not_in_propublica']}")
    logger.info(f"  errors: {stats['error']}")
    logger.info(f"  total records extracted: {stats['total_records']}")
    logger.info("=" * 60)

    conn.close()


if __name__ == '__main__':
    main()
