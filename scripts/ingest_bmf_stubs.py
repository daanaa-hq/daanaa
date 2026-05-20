#!/usr/bin/env python3
"""
scripts/ingest_bmf_stubs.py

Load 501(c)(3) stub records from the IRS BMF into registry_enriched.
Only inserts EINs not already in the DB — existing rows are never touched.

Stubs contain: name, state, city, address, zip, ruling date, deductibility,
foundation code, accounting period, and source='bmf_stub'.  No financials,
no NTEE code, no score — those get filled in lazily by later pipeline stages.

Usage:
    python3 scripts/ingest_bmf_stubs.py
    python3 scripts/ingest_bmf_stubs.py --dry-run
    python3 scripts/ingest_bmf_stubs.py --bmf /path/to/BMF.csv
    python3 scripts/ingest_bmf_stubs.py --active-only   # skip STATUS!=1
    python3 scripts/ingest_bmf_stubs.py --batch 1000
"""

import sqlite3, csv, time, argparse
from pathlib import Path
from datetime import datetime, timezone

DB_PATH  = Path.home() / "meritgiving" / "data" / "merit_registry.db"
BMF_PATH = Path.home() / "meritgiving" / "data" / "bmf" / "2026-04-BMF.csv"

# BMF STATUS codes: 1=unconditional exemption, 2=conditional
# 12=terminated, 25=revoked — skip those
ACTIVE_STATUSES = {"1", "2"}


def fmt_ruling(raw: str) -> str | None:
    """'202601' → '2026-01'  (YYYYMM → YYYY-MM)"""
    raw = raw.strip()
    if len(raw) == 6 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:]}"
    return raw or None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bmf", default=str(BMF_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--active-only", action="store_true",
                        help="Skip orgs with BMF STATUS != 1 or 2")
    parser.add_argument("--batch", type=int, default=500,
                        help="Rows per INSERT batch (default 500)")
    args = parser.parse_args()

    bmf_path = Path(args.bmf)
    if not bmf_path.exists():
        raise SystemExit(f"BMF file not found: {bmf_path}")

    db = sqlite3.connect(DB_PATH, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")

    # Load existing EINs once — fast membership test
    print("Loading existing EINs …", flush=True)
    existing = {r[0] for r in db.execute("SELECT EIN FROM registry_enriched")}
    print(f"  {len(existing):,} EINs already in DB", flush=True)

    now_iso = datetime.now(timezone.utc).isoformat()

    batch: list[tuple] = []
    total_read = 0
    total_skipped_existing = 0
    total_skipped_status = 0
    total_skipped_subsection = 0
    total_inserted = 0
    t0 = time.time()

    def flush_batch():
        nonlocal total_inserted
        if not batch:
            return
        db.executemany(
            """INSERT OR IGNORE INTO registry_enriched
               (EIN, organization_name, STATE, CITY, address, zipcode,
                ruling_date, deductibility, foundation_code, accounting_period,
                subsection, source, data_source, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            batch,
        )
        db.commit()
        total_inserted += len(batch)
        batch.clear()

    print(f"Streaming {bmf_path.name} …", flush=True)
    with open(bmf_path, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_read += 1

            sub = row.get("SUBSECTION", "").strip()
            if sub != "3":
                total_skipped_subsection += 1
                continue

            status = row.get("STATUS", "").strip()
            if args.active_only and status not in ACTIVE_STATUSES:
                total_skipped_status += 1
                continue

            ein = row.get("EIN", "").strip()
            if not ein:
                continue

            if ein in existing:
                total_skipped_existing += 1
                continue

            # Map BMF fields → stub row
            batch.append((
                ein,
                (row.get("NAME") or "").strip() or None,
                (row.get("STATE") or "").strip() or None,
                (row.get("CITY") or "").strip() or None,
                (row.get("STREET") or "").strip() or None,
                (row.get("ZIP") or "").strip()[:10] or None,
                fmt_ruling(row.get("RULING", "")),
                (row.get("DEDUCTIBILITY") or "").strip() or None,
                (row.get("FOUNDATION") or "").strip() or None,
                (row.get("ACCT_PD") or "").strip() or None,
                "3",          # subsection — always 501c3 here
                "bmf_stub",   # source
                "bmf",        # data_source
                now_iso,
            ))
            existing.add(ein)  # prevent dupe within same run

            if len(batch) >= args.batch:
                if not args.dry_run:
                    flush_batch()
                else:
                    batch.clear()
                    total_inserted += args.batch  # dry-run counter

            if total_read % 100_000 == 0:
                elapsed = time.time() - t0
                rate = total_read / elapsed
                print(
                    f"  {total_read:>9,} read  "
                    f"{total_inserted:>9,} inserted  "
                    f"{elapsed:.0f}s  ({rate:.0f} rows/s)",
                    flush=True,
                )

    # Final flush
    if not args.dry_run:
        flush_batch()

    elapsed = time.time() - t0
    print(f"\n[done] {elapsed:.0f}s")
    print(f"  BMF rows read:        {total_read:,}")
    print(f"  non-501c3 skipped:    {total_skipped_subsection:,}")
    print(f"  already in DB:        {total_skipped_existing:,}")
    if args.active_only:
        print(f"  inactive/revoked:     {total_skipped_status:,}")
    print(f"  stubs inserted:       {total_inserted:,}")
    if args.dry_run:
        print("  [dry-run — no writes]")
    else:
        new_total = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
        print(f"  DB total now:         {new_total:,}")


if __name__ == "__main__":
    main()
