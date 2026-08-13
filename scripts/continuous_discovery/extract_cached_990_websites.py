#!/usr/bin/env python3
"""Stage self-reported websites from locally cached IRS Form 990 XML files.

The filer supplies WebsiteAddressTxt in a public filing.  The filing EIN must
match a currently website-less registry record.  This script only writes to the
website discovery staging table; it never updates registry_enriched.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "merit_registry.db"
XML_ROOT = ROOT / "data" / "xml"
WEBSITE_RE = re.compile(r"<WebsiteAddressTxt>(.*?)</WebsiteAddressTxt>", re.IGNORECASE | re.DOTALL)
EIN_RE = re.compile(r"<EIN>(\d{9})</EIN>", re.IGNORECASE)
NULL_TOKENS = {"", "N/A", "NA", "NONE", "NO", "NO WEBSITE", "0", "-", "--", "TBD"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_website(raw: str | None) -> str | None:
    if not raw:
        return None
    value = html.unescape(raw).strip().strip('"').rstrip(".,;")
    if value.upper() in NULL_TOKENS:
        return None
    value = value.split()[0]
    if not value.lower().startswith(("http://", "https://")):
        value = "https://" + value
    parsed = urlparse(value)
    if not parsed.netloc or "." not in parsed.netloc or any(char in value for char in "<>\"'"):
        return None
    return value


def extract(path: Path) -> tuple[str, str | None, str] | None:
    try:
        payload = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    ein_match = EIN_RE.search(payload)
    website_match = WEBSITE_RE.search(payload)
    if not ein_match or not website_match:
        return None
    return ein_match.group(1), normalize_website(website_match.group(1)), str(path.relative_to(ROOT))


def missing_orgs(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT EIN, organization_name, CITY, STATE
        FROM registry_enriched
        WHERE COALESCE(website, '') = ''
          AND COALESCE(org_status, 'active') = 'active'
        """
    ).fetchall()
    return {str(row["EIN"]).zfill(9): row for row in rows}


def run(workers: int, limit: int | None, dry_run: bool) -> dict[str, int | str]:
    paths = list(XML_ROOT.rglob("*.xml"))
    if limit:
        paths = paths[:limit]
    run_id = "irs_990_cached_xml_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    totals: dict[str, int | str] = {
        "run_id": run_id,
        "xml_files": len(paths),
        "filings_with_site": 0,
        "matching_missing_orgs": 0,
        "staged": 0,
    }
    with sqlite3.connect(DB_PATH) as conn:
        orgs = missing_orgs(conn)
        candidates: dict[str, tuple[sqlite3.Row, str, str]] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for result in pool.map(extract, paths):
                if not result:
                    continue
                ein, website, relative_path = result
                if not website:
                    continue
                totals["filings_with_site"] += 1
                org = orgs.get(ein)
                if org and ein not in candidates:
                    candidates[ein] = (org, website, relative_path)
        totals["matching_missing_orgs"] = len(candidates)
        if dry_run:
            return totals
        for ein, (org, website, relative_path) in candidates.items():
            domain = urlparse(website).netloc.lower().removeprefix("www.")
            notes = json.dumps(
                {
                    "source": "IRS Form 990 e-file XML",
                    "cached_xml_path": relative_path,
                    "match_rule": "filing_ein_equals_registry_ein",
                    "live_url_check": "not_performed",
                },
                sort_keys=True,
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO website_discovery_candidates (
                    run_id, ein, organization_name, city, state, candidate_domain, final_url,
                    verification_status, confidence, nonprofit_signal_count, identity_match_score,
                    identity_match_level, title, description, content_preview, source, notes, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'candidate_self_reported', 99, 1, 1.0, 'ein_exact', NULL, 'IRS Form 990 self-reported website', NULL, 'irs_990_cached_xml', ?, ?)
                """,
                (run_id, ein, org["organization_name"], org["CITY"], org["STATE"], domain, website, notes, now_iso()),
            )
            totals["staged"] += 1
        conn.commit()
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.workers, args.limit, args.dry_run), sort_keys=True))


if __name__ == "__main__":
    main()
