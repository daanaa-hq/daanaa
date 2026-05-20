#!/usr/bin/env python3
"""
scripts/tag_near_miss_diamonds.py

Tags near-miss diamond orgs (pass all criteria except cause_tags) using
org name + NTEE code as signal. Most have no mission text.

Uses Ollama qwen2.5:7b locally — free, no API calls.
After completion, re-run compute_diamonds.py to promote them to diamonds.

Usage:
    python3 scripts/tag_near_miss_diamonds.py
    python3 scripts/tag_near_miss_diamonds.py --dry-run
    python3 scripts/tag_near_miss_diamonds.py --limit 50
"""

import sqlite3, json, argparse, time, urllib.request, urllib.error
from pathlib import Path

DB_PATH    = Path.home() / "meritgiving" / "data" / "merit_registry.db"
OLLAMA_URL = "http://localhost:11434"
MODEL      = "qwen2.5:7b"

NTEE_BROAD = {
    "A": "Arts, Culture & Humanities", "B": "Education",
    "C": "Environment & Conservation", "D": "Animal Welfare",
    "E": "Health Care", "F": "Mental Health & Crisis Services",
    "G": "Disease & Medical Disorders", "H": "Medical Research",
    "I": "Crime & Legal Services", "J": "Employment & Jobs",
    "K": "Food, Agriculture & Nutrition", "L": "Housing & Shelter",
    "M": "Public Safety & Emergency", "N": "Recreation, Sports & Leisure",
    "O": "Youth Development", "P": "Human Services",
    "Q": "International & Global Affairs", "R": "Civil Rights & Advocacy",
    "S": "Community Development", "T": "Philanthropy & Grantmaking",
    "U": "Science & Technology", "V": "Social Science Research",
    "W": "Public & Societal Benefit", "X": "Religion & Spirituality",
    "Y": "Mutual Aid & Membership", "Z": "Unknown",
}

PROMPT = """\
Tag this US nonprofit for a giving directory.

Name: {name}
Sector: {sector}
Mission: {mission}

Give 3-5 cause tags a donor would search for. Plain English, 2-4 words each. \
Focus on what they DO.

Return ONLY a JSON array. Example: ["food security", "youth mentorship"]

Tags:"""


def _ollama(prompt: str) -> str | None:
    body = json.dumps({"model": MODEL, "prompt": prompt,
                       "stream": False, "options": {"temperature": 0.1}}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["response"].strip()
    except Exception as e:
        print(f"  ollama error: {e}")
        return None


def _parse(raw: str) -> list[str]:
    import re
    m = re.search(r'\[.*?\]', raw, re.S)
    if not m:
        return []
    try:
        tags = json.loads(m.group(0))
        return [str(t).lower().strip() for t in tags if t][:5]
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.row_factory = sqlite3.Row

    rows = db.execute("""
        SELECT r.EIN, r.organization_name, r.NTEE1, r.mission
        FROM registry_enriched r
        INNER JOIN (
            SELECT EIN FROM propublica_financials
            WHERE totfuncexpns > 0 AND totnetassetend IS NOT NULL
            GROUP BY EIN HAVING COUNT(*) >= 3
        ) f ON f.EIN = r.EIN
        WHERE r.total_revenue > 0 AND r.total_revenue < 500000
          AND r.program_expense_pct >= 70
          AND r.ruling_date <= date('now', '-5 years')
          AND (r.cause_tags IS NULL OR r.cause_tags = '' OR r.cause_tags = '[]')
        ORDER BY r.total_revenue DESC
    """).fetchall()

    if args.limit:
        rows = rows[:args.limit]

    total = len(rows)
    print(f"[start] {total:,} near-miss orgs to tag  model={MODEL}")

    if args.dry_run:
        for r in rows[:5]:
            sector = NTEE_BROAD.get(r["NTEE1"] or "Z", "General Nonprofit")
            mission = r["mission"] or "(no mission text)"
            print(f"  {r['EIN']}  {r['organization_name'][:50]}")
            print(f"    sector: {sector}  mission: {mission[:60]}")
        print(f"\n[dry-run] would tag {total:,} orgs — no writes performed")
        return

    # Quick Ollama check
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5)
    except Exception:
        print("[error] Ollama not reachable at", OLLAMA_URL)
        return

    updated, skipped, errors = 0, 0, 0
    t0 = time.time()

    for i, row in enumerate(rows):
        ein  = row["EIN"]
        name = row["organization_name"] or ""
        ntee = row["NTEE1"] or "Z"
        sector = NTEE_BROAD.get(ntee, "General Nonprofit")
        mission = row["mission"] or "(no mission text — infer from name and sector)"

        prompt = PROMPT.format(name=name, sector=sector, mission=mission[:400])
        raw = _ollama(prompt)

        if raw is None:
            errors += 1
            continue

        tags = _parse(raw)
        if not tags:
            skipped += 1
            continue

        for attempt in range(10):
            try:
                db.execute(
                    "UPDATE registry_enriched SET cause_tags=? WHERE EIN=?",
                    (json.dumps(tags), ein)
                )
                db.commit()
                break
            except sqlite3.OperationalError as lock_err:
                if "locked" in str(lock_err) and attempt < 9:
                    time.sleep(0.5)
                else:
                    errors += 1
                    break
        else:
            continue
        updated += 1

        if updated % 50 == 0:
            elapsed = time.time() - t0
            rate = updated / elapsed
            remaining = (total - i - 1) / rate if rate > 0 else 0
            print(f"  [{i+1}/{total}] {updated} tagged  {rate:.1f}/s  ~{remaining/60:.1f} min left")

    db.commit()
    print(f"\n[done] {updated} tagged  {skipped} skipped  {errors} errors")
    print("Run compute_diamonds.py to promote new tags to diamonds.")


if __name__ == "__main__":
    main()
