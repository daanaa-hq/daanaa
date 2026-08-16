#!/usr/bin/env python3
"""Backfill registry_enriched.street_address from the IRS BMF extract.

The BMF (data/bmf.csv) is the only source we hold with street addresses;
registry_enriched only carried CITY/STATE/zipcode. The claim flow needs the
street for Phase 2 postal verification letters (Lob).

Idempotent: only fills rows where street_address IS NULL, so re-running after
a fresh BMF download just tops up. Single transaction — safe to interrupt.

Usage:
    venv/bin/python scripts/backfill_street_addresses.py [--csv data/bmf.csv]
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "merit_registry.db"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(ROOT / "data" / "bmf.csv"))
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()

    db = sqlite3.connect(args.db, timeout=60)
    try:
        db.execute("ALTER TABLE registry_enriched ADD COLUMN street_address TEXT")
    except sqlite3.OperationalError:
        pass  # column already present

    db.execute("CREATE TEMP TABLE bmf_street (ein TEXT PRIMARY KEY, street TEXT)")

    rows = 0
    with open(args.csv, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        batch = []
        for r in reader:
            ein = (r.get("EIN") or "").strip()
            street = (r.get("STREET") or "").strip()
            if len(ein) == 9 and street:
                batch.append((ein, street))
            if len(batch) >= 50_000:
                db.executemany("INSERT OR REPLACE INTO bmf_street VALUES (?, ?)", batch)
                rows += len(batch)
                batch.clear()
        if batch:
            db.executemany("INSERT OR REPLACE INTO bmf_street VALUES (?, ?)", batch)
            rows += len(batch)

    print(f"Loaded {rows:,} street addresses from {args.csv}")

    cur = db.execute("""
        UPDATE registry_enriched
        SET street_address = (SELECT street FROM bmf_street WHERE bmf_street.ein = registry_enriched.EIN)
        WHERE street_address IS NULL
          AND EIN IN (SELECT ein FROM bmf_street)
    """)
    db.commit()
    print(f"Backfilled {cur.rowcount:,} registry rows")

    total, filled = db.execute(
        "SELECT COUNT(*), COUNT(street_address) FROM registry_enriched"
    ).fetchone()
    print(f"Coverage: {filled:,} / {total:,} ({100.0 * filled / total:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
