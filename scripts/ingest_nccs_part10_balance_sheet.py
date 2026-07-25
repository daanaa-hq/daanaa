#!/usr/bin/env python3
"""
NCCS Part 10 (Balance Sheet) ingestion.

Fills total_assets / total_liabilities from Form 990 Part X end-of-year totals.
Processes newest year first and never overwrites a value already present, so a
re-run is safe and later years win only where earlier years left a hole.

Usage:
    python3 scripts/ingest_nccs_part10_balance_sheet.py [--limit-years N]
"""
import argparse
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"
NCCS_DIR = Path.home() / "meritgiving" / "data" / "nccs"
LOG = Path.home() / "meritgiving" / "logs" / "nccs_part10_ingest.log"

ASSET_COL = "F9_10_ASSET_TOT_EOY"
LIAB_COL = "F9_10_LIAB_TOT_EOY"
COMMIT_EVERY = 50_000


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def parse_amount(raw):
    """NCCS numerics arrive as bare digits, quoted, or empty. Return 0 on junk."""
    if not raw:
        return 0.0
    try:
        return float(str(raw).strip().strip('"'))
    except ValueError:
        return 0.0


def ingest(limit_years=None):
    files = sorted(NCCS_DIR.glob("F9-P10-T00-BALANCE-SHEET-*.CSV"), reverse=True)
    if limit_years:
        files = files[:limit_years]
    if not files:
        log("No Part 10 files found — nothing to do.")
        return 1

    conn = sqlite3.connect(str(DB), timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    cur = conn.cursor()

    grand_assets = grand_liab = 0

    for path in files:
        year = path.stem.split("-")[-1]
        rows = assets_set = liab_set = 0
        log(f"{year}: reading {path.name}")

        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            reader = csv.DictReader(fh)
            if ASSET_COL not in reader.fieldnames:
                log(f"{year}: SKIP — {ASSET_COL} absent from header")
                continue

            for row in reader:
                rows += 1
                ein = (row.get("ORG_EIN") or "").strip().zfill(9)
                if not ein or ein == "000000000":
                    continue

                assets = parse_amount(row.get(ASSET_COL))
                liab = parse_amount(row.get(LIAB_COL))
                if assets <= 0 and liab <= 0:
                    continue

                if assets > 0:
                    cur.execute(
                        "UPDATE registry_enriched SET total_assets=? "
                        "WHERE EIN=? AND total_assets IS NULL",
                        (assets, ein),
                    )
                    assets_set += cur.rowcount
                if liab > 0:
                    cur.execute(
                        "UPDATE registry_enriched SET total_liabilities=? "
                        "WHERE EIN=? AND total_liabilities IS NULL",
                        (liab, ein),
                    )
                    liab_set += cur.rowcount

                if rows % COMMIT_EVERY == 0:
                    conn.commit()
                    log(f"{year}: {rows:,} rows | +{assets_set:,} assets | +{liab_set:,} liabilities")

        conn.commit()
        grand_assets += assets_set
        grand_liab += liab_set
        log(f"{year}: DONE — {rows:,} rows | +{assets_set:,} assets | +{liab_set:,} liabilities")

    cur.execute("SELECT COUNT(total_assets), COUNT(total_liabilities) FROM registry_enriched")
    have_assets, have_liab = cur.fetchone()
    conn.close()

    log("=" * 70)
    log(f"Part 10 ingest complete: +{grand_assets:,} assets, +{grand_liab:,} liabilities")
    log(f"Coverage now: {have_assets:,} assets / {have_liab:,} liabilities")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-years", type=int, default=None)
    args = ap.parse_args()
    sys.exit(ingest(args.limit_years))
