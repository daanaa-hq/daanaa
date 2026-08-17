#!/usr/bin/env python3
"""
Fill Daanaa's direct-IRS Form 990 coverage gap for registry EINs that have
never been touched by this pipeline at all.

This complements, and does not replace,
scripts/ops/backfill_990_narrative_phase3.py:

- This script expands coverage to EINs never touched by the direct-IRS XML
  pipeline.
- Phase 3 refreshes already-covered EINs whose stored parser_version is older
  than the current fetch_irs_direct_filing.PARSER_VERSION.

Recommended sequence: run this script first to establish new coverage, then run
the Phase 3 backfill afterward if PARSER_VERSION has moved on.

Older-year schema risk: parse_990_xml() was built and tested primarily against
2026 filings. Older 990 XML may use materially different field names or shapes.
This is a real project risk, not a theoretical one: the original mission
fallback field assumed by this project was verified not to exist in real 2026
filings. Before trusting a full-year --all --apply run, use --limit against an
older year such as 2024 or 2025 and manually spot-check extracted mission and
Schedule O text quality.

Usage:
    python3 scripts/ops/fill_990_coverage_gap.py --year 2025
    python3 scripts/ops/fill_990_coverage_gap.py --year 2025 --limit 25 --apply
    python3 scripts/ops/fill_990_coverage_gap.py --year 2025 --all --apply

The default is a 25-filing dry run. --apply is required for database writes and
for updates to this script's separate completion-state file.
"""

import argparse
import fcntl
import json
import sqlite3
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scripts.ops import fetch_irs_direct_filing as direct
from scripts.ops import refresh_recent_filings_batch as recent


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = (
    REPO_ROOT / "data" / "ops_state" / "irs_990_fill_coverage.json"
)


def eligible_registry_eins(db: sqlite3.Connection) -> set[str]:
    """
    Return known registry EINs with no existing direct-IRS-pipeline coverage
    at all -- presence-based, not parser-version-based (stale rows belong to
    the Phase 3 backfill, not this job).

    "Coverage" deliberately checks more than three signals, not just
    irs_990_functional_expense_filings presence. That table is populated only
    when parse_990_xml() extracts financials -- which 990-EZ filings never do
    by design (their fields are unverified, see fetch_irs_direct_filing.py's
    docstring). A 990-EZ-only org that already got a mission/Schedule O/
    cause_tags written by this pipeline would still show as "uncovered" under
    a financial-only check, and get needlessly reprocessed by a later run
    covering a different year. The mission-upgrade guard in write_filing()
    would still prevent an older filing from clobbering a newer one, so this
    was not a correctness risk, but it was a real waste of a full batch
    download/parse pass and a dishonest "coverage" number. Checked directly
    against real code, not assumed: registry_enriched.data_source is set to
    'irs_direct' only on a financial write (same gap); mission_source='irs_990'
    and extracted_programs.schedule_o_source='irs_990_xml' are both set
    regardless of form type, so either is a reliable "this pipeline already
    touched this EIN" signal on its own.

    Fourth signal added in Codex review (2026-08-16), found real and
    non-hypothetical: a 990-EZ filing can produce Part III program
    descriptions (write_filing() sets programs_available=1) while having no
    usable mission and no Schedule O explanation that passes the
    junk/relevance filter -- none of the first three signals fire, so that
    EIN would be endlessly re-selected as "uncovered" on every future
    --year run despite having been fully processed. Confirmed real, not
    theoretical: 4,163 current registry rows have programs_available=1 and
    none of the other three signals. programs_available is written
    exclusively by fetch_irs_direct_filing.py in this codebase (verified via
    full grep), so it's a safe additional provenance signal, not a
    false-positive risk from some other writer.
    """
    return {
        row[0].strip().zfill(9)
        for row in db.execute(
            """
            SELECT DISTINCT registry.EIN
            FROM registry_enriched AS registry
            LEFT JOIN irs_990_functional_expense_filings AS filing
                ON filing.EIN = registry.EIN
            LEFT JOIN extracted_programs AS programs
                ON programs.EIN = registry.EIN
                AND programs.schedule_o_source = 'irs_990_xml'
            WHERE registry.EIN IS NOT NULL
              AND TRIM(registry.EIN) != ''
              AND filing.EIN IS NULL
              AND programs.EIN IS NULL
              AND (registry.mission_source IS NULL OR registry.mission_source != 'irs_990')
              AND (registry.programs_available IS NULL OR registry.programs_available = 0)
            """
        )
        if row[0]
    }


def state_key(year: int, batch_id: str) -> str:
    """Keep state scoped to a submission year plus its IRS batch ID."""
    return f"{year}:{batch_id}"


