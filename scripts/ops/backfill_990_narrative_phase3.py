#!/usr/bin/env python3
"""
scripts/ops/backfill_990_narrative_phase3.py

Backfills Phase 3 deterministic 990 narrative enrichment for filings written
before fetch_irs_direct_filing.PARSER_VERSION. Eligible filings come directly
from irs_990_functional_expense_filings, grouped by their stored IRS batch ZIP
source_url; no IRS index scan is needed.

For every eligible filing, this script downloads each distinct IRS batch ZIP
once, extracts only its needed XML members, then calls parse_990_xml() and
write_filing() from fetch_irs_direct_filing.py.

IMPORTANT: this is not narrative-only in effect. write_filing() also replays
the filing's financial-history and functional-expense writes. That is an
accepted, expected-idempotent side effect because the underlying filing has
not changed. This script separately reports substantive financial changes;
any nonzero result is unexpected and should be investigated.

Run this when the normal 04:15 recent-filings job is not running. This script
uses a separate lock and state file and never reads, writes, or alters the
nightly job's completion state.

Before the first --apply run, take a database backup:

    scripts/ops/daanaa_backup.sh

Usage:
    python3 scripts/ops/backfill_990_narrative_phase3.py
    python3 scripts/ops/backfill_990_narrative_phase3.py --batch-ids-only
    python3 scripts/ops/backfill_990_narrative_phase3.py --limit 25 --apply
    python3 scripts/ops/backfill_990_narrative_phase3.py --all --apply

The default is a 25-filing dry-run smoke test. --apply is required for every
database or checkpoint-state write.
"""

import argparse
import fcntl
import json
import re
import sqlite3
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from scripts.ops import fetch_irs_direct_filing as direct
from scripts.ops import refresh_recent_filings_batch as recent


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = (
    REPO_ROOT / "data" / "ops_state" / "irs_990_phase3_backfill.json"
)

# write_filing() stores source_url as:
#   https://apps.irs.gov/pub/epostcard/990/xml/<year>/<XML_BATCH_ID>.zip
# Keep this tied to direct.INDEX_BASE rather than duplicating the endpoint.
BATCH_SOURCE_URL_RE = re.compile(
    "^"
    + re.escape(direct.INDEX_BASE.rstrip("/"))
    + r"/(?P<year>\d{4})/(?P<batch_id>[^/]+)\.zip$"
)


def validate_parser_version_ordering(db: sqlite3.Connection) -> None:
    """
    Confirm that SQLite lexical comparison is safe before using the required
    parser_version < current-PARSER_VERSION eligibility predicate.

    The current version is semver/date-suffixed rather than literally
    date-prefixed, so this intentionally validates the actual stored strings
    instead of assuming a version convention.
    """
    observed = [
        row[0]
        for row in db.execute(
            "SELECT DISTINCT parser_version "
            "FROM irs_990_functional_expense_filings "
            "WHERE parser_version IS NOT NULL "
            "ORDER BY parser_version"
        )
    ]

    unexpected = [
        version
        for version in observed
        if version != direct.PARSER_VERSION and version >= direct.PARSER_VERSION
    ]
    if unexpected:
        raise recent.BatchProcessingError(
            "Refusing to rely on lexical parser-version ordering: current "
            f"PARSER_VERSION={direct.PARSER_VERSION!r}, but the table contains "
            f"non-current version(s) that sort at or above it: {unexpected!r}"
        )

    print(
        "Verified parser-version lexical ordering: "
        f"current={direct.PARSER_VERSION!r}; observed={observed!r}"
    )


def batch_id_from_source_url(source_url: str) -> str:
    """
    Recover XML_BATCH_ID only from the canonical direct-IRS ZIP URL written by
    write_filing(). Refuse noncanonical URLs rather than guessing a batch ID.
    """
    if not source_url:
        raise recent.BatchProcessingError(
            "Eligible filing has no source_url, so its XML_BATCH_ID is not "
            "recoverable from stored data. This is a real backfill gap; do not "
            "guess a batch from EIN or tax year."
        )

    parsed = urlparse(source_url)
    if parsed.query or parsed.fragment:
        raise recent.BatchProcessingError(
            f"Eligible filing has noncanonical source_url: {source_url!r}"
        )

    match = BATCH_SOURCE_URL_RE.fullmatch(source_url)
    if not match:
        raise recent.BatchProcessingError(
            "Eligible filing source_url does not match the direct IRS batch-ZIP "
            f"shape written by write_filing(): {source_url!r}"
        )

    batch_id = match["batch_id"]
    if recent.batch_month(batch_id) is None:
        raise recent.BatchProcessingError(
            f"source_url yielded an unrecognized XML_BATCH_ID: {batch_id!r}"
        )
    if not batch_id.startswith(f"{match['year']}_"):
        raise recent.BatchProcessingError(
            "source_url year and XML_BATCH_ID year disagree: "
            f"{source_url!r}"
        )

    # This also guarantees the source URL is exactly what write_filing() will
    # write back, rather than merely a URL that happens to look similar.
    if direct.batch_zip_url(batch_id) != source_url:
        raise recent.BatchProcessingError(
            "source_url is not the canonical URL generated by batch_zip_url(): "
            f"{source_url!r}"
        )
    return batch_id


