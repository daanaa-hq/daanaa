#!/usr/bin/env python3
"""
Backfill program_expense_pct from NCCS e-filer Part IX data.

Source: https://nccs-efile.s3.us-east-1.amazonaws.com/public/efile_v2_1/
Files:  F9-P09-T00-EXPENSES-[YEAR].CSV  (2009–2024)

Key columns used:
  ORG_EIN            — EIN
  TAX_YEAR           — tax year
  F9_09_EXP_TOT_PROG — total program service expenses
  F9_09_EXP_TOT_TOT  — total functional expenses

program_expense_pct = F9_09_EXP_TOT_PROG / F9_09_EXP_TOT_TOT * 100

Only fills rows where program_expense_pct is currently NULL or 0.
Preserves existing values.

Run:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/backfill_program_expenses.py [--years 2021 2022 2023]
"""

import argparse
import csv
import io
import sqlite3
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DB      = Path.home() / "meritgiving/data/merit_registry.db"
CACHE   = Path.home() / "meritgiving/data/nccs"
LOG     = Path.home() / "meritgiving/logs/backfill_program_expenses.log"

BASE_URL = "https://nccs-efile.s3.us-east-1.amazonaws.com/public/efile_v2_1"

DEFAULT_YEARS = list(range(2009, 2025))   # 2009–2024, oldest first (newer wins)

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def download(year: int, cache_dir: Path) -> Path:
    fname = f"F9-P09-T00-EXPENSES-{year}.CSV"
    dest  = cache_dir / fname
    if dest.exists():
        log(f"  {fname} already cached ({dest.stat().st_size/1e6:.0f} MB)")
        return dest
    url = f"{BASE_URL}/{fname}"
    log(f"  Downloading {url} ...")
    tmp = dest.with_suffix(".tmp")
    try:
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(dest)
        log(f"  Saved {dest.stat().st_size/1e6:.0f} MB → {dest.name}")
    except Exception as e:
        tmp.unlink(missing_ok=True)
        log(f"  FAILED {fname}: {e}")
        return None
    return dest

def parse_file(path: Path) -> dict:
    """Return {ein: (tax_year, prog_pct)} for valid rows."""
    records = {}
    skipped = 0
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ein = (row.get("ORG_EIN") or row.get("EIN2") or "").strip().zfill(9)
            if not ein or ein == "000000000":
                continue
            try:
                tax_year = int(row.get("TAX_YEAR") or 0)
                prog = float(row.get("F9_09_EXP_TOT_PROG") or 0)
                total = float(row.get("F9_09_EXP_TOT_TOT") or 0)
            except (ValueError, TypeError):
                skipped += 1
                continue
            if total <= 0:
                continue
            pct = round(prog / total * 100, 2)
            if pct < 0 or pct > 100:
                continue
            # Keep most recent tax year per EIN
            if ein not in records or tax_year > records[ein][0]:
                records[ein] = (tax_year, pct)
    if skipped:
        log(f"    Skipped {skipped:,} unparseable rows")
    return records

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS)
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing program_expense_pct values")
    args = parser.parse_args()

    log("=" * 60)
    log("Backfill program_expense_pct from NCCS e-filer data")
    log(f"Years: {min(args.years)}–{max(args.years)}")
    log("=" * 60)

    CACHE.mkdir(parents=True, exist_ok=True)

    # Build EIN → (tax_year, prog_pct) from all years; newer overwrites older
    all_records: dict[str, tuple] = {}

    for year in sorted(args.years):
        path = download(year, CACHE)
        if not path:
            continue
        log(f"  Parsing {path.name} ...")
        recs = parse_file(path)
        new = updated = 0
        for ein, (yr, pct) in recs.items():
            if ein not in all_records or yr > all_records[ein][0]:
                all_records[ein] = (yr, pct)
                new += 1
            else:
                updated += 1
        log(f"    {len(recs):,} rows → {new:,} new EINs, {updated:,} updated")

    log(f"Total unique EINs across all years: {len(all_records):,}")

    # Write to DB
    conn = sqlite3.connect(str(DB))

    if args.overwrite:
        rows = [(pct, ein) for ein, (_, pct) in all_records.items()]
        conn.executemany(
            "UPDATE registry_enriched SET program_expense_pct=? WHERE EIN=?", rows
        )
    else:
        # Only fill NULLs and zeros
        rows = [(pct, ein) for ein, (_, pct) in all_records.items()]
        conn.executemany("""
            UPDATE registry_enriched
            SET program_expense_pct = ?
            WHERE EIN = ?
              AND (program_expense_pct IS NULL OR program_expense_pct = 0)
        """, rows)

    conn.commit()

    # Report results
    filled = conn.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE program_expense_pct > 0"
    ).fetchone()[0]
    scoreable = conn.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE deductibility='1'
          AND total_revenue > 0 AND total_expenses > 0
          AND program_expense_pct IS NOT NULL AND program_expense_pct > 0
          AND months_of_reserve IS NOT NULL AND net_assets IS NOT NULL
    """).fetchone()[0]

    log(f"program_expense_pct filled: {filled:,} rows")
    log(f"Newly scoreable orgs:       {scoreable:,}")
    log("=" * 60)
    log("Backfill complete — re-run merit_scorer_v4_0.py to update scores")
    log("=" * 60)

    conn.close()

if __name__ == "__main__":
    main()
