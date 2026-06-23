#!/usr/bin/env python3
"""backfill_metro.py — stamp each org with its Census metro (CBSA) for search.

Adds/refreshes registry_enriched.metro from data/zip_to_metro.csv. ZIP comes
from registry_enriched.zipcode where present, else from data/bmf.csv by EIN
(only ~41% of rows carry a zipcode; the IRS BMF covers nearly all). The metro
is search metadata only — it is NOT written into mission text, so mission copy
stays town-accurate (Stewardship P3) while a Somerville org becomes findable
under "Boston". See scripts/build_metro_crosswalk.py for the crosswalk.
"""
import argparse
import csv
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "merit_registry.db")
CROSSWALK = os.path.join(BASE, "data", "zip_to_metro.csv")
BMF = os.path.join(BASE, "data", "bmf.csv")


def load_crosswalk():
    z2m = {}
    with open(CROSSWALK) as f:
        for r in csv.DictReader(f):
            z2m[r["zip5"]] = r["metro"]
    return z2m


def load_bmf_zip():
    ein2zip = {}
    with open(BMF, newline="") as f:
        rd = csv.reader(f)
        h = next(rd)
        ei, zi = h.index("EIN"), h.index("ZIP")
        for r in rd:
            z = r[zi].strip()[:5]
            if z.isdigit():
                ein2zip[r[ei].strip().zfill(9)] = z
    return ein2zip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    z2m = load_crosswalk()
    print(f"crosswalk ZIPs: {len(z2m):,}")
    ein2zip = load_bmf_zip()
    print(f"bmf EIN->zip: {len(ein2zip):,}")

    db = sqlite3.connect(DB, timeout=60)
    cols = [r[1] for r in db.execute("PRAGMA table_info(registry_enriched)")]
    if "metro" not in cols:
        if args.dry_run:
            print("[dry-run] would ALTER TABLE add column metro")
        else:
            db.execute("ALTER TABLE registry_enriched ADD COLUMN metro TEXT")
            db.commit()
            print("added column metro")

    rows = db.execute(
        "SELECT EIN, zipcode FROM registry_enriched "
        "WHERE deductibility=1 AND org_status='active'"
    ).fetchall()

    updates = []
    via_reg = via_bmf = 0
    for ein, zc in rows:
        z = str(zc).strip()[:5] if zc else ""
        metro = None
        if z.isdigit() and z in z2m:
            metro = z2m[z]; via_reg += 1
        else:
            bz = ein2zip.get(str(ein).zfill(9), "")
            if bz in z2m:
                metro = z2m[bz]; via_bmf += 1
        if metro:
            updates.append((metro, ein))

    print(f"orgs with metro: {len(updates):,} "
          f"(reg-zip {via_reg:,} + bmf-backfill {via_bmf:,}) of {len(rows):,}")

    if args.dry_run:
        print("[dry-run] no writes")
        db.close()
        return

    db.executemany("UPDATE registry_enriched SET metro=? WHERE EIN=?", updates)
    db.commit()
    db.close()
    print(f"wrote metro for {len(updates):,} orgs")


if __name__ == "__main__":
    sys.exit(main())
