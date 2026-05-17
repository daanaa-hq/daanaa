#!/usr/bin/env python3
"""
scripts/ingest_irs_soi_v2.py

Enhanced IRS SOI ingest — extracts the full value from all 12 zip files:
  1. Updates registry_enriched with net_assets, total_expenses, total_liabilities,
     months_of_reserve, employee_count for orgs missing ProPublica data
  2. Inserts rows into propublica_financials for multi-year history
     (same schema, soi_source='irs_soi')

Covers FY 2019–2024 × (990 + 990-EZ) = ~12 files.
~8M total rows across all files; most won't match registry_enriched.

Rules:
  - Never overwrite ProPublica data with SOI (ProPublica wins)
  - Among SOI years, newest wins for registry_enriched fields
  - propublica_financials: INSERT OR IGNORE (dedup by EIN + tax_prd_yr)
"""

import csv, io, sqlite3, zipfile, argparse
from pathlib import Path
from datetime import datetime, timezone

BASE    = Path.home() / "meritgiving"
SOI_DIR = BASE / "data" / "irs_soi"
DB_PATH = BASE / "data" / "merit_registry.db"
BATCH   = 3000

FILE_SPECS = [
    # Full 990 — richest data set
    {"pattern": "*eoextract990.zip",  "form": "990",
     "rev": "totrevenue", "assets": "totassetsend", "yr": "tax_pd",
     "netassets": "totnetassetend", "liab": "totliabend",
     "expns": "totfuncexpns", "empl": "noemplyeesw3cnt",
     "cntrbgfts": "totcntrbgfts", "prgmrev": "totprgmrevnue",
     "compofficer": "compnsatncurrofcr"},
    # 990-EZ (newer naming: 24eoextract990EZ.zip)
    {"pattern": "*eoextract990EZ.zip", "form": "990ez",
     "rev": "totrevnue", "assets": "totassetsend", "yr": "taxpd",
     "netassets": "totnetassetsend", "liab": "totliabend",
     "expns": "totexpns", "empl": None,
     "cntrbgfts": "totcntrbs", "prgmrev": "prgmservrev",
     "compofficer": None},
    # 990-EZ (older naming: 19eoextractez.zip … 23eoextractez.zip)
    {"pattern": "*eoextractez.zip",   "form": "990ez",
     "rev": "totrevnue", "assets": "totassetsend", "yr": "taxpd",
     "netassets": "totnetassetsend", "liab": "totliabend",
     "expns": "totexpns", "empl": None,
     "cntrbgfts": "totcntrbs", "prgmrev": "prgmservrev",
     "compofficer": None},
]


def parse_year(s):
    try:
        v = str(s).strip()
        return int(v[:4]) if len(v) >= 4 else 0
    except (ValueError, TypeError):
        return 0


def to_float(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(',', '').strip()) or None
    except (ValueError, TypeError):
        return None


def to_int(v):
    try:
        return int(str(v).strip()) or None
    except (ValueError, TypeError):
        return None


