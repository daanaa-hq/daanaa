#!/usr/bin/env python3
"""
Backfill IRS EO Master File data: org_status, irs_revoked, ruling_date
Maps IRS status codes to human-readable org_status.
"""

import sqlite3
import csv
from pathlib import Path
from datetime import datetime
import logging

DB_PATH = Path('/home/akbar/meritgiving/data/merit_registry.db')
EO_DIR = Path('/home/akbar/meritgiving/data')
LOG_DIR = Path('/home/akbar/meritgiving/logs')

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'backfill_irs_eo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# IRS status code mapping (from IRS EO Master File documentation)
STATUS_MAP = {
    '01': 'active',       # Active
    '02': 'inactive',     # Inactive - IRS Letter
    '03': 'inactive',     # Inactive - Org Letter
    '04': 'revoked',      # Revoked
    '05': 'pending',      # Pending
    '11': 'inactive',     # Inactive - Unrelated Bus Income
    '12': 'inactive',     # Inactive - Tax Liability
    '21': 'merged',       # Merged
    '22': 'inactive',     # Inactive - Dissolution
    '23': 'closed',       # Closed
    '24': 'pending',      # Pending
    '25': 'revoked',      # Revoked
    '26': 'closed',       # Closed or Dissolved
    '27': 'closed',       # Closed or Dissolved
    '28': 'revoked',      # Revoked
    '99': 'unknown',      # Unknown
}

def load_eo_data():
    """Load and merge all EO files."""
    logger.info("Loading IRS EO Master Files...")
    eo_data = {}

    for eo_file in sorted(EO_DIR.glob('eo*.csv')):
        logger.info(f"  Reading {eo_file.name}...")
        with open(eo_file, encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ein = row.get('EIN', '').strip()
                if ein and len(ein) >= 1:
                    # Keep first occurrence (dedupe by EIN)
                    if ein not in eo_data:
                        eo_data[ein] = row

    logger.info(f"Loaded {len(eo_data):,} unique orgs from EO files")
    return eo_data

def backfill_db(eo_data):
    """Backfill org_status, irs_revoked, ruling_date into registry_enriched."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    updated = 0
    revoked = 0

    for ein, row in eo_data.items():
        status_code = row.get('STATUS', '').strip()
        org_status = STATUS_MAP.get(status_code, 'unknown')
        irs_revoked = 1 if org_status == 'revoked' else 0
        ruling_date = row.get('RULING', '').strip() or None

        try:
            c.execute("""
                UPDATE registry_enriched
                SET org_status = ?, irs_revoked = ?, ruling_date = ?
                WHERE ein = ?
            """, (org_status, irs_revoked, ruling_date, ein))

            if irs_revoked:
                revoked += 1

            updated += 1
            if updated % 100_000 == 0:
                logger.info(f"  Updated {updated:,} records...")
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating {ein}: {e}")

    conn.commit()
    conn.close()

    logger.info(f"\n{'='*60}")
    logger.info(f"Backfill Complete:")
    logger.info(f"  Updated: {updated:,} records")
    logger.info(f"  Revoked: {revoked:,}")
    logger.info(f"  Status breakdown: {STATUS_MAP}")
    logger.info(f"{'='*60}\n")

if __name__ == '__main__':
    eo_data = load_eo_data()
    backfill_db(eo_data)
