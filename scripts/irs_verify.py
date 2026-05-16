#!/usr/bin/env python3
"""
irs_verify.py - IRS Authority & Verification Agent (v2.0)
Downloads authoritative IRS source files and verifies EINs in master_orgs.csv.

Handles pipe-delimited text files from IRS Tax Exempt Organization Search (TEOS).

Usage:
    python irs_verify.py [--dry-run] [--force-download] [--master-csv PATH] [--output-dir PATH]

Environment Variables:
    IRS_DATA_DIR        - Base directory for IRS data
    MASTER_ORGS_CSV     - Path to master_orgs.csv
    REPORTS_DIR         - Directory for verification reports
    IRS_DOWNLOAD_TIMEOUT- Download timeout in seconds (default: 300)
    IRS_MAX_RETRIES     - Max download retries (default: 3)
"""

import argparse
import csv
import hashlib
import logging
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Configuration ──────────────────────────────────────────────────────────

IRS_SOURCES = {
    "pub78": {
        "url": "https://apps.irs.gov/pub/epostcard/data-download-pub78.zip",
        "description": "IRS Publication 78 - Eligible for tax-deductible charitable contributions",
        "filename": "data-download-pub78.zip",
        "extracted_name": "data-download-pub78.txt",
        "delimiter": "|",
        "fieldnames": ["EIN", "LEGAL_NAME", "CITY", "STATE", "COUNTRY", "DEDUCTIBILITY_STATUS"],
    },
    "autorevocation": {
        "url": "https://apps.irs.gov/pub/epostcard/data-download-revocation.zip",
        "description": "IRS Auto-Revocation List - Automatic Revocation of Exemption",
        "filename": "data-download-revocation.zip",
        "extracted_name": "data-download-revocation.txt",
        "delimiter": "|",
        "fieldnames": [
            "EIN", "LEGAL_NAME", "DOING_BUSINESS_AS_NAME", "ORGANIZATION_ADDRESS",
            "CITY", "STATE", "ZIP_CODE", "COUNTRY", "EXEMPTION_TYPE",
            "REVOCATION_DATE", "REVOCATION_POSTING_DATE", "EXEMPTION_REINSTATEMENT_DATE",
        ],
    },
}

# Deductibility status codes from Pub 78 indicating verified deductibility
DEDUCTIBILITY_VERIFIED_CODES = {"PC", "POF", "SC", "IND", "GOV"}
# PC=Public Charity, POF=Private Operating Foundation, SC=Supporting Organization
# IND=Independent Organization, GOV=Governmental Unit

# Subsection code for 501(c)(3) organizations
SUBSECTION_501C3 = "03"

# EO BMF reference URL
EO_BMF_URL = (
    "https://www.irs.gov/charities-non-profits/"
    "exempt-organizations-business-master-file-extract-eo-bmf"
)

# ── Logging Setup ──────────────────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logger = logging.getLogger("irs_verify")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT, handlers=[logging.StreamHandler(sys.stdout)])


# ── Path Resolution ────────────────────────────────────────────────────────


class Paths:
    """Centralized path management with environment overrides."""

    def __init__(self, base_dir: Optional[str] = None, master_csv: Optional[str] = None, reports_dir: Optional[str] = None):
        self.base = Path(base_dir or os.environ.get("IRS_DATA_DIR", "/home/akbar/meritgiving/data/raw/irs_authority"))
        self.master_csv = Path(master_csv or os.environ.get("MASTER_ORGS_CSV", "/home/akbar/meritgiving/data/master_orgs.csv"))
        self.reports = Path(reports_dir or os.environ.get("REPORTS_DIR", "/home/akbar/meritgiving/data/reports"))
        self.archive = self.base / "archive"
        self.tmp = self.base / "tmp"

    def ensure_dirs(self) -> None:
        for p in [self.base, self.archive, self.tmp, self.reports]:
            p.mkdir(parents=True, exist_ok=True)


# ── HTTP Utilities ─────────────────────────────────────────────────────────


def create_session(timeout: int = 300, max_retries: int = 3) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "MERIT-IRS-Verify/2.0 (Tax-Exempt Org Verification; Tax-Exempt Organization Search Data User)",
    })
    return session


