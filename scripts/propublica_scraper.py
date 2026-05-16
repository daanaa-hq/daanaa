#!/usr/bin/env python3
"""
MERIT Worker A: ProPublica Bulk Data Collector
==============================================
Downloads full 990 filing histories for 501(c)(3) organizations via
ProPublica Nonprofit Explorer API v2.

Usage:
    python propublica_scraper.py --start 0 --limit 1000 --resume
    python propublica_scraper.py --state-filter CA --limit 500
    nohup python propublica_scraper.py --limit 10000 > scraper.log 2>&1 &
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

import requests

# ────────────────────────────────
# Configuration
# ────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "propublica"
CSV_DIR = BASE_DIR / "data" / "csv"
LOG_DIR = BASE_DIR / "data" / "logs"

MASTER_ORGS_CSV = CSV_DIR / "master_orgs.csv"
FINANCIALS_CSV = CSV_DIR / "financials_annual.csv"
ERROR_LOG = LOG_DIR / "propublica_errors.log"

API_BASE = "https://projects.propublica.org/nonprofits/api/v2"
RATE_LIMIT_DELAY = 0.25  # seconds between requests (max 4/sec, keep buffer)
MAX_RETRIES = 5
INITIAL_BACKOFF = 60  # seconds on HTTP 429

SEARCH_TERMS = [
    "foundation",
    "charity",
    "trust",
    "fund",
    "ministry",
    "coalition",
    "institute",
    "center",
    "association",
    "initiative",
    "project",
    "alliance",
    "endowment",
    "fellowship",
    "scholarship",
    "corporation",
    "society",
    "league",
    "council",
    "committee",
]

STATE_ABBREVIATIONS = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
]

# ────────────────────────────────
# Logging Setup
# ────────────────────────────────
def setup_logging(verbose: bool = False) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("propublica_scraper")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    file_handler = logging.FileHandler(ERROR_LOG, encoding="utf-8")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


LOG = setup_logging()

# ────────────────────────────────
# Rate-Limited HTTP Client
# ────────────────────────────────
class RateLimitedClient:
    """HTTP client with rate limiting and exponential backoff."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MERIT-WorkerA-ProPublica-Collector/1.0 (research@meritgiving.org)",
            "Accept": "application/json",
        })
        self.last_request_time: float = 0.0

    def _wait(self) -> None:
        """Enforce minimum delay between requests."""
        elapsed = time.monotonic() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.monotonic()

    def get(self, url: str, attempt: int = 1) -> Optional[requests.Response]:
        """GET with rate limiting and retry logic."""
        self._wait()
        try:
            resp = self.session.get(url, timeout=30)
        except requests.RequestException as exc:
            LOG.warning("Network error on %s: %s", url, exc)
            return None

        if resp.status_code == 429:
            backoff = INITIAL_BACKOFF * (2 ** (attempt - 1))
            LOG.warning("Rate limited (429). Backing off %ds…", backoff)
            time.sleep(backoff)
            if attempt < MAX_RETRIES:
                return self.get(url, attempt + 1)
            LOG.error("Max retries exceeded for %s after 429", url)
            return None

        if resp.status_code == 404:
            return resp  # Caller decides

        if resp.status_code != 200:
            LOG.warning("HTTP %d for %s", resp.status_code, url)
            return None

        return resp

    def close(self) -> None:
        self.session.close()


CLIENT = RateLimitedClient()


# ────────────────────────────────
# CSV Helpers
# ────────────────────────────────
ORG_COLUMNS = [
    "ein", "name", "city", "state", "zipcode",
    "subsection_code", "affiliation_code", "deductibility_code",
    "foundation_type", "ruling_date", "mission", "website",
    "first_seen", "last_updated",
]

FINANCIAL_COLUMNS = [
    "ein", "org_name", "tax_year", "tax_period",
    "form_type", "total_revenue_cents", "total_expenses_cents",
    "total_assets_cents", "contributions_cents",
    "program_expenses_cents", "fundraising_expenses_cents",
    "executive_compensation_cents", "pdf_url",
    "filing_date", "collected_at",
]


def load_csv_set(path: Path, key_col: str) -> set[str]:
    """Load a set of existing keys from a CSV for dedup/resume."""
    keys: set[str] = set()
    if not path.exists():
        return keys
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return keys
        for row in reader:
            val = row.get(key_col, "").strip()
            if val:
                keys.add(val)
    return keys


