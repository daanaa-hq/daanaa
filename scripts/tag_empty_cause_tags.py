#!/usr/bin/env python3
"""
tag_empty_cause_tags.py
Fix orgs where cause_tags='[]' — the empty JSON array state left when NTEE-keyword
rules ran but produced nothing. Uses Ollama with org name + mission text (if present).

Usage:
    python3 scripts/tag_empty_cause_tags.py
    python3 scripts/tag_empty_cause_tags.py --workers 6 --model qwen2.5:7b
    python3 scripts/tag_empty_cause_tags.py --dry-run --sample 20
    python3 scripts/tag_empty_cause_tags.py --limit 500
"""

import sqlite3, json, re, argparse, time, os, sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

DB_PATH       = os.path.expanduser("~/meritgiving/data/merit_registry.db")
OLLAMA_URL    = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:7b"
BATCH         = 500
COMMIT_EVERY  = 50

SYSTEM_PROMPT = (
    "You tag nonprofits for a donor-facing directory. "
    "Given an organization name and optional description, return ONLY a JSON array "
    "of 2-5 short plain-English cause tags (e.g. [\"food\",\"hunger relief\",\"community\"]). "
    "Tags must reflect what the org actually does, not its legal structure. "
    "Key rules: "
    "PTA, PTO, PTSA, PTSO → [\"education\",\"parent involvement\",\"schools\"]. "
    "Disease/condition abbreviations (NBIA, ALS, MS, etc.) → use the description to find the full name and tag accordingly. "
    "Benevolent associations → tag by their community (e.g. ethnic group, profession). "
    "No explanation, no markdown — just the JSON array."
)


def ask_ollama(name: str, city: str, mission: str, model: str, timeout: int = 20) -> list[str]:
    parts = [name.strip()]
    if city:
        parts.append(f"Location: {city.strip()}")
    if mission:
        # Trim to ~300 chars — enough context, not too slow
        m = mission.strip().replace('"', "'")
        parts.append(f"Description: {m[:300]}")
    context = "\n".join(parts)

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": model,
            "stream": False,
            "think": False,  # disable qwen3 thinking mode — eats token budget before answer
            "options": {"temperature": 0, "num_predict": 150},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": context},
            ],
        }, timeout=timeout)
        resp.raise_for_status()
        text = resp.json()["message"]["content"].strip()

        try:
            tags = json.loads(text)
            if isinstance(tags, list):
                return [str(t).strip().lower()[:60] for t in tags if str(t).strip()][:5]
        except json.JSONDecodeError:
            pass

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
    parser.add_argument("--workers",  type=int, default=4)
    parser.add_argument("--model",    default=DEFAULT_MODEL)
    parser.add_argument("--limit",    type=int, default=0)
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--sample",   type=int, default=10)
    args = parser.parse_args()

    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        if args.model not in models:
            print(f"Warning: model '{args.model}' not in Ollama. Available: {models}")
    except Exception as e:
        print(f"Cannot reach Ollama: {e}")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    write_lock = Lock()

    todo_q = """
        SELECT EIN, organization_name, CITY, mission
        FROM registry_enriched
        WHERE cause_tags = '[]'
    """
    total = db.execute(f"SELECT COUNT(*) FROM ({todo_q})").fetchone()[0]
    target = min(total, args.limit) if args.limit else total
    print(f"Orgs with cause_tags='[]': {total:,}")
    print(f"Target: {target:,}  Model: {args.model}  Workers: {args.workers}")

    if args.dry_run:
        rows = db.execute(todo_q + f" ORDER BY RANDOM() LIMIT {args.sample}").fetchall()
        print(f"\nDry run — {len(rows)} samples:\n")
        for row in rows:
            tags = ask_ollama(
                row["organization_name"] or "",
                row["CITY"] or "",
                row["mission"] or "",
                args.model
            )
            status = "✓" if tags else "·"
            has_m  = "M" if row["mission"] else " "
            print(f"  {status}{has_m} {(row['organization_name'] or '')[:55]:<55} → {tags}")
        db.close()
        return

    query = todo_q + (f" LIMIT {target}" if args.limit else "")
    rows = db.execute(query).fetchall()

    start     = time.time()
    written   = 0
    failed    = 0
    processed = 0
    pending: list[tuple[list, str]] = []

    def flush(force=False):
        nonlocal written
        if not pending:
            return
        if not force and len(pending) < COMMIT_EVERY:
            return
        with write_lock:
            db.executemany(
                "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                [(json.dumps(tags), ein) for tags, ein in pending],
            )
            db.commit()
            written += len(pending)
            pending.clear()

    def process(row):
        tags = ask_ollama(
            row["organization_name"] or "",
            row["CITY"] or "",
            row["mission"] or "",
            args.model,
        )
        return row["EIN"], tags

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process, r): r for r in rows}
        for fut in as_completed(futures):
            processed += 1
            ein, tags = fut.result()
            if tags:
                pending.append((tags, ein))
                flush()
            else:
                failed += 1

            if processed % 25 == 0:
                elapsed = time.time() - start
                rate    = processed / elapsed
                eta     = (target - processed) / rate if rate > 0 else 0
                pct     = processed / target * 100 if target else 0
                print(
                    f"  {processed:>5,}/{target:,} ({pct:.0f}%)  "
                    f"{written:>5,} written  {failed:>4,} failed  "
                    f"{rate:.1f}/s  ETA {eta/60:.0f}m",
                    end="\r", flush=True
                )

    flush(force=True)
    elapsed = time.time() - start
    print(f"\n\nDone in {elapsed/60:.1f} min")
    print(f"  Tagged:  {written:,}")
    print(f"  Failed:  {failed:,}")

    # Final count
    remaining = db.execute("SELECT COUNT(*) FROM registry_enriched WHERE cause_tags='[]'").fetchone()[0]
    print(f"  Still empty: {remaining:,}")
    db.close()


if __name__ == "__main__":
    main()
