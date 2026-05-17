#!/usr/bin/env python3
"""
scripts/extract_cause_tags.py

Extract 3-5 cause/focus tags from nonprofit mission statements using a local
LLM (ollama qwen2.5:7b). Results stored as JSON arrays in registry_enriched.cause_tags.

Usage:
    python3 scripts/extract_cause_tags.py              # process all untagged orgs
    python3 scripts/extract_cause_tags.py --limit 50   # test run
    python3 scripts/extract_cause_tags.py --rebuild    # retag everything
    python3 scripts/extract_cause_tags.py --dry-run    # show sample prompts
    python3 scripts/extract_cause_tags.py --model qwen2.5:14b  # after embeddings finish
"""

import sqlite3, json, sys, argparse, time, re
from pathlib import Path
import urllib.request, urllib.error

BASE    = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "merit_registry.db"

OLLAMA_URL    = "http://localhost:11434/api/generate"
MODEL         = "qwen2.5:7b"
BATCH_SIZE    = 12     # orgs per LLM call
REQUEST_DELAY = 0.05   # seconds between API calls

NTEE_BROAD = {
    "A": "Arts, Culture & Humanities",
    "B": "Education",
    "C": "Environment & Conservation",
    "D": "Animal Welfare",
    "E": "Health Care",
    "F": "Mental Health & Crisis Services",
    "G": "Disease & Medical Disorders",
    "H": "Medical Research",
    "I": "Crime & Legal Services",
    "J": "Employment & Jobs",
    "K": "Food, Agriculture & Nutrition",
    "L": "Housing & Shelter",
    "M": "Public Safety & Emergency",
    "N": "Recreation, Sports & Leisure",
    "O": "Youth Development",
    "P": "Human Services",
    "Q": "International & Global Affairs",
    "R": "Civil Rights & Advocacy",
    "S": "Community Development",
    "T": "Philanthropy & Grantmaking",
    "U": "Science & Technology",
    "V": "Social Science Research",
    "W": "Public & Societal Benefit",
    "X": "Religion & Spirituality",
    "Y": "Mutual Aid & Membership",
    "Z": "Unknown",
}

SYSTEM_PROMPT = (
    'You extract cause tags from nonprofit mission statements. '
    'Return ONLY a JSON object mapping position numbers (as strings) to arrays of 3-5 short descriptive tags (2-4 words each). '
    'Tags must be lowercase, specific, and descriptive. Include: type of work, population served, and approach when available. '
    'Example: {"1": ["classical music", "live performance", "arts education", "community access"]} '
    'Never include generic tags like "community", "nonprofit", "support", "services", or "mission". '
    'Return only valid JSON — no markdown, no explanation.'
)

PROMPT_TEMPLATE = (
    'Extract 3-5 cause tags for each nonprofit. '
    'Return JSON: {{"1": ["tag", ...], "2": [...], ...}}\n\n'
    '{orgs}'
)


def call_ollama(prompt: str, timeout: int = 90) -> str:
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 800},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            if result.get("error"):
                raise RuntimeError(result["error"])
            return result.get("response", "")
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        try:
            err_detail = json.loads(body_bytes).get("error", body_bytes.decode())
        except Exception:
            err_detail = body_bytes.decode()[:200]
        raise RuntimeError(f"HTTP {e.code}: {err_detail}")


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of LLM response text."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def fmt_org(pos: int, row) -> str:
    _, name, ntee1, mission = row
    ntee_label   = NTEE_BROAD.get((ntee1 or "").strip().upper(), "")
    mission_short = (mission or "")[:250].strip()
    lines = [f"{pos}. {name}"]
    if ntee_label:
        lines.append(f"   Category: {ntee_label}")
    if mission_short:
        lines.append(f"   Mission: {mission_short}")
    return "\n".join(lines)


def ensure_column(db: sqlite3.Connection):
    cols = {r[1] for r in db.execute("PRAGMA table_info(registry_enriched)")}
    if "cause_tags" not in cols:
        db.execute("ALTER TABLE registry_enriched ADD COLUMN cause_tags TEXT")
        db.commit()
        print("Added cause_tags column to registry_enriched")


