#!/usr/bin/env python3
"""
scripts/ops/refresh_recent_filings_batch.py

Batch-mode version of fetch_irs_direct_filing.py -- built 2026-08-16 to close
the residual gap that single-org tool left: gt990's bulk index only rebuilds
every ~2-3 months, and downloading a ~500MB monthly IRS batch ZIP per org
doesn't scale to checking the whole registry one at a time.

Discovers Form 990 filings in the most recent IRS monthly XML batches,
downloads each unprocessed ZIP ONCE, extracts only the filings whose EINs
exist in registry_enriched (not the whole batch), and delegates every
database write to fetch_irs_direct_filing.write_filing() -- same
never-downgrade UPDATE predicate and functional-expense reconciliation rule
as the single-org tool, so behavior stays identical between the two.

Drafted by Codex (codex exec -s read-only), reviewed and wired against the
actual fetch_irs_direct_filing.py interface after that file was refactored
to expose iter_990_index_rows(), batch_zip_url(), parse_990_xml(), and
write_filing() as standalone functions.

Usage:
    python3 scripts/ops/refresh_recent_filings_batch.py
    python3 scripts/ops/refresh_recent_filings_batch.py --apply
    python3 scripts/ops/refresh_recent_filings_batch.py --months 6 --apply

The default is a dry run. --apply is required to write both the database and
the batch-completion state file.
"""

import argparse
import fcntl
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.ops import fetch_irs_direct_filing as direct


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = (
    REPO_ROOT / "data" / "ops_state" / "irs_direct_recent_filings_batches.json"
)
BATCH_ID_MONTH_RE = re.compile(r"^(?P<year>\d{4})_TEOS_XML_(?P<month>\d{2})[A-Z]?$")


class BatchProcessingError(RuntimeError):
    """The batch was not fully processed and must remain eligible for retry."""


def subtract_months(today: date, months: int) -> date:
    """Return the first day of the month containing the inclusive cutoff."""
    absolute_month = today.year * 12 + today.month - 1 - (months - 1)
    return date(absolute_month // 12, absolute_month % 12 + 1, 1)


def batch_month(batch_id: str) -> date | None:
    """Return the month encoded in an IRS XML_BATCH_ID, if recognizable."""
    match = BATCH_ID_MONTH_RE.match(batch_id)
    if not match:
        return None
    try:
        return date(int(match["year"]), int(match["month"]), 1)
    except ValueError:
        return None


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "batches": {}}

    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BatchProcessingError(
            f"State file is unreadable; refusing to re-download batches: {path}: {exc}"
        ) from exc

    if state.get("version") != 1 or not isinstance(state.get("batches"), dict):
        raise BatchProcessingError(f"Unexpected state-file format: {path}")
    return state


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def known_eins(db: sqlite3.Connection) -> set[str]:
    return {
        row[0].strip().zfill(9)
        for row in db.execute("SELECT EIN FROM registry_enriched")
        if row[0]
    }


def discover_recent_batches(
    submission_years: list[int],
    cutoff: date,
    registry_eins: set[str],
) -> dict[str, dict[str, dict]]:
    """
    Return {batch_id: {ein: filing}}.

    This deliberately reuses direct.iter_990_index_rows() rather than
    reimplementing the IRS index request and CSV parsing.
    """
    batches: dict[str, dict[str, dict]] = {}

    for row in direct.iter_990_index_rows(submission_years):
        if row.get("RETURN_TYPE", "").strip() != "990":
            continue

        ein = row.get("EIN", "").strip().zfill(9)
        batch_id = row.get("XML_BATCH_ID", "").strip()
        object_id = row.get("OBJECT_ID", "").strip()
        tax_period = row.get("TAX_PERIOD", "").strip()

        if ein not in registry_eins or not batch_id or not object_id or not tax_period:
            continue

        release_month = batch_month(batch_id)
        if release_month is None:
            print(f"Skipping unrecognized XML_BATCH_ID: {batch_id}", file=sys.stderr)
            continue
        if release_month < cutoff:
            continue

        filing = {
            "tax_period": tax_period,
            "object_id": object_id,
            "batch_id": batch_id,
        }
        filings_for_batch = batches.setdefault(batch_id, {})

        # Match the single-org script's newest-tax-period behavior. Equal tax
        # periods retain the first index row encountered, as find_latest_filing()
        # does today.
        previous = filings_for_batch.get(ein)
        if previous is None or filing["tax_period"] > previous["tax_period"]:
            filings_for_batch[ein] = filing

    return batches


def download_batch(zip_url: str, destination: Path) -> None:
    """Download a ZIP once, using the direct script's requests dependency."""
    print(f"Downloading {zip_url} ...")
    response = direct.requests.get(zip_url, timeout=600, stream=True)
    response.raise_for_status()

    with destination.open("wb") as output:
        for chunk in response.iter_content(chunk_size=1 << 20):
            if chunk:
                output.write(chunk)


EXTRACT_CHUNK_SIZE = 5000


