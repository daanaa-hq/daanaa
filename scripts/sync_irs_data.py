#!/usr/bin/env python3
"""
sync_irs_data.py — weekly IRS Exempt Organizations BMF refresh + delta load.

Downloads the four regional IRS EO Business Master File extracts, combines
them into data/bmf.csv, then delta-loads organizations not already in
registry_enriched (INSERT OR IGNORE — existing enrichment is never touched,
same contract as import_bmf_orgs.py). New orgs are also inserted into the
org_fts search index so they are searchable immediately instead of waiting
for Saturday's full rebuild.

Only 501(c)(3) (SUBSECTION=03), DEDUCTIBILITY=1 orgs are imported.

Run modes:
  python3 sync_irs_data.py                 # download + delta load
  python3 sync_irs_data.py --mode delta    # same (default)
  python3 sync_irs_data.py --skip-download # delta load from existing bmf.csv
"""

import argparse
import csv
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

REPO = Path.home() / "meritgiving"
DB_PATH = REPO / "data" / "merit_registry.db"
BMF_CSV = REPO / "data" / "bmf.csv"
BMF_TMP = REPO / "data" / "bmf.csv.download"
LOG_FILE = REPO / "logs" / "irs_refresh.log"

# IRS EO BMF regional extracts (full replacement files, updated ~monthly)
IRS_URLS = [
    "https://www.irs.gov/pub/irs-soi/eo1.csv",
    "https://www.irs.gov/pub/irs-soi/eo2.csv",
    "https://www.irs.gov/pub/irs-soi/eo3.csv",
    "https://www.irs.gov/pub/irs-soi/eo4.csv",
]

BATCH = 10_000

INSERT_SQL = """
INSERT OR IGNORE INTO registry_enriched (
    EIN, organization_name, NTEE1, NTEECC, STATE, CITY,
    subsection, deductibility, ruling_date, zipcode, source
) VALUES (?, ?, ?, ?, ?, ?, '3', '1', ?, ?, 'IRS_BMF')
"""

FTS_INSERT_SQL = """
INSERT INTO org_fts (ein, merit_tier, org_name, mission, city, state, metro, category, cause_tags)
SELECT
    EIN, COALESCE(merit_tier, 'Spark'), organization_name, COALESCE(mission, ''),
    COALESCE(CITY, ''), COALESCE(STATE, ''), COALESCE(metro, ''), NTEECC,
    COALESCE(cause_tags, '{}')
FROM registry_enriched
WHERE EIN = ? AND organization_name IS NOT NULL AND org_status = 'active'
"""


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as fh:
        fh.write(line + "\n")


def download_bmf() -> bool:
    """Download all four regional files, combine into BMF_TMP, atomically replace BMF_CSV."""
    header_written = False
    try:
        with open(BMF_TMP, "w", encoding="utf-8") as out:
            for url in IRS_URLS:
                log(f"Downloading {url}")
                resp = requests.get(url, timeout=300, stream=True)
                resp.raise_for_status()
                lines = resp.iter_lines(decode_unicode=True)
                header = next(lines, None)
                if header is None:
                    log(f"ERROR: empty response from {url}")
                    return False
                if not header_written:
                    out.write(header + "\n")
                    header_written = True
                count = 0
                for line in lines:
                    if line:
                        out.write(line + "\n")
                        count += 1
                log(f"  {count:,} rows from {url.rsplit('/', 1)[-1]}")
    except Exception as e:
        log(f"ERROR downloading IRS data: {e}")
        BMF_TMP.unlink(missing_ok=True)
        return False

    size_mb = BMF_TMP.stat().st_size / 1e6
    if size_mb < 100:  # full BMF is ~330 MB; anything tiny means a bad download
        log(f"ERROR: combined file only {size_mb:.0f} MB — refusing to replace bmf.csv")
        BMF_TMP.unlink(missing_ok=True)
        return False

    BMF_TMP.replace(BMF_CSV)
    log(f"bmf.csv replaced ({size_mb:.0f} MB)")
    return True


