#!/usr/bin/env python3
"""
Phase 3: IRS Eligibility Database Persistence

Adds 4 columns to registry_enriched:
- irs_eligibility_status (verified | unverified | revoked | unknown | exception_possible)
- irs_eligibility_checked_at (ISO timestamp from manifest)
- irs_eligibility_sources (JSON array of source names)
- irs_eligibility_explanation (human-readable reason for status)

Uses IRS source files as authority; preserves wallet history and scoring.
"""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.irs_eligibility_helper import (
    initialize_helper,
    get_eligibility_fields,
    IrsEligibilityHelper,
)

DB_PATH = Path(__file__).parent.parent / "data" / "merit_registry.db"
MANIFEST_PATH = Path(__file__).parent.parent / "data/irs_authority/v6_eligibility/eligibility_manifest.json"

def add_irs_columns(db_path: str) -> bool:
    """Add IRS columns to registry_enriched if not present."""
    db = sqlite3.connect(db_path)
    cur = db.cursor()

    columns_to_add = [
        ("irs_eligibility_status", "TEXT"),
        ("irs_eligibility_checked_at", "TEXT"),
        ("irs_eligibility_sources", "TEXT"),
        ("irs_eligibility_explanation", "TEXT"),
    ]

    print("\n=== Adding IRS Columns ===")
    added = 0
    for col_name, col_type in columns_to_add:
        try:
            cur.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col_name} {col_type}")
            db.commit()
            print(f"✓ Added column: {col_name}")
            added += 1
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print(f"⊘ Column already exists: {col_name}")
            else:
                print(f"✗ Error adding {col_name}: {e}")
                db.close()
                return False

    db.close()
    return True


def persist_irs_eligibility(db_path: str, manifest_path: str, dry_run: bool = False) -> dict:
    """
    Populate IRS eligibility fields from helper.

    Returns: {
        'total': count of orgs processed,
        'verified': count with verified status,
        'unverified': count with unverified status,
        'revoked': count with revoked status,
        'unknown': count with unknown status,
        'exception_possible': count with exception_possible status,
        'updated': count of rows updated (0 in dry-run),
        'errors': list of EINs that failed
    }
    """

    # Initialize helper with manifest and data files
    try:
        initialize_helper(db_path, manifest_path)
        print("✓ IRS helper initialized")
    except Exception as e:
        print(f"✗ Failed to initialize IRS helper: {e}")
        return {}

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Get all orgs
    cur.execute("SELECT EIN FROM registry_enriched ORDER BY EIN")
    eins = [row['EIN'] for row in cur.fetchall()]

    print(f"\n=== Persisting IRS Eligibility (dry_run={dry_run}) ===")
    print(f"Processing {len(eins):,} organizations...")

    stats = {
        'total': len(eins),
        'verified': 0,
        'unverified': 0,
        'revoked': 0,
        'unknown': 0,
        'exception_possible': 0,
        'updated': 0,
        'errors': [],
    }

    # Process in batches for progress reporting
    batch_size = 50000
    for batch_idx in range(0, len(eins), batch_size):
        batch_eins = eins[batch_idx:batch_idx + batch_size]
        batch_end = min(batch_idx + batch_size, len(eins))

        print(f"  Processing {batch_end:,} / {len(eins):,}...")

        for ein in batch_eins:
            try:
                fields = get_eligibility_fields(ein)
                status = fields.get('irs_eligibility_status', 'unknown')

                # Track status distribution
                stats[status] = stats.get(status, 0) + 1

                # Update database (unless dry-run)
                if not dry_run:
                    # Convert sources list to JSON string
                    sources = fields.get('irs_eligibility_sources', [])
                    if isinstance(sources, list):
                        import json
                        sources_json = json.dumps(sources, separators=(',', ':'))
                    else:
                        sources_json = sources

                    cur.execute(
                        """
                        UPDATE registry_enriched
                        SET
                            irs_eligibility_status = ?,
                            irs_eligibility_checked_at = ?,
                            irs_eligibility_sources = ?,
                            irs_eligibility_explanation = ?
                        WHERE EIN = ?
                        """,
                        (
                            fields.get('irs_eligibility_status'),
                            fields.get('irs_eligibility_checked_at'),
                            sources_json,
                            fields.get('irs_eligibility_explanation'),
                            ein,
                        ),
                    )
                    stats['updated'] += 1

            except Exception as e:
                print(f"    ✗ Error processing {ein}: {e}")
                stats['errors'].append((ein, str(e)))

        if not dry_run:
            db.commit()

    db.close()

    # Report results
    print(f"\n=== Persistence Results ===")
    print(f"Total organizations: {stats['total']:,}")
    print(f"  Verified: {stats['verified']:,}")
    print(f"  Unverified: {stats['unverified']:,}")
    print(f"  Revoked: {stats['revoked']:,}")
    print(f"  Unknown: {stats['unknown']:,}")
    print(f"  Exception-possible: {stats['exception_possible']:,}")
    print(f"Rows updated: {stats['updated']:,}")

    if stats['errors']:
        print(f"✗ Errors processing {len(stats['errors'])} EINs")
        for ein, err in stats['errors'][:10]:  # Show first 10
            print(f"    {ein}: {err}")
        if len(stats['errors']) > 10:
            print(f"    ... and {len(stats['errors']) - 10} more")

    return stats


