#!/usr/bin/env python3
"""
State AG 990 Discovery: ProPublica Bulk Website Extraction
Discovers nonprofit websites from ProPublica's 1.8M organization database
that are not yet in Daanaa's registry.

Usage:
    python3 scripts/state_ag_discovery_propublica.py --limit 1000 --dry-run
    python3 scripts/state_ag_discovery_propublica.py --all --output results.csv
"""

import sys
import sqlite3
import requests
import logging
import csv
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import argparse
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path("/home/akbar/meritgiving/data/merit_registry.db")
OUTPUT_DIR = Path("/home/akbar/meritgiving/data/state_ag_discovery")
OUTPUT_DIR.mkdir(exist_ok=True)

PROPUBLICA_API_BASE = "https://projects.propublica.org/nonprofits/api/v2"
PROPUBLICA_RATE_LIMIT = 5  # requests per second

@dataclass
class Organization:
    """Organization record from ProPublica"""
    ein: str
    name: str
    website: Optional[str]
    city: str
    state: str
    zip_code: str
    ntee_code: Optional[str]
    subsection_code: str
    organization_id: str

class ProPublicaDiscovery:
    """Fetch and deduplicate organizations from ProPublica"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.daanaa_eins = set()
        self._load_daanaa_registry()

    def _load_daanaa_registry(self):
        """Load all EINs currently in Daanaa registry for deduplication"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE EIN IS NOT NULL")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT EIN FROM registry_enriched WHERE EIN IS NOT NULL AND EIN != ''")
            self.daanaa_eins = set(row[0] for row in cursor.fetchall())

            logger.info(f"Loaded {len(self.daanaa_eins):,} EINs from Daanaa registry (total {total:,} orgs)")
        except sqlite3.Error as e:
            logger.error(f"Database error loading registry: {e}")
            sys.exit(1)

    def fetch_all_orgs_with_websites(self, limit: Optional[int] = None) -> list[Organization]:
        """
        Fetch all organizations from ProPublica with website data.

        Note: ProPublica API doesn't support bulk export directly.
        This uses a pagination approach through the search endpoint.
        """
        organizations = []
        page = 1
        per_page = 100
        last_request_time = 0

        try:
            while True:
                # Rate limit: max 5 requests/sec
                elapsed = time.time() - last_request_time
                if elapsed < 0.2:  # 1/5 second
                    time.sleep(0.2 - elapsed)

                url = f"{PROPUBLICA_API_BASE}/organizations"
                params = {
                    'page': page,
                    'per_page': per_page,
                    'sort': 'name'
                }

                logger.info(f"Fetching page {page} ({per_page} orgs/page)...")
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                last_request_time = time.time()
                data = response.json()

                if not data.get('organizations'):
                    logger.info(f"Reached end of ProPublica data at page {page}")
                    break

                # Process each organization
                for org_data in data['organizations']:
                    org = Organization(
                        ein=org_data.get('ein', ''),
                        name=org_data.get('name', ''),
                        website=org_data.get('website', None),
                        city=org_data.get('city', ''),
                        state=org_data.get('state', ''),
                        zip_code=org_data.get('zip_code', ''),
                        ntee_code=org_data.get('ntee_code', None),
                        subsection_code=org_data.get('subsection_code', '3'),
                        organization_id=org_data.get('id', '')
                    )

                    if org.ein and org.website:  # Only include orgs with EIN and website
                        organizations.append(org)

                page += 1

                if limit and len(organizations) >= limit:
                    organizations = organizations[:limit]
                    logger.info(f"Reached limit of {limit} organizations")
                    break

                if page % 10 == 0:
                    logger.info(f"Progress: {len(organizations):,} orgs with websites found")

        except requests.RequestException as e:
            logger.error(f"API error: {e}")
            logger.info(f"Returning {len(organizations):,} orgs fetched so far")

        return organizations

    def deduplicate_against_daanaa(self, orgs: list[Organization]) -> tuple[list[Organization], dict]:
        """
        Filter organizations to only those not in Daanaa registry.
        Returns new orgs and statistics.
        """
        new_orgs = []
        stats = defaultdict(int)

        for org in orgs:
            stats['total_propublica'] += 1

            if org.ein in self.daanaa_eins:
                stats['already_in_daanaa'] += 1
                # Could still have missing website - could update existing
                continue
            else:
                new_orgs.append(org)
                stats['new_to_daanaa'] += 1

        stats['website_coverage'] = len([o for o in new_orgs if o.website]) / len(new_orgs) if new_orgs else 0

        return new_orgs, stats

    def export_to_csv(self, orgs: list[Organization], output_path: Path):
        """Export organizations to CSV for review/import"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'ein', 'name', 'website', 'city', 'state', 'zip_code',
                'ntee_code', 'subsection_code', 'organization_id', 'source'
            ])
            writer.writeheader()

            for org in orgs:
                writer.writerow({
                    'ein': org.ein,
                    'name': org.name,
                    'website': org.website or '',
                    'city': org.city,
                    'state': org.state,
                    'zip_code': org.zip_code,
                    'ntee_code': org.ntee_code or '',
                    'subsection_code': org.subsection_code,
                    'organization_id': org.organization_id,
                    'source': 'propublica_state_discovery'
                })

        logger.info(f"Exported {len(orgs)} orgs to {output_path}")

    def ingest_to_database(self, orgs: list[Organization], dry_run: bool = True):
        """Insert new organizations into Daanaa registry"""
        if not orgs:
            logger.warning("No organizations to ingest")
            return

        try:
            cursor = self.conn.cursor()
            inserted = 0
            updated = 0
            errors = 0

            for org in orgs:
                try:
                    # Check if org exists by EIN
                    cursor.execute("SELECT EIN FROM registry_enriched WHERE EIN = ?", (org.ein,))
                    exists = cursor.fetchone()

                    if exists:
                        # Update existing org with website if missing
                        if org.website:
                            if dry_run:
                                logger.info(f"[DRY RUN] Would update {org.ein}: {org.name} -> {org.website}")
                            else:
                                cursor.execute("""
                                    UPDATE registry_enriched
                                    SET website = ?, website_source = 'propublica_state_ag',
                                        website_checked_at = datetime('now')
                                    WHERE EIN = ? AND (website IS NULL OR website = '')
                                """, (org.website, org.ein))
                                updated += 1
                    else:
                        # Insert new organization
                        if dry_run:
                            logger.info(f"[DRY RUN] Would insert {org.ein}: {org.name}")
                        else:
                            cursor.execute("""
                                INSERT INTO registry_enriched (
                                    EIN, organization_name, website, CITY, STATE, zipcode,
                                    NTEECC, subsection, source, data_source, website_source,
                                    website_checked_at, updated_at, org_status
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 'active')
                            """, (
                                org.ein, org.name, org.website, org.city, org.state,
                                org.zip_code, org.ntee_code or '', org.subsection_code,
                                'propublica', 'propublica_state_ag',
                                'propublica_state_ag'
                            ))
                            inserted += 1
                except sqlite3.Error as e:
                    errors += 1
                    logger.error(f"Error processing {org.ein}: {e}")

            if not dry_run:
                self.conn.commit()
                logger.info(f"Committed: {inserted} new orgs, {updated} updates, {errors} errors")
            else:
                logger.info(f"[DRY RUN] Would commit: {inserted} new orgs, {updated} updates, {errors} errors")

        except sqlite3.Error as e:
            logger.error(f"Database error during ingest: {e}")
            if not dry_run:
                self.conn.rollback()

def main():
    parser = argparse.ArgumentParser(
        description="Discover nonprofit websites from ProPublica database"
    )
    parser.add_argument('--limit', type=int, default=1000,
                        help='Limit number of orgs to fetch (default: 1000)')
    parser.add_argument('--all', action='store_true',
                        help='Fetch all available orgs (overrides --limit)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without database changes')
    parser.add_argument('--output', type=str, default='propublica_discovery.csv',
                        help='Output CSV filename')
    parser.add_argument('--no-fetch', action='store_true',
                        help='Skip API fetch, use cached data')

    args = parser.parse_args()

    logger.info("="*70)
    logger.info("State AG 990 Discovery - ProPublica Bulk Extract")
    logger.info("="*70)

    discovery = ProPublicaDiscovery(DB_PATH)

    if args.no_fetch:
        logger.info("Skipping API fetch (using cached data)")
        # Would load from cache here
        return

    # Fetch organizations
    limit = None if args.all else args.limit
    logger.info(f"Fetching ProPublica orgs (limit: {limit or 'all'})...")
    orgs = discovery.fetch_all_orgs_with_websites(limit=limit)
    logger.info(f"Fetched {len(orgs):,} organizations with websites from ProPublica")

    # Deduplicate against Daanaa
    new_orgs, stats = discovery.deduplicate_against_daanaa(orgs)

    logger.info("\n" + "="*70)
    logger.info("DEDUPLICATION RESULTS")
    logger.info("="*70)
    logger.info(f"Total from ProPublica (with website): {stats['total_propublica']:,}")
    logger.info(f"Already in Daanaa: {stats['already_in_daanaa']:,}")
    logger.info(f"New to Daanaa: {stats['new_to_daanaa']:,}")
    logger.info(f"Website coverage in new orgs: {stats['website_coverage']:.1%}")

    if new_orgs:
        # Export to CSV
        output_path = OUTPUT_DIR / args.output
        discovery.export_to_csv(new_orgs, output_path)

        # Optionally ingest to database
        if not args.dry_run:
            logger.info("\nIngesting new orgs to database...")
            discovery.ingest_to_database(new_orgs, dry_run=args.dry_run)
        else:
            logger.info("\n[DRY RUN MODE] Simulating database ingest...")
            discovery.ingest_to_database(new_orgs, dry_run=True)

    logger.info("\n" + "="*70)
    logger.info(f"Discovery complete. Export: {OUTPUT_DIR / args.output}")
    logger.info("="*70)

if __name__ == '__main__':
    main()