def eligible_batches(db: sqlite3.Connection) -> tuple[dict[str, dict[str, dict]], int]:
    """
    Return ({batch_id: {unique_filing_key: filing}}, out_of_scope_count) for
    stale parser versions.

    Found running this script against the real database (not anticipated in
    the original design): irs_990_functional_expense_filings has rows from
    TWO different historical pipelines, distinguishable by source_url shape,
    not just by parser_version --
      1.1-2026-08-16-direct-irs -> https://apps.irs.gov/... (17,882 rows) --
        this script's actual scope, re-fetchable via batch_zip_url().
      1.0-2026-08-16 -> https://gt990datalake-rawdata.s3.amazonaws.com/...
        (30 rows) -- an older gt990-sourced ingestion path this script has
        no mechanism to re-fetch from (different bucket, different object
        naming, not what batch_zip_url()/extract_requested_xmls() expect).
    Rather than let batch_id_from_source_url()'s deliberate refusal-to-guess
    abort the entire run on the first gt990 row encountered, filter the
    eligibility query itself to the known-compatible source and report the
    excluded count -- so those 30 rows are visibly out of scope, not
    silently dropped from awareness or fatal to the 17,882 this CAN process.
    """
    rows = db.execute(
        "SELECT DISTINCT EIN, tax_year, object_id, source_url "
        "FROM irs_990_functional_expense_filings "
        "WHERE parser_version < ? "
        "ORDER BY source_url, EIN, tax_year, object_id",
        (direct.PARSER_VERSION,),
    ).fetchall()

    in_scope_prefix = direct.INDEX_BASE.rstrip("/") + "/"
    batches: dict[str, dict[str, dict]] = defaultdict(dict)
    out_of_scope = 0
    for ein, tax_year, object_id, source_url in rows:
        ein = (ein or "").strip().zfill(9)
        object_id = (object_id or "").strip()
        if not ein or not object_id or not object_id.isdigit() or tax_year is None:
            raise recent.BatchProcessingError(
                "Eligible filing has unsafe or incomplete identifying data: "
                f"EIN={ein!r}, tax_year={tax_year!r}, object_id={object_id!r}"
            )

        if not (source_url or "").startswith(in_scope_prefix):
            out_of_scope += 1
            continue

        batch_id = batch_id_from_source_url(source_url)
        filing_key = f"{ein}:{tax_year}:{object_id}"
        batches[batch_id][filing_key] = {
            "ein": ein,
            # write_filing() derives tax_year from the first four characters.
            "tax_period": f"{int(tax_year):04d}1231",
            "object_id": object_id,
            "batch_id": batch_id,
            "source_url": source_url,
        }

    return dict(batches), out_of_scope


def limited_batches(
    batches: dict[str, dict[str, dict]],
    limit: int | None,
) -> dict[str, dict[str, dict]]:
    """Return a deterministic filing-limited selection, preserving batches."""
    if limit is None:
        return batches

    selected: dict[str, dict[str, dict]] = {}
    remaining = limit
    for batch_id in sorted(batches):
        if remaining == 0:
            break
        filings = batches[batch_id]
        selected_filings = {
            key: filings[key]
            for key in sorted(filings)[:remaining]
        }
        if selected_filings:
            selected[batch_id] = selected_filings
            remaining -= len(selected_filings)
    return selected


def financial_snapshot(
    db: sqlite3.Connection,
    filing: dict,
) -> tuple[tuple | None, tuple | None, tuple | None]:
    """Capture substantive financial values only, excluding parser/timestamps."""
    ein = filing["ein"]
    tax_year = int(filing["tax_period"][:4])
    object_id = filing["object_id"]

    history = db.execute(
        "SELECT total_revenue, total_assets, total_expenses "
        "FROM org_revenue_history WHERE EIN = ? AND tax_year = ?",
        (ein, tax_year),
    ).fetchone()
    registry = db.execute(
        "SELECT total_revenue, total_assets, latest_tax_year "
        "FROM registry_enriched WHERE EIN = ?",
        (ein,),
    ).fetchone()
    expenses = db.execute(
        "SELECT total_amt, program_services_amt, management_general_amt, "
        "fundraising_amt, reconciles, validation_status "
        "FROM irs_990_functional_expense_filings "
        "WHERE EIN = ? AND tax_year = ? AND object_id = ?",
        (ein, tax_year, object_id),
    ).fetchone()
    return history, registry, expenses


