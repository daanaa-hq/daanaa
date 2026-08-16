#!/usr/bin/env python3
"""
scripts/ops/refresh_stale_orgs_from_gt990.py

Refreshes total_revenue/total_assets/latest_tax_year for already-populated
orgs whose data is stale relative to what's available in the gt990 raw-XML
index -- closes the gap found 2026-08-16 (Aga Khan Foundation USA stuck at
FY2023 while FY2025 was already public; see DECISIONS.md same date).

Distinct from scripts/enrichment/ingest_gt990_index.py, which only ever
refreshes source='bmf_stub' records (near-empty stub rows). This script is
scoped to the opposite population: orgs that already have real data, just
old data, prioritized by staleness and organization size.

Never touches program_expenses/management_expenses/fundraising_expenses/
program_expense_pct (confirmed unreliable at scale, separate concern -- see
DECISIONS.md 2026-08-16 "Expense breakdown chart hidden site-wide").

Safety rules (same as ingest_irs_soi.py):
  - Never downgrade to an older tax year than what's already in the DB
  - Additive only -- no new columns, no schema change
  - Dry-run by default; --apply required to write

Usage:
    python3 scripts/ops/refresh_stale_orgs_from_gt990.py --dry-run --limit 1000
    python3 scripts/ops/refresh_stale_orgs_from_gt990.py --apply --min-revenue 1000000
"""
import argparse
import csv
import sqlite3
import sys
import time
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
GT990_LATEST = Path.home() / "meritgiving" / "data" / "cache" / "gt990_latest.csv"
BATCH = 2000


def parse_year(tax_period: str) -> int:
    """'2025-12-31' or '2024-06-30' -> 2025 / 2024. Returns 0 on failure."""
    try:
        return int(tax_period[:4])
    except (ValueError, TypeError, IndexError):
        return 0


def to_float(v):
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def load_candidates(db, min_revenue: float, limit: int | None):
    """EINs already in the DB with real data, keyed for staleness comparison."""
    sql = """
        SELECT EIN, latest_tax_year, total_revenue
        FROM registry_enriched
        WHERE total_revenue >= ?
          AND latest_tax_year IS NOT NULL
          AND data_source != 'gt990_index'
        ORDER BY total_revenue DESC
    """
    params = [min_revenue]
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    rows = db.execute(sql, params).fetchall()
    return {r[0].zfill(9): {"year": r[1], "revenue": r[2]} for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    ap.add_argument("--min-revenue", type=float, default=1_000_000,
                     help="Only consider orgs at/above this revenue (default $1M -- large orgs file fastest/most reliably)")
    ap.add_argument("--limit", type=int, default=None, help="Cap candidate pool size (for testing)")
    args = ap.parse_args()

    if not GT990_LATEST.exists():
        print(f"ERROR: {GT990_LATEST} not found. Run scripts/ops/refresh_gt990_index.sh first.")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")

    print(f"Loading candidate orgs (revenue >= ${args.min_revenue:,.0f})...")
    candidates = load_candidates(db, args.min_revenue, args.limit)
    print(f"  {len(candidates):,} candidate EINs loaded")

    print(f"Scanning {GT990_LATEST} ({GT990_LATEST.stat().st_size / 1e9:.1f} GB)...")
    t0 = time.time()
    updates = {}  # ein -> (year, revenue, assets)
    scanned = 0

    with open(GT990_LATEST, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scanned += 1
            if scanned % 1_000_000 == 0:
                elapsed = time.time() - t0
                print(f"  scanned {scanned:,} rows ({elapsed:.0f}s, {len(updates):,} candidate updates found so far)")

            ein = (row.get("EIN") or "").strip().zfill(9)
            cand = candidates.get(ein)
            if not cand:
                continue

            form = (row.get("FormType") or "").strip()
            if form != "990":  # Skip EZ/PF -- different financial statement shape
                continue

            tax_period = (row.get("TaxPeriod") or "").strip()
            year = parse_year(tax_period)
            if year <= cand["year"]:
                continue  # Not newer than what we already have -- never downgrade

            revenue = to_float(row.get("TotalRevenueCY"))
            assets = to_float(row.get("TotalAssetsBkEOY"))
            if revenue is None:
                continue

            prev = updates.get(ein)
            if prev is None or year > prev[0]:
                updates[ein] = (year, revenue, assets)

    elapsed = time.time() - t0
    print(f"\nScan complete in {elapsed:.0f}s. {len(updates):,} orgs have newer data available.")

    if not updates:
        print("Nothing to update.")
        return

    sample = list(updates.items())[:5]
    print("\nSample updates (EIN -> new_year, new_revenue):")
    for ein, (year, revenue, assets) in sample:
        old = candidates[ein]
        print(f"  {ein}: {old['year']} -> {year}, ${old['revenue']:,.0f} -> ${revenue:,.0f}")

    if not args.apply:
        print(f"\nDRY RUN -- no changes written. Re-run with --apply to write {len(updates):,} updates.")
        return

    print(f"\nWriting {len(updates):,} updates...")
    batch = []
    for ein, (year, revenue, assets) in updates.items():
        batch.append((revenue, assets, year, ein))
        if len(batch) >= BATCH:
            db.executemany(
                "UPDATE registry_enriched SET total_revenue = ?, total_assets = COALESCE(?, total_assets), "
                "latest_tax_year = ?, data_source = 'gt990_index' WHERE EIN = ?",
                batch
            )
            db.commit()
            batch.clear()
    if batch:
        db.executemany(
            "UPDATE registry_enriched SET total_revenue = ?, total_assets = COALESCE(?, total_assets), "
            "latest_tax_year = ?, data_source = 'gt990_index' WHERE EIN = ?",
            batch
        )
        db.commit()

    print(f"Done. {len(updates):,} orgs refreshed.")
    db.close()


if __name__ == "__main__":
    main()
