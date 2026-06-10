#!/usr/bin/env python3
"""
Generate missions for IRS_BMF orgs using Qwen2.5-32B (port 11437).

Targets: source='IRS_BMF', mission IS NULL or mission=''
Speed: ~60 tok/s, batch=20 → ~245K orgs in ~20-24 hours

Usage:
    python3 scripts/generate_missions_irs_bmf.py
    python3 scripts/generate_missions_irs_bmf.py --limit 100 --workers 2
"""

import sqlite3, json, time, argparse, sys, re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
GEN_URL = "http://127.0.0.1:11437/v1/chat/completions"
MODEL = "Qwen3-30B-A3B-Instruct-2507-Q4_K_M"
BATCH_SIZE = 20
TOKENS_PER_ORG = 80

# Canonical NTEE major-group labels — must match frontend/src/data/categories.ts
_NTEE_LABELS = {
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

_FEW_SHOT = """\
Write 1-2 sentence mission descriptions. Use org NAME first, then sector and location.
- Start with what they do, not what they are.
- Present tense, active voice.
- No flowery language ("dedicated to", "strives to", "passionate about").
- Use revenue/size context if available.

Examples:
- Meals on Wheels: "Delivers hot meals and support to homebound seniors across the region."
- Boys & Girls Club: "Provides after-school programs and mentorship for young people."
- Food Bank: "Distributes fresh food to families experiencing food insecurity."
"""

_written = 0
_errors = 0
_write_lock = Lock()

def _build_prompt(batch: list[dict]) -> str:
    lines = []
    for org in batch:
        ntee = _NTEE_LABELS.get(org.get("NTEE1") or "", "community service")
        revenue = org.get("total_revenue")
        size = f"${revenue:,.0f} annual revenue" if revenue else "community-based"
        city = (org.get("CITY") or "").title()
        lines.append(
            f'  ein="{org["EIN"]}", name="{org["organization_name"]}", sector="{ntee}", '
            f'location="{city}, {org.get("STATE", "")}", size="{size}"'
        )

    return (
        _FEW_SHOT + "\n"
        "Write mission sentences for these organizations. "
        'Return ONLY a JSON array: [{"ein": "...", "mission": "..."}]\n\n'
        "Organizations:\n" + "\n".join(lines)
    )

def _call_llm(batch: list[dict]) -> dict[str, str]:
    """Returns {ein: mission_text}. Only EINs actually in the batch are accepted —
    the model must echo back the ein= we gave it; anything else is a hallucination
    that would UPDATE the wrong org's row."""
    valid_eins = {org["EIN"] for org in batch}
    prompt = _build_prompt(batch)
    n = len(batch)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You output only raw JSON arrays. No markdown, no explanation."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max(400, TOKENS_PER_ORG * n),
    }
    try:
        r = requests.post(GEN_URL, json=payload, timeout=600)
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        content = msg.get("content") or ""
        m = re.search(r"\[.*\]", content, re.DOTALL)
        if m:
            parsed = json.loads(m.group())
            return {
                item["ein"]: item["mission"].strip()
                for item in (parsed if isinstance(parsed, list) else [])
                if item.get("ein") in valid_eins and item.get("mission")
            }
    except Exception as e:
        print(f"LLM error: {e}", flush=True)
    return {}

def _write_batch(results: dict[str, str], conn: sqlite3.Connection, batch_size: int):
    global _written, _errors
    if not results:
        _errors += batch_size
        return
    with _write_lock:
        # Other night workers (reembed_watchdog, donate pipeline) hold write locks
        # for long stretches — retry with backoff instead of dropping the batch.
        for attempt in range(6):
            try:
                conn.executemany(
                    "UPDATE registry_enriched SET mission=?, mission_source='ai_generated' WHERE EIN=?",
                    [(mission, ein) for ein, mission in results.items()]
                )
                conn.commit()
                _written += len(results)
                _errors += batch_size - len(results)
                return
            except sqlite3.OperationalError as e:
                if "locked" not in str(e).lower() or attempt == 5:
                    raise
                conn.rollback()
                time.sleep(10 * (attempt + 1))

def main(limit=None, workers=1):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT EIN, organization_name, NTEE1, CITY, STATE, total_revenue
        FROM registry_enriched
        WHERE source='IRS_BMF'
        AND (mission IS NULL OR mission='')
        AND organization_name IS NOT NULL
        ORDER BY COALESCE(total_revenue, 0) DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    rows = [dict(r) for r in conn.execute(query).fetchall()]
    total = len(rows)

    if not total:
        print("Nothing to generate.", flush=True)
        conn.close()
        return

    print(f"Generating {total:,} IRS_BMF missions  model={MODEL}  workers={workers}", flush=True)

    # Build batches
    batches = [rows[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    conn.close()

    start = time.time()

    def process(batch):
        global _errors
        tconn = sqlite3.connect(DB_PATH, timeout=60)
        tconn.execute("PRAGMA busy_timeout=60000")
        try:
            results = _call_llm(batch)
            _write_batch(results, tconn, len(batch))
        except Exception:
            _errors += len(batch)  # keep progress honest when a batch dies
            raise
        finally:
            tconn.close()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(process, b) for b in batches]
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                fut.result()
            except Exception as e:
                print(f"\nBatch error: {e}", flush=True)
            elapsed = time.time() - start
            rate = _written / elapsed if elapsed > 0 else 0
            pct = (_written + _errors) / total * 100 if total else 0
            eta = (total - _written - _errors) / rate / 60 if rate > 0 else 0
            print(
                f"\r  [{pct:5.1f}%] {_written:,} written  {_errors:,} errors  "
                f"{rate:.0f}/sec  ETA {eta:.1f}m",
                end="", flush=True
            )

    elapsed = time.time() - start
    print(f"\n\nDone in {elapsed/60:.1f} min — {_written:,} missions, {_errors:,} errors", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    main(limit=args.limit, workers=args.workers)
