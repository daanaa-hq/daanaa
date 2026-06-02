#!/usr/bin/env python3
"""Ingest the IRS Automatic Revocation of Exemption list into `revoked_eins`.

An org on this list has LOST its tax-exempt status. The API's G2 gate
(merit_api.py `_is_revoked`) reads this table to suppress any donate path for a
revoked org — a core "official sources only, fail closed" protection.

Official source (IRS bulk data downloads):
  https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads
The auto-revocation file is pipe-delimited. Columns (no header) are, in order:
  EIN | Legal Name | DBA | Address | City | State | ZIP | Country |
  Exemption Type | Revocation Date | Revocation Posting Date | Reinstatement Date

This script is source-agnostic: pass a local file you downloaded, or a URL.
It upserts revoked EINs and (importantly) REMOVES any EIN that has since been
reinstated, so a reinstated org regains its donate path.

Usage:
  python3 scripts/ingest_auto_revocation.py --file /path/to/revocation.txt
  python3 scripts/ingest_auto_revocation.py --url  https://.../data-download-revocation.zip
  python3 scripts/ingest_auto_revocation.py --file revocation.txt --dry-run
"""
from __future__ import annotations

import argparse
import io
import os
import sqlite3
import sys
import zipfile

DB_PATH = os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/merit_registry.db"))


def _rows_from_text(text: str):
    """Yield (ein, revocation_date, posting_date, reinstated) per data line."""
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) < 11:
            continue
        ein = "".join(c for c in parts[0] if c.isdigit())[:10]
        if len(ein) < 9:
            continue
        rev_date = parts[9].strip() if len(parts) > 9 else ""
        post_date = parts[10].strip() if len(parts) > 10 else ""
        reinstated = parts[11].strip() if len(parts) > 11 else ""
        yield ein, rev_date, post_date, reinstated


def _load_text(file: str | None, url: str | None) -> str:
    if file:
        data = open(file, "rb").read()
    elif url:
        import urllib.request
        with urllib.request.urlopen(url, timeout=120) as r:  # noqa: S310 (trusted IRS URL)
            data = r.read()
    else:
        raise SystemExit("Provide --file or --url")
    # Handle a zip (the IRS download is zipped) transparently.
    if data[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(data))
        name = next((n for n in zf.namelist() if not n.endswith("/")), None)
        if not name:
            raise SystemExit("Empty zip")
        data = zf.read(name)
    return data.decode("latin-1", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--url")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    text = _load_text(args.file, args.url)

    revoked, reinstated = {}, set()
    for ein, rev_date, post_date, reinst in _rows_from_text(text):
        if reinst:
            reinstated.add(ein)
        else:
            revoked[ein] = (rev_date, post_date)

    print(f"Parsed: {len(revoked):,} revoked, {len(reinstated):,} reinstated")
    if args.dry_run:
        sample = list(revoked.items())[:5]
        print("Sample:", sample)
        return

    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS revoked_eins (
            ein TEXT PRIMARY KEY, revocation_date TEXT,
            revocation_posting_date TEXT, source TEXT DEFAULT 'irs_auto_revocation')
    """)
    db.executemany(
        "INSERT INTO revoked_eins (ein, revocation_date, revocation_posting_date) "
        "VALUES (?, ?, ?) ON CONFLICT(ein) DO UPDATE SET "
        "revocation_date=excluded.revocation_date, "
        "revocation_posting_date=excluded.revocation_posting_date",
        [(e, d[0], d[1]) for e, d in revoked.items()],
    )
    # Reinstated orgs regain their donate path.
    if reinstated:
        db.executemany("DELETE FROM revoked_eins WHERE ein = ?", [(e,) for e in reinstated])
    db.commit()
    total = db.execute("SELECT COUNT(*) FROM revoked_eins").fetchone()[0]
    db.close()
    print(f"revoked_eins now holds {total:,} EINs")


if __name__ == "__main__":
    main()
