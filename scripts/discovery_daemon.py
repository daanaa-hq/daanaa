#!/usr/bin/env python3
"""
Continuous discovery daemon.

Runs 24/7, finding and verifying links. Verified links queued for
batch deployment every 4 hours.

Process:
1. Find orgs without links
2. Discover links on their websites
3. Verify links are live + correct type
4. Queue verified links for deployment
5. Repeat continuously (rate-limited to avoid overwhelming servers)
"""

import sqlite3
import time
import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from website_discovery_comprehensive import WebsiteDiscovery
from verify_discovered_links import LinkVerifier

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/discovery_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


class ContinuousDiscoveryDaemon:
    """Runs discovery continuously, queuing verified links."""

    def __init__(self):
        self.discovery = WebsiteDiscovery(timeout=15)
        self.verifier = LinkVerifier(timeout=10)
        self.stats = {
            'discovered': 0,
            'verified': 0,
            'queued': 0,
            'errors': 0
        }

    def get_orgs_needing_discovery(self, batch_size=50):
        """Get organizations with websites but missing links."""
        db = sqlite3.connect(str(DB))
        cursor = db.cursor()

        cursor.execute("""
            SELECT EIN, organization_name, website
            FROM registry_enriched
            WHERE website IS NOT NULL
            AND website != ''
            AND (
                donate_url IS NULL
                OR volunteer_url IS NULL
            )
            AND EIN > 0
            ORDER BY RANDOM()
            LIMIT ?
        """, (batch_size,))

        results = cursor.fetchall()
        db.close()
        return results

    def discover_and_verify_org(self, ein, name, website):
        """Discover and verify links for one org."""
        try:
            # Discover
            result = self.discovery.discover_all(website)
            if 'error' in result:
                return {'status': 'error', 'reason': result['error']}

            verified_links = {}

            # Verify donation link
            if result.get('donation_links'):
                donate_url = result['donation_links'][0]['url']
                verification = self.verifier.verify_donation_link(donate_url)
                if verification.get('verified'):
                    verified_links['donate_url'] = donate_url
                    verified_links['donate_button_text'] = result['donation_links'][0].get('text', '')
                    self.stats['verified'] += 1
                self.stats['discovered'] += 1

            # Verify volunteer link
            if result.get('volunteer_links'):
                volunteer_url = result['volunteer_links'][0]['url']
                verification = self.verifier.verify_volunteer_link(volunteer_url)
                if verification.get('verified'):
                    verified_links['volunteer_url'] = volunteer_url
                    self.stats['verified'] += 1
                self.stats['discovered'] += 1

            # GitHub (no verification needed, URL format is sufficient)
            if result.get('github_repos'):
                verified_links['github_repo'] = result['github_repos'][0]['url']

            # skills.sh (no verification needed)
            if result.get('skills_profiles'):
                verified_links['skills_sh_profile'] = result['skills_profiles'][0]['url']

            if verified_links:
                self.queue_verified_links(ein, verified_links)
                self.stats['queued'] += 1
                return {'status': 'success', 'verified': len(verified_links)}
            else:
                return {'status': 'no_links'}

        except Exception as e:
            self.stats['errors'] += 1
            logger.warning(f"Error processing {ein}: {str(e)[:100]}")
            return {'status': 'error', 'reason': str(e)[:100]}

    def queue_verified_links(self, ein, links):
        """Queue verified links for batch deployment."""
        db = sqlite3.connect(str(DB))
        cursor = db.cursor()

        # Create queue table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS link_deployment_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ein INTEGER NOT NULL,
                links JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deployed_at TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT INTO link_deployment_queue (ein, links)
            VALUES (?, ?)
        """, (ein, json.dumps(links)))

        db.commit()
        db.close()

    def run_continuous_loop(self, batch_size=50, sleep_between_batches=5):
        """Run discovery continuously."""
        logger.info("=" * 60)
        logger.info("🚀 CONTINUOUS DISCOVERY DAEMON STARTED")
        logger.info("=" * 60)

        iteration = 0
        while True:
            iteration += 1
            try:
                logger.info(f"[Iteration {iteration}] Fetching {batch_size} orgs needing discovery...")
                orgs = self.get_orgs_needing_discovery(batch_size)

                if not orgs:
                    logger.info("No more orgs needing discovery, waiting before retry...")
                    time.sleep(60)
                    continue

                for ein, name, website in orgs:
                    result = self.discover_and_verify_org(ein, name, website)
                    if result['status'] == 'success':
                        logger.info(f"✅ {name} ({ein}): {result['verified']} links verified")
                    elif result['status'] == 'no_links':
                        logger.debug(f"⚪ {name} ({ein}): No links found")
                    else:
                        logger.warning(f"❌ {name} ({ein}): {result.get('reason')}")

                    # Rate limit
                    time.sleep(0.5)

                # Log progress
                logger.info(
                    f"[Iteration {iteration}] Progress: "
                    f"discovered={self.stats['discovered']}, "
                    f"verified={self.stats['verified']}, "
                    f"queued={self.stats['queued']}, "
                    f"errors={self.stats['errors']}"
                )

                # Sleep between batches
                logger.info(f"Sleeping {sleep_between_batches}s before next batch...")
                time.sleep(sleep_between_batches)

            except KeyboardInterrupt:
                logger.info("⏹️  Daemon stopped by user")
                break
            except Exception as e:
                logger.error(f"Fatal error in loop: {e}")
                time.sleep(60)  # Wait before retry


if __name__ == '__main__':
    daemon = ContinuousDiscoveryDaemon()
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    daemon.run_continuous_loop(batch_size=batch_size)
