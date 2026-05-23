#!/usr/bin/env python3
"""
enrich_cause_tags_claude.py — Claude Haiku cause-tag enrichment for orgs with missions
but sparse/missing tags.

Targets orgs that have a mission statement but ≤1 cause tag.
Processes in configurable batch sizes so you control token spend per run.
Fully resumable via checkpoint file.

Cost estimate: ~18K orgs × ~400 tokens input + 60 output ≈ $2-3 at Haiku pricing.

Usage:
    python3 scripts/enrich_cause_tags_claude.py                  # default 5K batch
    python3 scripts/enrich_cause_tags_claude.py --batch 2000     # smaller batches
    python3 scripts/enrich_cause_tags_claude.py --limit 500      # quick test
    python3 scripts/enrich_cause_tags_claude.py --dry-run        # no writes
    python3 scripts/enrich_cause_tags_claude.py --reset          # clear checkpoint, start fresh
"""

import sqlite3, json, re, argparse, time, sys, os
from pathlib import Path
from datetime import datetime
import anthropic

DB_PATH    = Path.home() / "meritgiving/data/merit_registry.db"
CHECKPOINT = Path.home() / "meritgiving/data/claude_tags_checkpoint.txt"
LOG_FILE   = Path("/tmp/enrich_cause_tags_claude.log")

MODEL      = "claude-haiku-4-5-20251001"
MAX_TOKENS = 80

SYSTEM = (
    "You tag nonprofits for a donor-facing directory. "
    "Given an org name and mission, return ONLY a JSON array of 2-5 short plain-English "
    "cause tags like [\"food security\",\"youth education\",\"community development\"]. "
    "Tags should be lowercase, 1-3 words, donor-friendly. "
    "No explanation, no markdown, just the JSON array."
)


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_checkpoint() -> str | None:
    return CHECKPOINT.read_text().strip() or None if CHECKPOINT.exists() else None


def save_checkpoint(ein: str):
    CHECKPOINT.write_text(ein)


def parse_tags(text: str) -> list[str]:
    text = text.strip()
    try:
        tags = json.loads(text)
        if isinstance(tags, list):
            return [str(t).strip().lower()[:60] for t in tags if str(t).strip()][:6]
    except json.JSONDecodeError:
        pass
    # Fallback: extract quoted strings
    found = re.findall(r'"([^"]{2,60})"', text)
    return [t.lower() for t in found[:6]] if found else []


def merge_tags(existing: list[str], new: list[str]) -> list[str]:
    seen = {t.lower() for t in existing}
    result = list(existing)
    for t in new:
        if t.lower() not in seen:
            result.append(t)
            seen.add(t.lower())
    return result


def ask_claude(client: anthropic.Anthropic, name: str, mission: str) -> list[str]:
    prompt = f"Organization: {name}\nMission: {mission[:800]}"
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_tags(msg.content[0].text)
    except Exception as e:
        log(f"  API error: {e}")
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=5000, help="Orgs per batch (default 5000)")
    parser.add_argument("--limit", type=int, default=0,    help="Hard cap on total orgs (0=all)")
    parser.add_argument("--dry-run", action="store_true",  help="No DB writes")
    parser.add_argument("--reset", action="store_true",    help="Clear checkpoint and start fresh")
    args = parser.parse_args()

    if args.reset and CHECKPOINT.exists():
        CHECKPOINT.unlink()
        log("Checkpoint cleared.")

    client = anthropic.Anthropic()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    log("Querying orgs with missions but sparse tags...")
    rows = db.execute("""
        SELECT EIN, organization_name, mission, cause_tags, CITY, STATE
        FROM registry_enriched
        WHERE mission IS NOT NULL AND mission != ''
        AND (
            cause_tags IS NULL OR cause_tags = '[]' OR cause_tags = ''
            OR cause_tags NOT LIKE '%,%'
        )
        ORDER BY total_revenue DESC NULLS LAST
    """).fetchall()

    candidates = [(r["EIN"], r["organization_name"], r["mission"], r["cause_tags"] or "[]") for r in rows]
    log(f"  {len(candidates):,} orgs with missions but sparse tags")

    # Resume from checkpoint
    checkpoint = load_checkpoint()
    if checkpoint:
        try:
            start = next(i for i, (ein, *_) in enumerate(candidates) if ein == checkpoint)
            candidates = candidates[start:]
            log(f"  Resuming from checkpoint EIN {checkpoint} ({len(candidates):,} remaining)")
        except StopIteration:
            log(f"  Checkpoint EIN {checkpoint} not found — starting fresh")

    if args.limit:
        candidates = candidates[:args.limit]
        log(f"  Capped at {args.limit} (--limit)")

    written = 0
    skipped = 0
    errors  = 0
    start_time = time.time()
    batch_num = 0

    for batch_start in range(0, len(candidates), args.batch):
        batch = candidates[batch_start:batch_start + args.batch]
        batch_num += 1
        log(f"\nBatch {batch_num}: orgs {batch_start+1}–{batch_start+len(batch)} of {len(candidates):,}")

        for i, (ein, name, mission, existing_tags_json) in enumerate(batch):
            global_i = batch_start + i + 1

            try:
                existing = json.loads(existing_tags_json) if existing_tags_json else []
            except Exception:
                existing = []

            new_tags = ask_claude(client, name, mission)

            if not new_tags:
                skipped += 1
                continue

            merged = merge_tags(existing, new_tags)

            if not args.dry_run:
                db.execute(
                    "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                    (json.dumps(merged), ein)
                )
                if i % 50 == 0:
                    db.commit()
            written += 1

            if (global_i) % 100 == 0:
                elapsed = time.time() - start_time
                rps = global_i / elapsed
                log(f"  [{global_i}/{len(candidates)}] written={written} skipped={skipped} errors={errors} {rps:.1f} req/s")
                save_checkpoint(ein)

            # Haiku rate limit: ~1K req/min tier 1 — small sleep to be safe
            time.sleep(0.07)

        db.commit()
        elapsed = time.time() - start_time
        log(f"Batch {batch_num} complete — written={written} skipped={skipped} elapsed={elapsed:.0f}s")

        if batch_start + args.batch < len(candidates):
            log("Sleeping 5s between batches...")
            time.sleep(5)

    db.close()
    total = time.time() - start_time
    log(f"\nDone in {total:.0f}s")
    log(f"  Written: {written:,}")
    log(f"  Skipped: {skipped:,}  (no tags returned)")
    log(f"  Errors:  {errors:,}")
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()
    log("Checkpoint cleared.")


if __name__ == "__main__":
    main()
