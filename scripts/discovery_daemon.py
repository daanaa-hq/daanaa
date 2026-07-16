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
from gpu_link_verifier import GPULinkVerifier

try:
    from charity_navigator_verify import CharityNavigatorVerifier
    CN_AVAILABLE = True
except ImportError:
    CN_AVAILABLE = False

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

    def __init__(self, use_cn_fallback=True):
        self.discovery = WebsiteDiscovery(timeout=15)
        self.verifier = LinkVerifier(timeout=10)
        self.gpu_verifier = GPULinkVerifier()  # GPU-accelerated semantic verification
        self.cn_verifier = CharityNavigatorVerifier(timeout=10) if CN_AVAILABLE and use_cn_fallback else None
        self.stats = {
            'discovered': 0,
            'verified': 0,
            'queued': 0,
            'errors': 0,
            'cn_verified': 0,
            'gpu_verified': 0
        }

    def get_orgs_needing_discovery(self, batch_size=50):
        """Get ALL active 501c3 organizations missing links, ordered by revenue (high to low)."""
        db = sqlite3.connect(str(DB))
        cursor = db.cursor()

        cursor.execute("""
            SELECT EIN, organization_name, website, STATE
            FROM registry_enriched
            WHERE (
                donate_url IS NULL
                OR volunteer_url IS NULL
            )
            AND EIN > 0
            AND org_status = 'active'
            ORDER BY
                CASE WHEN website IS NOT NULL AND website != '' THEN 0 ELSE 1 END,
                total_revenue DESC NULLS LAST
            LIMIT ?
        """, (batch_size,))

        results = cursor.fetchall()
        db.close()
        return results

    def apply_gpu_enhancement(self, links_dict):
        """Apply GPU semantic verification to boost confidence (non-blocking, fail-fast)."""
        if not links_dict:
            return links_dict

        # Build candidates for GPU verification
        candidates = []
        link_types = []

        if 'donate_url' in links_dict:
            candidates.append({
                'url': links_dict['donate_url'],
                'text': links_dict.get('donate_button_text', 'Donate'),
                'link_type': 'donate'
            })
            link_types.append('donate')

        if 'volunteer_url' in links_dict:
            candidates.append({
                'url': links_dict['volunteer_url'],
                'text': 'Volunteer',
                'link_type': 'volunteer'
            })
            link_types.append('volunteer')

        if not candidates:
            return links_dict

        # Run GPU verification (non-blocking with short timeout)
        try:
            verified = self.gpu_verifier.verify_batch(candidates)
            self.stats['gpu_verified'] += len(verified)

            # Enrich links with GPU semantic match scores
            for i, link_type in enumerate(link_types):
                if i < len(verified):
                    key_name = f'{link_type}_url'
                    if key_name in links_dict:
                        links_dict[f'{key_name}_semantic_match'] = verified[i].get('semantic_match', 0.0)
        except Exception as e:
            logger.debug(f"GPU enhancement failed (non-blocking): {e}")

        return links_dict

    def discover_and_verify_org(self, ein, name, website, state=None):
        """Discover and verify links for one org (website or CN fallback)."""
        try:
            verified_links = {}

            # If no website, skip to CN fallback immediately
            if not website or website.strip() == '':
                if self.cn_verifier:
                    cn_result = self.cn_verifier.verify_link(ein, name, state)
                    if cn_result and cn_result.get('donation_url'):
                        verified_links['donate_url'] = cn_result['donation_url']
                        verified_links['donate_source'] = 'charity_navigator'
                        self.stats['cn_verified'] += 1
                        self.stats['verified'] += 1

                if verified_links:
                    verified_links = self.apply_gpu_enhancement(verified_links)
                    self.queue_verified_links(ein, verified_links)
                    self.stats['queued'] += 1
                    return {'status': 'success', 'verified': len(verified_links)}
                else:
                    return {'status': 'no_links'}

            # Discover from website
            result = self.discovery.discover_all(website)
            if 'error' in result:
                # Fall back to CN if website fetch fails
                if self.cn_verifier:
                    cn_result = self.cn_verifier.verify_link(ein, name, state)
                    if cn_result and cn_result.get('donation_url'):
                        verified_links['donate_url'] = cn_result['donation_url']
                        verified_links['donate_source'] = 'charity_navigator'
                        self.stats['cn_verified'] += 1
                        self.stats['verified'] += 1
                        verified_links = self.apply_gpu_enhancement(verified_links)
                        self.queue_verified_links(ein, verified_links)
                        self.stats['queued'] += 1
                        return {'status': 'success', 'verified': len(verified_links)}
                return {'status': 'error', 'reason': result['error']}

            # Verify donation link from website
            if result.get('donation_links'):
                donate_url = result['donation_links'][0]['url']
                verification = self.verifier.verify_donation_link(donate_url)
                if verification.get('verified'):
                    verified_links['donate_url'] = donate_url
                    verified_links['donate_button_text'] = result['donation_links'][0].get('text', '')
                    self.stats['verified'] += 1
                self.stats['discovered'] += 1

            # Verify volunteer link from website
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

            # Fallback to Charity Navigator if no donation link found (90% confidence gate)
            if not verified_links.get('donate_url') and self.cn_verifier:
                cn_result = self.cn_verifier.verify_link(ein, name, state)
                if cn_result and cn_result.get('donation_url'):
                    verified_links['donate_url'] = cn_result['donation_url']
                    verified_links['donate_source'] = 'charity_navigator'
                    self.stats['cn_verified'] += 1
                    self.stats['verified'] += 1

            if verified_links:
                verified_links = self.apply_gpu_enhancement(verified_links)
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
        """Queue verified links for approval.

        All verified links from discovery go to pending queue.
        These are already verified by the verification pipeline.
        """
        db = sqlite3.connect(str(DB))
        cursor = db.cursor()

        # Create queue table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS link_deployment_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ein INTEGER NOT NULL,
                links JSON NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deployed_at TIMESTAMP
            )
        """)

        # Queue all verified links for approval
        cursor.execute("SELECT id FROM link_deployment_queue WHERE ein = ? AND deployed_at IS NULL", (ein,))
        existing = cursor.fetchone()

        if existing:
            # Update existing entry
            cursor.execute(
                "UPDATE link_deployment_queue SET links = ? WHERE ein = ? AND deployed_at IS NULL",
                (json.dumps(links), ein)
            )
        else:
            # Insert new entry
            cursor.execute("""
                INSERT INTO link_deployment_queue (ein, links, status)
                VALUES (?, ?, 'pending')
            """, (ein, json.dumps(links)))

        logger.info(f"✓ {ein}: {len(links)} links queued for approval")

        db.commit()
        db.close()

    def run_continuous_loop(self, batch_size=50, sleep_between_batches=5, sleep_between_orgs=0.5):
        """Run discovery continuously."""
        logger.info("=" * 60)
        logger.info("🚀 CONTINUOUS DISCOVERY DAEMON STARTED")
        logger.info(f"   Batch size: {batch_size} | Sleep: {sleep_between_orgs}s/org, {sleep_between_batches}s/batch")
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

                for ein, name, website, state in orgs:
                    result = self.discover_and_verify_org(ein, name, website, state)
                    if result['status'] == 'success':
                        logger.info(f"✅ {name} ({ein}): {result['verified']} links verified")
                    elif result['status'] == 'no_links':
                        logger.debug(f"⚪ {name} ({ein}): No links found")
                    else:
                        logger.warning(f"❌ {name} ({ein}): {result.get('reason')}")

                    # Rate limit
                    time.sleep(sleep_between_orgs)

                # Log progress with confidence breakdown
                db = sqlite3.connect(str(DB))
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE status = 'pending'")
                high_conf = cursor.fetchone()[0] or 0
                cursor.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE status = 'under_review'")
                under_review = cursor.fetchone()[0] or 0
                db.close()

                logger.info(
                    f"[Iteration {iteration}] Progress: "
                    f"discovered={self.stats['discovered']}, "
                    f"verified={self.stats['verified']}, "
                    f"gpu_enhanced={self.stats['gpu_verified']}, "
                    f"queued={self.stats['queued']}, "
                    f"cn_verified={self.stats['cn_verified']}, "
                    f"errors={self.stats['errors']} | "
                    f"Queue: {high_conf} (90%+) | {under_review} (under review)"
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
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    sleep_between_orgs = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    sleep_between_batches = float(sys.argv[3]) if len(sys.argv) > 3 else 5
    use_cn = sys.argv[4].lower() != 'no_cn' if len(sys.argv) > 4 else True

    daemon = ContinuousDiscoveryDaemon(use_cn_fallback=use_cn)
    daemon.run_continuous_loop(
        batch_size=batch_size,
        sleep_between_orgs=sleep_between_orgs,
        sleep_between_batches=sleep_between_batches
    )
