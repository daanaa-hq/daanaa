#!/usr/bin/env python3
"""
Cleanup stale nonprofit accounts
Moves inactive accounts (no login > 90 days AND no approved letters) to archive table
Runs weekly on Sunday at 2am
"""
import sqlite3
import os
import sys
import logging
from datetime import datetime, timedelta

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'merit_registry.db')
INACTIVITY_DAYS = 90
LOG_FILE = os.path.expanduser("~/meritgiving/logs/cleanup_stale_accounts.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_archive_table(conn):
    """Create nonprofit_accounts_archive table if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nonprofit_accounts_archive (
            id TEXT PRIMARY KEY,
            ein TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            opted_in_letters BOOLEAN DEFAULT 0,
            verified BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            archived_at TEXT DEFAULT CURRENT_TIMESTAMP,
            archive_reason TEXT
        )
    """)
    conn.commit()

def find_stale_accounts(conn):
    """Find accounts with no login > 90 days and no approved letters"""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=INACTIVITY_DAYS)).isoformat()

    # Find accounts with no activity in the last 90 days
    # (updated_at is used as proxy for last_login if last_login doesn't exist)
    cursor.execute("""
        SELECT
            na.id,
            na.ein,
            na.email,
            na.name,
            na.verified,
            na.created_at,
            na.updated_at,
            COUNT(oc.id) as letter_count,
            SUM(CASE WHEN oc.claim_status = 'verified' THEN 1 ELSE 0 END) as approved_letters
        FROM nonprofit_accounts na
        LEFT JOIN org_claims oc ON na.ein = oc.ein
        WHERE na.updated_at < ?
        GROUP BY na.id
        HAVING approved_letters IS NULL OR approved_letters = 0
    """, (cutoff_date,))

    return cursor.fetchall()

def archive_accounts(conn, accounts):
    """Move accounts to archive table"""
    cursor = conn.cursor()
    archived_count = 0

    for account in accounts:
        account_id, ein, email, name, verified, created_at, updated_at, letter_count, approved_letters = account

        try:
            # Insert into archive
            cursor.execute("""
                INSERT INTO nonprofit_accounts_archive
                (id, ein, email, name, verified, created_at, updated_at, archived_at, archive_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account_id,
                ein,
                email,
                name,
                verified,
                created_at,
                updated_at,
                datetime.now().isoformat(),
                f"Inactive for {INACTIVITY_DAYS}+ days, no approved letters"
            ))

            # Delete from active table
            cursor.execute("DELETE FROM nonprofit_accounts WHERE id = ?", (account_id,))
            archived_count += 1
            logger.info("Archived account: %s (%s, last_active: %s)", ein, email, updated_at)

        except sqlite3.IntegrityError as e:
            logger.warning("Skipped account %s: %s (duplicate in archive)", ein, e)
        except Exception as e:
            logger.error("Failed to archive account %s: %s", ein, e)

    conn.commit()
    return archived_count

def main():
    if not os.path.exists(DB_PATH):
        logger.error("Database not found: %s", DB_PATH)
        return 1

    conn = sqlite3.connect(DB_PATH)

    logger.info("=" * 70)
    logger.info("Cleanup stale nonprofit accounts started")
    logger.info("=" * 70)

    try:
        ensure_archive_table(conn)

        # Find stale accounts
        stale_accounts = find_stale_accounts(conn)
        logger.info("Found %d stale accounts (inactive > %d days)", len(stale_accounts), INACTIVITY_DAYS)

        if stale_accounts:
            # Archive them
            archived = archive_accounts(conn, stale_accounts)
            logger.info("Archived %d accounts", archived)
        else:
            logger.info("No stale accounts to archive")

        logger.info("=" * 70)
        return 0

    except Exception as e:
        logger.error("Cleanup failed: %s", e, exc_info=True)
        return 1
    finally:
        conn.close()

if __name__ == '__main__':
    sys.exit(main())
