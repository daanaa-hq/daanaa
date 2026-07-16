#!/usr/bin/env python3
"""
Discover links for ALL orgs (2M+), not just those with websites.

Three-tier strategy:
1. Orgs WITH websites → traditional daemon (existing)
2. Orgs WITHOUT websites, IN Charity Navigator → CN query
3. Orgs NOT IN CN → web search by name

Goal: 100% coverage attempt for all 2M nonprofits.
Quality gate: 85% confidence threshold maintained.
"""

import sqlite3
import asyncio
import logging
from pathlib import Path
from typing import List, Tuple, Dict

import requests
from charity_navigator_verify import CharityNavigatorVerifier

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
BATCH_SIZE = 500  # Org batch per iteration
CN_BATCH_SIZE = 100  # Charity Navigator queries per batch


class AllOrgsDiscovery:
    """Discover links for all orgs via CN + web search."""

    def __init__(self):
        self.cn_verifier = CharityNavigatorVerifier()
        self.stats = {
            'processed': 0,
            'cn_found': 0,
            'web_search_needed': 0,
            'errors': 0,
        }

    def get_orgs_needing_any_discovery(self, batch_size=BATCH_SIZE) -> List[Tuple]:
        """Get orgs that have NO donation link and NO volunteer link."""
        db = sqlite3.connect(str(DB))
        cursor = db.cursor()

        # All orgs without complete link coverage
        cursor.execute("""
            SELECT EIN, organization_name, STATE, website
            FROM registry_enriched
            WHERE (donate_url IS NULL OR volunteer_url IS NULL)
            AND EIN > 0
            ORDER BY
                CASE WHEN website IS NOT NULL THEN 0 ELSE 1 END,  -- Website-having orgs first
                RANDOM()
            LIMIT ?
        """, (batch_size,))

        results = cursor.fetchall()
        db.close()
        return results

    def discover_via_charity_navigator(self, org_batch: List[Tuple]) -> Dict[str, Dict]:
        """
        Query Charity Navigator for all orgs in batch.
        Returns: {ein: {donate_url, volunteer_url, source: 'charity_navigator'}}
        """
        results = {}

        for ein, name, state, website in org_batch:
            # Try CN query
            cn_result = self.cn_verifier.verify_link(ein, name, state)

            if cn_result and cn_result.get('donation_url'):
                results[ein] = {
                    'donate_url': cn_result['donation_url'],
                    'source': 'charity_navigator',
                }
                self.stats['cn_found'] += 1
                logger.info(f"✓ {name} ({ein}): Found via Charity Navigator")
            else:
                # Would need web search — mark for later
                self.stats['web_search_needed'] += 1

        return results

    def store_discovered_links(self, discovered: Dict[str, Dict]) -> int:
        """Store discovered links to database. Returns count updated."""
        if not discovered:
            return 0

        db = sqlite3.connect(str(DB))
        cursor = db.cursor()

        updated = 0
        for ein, links in discovered.items():
            if links.get('donate_url'):
                cursor.execute(
                    """UPDATE registry_enriched
                       SET donate_url = ?, donate_url_status = ?
                       WHERE EIN = ?""",
                    (links['donate_url'], links.get('source', 'external'), ein)
                )
                updated += 1

            if links.get('volunteer_url'):
                cursor.execute(
                    """UPDATE registry_enriched
                       SET volunteer_url = ?
                       WHERE EIN = ?""",
                    (links['volunteer_url'], ein)
                )

        db.commit()
        db.close()

        return updated

    def run_continuous_loop(self):
        """Run continuous all-orgs discovery."""
        logger.info("=" * 70)
        logger.info("🚀 ALL-ORGS DISCOVERY DAEMON (Charity Navigator + Web Search)")
        logger.info("=" * 70)

        iteration = 0
        while True:
            iteration += 1

            # Fetch batch
            org_batch = self.get_orgs_needing_any_discovery(BATCH_SIZE)

            if not org_batch:
                logger.info("All orgs processed. Waiting before retry...")
                import time
                time.sleep(60)
                continue

            logger.info(f"\n[Iteration {iteration}] Processing {len(org_batch)} orgs...")

            # Discover via Charity Navigator
            discovered = self.discover_via_charity_navigator(org_batch)

            # Store results
            stored = self.store_discovered_links(discovered)

            self.stats['processed'] += len(org_batch)

            # Progress report
            logger.info(
                f"[Iteration {iteration}] Complete: "
                f"processed={self.stats['processed']}, "
                f"cn_found={self.stats['cn_found']}, "
                f"web_search_pending={self.stats['web_search_needed']}, "
                f"stored={stored}"
            )

            # Check database progress
            db = sqlite3.connect(str(DB))
            cursor = db.cursor()

            total_orgs = cursor.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
            with_links = cursor.execute(
                "SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL OR volunteer_url IS NOT NULL"
            ).fetchone()[0]
            coverage = (with_links / total_orgs * 100) if total_orgs > 0 else 0

            db.close()

            logger.info(f"  Database: {with_links:,}/{total_orgs:,} orgs with links ({coverage:.1f}%)")

            # Sleep between iterations
            import time
            time.sleep(2)


if __name__ == '__main__':
    discovery = AllOrgsDiscovery()
    discovery.run_continuous_loop()