def append_or_create(path: Path, columns: list[str], rows: list[dict]) -> None:
    """Append rows to CSV; create with header if missing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def upsert_master_orgs(new_rows: list[dict]) -> None:
    """Upsert organizations into master_orgs.csv."""
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    if not new_rows:
        return

    existing: dict[str, dict] = {}
    if MASTER_ORGS_CSV.exists():
        with open(MASTER_ORGS_CSV, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ein = row.get("ein", "").strip()
                if ein:
                    existing[ein] = row

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    to_write: list[dict] = []
    for row in new_rows:
        ein = row.get("ein", "").strip()
        if not ein:
            continue
        if ein in existing:
            existing[ein].update(row)
            existing[ein]["last_updated"] = now
            to_write.append(existing[ein])
        else:
            row["first_seen"] = now
            row["last_updated"] = now
            existing[ein] = row
            to_write.append(row)

    with open(MASTER_ORGS_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ORG_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing.values())


# ────────────────────────────────
# JSON Persistence
# ────────────────────────────────
def save_raw_json(ein: str, data: dict, force: bool = False) -> bool:
    """Save raw org JSON; return True if written."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{ein}.json"
    if path.exists() and not force:
        return False
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return True


def save_failed_raw(ein: str, text: str) -> None:
    """Save unparsable response text for debugging."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"failed_{ein}.txt"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ────────────────────────────────
# Data Transformation
# ────────────────────────────────
def normalize_ein(ein: Any) -> str:
    """Strip dashes and pad to 9 digits."""
    s = re.sub(r"\D", "", str(ein))
    return s.zfill(9)[-9:]


def parse_date(raw: Optional[str]) -> str:
    """Convert ProPublica date strings to ISO YYYY-MM-DD."""
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%B %Y", "%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw.strip()


def dollars_to_cents(val: Any) -> int:
    """Convert dollar string/float to integer cents."""
    if val is None:
        return 0
    try:
        f = float(re.sub(r"[$,]", "", str(val)))
        return int(round(f * 100))
    except (ValueError, TypeError):
        return 0


def org_from_api(data: dict) -> dict:
    """Extract organization fields from API response."""
    org = data.get("organization", data)
    ein = normalize_ein(org.get("ein", org.get("EIN", "")))
    return {
        "ein": ein,
        "name": org.get("name", org.get("organization_name", "")).strip(),
        "city": org.get("city", "").strip(),
        "state": (org.get("state", org.get("State", "")) or "").strip().upper(),
        "zipcode": org.get("zipcode", org.get("ZIP", "")).strip(),
        "subsection_code": org.get("subsection_code", org.get("SUBSECTION", 3)),
        "affiliation_code": org.get("affiliation_code", org.get("AFFILIATION", 3)),
        "deductibility_code": org.get("deductibility_code", org.get("DEDUCTIBILITY", "PC")),
        "foundation_type": org.get("foundation_status", org.get("FOUNDATION", "Public Charity")),
        "ruling_date": parse_date(org.get("ruling_date", org.get("RULING_DATE", ""))),
        "mission": org.get("mission", org.get("Mission", "")).strip(),
        "website": org.get("website", "").strip(),
    }


def filings_from_api(data: dict) -> list[dict]:
    """Extract filing financials from API response."""
    filings: list[dict] = []
    raw_filings = data.get("filings_with_data", data.get("filings", []))
    org_name = data.get("organization", {}).get("name", "")
    ein = normalize_ein(data.get("organization", {}).get("ein", ""))

    for f in raw_filings:
        if isinstance(f, dict):
            tax_year = f.get("tax_prd_yr", f.get("tax_year", ""))
            tax_period = str(f.get("tax_prd", f.get("tax_period", "")))
            form_type = f.get("formtype", f.get("form_type", "990"))
            if isinstance(form_type, int):
                form_type = {0: "990", 1: "990EZ", 2: "990PF"}.get(form_type, "990")

            filings.append({
                "ein": ein,
                "org_name": org_name,
                "tax_year": tax_year,
                "tax_period": tax_period,
                "form_type": str(form_type).upper(),
                "total_revenue_cents": dollars_to_cents(f.get("totrevenue", f.get("total_revenue"))),
                "total_expenses_cents": dollars_to_cents(f.get("totfuncexpns", f.get("total_expenses"))),
                "total_assets_cents": dollars_to_cents(f.get("totassetsend", f.get("total_assets"))),
                "contributions_cents": dollars_to_cents(f.get("totcntrbs", f.get("contributions"))),
                "program_expenses_cents": dollars_to_cents(f.get("totprgmrevnue", f.get("program_expenses"))),
                "fundraising_expenses_cents": dollars_to_cents(f.get("lessdirfndrsng", f.get("fundraising_expenses"))),
                "executive_compensation_cents": dollars_to_cents(f.get("compnsatncurrofcr", f.get("executive_compensation"))),
                "pdf_url": f.get("pdf_url", ""),
                "filing_date": parse_date(str(f.get("filing_date", ""))),
                "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
    return filings


# ────────────────────────────────
# API Interaction
# ────────────────────────────────
def fetch_org(ein: str) -> Optional[dict]:
    """Fetch a single organization by EIN."""
    url = f"{API_BASE}/organizations/{ein}.json"
    resp = CLIENT.get(url)
    if resp is None:
        return None
    if resp.status_code == 404:
        LOG.info("EIN %s not found (404)", ein)
        return {"_error": 404, "ein": ein}
    try:
        return resp.json()
    except json.JSONDecodeError:
        LOG.warning("JSON decode failed for EIN %s", ein)
        save_failed_raw(ein, resp.text)
        return None


def search_orgs(term: str, page: int = 0) -> list[dict]:
    """Search organizations by term; return list of org dicts."""
    url = f"{API_BASE}/search.json?q={quote_plus(term)}&page={page}"
    resp = CLIENT.get(url)
    if resp is None:
        return []
    try:
        data = resp.json()
    except json.JSONDecodeError:
        LOG.warning("JSON decode failed for search: %s page %d", term, page)
        return []

    # ProPublica search returns organizations directly or under 'organizations'
    results = data.get("organizations", data if isinstance(data, list) else [])
    return [r for r in results if isinstance(r, dict)]


# ────────────────────────────────
# Core Pipeline
# ────────────────────────────────
def process_org(raw_data: dict, force: bool = False) -> bool:
    """Process and persist a single org + filings. Return True if new data saved."""
    if raw_data is None or raw_data.get("_error") == 404:
        return False

    org = org_from_api(raw_data)
    ein = org["ein"]
    if not ein or ein == "000000000":
        return False

    written = save_raw_json(ein, raw_data, force=force)
    upsert_master_orgs([org])

    filings = filings_from_api(raw_data)
    if filings:
        append_or_create(FINANCIALS_CSV, FINANCIAL_COLUMNS, filings)

    return written


def load_existing_eins() -> set[str]:
    """All EINs we already have raw JSON for (resume support)."""
    eins: set[str] = set()
    if not RAW_DIR.exists():
        return eins
    for p in RAW_DIR.glob("*.json"):
        if p.stem.startswith("failed_"):
            continue
        eins.add(p.stem)
    return eins


def load_master_eins() -> set[str]:
    """Load EINs from master CSV if it exists."""
    return load_csv_set(MASTER_ORGS_CSV, "ein")


def run_scraper(args: argparse.Namespace) -> None:
    LOG.info("═" * 60)
    LOG.info("MERIT Worker A — ProPublica Bulk Data Collector")
    LOG.info("Started: %s", datetime.now(timezone.utc).isoformat())
    LOG.info("═" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    existing = load_existing_eins()
    LOG.info("Existing raw files: %d", len(existing))

    master_eins = load_master_eins()
    LOG.info("EINs in master CSV: %d", len(master_eins))

    all_eins: list[str] = []

    # 1. Seed from master CSV
    if master_eins and not args.skip_master:
        all_eins.extend(sorted(master_eins))

    # 2. Expand via search terms
    search_queue: list[str] = []
    if args.search_terms:
        search_queue = [t.strip() for t in args.search_terms.split(",") if t.strip()]
    else:
        search_queue = SEARCH_TERMS.copy()

    if args.state_filter:
        # Prioritize state searches
        states = [s.strip().upper() for s in args.state_filter.split(",")]
        search_queue = states + [t for t in search_queue if t.upper() not in states]

    page_limit = max(1, getattr(args, "search_pages", 5))

    if not args.skip_search:
        LOG.info("Expanding via %d search term(s), up to %d pages each", len(search_queue), page_limit)
        for term in search_queue:
            LOG.info("Searching: %s", term)
            for page in range(page_limit):
                if len(all_eins) >= args.limit * 3:
                    break  # Enough buffer
                results = search_orgs(term, page)
                if not results:
                    break
                for org_hit in results:
                    ein = normalize_ein(org_hit.get("ein", org_hit.get("EIN", "")))
                    if ein and ein not in all_eins:
                        all_eins.append(ein)
                LOG.debug("  %s page %d → %d unique EINs so far", term, page, len(all_eins))

    # 3. Deduplicate and slice
    seen: set[str] = set()
    unique_eins: list[str] = []
    for e in all_eins[args.start :]:
        if e not in seen:
            seen.add(e)
            unique_eins.append(e)
        if len(unique_eins) >= args.limit:
            break

    LOG.info("Total unique EINs to process: %d", len(unique_eins))

    # 4. Process
    processed = skipped = failed = 0
    for idx, ein in enumerate(unique_eins, 1):
        if args.resume and not args.force and ein in existing:
            skipped += 1
            if idx % 500 == 0:
                LOG.info("[%d/%d] Skipped (exists): %s", idx, len(unique_eins), ein)
            continue

        LOG.debug("[%d/%d] Fetching %s", idx, len(unique_eins), ein)
        data = fetch_org(ein)
        if data is None:
            failed += 1
            LOG.warning("Failed to fetch EIN %s", ein)
            continue

        if data.get("_error") == 404:
            skipped += 1
            continue

        if process_org(data, force=args.force):
            processed += 1
        else:
            skipped += 1

        if idx % 100 == 0:
            LOG.info(
                "Progress: %d/%d | Processed: %d | Skipped: %d | Failed: %d",
                idx,
                len(unique_eins),
                processed,
                skipped,
                failed,
            )

    CLIENT.close()
    LOG.info("═" * 60)
    LOG.info("Done. Processed: %d | Skipped: %d | Failed: %d", processed, skipped, failed)
    LOG.info("Finished: %s", datetime.now(timezone.utc).isoformat())
    LOG.info("═" * 60)


# ────────────────────────────────
# CLI
# ────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MERIT Worker A: ProPublica Bulk 990 Data Collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resume from existing data, process up to 1000 orgs
  python propublica_scraper.py --limit 1000 --resume

  # Focus on California foundations only
  python propublica_scraper.py --state-filter CA --search-terms "foundation,charity"

  # Force re-download everything
  python propublica_scraper.py --limit 500 --force

  # Start from offset, skip search expansion
  python propublica_scraper.py --start 500 --limit 1000 --skip-search
        """,
    )
    parser.add_argument("--start", type=int, default=0, help="Start index in EIN list (default: 0)")
    parser.add_argument("--limit", type=int, default=1000, help="Max organizations to process (default: 1000)")
    parser.add_argument("--resume", action="store_true", help="Skip EINs already downloaded")
    parser.add_argument("--force", action="store_true", help="Re-download even if file exists")
    parser.add_argument("--state-filter", type=str, default="", help="Comma-separated state abbreviations to prioritize")
    parser.add_argument("--search-terms", type=str, default="", help="Override default search terms (comma-separated)")
    parser.add_argument("--search-pages", type=int, default=5, help="Max pages per search term (default: 5)")
    parser.add_argument("--skip-master", action="store_true", help="Ignore master_orgs.csv EINs")
    parser.add_argument("--skip-search", action="store_true", help="Skip search expansion; use master EINs only")
    parser.add_argument("--verbose", action="store_true", help="Debug-level logging")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        LOG.setLevel(logging.DEBUG)
        for h in LOG.handlers:
            h.setLevel(logging.DEBUG)

    try:
        run_scraper(args)
    except KeyboardInterrupt:
        LOG.info("Interrupted by user. Progress saved.")
        CLIENT.close()
        sys.exit(130)
    except Exception:
        LOG.exception("Fatal error in scraper")
        CLIENT.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
