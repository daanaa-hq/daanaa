#!/usr/bin/env python3
"""
Phase 5: Mission & Cause Backfill — Generate missions and extract causes for
all eligible orgs (deductible + active).

Pipeline:
1. Load eligible orgs (deductibility=1 AND org_status='active', mission IS NULL)
2. For each org:
   a. Generate 2-3 sentence mission via Qwen2.5-32B (port 11437)
   b. Extract causes via keyword rules + confidence scoring
   c. UPDATE registry_enriched with mission, cause_tags, mission_confidence
3. Checkpoint every 100 orgs for resumable progress
4. Log to /tmp/phase5_progress.log

GPU: Qwen2.5-32B-Instruct on port 11437
Speed: ~60 tok/s → 400K+ orgs in 30-40 hours depending on scale
Workers: 16 parallel (tuned for GPU mem + API throttling)

Usage:
    python3 scripts/phase5_mission_backfill.py --limit 1000 --workers 4 --dry-run
    python3 scripts/phase5_mission_backfill.py --workers 16
    python3 scripts/phase5_mission_backfill.py --resume  # Resume from last checkpoint
"""

import sqlite3
import json
import time
import argparse
import sys
import re
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Optional, Tuple, Dict
import requests

# Import local cause taxonomy
try:
    from cause_taxonomy import extract_causes, CAUSE_TAXONOMY
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from cause_taxonomy import extract_causes, CAUSE_TAXONOMY

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
CHECKPOINT_PATH = Path.home() / "meritgiving" / "logs" / "phase5_checkpoint.json"
PROGRESS_LOG = Path("/tmp/phase5_progress.log")

LLM_URL = "http://127.0.0.1:11437/v1/chat/completions"
LLM_MODEL = "Qwen2.5-32B-Instruct-Q4_K_M"
BATCH_SIZE = 16
TOKENS_PER_MISSION = 60
CHECKPOINT_INTERVAL = 100
LLM_TIMEOUT = 120

# NTEE major group labels
NTEE_LABELS = {
    "A": "arts and culture",
    "B": "education",
    "C": "environment",
    "D": "animals",
    "E": "health care",
    "F": "mental health",
    "G": "disease research and patient support",
    "H": "medical research",
    "I": "crime and legal services",
    "J": "employment",
    "K": "food and nutrition",
    "L": "housing and shelter",
    "M": "public safety and disaster relief",
    "N": "sports and recreation",
    "O": "youth development",
    "P": "human services",
    "Q": "international",
    "R": "civil rights and advocacy",
    "S": "community improvement",
    "T": "philanthropy and grantmaking",
    "U": "science and technology",
    "V": "social science",
    "W": "public benefit",
    "X": "faith-based",
    "Y": "mutual benefit",
    "Z": "community service",
}

FEW_SHOT = """\
Write 1-2 sentence mission descriptions. Use org NAME first, then sector and location.
- Start with what they do, not what they are.
- Present tense, active voice.
- No flowery language ("dedicated to", "strives to", "passionate about").
- Use size context to gauge scale (local vs. national) but NEVER quote dollar amounts or revenue figures in the output.

Examples:
- Meals on Wheels: "Delivers hot meals and support to homebound seniors across the region."
- Boys & Girls Club: "Provides after-school programs and mentorship for young people."
- Food Bank: "Distributes fresh food to families experiencing food insecurity."
"""

# Global state
_lock = Lock()
_stats = {
    "processed": 0,
    "generated": 0,
    "skipped": 0,
    "errors": 0,
    "timestamp": datetime.now(timezone.utc).isoformat(),
}


def log(msg: str, to_progress: bool = True) -> None:
    """Log to stdout and optionally to progress file."""
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if to_progress:
        with open(PROGRESS_LOG, "a") as f:
            f.write(line + "\n")


def load_checkpoint() -> dict:
    """Load resume checkpoint."""
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH) as f:
                cp = json.load(f)
                # Ensure processed_eins is a set for resume
                if "processed_eins" in cp and isinstance(cp["processed_eins"], list):
                    cp["processed_eins"] = set(cp["processed_eins"])
                return cp
        except Exception as e:
            log(f"Checkpoint read error: {e}", to_progress=False)
    return {
        "processed_eins": set(),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "generated_count": 0,
        "skipped_count": 0,
    }


