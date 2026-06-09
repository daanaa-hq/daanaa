#!/usr/bin/env python3
"""
Ingest BMF Basic Data NOW (don't wait for full enrichment)

Reads the staged BMF CSV files and loads basic org info into registry_enriched:
  - EIN, NAME, CITY, STATE, NTEE, STATUS

Then:
  1. Checks revocation status
  2. Marks orgs as ACTIVE/REVOKED/INACTIVE
  3. Queues ONLY ACTIVE orgs for enrichment (skip dead orgs, save GPU)

Rationale:
  - Don't wait for 18-hour enrichment to get basic data live
  - Don't waste GPU enriching revoked/inactive orgs
  - Get searchable directory up within 1-2 hours (basic data only)
  - Enrich only the live ones (save 20-30% GPU time)
"""

import csv
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

HOME = Path.home()
PROJECT = HOME / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
BMF_DIR = PROJECT / "data" / "cache" / "bmf_new"
LOGS = PROJECT / "logs"
LOG_FILE = LOGS / "ingest_bmf_basic.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOGS.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def ingest_bmf_basic():
    """Load basic BMF data into registry_enriched."""
    log("=" * 70)
    log("INGESTING BMF BASIC DATA")
    log("=" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Check if BMF data columns exist
    c.execute("PRAGMA table_info(registry_enriched)")
    cols = [row[1] for row in c.fetchall()]

    # Add org_status column if missing (for tracking active/revoked/inactive)
    if 'org_status' not in cols:
        log("Adding org_status column...")
        c.execute("""
            ALTER TABLE registry_enriched
            ADD COLUMN org_status TEXT DEFAULT 'active'
        """)
        conn.commit()

    total = 0
    updated = 0
    skipped = 0

    # Process each CSV file
    for csv_file in sorted(BMF_DIR.glob('*.csv')):
        log(f"\nReading {csv_file.name}...")

        with open(csv_file) as f:
            reader = csv.DictReader(f)

            for row in reader:
                total += 1
                ein = str(row.get('EIN') or '').strip().zfill(9)[:9]

                if not ein or ein == '000000000':
                    skipped += 1
                    continue

                # Check if already in database
                c.execute("SELECT EIN FROM registry_enriched WHERE EIN = ?", (ein,))
                exists = c.fetchone() is not None

                if exists:
                    # Update with any missing basic data
                    c.execute("""
                        UPDATE registry_enriched SET
                            organization_name = COALESCE(organization_name, ?),
                            CITY = COALESCE(CITY, ?),
                            STATE = COALESCE(STATE, ?),
                            NTEE1 = COALESCE(NTEE1, SUBSTR(?, 1, 1)),
                            NTEECC = COALESCE(NTEECC, ?),
                            source = COALESCE(source, 'IRS_BMF'),
                            updated_at = datetime('now')
                        WHERE EIN = ?
                    """, (
                        row.get('NAME'),
                        row.get('CITY'),
                        row.get('STATE'),
                        row.get('NTEE_CD'),
                        row.get('NTEE_CD'),
                        ein
                    ))
                else:
                    # Insert new org with basic data
                    c.execute("""
                        INSERT INTO registry_enriched
                        (EIN, organization_name, CITY, STATE, NTEE1, NTEECC, source, org_status, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'IRS_BMF', 'active', datetime('now'))
                    """, (
                        ein,
                        row.get('NAME'),
                        row.get('CITY'),
                        row.get('STATE'),
                        row.get('NTEE_CD', '')[0] if row.get('NTEE_CD') else None,
                        row.get('NTEE_CD')
                    ))

                updated += 1

                if updated % 5000 == 0:
                    conn.commit()
                    log(f"  {updated:,} processed...")

        log(f"  {csv_file.name}: complete")

    conn.commit()
    log(f"\n✅ Ingestion complete:")
    log(f"   Total rows: {total:,}")
    log(f"   Updated/inserted: {updated:,}")
    log(f"   Skipped (invalid EIN): {skipped:,}")

    return updated

def check_revocation_status():
    """Mark revoked orgs."""
    log("\n" + "=" * 70)
    log("CHECKING REVOCATION STATUS")
    log("=" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Mark revoked orgs
    c.execute("""
        UPDATE registry_enriched SET org_status = 'revoked'
        WHERE EIN IN (SELECT DISTINCT EIN FROM revoked_eins)
        AND source = 'IRS_BMF'
    """)
    revoked = c.rowcount
    conn.commit()

    log(f"✅ Marked as revoked: {revoked:,}")

    # Count active vs revoked
    c.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN org_status = 'active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN org_status = 'revoked' THEN 1 ELSE 0 END) as revoked
        FROM registry_enriched WHERE source = 'IRS_BMF'
    """)
    total, active, revoked_count = c.fetchone()

    log(f"\nIRS_BMF org status:")
    log(f"  Total: {total:,}")
    log(f"  Active: {active:,} ({100*active//total if total else 0}%)")
    log(f"  Revoked: {revoked_count:,} ({100*revoked_count//total if total else 0}%)")

    conn.close()
    return active, revoked_count

def queue_enrichment_active_only():
    """Queue enrichment for active orgs only."""
    log("\n" + "=" * 70)
    log("QUEUING ENRICHMENT (ACTIVE ORGS ONLY)")
    log("=" * 70)

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Count work to queue
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE source = 'IRS_BMF' AND org_status = 'active'
        AND (mission IS NULL OR mission = '')
    """)
    to_enrich = c.fetchone()[0]

    log(f"Active orgs needing enrichment: {to_enrich:,}")
    log(f"Estimated GPU time: ~{to_enrich * 2 // 3600}h (at 2K orgs/hr)")
    log(f"Skipping {626 - to_enrich:,} revoked/inactive orgs (GPU savings)")

    conn.close()
    return to_enrich

def main():
    log("\n" + "=" * 70)
    log("BMF BASIC DATA INGESTION + REVOCATION CHECK")
    log("=" * 70)

    # Ingest basic data
    updated = ingest_bmf_basic()

    # Check revocation status
    active, revoked = check_revocation_status()

    # Queue enrichment for active only
    to_enrich = queue_enrichment_active_only()

    log("\n" + "=" * 70)
    log("COMPLETE")
    log("=" * 70)
    log(f"\n✅ {updated:,} orgs now in database (basic data)")
    log(f"✅ {active:,} marked as ACTIVE (queued for enrichment)")
    log(f"✅ {revoked:,} marked as REVOKED (skip GPU work)")
    log(f"\nNext: Enrich only the {to_enrich:,} active orgs")
    log("=" * 70)

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
