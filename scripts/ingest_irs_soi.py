#!/usr/bin/env python3
"""
scripts/ingest_irs_soi.py
Ingest IRS Statistics of Income (SOI) 990 + 990-EZ annual extract files
into registry_enriched.

Source: https://www.irs.gov/statistics/soi-tax-stats-annual-extract-of-tax-exempt-organization-financial-data
Files in: data/irs_soi/

Covers fiscal years 2019–2024 across both 990 and 990-EZ filers.
Only updates revenue/assets/tax_year — never inserts new rows (SOI lacks
org names, states, and NTEE codes).

Rules:
  - Never downgrade a ProPublica row with older SOI data
  - Among SOI years, keep the most recent
  - Writes in year order (oldest→newest) so newest wins naturally

Usage:
    python3 scripts/ingest_irs_soi.py
    python3 scripts/ingest_irs_soi.py --dry-run
    python3 scripts/ingest_irs_soi.py --year 2023    # single year only
"""

import csv, io, sqlite3, os, sys, argparse, zipfile
from pathlib import Path
from datetime import datetime, timezone

BASE    = Path.home() / "meritgiving"
SOI_DIR = BASE / "data" / "irs_soi"
DB_PATH = BASE / "data" / "merit_registry.db"
BATCH   = 2000

# (file_glob_pattern, form_type, revenue_col, assets_col, year_col)
FILE_SPECS = [
    # 990 files: year prefix two-digit, revenue = totrevenue
    {"pattern": "*eoextract990.zip",   "form": "990",    "rev": "totrevenue",  "assets": "totassetsend", "yr": "tax_pd"},
    # 990-EZ files: revenue = totrevnue (different spelling), year col = taxpd
    {"pattern": "*eoextract*EZ*.zip",  "form": "990ez",  "rev": "totrevnue",   "assets": "totassetsend", "yr": "taxpd"},
    {"pattern": "*eoextractez.zip",    "form": "990ez",  "rev": "totrevnue",   "assets": "totassetsend", "yr": "taxpd"},
]


def parse_year(tax_pd_str):
    """YYYYMM → YYYY as int. Returns 0 on failure."""
    try:
        s = str(tax_pd_str).strip()
        if len(s) >= 4:
            return int(s[:4])
    except (ValueError, TypeError):
        pass
    return 0


def to_float(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(',', '').strip())
    except (ValueError, TypeError):
        return None


def ingest_file(db, zip_path: Path, form_type: str,
                rev_col: str, assets_col: str, yr_col: str,
                existing: dict, dry_run: bool, now: str) -> dict:
    stats = dict(rows=0, updated=0, skipped_no_ein=0,
                 skipped_older=0, skipped_not_in_db=0)

    batch = []

    def flush(force=False):
        if not batch or (not force and len(batch) < BATCH):
            return
        if not dry_run:
            db.executemany("""
                UPDATE registry_enriched
                SET total_revenue   = ?,
                    total_assets    = ?,
                    latest_tax_year = ?,
                    data_source     = 'irs_soi',
                    updated_at      = ?
                WHERE EIN = ?
            """, batch)
            db.commit()
        batch.clear()

    with zipfile.ZipFile(zip_path) as zf:
        inner = zf.namelist()[0]
        with zf.open(inner) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8', errors='replace'))

            for row in reader:
                stats["rows"] += 1

                ein = str(row.get("EIN") or "").strip().zfill(9)[:9]
                if not ein or ein == "000000000":
                    stats["skipped_no_ein"] += 1
                    continue

                tax_yr = parse_year(row.get(yr_col) or "")
                if tax_yr < 2000:
                    stats["skipped_no_ein"] += 1
                    continue

                if ein not in existing:
                    stats["skipped_not_in_db"] += 1
                    continue

                existing_yr, existing_src = existing[ein]

                # Never downgrade a ProPublica row with older SOI data
                if existing_src == "propublica" and tax_yr <= existing_yr:
                    stats["skipped_older"] += 1
                    continue
                if tax_yr < existing_yr:
                    stats["skipped_older"] += 1
                    continue

                revenue = to_float(row.get(rev_col))
                assets  = to_float(row.get(assets_col))

                if revenue is None and assets is None:
                    stats["skipped_older"] += 1
                    continue

                batch.append((revenue, assets, tax_yr, now, ein))
                existing[ein] = (tax_yr, "irs_soi")
                stats["updated"] += 1
                flush()

                if stats["rows"] % 100000 == 0:
                    print(f"    {stats['rows']:,} rows | updated={stats['updated']:,} "
                          f"older={stats['skipped_older']:,} not_in_db={stats['skipped_not_in_db']:,}")

    flush(force=True)
    return stats


def run(dry_run=False, only_year=None):
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")

    print("Loading EIN index from DB...")
    existing = {}
    for ein, tax_yr, src in db.execute(
        "SELECT EIN, latest_tax_year, data_source FROM registry_enriched"
    ):
        existing[ein] = (tax_yr or 0, src or "")
    print(f"  {len(existing):,} EINs in registry_enriched\n")

    now = datetime.now(timezone.utc).isoformat()

    # Collect all matching files — process oldest year first so newest wins
    files_to_process = []
    for spec in FILE_SPECS:
        for zip_path in sorted(SOI_DIR.glob(spec["pattern"])):
            # Extract two-digit year prefix from filename
            stem = zip_path.stem  # e.g. "22eoextract990"
            try:
                yr2 = int(stem[:2])
                full_year = 2000 + yr2
            except ValueError:
                full_year = 0

            if only_year and full_year != only_year:
                continue

            files_to_process.append((full_year, zip_path, spec))

    files_to_process.sort(key=lambda x: x[0])  # oldest first

    total_updated = 0
    for full_year, zip_path, spec in files_to_process:
        print(f"[{full_year} {spec['form']}] {zip_path.name}")
        stats = ingest_file(
            db, zip_path, spec["form"],
            spec["rev"], spec["assets"], spec["yr"],
            existing, dry_run, now
        )
        total_updated += stats["updated"]
        print(f"  rows={stats['rows']:,}  updated={stats['updated']:,}  "
              f"skipped_older={stats['skipped_older']:,}  "
              f"not_in_db={stats['skipped_not_in_db']:,}\n")

    # Final summary
    print("=" * 55)
    print(f"IRS SOI ingest {'DRY RUN ' if dry_run else ''}complete")
    print("=" * 55)
    print(f"  Total DB rows updated: {total_updated:,}")

    if not dry_run and total_updated > 0:
        # Quick coverage check
        updated_now, = db.execute(
            "SELECT COUNT(*) FROM registry_enriched WHERE data_source = 'irs_soi'"
        ).fetchone()
        total, = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()
        print(f"  irs_soi coverage:      {updated_now:,} / {total:,} orgs")
        print(f"\nNext step: python3 scripts/recompute_percentiles.py")

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest IRS SOI 990/990-EZ extracts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--year", type=int, help="Process only this year (e.g. 2023)")
    args = parser.parse_args()
    run(dry_run=args.dry_run, only_year=args.year)
