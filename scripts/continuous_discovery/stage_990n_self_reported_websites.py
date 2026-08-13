#!/usr/bin/env python3
"""Bulk-stage EIN-keyed websites from the local IRS Form 990-N data file.

The e-Postcard data includes a Website column entered by the filer.  This
extractor retains the most recent filing for each EIN and writes only the
discovery-candidate staging table. It never changes registry_enriched.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "merit_registry.db"
SOURCE_PATH = ROOT / "data" / "csv" / "postcard_filers.csv"
REJECTED_DOMAINS = {"etax990n.com", "irs.gov", "www.irs.gov"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_website(value: str | None) -> str | None:
    value = (value or "").strip().strip('"')
    if not value or "@" in value or " " in value:
        return None
    if not value.lower().startswith(("http://", "https://")):
        value = "https://" + value
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    domain = parsed.netloc.lower().removeprefix("www.")
    if not domain or "." not in domain or domain in REJECTED_DOMAINS:
        return None
    return value


def newest_filing_by_ein() -> tuple[dict[str, tuple[int, str]], int]:
    csv.field_size_limit(sys.maxsize)
    newest: dict[str, tuple[int, str]] = {}
    rows = 0
    with SOURCE_PATH.open(encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            rows += 1
            ein = (row.get("EIN") or "").zfill(9)
            website = normalize_website(row.get("Website"))
            if not website or not ein.isdigit():
                continue
            try:
                tax_year = int(row.get("Tax_Year") or 0)
            except ValueError:
                continue
            prior = newest.get(ein)
            if prior is None or tax_year > prior[0]:
                newest[ein] = (tax_year, website)
    return newest, rows


def run(dry_run: bool) -> dict[str, int | str]:
    run_id = "irs_990n_self_reported_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    newest, rows = newest_filing_by_ein()
    totals: dict[str, int | str] = {
        "run_id": run_id,
        "filing_rows": rows,
        "eins_with_usable_self_reported_website": len(newest),
        "matching_missing_orgs": 0,
        "staged": 0,
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        missing = {
            str(row["EIN"]).zfill(9): row
            for row in conn.execute(
                """
                SELECT EIN, organization_name, CITY, STATE
                FROM registry_enriched
                WHERE COALESCE(website, '') = ''
                  AND COALESCE(org_status, 'active') = 'active'
                """
            )
        }
        candidates = {ein: value for ein, value in newest.items() if ein in missing}
        totals["matching_missing_orgs"] = len(candidates)
        if dry_run:
            return totals
        for ein, (tax_year, website) in candidates.items():
            org = missing[ein]
            domain = urlparse(website).netloc.lower().removeprefix("www.")
            notes = json.dumps(
                {
                    "source": "IRS Form 990-N e-Postcard",
                    "filing_tax_year": tax_year,
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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'candidate_self_reported', 99, 1, 1.0, 'ein_exact', NULL, 'IRS Form 990-N self-reported website', NULL, 'irs_990n_self_reported', ?, ?)
                """,
                (run_id, ein, org["organization_name"], org["CITY"], org["STATE"], domain, website, notes, now_iso()),
            )
            totals["staged"] += 1
        conn.commit()
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.dry_run), sort_keys=True))


if __name__ == "__main__":
    main()
