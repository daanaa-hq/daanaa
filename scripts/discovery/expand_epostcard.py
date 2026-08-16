#!/usr/bin/env python3
"""
MERIT Worker E: e-Postcard (990-N) Expansion Script

Expands the master organization database by adding stub records for 501(c)(3)
organizations that file Form 990-N (e-Postcard) but have no financial data.

These organizations appear as "Verified — Limited Financial Data" rather than
being excluded from the directory.

SOURCE FILES:
    - index_2020.json    : IRS 990 index file for 2020
    - index_2022.json    : IRS 990 index file for 2022
    - bmf.csv            : IRS Business Master File
    - master_orgs.csv    : Existing MERIT master organization file

OUTPUT:
    - master_orgs_clean.csv  : Updated master file with new stub records appended
    - reports/epostcard_expansion_YYYY-MM-DD.csv : Expansion report

Author: MERIT Worker E
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


# ── CONFIGURATION ──────────────────────────────────────────────────────────

def get_data_dir():
    """Get data directory from command line or use default."""
    parser = argparse.ArgumentParser(
        description="MERIT e-Postcard (990-N) Expansion Script"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="/home/akbar/meritgiving/data",
        help="Path to data directory (default: /home/akbar/meritgiving/data)"
    )
    parser.add_argument(
        "--master-file",
        type=str,
        default=None,
        help="Path to master CSV file (default: DATA_DIR/master_orgs_clean.csv)"
    )
    parser.add_argument(
        "--index-files",
        type=str,
        nargs="+",
        default=None,
        help="Paths to index JSON files"
    )
    parser.add_argument(
        "--bmf-file",
        type=str,
        default=None,
        help="Path to BMF CSV file (default: DATA_DIR/bmf.csv)"
    )
    args = parser.parse_args()
    return args


args = get_data_dir()

DATA_DIR = Path(args.data_dir)
REPORTS_DIR = DATA_DIR / "reports"
MASTER_FILE = Path(args.master_file) if args.master_file else DATA_DIR / "master_orgs_clean.csv"
REPORT_FILE = REPORTS_DIR / f"epostcard_expansion_{datetime.now().strftime('%Y-%m-%d')}.csv"

# Input source files
if args.index_files:
    INDEX_FILES = [Path(f) for f in args.index_files]
else:
    INDEX_FILES = [
        DATA_DIR / "index_2020.json",
        DATA_DIR / "index_2022.json",
    ]

BMF_FILE = Path(args.bmf_file) if args.bmf_file else DATA_DIR / "bmf.csv"

# e-Postcard (990-N) filing threshold
GROSS_RECEIPTS_THRESHOLD = 50000

# Stub record defaults
STUB_MERIT_SCORE = 25
STUB_RECORD_STATUS = "Active — e-Postcard Filer"
STUB_BADGES = "Verified 501(c)(3)|Limited Financial Data"

# ── LOGGING ────────────────────────────────────────────────────────────────

LOG = []

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    LOG.append(line)
    print(line)


# ── DATA LOADING ───────────────────────────────────────────────────────────

def load_index_file(path: Path) -> list[dict]:
    """Load an IRS index JSON file and return a list of filing records."""
    if not path.exists():
        log(f"WARNING: Index file not found: {path}")
        return []

    log(f"Loading index file: {path.name} ...")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # IRS index files typically have "AllFilings" as the root key
    if isinstance(data, dict) and "AllFilings" in data:
        filings = data["AllFilings"]
    elif isinstance(data, list):
        filings = data
    elif isinstance(data, dict):
        # Some index files may have different structure
        # Try to find a list of filings
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                filings = value
                log(f"  Using key '{key}' with {len(filings)} records")
                break
        else:
            log(f"WARNING: Could not find filings list in {path.name}")
            return []
    else:
        log(f"WARNING: Unexpected JSON structure in {path.name}")
        return []

    log(f"  Loaded {len(filings):,} total filings from {path.name}")
    return filings


def extract_990n_filings(filings: list[dict]) -> set[str]:
    """Extract EINs of organizations that filed Form 990-N (e-Postcard).

    Criteria:
        - FormType is '990-N' or similar variant
        - Gross receipts <= $50,000 (the 990-N threshold)
    """
    ein_set = set()
    form_type_variants = {"990-N", "990N", "EPOSTCARD", "E-POSTCARD", "POSTCARD"}

    for filing in filings:
        form_type = str(filing.get("FormType", "")).strip().upper().replace("-", "")
        ein = str(filing.get("EIN", "")).strip().replace("-", "")

        # Check form type match
        is_990n = form_type in {"990N", "EPOSTCARD", "POSTCARD"}

        # Also check by gross receipts threshold
        gross_receipts = filing.get("GrossReceipts", filing.get("GrossReceiptsAmt", None))

        if is_990n:
            if gross_receipts is not None:
                try:
                    if float(gross_receipts) <= GROSS_RECEIPTS_THRESHOLD:
                        if ein and len(ein) == 9 and ein.isdigit():
                            ein_set.add(ein)
                except (ValueError, TypeError):
                    pass
            else:
                # No gross receipts data, but form type is 990-N
                if ein and len(ein) == 9 and ein.isdigit():
                    ein_set.add(ein)

    return ein_set


def load_bmf(path: Path) -> dict[str, dict]:
    """Load Business Master File CSV and return a dict keyed by EIN."""
    if not path.exists():
        log(f"WARNING: BMF file not found: {path}")
        return {}

    log(f"Loading BMF file: {path.name} ...")

    bmf_data = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        log(f"  BMF columns: {fieldnames}")

        count = 0
        for row in reader:
            count += 1
            ein = str(row.get("EIN", "")).strip().replace("-", "")
            if ein and len(ein) == 9 and ein.isdigit():
                bmf_data[ein] = row

    log(f"  Loaded {len(bmf_data):,} valid BMF records out of {count:,} total rows")
    return bmf_data


def load_master_eins(path: Path) -> tuple[set[str], list[str]]:
    """Load existing master file and return a set of EINs already present."""
    if not path.exists():
        log(f"WARNING: Master file not found: {path}")
        log("  Will create a new master file from scratch.")
        return set(), []

    log(f"Loading existing master file: {path.name} ...")

    existing_eins = set()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        log(f"  Master columns: {fieldnames}")

        count = 0
        for row in reader:
            count += 1
            ein = str(row.get("ein", row.get("EIN", ""))).strip().replace("-", "")
            if ein and len(ein) == 9 and ein.isdigit():
                existing_eins.add(ein)

    log(f"  Found {len(existing_eins):,} unique EINs in existing master file ({count:,} total rows)")
    return existing_eins, fieldnames


# ── STUB RECORD GENERATION ─────────────────────────────────────────────────

def create_stub_record(ein: str, bmf_row: dict, master_fieldnames: list[str]) -> dict:
    """Create a stub record for an e-Postcard filer with limited financial data."""

    # Extract fields from BMF
    name = bmf_row.get("NAME", bmf_row.get("ORGANIZATION_NAME", bmf_row.get("BusinessNameLine1", ""))).strip()
    city = bmf_row.get("CITY", bmf_row.get("City", "")).strip()
    state = bmf_row.get("STATE", bmf_row.get("State", "")).strip()
    ntee = bmf_row.get("NTEE_CD", bmf_row.get("NTEECode", bmf_row.get("NTEE", ""))).strip()

    # Clean up NTEE code (take first 3 characters if longer)
    if ntee and len(ntee) > 3:
        ntee = ntee[:3]

    # Build stub record using master file column names
    stub = {}
    for fn in master_fieldnames:
        lower_fn = fn.lower()
        if lower_fn == "ein":
            stub[fn] = ein
        elif lower_fn in ("name", "organization_name", "org_name"):
            stub[fn] = name
        elif lower_fn in ("city",):
            stub[fn] = city
        elif lower_fn in ("state",):
            stub[fn] = state
        elif lower_fn in ("ntee", "ntee_code", "ntee_cd"):
            stub[fn] = ntee
        elif lower_fn in ("record_status", "status"):
            stub[fn] = STUB_RECORD_STATUS
        elif lower_fn in ("MERIT_score", "score"):
            stub[fn] = str(STUB_MERIT_SCORE)
        elif lower_fn in ("badges",):
            stub[fn] = STUB_BADGES
        elif lower_fn in ("financials", "990_data", "filing_data"):
            stub[fn] = ""  # null equivalent in CSV
        else:
            stub[fn] = ""  # Default empty for other columns

    return stub


# ── MAIN PROCESS ───────────────────────────────────────────────────────────

def main():
    start_time = datetime.now()
    log("=" * 70)
    log("MERIT Worker E: e-Postcard (990-N) Expansion")
    log("=" * 70)

    # ── 1. Load existing master file ──────────────────────────────────────
    existing_eins, master_fieldnames = load_master_eins(MASTER_FILE)

    if not master_fieldnames:
        # Create default fieldnames if master doesn't exist
        master_fieldnames = [
            "ein", "name", "city", "state", "ntee",
            "record_status", "MERIT_score", "badges", "financials"
        ]
        log(f"  Using default column names: {master_fieldnames}")

    # ── 2. Load and extract 990-N EINs from index files ──────────────────
    all_990n_eins = set()

    for idx_path in INDEX_FILES:
        filings = load_index_file(idx_path)
        if filings:
            ein_set = extract_990n_filings(filings)
            log(f"  Found {len(ein_set):,} unique 990-N EINs in {idx_path.name}")
            all_990n_eins.update(ein_set)

    log(f"\nTotal unique 990-N EINs across all index files: {len(all_990n_eins):,}")

    # ── 3. Load BMF for cross-referencing ────────────────────────────────
    bmf_data = load_bmf(BMF_FILE)

    # ── 4. Find EINs not already in master ───────────────────────────────
    new_eins = all_990n_eins - existing_eins
    log(f"\nEINs already in master: {len(all_990n_eins & existing_eins):,}")
    log(f"EINs to add (new): {len(new_eins):,}")

    if not new_eins:
        log("\nNo new organizations to add. Exiting.")
        sys.exit(0)

    # ── 5. Create stub records ────────────────────────────────────────────
    stub_records = []
    matched_with_bmf = 0
    no_bmf_match = 0

    for ein in sorted(new_eins):
        bmf_row = bmf_data.get(ein)
        if bmf_row:
            stub = create_stub_record(ein, bmf_row, master_fieldnames)
            stub_records.append(stub)
            matched_with_bmf += 1
        else:
            # Create minimal stub even without BMF data
            minimal_bmf = {
                "NAME": "",
                "CITY": "",
                "STATE": "",
                "NTEE_CD": ""
            }
            stub = create_stub_record(ein, minimal_bmf, master_fieldnames)
            stub_records.append(stub)
            no_bmf_match += 1

    log(f"\nStub records created: {len(stub_records):,}")
    log(f"  Matched with BMF data: {matched_with_bmf:,}")
    log(f"  No BMF match (minimal stub): {no_bmf_match:,}")

    # ── 6. Determine state distribution ───────────────────────────────────
    state_counts = {}
    for stub in stub_records:
        for fn in master_fieldnames:
            if fn.lower() == "state":
                state = stub.get(fn, "")
                if state:
                    state_counts[state] = state_counts.get(state, 0) + 1

    log(f"\nTop 10 states by new records:")
    for state, count in sorted(state_counts.items(), key=lambda x: -x[1])[:10]:
        log(f"  {state}: {count:,}")

    # ── 7. Write updated master file ──────────────────────────────────────
    master_exists = MASTER_FILE.exists()

    if master_exists:
        # Append to existing file
        log(f"\nAppending {len(stub_records):,} new records to {MASTER_FILE.name} ...")
        with open(MASTER_FILE, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=master_fieldnames)
            for stub in stub_records:
                writer.writerow(stub)
    else:
        # Create new master file
        log(f"\nCreating new master file: {MASTER_FILE.name} ...")
        with open(MASTER_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=master_fieldnames)
            writer.writeheader()
            for stub in stub_records:
                writer.writerow(stub)

    log(f"  Done! Wrote {len(stub_records):,} records.")

    # ── 8. Write expansion report ─────────────────────────────────────────
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    log(f"\nGenerating expansion report: {REPORT_FILE.name} ...")

    with open(REPORT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        # Report header
        writer.writerow(["MERIT e-Postcard Expansion Report"])
        writer.writerow(["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])

        # Summary statistics
        writer.writerow(["=== SUMMARY STATISTICS ==="])
        writer.writerow(["Total 990-N EINs found in index files:", len(all_990n_eins)])
        writer.writerow(["Already in master file:", len(all_990n_eins & existing_eins)])
        writer.writerow(["New records added:", len(stub_records)])
        writer.writerow(["Matched with BMF:", matched_with_bmf])
        writer.writerow(["No BMF match (minimal stub):", no_bmf_match])
        writer.writerow(["Gross receipts threshold:", f"${GROSS_RECEIPTS_THRESHOLD:,}"])
        writer.writerow([])

        # State distribution
        writer.writerow(["=== STATE DISTRIBUTION (Top 20) ==="])
        writer.writerow(["State", "Count"])
        for state, count in sorted(state_counts.items(), key=lambda x: -x[1])[:20]:
            writer.writerow([state, count])
        writer.writerow([])

        # All new records detail
        writer.writerow(["=== NEW RECORDS DETAIL ==="])
        writer.writerow(master_fieldnames)
        for stub in stub_records:
            writer.writerow([stub.get(fn, "") for fn in master_fieldnames])

    log(f"  Report written: {REPORT_FILE}")

    # ── 9. Final summary ──────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    log(f"\n{'=' * 70}")
    log("EXPANSION COMPLETE")
    log(f"{'=' * 70}")
    log(f"Total new stub records added: {len(stub_records):,}")
    log(f"Records matched with BMF: {matched_with_bmf:,}")
    log(f"Records with minimal data: {no_bmf_match:,}")
    log(f"Output master file: {MASTER_FILE}")
    log(f"Expansion report: {REPORT_FILE}")
    log(f"Elapsed time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    log(f"{'=' * 70}\n")

    # Write execution log to report directory
    log_file = REPORTS_DIR / f"epostcard_expansion_{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
    log(f"Execution log saved: {log_file}")


if __name__ == "__main__":
    main()