def completed_filing_keys(state: dict, year: int, batch_id: str) -> set[str]:
    entry = state["batches"].get(state_key(year, batch_id), {})
    keys = entry.get("completed_filings", [])
    if not isinstance(keys, list):
        raise recent.BatchProcessingError(
            f"Unexpected completed_filings format for {state_key(year, batch_id)!r}"
        )
    return {key for key in keys if isinstance(key, str)}


def filing_key(filing: dict) -> str:
    """Stable state identity for one IRS XML object."""
    return f"{filing['ein']}:{filing['object_id']}"


def discover_year_batches(
    year: int,
    eligible_eins: set[str],
) -> dict[str, dict[str, dict]]:
    """
    Return {batch_id: {ein: filing}} for the given IRS submission year.

    The index is scanned once for both supported form types. If an eligible EIN
    appears more than once, retain only its latest real TAX_PERIOD before
    grouping by XML_BATCH_ID.
    """
    latest_by_ein: dict[str, dict] = {}

    for row in direct.iter_990_index_rows(
        [year],
        return_types=frozenset({"990", "990EZ"}),
    ):
        ein = row.get("EIN", "").strip().zfill(9)
        batch_id = row.get("XML_BATCH_ID", "").strip()
        object_id = row.get("OBJECT_ID", "").strip()
        tax_period = row.get("TAX_PERIOD", "").strip()
        form_type = row.get("RETURN_TYPE", "").strip()

        if ein not in eligible_eins:
            continue
        if not batch_id or not object_id or not object_id.isdigit() or not tax_period:
            continue
        if form_type not in {"990", "990EZ"}:
            continue

        batch_match = recent.BATCH_ID_MONTH_RE.fullmatch(batch_id)
        if batch_match is None or recent.batch_month(batch_id) is None:
            print(
                f"Skipping unrecognized XML_BATCH_ID from index: {batch_id!r}",
                file=sys.stderr,
            )
            continue
        if int(batch_match["year"]) != year:
            print(
                f"Skipping batch whose encoded year disagrees with --year {year}: "
                f"{batch_id!r}",
                file=sys.stderr,
            )
            continue

        filing = {
            "ein": ein,
            "tax_period": tax_period,
            "object_id": object_id,
            "batch_id": batch_id,
            "form_type": form_type,
        }
        previous = latest_by_ein.get(ein)
        if previous is None or filing["tax_period"] > previous["tax_period"]:
            latest_by_ein[ein] = filing

    batches: dict[str, dict[str, dict]] = defaultdict(dict)
    for ein, filing in latest_by_ein.items():
        batches[filing["batch_id"]][ein] = filing
    return dict(batches)


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
            ein: filings[ein]
            for ein in sorted(filings)[:remaining]
        }
        if selected_filings:
            selected[batch_id] = selected_filings
            remaining -= len(selected_filings)
    return selected


def narrative_snapshot(
    db: sqlite3.Connection,
    ein: str,
    tax_year: int,
) -> tuple[tuple | None, tuple | None, set[str]]:
    """Capture the narrative values needed for post-write reporting."""
    mission = db.execute(
        """
        SELECT mission, mission_source, mission_last_verified
        FROM registry_enriched
        WHERE EIN = ?
        """,
        (ein,),
    ).fetchone()
    schedule_o = db.execute(
        """
        SELECT schedule_o_text, schedule_o_source
        FROM extracted_programs
        WHERE EIN = ? AND schedule_o_year = ?
        """,
        (ein, tax_year),
    ).fetchone()
    tags_row = db.execute(
        "SELECT cause_tags FROM registry_enriched WHERE EIN = ?",
        (ein,),
    ).fetchone()

    try:
        tags = json.loads(tags_row[0]) if tags_row and tags_row[0] else []
    except (TypeError, ValueError, json.JSONDecodeError):
        tags = []

    return mission, schedule_o, set(tags) if isinstance(tags, list) else set()


def has_any_coverage(db: sqlite3.Connection, ein: str) -> bool:
    """
    Return whether an EIN now has any direct-pipeline coverage signal --
    same four-signal check as eligible_registry_eins(), kept in sync with it
    so "newly covered" reporting matches what future runs will treat as
    already-covered.
    """
    row = db.execute(
        """
        SELECT
            EXISTS(SELECT 1 FROM irs_990_functional_expense_filings WHERE EIN = ?)
            OR EXISTS(
                SELECT 1 FROM extracted_programs
                WHERE EIN = ? AND schedule_o_source = 'irs_990_xml'
            )
            OR EXISTS(
                SELECT 1 FROM registry_enriched
                WHERE EIN = ? AND mission_source = 'irs_990'
            )
            OR EXISTS(
                SELECT 1 FROM registry_enriched
                WHERE EIN = ? AND programs_available = 1
            )
        """,
        (ein, ein, ein, ein),
    ).fetchone()
    return bool(row and row[0])


