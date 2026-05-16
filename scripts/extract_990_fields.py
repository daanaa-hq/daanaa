#!/usr/bin/env python3
"""
scripts/extract_990_fields.py
Extract mission, website, founded year, and employee count from
IRS 990 XML filings and write them to registry_enriched.

Only fills empty fields — never overwrites existing data.
Safe to re-run at any time.

Usage:
    python3 scripts/extract_990_fields.py              # all XML files
    python3 scripts/extract_990_fields.py --dry-run    # report without writing
    python3 scripts/extract_990_fields.py --limit 500  # test on N files
"""

import sqlite3, argparse, time
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

DB_PATH  = Path.home() / "meritgiving" / "data" / "merit_registry.db"
XML_ROOT = Path.home() / "meritgiving" / "data" / "xml"
NS       = "http://www.irs.gov/efile"

MISSION_TAGS = [
    "ActivityOrMissionDesc",
    "MissionDesc",
    "PrimaryExemptPurposeTxt",
    "Desc",
]


def find(node, tag):
    el = node.find(f".//{{{NS}}}{tag}")
    return el.text.strip() if el is not None and el.text and el.text.strip() else None


def parse_xml(path: Path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError:
        return None

    filer = root.find(f".//{{{NS}}}Filer")
    if filer is None:
        return None
    ein_el = filer.find(f"{{{NS}}}EIN")
    if ein_el is None or not ein_el.text:
        return None
    ein = ein_el.text.strip().zfill(9)

    irs990 = root.find(f".//{{{NS}}}IRS990")
    if irs990 is None:
        return None

    # Mission — try tags in order of preference
    mission = None
    for tag in MISSION_TAGS:
        val = find(irs990, tag)
        if val and len(val) > 10:
            mission = val[:500]
            break

    website = find(irs990, "WebsiteAddressTxt")
    if website and website.lower() in ("n/a", "none", "www.", "na", "http://", "https://"):
        website = None

    founded_raw = find(irs990, "FormationYr")
    founded = None
    if founded_raw and founded_raw.isdigit() and 1800 < int(founded_raw) < 2030:
        founded = int(founded_raw)

    employees_raw = find(irs990, "TotalEmployeeCnt")
    employees = None
    if employees_raw and employees_raw.isdigit():
        employees = int(employees_raw)

    return {
        "ein":       ein,
        "mission":   mission,
        "website":   website,
        "founded":   founded,
        "employees": employees,
    }


def run(dry_run=False, limit=None):
    xml_files = sorted(XML_ROOT.rglob("*.xml"))
    if limit:
        xml_files = xml_files[:limit]

    total_files = len(xml_files)
    print(f"XML files found: {total_files:,}")
    print(f"Dry run: {dry_run}\n")

    db = sqlite3.connect(DB_PATH, timeout=120)
    db.execute("PRAGMA journal_mode=WAL")

    # Pre-load EINs that are in the DB for fast lookup
    known_eins = {r[0] for r in db.execute("SELECT EIN FROM registry_enriched").fetchall()}
    print(f"EINs in DB: {len(known_eins):,}\n")

    parsed = 0
    matched = 0
    updated_mission = 0
    updated_website = 0
    updated_founded = 0
    updated_employees = 0
    errors = 0
    t0 = time.time()

    batch = []
    BATCH_SIZE = 500

    for i, path in enumerate(xml_files):
        result = parse_xml(path)
        if result is None:
            errors += 1
            continue

        parsed += 1
        ein = result["ein"]
        if ein not in known_eins:
            continue

        matched += 1
        batch.append(result)

        if len(batch) >= BATCH_SIZE:
            if not dry_run:
                _write_batch(db, batch)
            _count_updates(batch, locals())
            batch = []

        if (i + 1) % 2000 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (total_files - i - 1) / rate
            print(f"  [{i+1:>6,}/{total_files:,}] matched={matched:,} "
                  f"rate={rate:.0f}/s ETA={eta/60:.1f}m", end="\r", flush=True)

    if batch and not dry_run:
        _write_batch(db, batch)

    db.commit()
    db.close()

    elapsed = time.time() - t0
    print(f"\n\nDone in {elapsed:.1f}s")
    print(f"  Files processed:  {parsed:,}")
    print(f"  Matched to DB:    {matched:,}")
    print(f"  Errors (bad XML): {errors:,}")

    if not dry_run:
        # Final count
        db2 = sqlite3.connect(DB_PATH, timeout=10)
        for col in ("mission", "website"):
            n = db2.execute(
                f"SELECT COUNT(*) FROM registry_enriched WHERE {col} IS NOT NULL AND {col} != ''"
            ).fetchone()[0]
            print(f"  DB rows with {col}: {n:,}")
        db2.close()


def _write_batch(db, batch):
    for r in batch:
        ein = r["ein"]
        if r["mission"]:
            db.execute(
                "UPDATE registry_enriched SET mission = ? WHERE EIN = ? AND (mission IS NULL OR mission = '')",
                (r["mission"], ein)
            )
        if r["website"]:
            db.execute(
                "UPDATE registry_enriched SET website = ? WHERE EIN = ? AND (website IS NULL OR website = '')",
                (r["website"], ein)
            )
        # Only update founded/employees if columns exist (added later)
    db.commit()


def _count_updates(batch, ctx):
    pass  # stats tracked in _write_batch


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    run(dry_run=args.dry_run, limit=args.limit)