def download_file(session: requests.Session, url: str, dest: Path, timeout: int, force: bool = False) -> Tuple[bool, str]:
    """
    Download file with resume support and checksum validation.
    Returns (success: bool, checksum: str).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".part")
    headers = {}

    if partial.exists() and not force:
        headers["Range"] = f"bytes={partial.stat().st_size}-"
        logger.info("Resuming download from %s (%s)", partial.stat().st_size, url)

    try:
        resp = session.get(url, stream=True, timeout=timeout, headers=headers)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Download failed for %s: %s", url, exc)
        return False, ""

    mode = "ab" if partial.exists() and resp.status_code == 206 else "wb"
    hasher = hashlib.sha256()
    bytes_downloaded = 0
    try:
        with open(partial, mode) as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    fh.write(chunk)
                    hasher.update(chunk)
                    bytes_downloaded += len(chunk)
    except OSError as exc:
        logger.error("Write error for %s: %s", partial, exc)
        return False, ""

    shutil.move(str(partial), str(dest))
    checksum = hasher.hexdigest()
    logger.info("Downloaded %s -> %s (%.2f MB, sha256:%s...)",
                url, dest.name, bytes_downloaded / (1024*1024), checksum[:16])
    return True, checksum


# ── ZIP / Delimited File Parsing ───────────────────────────────────────────


def extract_target_from_zip(zip_path: Path, target_name: str, tmp_dir: Path) -> Optional[Path]:
    """Extract specific file from ZIP by name. Returns path to extracted file."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Find file by name (case-insensitive)
            target_lower = target_name.lower()
            for name in zf.namelist():
                if name.lower() == target_lower or Path(name).name.lower() == target_lower:
                    zf.extract(name, tmp_dir)
                    extracted = tmp_dir / name
                    logger.info("Extracted %s from %s", name, zip_path.name)
                    return extracted
            # If exact match not found, extract first .txt file
            for name in zf.namelist():
                if name.lower().endswith(".txt"):
                    zf.extract(name, tmp_dir)
                    extracted = tmp_dir / name
                    logger.info("Extracted first .txt: %s from %s", name, zip_path.name)
                    return extracted
    except zipfile.BadZipFile as exc:
        logger.error("Bad ZIP file %s: %s", zip_path, exc)
    return None


