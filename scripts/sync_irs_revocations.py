#!/usr/bin/env python3
"""
sync_irs_revocations.py — download and load the IRS automatic-revocation list.

The IRS publishes a full CSV of every organization whose 501(c)(3) status was
automatically revoked (for failure to file for 3+ consecutive years). The file
is updated roughly monthly and is ~40 MB uncompressed.

Source: https://apps.irs.gov/pub/epostcard/data-download-revocation.zip

Run modes:
  python3 sync_irs_revocations.py            # download + load + report
  python3 sync_irs_revocations.py --check    # daily check only, no download
  python3 sync_irs_revocations.py --force    # re-download even if cache is fresh
"""

import csv
import io
import sqlite3
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB     = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG    = Path.home() / 'meritgiving' / 'logs' / 'irs_revocations.log'
CACHE  = Path.home() / 'meritgiving' / 'data' / 'irs_revocation_cache.csv'
STAMP  = Path.home() / 'meritgiving' / 'data' / 'irs_revocation_last_sync.txt'

# IRS auto-revocation list (full replacement file, ~40 MB)
IRS_URL = 'https://apps.irs.gov/pub/epostcard/data-download-revocation.zip'

# Re-download if cache is older than this many days
REFRESH_DAYS = 28

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, 'a') as fh:
        fh.write(line + '\n')

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def cache_is_fresh() -> bool:
    if not CACHE.exists() or not STAMP.exists():
        return False
    try:
        last = datetime.fromisoformat(STAMP.read_text().strip())
        return datetime.now() - last < timedelta(days=REFRESH_DAYS)
    except Exception:
        return False

def download_revocation_list() -> None:
    log(f'Downloading IRS revocation list from {IRS_URL}')
    resp = requests.get(IRS_URL, timeout=120, stream=True)
    resp.raise_for_status()

    raw = b''.join(resp.iter_content(chunk_size=1 << 16))
    log(f'Downloaded {len(raw):,} bytes')

    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = zf.namelist()
        csv_name = next((n for n in names if n.lower().endswith('.csv')), names[0])
        log(f'Extracting {csv_name}')
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_bytes(zf.read(csv_name))

    STAMP.write_text(datetime.now().isoformat())
    log(f'Cache written to {CACHE} ({CACHE.stat().st_size:,} bytes)')

# ---------------------------------------------------------------------------
# Load into DB
# ---------------------------------------------------------------------------

def load_into_db() -> dict:
    log('Loading revocation list into revoked_eins table')
    con = sqlite3.connect(str(DB))
    cur = con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS revoked_eins (
            ein                     TEXT PRIMARY KEY,
            revocation_date         TEXT,
            revocation_posting_date TEXT,
            source                  TEXT DEFAULT 'irs_auto_revocation'
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS irs_sync_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            synced_at     TEXT NOT NULL,
            rows_loaded   INTEGER,
            matched_orgs  INTEGER,
            source        TEXT
        )
    ''')
    con.commit()

    inserted = 0
    updated  = 0
    skipped  = 0

    with open(CACHE, newline='', encoding='utf-8-sig', errors='replace') as fh:
        # IRS auto-revocation file is pipe-delimited with NO header row.
        # Column layout (as published):
        #   0  EIN
        #   1  Organization Name
        #   2  Organization Name 2
        #   3  Street Address
        #   4  City
        #   5  State
        #   6  Zip
        #   7  Country
        #   8  Exemption Type
        #   9  Revocation Date
        #  10  Revocation Posting Date
        reader = csv.reader(fh, delimiter='|')

        batch = []
        for row in reader:
            if len(row) < 1:
                continue
            ein_raw = row[0].strip().replace('-', '')
            if not ein_raw.isdigit():
                skipped += 1
                continue
            ein = ein_raw.zfill(9)

            rev_date  = row[9].strip()  if len(row) > 9  else None
            post_date = row[10].strip() if len(row) > 10 else None

            batch.append((ein, rev_date, post_date))

            if len(batch) >= 10_000:
                cur.executemany(
                    'INSERT OR REPLACE INTO revoked_eins (ein, revocation_date, revocation_posting_date) VALUES (?,?,?)',
                    batch,
                )
                inserted += len(batch)
                batch = []

        if batch:
            cur.executemany(
                'INSERT OR REPLACE INTO revoked_eins (ein, revocation_date, revocation_posting_date) VALUES (?,?,?)',
                batch,
            )
            inserted += len(batch)

    con.commit()

    # Count how many of our indexed orgs are revoked
    cur.execute('''
        SELECT COUNT(*) FROM registry_enriched re
        JOIN revoked_eins rv ON re.EIN = rv.ein
    ''')
    matched = cur.fetchone()[0]

    # Write sync log
    cur.execute(
        'INSERT INTO irs_sync_log (synced_at, rows_loaded, matched_orgs, source) VALUES (?,?,?,?)',
        (datetime.now().isoformat(), inserted, matched, 'irs_auto_revocation'),
    )
    con.commit()
    con.close()

    return {'rows_loaded': inserted, 'matched_orgs': matched}

# ---------------------------------------------------------------------------
# Daily check (fast, no download)
# ---------------------------------------------------------------------------

def daily_check() -> None:
    """Log counts only — called by the nightly pipeline to surface any drift."""
    con = sqlite3.connect(str(DB))
    cur = con.cursor()
    try:
        cur.execute('SELECT COUNT(*) FROM revoked_eins')
        total = cur.fetchone()[0]
        cur.execute('''
            SELECT COUNT(*) FROM registry_enriched re
            JOIN revoked_eins rv ON re.EIN = rv.ein
        ''')
        matched = cur.fetchone()[0]
        last = STAMP.read_text().strip() if STAMP.exists() else 'never'
        log(f'Daily check: {total:,} revoked EINs loaded, {matched:,} match our index, last sync {last}')
    except Exception as e:
        log(f'Daily check error: {e}')
    finally:
        con.close()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = set(sys.argv[1:])
    check_only = '--check' in args
    force      = '--force' in args

    if check_only:
        daily_check()
        return

    if force or not cache_is_fresh():
        download_revocation_list()
    else:
        last = STAMP.read_text().strip()
        log(f'Cache is fresh (last sync: {last}). Use --force to re-download.')

    result = load_into_db()
    if 'error' not in result:
        log(f"Loaded {result['rows_loaded']:,} revoked EINs — {result['matched_orgs']:,} match our index")
    else:
        log(f"Load failed: {result['error']}")
        sys.exit(1)

if __name__ == '__main__':
    main()