def commit_batch(con, rows, retries=40, base=0.5):
    """executemany + commit, retrying on transient 'database is locked'."""
    for attempt in range(retries):
        try:
            con.executemany(INSERT_SQL, rows)
            con.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" not in str(e).lower() or attempt == retries - 1:
                raise
            time.sleep(min(base * (2**attempt), 10.0))


def ntee1(code):
    return code[0].upper() if code and code[0].isalpha() else None


def delta_load() -> int:
    """Insert BMF orgs not already in registry_enriched. Returns count added."""
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA busy_timeout=120000")

    before = con.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    existing = {row[0] for row in con.execute("SELECT EIN FROM registry_enriched")}
    log(f"Registry before: {before:,} orgs")

    new_eins = []
    batch = []
    skipped = 0

    with open(BMF_CSV, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("SUBSECTION", "").strip() != "03":
                skipped += 1
                continue
            if row.get("DEDUCTIBILITY", "").strip() != "1":
                skipped += 1
                continue

            ein = (row.get("EIN") or "").strip().zfill(9)
            name = (row.get("NAME") or "").strip()[:200]
            if not ein or not name or ein in existing:
                skipped += 1
                continue

            ntee = (row.get("NTEE_CD") or "").strip()[:10]
            batch.append((
                ein, name, ntee1(ntee), ntee or None,
                (row.get("STATE") or "").strip().upper()[:2],
                (row.get("CITY") or "").strip()[:100],
                (row.get("RULING") or "").strip()[:8],
                (row.get("ZIP") or "").strip()[:10],
            ))
            new_eins.append(ein)

            if len(batch) >= BATCH:
                commit_batch(con, batch)
                batch = []

    if batch:
        commit_batch(con, batch)

    after = con.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    added = after - before
    log(f"Registry after: {after:,} orgs (+{added:,} new)")

    # Mark any new org that is already on the IRS revocation list BEFORE the
    # FTS insert below, so revoked orgs never enter the search index
    # (fail-closed: the BMF can lag the revocation list).
    try:
        cur = con.execute("""
            UPDATE registry_enriched
            SET irs_revoked = 1, org_status = 'revoked'
            WHERE source = 'IRS_BMF' AND COALESCE(org_status, 'active') = 'active'
              AND EXISTS (SELECT 1 FROM revoked_eins v WHERE v.ein = registry_enriched.EIN)
        """)
        con.commit()
        if cur.rowcount:
            log(f"Revocation guard: {cur.rowcount:,} new orgs already revoked — excluded from search")
    except sqlite3.OperationalError as e:
        log(f"Revocation guard skipped (revoked_eins table unavailable): {e}")

    # Make new orgs searchable now instead of waiting for Saturday's FTS rebuild
    if added > 0:
        fts_added = 0
        for ein in new_eins:
            try:
                cur = con.execute(FTS_INSERT_SQL, (ein,))
                fts_added += cur.rowcount if cur.rowcount > 0 else 0
                if fts_added % BATCH == 0:
                    con.commit()
            except sqlite3.OperationalError as e:
                log(f"FTS insert warning for {ein}: {e}")
                break
        con.commit()
        log(f"FTS index: {fts_added:,} new orgs added incrementally")

    con.close()
    return added


def main():
    parser = argparse.ArgumentParser(description="Weekly IRS EO data refresh")
    parser.add_argument("--mode", default="delta", choices=["delta"])
    parser.add_argument("--skip-download", action="store_true",
                        help="Delta-load from existing bmf.csv without downloading")
    parser.add_argument("--log-file", help="(accepted for compatibility; logging always goes to logs/irs_refresh.log)")
    args = parser.parse_args()

    log("Starting IRS EO data sync...")

    if not args.skip_download:
        if not download_bmf():
            sys.exit(1)
    else:
        log(f"Skipping download; using existing {BMF_CSV}")

    added = delta_load()
    log(f"IRS sync complete: {added:,} new organizations")


if __name__ == "__main__":
    main()
