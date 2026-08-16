#!/usr/bin/env python3
"""
Integrate discovered websites into registry_enriched.
Adds website_discovered_date column and inserts high-confidence sites.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG_DIR = Path.home() / "meritgiving/logs"
VERIFICATION_FILE = LOG_DIR / "website_verification_results.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] INTEGRATE: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "website_integration.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

def integrate():
    """Integrate discovered websites into registry_enriched."""
    logger.info("=" * 80)
    logger.info("WEBSITE DISCOVERY INTEGRATION")
    logger.info("=" * 80)

    db = sqlite3.connect(DB)
    cursor = db.cursor()

    # Step 1: Add column if it doesn't exist
    logger.info("Checking for website_discovered_date column...")
    cursor.execute("PRAGMA table_info(registry_enriched)")
    columns = [row[1] for row in cursor.fetchall()]

    if "website_discovered_date" not in columns:
        logger.info("Adding website_discovered_date column...")
        cursor.execute("""
            ALTER TABLE registry_enriched
            ADD COLUMN website_discovered_date TEXT
        """)
        db.commit()
        logger.info("✓ Column added")
    else:
        logger.info("✓ Column already exists")

    # Step 2: Load verified websites and insert
    logger.info("Loading verified websites...")
    high_confidence_count = 0
    inserted_count = 0
    errors_count = 0

    try:
        with open(VERIFICATION_FILE, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)

                    # Only insert high-confidence (verified) websites
                    if record['status'] == 'VERIFIED':
                        high_confidence_count += 1

                        ein = record['ein']
                        website = record['website']
                        discovery_date = record['timestamp'][:10]  # YYYY-MM-DD

                        # Update or insert
                        cursor.execute("""
                            UPDATE registry_enriched
                            SET website = ?, website_discovered_date = ?
                            WHERE ein = ? AND (website IS NULL OR website = '')
                        """, (website, discovery_date, ein))

                        if cursor.rowcount > 0:
                            inserted_count += 1

                        if inserted_count % 10000 == 0:
                            logger.info(f"Progress: {inserted_count:,} websites integrated")
                            db.commit()

                except Exception as e:
                    errors_count += 1
                    if errors_count <= 5:
                        logger.warning(f"Parse error: {e}")

    except FileNotFoundError:
        logger.error("Verification results file not found. Run verification first.")
        return

    db.commit()
    db.close()

    logger.info("=" * 80)
    logger.info("INTEGRATION COMPLETE")
    logger.info(f"High-confidence websites found: {high_confidence_count:,}")
    logger.info(f"Websites integrated into registry: {inserted_count:,}")
    logger.info(f"Parse errors: {errors_count}")
    logger.info("=" * 80)

if __name__ == "__main__":
    integrate()
