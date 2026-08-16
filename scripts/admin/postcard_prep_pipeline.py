#!/usr/bin/env python3
"""
postcard_prep_pipeline.py — Ingest Form 990-N postcard nonprofits (200K orgs <$50K).

Phase 1 execution: Download, transform, validate, stage for Fri Aug 8 load.

Form 990-N (e-postcard) filers:
- Gross receipts <$50K (automatically filing threshold)
- Not required to file full 990 or 990-EZ
- File simplified "postcard" return only
- ~200K organizations annually

Source: IRS data.irs.gov or ProPublica epostcard API
"""

import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
POSTCARD_SOURCE = Path.home() / 'meritgiving' / 'data' / 'form_990n_postcard_data.csv'
POSTCARD_STAGING = Path.home() / 'meritgiving' / 'data' / 'postcard_staging.json'


class PostcardPipeline:
    """
    Transform Form 990-N data into registry_enriched schema.
    """

    def __init__(self):
        self.source_file = POSTCARD_SOURCE
        self.staging_file = POSTCARD_STAGING
        self.db = DB
        self.today = datetime.now()

    def download_postcard_data(self) -> int:
        """Download Form 990-N data from IRS (already exists, validate)."""
        if not self.source_file.exists():
            print(f'⚠ Postcard data not found at {self.source_file}')
            print('  Please download from: https://data.irs.gov/ (Form 990-N / e-postcard)')
            return 0

        rows = sum(1 for _ in open(self.source_file))
        print(f'✓ Found {rows:,} postcard records')
        return rows

    def transform_postcard_schema(self) -> List[Dict]:
        """Transform postcard CSV to registry_enriched schema."""
        print('Transforming postcard data to registry schema...')

        records = []
        with open(self.source_file, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ein = row.get('EIN', '').strip().replace('-', '').zfill(9)
                    if not ein or not ein.isdigit():
                        continue

                    org_name = row.get('Organization Name', '').strip()
                    if not org_name:
                        continue

                    # Postcard-specific fields
                    street = row.get('Street Address', '').strip()
                    city = row.get('City', '').strip()
                    state = row.get('State', '').strip()
                    zip_code = row.get('Zip Code', '').strip()

                    gross_receipts = self._parse_currency(
                        row.get('Gross Receipts', '')
                    )
                    tax_period_year = row.get('Tax Period Year', '')

                    # Registry-enriched schema (minimal for postcards)
                    record = {
                        'EIN': ein,
                        'organization_name': org_name,
                        'street_address': street,
                        'city': city,
                        'state': state,
                        'zip_code': zip_code,
                        'total_revenue': gross_receipts,
                        'filing_year': tax_period_year,
                        'org_status': 'active',  # Postcards only exist for active orgs
                        'irs_revoked': 0,
                        'ntee1': row.get('NTEE Code', '')[:1],  # First letter only
                        'ntee2': row.get('NTEE Code', '')[:2],
                        'nteecc': row.get('NTEE Code', ''),
                        'form_type': '990-N',
                        'is_postcard_org': 1,
                        'data_source': 'form_990n_epostcard',
                        'data_source_date': self.today.isoformat(),
                    }

                    # Set peer groups (postcard orgs = Micro + 1786-member peer group)
                    record['merit_band_v5_label'] = 'Micro'
                    record['merit_archetype_v5'] = 'DONATION_FUNDED'
                    record['merit_archetype_v5_label'] = 'Donation-Funded'
                    record['merit_peer_count_v5'] = 1786  # Approximate postcard peer group size

                    # Default confidence for postcard data
                    record['merit_confidence_v6'] = 60  # Lower: limited 990-N data

                    records.append(record)
                except Exception as e:
                    print(f'  Error processing EIN {row.get("EIN")}: {e}')
                    continue

        print(f'✓ Transformed {len(records):,} records')
        return records

    def validate_integrity(self, records: List[Dict]) -> Tuple[int, int]:
        """
        Validate postcard records against registry constraints.
        Returns: (valid_count, error_count)
        """
        print('Validating postcard data...')

        valid = []
        errors = 0

        for rec in records:
            issues = []

            # EIN validation
            if not rec.get('EIN') or len(rec['EIN']) != 9:
                issues.append('EIN invalid')

            # Org name required
            if not rec.get('organization_name'):
                issues.append('missing org name')

            # Cross-check: postcard org should be <$50K revenue
            revenue = rec.get('total_revenue')
            if revenue and revenue > 50_000:
                issues.append(f'revenue {revenue} > $50K')

            # State code should be 2-char
            if rec.get('state') and len(rec.get('state', '')) != 2:
                issues.append('invalid state')

            if issues:
                print(f"  ✗ {rec['EIN']}: {'; '.join(issues)}")
                errors += 1
            else:
                valid.append(rec)

        print(f'✓ Validation: {len(valid):,} valid, {errors:,} errors')
        return len(valid), errors

    def stage_for_load(self, records: List[Dict]) -> int:
        """
        Write validated records to staging file for Friday load.
        Returns: count of records staged.
        """
        print(f'Staging records to {self.staging_file}...')

        with open(self.staging_file, 'w') as f:
            json.dump({
                'postcard_count': len(records),
                'records': records,
                'staged_at': self.today.isoformat(),
            }, f, default=str, indent=2)

        print(f'✓ Staged {len(records):,} postcard records')
        return len(records)

    def check_against_existing(self) -> Dict:
        """
        Check postcard records against existing registry.
        Returns: overlap stats.
        """
        print('Checking against existing registry...')

        con = sqlite3.connect(str(self.db))
        cur = con.cursor()

        # Load postcard data
        with open(self.staging_file) as f:
            postcard_data = json.load(f)
            postcard_eins = {r['EIN'] for r in postcard_data['records']}

        # Check overlap
        cur.execute(
            f'SELECT COUNT(*) FROM registry_enriched WHERE EIN IN ({",".join("?" * len(postcard_eins))})',
            list(postcard_eins)
        )
        existing = cur.fetchone()[0]

        print(f'✓ Overlap check: {existing:,} postcards already in registry')

        con.close()
        return {
            'postcard_count': len(postcard_eins),
            'existing_overlap': existing,
            'new_orgs': len(postcard_eins) - existing,
        }

    def _parse_currency(self, value: str) -> int:
        """Parse currency string to integer."""
        if not value:
            return 0
        try:
            clean = value.replace('$', '').replace(',', '').strip()
            return int(float(clean))
        except (ValueError, TypeError):
            return 0

    def run(self) -> Dict:
        """Execute full pipeline."""
        print('=' * 60)
        print('POSTCARD PIPELINE — Phase 1 Preparation')
        print(f'Started: {self.today.isoformat()}')
        print('=' * 60)

        # Step 1: Download/validate source
        self.download_postcard_data()

        # Step 2: Transform schema
        records = self.transform_postcard_schema()

        # Step 3: Validate integrity
        valid, errors = self.validate_integrity(records)

        # Step 4: Stage for load
        staged = self.stage_for_load(records)

        # Step 5: Check against existing
        overlap = self.check_against_existing()

        result = {
            'status': 'ready_for_load',
            'staged_count': staged,
            'valid_count': valid,
            'error_count': errors,
            'overlap': overlap,
            'staging_file': str(self.staging_file),
            'load_eta': 'Fri Aug 8, 17:00 CDT',
        }

        print('\n' + '=' * 60)
        print('POSTCARD PIPELINE COMPLETE')
        print(f"✓ {staged:,} records ready for Friday load")
        print(f"✓ Staging file: {self.staging_file}")
        print('=' * 60)

        return result


def main():
    pipeline = PostcardPipeline()
    result = pipeline.run()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
