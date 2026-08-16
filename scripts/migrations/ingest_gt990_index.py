#!/usr/bin/env python3
"""
scripts/ingest_gt990_index.py

Backfills registry_enriched stubs using the GivingTuesday 990 index CSV.
The index has pre-extracted financials — no XML parsing required.

Fields updated:
  total_revenue, total_assets, total_liabilities, net_assets,
  latest_tax_year, website, data_source

Only touches rows with source='bmf_stub'. Never overwrites existing data
from richer sources (propublica / irs_soi).

Usage:
    python3 scripts/ingest_gt990_index.py
    python3 scripts/ingest_gt990_index.py --index data/cache/gt990_index_2026-03-20.csv
    python3 scripts/ingest_gt990_index.py --dry-run
"""

import sqlite3, csv, time, argparse
from pathlib import Path

DB_PATH    = Path.home() / "meritgiving" / "data" / "merit_registry.db"
INDEX_PATH = Path.home() / "meritgiving" / "data" / "cache" / "gt990_index_2026-03-20.csv"

SKIP_WEBSITE = {"", "N/A", "n/a", "NA", "None", "none"}


def clean_num(val: str) -> float | None:
    v = val.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default=str(INDEX_PATH))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    idx_path = Path(args.index)
    if not idx_path.exists():
        raise SystemExit(f"Index file not found: {idx_path}\n"
                         "Run: aws s3 cp s3://gt990datalake-rawdata/Indices/990xmls/"
                         "index_latest_only_efiledata_xmls_created_on_2026-03-20.csv "
                         "data/cache/gt990_index_2026-03-20.csv --no-sign-request")

    db = sqlite3.connect(DB_PATH, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")

    # Load stub EINs
    stub_eins = {r[0] for r in db.execute(
        "SELECT EIN FROM registry_enriched WHERE source='bmf_stub'"
    )}
    print(f"Stub EINs loaded: {len(stub_eins):,}", flush=True)

    # Scan index, collect best (latest) filing per EIN
    best: dict[str, dict] = {}

    with open(idx_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ein = row["EIN"].strip()
            if ein not in stub_eins:
                continue
            try:
                tax_year = int(row.get("TaxYear", "") or 0)
            except ValueError:
                tax_year = 0

            prev = best.get(ein)
            if prev and prev["tax_year"] >= tax_year:
                continue  # keep the newer filing

            website = row.get("Website", "").strip()
            best[ein] = {
                "tax_year":   tax_year or None,
                "revenue":    clean_num(row.get("TotalRevenueCY", "")),
                "assets":     clean_num(row.get("TotalAssetsBkEOY", "")),
                "liabilities":clean_num(row.get("TotalLiabilitiesBkEOY", "")),
                "net_assets": clean_num(row.get("TotalNetAssetsBkEOY", "")),
                "website":    website if website not in SKIP_WEBSITE else None,
                "form_type":  row.get("FormType", "").strip(),
            }

    print(f"Stubs matched in index: {len(best):,}", flush=True)
    with_rev = sum(1 for v in best.values() if v["revenue"] is not None)
    with_site = sum(1 for v in best.values() if v["website"])
    print(f"  with revenue: {with_rev:,}", flush=True)
    print(f"  with website: {with_site:,}", flush=True)

    if args.dry_run:
        print("[dry-run] no writes", flush=True)
        return

    written = 0
    t0 = time.time()
    for ein, d in best.items():
        db.execute("""
            UPDATE registry_enriched SET
              total_revenue   = CASE WHEN total_revenue IS NULL AND ? IS NOT NULL THEN ? ELSE total_revenue END,
              total_assets    = CASE WHEN total_assets IS NULL AND ? IS NOT NULL THEN ? ELSE total_assets END,
              total_liabilities = CASE WHEN total_liabilities IS NULL AND ? IS NOT NULL THEN ? ELSE total_liabilities END,
              net_assets      = CASE WHEN net_assets IS NULL AND ? IS NOT NULL THEN ? ELSE net_assets END,
              latest_tax_year = CASE WHEN ? IS NOT NULL THEN MAX(COALESCE(latest_tax_year,0), ?) ELSE latest_tax_year END,
              website         = CASE WHEN website IS NULL AND ? IS NOT NULL THEN ? ELSE website END,
              data_source     = CASE WHEN total_revenue IS NULL AND ? IS NOT NULL THEN 'gt990_index' ELSE data_source END
            WHERE EIN = ? AND source = 'bmf_stub'
        """, (
            d["revenue"], d["revenue"],
            d["assets"],  d["assets"],
            d["liabilities"], d["liabilities"],
            d["net_assets"],  d["net_assets"],
            d["tax_year"],    d["tax_year"],
            d["website"],     d["website"],
            d["revenue"],
            ein,
        ))
        written += 1
        if written % 5000 == 0:
            db.commit()
            print(f"  {written:,} written  ({time.time()-t0:.0f}s)", flush=True)

    db.commit()
    print(f"\n[done] {written:,} stubs updated in {time.time()-t0:.0f}s", flush=True)

    # Summary
    upgraded = db.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE source='bmf_stub' AND total_revenue IS NOT NULL
    """).fetchone()[0]
    print(f"Stubs with revenue now: {upgraded:,}", flush=True)


if __name__ == "__main__":
    main()
