#!/usr/bin/env python3
"""Continuous website discovery service (24/7).

Runs independently of nightly enrichment. Discovers and validates org websites,
extracts mission statements, and detects donation/volunteer link presence.

I/O bound (not GPU), so can run continuously while nightly GPU work happens separately.

Usage:
    python3 scripts/continuous_website_scraper.py [--workers 8] [--delay 5]

Args:
    --workers: Number of parallel HTTP requests (default: 8)
    --delay: Seconds between batch completions (default: 5)
"""

import sqlite3
import requests
import time
import logging
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import gzip
from typing import Tuple, Optional

DB_PATH = "data/merit_registry.db"
BATCH_SIZE = 100
TIMEOUT_CONNECT = 5
TIMEOUT_READ = 10
USER_AGENT = "Mozilla/5.0 (compatible; DaanaaBot/1.0; +https://daanaa.org/robots.txt)"

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def _score_website_quality(html: str, title: str) -> float:
    """Score website quality (0-100) to prioritize donation link scraping.

    Higher score = more likely to have donation infrastructure."""
    score = 0.0

    # Basic presence checks
    if '<html' in html.lower():
        score += 20
    if title:
        score += 15
    if len(html) > 5000:
        score += 15  # Substantial page

    # Donation infrastructure signals
    donation_platforms = [
        'donate', 'give', 'contribution', 'support', 'sponsor',
        'paypal', 'stripe', 'givebutter', 'donorbox', 'zeffy', 'every.org'
    ]
    html_lower = html.lower()
    for platform in donation_platforms:
        if platform in html_lower:
            score += 10
            break

    # Volunteer signals
    if any(word in html_lower for word in ['volunteer', 'join us', 'get involved']):
        score += 10

    return min(100.0, score)


