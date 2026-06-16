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
LLM_URL = "http://localhost:11437/v1/chat/completions"
MODEL   = "local"   # llama-server accepts any string as model name
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


def parse_tags(raw: str, expected: int) -> list[list[str]]:
    """Parse LLM output into a list-of-lists, one per org."""
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
        return [[] for _ in range(expected)]
    if not isinstance(parsed, list):
        return [[] for _ in range(expected)]
    # If it's a flat list of strings (single org response), wrap it
    if parsed and isinstance(parsed[0], str):
        return [parsed] + [[] for _ in range(expected - 1)]
    # Normalize: ensure each element is a list of strings
    result = []
    for item in parsed[:expected]:
        if isinstance(item, list):
            result.append([str(t).lower().strip() for t in item if t])
        else:
            result.append([])
    while len(result) < expected:
        result.append([])
    return result


def process_batch(orgs: list[dict], dry_run: bool) -> tuple[int, int]:
    """Return (tagged_count, error_count)."""
    if dry_run:
        for o in orgs:
            print(f"  DRY: {o['organization_name'][:60]}")
        return len(orgs), 0
    prompt = build_prompt(orgs)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 512,
    }
    try:
        raw    = llm_call(payload)
        parsed = parse_tags(raw, len(orgs))
    except Exception as e:
        print(f"  LLM error (batch of {len(orgs)}): {e}", flush=True)
        return 0, len(orgs)

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
    args = ap.parse_args()

    # Check llama-server is up
    try:
        urlreq.urlopen("http://localhost:11437/health", timeout=5)
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
    """
    total = db.execute(count_q).fetchone()[0]
    limit = args.limit if args.limit else total
    print(f"Orgs to tag via LLM: {min(total, limit):,} (of {total:,} untagged active)", flush=True)

    rows = db.execute(f"""
        SELECT EIN, organization_name, mission, NTEE1 FROM registry_enriched
        WHERE mission IS NOT NULL AND mission != ''
          AND (cause_tags IS NULL OR cause_tags = '[]' OR cause_tags = 'null')
          AND deductibility = 1 AND org_status = 'active'
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
