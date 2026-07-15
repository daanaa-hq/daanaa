#!/usr/bin/env python3
"""
Batch discovery enrichment for all organizations.

Finds websites, donation links, volunteer opportunities, GitHub repos, and skills.sh profiles
for all 2M organizations in the registry. ONLY STORES VERIFIED LINKS.

Verification process:
- Donation links: HTTP 200 + payment keywords or payment processor detected
- Volunteer links: HTTP 200 + volunteer keywords found
- GitHub/skills.sh: Detected and stored (no content verification needed)
"""

import sqlite3
import json
import requests
from datetime import datetime
from website_discovery_comprehensive import WebsiteDiscovery
from verify_discovered_links import LinkVerifier
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryBatchProcessor:
    """Batch process organizational discovery."""

    def __init__(self, db_path='/home/akbar/meritgiving/data/merit_registry.db'):
        self.db_path = db_path
        self.discovery = WebsiteDiscovery(timeout=15)
        self.verifier = LinkVerifier(timeout=10)
        self.stats = {
            'total_processed': 0,
            'websites_found': 0,
            'donation_links_found': 0,
            'donation_links_verified': 0,
            'volunteer_links_found': 0,
            'volunteer_links_verified': 0,
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

            # Donation links — verify before storing
            if discovery_result['donation_links'] and not current_donate_url:
                donate_link = discovery_result['donation_links'][0]
                self.stats['donation_links_found'] += 1

                # Verify the link
                verification = self.verifier.verify_donation_link(donate_link['url'])
                if verification.get('verified'):
                    updates['donate_url'] = donate_link['url']
                    updates['donate_confidence'] = int(donate_link.get('confidence', 0.85) * 100)
                    updates['donate_url_status'] = 'verified'
                    updates['donate_checked_at'] = datetime.now().isoformat()
                    self.stats['donation_links_verified'] += 1
                else:
                    # Link failed verification, don't store it
                    logger.info(f"Donation link rejected for {ein}: {verification.get('reason')}")

            # Volunteer links — verify before storing
            if discovery_result['volunteer_links'] and not current_volunteer_url:
                volunteer_link = discovery_result['volunteer_links'][0]
                self.stats['volunteer_links_found'] += 1

                # Verify the link
                verification = self.verifier.verify_volunteer_link(volunteer_link['url'])
                if verification.get('verified'):
                    updates['volunteer_url'] = volunteer_link['url']
                    self.stats['volunteer_links_verified'] += 1
                else:
                    # Link failed verification, don't store it
                    logger.info(f"Volunteer link rejected for {ein}: {verification.get('reason')}")

            # GitHub repos
            if discovery_result['github_repos']:
                github_link = discovery_result['github_repos'][0]
                updates['github_repo'] = github_link['url']
                self.stats['github_repos_found'] += 1

            # Skills.sh profiles
            if discovery_result['skills_profiles']:
                skills_link = discovery_result['skills_profiles'][0]
                updates['skills_sh_profile'] = skills_link['url']

            # Donate button text (from first donate link)
            if discovery_result['donation_links'] and not current_donate_url:
                donate_link = discovery_result['donation_links'][0]
                if donate_link.get('text'):
                    updates['donate_button_text'] = donate_link['text']

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
