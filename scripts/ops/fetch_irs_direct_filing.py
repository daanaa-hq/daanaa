#!/usr/bin/env python3
"""
scripts/ops/fetch_irs_direct_filing.py

Fetches a single org's most recent 990 filing directly from the IRS's own
publishing pipeline (apps.irs.gov), bypassing gt990's ~2-3 month bulk-rebuild
cadence. Built 2026-08-16 after confirming AKF (EIN 521231983) had a real
FY2025 filing (filed 2026-05-15) that gt990's June 4 index didn't have yet --
verified this source has it, and every figure matched CauseIQ exactly
(revenue $106,705,948, expenses $96,147,712, assets $601,887,350,
fundraising $1,445,364, reconciling Part IX breakdown).

IMPORTANT: the IRS's OWN AWS S3 bucket (s3://irs-form-990) was discontinued
December 31, 2021 and is no longer updated. This uses apps.irs.gov's direct
publishing instead (Form 990 series downloads), which IS still active and
updates monthly.

Mechanics:
1. Download the per-submission-year index CSV (index_2025.csv, index_2026.csv,
   etc. -- indexed by when IRS processed/released the filing, NOT the tax
   year it covers) to find the target EIN's most recent ObjectId + XML_BATCH_ID.
2. Download that one monthly batch ZIP (400-700MB, one IRS release covers
   ~50-70K filings across all orgs that submitted that month).
3. Extract just the target EIN's XML, parse revenue/assets/expenses and the
   Part IX functional-expense breakdown.

Scoped to single-org lookups (checking "does this specific org have newer
data than we have") -- NOT a bulk backfill tool. Downloading a ~500MB batch
ZIP per org doesn't scale; for bulk refresh, gt990's consolidated index
(scripts/ops/refresh_stale_orgs_from_gt990.py) remains the right tool.

The index/parse/write building blocks below (iter_990_index_rows,
batch_zip_url, parse_990_xml, write_filing) are also imported by
scripts/ops/refresh_recent_filings_batch.py, the batch-mode version that
downloads each monthly ZIP once and extracts every registry EIN found in it --
built 2026-08-16 once single-org lookups proved this source out. Keep those
functions' signatures stable; the batch script depends on them directly.

Usage:
    python3 scripts/ops/fetch_irs_direct_filing.py 521231983
    python3 scripts/ops/fetch_irs_direct_filing.py 521231983 --apply
"""
import argparse
import csv
import io
import subprocess
import sys
import sqlite3
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import requests

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
NS = "http://www.irs.gov/efile"
INDEX_BASE = "https://apps.irs.gov/pub/epostcard/990/xml"
PARSER_VERSION = "1.1-2026-08-16-direct-irs"


def batch_zip_url(batch_id: str) -> str:
    year = batch_id.split("_")[0]
    return f"{INDEX_BASE}/{year}/{batch_id}.zip"


def iter_990_index_rows(submission_years: list[int]) -> Iterator[dict]:
    """Yields raw index rows (RETURN_TYPE == '990' only) for the given
    submission years -- the year IRS processed/released the filing, not the
    tax year it covers. Shared by single-org lookup and batch discovery so
    there's one place that knows the index CSV's shape."""
    for year in submission_years:
        url = f"{INDEX_BASE}/{year}/index_{year}.csv"
        print(f"Checking {url} ...")
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  skip ({e})")
            continue
        reader = csv.DictReader(io.StringIO(resp.text))
        for row in reader:
            if row.get("RETURN_TYPE", "").strip() != "990":
                continue  # skip EZ/PF -- different statement shape
            yield row


def find_latest_filing(ein: str, submission_years: list[int]) -> dict | None:
    """Check the given submission-year indices (newest first) for this EIN's
    most recent Form 990 filing. Returns the newest match found."""
    best = None
    for row in iter_990_index_rows(submission_years):
        if row.get("EIN", "").strip().zfill(9) != ein:
            continue
        tax_period = row.get("TAX_PERIOD", "").strip()
        candidate = {
            "tax_period": tax_period,
            "object_id": row.get("OBJECT_ID", "").strip(),
            "batch_id": row.get("XML_BATCH_ID", "").strip(),
        }
        if best is None or tax_period > best["tax_period"]:
            best = candidate
    return best