def narrative_snapshot(
    db: sqlite3.Connection,
    filing: dict,
) -> tuple[tuple | None, tuple | None, list[str]]:
    """Capture the Phase 3 targets needed for post-write verification."""
    ein = filing["ein"]
    tax_year = int(filing["tax_period"][:4])

    schedule_o = db.execute(
        "SELECT schedule_o_text, schedule_o_source "
        "FROM extracted_programs WHERE EIN = ? AND schedule_o_year = ?",
        (ein, tax_year),
    ).fetchone()
    mission = db.execute(
        "SELECT mission, mission_source, mission_last_verified "
        "FROM registry_enriched WHERE EIN = ?",
        (ein,),
    ).fetchone()
    tags_row = db.execute(
        "SELECT cause_tags FROM registry_enriched WHERE EIN = ?",
        (ein,),
    ).fetchone()

    try:
        tags = json.loads(tags_row[0]) if tags_row and tags_row[0] else []
    except (TypeError, ValueError, json.JSONDecodeError):
        tags = []
    return schedule_o, mission, tags if isinstance(tags, list) else []


def process_batch(
    db: sqlite3.Connection,
    batch_id: str,
    filings: dict[str, dict],
    apply: bool,
) -> dict[str, int]:
    """
    Download one batch once, extract only the requested XML files, parse all
    files before any database write, then delegate writes to write_filing().
    """
    stats = {
        "filings_processed": 0,
        "schedule_o_rows_written": 0,
        "schedule_o_content_changes": 0,
        "missions_changed": 0,
        "cause_tag_additions": 0,
        "financial_writes_replayed": 0,
        "financial_substantive_changes": 0,
    }

    helper_filings = {
        key: {
            "object_id": filing["object_id"],
            "tax_period": filing["tax_period"],
            "batch_id": batch_id,
        }
        for key, filing in filings.items()
    }

    with tempfile.TemporaryDirectory(prefix=f"irs-990-phase3-{batch_id}-") as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "batch.zip"
        extract_dir = temp_path / "xml"
        extract_dir.mkdir()

        recent.download_batch(direct.batch_zip_url(batch_id), zip_path)
        recent.extract_requested_xmls(zip_path, extract_dir, helper_filings)

        parsed_filings: list[tuple[dict, dict]] = []
        for filing in filings.values():
            xml_path = extract_dir / f"{filing['object_id']}_public.xml"
            if not xml_path.exists():
                raise recent.BatchProcessingError(
                    f"Requested XML was absent after extraction: {xml_path.name}"
                )
            try:
                parsed = direct.parse_990_xml(xml_path.read_bytes())
            except Exception as exc:
                raise recent.BatchProcessingError(
                    f"Could not parse {xml_path.name} for EIN {filing['ein']}: {exc}"
                ) from exc
            if parsed is None:
                raise recent.BatchProcessingError(
                    f"No IRS990 payload in {xml_path.name} for EIN {filing['ein']}"
                )
            parsed_filings.append((filing, parsed))

        if not apply:
            stats["filings_processed"] = len(parsed_filings)
            stats["schedule_o_rows_written"] = sum(
                1 for _, parsed in parsed_filings if parsed.get("schedule_o")
            )
            stats["financial_writes_replayed"] = sum(
                1
                for _, parsed in parsed_filings
                if parsed.get("total_revenue") is not None
                or parsed.get("program_services_amt") is not None
            )
            return stats

        now = datetime.now(timezone.utc).isoformat()
        try:
            with db:
                for filing, parsed in parsed_filings:
                    before_narrative = narrative_snapshot(db, filing)
                    before_financial = financial_snapshot(db, filing)

                    direct.write_filing(
                        db,
                        filing["ein"],
                        {
                            "tax_period": filing["tax_period"],
                            "object_id": filing["object_id"],
                            "batch_id": batch_id,
                        },
                        parsed,
                        now,
                    )

                    after_narrative = narrative_snapshot(db, filing)
                    after_financial = financial_snapshot(db, filing)

                    stats["filings_processed"] += 1

                    if parsed.get("schedule_o"):
                        stats["schedule_o_rows_written"] += 1
                    if before_narrative[0] != after_narrative[0]:
                        stats["schedule_o_content_changes"] += 1
                    if before_narrative[1] != after_narrative[1]:
                        stats["missions_changed"] += 1

                    before_tags = set(before_narrative[2])
                    after_tags = set(after_narrative[2])
                    stats["cause_tag_additions"] += len(after_tags - before_tags)

                    if (
                        parsed.get("total_revenue") is not None
                        or parsed.get("program_services_amt") is not None
                    ):
                        stats["financial_writes_replayed"] += 1
                    if before_financial != after_financial:
                        stats["financial_substantive_changes"] += 1
        except sqlite3.Error as exc:
            raise recent.BatchProcessingError(
                f"Database transaction failed for {batch_id}; rolled back: {exc}"
            ) from exc

    return stats


