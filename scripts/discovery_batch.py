#!/usr/bin/env python3
"""Event Discovery Batch Processor

Runs nightly to:
1. Discover events from nonprofit websites
2. Queue candidates for admin review (no auto-publish)
3. Respect robots.txt and rate limits
4. Log all discoveries and failures

Candidates stay in pending_review until promoted by admin.
Unconfirmed events never open for signup.
"""

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import event_discovery_engine

# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Use canonical database path (same one the API reads)
# LIVE_DB_PATH is only used if explicitly set; otherwise use the canonical registry DB
DB_PATH = os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/merit_registry.db"))
LIVE_DB_PATH = os.environ.get("LIVE_DB_PATH", DB_PATH)  # Must be same as API

def get_db(path: str) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db

def discover_org_events(db: sqlite3.Connection, ein: str, website: str) -> int:
    """
    Fetch organization's website and discover events.
    Returns number of candidates queued.
    """
    if not website or not website.startswith(('http://', 'https://')):
        logger.warning(f"EIN {ein}: invalid website URL: {website}")
        return 0

    try:
        logger.info(f"EIN {ein}: fetching {website}")
        html = event_discovery_engine.fetch_source(website)
        candidates = event_discovery_engine.extract_candidates(website, html)

        if candidates:
            added = event_discovery_engine.queue_candidates(db, ein, candidates)
            logger.info(f"EIN {ein}: queued {added} candidate(s)")
            return added
        else:
            logger.info(f"EIN {ein}: no candidates found")
            return 0

    except ValueError as e:
        logger.warning(f"EIN {ein}: {e}")
        return 0
    except Exception as e:
        logger.error(f"EIN {ein}: failed to discover: {type(e).__name__}: {e}")
        return 0

def main():
    """Run discovery batch."""
    logger.info("Starting discovery batch processor")

    db = get_db(LIVE_DB_PATH)

    # Ensure schema exists
    event_discovery_engine.ensure_queue(db)

    # Find nonprofits with websites that haven't been checked in 14-60 days
    # (rolling window for discovery)
    start_date, end_date = event_discovery_engine.rolling_window()
    logger.info(f"Discovery window: {start_date} to {end_date}")

    # Query: orgs with claimed events, valid websites, not checked recently
    orgs = db.execute("""
        SELECT DISTINCT re.ein, re.website
        FROM registry_enriched re
        JOIN org_claims oc ON re.ein = oc.ein
        WHERE re.website IS NOT NULL
        AND re.website LIKE 'http%'
        AND oc.claim_status IN ('verified', 'active')
        AND oc.revoked_at IS NULL
        LIMIT 1000  -- batch limit per run
    """).fetchall()

    logger.info(f"Found {len(orgs)} organizations to scan")

    total_queued = 0
    skipped = 0
    failed = 0

    for row in orgs:
        ein = row['ein']
        website = row['website']

        # Check if we've already scanned this website recently (skip if so)
        recent = db.execute("""
            SELECT COUNT(*) as count FROM event_discovery_queue
            WHERE ein=? AND last_checked_at > datetime('now', '-7 days')
        """, (ein,)).fetchone()

        if recent['count'] > 0:
            skipped += 1
            continue

        # Discover events
        added = discover_org_events(db, ein, website)
        total_queued += added

    db.close()

    logger.info(f"""
Discovery batch complete:
  - Scanned: {len(orgs) - skipped}
  - Skipped (recent): {skipped}
  - Candidates queued: {total_queued}
""")

    return 0

if __name__ == '__main__':
    sys.exit(main())
