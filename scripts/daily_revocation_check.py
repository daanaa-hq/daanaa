#!/usr/bin/env python3
"""
Daily revocation monitoring — check IRS for new org status changes.
Runs nightly via cron; updates irs_revoked flag + org_status.
Alerts on newly revoked orgs (currently visible on site).
"""

import sqlite3
import csv
from pathlib import Path
import logging
from datetime import datetime

DB_PATH = Path('/home/akbar/meritgiving/data/merit_registry.db')
EO_DIR = Path('/home/akbar/meritgiving/data')
LOG_DIR = Path('/home/akbar/meritgiving/logs')

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'daily_revocation_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Map IRS status codes to our org_status
STATUS_MAP = {
    '01': 'active',
    '02': 'inactive',
    '04': 'revoked',
    '25': 'revoked',
    '28': 'revoked',
}

def load_eo_data():
    """Load latest EO Master File data."""
    logger.info("Loading latest IRS EO Master File...")
    eo_data = {}

    for eo_file in sorted(EO_DIR.glob('eo*.csv')):
        with open(eo_file, encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ein = row.get('EIN', '').strip()
                if ein and ein not in eo_data:
                    eo_data[ein] = row

    logger.info(f"Loaded {len(eo_data):,} orgs from EO files")
    return eo_data

def check_for_changes(eo_data):
    """Compare current EO data with DB; flag newly revoked orgs."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    newly_revoked = []
    status_changed = 0

    for ein, eo_row in eo_data.items():
        status_code = eo_row.get('STATUS', '').strip()
        new_status = STATUS_MAP.get(status_code, 'unknown')

        # Check if this org is in our DB
        c.execute("SELECT ein, irs_revoked, org_status FROM registry_enriched WHERE ein = ?", (ein,))
        db_row = c.fetchone()

        if db_row:
            _, db_revoked, db_status = db_row
            is_newly_revoked = (new_status == 'revoked' and db_revoked == 0)

            if is_newly_revoked:
                newly_revoked.append((ein, eo_row.get('NAME', '')))
                logger.warning(f"NEWLY REVOKED: {ein} ({eo_row.get('NAME', '')})")

            # Update if status changed
            if db_status != new_status:
                c.execute("""
                    UPDATE registry_enriched
                    SET org_status = ?, irs_revoked = ?
                    WHERE ein = ?
                """, (new_status, 1 if new_status == 'revoked' else 0, ein))
                status_changed += 1

    conn.commit()
    conn.close()

    return newly_revoked, status_changed

def alert_on_revocations(newly_revoked):
    """Log alerts for newly revoked orgs."""
    if not newly_revoked:
        logger.info("No newly revoked orgs detected.")
        return

    logger.warning(f"\n{'='*60}")
    logger.warning(f"ALERT: {len(newly_revoked)} newly revoked orgs detected!")
    logger.warning(f"{'='*60}")

    for ein, name in newly_revoked[:20]:  # Show first 20
        logger.warning(f"  {ein}: {name}")

    if len(newly_revoked) > 20:
        logger.warning(f"  ... and {len(newly_revoked) - 20} more")

    logger.warning(f"{'='*60}\n")

def main():
    logger.info("Daily Revocation Check — Starting")

    eo_data = load_eo_data()
    newly_revoked, status_changed = check_for_changes(eo_data)

    logger.info(f"\nDaily Check Summary:")
    logger.info(f"  Status updates: {status_changed}")
    logger.info(f"  Newly revoked: {len(newly_revoked)}")

    if newly_revoked:
        alert_on_revocations(newly_revoked)

if __name__ == '__main__':
    main()
