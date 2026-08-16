#!/usr/bin/env python3
"""
Second-pass: add orgs from bmf.csv that are NOT already in registry_enriched.
These are 501(c)(3) orgs in the IRS data with no precomputed enrichment.
Only imports SUBSECTION=3 (501c3), DEDUCTIBILITY=1 orgs.
Inserts with INSERT OR IGNORE so precomputed orgs are never overwritten.
"""
import csv, sqlite3, sys, time
from pathlib import Path
from datetime import datetime

BMF_CSV = Path("data/bmf.csv")
DB_PATH  = Path("data/merit_registry.db")
BATCH    = 10_000


def commit_batch(con, rows, retries=40, base=0.5):
    """executemany + commit, retrying on transient 'database is locked'.

    The live DB has many concurrent writers (web_finder, reembed, cause_tags,
    auto_ingest). WAL allows one writer at a time, so a bulk insert must wait
    its turn — busy_timeout alone proved insufficient under heavy contention,
    so we retry the whole batch with capped exponential backoff.
    """
    for attempt in range(retries):
        try:
            con.executemany(INSERT_SQL, rows)
            con.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" not in str(e).lower() or attempt == retries - 1:
                raise
            time.sleep(min(base * (2 ** attempt), 10.0))

INSERT_SQL = """
INSERT OR IGNORE INTO registry_enriched (
    EIN, organization_name, NTEE1, NTEECC, STATE, CITY,
    subsection, deductibility, ruling_date, zipcode, source
) VALUES (?, ?, ?, ?, ?, ?, '3', '1', ?, ?, 'IRS_BMF')
"""


def ntee1(code):
    return code[0].upper() if code and code[0].isalpha() else None


def main():
    print(f"[{datetime.now():%H:%M:%S}] Adding BMF-only orgs to registry_enriched...")
    before = sqlite3.connect(DB_PATH).execute(
        "SELECT COUNT(*) FROM registry_enriched"
    ).fetchone()[0]
    print(f"  DB before: {before:,} orgs")

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA cache_size=-64000")
    # Wait for the write lock instead of failing instantly — overnight writers
    # (web_finder UPDATEs, reembed, cause_tags) hold the single WAL writer slot.
    con.execute("PRAGMA busy_timeout=120000")

    inserted = 0
    skipped = 0
    batch = []

    with open(BMF_CSV, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if row.get("SUBSECTION", "").strip() != "03":
                skipped += 1
                continue
            if row.get("DEDUCTIBILITY", "").strip() != "1":
                skipped += 1
                continue

            ein   = (row.get("EIN") or "").strip().zfill(9)
            name  = (row.get("NAME") or "").strip()[:200]
            ntee  = (row.get("NTEE_CD") or "").strip()[:10]
            state = (row.get("STATE") or "").strip().upper()[:2]
            city  = (row.get("CITY") or "").strip()[:100]
            ruling = (row.get("RULING") or "").strip()[:8]
            zipcode = (row.get("ZIP") or "").strip()[:10]

            if not ein or not name:
                skipped += 1
                continue

            batch.append((
                ein, name, ntee1(ntee), ntee or None, state, city, ruling, zipcode
            ))

            if len(batch) >= BATCH:
                commit_batch(con, batch)
                inserted += len(batch)
                batch = []

            if (i + 1) % 500_000 == 0:
                print(f"  [{datetime.now():%H:%M:%S}] {i+1:,} rows read | inserted: {inserted:,}", flush=True)

    if batch:
        commit_batch(con, batch)
        inserted += len(batch)

    after = con.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    con.close()

    print(f"\n[{datetime.now():%H:%M:%S}] Done!")
    print(f"  New orgs added: {after - before:,}")
    print(f"  Total in DB: {after:,}")
    print(f"  Skipped (non-501c3 or no deductibility): {skipped:,}")
    print(f"\nNext step: python3 scripts/build_fts_index.py")


if __name__ == "__main__":
    main()