def ingest_file(db, zip_path, spec, existing_src, dry_run, now):
    """
    existing_src: dict {ein: (latest_tax_year, data_source)}
    Returns (rows_read, registry_updated, financials_inserted)
    """
    rows_read = reg_updated = fin_inserted = 0
    reg_batch  = []  # (net_assets, total_expenses, total_liabilities, months_of_reserve, employee_count, total_revenue, total_assets, latest_tax_year, now, ein)
    fin_batch  = []  # (EIN, yr, rev, expns, assets, liab, netassets, cntrbgfts, prgmrev, compofficer, None)

    def flush_all(force=False):
        nonlocal reg_updated, fin_inserted
        if not force and len(reg_batch) < BATCH and len(fin_batch) < BATCH:
            return
        if not dry_run:
            if reg_batch:
                db.executemany("""
                    UPDATE registry_enriched
                    SET net_assets        = CASE WHEN net_assets IS NULL THEN ? ELSE net_assets END,
                        total_expenses    = CASE WHEN total_expenses IS NULL THEN ? ELSE total_expenses END,
                        total_liabilities = CASE WHEN total_liabilities IS NULL THEN ? ELSE total_liabilities END,
                        months_of_reserve = CASE WHEN months_of_reserve IS NULL THEN ? ELSE months_of_reserve END,
                        employee_count    = CASE WHEN employee_count IS NULL AND ? IS NOT NULL THEN ? ELSE employee_count END,
                        total_revenue     = ?,
                        total_assets      = ?,
                        latest_tax_year   = ?,
                        data_source       = CASE WHEN data_source IS NULL OR data_source = '' THEN 'irs_soi' ELSE data_source END,
                        updated_at        = ?
                    WHERE EIN = ?
                """, reg_batch)
                reg_updated += len(reg_batch)
                reg_batch.clear()
            if fin_batch:
                db.executemany("""
                    INSERT OR IGNORE INTO propublica_financials
                        (EIN, tax_prd_yr, totrevenue, totfuncexpns, totassetsend,
                         totliabend, totnetassetend, totcntrbgfts, totprgmrevnue,
                         compnsatncurrofcr, pdf_url)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, fin_batch)
                fin_inserted += len(fin_batch)
                fin_batch.clear()
            db.commit()

    with zipfile.ZipFile(zip_path) as zf:
        inner = zf.namelist()[0]
        with zf.open(inner) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8', errors='replace'))
            for row in reader:
                rows_read += 1
                ein = str(row.get("EIN") or "").strip().zfill(9)[:9]
                if not ein or ein == "000000000":
                    continue

                tax_yr = parse_year(row.get(spec["yr"]) or "")
                if tax_yr < 2000:
                    continue

                if ein not in existing_src:
                    continue

                cur_yr, cur_src = existing_src[ein]

                # Multi-year financials: insert regardless (OR IGNORE deduplicates)
                rev       = to_float(row.get(spec["rev"]))
                expns     = to_float(row.get(spec["expns"]))
                assets    = to_float(row.get(spec["assets"]))
                liab      = to_float(row.get(spec["liab"]))
                netassets = to_float(row.get(spec["netassets"]))
                cntrbgfts = to_float(row.get(spec["cntrbgfts"]))
                prgmrev   = to_float(row.get(spec["prgmrev"])) if spec["prgmrev"] else None
                compofficer = to_float(row.get(spec["compofficer"])) if spec["compofficer"] else None
                empl      = to_int(row.get(spec["empl"]))

                fin_batch.append((ein, tax_yr, rev, expns, assets, liab, netassets,
                                  cntrbgfts, prgmrev, compofficer, None))

                # Registry update: newest SOI year wins, never overwrite ProPublica
                if cur_src == "propublica":
                    pass  # still insert financials above, just skip registry update
                elif tax_yr >= cur_yr:
                    months_rsv = None
                    if netassets is not None and expns and expns > 0:
                        months_rsv = round(netassets / (expns / 12.0), 2)
                        months_rsv = max(-999.0, min(999.0, months_rsv))
                    reg_batch.append((
                        netassets, expns, liab, months_rsv,
                        empl, empl,
                        rev, assets, tax_yr, now,
                        ein
                    ))
                    existing_src[ein] = (tax_yr, "irs_soi")

                if rows_read % 200000 == 0:
                    flush_all(force=True)
                    print(f"    {rows_read:,} rows read | registry+={reg_updated:,} financials+={fin_inserted:,}")

    flush_all(force=True)
    return rows_read, reg_updated, fin_inserted


def run(dry_run=False, only_year=None):
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA cache_size=-131072")  # 128MB cache

    print("Loading EIN + source index from DB...")
    existing = {}
    for ein, yr, src in db.execute(
        "SELECT EIN, latest_tax_year, data_source FROM registry_enriched"
    ):
        existing[ein] = (yr or 0, src or "")
    print(f"  {len(existing):,} EINs in registry\n")

    now = datetime.now(timezone.utc).isoformat()
    total_reg = total_fin = 0

    files_to_process = []
    for spec in FILE_SPECS:
        for zip_path in sorted(SOI_DIR.glob(spec["pattern"])):
            stem = zip_path.stem
            try:
                yr2 = int(stem[:2])
                full_year = 2000 + yr2
            except ValueError:
                full_year = 0
            if only_year and full_year != only_year:
                continue
            files_to_process.append((full_year, zip_path, spec))

    files_to_process.sort(key=lambda x: x[0])

    for full_year, zip_path, spec in files_to_process:
        print(f"[{full_year} {spec['form']}] {zip_path.name}")
        r, reg, fin = ingest_file(db, zip_path, spec, existing, dry_run, now)
        total_reg += reg
        total_fin += fin
        print(f"  rows={r:,}  registry_updated={reg:,}  financials_inserted={fin:,}\n")

    print("=" * 60)
    print(f"IRS SOI v2 ingest {'(DRY RUN) ' if dry_run else ''}complete")
    print(f"  Registry rows updated: {total_reg:,}")
    print(f"  Financial history rows inserted: {total_fin:,}")

    if not dry_run:
        stats = db.execute("""
            SELECT COUNT(*) total, COUNT(net_assets) has_net,
                   COUNT(employee_count) has_empl,
                   COUNT(months_of_reserve) has_rsv
            FROM registry_enriched
        """).fetchone()
        fin_total = db.execute("SELECT COUNT(*) FROM propublica_financials").fetchone()[0]
        print(f"\nCoverage after ingest:")
        print(f"  net_assets:       {stats[1]:,} / {stats[0]:,} orgs")
        print(f"  employee_count:   {stats[2]:,} / {stats[0]:,} orgs")
        print(f"  months_of_reserve:{stats[3]:,} / {stats[0]:,} orgs")
        print(f"  propublica_financials total: {fin_total:,} rows")

    db.close()
    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--year", type=int, help="Only process this year")
    args = parser.parse_args()
    run(dry_run=args.dry_run, only_year=args.year)