def extract_requested_xmls(
    zip_path: Path,
    extract_dir: Path,
    filings: dict[str, dict],
) -> None:
    """
    Extract the requested XML members, batched into a handful of unzip calls.

    IRS ZIPs use a compression method unsupported by Python's zipfile module;
    this preserves the direct script's use of command-line unzip. The Debian
    "UnZip 6.00" build actually installed here does NOT support "-@" to read
    a member list from stdin (verified: it silently treats "-@" as a literal
    filename argument and reports it unmatched) -- member names must be
    passed as positional args, and they must come right after the zip
    filename, before "-d" (Info-Zip's fixed argument order). Chunked at
    EXTRACT_CHUNK_SIZE as cheap insurance against argv length limits on an
    unusually large batch; a full batch (~19K EINs) fits comfortably under
    ARG_MAX in one call, so this is a small handful of invocations in
    practice.
    """
    members = []
    for filing in filings.values():
        object_id = filing["object_id"]
        if not object_id.isdigit():
            raise BatchProcessingError(f"Unsafe/unexpected OBJECT_ID: {object_id!r}")
        members.append(f"{object_id}_public.xml")

    for start in range(0, len(members), EXTRACT_CHUNK_SIZE):
        chunk = members[start:start + EXTRACT_CHUNK_SIZE]
        result = subprocess.run(
            ["unzip", "-o", str(zip_path), *chunk, "-d", str(extract_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise BatchProcessingError(
                "unzip could not extract every requested XML member: "
                f"{result.stderr.strip()}"
            )


def process_batch(
    db: sqlite3.Connection,
    batch_id: str,
    filings: dict[str, dict],
    apply: bool,
) -> dict[str, int]:
    zip_url = direct.batch_zip_url(batch_id)
    stats = {"matched_eins": len(filings), "parsed": 0, "written": 0}

    with tempfile.TemporaryDirectory(prefix=f"irs-990-{batch_id}-") as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "batch.zip"
        extract_dir = temp_path / "xml"
        extract_dir.mkdir()

        download_batch(zip_url, zip_path)
        extract_requested_xmls(zip_path, extract_dir, filings)

        parsed_filings: list[tuple[str, dict, dict]] = []
        for ein, filing in filings.items():
            xml_path = extract_dir / f"{filing['object_id']}_public.xml"
            if not xml_path.exists():
                raise BatchProcessingError(
                    f"Requested XML was absent after extraction: {xml_path.name}"
                )

            try:
                parsed = direct.parse_990_xml(xml_path.read_bytes())
            except Exception as exc:
                raise BatchProcessingError(
                    f"Could not parse {xml_path.name} for EIN {ein}: {exc}"
                ) from exc

            if parsed is None:
                raise BatchProcessingError(
                    f"No IRS990 payload in {xml_path.name} for EIN {ein}"
                )

            parsed_filings.append((ein, filing, parsed))
            stats["parsed"] += 1

        if not apply:
            return stats

        now = datetime.now(timezone.utc).isoformat()
        try:
            with db:
                for ein, filing, parsed in parsed_filings:
                    # Exact 3-table write behavior is owned by the direct-filing
                    # script, including its never-downgrade UPDATE predicate and
                    # functional-expense reconciliation rule.
                    direct.write_filing(db, ein, filing, parsed, now)
                    stats["written"] += 1
        except sqlite3.Error as exc:
            raise BatchProcessingError(
                f"Database transaction failed for {batch_id}; rolled back: {exc}"
            ) from exc

    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Number of IRS batch months to consider (default: 3).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write database changes and mark successfully completed batches.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help=f"Completion-state JSON path (default: {DEFAULT_STATE_PATH}).",
    )
    args = parser.parse_args()

    if args.months < 1:
        parser.error("--months must be at least 1")

    lock_path = args.state_file.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another recent-filings refresh is already running; skipping.")
            return 0

        today = datetime.now(timezone.utc).date()
        cutoff = subtract_months(today, args.months)
        submission_years = list(range(today.year, cutoff.year - 1, -1))

        state = load_state(args.state_file)
        db = sqlite3.connect(direct.DB_PATH, timeout=120)
        db.execute("PRAGMA busy_timeout = 120000")

        try:
            registry_eins = known_eins(db)
            print(f"Registry EINs loaded: {len(registry_eins):,}")
            print(
                f"Checking IRS submission years {submission_years}; "
                f"batch cutoff {cutoff.isoformat()}."
            )

            batches = discover_recent_batches(
                submission_years=submission_years,
                cutoff=cutoff,
                registry_eins=registry_eins,
            )
            pending = {
                batch_id: filings
                for batch_id, filings in batches.items()
                if state["batches"].get(batch_id, {}).get("status") != "completed"
            }

            if not pending:
                print("No unprocessed recent IRS batches found.")
                return 0

            print(
                f"Found {len(pending):,} unprocessed batch(es), containing "
                f"{sum(len(filings) for filings in pending.values()):,} registry EIN(s)."
            )

            for batch_id in sorted(pending):
                filings = pending[batch_id]
                print(f"\nProcessing {batch_id}: {len(filings):,} registry EIN(s)")
                stats = process_batch(db, batch_id, filings, args.apply)
                print(
                    f"  parsed={stats['parsed']:,} "
                    f"written={stats['written']:,} "
                    f"dry_run={not args.apply}"
                )

                if args.apply:
                    state["batches"][batch_id] = {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "matched_eins": stats["matched_eins"],
                        "parsed": stats["parsed"],
                        "written": stats["written"],
                        "source_url": direct.batch_zip_url(batch_id),
                    }
                    # State is recorded only after its DB transaction commits.
                    save_state(args.state_file, state)

            return 0
        finally:
            db.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BatchProcessingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