def run(limit=None, rebuild=False, dry_run=False):
    db = sqlite3.connect(DB_PATH)
    ensure_column(db)

    if rebuild:
        db.execute("UPDATE registry_enriched SET cause_tags = NULL")
        db.commit()
        print("Cleared existing cause_tags")

    rows = db.execute("""
        SELECT EIN, organization_name, NTEE1, mission
        FROM registry_enriched
        WHERE mission IS NOT NULL AND LENGTH(TRIM(mission)) > 30
          AND cause_tags IS NULL
        ORDER BY COALESCE(ntee1_percentile, 0) DESC
    """).fetchall()

    if limit:
        rows = rows[:limit]

    total   = len(rows)
    done    = 0
    errors  = 0
    t_start = time.time()

    print(f"Orgs to tag: {total:,} (model: {MODEL}, batch: {BATCH_SIZE})\n")

    if dry_run:
        batch = rows[:min(BATCH_SIZE, len(rows))]
        org_block = "\n\n".join(fmt_org(i + 1, r) for i, r in enumerate(batch))
        print("--- Sample prompt ---")
        print(PROMPT_TEMPLATE.format(orgs=org_block))
        return

    for batch_start in range(0, total, BATCH_SIZE):
        batch     = rows[batch_start : batch_start + BATCH_SIZE]
        org_block = "\n\n".join(fmt_org(i + 1, r) for i, r in enumerate(batch))
        prompt    = PROMPT_TEMPLATE.format(orgs=org_block)

        try:
            raw  = call_ollama(prompt)
            tags = extract_json(raw)
        except Exception as e:
            errors += 1
            print(f"\n  Error batch {batch_start}: {e}")
            time.sleep(3)
            continue

        updates = []
        for i, row in enumerate(batch):
            ein      = row[0]
            pos_key  = str(i + 1)
            tag_list = tags.get(pos_key, [])
            if isinstance(tag_list, list) and tag_list:
                tag_list = [t.lower().strip() for t in tag_list if isinstance(t, str) and len(t) > 2][:5]
                if tag_list:
                    updates.append((json.dumps(tag_list), ein))

        if updates:
            db.executemany(
                "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                updates
            )
            db.commit()

        done  += len(batch)
        elapsed = time.time() - t_start
        rate    = done / elapsed if elapsed > 0 else 0
        eta     = (total - done) / rate if rate > 0 else 0
        pct     = done / total * 100
        tagged  = len(updates)
        print(
            f"  [{pct:5.1f}%] {done:,}/{total:,}  "
            f"{rate:.1f} orgs/s  tagged {tagged}/{len(batch)}  "
            f"ETA {eta/60:.1f}m",
            end="\r", flush=True,
        )

        if REQUEST_DELAY > 0:
            time.sleep(REQUEST_DELAY)

    elapsed = time.time() - t_start
    print(f"\n\nDone — {done:,} orgs processed, {errors} errors, {elapsed/60:.1f} min")

    samples = db.execute("""
        SELECT organization_name, NTEE1, cause_tags
        FROM registry_enriched
        WHERE cause_tags IS NOT NULL
        ORDER BY COALESCE(ntee1_percentile, 0) DESC
        LIMIT 15
    """).fetchall()
    print("\nSample results:")
    for name, ntee, ct in samples:
        tags_list = json.loads(ct) if ct else []
        print(f"  [{ntee}] {name[:45]:<45}  {', '.join(tags_list)}")

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",   type=int,           help="Process N orgs (test mode)")
    parser.add_argument("--rebuild", action="store_true", help="Retag all orgs from scratch")
    parser.add_argument("--dry-run", action="store_true", help="Show sample prompt, don't run")
    parser.add_argument("--model",   default=MODEL,      help=f"Ollama model (default: {MODEL})")
    args = parser.parse_args()

    MODEL = args.model
    run(limit=args.limit, rebuild=args.rebuild, dry_run=args.dry_run)
