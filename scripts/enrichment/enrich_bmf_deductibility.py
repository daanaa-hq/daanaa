#!/usr/bin/env python3
"""
scripts/enrich_bmf_deductibility.py
Populate deductibility and subsection columns in registry_enriched
from the IRS Business Master File (BMF).

Deductibility codes:
  1 = Tax deductible (public charity)
  2 = NOT deductible
  4 = Deductible under private foundation rules (50% limit)
  0 = Unknown

Subsection codes: 3 = 501(c)(3), 4 = 501(c)(4), 6 = 501(c)(6), etc.

Run after BMF download. Safe to re-run.
"""

import sqlite3, csv, time
from pathlib import Path

DB_PATH  = Path.home() / "meritgiving" / "data" / "merit_registry.db"
BMF_PATH = Path.home() / "meritgiving" / "data" / "bmf" / "2026-04-BMF.csv"


def run():
    print("Loading BMF...")
    t0 = time.time()
    bmf = {}
    with open(BMF_PATH, newline='', encoding='utf-8', errors='replace') as f:
        for row in csv.DictReader(f):
            ein = row.get('EIN', '').strip().zfill(9)
            if ein:
                bmf[ein] = {
                    'deductibility': row.get('DEDUCTIBILITY', '').strip(),
                    'subsection':    row.get('SUBSECTION', '').strip(),
                }
    print(f"  {len(bmf):,} BMF entries loaded in {time.time()-t0:.1f}s")

    db = sqlite3.connect(DB_PATH, timeout=120)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")

    existing = {r[1] for r in db.execute("PRAGMA table_info(registry_enriched)").fetchall()}
    for col in ("deductibility", "subsection"):
        if col not in existing:
            db.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col} TEXT")
            print(f"  Added column: {col}")
    db.commit()

    total = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    print(f"  {total:,} orgs in registry_enriched\n")

    updates = []
    not_in_bmf = 0
    for (ein,) in db.execute("SELECT EIN FROM registry_enriched").fetchall():
        if ein in bmf:
            updates.append((bmf[ein]['deductibility'], bmf[ein]['subsection'], ein))
        else:
            updates.append(('0', '', ein))
            not_in_bmf += 1

    print(f"Updating {len(updates):,} rows ({not_in_bmf:,} not in BMF → code 0)...")
    db.executemany(
        "UPDATE registry_enriched SET deductibility = ?, subsection = ? WHERE EIN = ?",
        updates
    )
    db.commit()

    # Report
    print("\nDeductibility breakdown:")
    for code, label in [('1','Deductible'), ('4','Private foundation'), ('2','NOT deductible'), ('0','Unknown')]:
        n = db.execute(
            "SELECT COUNT(*) FROM registry_enriched WHERE deductibility = ?", (code,)
        ).fetchone()[0]
        flag = ' ← WILL BE FILTERED OUT' if code == '2' else ''
        print(f"  Code {code} ({label}): {n:>8,}{flag}")

    print("\nSubsection breakdown (top 5):")
    for sub, cnt in db.execute("""
        SELECT subsection, COUNT(*) FROM registry_enriched
        GROUP BY subsection ORDER BY COUNT(*) DESC LIMIT 6
    """).fetchall():
        label = '← donors only' if sub == '3' else ''
        print(f"  501(c)({sub or '?'}): {cnt:>8,}  {label}")

    db.close()
    print("\nDone.")


if __name__ == "__main__":
    run()
