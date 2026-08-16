#!/usr/bin/env python3
"""
Phase 3 Precompute Rebuild — Includes IRS Eligibility Fields

Rebuilds precomputed org detail JSON files to include:
- irs_eligibility_status
- irs_eligibility_checked_at
- irs_eligibility_sources
- irs_eligibility_notes

This makes IRS eligibility data available on the droplet (staging/production).

IMPORTANT: the live API's load_org_detail() (droplet_api.py) reads
orgs/<ein[:3]>/<ein>.json.gz — a sharded, gzip-compressed tree — NOT a flat
orgs/<ein>.json file. An earlier version of this script wrote to the flat
path, which meant the rebuild "succeeded" and deployed cleanly but the live
API never saw the new fields (it doesn't read that path at all). See
LESSONS.md 2026-08-12 for the incident. This version targets the sharded
path the API actually reads.

Orgs without an existing sharded .json.gz file (bmf_stub / minimal orgs,
~121K of ~2.057M) are skipped here — load_org_detail() falls back to
search.db for those, which is a separate artifact this script does not
touch. Tracked as a known follow-up, not blocking the primary rebuild.

Usage:
  python3 scripts/rebuild_precompute_with_irs.py [--dry-run] [--limit N]
"""

import gzip
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
            irs_eligibility_notes
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
        'skipped_no_file': 0,
        'errors': [],
        'precompute_dir': str(PRECOMPUTE_DIR),
    }

    for idx, row in enumerate(rows, 1):
        if idx % 100000 == 0:
            print(f"  Processing {idx:,} / {len(rows):,}...")

        try:
            ein = row['EIN']
            org_file = PRECOMPUTE_DIR / ein[:3] / f"{ein}.json.gz"

            # Only update orgs that already have a precomputed detail file.
            # Orgs without one (bmf_stub/minimal) are served from search.db by
            # load_org_detail()'s fallback path, which this script doesn't touch.
            if not org_file.exists():
                stats['skipped_no_file'] += 1
                continue

            with gzip.open(org_file, 'rt', encoding='utf-8') as f:
                org_data = json.load(f)

            # Add/update IRS fields
            org_data['irs_eligibility_status'] = row['irs_eligibility_status']
            org_data['irs_eligibility_checked_at'] = row['irs_eligibility_checked_at']
            org_data['irs_eligibility_sources'] = json.loads(
                row['irs_eligibility_sources']
            ) if row['irs_eligibility_sources'] else []
            org_data['irs_eligibility_notes'] = row['irs_eligibility_notes']

            # Write back (unless dry-run)
            if not dry_run:
                with gzip.open(org_file, 'wt', encoding='utf-8') as f:
                    json.dump(org_data, f, separators=(',', ':'))
                stats['updated'] += 1

        except Exception as e:
            print(f"    ✗ Error processing {row['EIN']}: {e}")
            stats['errors'].append((row['EIN'], str(e)))

    print(f"\n=== Precompute Results ===")
    print(f"Orgs processed: {stats['total']:,}")
    print(f"Files updated: {stats['updated']:,}")
    print(f"Skipped (no precomputed file, served via search.db fallback): {stats['skipped_no_file']:,}")

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
