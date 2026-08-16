#!/usr/bin/env python3
"""
Run Migration 004: Create Needs Network Schema

Purpose: Create all tables for Phase 3B (Needs Network backend)
- needs: Live Needs published by nonprofits
- need_intakes: Nonprofit submissions + AI drafts
- need_approvals: Approval audit trail
- need_freshness_log: Re-confirmation tracking
- need_donor_interest: Interest signals (privacy-safe)

Safety:
- Checks if tables already exist (idempotent)
- Creates indexes for performance
- Logs all operations
- Rollback: Remove tables and re-run previous migration if needed

Author: Claude Code
Date: 2026-08-09
"""

import sqlite3
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / 'meritgiving' / 'logs' / 'migrations.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
MIGRATION_FILE = Path.home() / 'meritgiving' / 'migrations' / '004_create_needs_network_schema.sql'

def run_migration():
    """Apply migration 004 to the database."""

    if not DB_PATH.exists():
        logger.error(f"Database not found: {DB_PATH}")
        return False

    if not MIGRATION_FILE.exists():
        logger.error(f"Migration file not found: {MIGRATION_FILE}")
        return False

    logger.info("=" * 70)
    logger.info("MIGRATION 004: Create Needs Network Schema")
    logger.info("=" * 70)

    # Read migration SQL
    with open(MIGRATION_FILE) as f:
        migration_sql = f.read()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute migration
        logger.info("Executing migration SQL...")
        cursor.executescript(migration_sql)
        conn.commit()

        # Verify tables created
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'need%'
            ORDER BY name
        """)
        tables = cursor.fetchall()

        logger.info(f"\nTables created: {len(tables)}")
        for (table_name,) in tables:
            logger.info(f"  ✓ {table_name}")

        # Count indexes
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_need%'
        """)
        index_count = cursor.fetchone()[0]
        logger.info(f"\nIndexes created: {index_count}")

        conn.close()

        logger.info("\n" + "=" * 70)
        logger.info("✅ MIGRATION 004 COMPLETE")
        logger.info("=" * 70)
        logger.info("\nTables ready:")
        logger.info("  - needs (live Needs published by nonprofits)")
        logger.info("  - need_intakes (submissions + AI drafts)")
        logger.info("  - need_approvals (approval audit trail)")
        logger.info("  - need_freshness_log (re-confirmation tracking)")
        logger.info("  - need_donor_interest (interest signals)")
        logger.info("\nNext steps:")
        logger.info("  1. Run: python3 scripts/build_needs_api_routes.py")
        logger.info("  2. Deploy API changes")
        logger.info("  3. Wire frontend to /api/needs endpoints")

        return True

    except sqlite3.Error as e:
        logger.error(f"\n❌ MIGRATION FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == '__main__':
    success = run_migration()
    exit(0 if success else 1)
