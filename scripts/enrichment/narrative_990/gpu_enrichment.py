#!/usr/bin/env python3
"""
scripts/enrichment/narrative_990/gpu_enrichment.py

Phase 4 of the 990 Narrative Enrichment project (docs/990-enrichment/):
GPU-derived semantic fields (mission_summary, services, populations_served,
geographies, reported_outcomes, new_or_changed_programs, other_useful_facts),
computed only from the bounded deterministic excerpts Phase 3 already
extracts (scripts/ops/fetch_irs_direct_filing.py's parse_990_xml() output) --
never from a whole filing.

Storage: migrations/024_irs_990_narrative_gpu_summary.sql (NOT YET APPLIED --
requires founder approval per CLAUDE.md's schema-change gate; this module's
write_gpu_summary() targets that table and is tested against a rolled-back
transaction, not live data, until the migration is approved and run).

Skip-cache: keyed on (ein, tax_year, object_id) + input_sha256 + model_version
+ prompt_version. If an exact match already exists, the GPU call is skipped
entirely -- same "don't duplicate effort" principle applied to Phase 3's
already_processed_eins() (refresh_recent_filings_batch.py), now covering the
more expensive GPU step specifically.

Usage (manual, one filing):
    python3 -m scripts.enrichment.narrative_990.gpu_enrichment 592240895 \
        data/990_xml/samples/592240895_990_202509.xml 202509
"""
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
from scripts.ops.fetch_irs_direct_filing import parse_990_xml  # noqa: E402
from scripts.enrichment.llm_extraction import (  # noqa: E402
    extract_narrative_enrichment, build_narrative_input,
)

DB_PATH = REPO_ROOT / "data" / "merit_registry.db"
PROMPT_VERSION = "1.1-2026-08-16-evidence-quotes"
# Codex Review D (2026-08-16): llm_extraction.MODEL ("qwen3-30b-a3b-instruct")
# is only the API-facing model-name string sent to llama-server -- it does
# not identify the actual deployed quantized artifact, so a swapped gguf
# file with the same served name wouldn't invalidate the skip-cache. Store
# the specific artifact identifier here instead, independent of what the
# API call itself uses.
MODEL_ARTIFACT_VERSION = "Qwen3-30B-A3B-Instruct-2507-Q4_K_M"


def input_hash(bounded_text: str) -> str:
    return hashlib.sha256(bounded_text.encode("utf-8")).hexdigest()


def already_cached(db: sqlite3.Connection, ein: str, tax_year: int, object_id: str, input_sha256: str) -> bool:
    """True if this exact filing was already GPU-processed with the current
    input hash, model, and prompt version -- i.e. genuinely nothing new to
    compute, not just "we've seen this EIN". Same principle as Phase 3's
    already_processed_eins(), applied to the more expensive GPU step."""
    row = db.execute(
        "SELECT 1 FROM irs_990_narrative_gpu_summary "
        "WHERE ein = ? AND tax_year = ? AND object_id = ? "
        "AND input_sha256 = ? AND model_version = ? AND prompt_version = ?",
        (ein, tax_year, object_id, input_sha256, MODEL_ARTIFACT_VERSION, PROMPT_VERSION),
    ).fetchone()
    return row is not None


def write_gpu_summary(
    db: sqlite3.Connection, ein: str, tax_year: int, object_id: str,
    result: dict, parsed_filing: dict, input_sha256: str, now: str,
) -> None:
    """Writes one GPU enrichment result. INSERT OR REPLACE on the (ein,
    tax_year, object_id) primary key -- idempotent, matching the convention
    established throughout this project (extracted_programs, org_revenue_history).
    significant_new_program/significant_change come from parsed_filing
    (Phase 3's deterministic extraction), not from the model's result dict --
    Codex Review D (2026-08-16): these should be persisted as filing facts,
    not left to the model to infer/describe."""
    db.execute(
        "INSERT OR REPLACE INTO irs_990_narrative_gpu_summary "
        "(ein, tax_year, object_id, significant_new_program, significant_change, "
        " mission_summary, services_json, "
        " populations_served_json, geographies_json, reported_outcomes_json, "
        " new_or_changed_programs_json, other_useful_facts_json, grounded, "
        " input_sha256, model_version, prompt_version, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            ein, tax_year, object_id,
            _bool_or_none(parsed_filing.get("significant_new_program")),
            _bool_or_none(parsed_filing.get("significant_change")),
            result.get("mission_summary"),
            json.dumps(result.get("services") or []),
            json.dumps(result.get("populations_served") or []),
            json.dumps(result.get("geographies") or []),
            json.dumps(result.get("reported_outcomes") or []),
            json.dumps(result.get("new_or_changed_programs") or []),
            json.dumps(result.get("other_useful_facts") or []),
            int(bool(result.get("grounded"))),
            input_sha256, MODEL_ARTIFACT_VERSION, PROMPT_VERSION, now,
        ),
    )


def _bool_or_none(value) -> int | None:
    """parse_990_xml() returns True/False/None for these flags (None = the
    filing didn't include the indicator at all, distinct from False)."""
    return None if value is None else int(bool(value))


def enrich_one(db: sqlite3.Connection, ein: str, tax_year: int, object_id: str, parsed_filing: dict) -> str:
    """Returns one of: 'skipped_cached', 'skipped_no_input', 'written', 'failed'."""
    bounded = build_narrative_input(parsed_filing)
    if not bounded.strip():
        return "skipped_no_input"
    h = input_hash(bounded)
    if already_cached(db, ein, tax_year, object_id, h):
        return "skipped_cached"
    result = extract_narrative_enrichment(parsed_filing, ein)
    if result is None:
        return "failed"
    now = datetime.now(timezone.utc).isoformat()
    write_gpu_summary(db, ein, tax_year, object_id, result, parsed_filing, h, now)
    return "written"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ein")
    ap.add_argument("xml_path")
    ap.add_argument("tax_period", help="e.g. 202509 (YYYYMM)")
    ap.add_argument("--apply", action="store_true",
                     help="Commit the write (default: dry run, rolled back)")
    args = ap.parse_args()

    content = Path(args.xml_path).read_bytes()
    parsed = parse_990_xml(content)
    if parsed is None:
        print("Could not parse filing.")
        sys.exit(1)

    tax_year = int(args.tax_period[:4])
    object_id = f"MANUAL_{args.ein}_{args.tax_period}"

    db = sqlite3.connect(str(DB_PATH))
    db.execute("BEGIN")
    status = enrich_one(db, args.ein, tax_year, object_id, parsed)
    print(f"Status: {status}")
    if status == "written":
        row = db.execute(
            "SELECT mission_summary, services_json, grounded FROM irs_990_narrative_gpu_summary "
            "WHERE ein = ? AND tax_year = ? AND object_id = ?",
            (args.ein, tax_year, object_id),
        ).fetchone()
        print(f"  mission_summary: {row[0]}")
        print(f"  services: {row[1]}")
        print(f"  grounded: {row[2]}")
    if args.apply:
        db.commit()
        print("APPLIED.")
    else:
        db.execute("ROLLBACK")
        print("DRY RUN -- rolled back, nothing written. Re-run with --apply.")
    db.close()


if __name__ == "__main__":
    main()
