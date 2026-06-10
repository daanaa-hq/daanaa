#!/usr/bin/env python3
"""
scripts/expand_990_coverage.py

Uses the local gt990 index CSV to find 990 XML filings for gap Flame orgs
(those with mission + score but no website), downloads those XML files from
the gt990 S3 bucket, and extracts WebsiteAddressTxt.

Runs entirely on the local server — no API tokens needed.
Zero auth required (gt990 S3 bucket is public).

Usage:
    python3 scripts/expand_990_coverage.py              # all matched orgs
    python3 scripts/expand_990_coverage.py --limit 500  # smaller batch
    python3 scripts/expand_990_coverage.py --workers 16 # more workers
    python3 scripts/expand_990_coverage.py --dry-run    # no DB writes

After completion, run migrate_merit_tier.py to promote Flame→Lantern/Beacon.
"""

import sqlite3, csv, time, argparse, logging
import urllib.request, urllib.error
import xml.etree.ElementTree as ET
import threading
from pathlib import Path
from queue import Queue, Empty

from website_normalize import normalize_website

DB_PATH   = Path.home() / "meritgiving" / "data" / "merit_registry.db"
GT990_IDX = Path.home() / "meritgiving" / "data" / "cache" / "gt990_index_2026-03-20.csv"

NS = "http://www.irs.gov/efile"
MISSION_TAGS = ["ActivityOrMissionDesc", "MissionDesc", "PrimaryExemptPurposeTxt", "Desc"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def connect():
    db = sqlite3.connect(DB_PATH, timeout=60, check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    return db


def load_gap_eins(db) -> dict[str, dict]:
    """Load Flame orgs eligible for Lantern if website confirmed."""
    rows = db.execute("""
        SELECT EIN, peer_percentile, ntee1_percentile, total_revenue
        FROM registry_enriched
        WHERE merit_tier = 'Flame'
          AND mission IS NOT NULL AND TRIM(mission) != ''
          AND COALESCE(peer_percentile, ntee1_percentile) IS NOT NULL
          AND latest_tax_year >= 2022
          AND total_revenue > 0
          AND (website IS NULL OR TRIM(website) = '')
          AND (merit_band IS NULL OR merit_band != 'Concerns')
        ORDER BY COALESCE(peer_percentile, ntee1_percentile) DESC
    """).fetchall()
    return {r[0].zfill(9): {"pct": r[1] or r[2], "revenue": r[3]} for r in rows}


def build_filing_map(gap_eins: set[str]) -> dict[str, dict]:
    """
    Scan local gt990 index CSV, build EIN→{url, year} map for gap orgs.
    Keeps the most recent 990/990EZ per org.
    """
    if not GT990_IDX.exists():
        log.error(f"Local index not found: {GT990_IDX}")
        return {}

    log.info(f"Reading gt990 index: {GT990_IDX}")
    filing_map: dict[str, dict] = {}
    total_rows = 0
    with open(GT990_IDX, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            ein = (row.get("EIN") or "").strip().zfill(9)
            if ein not in gap_eins:
                continue
            form = (row.get("FormType") or "").strip()
            if form not in ("990", "990EZ", "990-EZ"):
                continue
            url = (row.get("URL") or "").strip()
            if not url:
                continue
            tax_year = (row.get("TaxYear") or "0").strip()
            try:
                yr = int(tax_year)
            except Exception:
                yr = 0
            prev = filing_map.get(ein)
            if prev is None or yr > prev["year"]:
                filing_map[ein] = {"ein": ein, "url": url, "year": yr}

    log.info(f"  Scanned {total_rows:,} index rows → matched {len(filing_map):,} gap orgs")
    return filing_map


def parse_xml_url(url: str) -> str | None:
    """Download and parse a 990 XML from S3. Returns website URL or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Daanaa/1.0 data-pipeline"})
        with urllib.request.urlopen(req, timeout=30) as r:
            content = r.read()
    except Exception:
        return None

    # Strip BOM
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return None

    irs990 = root.find(f".//{{{NS}}}IRS990")
    if irs990 is None:
        irs990 = root.find(f".//{{{NS}}}IRS990EZ")
    if irs990 is None:
        return None

    for tag in ("WebsiteAddressTxt", "WebsiteAddress", "website"):
        el = irs990.find(f".//{{{NS}}}{tag}")
        if el is not None and el.text:
            raw = el.text.strip()
            if (raw
                    and " " not in raw      # no spaces = not a phrase/name
                    and len(raw) >= 6):     # minimum plausible URL length
                # canonical form (lowercase bare host, mangled schemes
                # repaired); None for junk like N/A / www. / xxx
                return normalize_website(raw)
    return None


def worker_thread(task_q: Queue, result_q: Queue, stop: threading.Event):
    while not stop.is_set():
        try:
            item = task_q.get(timeout=1)
        except Empty:
            continue
        website = parse_xml_url(item["url"])
        result_q.put({"ein": item["ein"], "website": website})
        task_q.task_done()
        time.sleep(0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Max gap orgs to process")
    ap.add_argument("--workers", type=int, default=12, help="Download workers (default 12)")
    ap.add_argument("--dry-run", action="store_true", help="No DB writes")
    args = ap.parse_args()

    db = connect()
    gap_eins_data = load_gap_eins(db)
    gap_eins = set(gap_eins_data.keys())
    log.info(f"Gap orgs (Flame, has mission+score, no website): {len(gap_eins):,}")

    filing_map = build_filing_map(gap_eins)
    if not filing_map:
        log.error("No filings found in local index.")
        return

    tasks = list(filing_map.values())

    if args.limit:
        # Highest-ranked by peer percentile first
        tasks.sort(key=lambda t: gap_eins_data.get(t["ein"], {}).get("pct", 0) or 0, reverse=True)
        tasks = tasks[:args.limit]
        log.info(f"Limited to top {args.limit:,} by peer percentile")

    log.info(f"Processing {len(tasks):,} XML files with {args.workers} workers")
    if args.dry_run:
        log.info("DRY RUN — no DB writes")

    task_q: Queue = Queue()
    result_q: Queue = Queue()
    stop = threading.Event()

    for t in tasks:
        task_q.put(t)

    threads = [
        threading.Thread(target=worker_thread, args=(task_q, result_q, stop), daemon=True)
        for _ in range(args.workers)
    ]
    for t in threads:
        t.start()

    processed = 0
    found = 0
    write_batch = []
    t0 = time.time()

    while processed < len(tasks):
        try:
            result = result_q.get(timeout=60)
        except Empty:
            log.warning("Result queue timeout — workers may be stalled")
            continue

        processed += 1
        if result["website"]:
            found += 1
            write_batch.append((result["website"], result["ein"]))

        if not args.dry_run and len(write_batch) >= 100:
            db.executemany(
                "UPDATE registry_enriched SET website = ? WHERE EIN = ? AND (website IS NULL OR TRIM(website) = '')",
                write_batch
            )
            db.commit()
            write_batch.clear()

        if processed % 500 == 0 or processed == len(tasks):
            elapsed = time.time() - t0
            rate = processed / elapsed * 60
            pct = 100 * processed / len(tasks)
            eta_min = (len(tasks) - processed) / max(rate / 60, 0.01) / 60
            log.info(f"[{pct:4.1f}%] {processed:,}/{len(tasks):,} | "
                     f"websites={found:,} ({100*found/max(processed,1):.1f}%) | "
                     f"{rate:.0f}/min | ETA {eta_min:.0f}min")

    stop.set()

    if not args.dry_run and write_batch:
        db.executemany(
            "UPDATE registry_enriched SET website = ? WHERE EIN = ? AND (website IS NULL OR TRIM(website) = '')",
            write_batch
        )
        db.commit()

    elapsed = time.time() - t0
    log.info(f"\nDone. {processed:,} processed, {found:,} websites found ({100*found/max(processed,1):.1f}%)")
    log.info(f"Time: {elapsed/60:.1f} minutes")

    if found > 0 and not args.dry_run:
        log.info("Next: run migrate_merit_tier.py to promote Flame→Lantern/Beacon")

    db.close()


if __name__ == "__main__":
    main()
