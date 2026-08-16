#!/usr/bin/env python3
"""
Validate Track B functional-expense recovery against ProPublica Nonprofit Explorer.

This is a read-only validation script. It never writes to SQLite or alters
donor-facing data. It samples exactly 96 accepted filings:

  4 registry_enriched.total_revenue bands
  x 2 filing-age strata (the latest two tax years present vs. older)
  x 12 accepted filings per cell.

Dry run (default) prints the deterministic sample manifest without HTTP requests.
--apply performs the 96 live ProPublica API checks and prints the review report.

Drafted by Codex (codex exec -s read-only) 2026-08-16, resuming the stratified
spot-check Track B's original plan called for (see DECISIONS.md 2026-08-16,
"Track B/C consolidation scoped"). The pilot (30 orgs, 93.3% reconciliation)
only checked internal Part IX arithmetic consistency, not agreement against
an independent source -- this does that second check.

Usage:
    python3 scripts/discovery/validate_990_expense_recovery.py --dry-run
    python3 scripts/discovery/validate_990_expense_recovery.py --apply

The API is queried sequentially with a two-second interval, following the
2026-07-18 crawler-etiquette convention. Cross-source comparisons require
exact whole-dollar equality. The $1 component-sum tolerance used during XML
extraction is deliberately not used here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "merit_registry.db"

API_BASE = "https://projects.propublica.org/nonprofits/api/v2/organizations"
USER_AGENT = "Daanaa-990-Expense-Validation/1.0 (+https://daanaa.org)"
REQUEST_INTERVAL_SECONDS = 2.0  # 2026-07-18 crawler-etiquette convention
REQUEST_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 3
INITIAL_429_BACKOFF_SECONDS = 60
SAMPLE_PER_CELL = 12
SAMPLE_SEED = "track-b-propublica-spot-check-2026-08-16"

LOCAL_FIELDS = (
    "total_amt",
    "program_services_amt",
    "management_general_amt",
    "fundraising_amt",
)

# ProPublica has used slightly different names across API exports. The canonical
# current names are listed first; aliases make an API field rename visible in the
# report as a missing-field discrepancy rather than silently treating it as zero.
PROPUBLICA_FIELDS = {
    "total_amt": (
        "totfuncexpns",
        "total_expenses",
    ),
    "program_services_amt": (
        "totprgmserviceexp",
        "program_services_expenses",
        "program_expenses",
    ),
    "management_general_amt": (
        "mgmtandgeneralexpns",
        "management_and_general_expenses",
        "management_expenses",
    ),
    "fundraising_amt": (
        "fundraisingexpns",
        "fundraising_expenses",
    ),
}


@dataclass(frozen=True)
class Filing:
    ein: str
    tax_year: int
    object_id: str | None
    total_revenue: float
    revenue_band: str
    age_stratum: str
    local: dict[str, Any]


class PoliteClient:
    """Single-threaded ProPublica client with identified UA and shared cadence."""

    def __init__(self) -> None:
        self._last_request_at = 0.0

    def _wait_for_slot(self) -> None:
        remaining = REQUEST_INTERVAL_SECONDS - (time.monotonic() - self._last_request_at)
        if remaining > 0:
            time.sleep(remaining)

    def get_json(self, ein: str) -> tuple[dict[str, Any] | None, str | None]:
        url = f"{API_BASE}/{ein}.json"

        for attempt in range(1, MAX_ATTEMPTS + 1):
            self._wait_for_slot()
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                },
            )
            self._last_request_at = time.monotonic()

            try:
                with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                    return json.load(response), None
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    return None, "propublica_org_not_found"
                if exc.code == 429 and attempt < MAX_ATTEMPTS:
                    backoff = INITIAL_429_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    print(
                        f"  EIN {ein}: ProPublica returned 429; "
                        f"waiting {backoff}s before retry {attempt + 1}/{MAX_ATTEMPTS}.",
                        file=sys.stderr,
                    )
                    time.sleep(backoff)
                    continue
                return None, f"http_{exc.code}"
            except urllib.error.URLError as exc:
                return None, f"network_error:{exc.reason}"
            except json.JSONDecodeError:
                return None, "malformed_json"

        return None, "request_attempts_exhausted"


def readonly_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def latest_two_tax_years(conn: sqlite3.Connection) -> tuple[int, int]:
    rows = conn.execute(
        """
        SELECT DISTINCT tax_year
        FROM irs_990_functional_expense_filings
        WHERE validation_status = 'accepted'
          AND tax_year IS NOT NULL
        ORDER BY tax_year DESC
        LIMIT 2
        """
    ).fetchall()
    if len(rows) != 2:
        raise RuntimeError(
            "Need at least two distinct tax years among accepted functional-expense filings."
        )
    return int(rows[0][0]), int(rows[1][0])


def revenue_band(total_revenue: float) -> str:
    if total_revenue < 250_000:
        return "<$250k"
    if total_revenue < 1_000_000:
        return "$250k-$1m"
    if total_revenue < 10_000_000:
        return "$1m-$10m"
    return ">$10m"


def filing_age_stratum(tax_year: int, latest_years: tuple[int, int]) -> str:
    return "latest_two_tax_years" if tax_year in latest_years else "older"


def stable_sample_key(filing: Filing) -> str:
    payload = "|".join(
        (
            SAMPLE_SEED,
            filing.revenue_band,
            filing.age_stratum,
            filing.ein,
            str(filing.tax_year),
            filing.object_id or "",
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_sample(conn: sqlite3.Connection) -> tuple[list[Filing], tuple[int, int], dict[tuple[str, str], int]]:
    latest_years = latest_two_tax_years(conn)
    rows = conn.execute(
        """
        SELECT
            f.EIN,
            f.tax_year,
            f.object_id,
            f.total_amt,
            f.program_services_amt,
            f.management_general_amt,
            f.fundraising_amt,
            r.total_revenue
        FROM irs_990_functional_expense_filings AS f
        JOIN registry_enriched AS r
          ON r.EIN = f.EIN
        WHERE f.validation_status = 'accepted'
          AND f.tax_year IS NOT NULL
          AND r.total_revenue IS NOT NULL
          AND r.total_revenue >= 0
        """
    ).fetchall()

    cells: dict[tuple[str, str], list[Filing]] = {}
    for row in rows:
        revenue = float(row[7])
        filing = Filing(
            ein=str(row[0]).zfill(9),
            tax_year=int(row[1]),
            object_id=row[2],
            total_revenue=revenue,
            revenue_band=revenue_band(revenue),
            age_stratum=filing_age_stratum(int(row[1]), latest_years),
            local={
                "total_amt": row[3],
                "program_services_amt": row[4],
                "management_general_amt": row[5],
                "fundraising_amt": row[6],
            },
        )
        cells.setdefault((filing.revenue_band, filing.age_stratum), []).append(filing)

    band_order = ("<$250k", "$250k-$1m", "$1m-$10m", ">$10m")
    age_order = ("latest_two_tax_years", "older")
    shortages: dict[tuple[str, str], int] = {}
    sample: list[Filing] = []

    for band in band_order:
        for age in age_order:
            cell = (band, age)
            candidates = sorted(cells.get(cell, []), key=stable_sample_key)
            if len(candidates) < SAMPLE_PER_CELL:
                shortages[cell] = len(candidates)
                continue
            sample.extend(candidates[:SAMPLE_PER_CELL])

    if shortages:
        detail = ", ".join(
            f"{band} / {age}: {count} available"
            for (band, age), count in shortages.items()
        )
        raise RuntimeError(
            f"Cannot form the required 96-filing stratified sample; {detail}."
        )

    return sample, latest_years, {cell: len(items) for cell, items in cells.items()}


def whole_dollars(value: Any) -> int | None:
    """Return an exact dollar integer; None for absent or fractional data."""
    if value is None or value == "":
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not amount.is_finite() or amount != amount.to_integral_value():
        return None
    return int(amount)


def first_present(record: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for field in aliases:
        if field in record and record[field] not in (None, ""):
            return record[field]
    return None


def matching_propublica_filing(
    payload: dict[str, Any],
    tax_year: int,
) -> tuple[dict[str, Any] | None, str | None]:
    filings = payload.get("filings_with_data") or payload.get("filings") or []
    matches: list[dict[str, Any]] = []

    for filing in filings:
        try:
            year = int(filing.get("tax_prd_yr"))
        except (TypeError, ValueError):
            continue
        if year == tax_year:
            matches.append(filing)

    if len(matches) == 1:
        return matches[0], None
    if not matches:
        available = sorted(
            {
                int(f["tax_prd_yr"])
                for f in filings
                if str(f.get("tax_prd_yr", "")).isdigit()
            },
            reverse=True,
        )
        if available:
            return None, f"no_matching_tax_year; available={available}"
        return None, "no_propublica_filings_with_year"
    return None, f"ambiguous_propublica_tax_year; matches={len(matches)}"


def extract_propublica_amounts(filing: dict[str, Any]) -> dict[str, Any]:
    return {
        local_name: first_present(filing, aliases)
        for local_name, aliases in PROPUBLICA_FIELDS.items()
    }


def classify_hint(
    local: dict[str, Any],
    remote: dict[str, Any] | None,
    match_issue: str | None,
) -> str:
    if match_issue:
        if match_issue.startswith("no_matching_tax_year"):
            return "wrong filing year matched"
        return "other"

    assert remote is not None
    if any(whole_dollars(local[field]) is None for field in LOCAL_FIELDS):
        return "XML-shape issue"
    if any(whole_dollars(remote[field]) is None for field in LOCAL_FIELDS):
        return "missing field"
    return "other"


def format_value(value: Any) -> str:
    amount = whole_dollars(value)
    return "missing/non-whole-dollar" if amount is None else f"${amount:,.0f}"


def print_manifest(
    sample: list[Filing],
    latest_years: tuple[int, int],
    availability: dict[tuple[str, str], int],
) -> None:
    print("Track B ProPublica validation — dry-run sample manifest")
    print(f"Latest-two-tax-years stratum: {latest_years[0]}, {latest_years[1]}")
    print(f"Sample seed: {SAMPLE_SEED}")
    print("No HTTP requests and no database writes were performed.\n")

    for cell, count in sorted(availability.items()):
        print(f"Available: {cell[0]:>10} | {cell[1]:>20}: {count:,}")

    print("\nSelected filings:")
    for filing in sample:
        print(
            f"{filing.revenue_band:>10} | {filing.age_stratum:>20} | "
            f"{filing.ein} | FY{filing.tax_year} | object_id={filing.object_id or '-'}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Perform the live, read-only ProPublica spot-check requests.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the deterministic 96-filing manifest only (default).",
    )
    args = parser.parse_args()

    try:
        with readonly_connection() as conn:
            sample, latest_years, availability = load_sample(conn)
    except (sqlite3.Error, FileNotFoundError, RuntimeError) as exc:
        print(f"Validation setup failed: {exc}", file=sys.stderr)
        return 1

    if not args.apply:
        print_manifest(sample, latest_years, availability)
        print("\nDry run -- no ProPublica requests made. Re-run with --apply to validate.")
        return 0

    print("Track B ProPublica validation — live read-only report")
    print(f"Sample: {len(sample)} filings; latest-two-tax-years={latest_years}")
    print(
        f"Cadence: one request every {REQUEST_INTERVAL_SECONDS:.0f}s; "
        f"database mode: read-only.\n"
    )

    client = PoliteClient()
    exact_agreements = 0
    comparable = 0
    discrepancies: list[dict[str, Any]] = []
    outcome_counts: Counter[str] = Counter()

    for index, sampled in enumerate(sample, start=1):
        print(
            f"[{index:02d}/{len(sample)}] {sampled.ein} FY{sampled.tax_year} "
            f"({sampled.revenue_band}, {sampled.age_stratum})",
            file=sys.stderr,
        )
        payload, fetch_issue = client.get_json(sampled.ein)

        remote: dict[str, Any] | None = None
        match_issue: str | None = fetch_issue
        if payload is not None:
            pp_filing, match_issue = matching_propublica_filing(payload, sampled.tax_year)
            if pp_filing is not None:
                remote = extract_propublica_amounts(pp_filing)

        if remote is not None and all(
            whole_dollars(sampled.local[field]) is not None
            and whole_dollars(remote[field]) is not None
            for field in LOCAL_FIELDS
        ):
            comparable += 1
            field_matches = {
                field: whole_dollars(sampled.local[field]) == whole_dollars(remote[field])
                for field in LOCAL_FIELDS
            }
            if all(field_matches.values()):
                exact_agreements += 1
                outcome_counts["exact_agreement"] += 1
                continue
            outcome_counts["value_disagreement"] += 1
        else:
            outcome_counts["unresolved"] += 1

        discrepancies.append(
            {
                "filing": sampled,
                "remote": remote,
                "issue": match_issue,
                "hint": classify_hint(sampled.local, remote, match_issue),
            }
        )

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"Sampled accepted filings:                 {len(sample)}")
    print(f"Comparable exact-dollar filings:          {comparable}")
    print(f"Exact agreements:                         {exact_agreements}")
    print(
        f"Overall agreement rate (all sampled):     "
        f"{100 * exact_agreements / len(sample):.1f}%"
    )
    print(
        f"Agreement rate (comparable filings only): "
        f"{100 * exact_agreements / comparable:.1f}%"
        if comparable
        else "Agreement rate (comparable filings only): n/a"
    )
    print(f"Discrepancies / unresolved cases:         {len(discrepancies)}")
    for name, count in sorted(outcome_counts.items()):
        print(f"  {name}: {count}")

    if not discrepancies:
        print("\nNo discrepancies found.")
        return 0

    print("\n" + "=" * 78)
    print("DISCREPANCIES FOR HUMAN REVIEW")
    print("=" * 78)

    for item in discrepancies:
        filing: Filing = item["filing"]
        remote = item["remote"]
        print(
            f"\nEIN {filing.ein} | FY{filing.tax_year} | "
            f"{filing.revenue_band} | {filing.age_stratum}"
        )
        print(f"Review hint: {item['hint']}")
        if item["issue"]:
            print(f"ProPublica matching/fetch note: {item['issue']}")

        print(f"{'Field':<28} {'Stored XML value':>22} {'ProPublica value':>22}")
        print("-" * 76)
        for field in LOCAL_FIELDS:
            pp_value = remote[field] if remote is not None else None
            print(
                f"{field:<28} "
                f"{format_value(filing.local[field]):>22} "
                f"{format_value(pp_value):>22}"
            )

    print(
        "\nClassification hints are triage only. This script does not alter "
        "filings, resolve discrepancies, or promote expense data."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
