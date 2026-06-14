#!/usr/bin/env python3
"""
Import US zip code reference data into merit_registry.db.

Source: GeoNames postal code database (public domain, CC0)
https://download.geonames.org/export/zip/US.zip

Columns (tab-separated):
  country_code, postal_code, place_name, admin_name1 (state), admin_code1 (state abbr),
  admin_name2 (county), admin_code2 (county fips), admin_name3, admin_code3,
  latitude, longitude, accuracy

Run once:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/import_zip_codes.py

Safe to re-run (INSERT OR REPLACE). ~42K rows, ~15 seconds.
"""

import io
import os
import sqlite3
import sys
import zipfile

import requests

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'merit_registry.db')
GEONAMES_URL = 'https://download.geonames.org/export/zip/US.zip'


def fetch_geonames() -> list[tuple]:
    print('Downloading GeoNames US postal codes (public domain)…')
    r = requests.get(GEONAMES_URL, timeout=120, stream=True)
    r.raise_for_status()

    content = b''
    total = 0
    for chunk in r.iter_content(chunk_size=65536):
        content += chunk
        total += len(chunk)
        if total % (1024 * 1024) == 0:
            print(f'  {total // 1024 // 1024} MB downloaded…', end='\r')
    print(f'  {total // 1024} KB downloaded')

    rows = []
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        # GeoNames zip contains US.txt
        txt_name = next((n for n in z.namelist() if n.endswith('.txt') and not n.startswith('readme')), None)
        if not txt_name:
            raise RuntimeError(f'Unexpected zip contents: {z.namelist()}')
        with z.open(txt_name) as f:
            for line in io.TextIOWrapper(f, encoding='utf-8'):
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 11:
                    continue
                # country_code=0, postal_code=1, place_name=2, admin_name1=3, admin_code1=4,
                # admin_name2=5, admin_code2=6, lat=9, lon=10
                country = parts[0]
                if country != 'US':
                    continue
                zip_code   = parts[1].strip().zfill(5)
                city       = parts[2].strip()
                state_name = parts[3].strip()
                state_id   = parts[4].strip().upper()
                county     = parts[5].strip()
                county_fips= parts[6].strip()
                try:
                    lat = float(parts[9]) if parts[9] else None
                    lon = float(parts[10]) if parts[10] else None
                except ValueError:
                    lat = lon = None
                rows.append((zip_code, city, state_id, state_name, county, county_fips, lat, lon))

    print(f'  Parsed {len(rows):,} US zip codes')
    return rows


def import_rows(db_path: str, rows: list[tuple]) -> int:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS zip_codes (
            zip         TEXT PRIMARY KEY,
            city        TEXT,
            state_id    TEXT,
            state_name  TEXT,
            county_name TEXT,
            county_fips TEXT,
            lat         REAL,
            lon         REAL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_zip_state ON zip_codes(state_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_zip_county ON zip_codes(county_name, state_id)")

    inserted = 0
    batch = []
    for row in rows:
        if not row[0] or len(row[0]) != 5 or not row[0].isdigit():
            continue
        batch.append(row)
        if len(batch) >= 1000:
            conn.executemany(
                "INSERT OR REPLACE INTO zip_codes "
                "(zip, city, state_id, state_name, county_name, county_fips, lat, lon) "
                "VALUES (?,?,?,?,?,?,?,?)",
                batch
            )
            inserted += len(batch)
            batch = []
    if batch:
        conn.executemany(
            "INSERT OR REPLACE INTO zip_codes "
            "(zip, city, state_id, state_name, county_name, county_fips, lat, lon) "
            "VALUES (?,?,?,?,?,?,?,?)",
            batch
        )
        inserted += len(batch)
    conn.commit()
    conn.close()
    return inserted


def main():
    if not os.path.exists(DB_PATH):
        print(f'ERROR: database not found at {DB_PATH}')
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        count = conn.execute("SELECT COUNT(*) FROM zip_codes WHERE city IS NOT NULL AND city != ''").fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    conn.close()

    if count > 30000 and '--force' not in sys.argv:
        print(f'zip_codes already populated ({count:,} rows). Use --force to reimport.')
        return

    rows = fetch_geonames()
    print(f'Importing {len(rows):,} rows into {DB_PATH}…')
    inserted = import_rows(DB_PATH, rows)
    print(f'Done. {inserted:,} rows imported.')

    conn = sqlite3.connect(DB_PATH)
    spot = conn.execute(
        "SELECT zip, city, state_id, county_name FROM zip_codes "
        "WHERE zip IN ('60614','10001','90210','77001') ORDER BY zip"
    ).fetchall()
    conn.close()
    print('\nSpot check:')
    for row in spot:
        print(f'  {row}')


if __name__ == '__main__':
    main()
