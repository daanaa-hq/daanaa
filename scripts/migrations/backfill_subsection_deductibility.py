#!/usr/bin/env python3
"""
Backfill subsection and deductibility from the IRS BMF for all orgs
where bmf_present = 1.

The BMF is the authoritative source for subsection (501(c)(X)) and
deductibility status. NCCS data, which populated many of these columns
originally, can be stale or misclassified. This script overwrites the
DB values with the BMF truth for every org that appears in the BMF.

Run after any BMF refresh, or as a one-time correctness fix.
"""

import sqlite3
import csv
import os
import sys

DB_PATH = os.environ.get("MERIT_DB_PATH", "/home/akbar/meritgiving/data/merit_registry.db")
BMF_PATH = os.environ.get("MERIT_BMF_PATH", "/home/akbar/meritgiving/data/bmf.csv")


def run():
    print("Loading BMF...")
    bmf = {}
    with open(BMF_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            ein = row["EIN"].strip()
            sub_raw = row["SUBSECTION"].strip()
            # BMF uses 2-digit codes (03, 06, etc.); strip leading zero for DB format
            sub = sub_raw.lstrip("0") or "0"
            ded = row["DEDUCTIBILITY"].strip()
            bmf[ein] = (sub, ded)
    print(f"  BMF rows: {len(bmf):,}")

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")

    # Fetch all orgs that have a BMF record
    rows = db.execute(
        "SELECT EIN, subsection, deductibility FROM registry_enriched WHERE bmf_present = 1"
    ).fetchall()
    print(f"  DB orgs with bmf_present=1: {len(rows):,}")

    updates = []
    for ein, db_sub, db_ded in rows:
        if ein not in bmf:
            continue
        bmf_sub, bmf_ded = bmf[ein]
        if bmf_sub != str(db_sub) or bmf_ded != str(db_ded):
            updates.append((bmf_sub, bmf_ded, ein))

    print(f"  Orgs requiring update: {len(updates):,}")

    if not updates:
        print("Nothing to update.")
        return

    # Preview what changed
    from collections import Counter
    sub_changes = Counter()
    for new_sub, new_ded, ein in updates:
        sub_changes[new_sub] += 1
    print("  New subsection distribution (top 10):")
    for sub, cnt in sub_changes.most_common(10):
        label = {
            "3": "501(c)(3) public charity",
            "4": "501(c)(4) social welfare",
            "5": "501(c)(5) labor/ag",
            "6": "501(c)(6) chamber/business",
            "7": "501(c)(7) social club",
            "8": "501(c)(8) fraternal",
            "2": "501(c)(2) title holding",
            "13": "501(c)(13) cemetery",
            "19": "501(c)(19) veterans",
        }.get(sub, f"501(c)({sub})")
        print(f"    {sub} ({label}): {cnt:,}")

    print("\nApplying updates...")
    db.executemany(
        "UPDATE registry_enriched SET subsection = ?, deductibility = ? WHERE EIN = ?",
        updates,
    )
    db.commit()
    print(f"  Done. {len(updates):,} rows updated.")

    # Verify the flagged org
    row = db.execute(
        "SELECT EIN, organization_name, subsection, deductibility FROM registry_enriched WHERE EIN = '453727138'"
    ).fetchone()
    if row:
        print(f"\nVerification — 453727138: {row[1]}")
        print(f"  subsection={row[2]}, deductibility={row[3]}")

    # New active 501(c)(3) deductible count
    count = db.execute(
        "SELECT COUNT(*) FROM registry_enriched "
        "WHERE subsection = '3' AND deductibility = '1' "
        "AND COALESCE(irs_revoked, 0) != 1 "
        "AND COALESCE(org_status, '') != 'revoked'"
    ).fetchone()[0]
    print(f"\nNew active deductible 501(c)(3) count: {count:,}")
    db.close()


if __name__ == "__main__":
    run()
