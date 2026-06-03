#!/usr/bin/env python3
"""
Cross-check our registry against the IRS auto-revocation list.

The IRS publishes a CSV of organizations whose tax-exempt status was
automatically revoked for failing to file for 3 consecutive years.
Any org on that list should NOT be shown as an active, tax-deductible
501(c)(3) on Daanaa.

Usage:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/check_revocations.py              # report only
    python3 scripts/check_revocations.py --apply      # mark revoked in DB
    python3 scripts/check_revocations.py --dry-run    # show matches, no writes

The script downloads the IRS revocation list fresh each run (cached for
24h in /tmp) and writes a report to logs/revocation_check.log.
"""
import sqlite3, csv, os, sys, io, zipfile, urllib.request, logging, argparse
from datetime import datetime, timedelta

IRS_URL   = "https://apps.irs.gov/pub/epostcard/data-download-revocation.zip"
CACHE     = "/tmp/irs_revocations.csv"
CACHE_AGE = 24  # hours before re-downloading
DB_PATH   = os.path.expanduser("~/meritgiving/data/merit_registry.db")
LOG_PATH  = os.path.expanduser("~/meritgiving/logs/revocation_check.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger(__name__)


def fetch_revocation_eins() -> set[str]:
    """Download (or use cache) and return the set of revoked EINs."""
    cache_fresh = (
        os.path.exists(CACHE)
        and datetime.fromtimestamp(os.path.getmtime(CACHE)) > datetime.now() - timedelta(hours=CACHE_AGE)
    )
    if cache_fresh:
        log.info(f"Using cached revocation list: {CACHE}")
    else:
        log.info(f"Downloading IRS revocation list from {IRS_URL} …")
        with urllib.request.urlopen(IRS_URL, timeout=60) as r:
            data = r.read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            name = z.namelist()[0]
            with z.open(name) as f:
                content = f.read().decode("utf-8", errors="replace")
        with open(CACHE, "w") as out:
            out.write(content)
        log.info(f"Cached {len(content):,} bytes → {CACHE}")

    eins: set[str] = set()
    with open(CACHE, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if row:
                ein = row[0].strip().replace("-", "")
                if ein:
                    eins.add(ein)
    log.info(f"Loaded {len(eins):,} revoked EINs from IRS list")
    return eins


def run(apply: bool = False, dry_run: bool = False) -> None:
    revoked = fetch_revocation_eins()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Only check orgs we're actively showing as deductible
    rows = db.execute(
        "SELECT EIN, organization_name, STATE FROM registry_enriched "
        "WHERE deductibility IN ('1','2') OR deductibility IS NULL"
    ).fetchall()
    log.info(f"Checking {len(rows):,} orgs in registry …")

    matches = [r for r in rows if r["EIN"].replace("-", "") in revoked]
    log.info(f"Found {len(matches):,} orgs in registry that appear on IRS revocation list")

    if matches:
        log.info("Sample matches (first 20):")
        for r in matches[:20]:
            log.info(f"  EIN {r['EIN']}  {r['organization_name']}  ({r['STATE']})")

    if apply and not dry_run and matches:
        log.info("Marking revoked orgs (setting deductibility='revoked') …")
        eins = [r["EIN"] for r in matches]
        db.executemany(
            "UPDATE registry_enriched SET deductibility='revoked' WHERE EIN=?",
            [(e,) for e in eins],
        )
        db.commit()
        log.info(f"Marked {len(eins):,} orgs as revoked in registry_enriched")
    elif dry_run:
        log.info("Dry run — no writes")
    else:
        log.info("Report only — re-run with --apply to update the database")

    db.close()
    log.info(f"Done. Full report in {LOG_PATH}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Cross-check registry against IRS revocation list")
    p.add_argument("--apply",   action="store_true", help="Write revoked status to DB")
    p.add_argument("--dry-run", action="store_true", help="Report matches without writing")
    args = p.parse_args()
    run(apply=args.apply, dry_run=args.dry_run)