def empty_stats() -> dict:
    return {
        "filings_selected": 0,
        "filings_parsed": 0,
        "filings_written": 0,
        "eins_newly_covered": 0,
        "missions_written": 0,
        "schedule_o_rows_written": 0,
        "cause_tag_additions": 0,
        "form_990_parsed": 0,
        "form_990ez_parsed": 0,
        "form_990_written": 0,
        "form_990ez_written": 0,
        "parse_failures": [],
    }


def process_batch(
    db: sqlite3.Connection,
    batch_id: str,
    filings: dict[str, dict],
    apply: bool,
) -> dict:
    """
    Download one batch ZIP once, extract only requested XMLs, and continue
    after individual XML parse failures. Download/extraction/database failures
    remain batch failures because their success cannot be established safely.
    """
    stats = empty_stats()
    stats["filings_selected"] = len(filings)

    with tempfile.TemporaryDirectory(prefix=f"irs-990-fill-{batch_id}-") as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "batch.zip"
        extract_dir = temp_path / "xml"
        extract_dir.mkdir()

        recent.download_batch(direct.batch_zip_url(batch_id), zip_path)
        recent.extract_requested_xmls(zip_path, extract_dir, filings)

        parsed_filings: list[tuple[dict, dict]] = []
        for filing in filings.values():
            ein = filing["ein"]
            xml_path = extract_dir / f"{filing['object_id']}_public.xml"

            try:
                if not xml_path.exists():
                    raise FileNotFoundError(
                        f"Requested XML was absent after extraction: {xml_path.name}"
                    )
                parsed = direct.parse_990_xml(xml_path.read_bytes())
                if parsed is None:
                    raise ValueError("No IRS990 or IRS990EZ payload")
            except Exception as exc:
                failure = {
                    "ein": ein,
                    "batch_id": batch_id,
                    "object_id": filing["object_id"],
                    "error": str(exc),
                }
                stats["parse_failures"].append(failure)
                print(
                    f"  PARSE FAILURE EIN={ein} batch_id={batch_id} "
                    f"object_id={filing['object_id']}: {exc}",
                    file=sys.stderr,
                )
                continue

            parsed_filings.append((filing, parsed))
            stats["filings_parsed"] += 1
            if filing["form_type"] == "990":
                stats["form_990_parsed"] += 1
            else:
                stats["form_990ez_parsed"] += 1

        if not apply:
            return stats

        now = datetime.now(timezone.utc).isoformat()
        try:
            with db:
                for filing, parsed in parsed_filings:
                    ein = filing["ein"]
                    tax_year = int(filing["tax_period"][:4])
                    before_mission, before_schedule_o, before_tags = narrative_snapshot(
                        db, ein, tax_year
                    )
                    had_coverage = has_any_coverage(db, ein)

                    direct.write_filing(
                        db,
                        ein,
                        {
                            "tax_period": filing["tax_period"],
                            "object_id": filing["object_id"],
                            "batch_id": batch_id,
                        },
                        parsed,
                        now,
                    )

                    after_mission, after_schedule_o, after_tags = narrative_snapshot(
                        db, ein, tax_year
                    )
                    stats["filings_written"] += 1
                    if filing["form_type"] == "990":
                        stats["form_990_written"] += 1
                    else:
                        stats["form_990ez_written"] += 1

                    if not had_coverage and has_any_coverage(db, ein):
                        stats["eins_newly_covered"] += 1
                    if before_mission != after_mission:
                        stats["missions_written"] += 1
                    if before_schedule_o != after_schedule_o:
                        stats["schedule_o_rows_written"] += 1
                    stats["cause_tag_additions"] += len(after_tags - before_tags)
        except sqlite3.Error as exc:
            raise recent.BatchProcessingError(
                f"Database transaction failed for {batch_id}; rolled back: {exc}"
            ) from exc

    return stats


def add_stats(total: dict, batch_stats: dict) -> None:
    for key, value in batch_stats.items():
        if key == "parse_failures":
            total.setdefault(key, []).extend(value)
        elif isinstance(value, int):
            total[key] = total.get(key, 0) + value


