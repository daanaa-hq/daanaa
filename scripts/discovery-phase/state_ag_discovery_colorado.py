#!/usr/bin/env python3
"""
State AG 990 Discovery: Colorado CSV Import
Discovers nonprofit websites from Colorado's public nonprofit registry.
Data source: https://data.colorado.gov/ - Colorado Nonprofits database

Usage:
    python3 scripts/state_ag_discovery_colorado.py --csv colorado_nonprofits.csv --dry-run
    python3 scripts/state_ag_discovery_colorado.py --csv data.csv --output co_discovery.csv
"""

import sys
import sqlite3
import csv
import logging
import requests
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import argparse
from collections import defaultdict
from difflib import SequenceMatcher
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path("/home/akbar/meritgiving/data/merit_registry.db")
OUTPUT_DIR = Path("/home/akbar/meritgiving/data/state_ag_discovery")
OUTPUT_DIR.mkdir(exist_ok=True)

@dataclass
class ColoradoOrg:
    """Colorado nonprofit record"""
    legal_name: str
    dba_name: Optional[str]
    website: Optional[str]
    address: str
    city: str
    state: str
    zip_code: str
    phone: Optional[str]
    email: Optional[str]
    ein: Optional[str]
    registration_status: str
    county: Optional[str]

class ColoradoDiscovery:
    """Process Colorado nonprofit CSV and discover new websites"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.daanaa_eins = set()
        self.daanaa_orgs_by_name = {}
        self._load_daanaa_registry()

    def _load_daanaa_registry(self):
        """Load Daanaa registry for deduplication"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            # Load by EIN
            cursor.execute("SELECT EIN FROM registry_enriched WHERE EIN IS NOT NULL AND EIN != ''")
            self.daanaa_eins = set(row[0] for row in cursor.fetchall())

            # Load by name for fuzzy matching
            cursor.execute("""
                SELECT organization_name, EIN FROM registry_enriched
                WHERE organization_name IS NOT NULL AND organization_name != ''
            """)
            self.daanaa_orgs_by_name = {row[0].upper(): row[1] for row in cursor.fetchall()}

            logger.info(f"Loaded {len(self.daanaa_eins):,} EINs from Daanaa registry")
            logger.info(f"Loaded {len(self.daanaa_orgs_by_name):,} org names from Daanaa registry")

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            sys.exit(1)

    def parse_colorado_csv(self, csv_path: Path) -> list[ColoradoOrg]:
        """Parse Colorado nonprofit CSV file"""
        orgs = []

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                # Print sample headers for debugging
                if reader.fieldnames:
                    logger.info(f"CSV columns: {reader.fieldnames[:10]}")

                for row in reader:
                    # Map CSV columns (adjust based on actual Colorado data format)
                    org = ColoradoOrg(
                        legal_name=row.get('Charity Name', '').strip(),
                        dba_name=row.get('DBA', '').strip() or None,
                        website=row.get('Website URL', '').strip() or None,
                        address=row.get('Street Address', '').strip(),
                        city=row.get('City', '').strip(),
                        state=row.get('State', '').strip() or 'CO',
                        zip_code=row.get('Zip Code', '').strip() or row.get('ZIP', '').strip(),
                        phone=row.get('Phone', '').strip() or None,
                        email=row.get('Email', '').strip() or None,
                        ein=row.get('EIN', '').strip() or None,
                        registration_status=row.get('Status', 'Active').strip(),
                        county=row.get('County', '').strip() or None
                    )

                    if org.legal_name:  # Only include if we have a name
                        orgs.append(org)

            logger.info(f"Parsed {len(orgs):,} organizations from Colorado CSV")
            return orgs

        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            sys.exit(1)

    def fuzzy_match_name(self, co_name: str, threshold: float = 0.85) -> Optional[str]:
        """
        Fuzzy match Colorado org name against Daanaa registry.
        Returns EIN if match found, None otherwise.
        """
        co_name_upper = co_name.upper()

        # Exact match first
        if co_name_upper in self.daanaa_orgs_by_name:
            return self.daanaa_orgs_by_name[co_name_upper]

        # Fuzzy match with threshold
        best_match = None
        best_ratio = 0

        for daanaa_name, ein in self.daanaa_orgs_by_name.items():
            ratio = SequenceMatcher(None, co_name_upper, daanaa_name).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                if ratio >= threshold:
                    best_match = ein

        if best_match and best_ratio >= threshold:
            logger.debug(f"Fuzzy match: {co_name} -> {best_match} ({best_ratio:.2%})")
            return best_match

        return None

    def deduplicate_and_enrich(self, co_orgs: list[ColoradoOrg]) -> tuple[list[ColoradoOrg], dict]:
        """
        Deduplicate Colorado orgs against Daanaa.
        Returns new orgs and match statistics.
        """
        new_orgs = []
        stats = defaultdict(int)
        matches_by_strategy = defaultdict(int)

        for org in co_orgs:
            stats['total_colorado'] += 1

            # Strategy 1: Exact EIN match
            if org.ein and org.ein in self.daanaa_eins:
                stats['exact_ein_match'] += 1
                matches_by_strategy['ein'] += 1
                # Could enrich website if missing
                continue

            # Strategy 2: Fuzzy name match
            matched_ein = self.fuzzy_match_name(org.legal_name)
            if matched_ein:
                stats['fuzzy_name_match'] += 1
                matches_by_strategy['name'] += 1
                org.ein = matched_ein  # Use matched EIN
                # Could enrich website if missing
                continue

            # No match found - new to Daanaa
            stats['new_to_daanaa'] += 1
            new_orgs.append(org)

        stats['website_coverage'] = len([o for o in new_orgs if o.website]) / len(new_orgs) if new_orgs else 0

        logger.info("\nMatch Strategy Breakdown:")
        for strategy, count in matches_by_strategy.items():
            logger.info(f"  {strategy}: {count:,}")

        return new_orgs, stats

    def export_to_csv(self, orgs: list[ColoradoOrg], output_path: Path):
        """Export Colorado organizations to CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'legal_name', 'dba_name', 'website', 'address', 'city', 'state',
                'zip_code', 'phone', 'email', 'ein', 'registration_status', 'county', 'source'
            ])
            writer.writeheader()

            for org in orgs:
                writer.writerow({
                    'legal_name': org.legal_name,
                    'dba_name': org.dba_name or '',
                    'website': org.website or '',
                    'address': org.address,
                    'city': org.city,
                    'state': org.state,
                    'zip_code': org.zip_code,
                    'phone': org.phone or '',
                    'email': org.email or '',
                    'ein': org.ein or '',
                    'registration_status': org.registration_status,
                    'county': org.county or '',
                    'source': 'colorado_state_ag'
                })

        logger.info(f"Exported {len(orgs)} orgs to {output_path}")

    def ingest_to_database(self, orgs: list[ColoradoOrg], dry_run: bool = True):
        """Insert new Colorado organizations into Daanaa registry"""
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
                    # Try to match by EIN first
                    if org.ein:
                        cursor.execute("SELECT EIN FROM registry_enriched WHERE EIN = ?", (org.ein,))
                        exists = cursor.fetchone()

                        if exists:
                            # Update existing with website if missing
                            if org.website:
                                if dry_run:
                                    logger.info(f"[DRY RUN] Update {org.ein}: {org.legal_name} -> website")
                                else:
                                    cursor.execute("""
                                        UPDATE registry_enriched
                                        SET website = ?, website_source = 'colorado_state_ag'
                                        WHERE EIN = ? AND (website IS NULL OR website = '')
                                    """, (org.website, org.ein))
                                    updated += 1
                            continue

                    # Insert new organization
                    if dry_run:
                        logger.info(f"[DRY RUN] Insert: {org.legal_name} ({org.ein or 'no EIN'})")
                    else:
                        cursor.execute("""
                            INSERT INTO registry_enriched (
                                EIN, organization_name, website, CITY, STATE, zipcode,
                                street_address, source, data_source, website_source,
                                website_checked_at, updated_at, org_status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 'active')
                        """, (
                            org.ein or '',
                            org.legal_name,
                            org.website,
                            org.city,
                            org.state,
                            org.zip_code,
                            org.address,
                            'colorado_ag',
                            'colorado_state_ag',
                            'colorado_state_ag'
                        ))
                        inserted += 1

                except sqlite3.Error as e:
                    errors += 1
                    logger.error(f"Error processing {org.legal_name}: {e}")

            if not dry_run:
                self.conn.commit()
                logger.info(f"Committed: {inserted} new, {updated} updated, {errors} errors")
            else:
                logger.info(f"[DRY RUN] Would commit: {inserted} new, {updated} updated, {errors} errors")

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if not dry_run:
                self.conn.rollback()

def main():
    parser = argparse.ArgumentParser(
        description="Discover nonprofit websites from Colorado state registry"
    )
    parser.add_argument('--csv', type=str, required=True,
                        help='Path to Colorado nonprofit CSV file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without database changes')
    parser.add_argument('--output', type=str, default='colorado_discovery.csv',
                        help='Output CSV filename')

    args = parser.parse_args()

    logger.info("="*70)
    logger.info("State AG 990 Discovery - Colorado CSV Import")
    logger.info("="*70)

    discovery = ColoradoDiscovery(DB_PATH)

    # Parse Colorado CSV
    logger.info(f"Parsing Colorado CSV: {args.csv}")
    co_orgs = discovery.parse_colorado_csv(Path(args.csv))

    # Deduplicate
    logger.info("Deduplicating against Daanaa registry...")
    new_orgs, stats = discovery.deduplicate_and_enrich(co_orgs)

    logger.info("\n" + "="*70)
    logger.info("DEDUPLICATION RESULTS")
    logger.info("="*70)
    logger.info(f"Total from Colorado: {stats['total_colorado']:,}")
    logger.info(f"Exact EIN matches: {stats['exact_ein_match']:,}")
    logger.info(f"Fuzzy name matches: {stats['fuzzy_name_match']:,}")
    logger.info(f"New to Daanaa: {stats['new_to_daanaa']:,}")
    logger.info(f"Website coverage in new orgs: {stats['website_coverage']:.1%}")

    if new_orgs:
        # Export to CSV
        output_path = OUTPUT_DIR / args.output
        discovery.export_to_csv(new_orgs, output_path)

        # Ingest to database
        if not args.dry_run:
            logger.info("\nIngesting new orgs to database...")
            discovery.ingest_to_database(new_orgs, dry_run=args.dry_run)
        else:
            logger.info("\n[DRY RUN MODE] Simulating database ingest...")
            discovery.ingest_to_database(new_orgs, dry_run=True)

    logger.info("\n" + "="*70)
    logger.info(f"Colorado discovery complete. Export: {OUTPUT_DIR / args.output}")
    logger.info("="*70)

if __name__ == '__main__':
    main()
