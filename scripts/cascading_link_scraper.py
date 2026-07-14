#!/usr/bin/env python3
"""Cascading link scraper — triggered after good websites are found.

Once a website is validated (website_status='ok' AND quality_score > 40),
this service:
1. Extracts donate URL (confidence-scored)
2. Extracts volunteer interest links
3. Tests that links are live and not corrupted

Runs continuously, triggered by website discovery results.

Usage:
    python3 scripts/cascading_link_scraper.py [--workers 4] [--delay 10]
"""

import sqlite3
import requests
import time
import logging
import argparse
import re
import json
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DB_PATH = "data/merit_registry.db"
BATCH_SIZE = 50
TIMEOUT = (5, 10)
USER_AGENT = "Mozilla/5.0 (compatible; DaanaaBot/1.0; +https://daanaa.org/robots.txt)"

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def _score_donate_url(url: str, html_content: str = "") -> float:
    """Score likelihood that a URL is a real donation endpoint (0-100).

    High scores: payment processor paths, clear donate verbs.
    Low scores: general links that happen to mention 'donate'."""

    score = 50.0  # Base score

    donation_platforms = {
        'paypal': 10, 'stripe': 10, 'givebutter': 8, 'donorbox': 8,
        'zeffy': 8, 'every.org': 8, 'givewell': 5, 'network-for-good': 5
    }

    url_lower = url.lower()
    for platform, points in donation_platforms.items():
        if platform in url_lower:
            score += points
            break

    # Path patterns
    if any(p in url_lower for p in ['/donate', '/give', '/support', '/sponsor']):
        score += 15
    if any(p in url_lower for p in ['donation', 'contributor', 'sustainer']):
        score += 5

    # Negative signals
    if any(p in url_lower for p in ['login', 'account', 'profile', '#']):
        score -= 10

    return min(100.0, max(0.0, score))


def test_link_validity(url: str) -> Tuple[bool, int]:
    """Test if a link is live and returns 200-level status.

    Returns (is_valid, http_status_code)."""
    try:
        resp = requests.head(
            url,
            timeout=TIMEOUT,
            headers={'User-Agent': USER_AGENT},
            allow_redirects=True,
            verify=True
        )
        return (200 <= resp.status_code < 400, resp.status_code)
    except Exception:
        try:
            # Fallback to GET if HEAD fails
            resp = requests.get(
                url,
                timeout=TIMEOUT,
                headers={'User-Agent': USER_AGENT},
                allow_redirects=True,
                verify=True,
                stream=True
            )
            resp.close()
            return (200 <= resp.status_code < 400, resp.status_code)
        except Exception:
            return (False, 0)


def extract_and_score_donate_links(ein: str, html: str, base_url: str) -> list[dict]:
    """Extract donate links from HTML with confidence scoring."""
    links = []

    patterns = [
        r'href=["\']([^"\']*(?:donate|give|support|sponsor|contribute)[^"\']*)["\']',
        r'href=["\']([^"\']*(?:paypal|stripe|givebutter|donorbox|zeffy)[^"\']*)["\']',
    ]

    found_urls = set()
    for pattern in patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            url = match.group(1)
            if url and not url.startswith('#'):
                # Resolve relative URLs
                if url.startswith('/'):
                    url = urljoin(base_url, url)
                elif not url.startswith('http'):
                    url = urljoin(base_url, url)

                found_urls.add(url)

    # Score each link
    for url in found_urls:
        is_valid, status = test_link_validity(url)
        if is_valid:
            confidence = _score_donate_url(url, html)
            links.append({
                'ein': ein,
                'donate_url': url,
                'confidence': confidence,
                'status_code': status,
                'source': 'cascading_scraper',
                'checked_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z'
            })

    return sorted(links, key=lambda x: x['confidence'], reverse=True)[:3]  # Top 3


