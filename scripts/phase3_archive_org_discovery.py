#!/usr/bin/env python3
"""
Phase 3: Archive.org Wayback Machine Discovery
Find historical/archived websites for orgs without current verified sites.
Expected: 5-10% success rate on orgs with no website_status='ok'.
Zero cost, parallel workers.
"""

import sqlite3
import requests
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DB_PATH = Path('/home/akbar/meritgiving/data/merit_registry.db')
LOG_DIR = Path('/home/akbar/meritgiving/logs')

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'phase3_archive_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

WAYBACK_API = 'https://archive.org/wayback/available'
REQUEST_TIMEOUT = 5
WORKERS = 15

def search_archive(ein, org_name):
    """Search Wayback Machine for archived version of org name + .org"""
    if not org_name or len(org_name) < 3:
        return None, None

    clean_name = org_name.replace(', Inc', '').replace(', LLC', '').strip()
    domain = f"{clean_name.lower().replace(' ', '')}.org"

    try:
        resp = requests.get(
            WAYBACK_API,
            params={'url': domain, 'output': 'json'},
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get('archived_snapshots'):
            snapshot = data['archived_snapshots'].get('closest')
            if snapshot and snapshot.get('status') == '200':
                url = snapshot.get('url')  # e.g., https://web.archive.org/web/20190101000000/example.org
                return url, 'archive_org'
    except Exception as e:
        logger.debug(f"{ein}: Archive search error: {e}")

    return None, None

def save_discovery(ein, url, source):
    """Save Archive.org discovery to database."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    try:
        c.execute("""
            UPDATE registry_enriched
            SET website = ?, website_status = ?
            WHERE ein = ? AND (website IS NULL OR website = '')
        """, (url, source, ein))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"DB error for {ein}: {e}")
        return False
    finally:
        conn.close()

def get_orgs_without_websites(limit=5000):
    """Get orgs with no verified website_status='ok'."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("""
        SELECT ein, organization_name
        FROM registry_enriched
        WHERE (website IS NULL OR website = '')
          AND (website_status IS NULL OR website_status != 'ok')
          AND organization_name IS NOT NULL
          AND org_status = 'active'
        ORDER BY total_revenue DESC
        LIMIT ?
    """, (limit,))

    results = c.fetchall()
    conn.close()
    return results

def main():
    logger.info("Phase 3: Archive.org Wayback Machine Discovery — Starting")
    logger.info("Target: 5-10% success rate, historical websites for 5K orgs")

    batch_size = 5000
    workers = WORKERS

    orgs = get_orgs_without_websites(batch_size)

    if not orgs:
        logger.warning("No orgs to discover")
        return

    logger.info(f"Processing {len(orgs)} orgs with {workers} workers")

    found = 0
    not_found = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(search_archive, ein, name): (ein, name) for ein, name in orgs}

        for i, future in enumerate(as_completed(futures)):
            try:
                ein, name = futures[future]
                url, source = future.result()

                if url:
                    if save_discovery(ein, url, source):
                        found += 1
                        logger.info(f"{ein}: ✓ {url}")
                    else:
                        logger.debug(f"{ein}: DB skip (already has website)")
                else:
                    not_found += 1
                    if i % 100 == 0:
                        logger.debug(f"{ein}: ✗ {name}")

                # Progress every 500
                if (found + not_found) % 500 == 0:
                    rate = 100 * found / (found + not_found) if (found + not_found) > 0 else 0
                    logger.info(f"Progress: {found + not_found} processed, {found} found ({rate:.1f}%)")

            except Exception as e:
                logger.error(f"Processing error: {e}")
                errors += 1

    # Report
    total = found + not_found
    success_rate = 100 * found / total if total > 0 else 0

    logger.info(f"\n{'='*60}")
    logger.info(f"Phase 3 Batch Complete:")
    logger.info(f"  Processed: {total}")
    logger.info(f"  Found: {found}")
    logger.info(f"  Not found: {not_found}")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Success rate: {success_rate:.1f}%")
    logger.info(f"  Extrapolation: {int(success_rate/100 * 1600000)} potential websites from 1.6M backlog")
    logger.info(f"{'='*60}")

if __name__ == '__main__':
    main()