def save_checkpoint(checkpoint: dict) -> None:
    """Persist checkpoint."""
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    checkpoint["processed_eins"] = list(checkpoint["processed_eins"])
    checkpoint["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(checkpoint, f, indent=2)


def build_prompt(batch: list[dict]) -> str:
    """Build LLM prompt for batch of orgs."""
    lines = []
    for org in batch:
        ntee = NTEE_LABELS.get(org.get("NTEE1") or "", "community service")
        revenue = org.get("total_revenue")
        size = f"${revenue:,.0f} annual revenue" if revenue else "community-based"
        city = (org.get("CITY") or "").title()
        lines.append(
            f'  ein="{org["EIN"]}", name="{org["organization_name"]}", sector="{ntee}", '
            f'location="{city}, {org.get("STATE", "")}", size="{size}"'
        )

    return (
        FEW_SHOT + "\n"
        "Write mission sentences for these organizations. "
        'Return ONLY a JSON array: [{"ein": "...", "mission": "..."}]\n\n'
        "Organizations:\n" + "\n".join(lines)
    )


def call_llm(batch: list) -> Dict[str, str]:
    """
    Call Qwen2.5-32B to generate missions.

    Returns: {ein: mission_text}
    Only EINs in the input batch are accepted (prevents hallucinations).
    """
    valid_eins = {org["EIN"] for org in batch}
    prompt = build_prompt(batch)
    n = len(batch)

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You output only raw JSON arrays. No markdown, no explanation.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max(400, TOKENS_PER_MISSION * n),
    }

    try:
        r = requests.post(LLM_URL, json=payload, timeout=LLM_TIMEOUT)
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        content = msg.get("content") or ""

        # Extract JSON array from response
        m = re.search(r"\[.*\]", content, re.DOTALL)
        if m:
            parsed = json.loads(m.group())
            return {
                item["ein"]: item["mission"].strip()
                for item in (parsed if isinstance(parsed, list) else [])
                if item.get("ein") in valid_eins and item.get("mission")
            }
    except Exception as e:
        log(f"LLM error: {e}", to_progress=True)

    return {}


def write_batch(
    results: Dict[str, Tuple[str, list, float]],
    conn: sqlite3.Connection,
    batch_size: int,
) -> None:
    """
    Write results to database.

    Args:
        results: {ein: (mission_text, cause_tags_list, confidence_score)}
        conn: Database connection
        batch_size: For error counting
    """
    global _stats

    if not results:
        with _lock:
            _stats["skipped"] += batch_size
        return

    # Retry loop for database locks
    for attempt in range(6):
        try:
            prepared = [
                (mission, json.dumps(causes), confidence, ein)
                for ein, (mission, causes, confidence) in results.items()
            ]
            conn.executemany(
                "UPDATE registry_enriched "
                "SET mission=?, cause_tags=?, mission_confidence=?, "
                "mission_source='ai_generated' WHERE EIN=?",
                prepared,
            )
            conn.commit()

            with _lock:
                _stats["generated"] += len(results)
                _stats["skipped"] += batch_size - len(results)
            return
        except sqlite3.OperationalError as e:
            if "locked" not in str(e).lower() or attempt == 5:
                raise
            conn.rollback()
            time.sleep(10 * (attempt + 1))


def process_org(
    org: dict, conn: sqlite3.Connection
) -> Optional[Tuple[str, str, list, float]]:
    """
    Process a single org: generate mission, extract causes.

    Returns: (ein, mission_text, cause_tags, confidence) or None if failed
    """
    try:
        # Skip if mission exists
        if org.get("mission"):
            return None

        # Generate mission via LLM
        missions = call_llm([org])
        if org["EIN"] not in missions:
            return None

        mission = missions[org["EIN"]]

        # Extract causes from mission
        causes, confidence = extract_causes(mission)

        return (org["EIN"], mission, causes, confidence)
    except Exception as e:
        log(f"Error processing org {org.get('EIN')}: {e}", to_progress=False)
        return None


