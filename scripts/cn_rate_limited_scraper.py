#!/usr/bin/env python3
"""
Charity Navigator rate-limited scraper.
Gentle 1 req/sec to avoid getting blocked.

For orgs WITHOUT websites: query CN for verified donation links.
Runs independently, won't interfere with website discovery.

Usage: python3 scripts/cn_rate_limited_scraper.py [--limit 1000]
"""

import sqlite3
import time
import logging
import sys
from pathlib import Path

try:
    from charity_navigator_verify import CharityNavigatorVerifier
except ImportError:
    print("Error: charity_navigator_verify module required")
    sys.exit(1)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
RATE_LIMIT = 1.0  # 1 request per second (gentle on CN)


class RateLimitedCNScraper:
    """Gentle Charity Navigator scraper (won't get us blocked)."""

    def __init__(self):
        self.verifier = CharityNavigatorVerifier(timeout=10)
        self.stats = {
            'processed': 0,
            'found': 0,
            'not_found': 0,
            'errors': 0,
        }
        self.last_request_time = 0

    def rate_limit_wait(self):
        """Enforce 1 req/sec rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT:
            time.sleep(RATE_LIMIT - elapsed)
        self.last_request_time = time.time()

    def scrape_orgs_without_website(self, limit=None):
        """
        Query CN for orgs that have no website on file.
        Gentle 1 req/sec to avoid rate limiting.
        """
        db = sqlite3.connect(str(DB))
        cursor = db.cursor()

        # Orgs with NO website AND no donate link
        cursor.execute("""
            SELECT EIN, organization_name, STATE
            FROM registry_enriched
            WHERE (website IS NULL OR website = '')
            AND donate_url IS NULL
            AND EIN > 0
            ORDER BY RANDOM()
            LIMIT ?
        """, (limit or 10000,))

        orgs = cursor.fetchall()
        db.close()

        logger.info(f"Found {len(orgs)} orgs without website to query")

        updated = 0

        for ein, name, state in orgs:
            self.rate_limit_wait()  # 1 req/sec

            try:
                result = self.verifier.verify_link(ein, name, state)

                if result and result.get('donation_url'):
                    # Store in DB
                    db = sqlite3.connect(str(DB))
                    db.execute(
                        "UPDATE registry_enriched SET donate_url = ?, donate_url_status = 'charity_navigator' WHERE EIN = ?",
                        (result['donation_url'], ein)
                    )
                    db.commit()
                    db.close()

                    self.stats['found'] += 1
                    updated += 1
                    logger.info(f"✓ {name} ({ein}): Found via CN")

                else:
                    self.stats['not_found'] += 1

                self.stats['processed'] += 1

                # Progress every 100 orgs
                if self.stats['processed'] % 100 == 0:
                    logger.info(
                        f"Progress: {self.stats['processed']} processed, "
                        f"{self.stats['found']} found, "
                        f"{self.stats['not_found']} not found"
                    )

            except Exception as e:
                self.stats['errors'] += 1
                logger.warning(f"Error for {ein}: {str(e)[:100]}")

        logger.info(
            f"Scraping complete: "
            f"processed={self.stats['processed']}, "
            f"found={self.stats['found']}, "
            f"updated={updated}"
        )

        return updated


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Gentle Charity Navigator scraper (1 req/sec)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='Max orgs to query (default: 1000)'
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("🔍 CHARITY NAVIGATOR RATE-LIMITED SCRAPER")
    logger.info(f"   Rate: 1 req/sec (gentle, won't get blocked)")
    logger.info(f"   Limit: {args.limit} orgs")
    logger.info("=" * 70)

    scraper = RateLimitedCNScraper()
    scraper.scrape_orgs_without_website(limit=args.limit)