def record_batch_state(
    state: dict,
    year: int,
    batch_id: str,
    selected_filings: dict[str, dict],
    stats: dict,
) -> None:
    """
    Record only successfully written filings. Parse failures deliberately stay
    absent from completed_filings so the next --apply invocation retries them.
    """
    key = state_key(year, batch_id)
    entry = state["batches"].setdefault(key, {})
    completed = set(entry.get("completed_filings", []))
    failed_eins = {failure["ein"] for failure in stats["parse_failures"]}

    for filing in selected_filings.values():
        if filing["ein"] not in failed_eins:
            completed.add(filing_key(filing))

    entry.update(
        {
            "status": "partial" if failed_eins else "completed",
            "year": year,
            "batch_id": batch_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "source_url": direct.batch_zip_url(batch_id),
            "completed_filings": sorted(completed),
            "last_run_stats": {
                key: value
                for key, value in stats.items()
                if key != "parse_failures"
            },
            "parse_failures": stats["parse_failures"],
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fill direct-IRS 990/990-EZ coverage for registry EINs with no "
            "existing direct-pipeline coverage."
        )
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Required IRS submission year; process one bounded year per run.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write database changes and this script's separate state file.",
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
        help="Process all eligible filings for --year; mutually exclusive with --limit.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help=f"Coverage-fill-only state JSON path (default: {DEFAULT_STATE_PATH}).",
    )
    args = parser.parse_args()

    if args.year < 1900 or args.year > 9999:
        parser.error("--year must be a four-digit submission year")
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.all and "--limit" in sys.argv:
        parser.error("--all and --limit are mutually exclusive")

    lock_path = args.state_file.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another 990 coverage-fill run is already running; skipping.")
            return 0

        db = sqlite3.connect(direct.DB_PATH, timeout=120)
        db.execute("PRAGMA busy_timeout = 120000")
        try:
            state = recent.load_state(args.state_file)
            eligible_eins = eligible_registry_eins(db)
            print(
                f"Eligible never-covered registry EINs: {len(eligible_eins):,}. "
                f"Scanning IRS submission year {args.year}; "
                f"parser_version={direct.PARSER_VERSION!r}."
            )

            batches = discover_year_batches(args.year, eligible_eins)
            discovered_count = sum(len(filings) for filings in batches.values())
            print(
                f"Found {discovered_count:,} latest eligible filing(s) across "
                f"{len(batches):,} batch(es)."
            )

            pending: dict[str, dict[str, dict]] = {}
            skipped_from_state = 0
            for batch_id, filings in batches.items():
                completed = completed_filing_keys(state, args.year, batch_id)
                remaining = {
                    ein: filing
                    for ein, filing in filings.items()
                    if filing_key(filing) not in completed
                }
                skipped_from_state += len(filings) - len(remaining)
                if remaining:
                    pending[batch_id] = remaining

            if skipped_from_state:
                print(
                    f"Skipping {skipped_from_state:,} filing(s) already completed "
                    "by this coverage-fill state file."
                )

            if not pending:
                print("No eligible unprocessed filings remain for this submission year.")
                return 0

            selected = limited_batches(
                pending,
                limit=None if args.all else args.limit,
            )
            selected_count = sum(len(filings) for filings in selected.values())
            print(
                f"Selected {selected_count:,} filing(s) from {len(selected):,} "
                f"batch(es); dry_run={not args.apply}."
            )

            totals = empty_stats()
            for batch_id in sorted(selected):
                filings = selected[batch_id]
                print(f"\nProcessing {batch_id}: {len(filings):,} filing(s)")
                stats = process_batch(db, batch_id, filings, args.apply)
                add_stats(totals, stats)

                print(
                    f"  parsed={stats['filings_parsed']:,} "
                    f"written={stats['filings_written']:,} "
                    f"newly_covered={stats['eins_newly_covered']:,} "
                    f"missions_written={stats['missions_written']:,} "
                    f"schedule_o_rows_written={stats['schedule_o_rows_written']:,} "
                    f"cause_tag_additions={stats['cause_tag_additions']:,} "
                    f"parse_failures={len(stats['parse_failures']):,}"
                )

                if args.apply:
                    record_batch_state(state, args.year, batch_id, filings, stats)
                    # State follows the committed DB transaction; failed XMLs
                    # remain retryable because they were not marked completed.
                    recent.save_state(args.state_file, state)

            print("\nPost-run report:")
            for key in (
                "filings_selected",
                "filings_parsed",
                "filings_written",
                "eins_newly_covered",
                "missions_written",
                "schedule_o_rows_written",
                "cause_tag_additions",
                "form_990_parsed",
                "form_990ez_parsed",
                "form_990_written",
                "form_990ez_written",
            ):
                print(f"  {key}={totals.get(key, 0):,}")

            failures = totals["parse_failures"]
            print(f"  parse_failures={len(failures):,}")
            if failures:
                print("  Reviewable parse failures:")
                for failure in failures:
                    print(
                        f"    EIN={failure['ein']} batch_id={failure['batch_id']} "
                        f"object_id={failure['object_id']} error={failure['error']}",
                        file=sys.stderr,
                    )

            if not args.apply:
                print(
                    "\nDry run: no database rows or coverage-fill state were written. "
                    "Reported write and newly-covered counts are therefore zero."
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
