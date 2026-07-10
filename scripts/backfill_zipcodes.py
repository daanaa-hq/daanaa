#!/usr/bin/env python3
"""backfill_zipcodes.py — fill registry_enriched.zipcode from the IRS BMF.

Zipcode coverage was 40% (821K/2.04M), which silently hid 60% of orgs from
the droplet's radius/"near me" search (proximity matches SUBSTR(zipcode,1,5);
NULL never matches — found 2026-07-10, Houston+website returned 0). The BMF
carries ZIP for ~1.97M EINs, same source that took street_address to 95.7%.

Only fills NULL/empty zipcodes — never overwrites an existing value.
Safe to re-run. Uses a long busy timeout so it can interleave with the
overnight enrichment loop's commits.
"""
import csv
import sqlite3
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "merit_registry.db"
BMF = BASE / "data" / "bmf.csv"


def main() -> None:
    t0 = time.time()
    zips: dict[str, str] = {}
    with open(BMF, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ein = (row.get("EIN") or "").strip().zfill(9)
            z = (row.get("ZIP") or "").strip()
            if ein and z:
                zips[ein] = z
    print(f"BMF zips loaded: {len(zips):,} ({time.time()-t0:.0f}s)")

    db = sqlite3.connect(DB, timeout=300)
    before = db.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE zipcode IS NOT NULL AND zipcode != ''"
    ).fetchone()[0]

    rows = db.execute(
        "SELECT EIN FROM registry_enriched WHERE zipcode IS NULL OR zipcode = ''"
    ).fetchall()
    updates = [(zips[ein], ein) for (ein,) in rows if ein in zips]
    print(f"missing zipcode: {len(rows):,} | BMF matches: {len(updates):,}")

    CHUNK = 50_000
    done = 0
    for i in range(0, len(updates), CHUNK):
        db.executemany(
            "UPDATE registry_enriched SET zipcode = ? WHERE EIN = ? AND (zipcode IS NULL OR zipcode = '')",
            updates[i : i + CHUNK],
        )
        db.commit()
        done += len(updates[i : i + CHUNK])
        print(f"  committed {done:,}/{len(updates):,}")

    after = db.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE zipcode IS NOT NULL AND zipcode != ''"
    ).fetchone()[0]
    total = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    print(f"zipcode coverage: {before:,} -> {after:,} of {total:,} "
          f"({100*after/total:.1f}%) in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    sys.exit(main())