def parse_990_xml(content: bytes) -> dict | None:
    """Parses a single 990 XML's revenue/assets/expenses, Part IX
    functional-expense breakdown, and organization-authored mission text.
    Returns None if it's not a parseable IRS990 return.

    Mission text added 2026-08-16 (Track B/C consolidation, see DECISIONS.md
    same date): one XML download now produces financials + Part IX + a
    mission-text candidate in a single pass, instead of a separate pipeline
    re-downloading the same filing just for Part III text."""
    root = ET.fromstring(content)
    irs990 = root.find(f".//{{{NS}}}IRS990")
    if irs990 is None:
        return None
    grp = irs990.find(f".//{{{NS}}}TotalFunctionalExpensesGrp")

    def amt(tag, node=irs990):
        el = node.find(f".//{{{NS}}}{tag}")
        if el is None or not el.text:
            return None
        try:
            return float(el.text)
        except ValueError:
            return None

    def text(el):
        if el is None or not el.text:
            return None
        value = " ".join(el.text.split())
        return value or None

    # Part I is the organization's explicit short mission statement, so prefer
    # it to the longer Part III program-service accomplishment descriptions.
    mission_text = text(irs990.find(f"{{{NS}}}ActivityOrMissionDesc"))
    if mission_text is None:
        program_descriptions = [
            value
            for value in (
                text(description)
                for description in irs990.findall(
                    f"{{{NS}}}ProgramServiceAccomplishmentGrp/"
                    f"{{{NS}}}DescriptionProgramServiceAccomTxt"
                )
            )
            if value
        ]
        mission_text = "\n\n".join(program_descriptions) or None

    return {
        "total_revenue": amt("CYTotalRevenueAmt"),
        "total_assets": amt("TotalAssetsEOYAmt"),
        "total_expenses": amt("TotalAmt", grp) if grp is not None else None,
        "program_services_amt": amt("ProgramServicesAmt", grp) if grp is not None else None,
        "management_general_amt": amt("ManagementAndGeneralAmt", grp) if grp is not None else None,
        "fundraising_amt": amt("FundraisingAmt", grp) if grp is not None else None,
        "mission_text": mission_text,
    }


def fetch_and_parse(batch_id: str, object_id: str) -> dict | None:
    zip_url = batch_zip_url(batch_id)
    print(f"Downloading {zip_url} (this is a full monthly batch, ~400-700MB)...")

    xml_name = f"{object_id}_public.xml"
    # Python's zipfile module doesn't support the compression method IRS uses
    # for these archives ("That compression method is not supported") --
    # confirmed the command-line `unzip` handles it fine, so shell out to it
    # instead of fighting zipfile.
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "batch.zip"
        resp = requests.get(zip_url, timeout=600, stream=True)
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)

        result = subprocess.run(
            ["unzip", "-o", str(zip_path), xml_name, "-d", tmpdir],
            capture_output=True, text=True
        )
        xml_path = Path(tmpdir) / xml_name
        if result.returncode != 0 or not xml_path.exists():
            print(f"  {xml_name} not found in batch (unzip: {result.stderr.strip()})")
            return None
        content = xml_path.read_bytes()

    return parse_990_xml(content)


