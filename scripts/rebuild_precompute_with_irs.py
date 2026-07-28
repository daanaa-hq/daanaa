#!/usr/bin/env python3
"""
Phase 3 Precompute Rebuild — Includes IRS Eligibility Fields

Rebuilds precomputed org detail JSON files to include:
- irs_eligibility_status
- irs_eligibility_checked_at
- irs_eligibility_sources
- irs_eligibility_explanation

This makes IRS eligibility data available on the droplet (staging/production).

Usage:
  python3 scripts/rebuild_precompute_with_irs.py [--dry-run] [--limit N]
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "merit_registry.db"
PRECOMPUTE_DIR = Path(__file__).parent.parent / "precompute_output" / "orgs"

def build_precompute_with_irs(limit: int = None, dry_run: bool = False) -> dict:
    """
    Rebuild org precompute files with IRS eligibility fields.

    Returns: {
        'total': count of orgs processed,
        'updated': count of files updated,
        'errors': list of EINs that failed,
        'precompute_dir': path to precompute directory
    }
    """

    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Get orgs with IRS eligibility data
    query = """
        SELECT
            EIN,
            organization_name,
            irs_eligibility_status,
            irs_eligibility_checked_at,
            irs_eligibility_sources,
            irs_eligibility_explanation
        FROM registry_enriched
        WHERE irs_eligibility_status IS NOT NULL
        ORDER BY EIN
    """

    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query)
    rows = cur.fetchall()
    db.close()

    print(f"\n=== Precompute Rebuild with IRS (dry_run={dry_run}) ===")
    print(f"Found {len(rows):,} orgs with IRS eligibility data")

    # Ensure precompute directory exists
    PRECOMPUTE_DIR.mkdir(parents=True, exist_ok=True)

    stats = {
        'total': len(rows),
        'updated': 0,
        'errors': [],
        'precompute_dir': str(PRECOMPUTE_DIR),
    }

    for idx, row in enumerate(rows, 1):
        if idx % 100000 == 0:
            print(f"  Processing {idx:,} / {len(rows):,}...")

        try:
            ein = row['EIN']
            org_file = PRECOMPUTE_DIR / f"{ein}.json"

            # Try to load existing org data
            if org_file.exists():
                with open(org_file, 'r', encoding='utf-8') as f:
                    org_data = json.load(f)
            else:
                org_data = {'ein': ein}

            # Add/update IRS fields
            org_data['irs_eligibility_status'] = row['irs_eligibility_status']
            org_data['irs_eligibility_checked_at'] = row['irs_eligibility_checked_at']
            org_data['irs_eligibility_sources'] = json.loads(
                row['irs_eligibility_sources']
            ) if row['irs_eligibility_sources'] else []
            org_data['irs_eligibility_explanation'] = row['irs_eligibility_explanation']

            # Write back (unless dry-run)
            if not dry_run:
                with open(org_file, 'w', encoding='utf-8') as f:
                    json.dump(org_data, f, separators=(',', ':'))
                stats['updated'] += 1

        except Exception as e:
            print(f"    ✗ Error processing {row['EIN']}: {e}")
            stats['errors'].append((row['EIN'], str(e)))

    print(f"\n=== Precompute Results ===")
    print(f"Orgs processed: {stats['total']:,}")
    print(f"Files updated: {stats['updated']:,}")

    if stats['errors']:
        print(f"✗ Errors: {len(stats['errors'])}")
        for ein, err in stats['errors'][:10]:
            print(f"    {ein}: {err}")

    return stats


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Rebuild precompute with IRS eligibility')
    parser.add_argument('--dry-run', action='store_true', help='Do not write files')
    parser.add_argument('--limit', type=int, help='Process only N orgs (for testing)')
    args = parser.parse_args()

    stats = build_precompute_with_irs(limit=args.limit, dry_run=args.dry_run)

    if stats['errors']:
        print(f"\n⚠ Precompute rebuild had {len(stats['errors'])} errors")
        sys.exit(1)
    else:
        print(f"\n✓ Precompute rebuild complete")
        sys.exit(0)