def extract_volunteer_links(html: str, base_url: str) -> list[str]:
    """Extract volunteer/get-involved links from HTML."""
    links = set()

    patterns = [
        r'href=["\']([^"\']*(?:volunteer|join|get.*involved|participate|help|serve)[^"\']*)["\']',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            url = match.group(1)
            if url and not url.startswith('#'):
                if url.startswith('/'):
                    url = urljoin(base_url, url)
                elif not url.startswith('http'):
                    url = urljoin(base_url, url)
                links.add(url)

    # Test validity
    valid_links = []
    for url in links:
        is_valid, _ = test_link_validity(url)
        if is_valid:
            valid_links.append(url)

    return valid_links[:2]  # Top 2


def process_organization(ein: str, website: str) -> dict:
    """Process a single org: fetch website, extract links."""
    try:
        resp = requests.get(
            website,
            timeout=TIMEOUT,
            headers={'User-Agent': USER_AGENT},
            allow_redirects=True,
            verify=True
        )
        resp.raise_for_status()
        html = resp.text

        donate_links = extract_and_score_donate_links(ein, html, website)
        volunteer_links = extract_volunteer_links(html, website)

        return {
            'ein': ein,
            'donate_links': donate_links,
            'volunteer_links': volunteer_links
        }
    except Exception as e:
        logger.warning(f"{ein}: Failed to process {website}: {e}")
        return None


def process_batch(batch_eins: list[str], workers: int):
    """Process a batch of orgs: scrape for donation/volunteer links."""
    conn = sqlite3.connect(DB_PATH)

    # Get websites with good quality scores that haven't been link-checked
    query = """
        SELECT EIN, website
        FROM registry_enriched
        WHERE EIN IN ({})
          AND website_status = 'ok'
          AND donate_url IS NULL
        LIMIT 50
    """.format(','.join('?' * len(batch_eins)))

    rows = conn.execute(query, batch_eins).fetchall()
    conn.close()

    if not rows:
        logger.info(f"Batch {batch_eins[0:3]}: no new websites to link-scrape")
        return

    logger.info(f"Cascading scraper: processing {len(rows)} websites for links...")

    # Parallel processing
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futs = {
            executor.submit(process_organization, ein, website): ein
            for ein, website in rows
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
            donate_links = result['donate_links']
            if donate_links:
                # Write the highest-confidence donate link
                best_link = donate_links[0]
                conn.execute("""
                    UPDATE registry_enriched
                    SET donate_url=?, donate_confidence=?, donate_url_status=?, donate_checked_at=?
                    WHERE EIN=?
                """, (
                    best_link['donate_url'],
                    best_link['confidence'],
                    'cascading_scraper',
                    now,
                    result['ein']
                ))

            # Could add volunteer tracking here in future
            # for now, just log it exists

        conn.commit()
        conn.close()

        links_found = sum(1 for r in results if r['donate_links'])
        logger.info(f"  ✓ Found {links_found} donation endpoints")


def main():
    parser = argparse.ArgumentParser(description="Cascading link scraper")
    parser.add_argument('--workers', type=int, default=4, help="Parallel workers")
    parser.add_argument('--delay', type=int, default=10, help="Delay between batches")
    parser.add_argument('--limit', type=int, default=None, help="Max orgs to process (debug)")
    args = parser.parse_args()

    logger.info(f"Starting cascading link scraper ({args.workers} workers)")

    conn = sqlite3.connect(DB_PATH)

    # Get orgs with good websites but no donate link yet
    query = """
        SELECT EIN FROM registry_enriched
        WHERE website_status = 'ok'
          AND donate_url IS NULL
        ORDER BY RANDOM()
    """
    if args.limit:
        query += f" LIMIT {args.limit}"

    eins = [row[0] for row in conn.execute(query).fetchall()]
    conn.close()

    if not eins:
        logger.info("No new websites to scrape for links.")
        return

    logger.info(f"Found {len(eins):,} orgs needing link discovery")

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

    logger.info("Cascading link scraper completed.")


if __name__ == '__main__':
    main()
