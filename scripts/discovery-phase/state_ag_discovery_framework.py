#!/usr/bin/env python3
"""
State AG 990 Discovery Framework
Generic deduplication, validation, and ingestion framework for multiple state sources.

Usage:
    python3 scripts/state_ag_discovery_framework.py --source propublica --validate
    python3 scripts/state_ag_discovery_framework.py --source colorado --ingest --dry-run
"""

import sqlite3
import logging
import csv
import requests
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
import argparse
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path("/home/akbar/meritgiving/data/merit_registry.db")
DISCOVERY_DIR = Path("/home/akbar/meritgiving/data/state_ag_discovery")
DISCOVERY_DIR.mkdir(exist_ok=True)

@dataclass
class DiscoveryRecord:
    """Unified discovery record format"""
    ein: Optional[str]
    organization_name: str
    website: Optional[str]
    city: str
    state: str
    zip_code: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    source_state: str
    source_database: str
    confidence: str  # HIGH, MEDIUM, LOW
    match_strategy: Optional[str]  # 'exact_ein', 'fuzzy_name', 'new'
    validation_status: Optional[str] = None  # 'valid', 'dead_link', 'unknown'
    notes: Optional[str] = None

class StateDiscoveryFramework:
    """Generic framework for state AG database discovery"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.daanaa_eins = set()
        self.daanaa_orgs_by_name = {}
        self._load_daanaa_registry()

    def _load_daanaa_registry(self):
        """Load existing Daanaa registry for deduplication"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            cursor.execute("SELECT EIN FROM registry_enriched WHERE EIN IS NOT NULL AND EIN != ''")
            self.daanaa_eins = set(row[0] for row in cursor.fetchall())

            cursor.execute("""
                SELECT organization_name, EIN FROM registry_enriched
                WHERE organization_name IS NOT NULL AND organization_name != ''
            """)
            self.daanaa_orgs_by_name = {row[0].upper(): row[1] for row in cursor.fetchall()}

            logger.info(f"Registry loaded: {len(self.daanaa_eins):,} EINs, {len(self.daanaa_orgs_by_name):,} names")

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise

    def deduplicate(self, records: List[DiscoveryRecord]) -> Tuple[List[DiscoveryRecord], Dict]:
        """
        Deduplicate discovery records against existing Daanaa registry.
        Returns new records and statistics.
        """
        new_records = []
        stats = defaultdict(int)
        enrich_records = []  # Existing orgs that could be enriched with website

        for record in records:
            stats['total_input'] += 1

            # Strategy 1: Exact EIN match
            if record.ein and record.ein in self.daanaa_eins:
                stats['exact_ein_match'] += 1
                record.match_strategy = 'exact_ein'
                record.confidence = 'HIGH'
                if record.website:
                    enrich_records.append(record)
                continue

            # Strategy 2: Fuzzy name match
            matched_ein = self._fuzzy_match_name(record.organization_name)
            if matched_ein:
                stats['fuzzy_name_match'] += 1
                record.ein = matched_ein
                record.match_strategy = 'fuzzy_name'
                record.confidence = 'MEDIUM'
                if record.website:
                    enrich_records.append(record)
                continue

            # Strategy 3: New organization
            stats['new_orgs'] += 1
            record.match_strategy = 'new'
            record.confidence = 'MEDIUM' if record.website else 'LOW'
            new_records.append(record)

        stats['website_coverage_new'] = (
            len([r for r in new_records if r.website]) / len(new_records)
            if new_records else 0
        )

        logger.info(f"Deduplication complete: {stats['new_orgs']:,} new, "
                   f"{stats['exact_ein_match']:,} EIN matches, "
                   f"{stats['fuzzy_name_match']:,} name matches")

        return new_records, dict(stats), enrich_records

    def _fuzzy_match_name(self, name: str, threshold: float = 0.85) -> Optional[str]:
        """Fuzzy match organization name against registry"""
        name_upper = name.upper()

        if name_upper in self.daanaa_orgs_by_name:
            return self.daanaa_orgs_by_name[name_upper]

        best_match = None
        best_ratio = 0

        for daanaa_name, ein in self.daanaa_orgs_by_name.items():
            ratio = SequenceMatcher(None, name_upper, daanaa_name).ratio()
            if ratio >= threshold and ratio > best_ratio:
                best_ratio = ratio
                best_match = ein

        return best_match

    def validate_websites(self, records: List[DiscoveryRecord], timeout: int = 3) -> List[DiscoveryRecord]:
        """
        Validate website URLs via HTTP HEAD request.
        Updates validation_status field.
        """
        validated = 0
        dead = 0
        errors = 0

        for record in records:
            if not record.website:
                record.validation_status = 'unknown'
                continue

            try:
                response = requests.head(record.website, timeout=timeout, allow_redirects=True)
                if response.status_code == 200:
                    record.validation_status = 'valid'
                    validated += 1
                else:
                    record.validation_status = 'dead_link'
                    dead += 1
                    record.notes = f"HTTP {response.status_code}"
            except requests.RequestException as e:
                record.validation_status = 'unknown'
                errors += 1
                record.notes = str(e)

        logger.info(f"Website validation: {validated} valid, {dead} dead, {errors} unknown")
        return records

    def export_to_csv(self, records: List[DiscoveryRecord], output_path: Path):
        """Export discovery records to CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'ein', 'organization_name', 'website', 'city', 'state', 'zip_code',
                'phone', 'email', 'source_state', 'source_database', 'confidence',
                'match_strategy', 'validation_status', 'notes'
            ])
            writer.writeheader()

            for record in records:
                writer.writerow({
                    'ein': record.ein or '',
                    'organization_name': record.organization_name,
                    'website': record.website or '',
                    'city': record.city,
                    'state': record.state,
                    'zip_code': record.zip_code or '',
                    'phone': record.phone or '',
                    'email': record.email or '',
                    'source_state': record.source_state,
                    'source_database': record.source_database,
                    'confidence': record.confidence,
                    'match_strategy': record.match_strategy or '',
                    'validation_status': record.validation_status or '',
                    'notes': record.notes or ''
                })

        logger.info(f"Exported {len(records)} records to {output_path}")

    def ingest_to_database(self, records: List[DiscoveryRecord], dry_run: bool = True):
        """Insert discovery records into Daanaa registry"""
        if not records:
            logger.warning("No records to ingest")
            return

        try:
            cursor = self.conn.cursor()
            inserted = 0
            updated = 0
            skipped = 0
            errors = 0

            for record in records:
                try:
                    # Skip low-confidence orgs without website
                    if record.confidence == 'LOW' and not record.website:
                        skipped += 1
                        continue

                    # Skip dead links
                    if record.validation_status == 'dead_link':
                        skipped += 1
                        continue

                    if dry_run:
                        logger.info(f"[DRY] {record.ein or 'NEW'}: {record.organization_name[:50]}")
                    else:
                        cursor.execute("""
                            INSERT INTO registry_enriched (
                                EIN, organization_name, website, CITY, STATE, zipcode,
                                source, data_source, website_source, website_checked_at,
                                updated_at, org_status, contact_available
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'),
                                     datetime('now'), 'active', ?)
                        """, (
                            record.ein or '',
                            record.organization_name,
                            record.website,
                            record.city,
                            record.state,
                            record.zip_code,
                            record.source_database,
                            record.source_database,
                            record.source_state,
                            1 if record.phone or record.email else 0
                        ))
                        inserted += 1

                except sqlite3.IntegrityError:
                    # EIN already exists - could update website if missing
                    updated += 1
                except sqlite3.Error as e:
                    errors += 1
                    logger.error(f"Error: {e}")

            if not dry_run:
                self.conn.commit()

            logger.info(f"Ingest result: {inserted} inserted, {updated} skipped, {errors} errors")

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if not dry_run:
                self.conn.rollback()

class DiscoveryOrchestrator:
    """Orchestrates multi-state discovery"""

    def __init__(self):
        self.framework = StateDiscoveryFramework(DB_PATH)
        self.results = {}

    def run_full_pipeline(self, sources: List[str], validate: bool = False, ingest: bool = False, dry_run: bool = True):
        """Run discovery pipeline for specified sources"""
        logger.info("="*70)
        logger.info("STATE AG 990 DISCOVERY - FULL PIPELINE")
        logger.info("="*70)

        for source in sources:
            logger.info(f"\nProcessing {source}...")
            # Load, deduplicate, validate, export
            # (implementation depends on source-specific loaders)

    def generate_report(self) -> Dict:
        """Generate summary report of all discoveries"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'sources': self.results,
            'total_new_orgs': sum(r.get('new_orgs', 0) for r in self.results.values()),
            'total_websites': sum(r.get('with_websites', 0) for r in self.results.values())
        }
        return report

def main():
    parser = argparse.ArgumentParser(description="State AG 990 Discovery Framework")
    parser.add_argument('--source', choices=['propublica', 'colorado', 'ny', 'il', 'all'],
                        help='Data source to process')
    parser.add_argument('--validate', action='store_true',
                        help='Validate websites via HTTP')
    parser.add_argument('--ingest', action='store_true',
                        help='Ingest to database')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run mode')

    args = parser.parse_args()

    logger.info("State AG Discovery Framework initialized")

    if args.source == 'all':
        orchestrator = DiscoveryOrchestrator()
        orchestrator.run_full_pipeline(
            ['propublica', 'colorado', 'ny', 'il'],
            validate=args.validate,
            ingest=args.ingest,
            dry_run=args.dry_run
        )
    else:
        logger.info(f"Single source mode: {args.source}")

if __name__ == '__main__':
    main()
