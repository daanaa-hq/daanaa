#!/usr/bin/env python3
"""
scripts/ops/build_org_revenue_history.py

Builds org_revenue_history from data/cache/gt990_latest.csv -- backs the
real 5-year financial trends feature (FinancialTrends.tsx previously showed
a fabricated claim with no data behind it; see DECISIONS.md 2026-08-16).

CSV-only, no XML downloads needed: gt990_latest.csv already carries
TotalRevenueCY/TotalAssetsBkEOY/TaxYear pre-extracted per filing. Form 990
only (EZ/PF have a different statement shape -- can extend later).

Additive-only: writes to the new org_revenue_history table (migration 023),
never touches registry_enriched.

Usage:
    python3 scripts/ops/build_org_revenue_history.py --limit 1000   # test
    python3 scripts/ops/build_org_revenue_history.py                # full run
"""
import argparse
import csv
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
GT990_LATEST = Path.home() / "meritgiving" / "data" / "cache" / "gt990_latest.csv"
BATCH = 5000


def to_float(v):
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Cap known-EIN set size (for testing)")
    args = ap.parse_args()

    db = sqlite3.connect(DB_PATH, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")

    print("Loading known EINs from registry_enriched...")
    sql = "SELECT EIN FROM registry_enriched"
    if args.limit:
        sql += f" LIMIT {args.limit}"
    known = {r[0].zfill(9) for r in db.execute(sql).fetchall()}
    print(f"  {len(known):,} EINs loaded")

    now = datetime.now(timezone.utc).isoformat()
    batch = []
    scanned = 0
    matched = 0
    t0 = time.time()

    print(f"Scanning {GT990_LATEST} ({GT990_LATEST.stat().st_size / 1e9:.1f} GB)...")
    with open(GT990_LATEST, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scanned += 1
            if scanned % 1_000_000 == 0:
                elapsed = time.time() - t0
                print(f"  scanned {scanned:,} rows ({elapsed:.0f}s, {matched:,} matched)")

            ein = (row.get("EIN") or "").strip().zfill(9)
            if ein not in known:
                continue

            form = (row.get("FormType") or "").strip()
            if form != "990":
                continue

            tax_year_raw = (row.get("TaxYear") or "").strip()
            if not tax_year_raw.isdigit():
                continue
            tax_year = int(tax_year_raw)

            revenue = to_float(row.get("TotalRevenueCY"))
            assets = to_float(row.get("TotalAssetsBkEOY"))
            expenses = to_float(row.get("TotalExpensesCY"))
            if revenue is None and assets is None and expenses is None:
                continue

            matched += 1
            batch.append((ein, tax_year, revenue, assets, expenses, form, now))

            if len(batch) >= BATCH:
                db.executemany(
                    "INSERT OR REPLACE INTO org_revenue_history "
                    "(EIN, tax_year, total_revenue, total_assets, total_expenses, form_type, extracted_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    batch
                )
                db.commit()
                batch.clear()

    if batch:
        db.executemany(
            "INSERT OR REPLACE INTO org_revenue_history "
            "(EIN, tax_year, total_revenue, total_assets, total_expenses, form_type, extracted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            batch
        )
        db.commit()

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. {matched:,} (EIN, tax_year) rows written.")

    n_orgs = db.execute("SELECT COUNT(DISTINCT EIN) FROM org_revenue_history").fetchone()[0]
    n_five_plus = db.execute("""
        SELECT COUNT(*) FROM (
            SELECT EIN FROM org_revenue_history GROUP BY EIN HAVING COUNT(*) >= 5
        )
    """).fetchone()[0]
    print(f"Distinct orgs with any history: {n_orgs:,}")
    print(f"Orgs with 5+ years of history: {n_five_plus:,}")

    db.close()


if __name__ == "__main__":
    main()
