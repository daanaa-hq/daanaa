#!/usr/bin/env python3
"""
enrich_cause_tags_ollama.py
Ollama-based cause_tags enrichment for orgs with no NTEE and no keyword match.
Runs on the local server — zero Anthropic API cost.

Uses gemma2:2b (1.5 GB, fast) with concurrent workers.
Safe to interrupt and resume — skips orgs that already have tags.

Usage:
    python3 scripts/enrich_cause_tags_ollama.py
    python3 scripts/enrich_cause_tags_ollama.py --workers 16 --model gemma2:2b
    python3 scripts/enrich_cause_tags_ollama.py --dry-run --sample 20
    python3 scripts/enrich_cause_tags_ollama.py --limit 10000   # partial run
"""

import sqlite3, json, re, argparse, time, os, sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

DB_PATH      = os.path.expanduser("~/meritgiving/data/merit_registry.db")
OLLAMA_URL   = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma2:2b"
BATCH        = 500     # rows fetched per DB read
COMMIT_EVERY = 100     # writes between commits

SYSTEM_PROMPT = (
    "You tag nonprofits for a donor-facing directory. "
    "Given an organization name, return ONLY a JSON array of 2-4 short, "
    "plain-English cause tags (e.g. [\"food\",\"hunger relief\"]). "
    "No explanation, no markdown, just the JSON array."
)


def ask_ollama(name: str, city: str, model: str, timeout: int = 12) -> list[str]:
    """Call Ollama and return a list of tags. Returns [] on failure."""
    context = name.strip()
    if city:
        context += f" ({city.strip()})"
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": model,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 60},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": context},
            ],
        }, timeout=timeout)
        resp.raise_for_status()
        text = resp.json()["message"]["content"].strip()

        # Try direct JSON parse first
        try:
            tags = json.loads(text)
            if isinstance(tags, list):
                return [str(t).strip().lower()[:60] for t in tags if str(t).strip()][:5]
        except json.JSONDecodeError:
            pass

        # Fallback: extract array from text
        m = re.search(r'\[.*?\]', text, re.DOTALL)
        if m:
            try:
                tags = json.loads(m.group())
                if isinstance(tags, list):
                    return [str(t).strip().lower()[:60] for t in tags if str(t).strip()][:5]
            except json.JSONDecodeError:
                pass

        return []
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers",  type=int, default=8,
                        help="Concurrent Ollama workers (default 8)")
    parser.add_argument("--model",    default=DEFAULT_MODEL,
                        help=f"Ollama model (default {DEFAULT_MODEL})")
    parser.add_argument("--limit",    type=int, default=0,
                        help="Stop after N orgs (0 = unlimited)")
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--sample",   type=int, default=10,
                        help="Sample size for dry-run (default 10)")
    args = parser.parse_args()

    # Verify Ollama is reachable
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        if args.model not in models:
            print(f"Warning: model '{args.model}' not found in Ollama. Available: {models}")
    except Exception as e:
        print(f"Cannot reach Ollama at localhost:11434: {e}")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    write_lock = Lock()

    todo_q = """
        SELECT EIN, organization_name, CITY FROM registry_enriched
        WHERE (cause_tags IS NULL OR cause_tags = '')
          AND (NTEE1 IS NULL OR NTEE1 = '')
    """
    todo = db.execute(f"SELECT COUNT(*) FROM ({todo_q})").fetchone()[0]
    target = min(todo, args.limit) if args.limit else todo
    print(f"Orgs to enrich: {todo:,}")
    if args.limit:
        print(f"Running limited to: {args.limit:,}")
    print(f"Model: {args.model}  Workers: {args.workers}")

    if args.dry_run:
        rows = db.execute(todo_q + f" ORDER BY RANDOM() LIMIT {args.sample}").fetchall()
        print(f"\nDry run — {len(rows)} samples:\n")
        for r in rows:
            tags = ask_ollama(r["organization_name"], r["CITY"] or "", args.model)
            status = "✓" if tags else "·"
            print(f"  {status} {(r['organization_name'] or '')[:55]:<55} → {tags}")
        db.close()
        return

    start     = time.time()
    written   = 0
    failed    = 0
    processed = 0
    pending_writes: list[tuple[str, str]] = []

    def flush(force=False):
        nonlocal written
        if not pending_writes:
            return
        if not force and len(pending_writes) < COMMIT_EVERY:
            return
        with write_lock:
            db.executemany(
                "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                [(json.dumps(tags), ein) for tags, ein in pending_writes],
            )
            db.commit()
            written += len(pending_writes)
            pending_writes.clear()

    rows = db.execute(todo_q + (f" LIMIT {args.limit}" if args.limit else "")).fetchall()

    def process(row):
        tags = ask_ollama(row["organization_name"] or "", row["CITY"] or "", args.model)
        return row["EIN"], tags

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process, r): r for r in rows}
        for fut in as_completed(futures):
            processed += 1
            ein, tags = fut.result()
            if tags:
                pending_writes.append((tags, ein))
                flush()
            else:
                failed += 1

            if processed % 50 == 0:
                elapsed = time.time() - start
                rate = processed / elapsed
                eta = (target - processed) / rate if rate > 0 else 0
                pct = processed / target * 100 if target else 0
                print(
                    f"  {processed:>7,}/{target:,} ({pct:.0f}%)  "
                    f"{written:>7,} written  {failed:>5,} failed  "
                    f"{rate:.0f}/s  ETA {eta/60:.0f}m",
                    end="\r"
                )

    flush(force=True)
    elapsed = time.time() - start
    print(f"\n\nCompleted in {elapsed/60:.1f} min")
    print(f"  Tagged:   {written:,}")
    print(f"  Failed:   {failed:,}  (no parseable response)")
    db.close()


if __name__ == "__main__":
    main()