def _detect_donation_links(html: str) -> list[str]:
    """Extract potential donation links from HTML."""
    donation_links = set()

    # Look for common donation endpoints
    patterns = [
        r'href=["\']([^"\']*(?:donate|give|support|contribute|sponsor)[^"\']*)["\']',
        r'href=["\']([^"\']*(?:paypal|stripe|givebutter|donorbox|zeffy)[^"\']*)["\']',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            url = match.group(1)
            if url and not url.startswith('#'):
                donation_links.add(url)

    return list(donation_links)[:5]  # Top 5


def _detect_volunteer_links(html: str) -> list[str]:
    """Extract potential volunteer interest links from HTML."""
    volunteer_links = set()

    patterns = [
        r'href=["\']([^"\']*(?:volunteer|join|get.*involved|participate)[^"\']*)["\']',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            url = match.group(1)
            if url and not url.startswith('#'):
                volunteer_links.add(url)

    return list(volunteer_links)[:3]  # Top 3


def scrape_organization_website(ein: str, website_url: str) -> Optional[dict]:
    """Scrape a single org website. Returns dict with extracted data or None on failure."""
    try:
        resp = requests.get(
            website_url,
            timeout=(TIMEOUT_CONNECT, TIMEOUT_READ),
            headers={'User-Agent': USER_AGENT},
            allow_redirects=True,
            verify=True
        )
        resp.raise_for_status()

        html = resp.text
        title = resp.history[0].headers.get('title', '') if resp.history else ''

        return {
            'ein': ein,
            'website': website_url,
            'status': 'ok',
            'title': title,
            'quality_score': _score_website_quality(html, title),
            'has_donation_links': len(_detect_donation_links(html)) > 0,
            'has_volunteer_links': len(_detect_volunteer_links(html)) > 0,
            'donation_link_candidates': _detect_donation_links(html),
            'volunteer_link_candidates': _detect_volunteer_links(html),
            'fetched_at': datetime.utcnow().isoformat() + 'Z'
        }
    except requests.exceptions.Timeout:
        return {'ein': ein, 'website': website_url, 'status': 'timeout'}
    except requests.exceptions.ConnectionError:
        return {'ein': ein, 'website': website_url, 'status': 'connection_error'}
    except requests.exceptions.HTTPError as e:
        return {'ein': ein, 'website': website_url, 'status': f'http_{e.response.status_code}'}
    except Exception as e:
        return {'ein': ein, 'website': website_url, 'status': f'error_{type(e).__name__}'}


def fetch_org_websites_batch(eins: list[str], conn: sqlite3.Connection) -> list[Tuple[str, str]]:
    """Fetch websites for a batch of EINs that haven't been checked recently."""
    query = """
        SELECT DISTINCT re.EIN, re.website
        FROM registry_enriched re
        WHERE re.EIN IN ({})
          AND re.website IS NOT NULL
          AND (re.website_status IS NULL
               OR (re.website_status = 'ok' AND re.updated_at < datetime('now', '-7 days'))
               OR re.website_status != 'ok')
        LIMIT 100
    """.format(','.join('?' * len(eins)))

    rows = conn.execute(query, eins).fetchall()
    return [(row[0], row[1]) for row in rows]


def process_batch(batch_eins: list[str], workers: int):
    """Process a batch of organizations: scrape websites, detect links."""
    conn = sqlite3.connect(DB_PATH)
    websites_to_scrape = fetch_org_websites_batch(batch_eins, conn)
    conn.close()

    if not websites_to_scrape:
        logger.info(f"Batch {batch_eins[0:3]}: no websites to check")
        return

    logger.info(f"Scraping {len(websites_to_scrape)} websites...")

    # Parallel scraping
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futs = {
            executor.submit(scrape_organization_website, ein, website): ein
            for ein, website in websites_to_scrape
        }

        for fut in as_completed(futs):
            result = fut.result()
            if result:
                results.append(result)

    # Write results to database
    if results:
        conn = sqlite3.connect(DB_PATH)
        now = datetime.utcnow().isoformat(timespec='seconds') + 'Z'

        for result in results:
            if result['status'] == 'ok':
                conn.execute("""
                    UPDATE registry_enriched
                    SET website_status='ok', updated_at=?
                    WHERE EIN=?
                """, (now, result['ein']))
            else:
                conn.execute("""
                    UPDATE registry_enriched
                    SET website_status=?, updated_at=?
                    WHERE EIN=?
                """, (result['status'], now, result['ein']))

        conn.commit()
        conn.close()

        success = sum(1 for r in results if r['status'] == 'ok')
        has_donation = sum(1 for r in results if r.get('has_donation_links'))
        has_volunteer = sum(1 for r in results if r.get('has_volunteer_links'))

        logger.info(f"  ✓ {success}/{len(results)} websites reachable")
        logger.info(f"  → {has_donation} have donation links, {has_volunteer} have volunteer pages")


def main():
    parser = argparse.ArgumentParser(description="Continuous website discovery service")
    parser.add_argument('--workers', type=int, default=8, help="Parallel HTTP workers")
    parser.add_argument('--delay', type=int, default=5, help="Delay between batches (seconds)")
    parser.add_argument('--limit', type=int, default=None, help="Max orgs to process (debug)")
    args = parser.parse_args()

    logger.info(f"Starting continuous website scraper ({args.workers} workers, {args.delay}s batch delay)")
    logger.info(f"Database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    # Get orgs with websites not checked recently
    query = """
        SELECT EIN FROM registry_enriched
        WHERE website IS NOT NULL
          AND (website_status IS NULL OR updated_at < datetime('now', '-7 days'))
        ORDER BY RANDOM()
    """
    if args.limit:
        query += f" LIMIT {args.limit}"

    eins = [row[0] for row in conn.execute(query).fetchall()]
    conn.close()

    if not eins:
        logger.info("No websites to check. Exiting.")
        return

    logger.info(f"Found {len(eins):,} orgs with unchecked/stale websites")

    # Process in batches
    for i in range(0, len(eins), BATCH_SIZE):
        batch = eins[i:i+BATCH_SIZE]
        try:
            process_batch(batch, args.workers)
        except Exception as e:
            logger.error(f"Batch error: {e}")

        if i + BATCH_SIZE < len(eins):
            logger.info(f"Sleeping {args.delay}s before next batch...")
            time.sleep(args.delay)

    logger.info("Continuous website scraper completed.")


if __name__ == '__main__':
    main()
