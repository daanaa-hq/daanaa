#!/usr/bin/env python3
"""
Batch discovery enrichment for all organizations.

Finds websites, donation links, volunteer opportunities, GitHub repos, and skills.sh profiles
for all 2M organizations in the registry. Runs in phases:
- Phase 1: Query organizations with no website but known donation/volunteer activity
- Phase 2: Web search + discovery for orgs with websites
- Phase 3: Full discovery run for remaining orgs
"""

import sqlite3
import json
import requests
from datetime import datetime
from website_discovery_comprehensive import WebsiteDiscovery
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryBatchProcessor:
    """Batch process organizational discovery."""

    def __init__(self, db_path='/home/akbar/meritgiving/data/merit_registry.db'):
        self.db_path = db_path
        self.discovery = WebsiteDiscovery(timeout=15)
        self.stats = {
            'total_processed': 0,
            'websites_found': 0,
            'donation_links_found': 0,
            'volunteer_links_found': 0,
            'github_repos_found': 0,
            'errors': 0,
            'skipped': 0
        }

    def get_orgs_to_process(self, limit=1000, offset=0):
        """Get organizations to process."""
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()

        # Get orgs with websites but no donation URL
        cursor.execute("""
            SELECT
                EIN,
                organization_name,
                website,
                donate_url,
                volunteer_url
            FROM registry_enriched
            WHERE website IS NOT NULL
            AND website != ''
            AND (donate_url IS NULL OR volunteer_url IS NULL)
            AND EIN > 0
            ORDER BY total_revenue DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        results = cursor.fetchall()
        db.close()
        return results

    def process_org(self, ein, name, website, current_donate_url, current_volunteer_url):
        """Process a single organization."""
        try:
            if not website:
                self.stats['skipped'] += 1
                return None

            # Run discovery
            discovery_result = self.discovery.discover_all(website)

            if 'error' in discovery_result:
                logger.warning(f"Discovery failed for {name} ({ein}): {discovery_result['error']}")
                self.stats['errors'] += 1
                return None

            # Extract results
            updates = {}

            # Donation links
            if discovery_result['donation_links'] and not current_donate_url:
                donate_link = discovery_result['donation_links'][0]
                updates['donate_url'] = donate_link['url']
                updates['donate_confidence'] = int(donate_link.get('confidence', 0.85) * 100)
                self.stats['donation_links_found'] += 1

            # Volunteer links
            if discovery_result['volunteer_links'] and not current_volunteer_url:
                volunteer_link = discovery_result['volunteer_links'][0]
                updates['volunteer_url'] = volunteer_link['url']
                self.stats['volunteer_links_found'] += 1

            # GitHub repos (store in discovery data for now)
            if discovery_result['github_repos']:
                self.stats['github_repos_found'] += 1

            if updates:
                self._update_org(ein, updates)
                self.stats['total_processed'] += 1

            return updates

        except Exception as e:
            logger.error(f"Error processing {ein}: {e}")
            self.stats['errors'] += 1
            return None

    def _update_org(self, ein, updates):
        """Update organization in database."""
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()

        update_fields = []
        values = []

        for key, value in updates.items():
            update_fields.append(f"{key} = ?")
            values.append(value)

        update_fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())

        values.append(ein)

        query = f"UPDATE registry_enriched SET {', '.join(update_fields)} WHERE EIN = ?"
        cursor.execute(query, values)
        db.commit()
        db.close()

    def run_batch(self, batch_size=100, max_orgs=None):
        """Run batch discovery on organizations."""
        offset = 0
        processed_total = 0

        while True:
            if max_orgs and processed_total >= max_orgs:
                break

            orgs = self.get_orgs_to_process(limit=batch_size, offset=offset)

            if not orgs:
                break

            for ein, name, website, donate_url, volunteer_url in orgs:
                try:
                    self.process_org(ein, name, website, donate_url, volunteer_url)
                    processed_total += 1

                    if processed_total % 100 == 0:
                        logger.info(f"Processed {processed_total} orgs...")
                        self._report_progress()

                except Exception as e:
                    logger.error(f"Fatal error on {ein}: {e}")
                    self.stats['errors'] += 1

            offset += batch_size

            # Rate limiting
            time.sleep(0.5)

        return self.stats

    def _report_progress(self):
        """Print progress report."""
        logger.info(f"""
        Progress Report:
        - Total processed: {self.stats['total_processed']}
        - Websites found: {self.stats['websites_found']}
        - Donation links: {self.stats['donation_links_found']}
        - Volunteer links: {self.stats['volunteer_links_found']}
        - GitHub repos: {self.stats['github_repos_found']}
        - Errors: {self.stats['errors']}
        - Skipped: {self.stats['skipped']}
        """)


if __name__ == "__main__":
    import sys

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    max_orgs = int(sys.argv[2]) if len(sys.argv) > 2 else None

    processor = DiscoveryBatchProcessor()

    print("=" * 60)
    print("DISCOVERY BATCH ENRICHMENT")
    print("=" * 60)
    print()

    stats = processor.run_batch(batch_size=batch_size, max_orgs=max_orgs)

    print()
    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(json.dumps(stats, indent=2))
