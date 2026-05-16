#!/usr/bin/env python3
"""
scripts/ingest_nccs_core.py
Load an NCCS Core Data file (CSV) into registry_enriched.

The NCCS Core files are published annually by the Urban Institute:
  https://nccs-data.urban.org/data.php?ds=core

Download the most recent year's "501(c)(3) Public Charities" file,
then run:
    python3 scripts/ingest_nccs_core.py --file data/nccs/core_2023_pc.csv

What it does:
  - For rows already in registry_enriched: updates revenue if the NCCS
    tax year is newer than what we have.
  - For new EINs: inserts them.
  - Never overwrites a ProPublica-sourced row with stale NCCS data if
    the NCCS tax year is older.

NCCS column names vary slightly by year.  The script tries common aliases.
"""

import csv, sqlite3, os, sys, argparse
from pathlib import Path
from datetime import datetime, timezone

BASE    = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "merit_registry.db"
BATCH   = 1000

# NCCS column aliases (varies by file year)
EIN_COLS     = ["EIN", "ein"]
NAME_COLS    = ["NAME", "ORGNAME", "name"]
NTEE_COLS    = ["NTEE1", "NTEECC", "ntee1", "nteecc"]
STATE_COLS   = ["STATE", "state"]
CITY_COLS    = ["CITY", "city"]
REV_COLS     = ["TOTREV", "TOTREV2", "totrev", "TOTREVENUE"]
ASSET_COLS   = ["ASSET", "TOTASSETSEND", "totassetsend"]
YEAR_COLS    = ["TAXYR", "TAX_PRD_YR", "taxyr", "TAXYEAR"]

def first_val(row, keys):
    for k in keys:
        v = row.get(k)
        if v not in (None, '', 'NA', 'N/A'):
            return v
    return None

def to_float(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(',', '').strip())
    except (ValueError, TypeError):
        return None

def to_int(v):
    if v is None:
        return None
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return None


def run(csv_path: Path, dry_run: bool = False):
    if not csv_path.exists():
        print(f"File not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")

    # Load current EIN → (latest_tax_year, data_source) map
    print("Loading existing EIN index...")
    existing = {}
    for ein, tax_yr, src in db.execute(
        "SELECT EIN, latest_tax_year, data_source FROM registry_enriched"
    ):
        existing[ein] = (tax_yr or 0, src or '')
    print(f"  {len(existing):,} EINs in DB")

    now = datetime.now(timezone.utc).isoformat()

    stats = dict(rows_read=0, updated=0, inserted=0, skipped_older=0, skipped_no_ein=0)

    update_batch = []
    insert_batch = []

    def flush(force=False):
        if not dry_run:
            if force or len(update_batch) >= BATCH:
                if update_batch:
                    db.executemany("""
                        UPDATE registry_enriched SET
                            total_revenue   = ?,
                            total_assets    = ?,
                            latest_tax_year = ?,
                            NTEE1           = COALESCE(NULLIF(?, ''), NTEE1),
                            STATE           = COALESCE(NULLIF(?, ''), STATE),
                            CITY            = COALESCE(NULLIF(?, ''), CITY),
                            data_source     = 'nccs',
                            updated_at      = ?
                        WHERE EIN = ?
                    """, update_batch)
                    update_batch.clear()
            if force or len(insert_batch) >= BATCH:
                if insert_batch:
                    db.executemany("""
                        INSERT OR IGNORE INTO registry_enriched
                            (EIN, organization_name, NTEE1, STATE, CITY,
                             total_revenue, total_assets, latest_tax_year,
                             data_source, updated_at, coverage_score)
                        VALUES (?,?,?,?,?,?,?,?,'nccs',?,?)
                    """, insert_batch)
                    insert_batch.clear()
            db.commit()

    with open(csv_path, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["rows_read"] += 1

            ein = first_val(row, EIN_COLS)
            if not ein:
                stats["skipped_no_ein"] += 1
                continue
            ein = str(ein).strip().zfill(9)[:9]

            name    = (first_val(row, NAME_COLS) or '').strip()[:300]
            ntee    = (first_val(row, NTEE_COLS) or '').strip()[:1].upper()
            state   = (first_val(row, STATE_COLS) or '').strip()[:2].upper()
            city    = (first_val(row, CITY_COLS) or '').strip()[:100]
            revenue = to_float(first_val(row, REV_COLS))
            assets  = to_float(first_val(row, ASSET_COLS))
            tax_yr  = to_int(first_val(row, YEAR_COLS))

            if stats["rows_read"] % 50000 == 0:
                pct = stats["rows_read"] / max(stats["rows_read"], 1) * 100
                print(f"  {stats['rows_read']:,} rows | "
                      f"updated={stats['updated']:,} inserted={stats['inserted']:,} "
                      f"skipped_older={stats['skipped_older']:,}")

            if ein in existing:
                existing_yr, existing_src = existing[ein]
                # Never downgrade a ProPublica row with older NCCS data
                if existing_src == 'propublica' and (tax_yr or 0) <= existing_yr:
                    stats["skipped_older"] += 1
                    continue
                # Skip if NCCS data is older than what's already stored
                if (tax_yr or 0) < existing_yr:
                    stats["skipped_older"] += 1
                    continue
                update_batch.append((revenue, assets, tax_yr, ntee, state, city, now, ein))
                stats["updated"] += 1
            else:
                coverage = sum([bool(revenue), bool(assets), bool(tax_yr), bool(name)])
                insert_batch.append((ein, name, ntee or None, state or None, city or None,
                                     revenue, assets, tax_yr, now, coverage))
                existing[ein] = (tax_yr or 0, 'nccs')
                stats["inserted"] += 1

            flush()

    flush(force=True)

    print(f"""
{'='*55}
NCCS Core ingest {'DRY RUN ' if dry_run else ''}complete — {csv_path.name}
{'='*55}
  Rows read         : {stats['rows_read']:>8,}
  DB rows updated   : {stats['updated']:>8,}
  New EINs inserted : {stats['inserted']:>8,}
  Skipped (older)   : {stats['skipped_older']:>8,}
  Skipped (no EIN)  : {stats['skipped_no_ein']:>8,}
{'='*55}
""")

    if not dry_run and (stats['updated'] + stats['inserted']) > 0:
        print("Next step: run  python3 scripts/recompute_percentiles.py\n")

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest NCCS Core CSV into registry_enriched")
    parser.add_argument("--file", required=True, help="Path to NCCS Core CSV file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(Path(args.file), dry_run=args.dry_run)