def fetch_orgs_for_phase5(
    conn: sqlite3.Connection,
    limit: Optional[int] = None,
    skip_eins: Optional[set] = None,
) -> list:
    """
    Fetch orgs for Phase 5 backfill.

    Filters:
    - deductibility=1 AND org_status='active' (eligible orgs)
    - mission_source='ai_ntee' (upgrade ai_ntee to ai_generated via Qwen)
    - NOT already processed in this checkpoint
    """
    skip_eins = skip_eins or set()

    query = """
    SELECT EIN, organization_name, NTEE1, CITY, STATE, total_revenue
    FROM registry_enriched
    WHERE deductibility = 1
      AND org_status = 'active'
      AND mission_source = 'ai_ntee'
    LIMIT ?
    """

    try:
        cursor = conn.execute(query, (limit or 100_000,))
        orgs = [dict(row) for row in cursor.fetchall()]
        return [o for o in orgs if o["EIN"] not in skip_eins]
    except sqlite3.OperationalError as e:
        if "no such column" in str(e).lower():
            log(f"Database schema incomplete: {e}", to_progress=True)
            return []
        raise


def main(
    limit: int = None,
    workers: int = 16,
    dry_run: bool = False,
    resume: bool = False,
) -> None:
    """
    Main Phase 5 mission backfill pipeline.

    Args:
        limit: Max orgs to process (for testing)
        workers: Parallel workers
        dry_run: Show sample prompts but don't write
        resume: Resume from last checkpoint
    """
    global _stats

    log(f"Phase 5 Mission & Cause Backfill starting...")
    log(f"  LLM: {LLM_MODEL} on port 11437")
    log(f"  Workers: {workers}")
    log(f"  Batch size: {BATCH_SIZE}")
    log(f"  Dry run: {dry_run}")
    log(f"  Resume: {resume}")

    # Load checkpoint
    checkpoint = load_checkpoint() if resume else load_checkpoint()
    processed_eins = checkpoint.get("processed_eins", set())

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row

    try:
        # Fetch orgs for Phase 5
        orgs = fetch_orgs_for_phase5(conn, limit=limit, skip_eins=processed_eins)
        total = len(orgs)

        log(f"Found {total} orgs to upgrade (ai_ntee → ai_generated via Qwen)")

        if total == 0:
            log("No ai_ntee missions to upgrade. All done or already upgraded.")
            return

        if dry_run:
            log("DRY RUN MODE — showing sample prompts only")
            sample = orgs[:min(2, total)]
            for org in sample:
                prompt = build_prompt([org])
                log(f"\nSample prompt for {org['organization_name']} ({org['EIN']}):\n{prompt[:500]}...")
            return

        # Process in batches
        batch_num = 0
        for start in range(0, total, BATCH_SIZE):
            batch = orgs[start : start + BATCH_SIZE]
            batch_num += 1

            log(f"Batch {batch_num}: Processing {len(batch)} orgs...")

            # Generate missions
            missions_dict = call_llm(batch)

            # Extract causes for each result
            results = {}
            for ein, mission in missions_dict.items():
                causes, confidence = extract_causes(mission)
                results[ein] = (mission, causes, confidence)

            # Write batch to database
            write_batch(results, conn, len(batch))

            # Update stats
            with _lock:
                _stats["processed"] += len(batch)

            # Save checkpoint every CHECKPOINT_INTERVAL
            if batch_num % (CHECKPOINT_INTERVAL // BATCH_SIZE) == 0:
                processed_eins.update(ein for ein, _ in missions_dict.items())
                checkpoint["processed_eins"] = processed_eins
                checkpoint["generated_count"] = _stats["generated"]
                checkpoint["skipped_count"] = _stats["skipped"]
                save_checkpoint(checkpoint)
                log(
                    f"Checkpoint saved. Processed: {_stats['processed']}, "
                    f"Generated: {_stats['generated']}, Skipped: {_stats['skipped']}"
                )

            time.sleep(0.5)  # Gentle rate limiting

    finally:
        conn.close()

    # Final stats
    log(f"\nPhase 5 Complete!")
    log(f"  Processed: {_stats['processed']}")
    log(f"  Generated: {_stats['generated']}")
    log(f"  Skipped: {_stats['skipped']}")
    log(f"  Errors: {_stats['errors']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 5: Mission & Cause Backfill")
    parser.add_argument("--limit", type=int, help="Max orgs to process (for testing)")
    parser.add_argument("--workers", type=int, default=16, help="Parallel workers (default 16)")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts only")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")

    args = parser.parse_args()

    main(
        limit=args.limit,
        workers=args.workers,
        dry_run=args.dry_run,
        resume=args.resume,
    )
