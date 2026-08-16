#!/usr/bin/env python3
"""
Ingest the data/propublica_cache/*.json files into registry_enriched.
Updates mission, website, has_mission, has_website, data_source.
Only touches rows where mission IS NULL or empty (won't overwrite existing).
"""
import sqlite3, os, json
from pathlib import Path

DB   = Path.home() / "meritgiving/data/merit_registry.db"
CACHE = Path.home() / "meritgiving/data/propublica_cache"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

files = list(CACHE.glob("*.json"))
print(f"Cache files: {len(files):,}")

updated = skipped = missing = 0

for i, f in enumerate(files):
    ein = f.stem
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        continue

    org = data.get("organization") or {}
    mission = (org.get("mission") or "").strip()
    website = (org.get("website") or "").strip()

    filings = data.get("filings_with_data") or []
    latest_year = None
    if filings:
        try:
            latest_year = max(int(f2.get("tax_prd_yr", 0)) for f2 in filings if f2.get("tax_prd_yr")) or None
        except Exception:
            pass

    if not mission and not website and not latest_year:
        skipped += 1
        continue

    row = conn.execute("SELECT EIN FROM registry_enriched WHERE EIN = ?", (ein,)).fetchone()
    if not row:
        missing += 1
        continue

    conn.execute("""
        UPDATE registry_enriched
        SET mission     = CASE WHEN (mission IS NULL OR mission = '') AND ? != '' THEN ? ELSE mission END,
            website     = CASE WHEN (website IS NULL OR website = '') AND ? != '' THEN ? ELSE website END,
            data_source = CASE WHEN (data_source IS NULL OR data_source = '') THEN 'propublica' ELSE data_source END,
            latest_tax_year = CASE WHEN latest_tax_year IS NULL AND ? IS NOT NULL THEN ? ELSE latest_tax_year END
        WHERE EIN = ?
    """, (mission, mission, website, website, latest_year, latest_year, ein))
    updated += 1

    if (i + 1) % 5000 == 0:
        conn.commit()
        print(f"  {i+1:,} / {len(files):,}  updated={updated:,}")

conn.commit()
conn.close()
print(f"\nDone: updated={updated:,}  no_content={skipped:,}  not_in_db={missing:,}")
