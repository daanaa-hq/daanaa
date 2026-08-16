#!/usr/bin/env python3
"""
Backfill revenue_3yr_avg and total_liabilities from IRS SOI extract files (2019–2024).

For each EIN:
  - revenue_3yr_avg: average total_revenue across the 3 most recent tax periods
  - total_liabilities: total liabilities from the most recent tax period

Falls back gracefully if fewer than 3 years exist.

Run:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/backfill_revenue_history.py
"""

import csv
import io
import sqlite3
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DB  = Path.home() / "meritgiving/data/merit_registry.db"
SOI = Path.home() / "meritgiving/data/irs_soi"
LOG = Path.home() / "meritgiving/logs/backfill_revenue_history.log"

# Auto-discovered from data/irs_soi/ — just drop new IRS SOI files there.
# Source: https://www.irs.gov/pub/irs-soi/[YY]eoextract990.zip (published annually)
# e.g. wget https://www.irs.gov/pub/irs-soi/25eoextract990.zip -P data/irs_soi/
def _discover_soi_files(soi_dir: Path) -> list[tuple[str, str]]:
    import re
    files = []
    for p in sorted(soi_dir.glob("*eoextract990.zip")):
        m = re.match(r"(\d{2})eoextract990\.zip", p.name)
        year = f"20{m.group(1)}" if m else p.stem
        files.append((year, p.name))
    return files

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def read_soi_file(zip_path: Path) -> dict:
    """Read one SOI 990 extract zip. Returns {ein: (tax_pd, revenue, liabilities)}."""
    records = {}
    try:
        with zipfile.ZipFile(zip_path) as z:
            fname = z.namelist()[0]
            with z.open(fname) as f:
                content = f.read().decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(content))
        # Strip BOM and normalize to lowercase (IRS files inconsistently use EIN vs ein)
        fieldnames = [c.lstrip("﻿").strip().lower() for c in (reader.fieldnames or [])]
        reader.fieldnames = fieldnames

        for row in reader:
            ein = (row.get("ein") or "").strip().zfill(9)
            tax_pd = (row.get("tax_pd") or "").strip()
            if not ein or not tax_pd:
                continue
            try:
                tax_year = int(tax_pd) // 100  # YYYYMM → YYYY
                revenue = float(row.get("totrevenue") or 0)
                liabilities = float(row.get("totliabend") or 0)
            except (ValueError, TypeError):
                continue
            # Keep most recent period per EIN within this file
            if ein not in records or tax_year > records[ein][0]:
                records[ein] = (tax_year, revenue, liabilities)
    except Exception as e:
        log(f"  Warning reading {zip_path.name}: {e}")
    return records


def main():
    log("=" * 60)
    log("Backfill revenue history starting")
    log("=" * 60)

    # Load all years: ein → [(tax_year, revenue, liabilities), ...]
    ein_history: dict[str, list] = defaultdict(list)

    for label, fname in _discover_soi_files(SOI):
        path = SOI / fname
        if not path.exists():
            log(f"  {fname} not found — skipping")
            continue
        log(f"  Reading {fname} ({label})...")
        records = read_soi_file(path)
        for ein, (tax_year, revenue, liabilities) in records.items():
            ein_history[ein].append((tax_year, revenue, liabilities))
        log(f"    {len(records):,} EINs loaded")

    log(f"Total unique EINs across all years: {len(ein_history):,}")

    # Compute per-EIN aggregates
    log("Computing 3-year averages and latest liabilities...")
    computed = {}  # ein → (revenue_3yr_avg, total_liabilities)
    for ein, entries in ein_history.items():
        # Sort by tax_year descending, deduplicate (keep latest per year)
        by_year = {}
        for tax_year, revenue, liabilities in entries:
            if tax_year not in by_year or revenue > by_year[tax_year][0]:
                by_year[tax_year] = (revenue, liabilities)
        sorted_entries = sorted(by_year.items(), reverse=True)  # newest first

        # 3-year average revenue
        recent = sorted_entries[:3]
        revenues = [rev for _, (rev, _) in recent if rev > 0]
        rev_avg = sum(revenues) / len(revenues) if revenues else None

        # Latest liabilities
        _, (_, latest_liab) = sorted_entries[0]
        total_liab = latest_liab if latest_liab >= 0 else None

        computed[ein] = (rev_avg, total_liab)

    log(f"Computed aggregates for {len(computed):,} EINs")

    # Add columns if needed and write to DB
    conn = sqlite3.connect(str(DB))
    existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(registry_enriched)")]

    for col, typedef in [("revenue_3yr_avg", "REAL"), ("total_liabilities", "REAL")]:
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col} {typedef}")
            log(f"Added column {col}")

    log("Writing to registry_enriched...")
    rows = [
        (rev_avg, total_liab, ein)
        for ein, (rev_avg, total_liab) in computed.items()
        if rev_avg is not None or total_liab is not None
    ]
    conn.executemany(
        "UPDATE registry_enriched SET revenue_3yr_avg=?, total_liabilities=? WHERE EIN=?",
        rows,
    )
    conn.commit()

    # Verify
    filled = conn.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE revenue_3yr_avg IS NOT NULL"
    ).fetchone()[0]
    liab_filled = conn.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE total_liabilities IS NOT NULL"
    ).fetchone()[0]
    log(f"revenue_3yr_avg filled: {filled:,} rows")
    log(f"total_liabilities filled: {liab_filled:,} rows")

    # Check overlap with scoreable orgs
    overlap = conn.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE deductibility='1'
          AND total_revenue > 0 AND total_expenses > 0
          AND program_expense_pct IS NOT NULL AND program_expense_pct > 0
          AND months_of_reserve IS NOT NULL AND net_assets IS NOT NULL
          AND revenue_3yr_avg IS NOT NULL
    """).fetchone()[0]
    log(f"Scoreable orgs with 3yr revenue history: {overlap:,}")

    conn.close()
    log("=" * 60)
    log("Backfill complete")
    log("=" * 60)


if __name__ == "__main__":
    main()