def add_stats(total: dict[str, int], batch_stats: dict[str, int]) -> None:
    for key, value in batch_stats.items():
        total[key] = total.get(key, 0) + value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill Phase 3 Schedule O, cause tags, and IRS mission corrections."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the database and Phase 3-only state file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum eligible filings to process (default: 25 smoke-test filings).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every eligible filing; mutually exclusive with --limit.",
    )
    parser.add_argument(
        "--batch-ids-only",
        action="store_true",
        help="List eligible batch IDs and filing counts without downloading or parsing XML.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help=f"Phase 3-only checkpoint-state path (default: {DEFAULT_STATE_PATH}).",
    )
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.all and "--limit" in sys.argv:
        parser.error("--all and --limit are mutually exclusive")
    if args.batch_ids_only and args.apply:
        parser.error("--batch-ids-only cannot be combined with --apply")

    lock_path = args.state_file.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another Phase 3 narrative backfill is already running; skipping.")
            return 0

        db = sqlite3.connect(direct.DB_PATH, timeout=120)
        db.execute("PRAGMA busy_timeout = 120000")
        try:
            validate_parser_version_ordering(db)
            state = recent.load_state(args.state_file)
            batches, out_of_scope = eligible_batches(db)
            if out_of_scope:
                print(
                    f"NOTE: {out_of_scope:,} stale-parser-version filing(s) are from a "
                    "non-apps.irs.gov source (e.g. gt990) this script has no re-fetch "
                    "mechanism for -- out of scope, not processed, not silently dropped."
                )

            completed_with_remaining_work = [
                batch_id
                for batch_id in batches
                if state["batches"].get(batch_id, {}).get("status") == "completed"
            ]
            if completed_with_remaining_work:
                raise recent.BatchProcessingError(
                    "Phase 3 state marks batch(es) completed but their stale "
                    "parser-version rows remain eligible: "
                    f"{completed_with_remaining_work!r}. Refusing to skip them."
                )

            total_eligible = sum(len(filings) for filings in batches.values())
            print(
                f"Eligible Phase 3 filings: {total_eligible:,} "
                f"across {len(batches):,} batch(es)."
            )

            if args.batch_ids_only:
                for batch_id in sorted(batches):
                    print(f"{batch_id}: {len(batches[batch_id]):,} filing(s)")
                return 0

            if not batches:
                print("No stale-parser filings require Phase 3 backfill.")
                return 0

            selected = limited_batches(
                batches,
                limit=None if args.all else args.limit,
            )
            selected_count = sum(len(filings) for filings in selected.values())
            print(
                f"Selected {selected_count:,} filing(s) from {len(selected):,} "
                f"batch(es); dry_run={not args.apply}."
            )

            totals: dict[str, int] = {}
            for batch_id in sorted(selected):
                filings = selected[batch_id]
                print(f"\nProcessing {batch_id}: {len(filings):,} filing(s)")
                stats = process_batch(db, batch_id, filings, args.apply)
                add_stats(totals, stats)
                print(
                    f"  filings_processed={stats['filings_processed']:,} "
                    f"schedule_o_rows_written={stats['schedule_o_rows_written']:,} "
                    f"missions_changed={stats['missions_changed']:,} "
                    f"cause_tag_additions={stats['cause_tag_additions']:,} "
                    f"financial_writes_replayed={stats['financial_writes_replayed']:,} "
                    f"financial_substantive_changes="
                    f"{stats['financial_substantive_changes']:,}"
                )

                if args.apply:
                    full_batch_completed = len(filings) == len(batches[batch_id])
                    state["batches"][batch_id] = {
                        "status": "completed" if full_batch_completed else "partial",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "eligible_filings_in_this_run": len(filings),
                        "eligible_filings_in_batch_before_run": len(batches[batch_id]),
                        "source_url": direct.batch_zip_url(batch_id),
                        "stats": stats,
                    }
                    # Save only after process_batch's transaction committed.
                    recent.save_state(args.state_file, state)

            print("\nPost-run verification:")
            for key in (
                "filings_processed",
                "schedule_o_rows_written",
                "schedule_o_content_changes",
                "missions_changed",
                "cause_tag_additions",
                "financial_writes_replayed",
                "financial_substantive_changes",
            ):
                print(f"  {key}={totals.get(key, 0):,}")

            if args.apply and totals.get("financial_substantive_changes", 0):
                print(
                    "WARNING: substantive financial values changed during what "
                    "should be an idempotent replay. Investigate before "
                    "continuing the full backfill.",
                    file=sys.stderr,
                )

            return 0
        finally:
            db.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except recent.BatchProcessingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
