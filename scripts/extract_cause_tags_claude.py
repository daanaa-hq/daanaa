#!/usr/bin/env python3
"""
scripts/extract_cause_tags_claude.py

Extract 3-5 cause tags per nonprofit using Claude Sonnet via Anthropic API.

Estimated cost:  ~$19 for 23,529 orgs (Sonnet 4.6 pricing)
Estimated time:  ~20-25 min

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 scripts/extract_cause_tags_claude.py              # all untagged
    python3 scripts/extract_cause_tags_claude.py --rebuild    # retag everything
    python3 scripts/extract_cause_tags_claude.py --limit 30   # test run
    python3 scripts/extract_cause_tags_claude.py --dry-run    # show prompt only
    python3 scripts/extract_cause_tags_claude.py --model claude-haiku-4-5-20251001
"""

import sqlite3, json, sys, argparse, time, os, re
from pathlib import Path
import anthropic

BASE    = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "merit_registry.db"

MODEL      = "claude-sonnet-4-6"
BATCH_SIZE = 20
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
- Return a JSON object mapping position numbers (as strings "1", "2"...) to arrays of tags.
- Each org gets exactly 3-5 tags. Never fewer than 3.
- Tags are 2-4 words, lowercase, specific, and consistent across similar orgs.
- Use stable vocabulary: always "food bank" not "food assistance" or "food rescue"; \
always "affordable housing" not "low-income housing"; \
always "mental health" not "behavioral health"; \
always "civil liberties" not "civil rights advocacy" for ACLU-type orgs.
- Cover: the type of work, population served, and approach/method when available.
- Never use generic filler: "community", "nonprofit", "support", "services", "mission", \
"charity", "501c3", "organization", "helping", "engagement".
- Return only the JSON object — no markdown, no explanation."""

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
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not dry_run:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Run:  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key) if not dry_run else None

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

    total      = len(rows)
    done       = 0
    errors     = 0
    tokens_in  = 0
    tokens_out = 0
    t_start    = time.time()

    # Sonnet 4.6 pricing: $3/M input, $15/M output
    INPUT_RATE  = 3.00 / 1_000_000
    OUTPUT_RATE = 15.00 / 1_000_000

    print(f"Orgs to tag:  {total:,}")
    print(f"Model:        {MODEL}  (batch: {BATCH_SIZE})")
    print(f"Est. cost:    ~${total * 150 * INPUT_RATE + total * 25 * OUTPUT_RATE:.2f}\n")

    if dry_run:
        batch = rows[:min(BATCH_SIZE, len(rows))]
        org_block = "\n\n".join(fmt_org(i + 1, r) for i, r in enumerate(batch))
        print("--- System ---")
        print(SYSTEM_PROMPT[:500], "...\n")
        print("--- Prompt sample ---")
        print(PROMPT_TEMPLATE.format(orgs=org_block[:1000]), "...")
        return

    for batch_start in range(0, total, BATCH_SIZE):
        batch     = rows[batch_start : batch_start + BATCH_SIZE]
        org_block = "\n\n".join(fmt_org(i + 1, r) for i, r in enumerate(batch))
        prompt    = PROMPT_TEMPLATE.format(orgs=org_block)

        tags = {}
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.messages.create(
                    model=MODEL,
                    max_tokens=700,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                tokens_in  += resp.usage.input_tokens
                tokens_out += resp.usage.output_tokens
                tags = extract_json(resp.content[0].text)
                break
            except anthropic.RateLimitError:
                time.sleep(60)
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

        done        += len(batch)
        elapsed      = time.time() - t_start
        rate         = done / elapsed if elapsed > 0 else 0
        eta          = (total - done) / rate if rate > 0 else 0
        pct          = done / total * 100
        cost_so_far  = tokens_in * INPUT_RATE + tokens_out * OUTPUT_RATE
        print(
            f"  [{pct:5.1f}%] {done:,}/{total:,}  "
            f"{rate:.1f} orgs/s  "
            f"${cost_so_far:.2f}  "
            f"ETA {eta/60:.1f}m",
            end="\r", flush=True,
        )

    elapsed    = time.time() - t_start
    final_cost = tokens_in * INPUT_RATE + tokens_out * OUTPUT_RATE
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
    parser.add_argument("--dry-run", action="store_true", help="Show prompt only, no API calls")
    parser.add_argument("--model",   default=MODEL,      help=f"Anthropic model (default: {MODEL})")
    args = parser.parse_args()

    MODEL = args.model
    run(limit=args.limit, rebuild=args.rebuild, dry_run=args.dry_run)
