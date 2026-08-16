#!/usr/bin/env python3
"""
scripts/patch_precompute_website_status.py

Patches existing precomputed org JSON files to reflect a website_status
promotion that already happened in the live database. Follows the same
convention as patch_precompute_financials.py: read gzipped JSON, patch
one field, rewrite in-place. Idempotent, safe to re-run.

Built for the 2026-08-15 Website Discovery Phase 2 promotion (1,458 orgs
beta -> ok, see DECISIONS.md) but takes an EIN list so it's reusable for
any future website_status change that needs to reach precompute without
a full rebuild.

Usage:
    python3 scripts/patch_precompute_website_status.py --ein-csv path/to/eins.csv
    python3 scripts/patch_precompute_website_status.py --ein-csv path/to/eins.csv --limit 10  # test run
"""

import argparse
import csv
import gzip
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "merit_registry.db"
ORGS_DIR = Path(__file__).parent.parent / "precompute_output" / "orgs"


def load_ein_list(csv_path):
    eins = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            eins.append(row["EIN"])
    return eins


def find_org_file(ein):
    """Precompute orgs are sharded into subdirs by the first 3 digits of
    the EIN (see precompute_orgs.py output layout)."""
    shard = ein[:3]
    path = ORGS_DIR / shard / f"{ein}.json.gz"
    return path if path.exists() else None


def patch_file(path, new_status):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    old_status = data.get("website_status")
    if old_status == new_status:
        return "already_correct"
    data["website_status"] = new_status
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=1) as f:
        json.dump(data, f)
    return f"{old_status}->{new_status}"


def main():
    parser = argparse.ArgumentParser(description="Patch precompute website_status for a specific EIN list")
    parser.add_argument("--ein-csv", required=True, help="CSV with an EIN column")
    parser.add_argument("--limit", type=int, default=None, help="Test run: only patch first N")
    args = parser.parse_args()

    eins = load_ein_list(args.ein_csv)
    if args.limit:
        eins = eins[: args.limit]
    print(f"Loaded {len(eins)} EINs to patch", flush=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    patched, not_found, already_correct, errors = 0, 0, 0, 0
    for ein in eins:
        row = conn.execute(
            "SELECT website_status FROM registry_enriched WHERE EIN = ?", (ein,)
        ).fetchone()
        if not row:
            not_found += 1
            continue
        current_status = row["website_status"]

        path = find_org_file(ein)
        if path is None:
            not_found += 1
            continue

        try:
            result = patch_file(path, current_status)
        except Exception as e:
            print(f"  ERROR {ein}: {e}", flush=True)
            errors += 1
            continue

        if result == "already_correct":
            already_correct += 1
        else:
            patched += 1

    conn.close()

    print("=" * 60)
    print(f"Patched:         {patched}")
    print(f"Already correct: {already_correct}")
    print(f"Not found:       {not_found}")
    print(f"Errors:          {errors}")
    print("=" * 60)


if __name__ == "__main__":
    main()