def write_filing(db: sqlite3.Connection, ein: str, filing: dict, data: dict, now: str) -> bool:
    """Writes one parsed filing to all 3 tables (org_revenue_history,
    irs_990_functional_expense_filings, registry_enriched) using the
    established safety rules: never downgrade, reconciliation-checked
    expense breakdown. Returns whether the expense breakdown reconciled.
    Shared by the single-org CLI and the batch script -- change write
    behavior here only, not in both places."""
    tax_year = int(filing["tax_period"][:4])
    total = data["total_expenses"]
    program = data["program_services_amt"] or 0
    mgmt = data["management_general_amt"] or 0
    fundraising = data["fundraising_amt"] or 0
    reconciles = bool(total and abs((program + mgmt + fundraising) - total) <= 1)

    db.execute(
        "INSERT OR REPLACE INTO org_revenue_history "
        "(EIN, tax_year, total_revenue, total_assets, total_expenses, form_type, source, extracted_at) "
        "VALUES (?, ?, ?, ?, ?, '990', 'irs_direct', ?)",
        (ein, tax_year, data["total_revenue"], data["total_assets"], data["total_expenses"], now)
    )
    if data["program_services_amt"] is not None:
        db.execute(
            "INSERT OR REPLACE INTO irs_990_functional_expense_filings "
            "(EIN, tax_year, object_id, source_url, total_amt, program_services_amt, "
            "management_general_amt, fundraising_amt, reconciles, validation_status, parser_version, extracted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ein, tax_year, filing["object_id"], batch_zip_url(filing["batch_id"]),
             total, program, mgmt, fundraising, int(reconciles),
             "accepted" if reconciles else "rejected", PARSER_VERSION, now)
        )
    db.execute(
        "UPDATE registry_enriched SET total_revenue = ?, total_assets = ?, latest_tax_year = ?, "
        "data_source = 'irs_direct' WHERE EIN = ? AND (latest_tax_year IS NULL OR latest_tax_year < ?)",
        (data["total_revenue"], data["total_assets"], tax_year, ein, tax_year)
    )

    # Mission text, added 2026-08-16. Guard clause copied verbatim from
    # scripts/enrichment/ingest_990_missions.py's existing precedence rule
    # (verified against that file, not assumed): only write when the org has
    # no mission yet, or its current mission was AI-generated. Never
    # overwrites a claimed/nonprofit-submitted mission, a scraped-from-website
    # mission, or a mission from a previous, newer irs_990 filing.
    mission_text = data.get("mission_text")
    if mission_text and len(mission_text.strip()) >= 20:
        db.execute(
            "UPDATE registry_enriched "
            "SET mission = ?, mission_source = 'irs_990', "
            "    mission_last_verified = ? "
            "WHERE EIN = ? "
            "  AND (mission_source IS NULL OR mission_source LIKE 'ai_%' "
            "       OR mission IS NULL OR mission = '')",
            (mission_text, tax_year, ein),
        )

    return reconciles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ein")
    ap.add_argument("--apply", action="store_true", help="Write to the database (default: print only)")
    args = ap.parse_args()

    ein = args.ein.zfill(9)
    current_year = datetime.now().year
    filing = find_latest_filing(ein, [current_year, current_year - 1])
    if not filing:
        print("No Form 990 filing found in the checked submission years.")
        sys.exit(1)

    print(f"Found: tax_period={filing['tax_period']}, object_id={filing['object_id']}, batch={filing['batch_id']}")
    data = fetch_and_parse(filing["batch_id"], filing["object_id"])
    if not data:
        print("Could not parse the filing.")
        sys.exit(1)

    print(f"\nParsed (tax_year={filing['tax_period'][:4]}):")
    for k, v in data.items():
        print(f"  {k}: {v}")

    if not args.apply:
        total = data["total_expenses"]
        program = data["program_services_amt"] or 0
        mgmt = data["management_general_amt"] or 0
        fundraising = data["fundraising_amt"] or 0
        reconciles = bool(total and abs((program + mgmt + fundraising) - total) <= 1)
        print(f"  reconciles: {reconciles}")
        print("\nDry run -- no changes written. Re-run with --apply to write.")
        return

    db = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    reconciles = write_filing(db, ein, filing, data, now)
    db.commit()
    print(f"  reconciles: {reconciles}")
    print("Written.")


if __name__ == "__main__":
    main()
