#!/usr/bin/env python3
"""
enrich_cause_tags_llm.py
LLM-based cause tag enrichment using the local llama-server (:11437, OpenAI-compat).

Targets orgs that have a mission statement but still have no cause tags after
the keyword pass. Runs in parallel (configurable workers) against Qwen3-30B
(or whatever model is loaded on :11437).

Safe to interrupt and resume — skips orgs that already have tags.

Usage:
    python3 scripts/enrich_cause_tags_llm.py --dry-run
    python3 scripts/enrich_cause_tags_llm.py --workers 6
    python3 scripts/enrich_cause_tags_llm.py --limit 500   # test run
"""

import sqlite3, json, time, argparse, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import request as urlreq, error as urlerr

BASE    = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "merit_registry.db"
LLM_URL = "http://127.0.0.1:8080/v1/chat/completions"
MODEL   = "agent"   # llama-server accepts any string as model name
BATCH   = 12        # orgs per LLM call (batching reduces per-token overhead)

SYSTEM_PROMPT = """\
You extract 2-5 concise cause/focus tags from nonprofit mission descriptions.
Tags should be lowercase, 1-3 words each, reflecting the org's primary work.
Examples: education, food bank, mental health, youth sports, animal rescue,
housing, environment, arts, community development, veterans, seniors, faith,
job training, disability services, immigration, domestic violence, literacy.
Return only a JSON array of strings, nothing else. E.g.: ["education","youth"]"""

def llm_call(payload: dict, timeout: int = 60) -> str:
    data = json.dumps(payload).encode()
    req  = urlreq.Request(LLM_URL, data=data,
                          headers={"Content-Type": "application/json"})
    with urlreq.urlopen(req, timeout=timeout) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def build_prompt(orgs: list[dict]) -> str:
    lines = []
    for i, o in enumerate(orgs, 1):
        name    = o["organization_name"] or ""
        mission = (o["mission"] or "")[:300]
        ntee    = o["NTEE1"] or ""
        lines.append(f"{i}. [{ntee}] {name}: {mission}")
    return (
        "For each nonprofit below, return cause tags as a JSON array. "
        "Return a JSON array of arrays (one inner array per org, same order).\n\n"
        + "\n".join(lines)
    )


def parse_tags(raw: str, expected: int) -> list[list[str]] | None:
    """Parse LLM output into a list-of-lists, one per org — or None if the
    response does not CLEANLY align to `expected` orgs.

    Alignment is structural: tags get zipped back to orgs by position, so a
    short/long/garbled response would silently shift every tag after the gap
    onto the wrong org (this mislabelled shelter orgs with 'animals' in a
    batch of 12). On any ambiguity we return None and the caller re-does the
    batch one org at a time, where alignment can't drift.
    """
    raw = raw.strip()
    # Strip markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    if not isinstance(parsed, list):
        return None
    # Single org: accept a flat list of strings or a [[...]] wrapper.
    if expected == 1:
        if parsed and isinstance(parsed[0], str):
            return [[str(t).lower().strip().replace('_', ' ') for t in parsed if t]]
        if parsed and isinstance(parsed[0], list):
            return [[str(t).lower().strip().replace('_', ' ') for t in parsed[0] if t]]
        return [[]]
    # Multi: require EXACTLY `expected` inner lists, else treat as misaligned.
    if len(parsed) != expected or not all(isinstance(x, list) for x in parsed):
        return None
    return [[str(t).lower().strip().replace('_', ' ') for t in item if t] for item in parsed]


def _call_and_parse(orgs: list[dict]) -> list[list[str]] | None:
    """One LLM call for `orgs`; returns aligned tags or None (LLM/parse fail)."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": build_prompt(orgs)},
        ],
        "temperature": 0.1,
        "max_tokens": 512,
    }
    try:
        return parse_tags(llm_call(payload), len(orgs))
    except Exception as e:
        print(f"  LLM error (batch of {len(orgs)}): {e}", flush=True)
        return None


def process_batch(orgs: list[dict], dry_run: bool) -> tuple[int, int]:
    """Return (tagged_count, error_count)."""
    if dry_run:
        for o in orgs:
            print(f"  DRY: {o['organization_name'][:60]}")
        return len(orgs), 0

    parsed = _call_and_parse(orgs)
    # Misaligned (or failed) multi-org response → re-do per org, where the
    # one-to-one mapping is unambiguous. Single-org failure is just an error.
    if parsed is None:
        if len(orgs) == 1:
            return 0, 1
        parsed = []
        for o in orgs:
            p = _call_and_parse([o])
            parsed.append(p[0] if p else [])

    db = sqlite3.connect(DB_PATH, timeout=30)
    saved = 0
    for org, tags in zip(orgs, parsed):
        if tags:
            db.execute(
                "UPDATE registry_enriched SET cause_tags=? WHERE EIN=?",
                (json.dumps(tags), org["EIN"])
            )
            saved += 1
    db.commit()
    db.close()
    return saved, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers",  type=int, default=4)
    ap.add_argument("--limit",    type=int, default=0)
    ap.add_argument("--dry-run",  action="store_true")
    ap.add_argument("--small-first", action="store_true",
                    help="Tag smallest/no-revenue orgs first (discoverability of tiny nonprofits)")
    args = ap.parse_args()

    # Check llama-server is up
    try:
        urlreq.urlopen("http://127.0.0.1:8080/health", timeout=5)
    except Exception:
        print("ERROR: llama-server not responding on :11437 — run gpu_night.sh start first")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    count_q = """
        SELECT COUNT(*) FROM registry_enriched
        WHERE mission IS NOT NULL AND mission != ''
          AND (cause_tags IS NULL OR cause_tags = '[]' OR cause_tags = 'null')
          AND deductibility = 1 AND org_status = 'active'
          AND mission_source = 'ai_generated'
    """
    total = db.execute(count_q).fetchone()[0]
    limit = args.limit if args.limit else total
    print(f"Orgs to tag via LLM: {min(total, limit):,} (of {total:,} untagged active)", flush=True)

    # --small-first targets the invisible long tail (tiny/no-revenue orgs) so
    # GPU time lifts discoverability of small nonprofits (Stewardship P4).
    order_clause = "ORDER BY total_revenue ASC NULLS FIRST" if args.small_first else ""
    rows = db.execute(f"""
        SELECT EIN, organization_name, mission, NTEE1 FROM registry_enriched
        WHERE mission IS NOT NULL AND mission != ''
          AND (cause_tags IS NULL OR cause_tags = '[]' OR cause_tags = 'null')
          AND deductibility = 1 AND org_status = 'active'
          AND mission_source = 'ai_generated'
        {order_clause}
        LIMIT {limit}
    """).fetchall()
    db.close()

    orgs = [dict(r) for r in rows]
    batches = [orgs[i:i+BATCH] for i in range(0, len(orgs), BATCH)]

    tagged = 0; errors = 0; done = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(process_batch, b, args.dry_run): b for b in batches}
        for fut in as_completed(futs):
            t, e = fut.result()
            tagged += t; errors += e; done += len(futs[fut])
            elapsed = time.time() - t0
            rate = done / max(elapsed, 1)
            remaining = (len(orgs) - done) / max(rate, 1)
            print(
                f"\r  {tagged:,} tagged | {errors:,} errors | "
                f"{done:,}/{len(orgs):,} done | {rate:.0f}/s | "
                f"~{remaining/60:.0f}m left",
                end='', flush=True
            )

    print(f"\nDone: {tagged:,} orgs tagged, {errors:,} errors in {(time.time()-t0)/60:.1f}m")


if __name__ == "__main__":
    main()
