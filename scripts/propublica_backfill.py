#!/usr/bin/env python3
"""
scripts/propublica_backfill.py
Update registry_enriched with the latest revenue, assets, mission, and
tax year from the ProPublica cache files.

For each EIN in data/propublica_cache/, picks the most recent filing
with valid (non-zero) revenue and writes it back to the DB.

After this runs, execute scripts/recompute_percentiles.py to refresh
ntee1_percentile rankings.

Usage:
    python3 scripts/propublica_backfill.py
    python3 scripts/propublica_backfill.py --dry-run
"""

import json, sqlite3, os, sys, argparse
from pathlib import Path
from datetime import datetime, timezone

BASE     = Path.home() / "meritgiving"
CACHE    = BASE / "data" / "propublica_cache"
DB_PATH  = BASE / "data" / "merit_registry.db"
BATCH    = 500
LOG_EVERY = 2000

def best_filing(filings):
    """Return the most recent filing that has a positive revenue figure."""
    valid = []
    for f in filings:
        try:
            yr  = int(f.get("tax_prd_yr") or 0)
            rev = float(f.get("totrevenue") or 0)
            if yr > 0 and rev > 0:
                valid.append((yr, f))
        except (TypeError, ValueError):
            continue
    if not valid:
        return None
    valid.sort(key=lambda x: x[0], reverse=True)
    return valid[0][1]


def run(dry_run=False):
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    now = datetime.now(timezone.utc).isoformat()

    # Build EIN lookup: both zero-padded and stripped → rowid
    print("Building EIN index from DB...")
    ein_set = set()
    for (ein,) in db.execute("SELECT EIN FROM registry_enriched"):
        ein_set.add(ein)
    print(f"  {len(ein_set):,} EINs in registry_enriched")

    files = sorted(CACHE.glob("*.json"))
    print(f"  {len(files):,} files in propublica_cache\n")

    stats = dict(processed=0, updated=0, skipped_no_filing=0,
                 skipped_not_in_db=0, skipped_bad_file=0)

    batch = []

    def flush(force=False):
        if not batch or (not force and len(batch) < BATCH):
            return
        if not dry_run:
            db.executemany(
                """UPDATE registry_enriched SET
                       total_revenue   = ?,
                       total_assets    = ?,
                       latest_tax_year = ?,
                       mission         = COALESCE(NULLIF(?, ''), mission),
                       website         = COALESCE(NULLIF(?, ''), website),
                       data_source     = ?,
                       updated_at      = ?,
                       coverage_score  = ?
                   WHERE EIN = ?""",
                batch
            )
            db.commit()
        batch.clear()

    for i, path in enumerate(files, 1):
        stats["processed"] += 1

        # --- parse file ---
        try:
            raw = path.read_text(encoding="utf-8").strip()
            if not raw or raw == "null":
                stats["skipped_bad_file"] += 1
                continue
            data = json.loads(raw)
        except Exception:
            stats["skipped_bad_file"] += 1
            continue

        # --- resolve EIN ---
        ein_raw = path.stem                        # e.g. "010024455"
        ein_alt = ein_raw.lstrip("0") or "0"       # e.g. "10024455"

        if ein_raw in ein_set:
            ein_db = ein_raw
        elif ein_alt in ein_set:
            ein_db = ein_alt
        else:
            stats["skipped_not_in_db"] += 1
            continue

        # --- pick best filing ---
        filings = data.get("filings_with_data") or []
        filing  = best_filing(filings)
        if filing is None:
            stats["skipped_no_filing"] += 1
            continue

        revenue   = float(filing.get("totrevenue") or 0)
        assets    = float(filing.get("totassetsend") or 0) or None
        tax_year  = int(filing.get("tax_prd_yr") or 0) or None

        org       = data.get("organization") or {}
        mission   = (org.get("mission") or "").strip()[:2000]
        website   = (org.get("website") or "").strip()[:500]

        # coverage_score: 1 pt per available field
        coverage = sum([
            bool(revenue),
            bool(assets),
            bool(tax_year),
            bool(mission),
            bool(website),
        ])

        batch.append((
            revenue, assets, tax_year,
            mission, website,
            "propublica", now,
            coverage,
            ein_db,
        ))
        stats["updated"] += 1
        flush()

        if i % LOG_EVERY == 0:
            pct = i / len(files) * 100
            print(f"  [{pct:5.1f}%] {i:,}/{len(files):,} files  |  "
                  f"updated={stats['updated']:,}  "
                  f"no_filing={stats['skipped_no_filing']:,}  "
                  f"not_in_db={stats['skipped_not_in_db']:,}")

    flush(force=True)

    print(f"""
{'='*55}
ProPublica backfill {'DRY RUN ' if dry_run else ''}complete
{'='*55}
  Files processed   : {stats['processed']:>8,}
  DB rows updated   : {stats['updated']:>8,}
  No valid filing   : {stats['skipped_no_filing']:>8,}
  EIN not in DB     : {stats['skipped_not_in_db']:>8,}
  Bad/empty files   : {stats['skipped_bad_file']:>8,}
{'='*55}
""")

    if not dry_run:
        print("Next step: run  python3 scripts/recompute_percentiles.py\n")

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and count without writing to DB")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
