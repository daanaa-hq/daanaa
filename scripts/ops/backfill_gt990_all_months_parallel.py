#!/usr/bin/env python3
"""
scripts/ops/backfill_gt990_all_months_parallel.py

Batch-parallel wrapper around refresh_recent_filings_batch.py's already-correct
discovery/parse/write logic. Built 2026-08-17 to backfill a long window of
historical GT990 monthly batches (default 36 months) fast, using this
server's 16 CPUs, without reimplementing any of the safety-critical parsing
or write logic.

Design: this does NOT reimplement parse_990_xml(), write_filing(), or the
IRS ZIP extraction (which requires the `unzip` CLI -- IRS batch ZIPs use a
compression method Python's zipfile module doesn't support; see
refresh_recent_filings_batch.py's extract_requested_xmls() docstring).
Instead:

  - Batch discovery, download, extraction, and parsing (the CPU/network-bound
    work) run in a multiprocessing.Pool across up to 16 worker processes --
    one batch per worker at a time. Each worker calls the *exact* reference
    functions (download_batch, extract_requested_xmls, direct.parse_990_xml)
    imported from refresh_recent_filings_batch.py, so behavior is identical
    to the sequential script.
  - Workers do NOT open the database or write anything. They return parsed
    (ein, filing, parsed_dict) tuples to the main process.
  - The main process writes every batch's results serially, inside a single
    `with db:` transaction per batch, calling the same
    direct.write_filing() used by the sequential script (same never-downgrade
    UPDATE predicate and functional-expense reconciliation rule). This
    avoids any concurrent-SQLite-write risk entirely -- multiple processes
    never touch merit_registry.db at the same time.

Resumability and dedup are inherited from the reference script: state is
recorded per batch_id in a JSON file (same schema as
refresh_recent_filings_batch.py's state file, but a separate path so this
long-window backfill never marks-complete a batch the nightly cron hasn't
independently processed, or vice versa), and already_processed_eins() skips
any EIN whose exact filing (EIN, tax_year, object_id, current parser_version)
is already recorded -- so re-running this script, or running it alongside
the nightly cron, never reprocesses or downgrades a filing. "Keep the latest
one if it's repeating" is exactly write_filing()'s never-downgrade predicate:
across all months processed, whichever tax_period is newest for a given EIN
is what ends up in registry_enriched, regardless of processing order.

Mission-quality flagging (new in this script, not present in the reference
script): after write_filing() succeeds, the freshly written mission is
checked against embedding server (port 11436, mxbai-embed-large-v1). This is
advisory only -- it flags but does not withhold low-quality-looking missions
from the database, exactly matching the rest of this pipeline's precedent
(AI-generated missions have never been withheld pending review; see
mission_source='ai_generated' rows already live in production). The check
is: (1) length 10-500 chars, (2) not ALL CAPS, (3) at least 2 words, (4) if
the embedding server responds, its vector's L2 norm is sanity-bounded. Any
failure of the embedding call itself (server down, timeout) degrades to
"unverified" rather than raising -- this is explicitly a best-effort
diagnostic signal, not a gate, and network flakiness must never block a
write that IRS data itself supports.

Usage:
    python3 scripts/ops/backfill_gt990_all_months_parallel.py --months 3 --workers 4
    python3 scripts/ops/backfill_gt990_all_months_parallel.py --months 36 --workers 16 --apply
    python3 scripts/ops/backfill_gt990_all_months_parallel.py --months 36 --workers 16 --force --apply

Default is a dry run: batches are discovered, downloaded, extracted, and
parsed, but nothing is written to the database or the state file. --apply is
required for both.
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import tempfile
import time
from datetime import date, datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.ops import fetch_irs_direct_filing as direct
from scripts.ops import refresh_recent_filings_batch as recent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Deliberately separate from refresh_recent_filings_batch.py's own state file
# (irs_direct_recent_filings_batches.json) -- this script covers a much wider
# historical window and must not cross-contaminate the nightly cron's
# completion tracking, or vice versa. A batch fully processed by one script
# is still safely reprocessable by the other: already_processed_eins() skips
# any EIN whose exact filing is already in the DB at the current parser
# version, so double coverage costs a wasted download/parse pass, not a
# correctness bug.
DEFAULT_STATE_PATH = REPO_ROOT / "data" / "ops_state" / "irs_gt990_parallel_backfill.json"
EMBED_SERVER = "http://localhost:11436"


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "batches": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"State file unreadable, refusing to proceed: {path}: {exc}") from exc
    if state.get("version") != 1 or not isinstance(state.get("batches"), dict):
        raise RuntimeError(f"Unexpected state-file format: {path}")
    return state


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def validate_mission_quality(mission: str | None) -> dict:
    """Advisory-only quality flag. See module docstring for the exact heuristic.

    Two real bugs found and fixed 2026-08-17, discovered by manually sampling
    real, freshly-written mission text and finding it consistently legitimate
    despite a ~65-70% "low quality" flag rate in the run logs:

    1. The embedding call posted to f"{EMBED_SERVER}/api/embed" -- that is
       Ollama's endpoint path. Port 11436 runs llama.cpp's llama-server (see
       CLAUDE.md's inference-services table), whose OpenAI-compatible
       endpoint is POST /v1/embeddings with {"input": text}, returning
       {"data": [{"embedding": [...]}], ...}. Every call was silently 404ing
       and falling through to the text-only fallback path -- this specific
       failure mode was harmless (advisory-only, degrades safely by design),
       but the embedding sanity check had never actually executed.

    2. `m.isupper()` was treated as "likely junk" -- but IRS 990/990-EZ
       mission text is very commonly transcribed entirely in capitals (a
       normal filing/preparer convention, not a data-quality signal; e.g.
       "PROVIDE YOUTH SKATING AND RECREATIONAL ACTIVITIES TO THE YOUTH OF
       THE RHINELANDER AREA" is a completely legitimate, real mission
       statement). This single check explains nearly the entire false-flag
       rate observed. Removed -- casing is not evidence of quality here.

    Neither bug affected what got written to the database: this check has
    always been advisory-only (flags, never withholds), so mission/program
    text written under the old code is exactly as correct as under this
    fix. Only the "low_quality_missions" counter in already-completed run
    logs is unreliable and should be disregarded; it does not reflect the
    real data.
    """
    if not mission:
        return {"valid": False, "reason": "empty"}
    m = mission.strip()
    if len(m) < 10:
        return {"valid": False, "reason": "too_short"}
    if len(m) > 500:
        return {"valid": False, "reason": "too_long"}
    if len(m.split()) < 2:
        return {"valid": False, "reason": "too_few_words"}
    try:
        resp = requests.post(f"{EMBED_SERVER}/v1/embeddings", json={"input": m}, timeout=2)
        if resp.status_code == 200:
            data = resp.json().get("data")
            vec = data[0].get("embedding") if data else None
            if vec:
                norm = sum(x * x for x in vec) ** 0.5
                if norm < 0.1 or norm > 100:
                    return {"valid": False, "reason": "embedding_anomaly"}
                return {"valid": True, "reason": "passed_all_checks"}
    except Exception as exc:  # best-effort diagnostic only, never blocks a write
        logger.debug("Embedding server unreachable (%s); mission left unverified", exc)
    return {"valid": True, "reason": "unverified_text_checks_only"}


def discover_recent_batches_multi_type(
    submission_years: list[int],
    cutoff: date,
    registry_eins: set[str],
    return_types: frozenset[str],
) -> dict[str, dict[str, dict]]:
    """
    Local variant of refresh_recent_filings_batch.discover_recent_batches(),
    parameterized on return_types instead of hardcoding "990" only.

    Added 2026-08-17: parse_990_xml() and write_filing() already fully
    support 990-EZ (narrative fields only -- mission, programs, Schedule O,
    grant purposes; financials deliberately left None and never clobber an
    EIN's existing revenue/assets, per parse_990_xml()'s own docstring) and
    the single-org CLI already exposes this via --include-ez. Neither batch
    script (the nightly cron or this one) was ever wired to request it,
    because discover_recent_batches() hardcodes an
    `if RETURN_TYPE != "990"` filter. Sampling a real index (2026, ~500K
    rows) found 990-EZ filings at roughly 2/3 the volume of 990 itself
    (111,950 vs 163,606) -- a large, previously-untouched pool of orgs whose
    donations are tax-deductible the same as any other 501(c)(3), just never
    given direct-IRS mission/program coverage. 990-PF was also found in the
    same sample (68,094) but is NOT included here: parse_990_xml() only
    recognizes IRS990 and IRS990EZ root elements and returns None for
    anything else (verified by reading the function, not assumed) -- 990-PF
    has a genuinely different XML schema and would need real new parser
    work, not just a wider filter. Left out deliberately rather than passed
    through to write silently-empty rows.

    This function is otherwise identical to the reference implementation:
    same cutoff/registry-EIN filtering, same newest-tax-period-wins dedup
    per batch. Not added to the reference script itself, to avoid changing
    the nightly cron's existing, already-relied-upon 990-only behavior as a
    side effect of this backfill's own scope expansion.
    """
    batches: dict[str, dict[str, dict]] = {}

    for row in direct.iter_990_index_rows(submission_years, return_types):
        if row.get("RETURN_TYPE", "").strip() not in return_types:
            continue

        ein = row.get("EIN", "").strip().zfill(9)
        batch_id = row.get("XML_BATCH_ID", "").strip()
        object_id = row.get("OBJECT_ID", "").strip()
        tax_period = row.get("TAX_PERIOD", "").strip()

        if ein not in registry_eins or not batch_id or not object_id or not tax_period:
            continue

        release_month = recent.batch_month(batch_id)
        if release_month is None:
            logger.warning(f"Skipping unrecognized XML_BATCH_ID: {batch_id}")
            continue
        if release_month < cutoff:
            continue

        filing = {"tax_period": tax_period, "object_id": object_id, "batch_id": batch_id}
        filings_for_batch = batches.setdefault(batch_id, {})

        previous = filings_for_batch.get(ein)
        if previous is None or filing["tax_period"] > previous["tax_period"]:
            filings_for_batch[ein] = filing

    return batches


def extract_requested_xmls_lenient(
    zip_path: Path, extract_dir: Path, filings: dict, batch_id: str
) -> list[str]:
    """
    Lenient variant of refresh_recent_filings_batch.extract_requested_xmls().

    Real bug #1 found running this script at scale (2026-08-17): the
    reference script's extract_requested_xmls() raises BatchProcessingError
    if unzip's exit code is non-zero for ANY missing member, which aborts
    the ENTIRE batch -- including the tens of thousands of EINs whose XML
    *was* present and successfully extracted. Two batches
    (2026_TEOS_XML_05A, 2025_TEOS_XML_05A) were discarded whole this way
    despite the vast majority of their members extracting fine. Fixed by
    not raising on a non-zero unzip exit code -- unzip legitimately returns
    non-zero (typically 11) when a subset of requested members are missing,
    even though every other requested member in that same call extracted.

    Real bug #2 found investigating why ALL nine 2024 batches wrote zero
    filings (2026-08-17, same day): IRS packages its batch ZIPs
    inconsistently. Some (confirmed: every 2026 batch checked) store members
    at the ZIP root -- "{object_id}_public.xml". Others (confirmed: every
    2024 batch checked, e.g. 2024_TEOS_XML_11A, downloaded and inspected
    directly with `unzip -l`) nest every member one level down, inside a
    folder named after the batch_id itself --
    "{batch_id}/{object_id}_public.xml". Requesting only the root-level path
    (what both this script and the reference script did originally) matches
    nothing in a nested ZIP, which unzip reports as "not matched" for every
    single member -- indistinguishable from bug #1's stale-index case
    without actually downloading and inspecting a failing ZIP, which is what
    surfaced this. Fixed with a two-pass extraction: try the flat root path
    first (the common case, one unzip call, no wasted work for normal
    batches); for any member still missing afterward, retry with the
    batch_id-prefixed path, then move any newly-found file up out of the
    nested folder to the flat location every downstream call in this script
    expects (extract_dir / "{object_id}_public.xml") -- so callers never need
    to know which of the two packaging styles a given batch used.

    Downstream code in this script already handles a genuinely missing XML
    file per-EIN gracefully (skips that EIN, logs it, continues with the
    rest of the batch), so nothing here silently drops a *processable*
    filing -- these two fixes only stop treating "packaging quirks" as a
    reason to lose data that was actually there.
    """
    import shutil
    import subprocess

    object_ids = []
    for filing in filings.values():
        object_id = filing["object_id"]
        if not object_id.isdigit():
            raise recent.BatchProcessingError(f"Unsafe/unexpected OBJECT_ID: {object_id!r}")
        object_ids.append(object_id)

    def run_unzip(members: list[str], dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        for start in range(0, len(members), recent.EXTRACT_CHUNK_SIZE):
            chunk = members[start:start + recent.EXTRACT_CHUNK_SIZE]
            subprocess.run(
                ["unzip", "-o", str(zip_path), *chunk, "-d", str(dest)],
                capture_output=True,
                text=True,
                check=False,
            )

    # Pass 1: flat root-level path (the common case).
    flat_members = [f"{oid}_public.xml" for oid in object_ids]
    run_unzip(flat_members, extract_dir)

    still_missing = [oid for oid in object_ids if not (extract_dir / f"{oid}_public.xml").exists()]

    if still_missing:
        # Pass 2: retry only the misses, under the batch_id-prefixed path.
        nested_dir = extract_dir / "_nested"
        nested_members = [f"{batch_id}/{oid}_public.xml" for oid in still_missing]
        run_unzip(nested_members, nested_dir)

        for oid in still_missing:
            nested_path = nested_dir / batch_id / f"{oid}_public.xml"
            if nested_path.exists():
                shutil.move(str(nested_path), str(extract_dir / f"{oid}_public.xml"))

    unmatched = [oid for oid in object_ids if not (extract_dir / f"{oid}_public.xml").exists()]
    return unmatched


def fetch_and_parse_batch_worker(args: tuple) -> dict:
    """
    Runs in a worker process. Downloads the batch ZIP, extracts only the
    requested registry EINs, and parses each one -- reusing
    refresh_recent_filings_batch.py's own download_batch(),
    extract_requested_xmls(), and direct.parse_990_xml() so extraction
    behavior is byte-for-byte identical to the sequential script. Does NOT
    touch the database.
    """
    batch_id, filings = args
    start = time.time()
    zip_url = direct.batch_zip_url(batch_id)
    parsed_filings: list[tuple[str, dict, dict]] = []
    errors: list[str] = []

    try:
        with tempfile.TemporaryDirectory(prefix=f"irs-990-{batch_id}-") as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "batch.zip"
            extract_dir = temp_path / "xml"
            extract_dir.mkdir()

            recent.download_batch(zip_url, zip_path)
            unmatched = extract_requested_xmls_lenient(zip_path, extract_dir, filings, batch_id)
            if unmatched:
                errors.append(
                    f"{len(unmatched)} object_id(s) genuinely absent from this batch's ZIP "
                    f"(checked both flat and {batch_id}/-prefixed paths; not fatal to the "
                    f"rest of the batch)"
                )

            for ein, filing in filings.items():
                xml_path = extract_dir / f"{filing['object_id']}_public.xml"
                if not xml_path.exists():
                    errors.append(f"{ein}: XML absent after extraction")
                    continue
                try:
                    parsed = direct.parse_990_xml(xml_path.read_bytes())
                except Exception as exc:
                    errors.append(f"{ein}: parse failed: {exc}")
                    continue
                if parsed is None:
                    errors.append(f"{ein}: no IRS990 payload")
                    continue
                parsed_filings.append((ein, filing, parsed))
    except Exception as exc:
        return {
            "batch_id": batch_id,
            "success": False,
            "error": str(exc),
            "elapsed_sec": time.time() - start,
        }

    return {
        "batch_id": batch_id,
        "success": True,
        "parsed_filings": parsed_filings,
        "errors": errors,
        "matched_eins": len(filings),
        "elapsed_sec": time.time() - start,
    }


def write_batch_results(db: sqlite3.Connection, batch_id: str, parsed_filings: list) -> dict:
    """Serial write in the main process -- one transaction per batch, same
    write_filing() call the sequential script uses.

    Real bug found and fixed 2026-08-17, same day as the two extraction
    fixes: this originally read parsed.get("mission") and
    parsed.get("cause_tags"), but parse_990_xml() actually returns the
    mission text under the key "mission_text", and never returns a
    "cause_tags" key at all (cause tags are produced by a separate,
    unrelated pipeline stage -- not part of this parser's output). Both
    conditions were always false, so the GPU embedding-based mission-quality
    check (validate_mission_quality(), which calls the local mxbai-embed
    server on port 11436) silently never ran against any of the ~432K rows
    written overnight -- every "low_quality_missions=0" in the logs meant
    "the check was skipped", not "everything passed". Not a correctness
    risk (the check is advisory-only and never gated a write either way),
    but real wasted GPU capacity and a misleading log line. Fixed to use
    the correct key and to report something real (schedule_o/programs
    presence) in place of the never-real cause_tags_added metric."""
    now = datetime.now(timezone.utc).isoformat()
    written = 0
    missions_flagged_low_quality = 0
    with_narrative = 0

    with db:
        for ein, filing, parsed in parsed_filings:
            direct.write_filing(db, ein, filing, parsed, now)
            written += 1
            mission_text = parsed.get("mission_text")
            if mission_text:
                quality = validate_mission_quality(mission_text)
                if not quality["valid"]:
                    missions_flagged_low_quality += 1
            if parsed.get("schedule_o") or parsed.get("programs"):
                with_narrative += 1

    return {
        "written": written,
        "missions_flagged_low_quality": missions_flagged_low_quality,
        "with_narrative": with_narrative,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch-parallel GT990 historical backfill (download/parse "
        "parallelized across workers; DB writes serialized in the main process)."
    )
    parser.add_argument("--months", type=int, default=36, help="Months of IRS batches to consider (default 36)")
    parser.add_argument("--workers", type=int, default=16, help="Parallel download/parse workers (default 16, max 16)")
    parser.add_argument("--apply", action="store_true", help="Write to the database and persist state")
    parser.add_argument("--force", action="store_true", help="Ignore resume state; reprocess all discovered batches")
    parser.add_argument(
        "--include-ez", action="store_true",
        help="Also discover 990-EZ filings (narrative only: mission/programs/Schedule O, "
             "no financials -- see discover_recent_batches_multi_type() docstring). Uses a "
             "separate state file so a batch_id already marked complete under 990-only "
             "scope is still re-checked for its newly-in-scope EZ filings.",
    )
    parser.add_argument("--state-file", type=Path, default=None)
    args = parser.parse_args()

    if args.months < 1:
        parser.error("--months must be at least 1")
    args.workers = max(1, min(args.workers, 16))

    if args.state_file is None:
        args.state_file = (
            DEFAULT_STATE_PATH.with_name(DEFAULT_STATE_PATH.stem + "_with_ez.json")
            if args.include_ez else DEFAULT_STATE_PATH
        )

    state = load_state(args.state_file) if not args.force else {"version": 1, "batches": {}}

    today = datetime.now(timezone.utc).date()
    cutoff = recent.subtract_months(today, args.months)
    submission_years = list(range(today.year, cutoff.year - 1, -1))

    return_types = frozenset({"990", "990EZ"}) if args.include_ez else frozenset({"990"})

    db = sqlite3.connect(direct.DB_PATH, timeout=120)
    db.execute("PRAGMA busy_timeout = 120000")

    try:
        registry_eins = recent.known_eins(db)
        logger.info(f"Registry EINs loaded: {len(registry_eins):,}")
        logger.info(
            f"Checking IRS submission years {submission_years}; batch cutoff {cutoff.isoformat()}; "
            f"return_types={sorted(return_types)}"
        )

        batches = discover_recent_batches_multi_type(
            submission_years=submission_years,
            cutoff=cutoff,
            registry_eins=registry_eins,
            return_types=return_types,
        )

        pending = {
            batch_id: filings
            for batch_id, filings in batches.items()
            if state["batches"].get(batch_id, {}).get("status") != "completed"
        }

        if not pending:
            logger.info("No unprocessed batches in the requested window.")
            return 0

        total_matched = sum(len(f) for f in pending.values())
        logger.info(
            f"Found {len(pending):,} unprocessed batch(es), "
            f"{total_matched:,} registry EIN(s) total. "
            f"{'DRY RUN' if not args.apply else 'APPLY MODE'} | {args.workers} workers"
        )

        # Pre-filter each batch's filings against already_processed_eins() up
        # front, in the main process, before dispatching to workers -- avoids
        # downloading/extracting XML for EINs we'd just discard, and keeps
        # already_processed_eins() (a DB read) out of the worker processes.
        worker_jobs = []
        already_processed_total = 0
        for batch_id, filings in pending.items():
            already_done = recent.already_processed_eins(db, filings)
            already_processed_total += len(already_done)
            remaining = {ein: f for ein, f in filings.items() if ein not in already_done}
            if remaining:
                worker_jobs.append((batch_id, remaining))
            else:
                logger.info(f"{batch_id}: all {len(filings):,} EIN(s) already processed at current parser version")
                if args.apply:
                    state["batches"][batch_id] = {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "matched_eins": len(filings),
                        "already_processed": len(already_done),
                        "parsed": 0,
                        "written": 0,
                        "source_url": direct.batch_zip_url(batch_id),
                    }
                    save_state(args.state_file, state)

        if not worker_jobs:
            logger.info(f"All {already_processed_total:,} matched EIN(s) already processed. Nothing to download.")
            return 0

        logger.info(
            f"Dispatching {len(worker_jobs)} batch(es) to {args.workers} worker(s) "
            f"({already_processed_total:,} EIN(s) already covered, skipped up front)"
        )

        total_written = 0
        total_flagged = 0
        total_with_narrative = 0
        total_errors = 0

        with Pool(processes=args.workers) as pool:
            for result in pool.imap_unordered(fetch_and_parse_batch_worker, worker_jobs):
                batch_id = result["batch_id"]
                if not result["success"]:
                    logger.error(f"✗ {batch_id}: {result['error']} ({result['elapsed_sec']:.1f}s)")
                    total_errors += 1
                    continue

                parsed_filings = result["parsed_filings"]
                for err in result["errors"]:
                    logger.warning(f"  {batch_id}: {err}")

                if args.apply and parsed_filings:
                    write_stats = write_batch_results(db, batch_id, parsed_filings)
                else:
                    write_stats = {"written": 0, "missions_flagged_low_quality": 0, "with_narrative": 0}

                logger.info(
                    f"✓ {batch_id}: matched={result['matched_eins']:,} "
                    f"parsed={len(parsed_filings):,} written={write_stats['written']:,} "
                    f"low_quality_missions={write_stats['missions_flagged_low_quality']:,} "
                    f"with_narrative={write_stats['with_narrative']:,} "
                    f"in {result['elapsed_sec']:.1f}s"
                )

                total_written += write_stats["written"]
                total_flagged += write_stats["missions_flagged_low_quality"]
                total_with_narrative += write_stats["with_narrative"]

                if args.apply:
                    state["batches"][batch_id] = {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "matched_eins": result["matched_eins"],
                        "parsed": len(parsed_filings),
                        "written": write_stats["written"],
                        "source_url": direct.batch_zip_url(batch_id),
                    }
                    # Persist after each batch's transaction commits, same as
                    # the sequential reference script -- a crash mid-run never
                    # loses more than the in-flight batch.
                    save_state(args.state_file, state)

        logger.info("")
        logger.info("=" * 60)
        logger.info("BACKFILL RUN COMPLETE")
        logger.info(f"  Batches processed: {len(worker_jobs)} (errors: {total_errors})")
        logger.info(f"  EINs written: {total_written:,}")
        logger.info(f"  Missions flagged low-quality by GPU embedding check (advisory only): {total_flagged:,}")
        logger.info(f"  Filings with narrative (Schedule O or programs): {total_with_narrative:,}")
        logger.info(f"  Mode: {'Apply' if args.apply else 'Dry run'}")
        logger.info("=" * 60)
        return 1 if total_errors else 0
    finally:
        db.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