def iter_delimited_file(
    file_path: Path,
    delimiter: str = "|",
    encoding: str = "utf-8",
    fieldnames: Optional[List[str]] = None,
):
    """
    Memory-efficient generator for pipe-delimited IRS files.
    Yields dicts. Handles \r (CR) line endings. Skips empty rows.
    """
    for enc in [encoding, "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc, errors="replace") as fh:
                content = fh.read().replace("\r", "\n")
            break
        except UnicodeDecodeError:
            continue
    else:
        return

    reader = csv.DictReader(
        content.split("\n"),
        fieldnames=fieldnames,
        delimiter=delimiter,
    )
    count = 0
    for row in reader:
        if row and any(v.strip() for v in row.values()):
            yield {k: (v or "").strip() for k, v in row.items()}
            count += 1
    logger.info("Iterated %d records from %s", count, file_path.name)


# ── IRS Data Loaders ───────────────────────────────────────────────────────


def load_pub78_records(file_path: Path, fieldnames: List[str], delimiter: str = "|") -> Dict[str, Dict[str, str]]:
    """
    Memory-efficient Pub 78 parser. Streams file and builds EIN-indexed dict.
    Returns: {EIN: {"deductibility": str, "name": str, "city": str, "state": str}}
    """
    pub78: Dict[str, Dict[str, str]] = {}
    count = 0

    # Use csv.reader for memory efficiency (no dict overhead)
    for enc in ["utf-8", "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc, errors="replace") as fh:
                content = fh.read().replace("\r", "\n")
            break
        except UnicodeDecodeError:
            continue

    reader = csv.reader(content.split("\n"), delimiter=delimiter)
    # Build index mapping: fieldname -> column position
    idx = {name: i for i, name in enumerate(fieldnames)}

    for row in reader:
        if not row or len(row) < len(fieldnames):
            continue
        ein = normalize_ein(row[idx["EIN"]])
        if not ein:
            continue
        pub78[ein] = {
            "deductibility": row[idx["DEDUCTIBILITY_STATUS"]].strip().upper(),
            "name": row[idx["LEGAL_NAME"]].strip(),
            "city": row[idx["CITY"]].strip(),
            "state": row[idx["STATE"]].strip(),
            "country": row[idx["COUNTRY"]].strip(),
        }
        count += 1
        if count % 250000 == 0:
            logger.debug("  Pub78: loaded %d records...", count)

    logger.info("Pub78: %d valid EIN records loaded", len(pub78))
    return pub78


def load_revocation_records(file_path: Path, fieldnames: List[str], delimiter: str = "|") -> Dict[str, Dict[str, str]]:
    """
    Memory-efficient Auto-Revocation parser. Streams file and builds EIN-indexed dict.
    Returns: {EIN: {"revocation_date": str, "reinstatement_date": str, "exemption_type": str}}
    """
    revocations: Dict[str, Dict[str, str]] = {}
    count = 0

    for enc in ["utf-8", "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc, errors="replace") as fh:
                content = fh.read().replace("\r", "\n")
            break
        except UnicodeDecodeError:
            continue

    reader = csv.reader(content.split("\n"), delimiter=delimiter)
    idx = {name: i for i, name in enumerate(fieldnames)}

    for row in reader:
        if not row or len(row) < len(fieldnames):
            continue
        ein = normalize_ein(row[idx["EIN"]])
        if not ein:
            continue
        revocations[ein] = {
            "revocation_date": row[idx["REVOCATION_DATE"]].strip(),
            "revocation_posting_date": row[idx["REVOCATION_POSTING_DATE"]].strip(),
            "reinstatement_date": row[idx["EXEMPTION_REINSTATEMENT_DATE"]].strip(),
            "exemption_type": row[idx["EXEMPTION_TYPE"]].strip().upper(),
        }
        count += 1
        if count % 250000 == 0:
            logger.debug("  AutoRevocation: loaded %d records...", count)

    logger.info("AutoRevocation: %d revoked EINs loaded", len(revocations))
    return revocations


# ── EIN Utilities ──────────────────────────────────────────────────────────


def normalize_ein(ein: str) -> str:
    """Strip formatting and return 9-digit EIN, or empty string if invalid."""
    if not ein:
        return ""
    digits = "".join(ch for ch in str(ein) if ch.isdigit())
    return digits if len(digits) == 9 else ""


# ── Master CSV Operations ──────────────────────────────────────────────────


def load_master_orgs(master_path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """Load master_orgs.csv, return (fieldnames, rows)."""
    if not master_path.exists():
        logger.error("Master file not found: %s", master_path)
        sys.exit(1)
    with open(master_path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            logger.error("Empty master file: %s", master_path)
            sys.exit(1)
        fieldnames = list(reader.fieldnames)
        rows = [row for row in reader]
    logger.info("Master orgs loaded: %d records, columns: %s", len(rows), fieldnames)
    return fieldnames, rows


def ensure_columns(fieldnames: List[str], required: List[str]) -> List[str]:
    """Add any missing required columns to fieldnames list."""
    updated = list(fieldnames)
    for col in required:
        if col not in updated:
            updated.append(col)
            logger.info("Added missing column to master: %s", col)
    return updated


def save_master_orgs(master_path: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    """Atomically write updated master CSV."""
    tmp = master_path.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    shutil.move(str(tmp), str(master_path))
    logger.info("Master file updated: %s (%d rows)", master_path, len(rows))


# ── Verification Engine ────────────────────────────────────────────────────


def run_verification(
    fieldnames: List[str],
    rows: List[Dict[str, str]],
    pub78: Dict[str, Dict[str, str]],
    revocations: Dict[str, Dict[str, str]],
    dry_run: bool = False,
) -> Tuple[List[str], List[Dict[str, str]], Dict[str, int], List[Dict[str, str]]]:
    """
    Core verification logic:
      - EIN in AutoRevocation (no reinstatement)  -> "Revoked"
      - EIN in Pub78 + deductibility in verified  -> "Verified"
      - EIN in Pub78 + deductibility not verified -> "Unverified-Deductibility"
      - EIN NOT in Pub78                          -> "Unverified-Deductibility"
      - EIN missing/malformed                     -> "Error-Invalid-EIN"

    Returns: (updated_fieldnames, updated_rows, summary_counts, detail_report_rows)
    """
    fieldnames = ensure_columns(fieldnames, [
        "record_status",
        "pub78_verified_date",
        "irs_revocation_date",
        "irs_reinstatement_date",
        "irs_deductibility_code",
        "irs_exemption_type",
    ])

    updated_rows: List[Dict[str, str]] = []
    detail_rows: List[Dict[str, str]] = []
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    counts = {
        "total": len(rows),
        "verified": 0,
        "revoked": 0,
        "reinstated": 0,
        "unverified": 0,
        "errors": 0,
        "unchanged": 0,
    }

    for idx, row in enumerate(rows, 1):
        raw_ein = row.get("EIN", row.get("ein", ""))
        ein = normalize_ein(raw_ein)
        org_name = row.get("organization_name", row.get("name", row.get("NAME", f"Row-{idx}")))

        if not ein:
            row["record_status"] = "Error-Invalid-EIN"
            counts["errors"] += 1
            updated_rows.append(row)
            detail_rows.append({
                "row": idx,
                "ein": raw_ein or "MISSING",
                "organization_name": org_name,
                "previous_status": row.get("record_status", ""),
                "new_status": "Error-Invalid-EIN",
                "reason": "EIN missing or malformed",
            })
            continue

        prev_status = row.get("record_status", "")
        new_status = prev_status
        reason = "No change"
        revocation_date = ""
        reinstatement_date = ""
        deduct_code = ""
        exempt_type = ""

        # Priority 1: Check Auto-Revocation list
        if ein in revocations:
            rev_info = revocations[ein]
            revocation_date = rev_info.get("revocation_date", "")
            reinstatement_date = rev_info.get("reinstatement_date", "")
            exempt_type = rev_info.get("exemption_type", "")

            if reinstatement_date:
                # Has been reinstated - check Pub78
                new_status = "Reinstated"
                counts["reinstated"] += 1
                reason = f"Auto-Revoked but reinstated on {reinstatement_date}"
            else:
                new_status = "Revoked"
                counts["revoked"] += 1
                reason = f"Auto-Revocation (date: {revocation_date})"

        # Priority 2: Check Pub78 deductibility (only if not revoked)
        if ein in pub78:
            pub_info = pub78[ein]
            deduct = pub_info.get("deductibility", "").strip().upper()
            deduct_code = deduct

            if deduct in DEDUCTIBILITY_VERIFIED_CODES:
                if new_status not in ("Revoked",):
                    new_status = "Verified"
                    row["pub78_verified_date"] = now_iso
                    counts["verified"] += 1
                    reason = f"Pub78 match: deductibility={deduct}"
            else:
                if new_status not in ("Revoked",):
                    new_status = "Unverified-Deductibility"
                    counts["unverified"] += 1
                    reason = f"Pub78 found but deductibility={deduct} (required: one of {DEDUCTIBILITY_VERIFIED_CODES})"

        # Priority 3: Not found in Pub78 and not revoked
        elif ein not in revocations:
            new_status = "Unverified-Deductibility"
            counts["unverified"] += 1
            reason = "EIN not found in IRS Publication 78"

        # Apply updates
        row["record_status"] = new_status
        if revocation_date:
            row["irs_revocation_date"] = revocation_date
        if reinstatement_date:
            row["irs_reinstatement_date"] = reinstatement_date
        if deduct_code:
            row["irs_deductibility_code"] = deduct_code
        if exempt_type:
            row["irs_exemption_type"] = exempt_type

        if new_status == prev_status:
            counts["unchanged"] += 1

        updated_rows.append(row)
        detail_rows.append({
            "row": idx,
            "ein": ein,
            "organization_name": org_name,
            "previous_status": prev_status,
            "new_status": new_status,
            "reason": reason,
        })

    return fieldnames, updated_rows, counts, detail_rows


# ── Report Generation ──────────────────────────────────────────────────────


def generate_weekly_report(
    detail_rows: List[Dict[str, str]],
    counts: Dict[str, int],
    reports_dir: Path,
    dry_run: bool = False,
) -> Path:
    """Generate timestamped verification report CSV."""
    date_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"verification_weekly_{date_tag}.csv"

    if dry_run:
        logger.info("[DRY-RUN] Would write report to %s", report_path)
        return report_path

    # Summary header rows
    report_rows: List[Dict[str, str]] = []
    report_rows.append({
        "row": "",
        "ein": "",
        "organization_name": "=== MERIT IRS WEEKLY VERIFICATION REPORT ===",
        "previous_status": "",
        "new_status": "",
        "reason": "",
    })
    report_rows.append({
        "row": "",
        "ein": "Report Date",
        "organization_name": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "previous_status": "",
        "new_status": "",
        "reason": "",
    })
    report_rows.append({
        "row": "",
        "ein": "---",
        "organization_name": "---",
        "previous_status": "---",
        "new_status": "---",
        "reason": "---",
    })
    report_rows.append({
        "row": "",
        "ein": "TOTAL",
        "organization_name": str(counts["total"]),
        "previous_status": "",
        "new_status": "",
        "reason": "Total records processed",
    })
    report_rows.append({
        "row": "",
        "ein": "VERIFIED",
        "organization_name": str(counts["verified"]),
        "previous_status": "",
        "new_status": "",
        "reason": f"Pub78 match (deductibility in {DEDUCTIBILITY_VERIFIED_CODES})",
    })
    report_rows.append({
        "row": "",
        "ein": "REVOKED",
        "organization_name": str(counts["revoked"]),
        "previous_status": "",
        "new_status": "",
        "reason": "Auto-Revocation list (no reinstatement)",
    })
    report_rows.append({
        "row": "",
        "ein": "REINSTATED",
        "organization_name": str(counts["reinstated"]),
        "previous_status": "",
        "new_status": "",
        "reason": "Auto-Revoked but later reinstated",
    })
    report_rows.append({
        "row": "",
        "ein": "UNVERIFIED",
        "organization_name": str(counts["unverified"]),
        "previous_status": "",
        "new_status": "",
        "reason": "Not in Pub78 or failed deductibility check",
    })
    report_rows.append({
        "row": "",
        "ein": "ERRORS",
        "organization_name": str(counts["errors"]),
        "previous_status": "",
        "new_status": "",
        "reason": "Invalid/missing EIN",
    })
    report_rows.append({
        "row": "",
        "ein": "UNCHANGED",
        "organization_name": str(counts["unchanged"]),
        "previous_status": "",
        "new_status": "",
        "reason": "Status unchanged from previous run",
    })
    report_rows.append({
        "row": "",
        "ein": "---",
        "organization_name": "---",
        "previous_status": "---",
        "new_status": "---",
        "reason": "---",
    })
    report_rows.append({
        "row": "",
        "ein": "",
        "organization_name": "=== DETAIL RECORDS ===",
        "previous_status": "",
        "new_status": "",
        "reason": "",
    })
    report_rows.extend(detail_rows)

    fieldnames = ["row", "ein", "organization_name", "previous_status", "new_status", "reason"]
    with open(report_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report_rows)

    logger.info("Weekly report written: %s", report_path)
    return report_path


# ── Archive Management ─────────────────────────────────────────────────────


def archive_downloaded_files(paths: Paths, max_age_days: int = 90) -> None:
    """Archive this week's downloaded files and clean up old archives."""
    date_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
    for key, source in IRS_SOURCES.items():
        src = paths.base / source["filename"]
        if src.exists():
            archived = paths.archive / f"{source['filename'].replace('.zip', '')}_{date_tag}.zip"
            shutil.copy2(str(src), str(archived))
            logger.debug("Archived %s -> %s", src.name, archived.name)

    # Clean old archives
    cutoff = datetime.now(timezone.utc).timestamp() - (max_age_days * 86400)
    count = 0
    for f in paths.archive.glob("*.zip"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            count += 1
    if count:
        logger.info("Cleaned up %d archived files older than %d days", count, max_age_days)


# ── Main Entry Point ───────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="IRS Authority & Verification Agent v2.0")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without modifying master CSV")
    parser.add_argument("--force-download", action="store_true", help="Force re-download even if files exist")
    parser.add_argument("--master-csv", type=str, default=None, help="Override path to master_orgs.csv")
    parser.add_argument("--output-dir", type=str, default=None, help="Override base IRS data directory")
    parser.add_argument("--reports-dir", type=str, default=None, help="Override reports output directory")
    parser.add_argument("--timeout", type=int, default=300, help="HTTP download timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=3, help="Max HTTP retry attempts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-archive", action="store_true", help="Skip file archiving")
    args = parser.parse_args()

    setup_logging(args.verbose)
    paths = Paths(base_dir=args.output_dir, master_csv=args.master_csv, reports_dir=args.reports_dir)
    paths.ensure_dirs()

    logger.info("=" * 60)
    logger.info("IRS Authority & Verification Agent v2.0")
    logger.info("Run started: %s", datetime.now(timezone.utc).isoformat())
    logger.info("Dry-run: %s", args.dry_run)
    logger.info("Sources: Pub78, AutoRevocation (pipe-delimited TEOS format)")
    logger.info("=" * 60)

    # ── Step 1: Load master_orgs.csv ───────────────────────────────────────
    fieldnames, master_rows = load_master_orgs(paths.master_csv)

    # ── Step 2: Download IRS sources ───────────────────────────────────────
    session = create_session(timeout=args.timeout, max_retries=args.max_retries)
    downloaded_files: Dict[str, Path] = {}

    for key, source in IRS_SOURCES.items():
        dest = paths.base / source["filename"]
        success, checksum = download_file(
            session, source["url"], dest, args.timeout, force=args.force_download
        )
        if success:
            downloaded_files[key] = dest
        else:
            if dest.exists():
                logger.warning("Using existing cached file for %s: %s", key, dest)
                downloaded_files[key] = dest
            else:
                logger.error("Failed to download %s and no cache exists. Aborting.", key)
                return 1

    # ── Step 3: Extract and parse ──────────────────────────────────────────
    pub78_data: Dict[str, Dict[str, str]] = {}
    revocation_data: Dict[str, Dict[str, str]] = {}

    if "pub78" in downloaded_files:
        target = extract_target_from_zip(
            downloaded_files["pub78"], IRS_SOURCES["pub78"]["extracted_name"], paths.tmp
        )
        if target:
            pub78_data = load_pub78_records(
                target,
                fieldnames=IRS_SOURCES["pub78"]["fieldnames"],
                delimiter=IRS_SOURCES["pub78"]["delimiter"],
            )
        else:
            logger.error("No .txt file found in Pub78 ZIP")
            return 1

    if "autorevocation" in downloaded_files:
        target = extract_target_from_zip(
            downloaded_files["autorevocation"], IRS_SOURCES["autorevocation"]["extracted_name"], paths.tmp
        )
        if target:
            revocation_data = load_revocation_records(
                target,
                fieldnames=IRS_SOURCES["autorevocation"]["fieldnames"],
                delimiter=IRS_SOURCES["autorevocation"]["delimiter"],
            )
        else:
            logger.error("No .txt file found in AutoRevocation ZIP")
            return 1

    # ── Step 4: Run verification ───────────────────────────────────────────
    updated_fieldnames, updated_rows, counts, detail_rows = run_verification(
        fieldnames, master_rows, pub78_data, revocation_data, dry_run=args.dry_run
    )

    # ── Step 5: Save updated master ────────────────────────────────────────
    if not args.dry_run:
        save_master_orgs(paths.master_csv, updated_fieldnames, updated_rows)
    else:
        logger.info("[DRY-RUN] Master CSV NOT modified")

    # ── Step 6: Archive files ──────────────────────────────────────────────
    if not args.no_archive and not args.dry_run:
        archive_downloaded_files(paths)

    # ── Step 7: Generate report ────────────────────────────────────────────
    report_path = generate_weekly_report(detail_rows, counts, paths.reports, dry_run=args.dry_run)

    # ── Summary ────────────────────────────────────────────────────────────
    logger.info("-" * 40)
    logger.info("VERIFICATION COMPLETE")
    logger.info("  Total records processed : %d", counts["total"])
    logger.info("  Verified (Pub78 match)  : %d", counts["verified"])
    logger.info("  Revoked (Auto-Revoke)   : %d", counts["revoked"])
    logger.info("  Reinstated              : %d", counts["reinstated"])
    logger.info("  Unverified              : %d", counts["unverified"])
    logger.info("  Errors (bad EIN)        : %d", counts["errors"])
    logger.info("  Unchanged               : %d", counts["unchanged"])
    logger.info("  Report file             : %s", report_path)
    logger.info("-" * 40)

    # Cleanup tmp
    shutil.rmtree(paths.tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
