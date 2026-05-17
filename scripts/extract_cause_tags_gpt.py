#!/usr/bin/env python3
"""
scripts/extract_cause_tags_gpt.py

Extract 3-5 cause tags per nonprofit using GPT-4o (structured output).
Replaces the qwen2.5:7b local run with higher consistency vocabulary.

Estimated cost: ~$14 for 23,529 orgs at gpt-4o pricing.
Estimated time: ~25-35 min.

Usage:
    export OPENAI_API_KEY=sk-...
    python3 scripts/extract_cause_tags_gpt.py              # all untagged orgs
    python3 scripts/extract_cause_tags_gpt.py --rebuild    # retag everything
    python3 scripts/extract_cause_tags_gpt.py --limit 30   # test run
    python3 scripts/extract_cause_tags_gpt.py --dry-run    # show prompt, no API calls
    python3 scripts/extract_cause_tags_gpt.py --model gpt-4o-mini  # cheaper option
"""

import sqlite3, json, sys, argparse, time, os, re
from pathlib import Path
from openai import OpenAI

BASE    = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "merit_registry.db"

MODEL      = "gpt-4o"
BATCH_SIZE = 20     # orgs per API call — gpt-4o handles larger context comfortably
MAX_RETRIES = 3

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

SYSTEM_PROMPT = """\
You extract cause tags from US nonprofit mission statements for a donor-discovery platform.

Rules:
- Return a JSON object mapping position numbers (as strings "1", "2" ...) to arrays of tags.
- Each org gets 3-5 tags. Never fewer than 3.
- Tags are 2-4 words, lowercase, specific, and consistent across similar orgs.
- Use a stable vocabulary: always "food bank" not "food assistance" or "food rescue"; \
always "affordable housing" not "low-income housing" or "family homes"; \
always "mental health" not "behavioral health" or "mental health care".
- Include: the type of work, the population served, and the approach or method when available.
- Never use generic tags: "community", "nonprofit", "support", "services", "mission", "charity", "501c3".
- Return only valid JSON — no markdown, no explanation, no extra text.

Example output:
{"1": ["food bank", "hunger relief", "food rescue", "low-income families"], \
"2": ["affordable housing", "home construction", "volunteer building", "poverty reduction"]}"""

PROMPT_TEMPLATE = """\
Extract 3-5 cause tags for each nonprofit. Return JSON: {{"1": ["tag",...], "2": [...], ...}}

{orgs}"""


def fmt_org(pos: int, row) -> str:
    _, name, ntee1, mission = row
    ntee_label    = NTEE_BROAD.get((ntee1 or "").strip().upper(), "")
    mission_short = (mission or "")[:300].strip()
    lines = [f"{pos}. {name}"]
    if ntee_label:
        lines.append(f"   Category: {ntee_label}")
    if mission_short:
        lines.append(f"   Mission: {mission_short}")
    return "\n".join(lines)


def extract_json(text: str) -> dict:
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


def ensure_column(db: sqlite3.Connection):
    cols = {r[1] for r in db.execute("PRAGMA table_info(registry_enriched)")}
    if "cause_tags" not in cols:
        db.execute("ALTER TABLE registry_enriched ADD COLUMN cause_tags TEXT")
        db.commit()
        print("Added cause_tags column to registry_enriched")


def run(limit=None, rebuild=False, dry_run=False):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and not dry_run:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Run:  export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    client = OpenAI(api_key=api_key) if not dry_run else None

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
    tokens_in  = 0
    tokens_out = 0
    t_start = time.time()

    print(f"Orgs to tag: {total:,}  model: {MODEL}  batch: {BATCH_SIZE}")
    print(f"Est. cost:   ${total * 0.000600:.2f} (rough, based on ~100 tokens/org input)\n")

    if dry_run:
        batch = rows[:min(BATCH_SIZE, len(rows))]
        org_block = "\n\n".join(fmt_org(i + 1, r) for i, r in enumerate(batch))
        print("--- System ---")
        print(SYSTEM_PROMPT[:400], "...\n")
        print("--- Prompt ---")
        print(PROMPT_TEMPLATE.format(orgs=org_block[:800]), "...\n")
        return

    for batch_start in range(0, total, BATCH_SIZE):
        batch     = rows[batch_start : batch_start + BATCH_SIZE]
        org_block = "\n\n".join(fmt_org(i + 1, r) for i, r in enumerate(batch))
        prompt    = PROMPT_TEMPLATE.format(orgs=org_block)

        tags = {}
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=600,
                    response_format={"type": "json_object"},
                )
                tokens_in  += resp.usage.prompt_tokens
                tokens_out += resp.usage.completion_tokens
                tags = json.loads(resp.choices[0].message.content)
                break
            except Exception as e:
                errors += 1
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"\n  Failed batch {batch_start}: {e}")

        updates = []
        for i, row in enumerate(batch):
            ein      = row[0]
            tag_list = tags.get(str(i + 1), [])
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

        done   += len(batch)
        elapsed = time.time() - t_start
        rate    = done / elapsed if elapsed > 0 else 0
        eta     = (total - done) / rate if rate > 0 else 0
        pct     = done / total * 100
        cost_so_far = tokens_in * 2.50/1e6 + tokens_out * 10.00/1e6
        print(
            f"  [{pct:5.1f}%] {done:,}/{total:,}  "
            f"{rate:.1f} orgs/s  "
            f"${cost_so_far:.2f}  "
            f"ETA {eta/60:.1f}m",
            end="\r", flush=True,
        )

    elapsed = time.time() - t_start
    final_cost = tokens_in * 2.50/1e6 + tokens_out * 10.00/1e6
    print(f"\n\nDone — {done:,} orgs in {elapsed/60:.1f} min")
    print(f"Tokens: {tokens_in:,} in / {tokens_out:,} out")
    print(f"Cost:   ${final_cost:.2f}")

    samples = db.execute("""
        SELECT organization_name, NTEE1, cause_tags
        FROM registry_enriched
        WHERE cause_tags IS NOT NULL
        ORDER BY COALESCE(ntee1_percentile, 0) DESC
        LIMIT 20
    """).fetchall()
    print("\nSample results:")
    for name, ntee, ct in samples:
        tag_list = json.loads(ct) if ct else []
        print(f"  [{ntee}] {name[:45]:<45}  {', '.join(tag_list)}")

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",   type=int,           help="Process N orgs")
    parser.add_argument("--rebuild", action="store_true", help="Retag all from scratch")
    parser.add_argument("--dry-run", action="store_true", help="Show prompt, no API calls")
    parser.add_argument("--model",   default=MODEL,      help=f"OpenAI model (default: {MODEL})")
    args = parser.parse_args()

    MODEL = args.model
    run(limit=args.limit, rebuild=args.rebuild, dry_run=args.dry_run)