def verify_persistence(db_path: str) -> bool:
    """Verify that IRS columns have data."""
    db = sqlite3.connect(db_path)
    cur = db.cursor()

    print(f"\n=== Verification ===")

    # Check row counts by status
    cur.execute("""
        SELECT
            irs_eligibility_status,
            COUNT(*) as cnt
        FROM registry_enriched
        WHERE irs_eligibility_status IS NOT NULL
        GROUP BY irs_eligibility_status
        ORDER BY cnt DESC
    """)

    rows = cur.fetchall()
    if not rows:
        print("✗ No IRS data found in database")
        db.close()
        return False

    print("Distribution by status:")
    for status, count in rows:
        print(f"  {status}: {count:,}")

    # Check for revoked in active scoring tiers (should be 0)
    cur.execute("""
        SELECT COUNT(*) as cnt FROM registry_enriched
        WHERE irs_eligibility_status = 'revoked'
        AND scoring_tier IN ('1_verified', '2_verified', '3_verified')
    """)
    revoked_in_active = cur.fetchone()[0]

    if revoked_in_active > 0:
        print(f"\n✗ CRITICAL: {revoked_in_active} revoked orgs in active tiers")
        db.close()
        return False
    else:
        print(f"\n✓ No revoked orgs in active tiers")

    db.close()
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 3 IRS Eligibility Persistence")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to database")
    parser.add_argument("--add-columns-only", action="store_true", help="Add columns but do not persist data")
    args = parser.parse_args()

    # Dry-run is strictly read-only: no schema or data writes.
    if args.dry_run:
        stats = persist_irs_eligibility(str(DB_PATH), str(MANIFEST_PATH), dry_run=True)
        if not stats or stats.get("errors"):
            print("\n✗ Dry-run encountered errors")
            sys.exit(1)
        print("\n✓ Dry-run complete (no schema or data writes)")
        sys.exit(0)

    if not add_irs_columns(str(DB_PATH)):
        print("\n✗ Failed to add columns")
        sys.exit(1)

    if args.add_columns_only:
        print("\n✓ Columns added successfully")
        sys.exit(0)

    stats = persist_irs_eligibility(str(DB_PATH), str(MANIFEST_PATH), dry_run=False)
    if not stats or stats.get("errors") or stats.get("updated") != stats.get("total"):
        print("\n✗ Persistence incomplete or encountered errors")
        sys.exit(1)

    if not verify_persistence(str(DB_PATH)):
        print("\n✗ Verification failed")
        sys.exit(1)

    print("\n✓ Phase 3 persistence complete")
