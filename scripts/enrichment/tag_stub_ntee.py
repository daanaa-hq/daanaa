#!/usr/bin/env python3
"""
scripts/tag_stub_ntee.py

Assigns NTEE1 codes to bmf_stub records using Ollama (batch mode, CPU-safe).
Batches 50 orgs per LLM call to amortise inference overhead.

Priority: stubs with financials first (can be scored immediately after).

Usage:
    python3 scripts/tag_stub_ntee.py
    python3 scripts/tag_stub_ntee.py --priority-only   # 45K with revenue first
    python3 scripts/tag_stub_ntee.py --model gemma2:2b
    python3 scripts/tag_stub_ntee.py --batch 30
"""

import sqlite3, json, time, argparse, urllib.request
from pathlib import Path

DB_PATH    = Path.home() / "meritgiving" / "data" / "merit_registry.db"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma2:2b"
BATCH_SIZE    = 50

NTEE1_VALID = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

NTEE1_MAP = (
    "A=Arts/Culture B=Education C=Environment D=Animals E=HealthCare "
    "F=MentalHealth G=Disease H=MedResearch I=Crime J=Employment "
    "K=Food/Nutrition L=Housing M=PublicSafety N=Recreation O=Youth "
    "P=HumanServices Q=International R=CivilRights S=Community "
    "T=Philanthropy U=Science V=SocialScience W=PublicBenefit "
    "X=Religion Y=Membership Z=Unknown"
)

PROMPT_TMPL = """Classify these US nonprofits with NTEE1 codes.
NTEE1: {ntee_map}

For each org return one letter. Reply ONLY with a JSON array of letters, same order, no extra text.
Example: ["B","E","A","P"]

Organizations:
{org_list}

Reply:"""


def call_ollama(prompt: str, model: str) -> str | None:
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 200},
    }).encode()
    try:
        req = urllib.request.Request(
            OLLAMA_URL, data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()).get("response", "").strip()
    except Exception as e:
        return None


def parse_letters(text: str, expected: int) -> list[str | None]:
    """Extract list of NTEE letters from model response."""
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            items = json.loads(text[start:end])
            result = []
            for item in items[:expected]:
                letter = str(item).strip().upper()[:1]
                result.append(letter if letter in NTEE1_VALID else None)
            while len(result) < expected:
                result.append(None)
            return result
        except Exception:
            pass
    # Fallback: scan for letters
    letters = [c for c in text.upper() if c in NTEE1_VALID]
    result = letters[:expected]
    while len(result) < expected:
        result.append(None)
    return result


def write_batch(db: sqlite3.Connection, pairs: list[tuple[str, str]]):
    """Write (ein, ntee1) pairs with retry on lock."""
    for attempt in range(8):
        try:
            db.executemany(
                "UPDATE registry_enriched SET NTEE1=? WHERE EIN=? AND source='bmf_stub'",
                [(ntee1, ein) for ein, ntee1 in pairs if ntee1 and ntee1 != "Z"],
            )
            db.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < 7:
                time.sleep(0.5)
            else:
                raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-only", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")

    if args.priority_only:
        query = """
            SELECT EIN, organization_name, STATE FROM registry_enriched
            WHERE source='bmf_stub' AND NTEE1 IS NULL AND total_revenue IS NOT NULL
            ORDER BY total_revenue DESC
        """
    else:
        query = """
            SELECT EIN, organization_name, STATE FROM registry_enriched
            WHERE source='bmf_stub' AND NTEE1 IS NULL
            ORDER BY CASE WHEN total_revenue IS NOT NULL THEN 0 ELSE 1 END,
                     total_revenue DESC NULLS LAST
        """

    rows = db.execute(query).fetchall()
    total = len(rows)
    print(f"[tag_stub_ntee] {total:,} stubs  model={args.model}  batch={args.batch}", flush=True)
    if total == 0:
        return

    tagged = 0
    failed = 0
    t0 = time.time()

    for offset in range(0, total, args.batch):
        chunk = rows[offset:offset + args.batch]
        org_list = "\n".join(
            f"{i+1}. {row[1] or row[0]} ({row[2] or 'US'})"
            for i, row in enumerate(chunk)
        )
        prompt = PROMPT_TMPL.format(ntee_map=NTEE1_MAP, org_list=org_list)
        response = call_ollama(prompt, args.model)

        if response:
            letters = parse_letters(response, len(chunk))
            pairs = [(chunk[i][0], letters[i]) for i in range(len(chunk))]
            write_batch(db, pairs)
            tagged += sum(1 for _, l in pairs if l)
            failed += sum(1 for _, l in pairs if not l)
        else:
            failed += len(chunk)

        done = offset + len(chunk)
        if done % 500 == 0 or done >= total:
            elapsed = time.time() - t0
            rate    = done / elapsed * 3600
            eta_h   = (total - done) / (done / elapsed) / 3600 if done else 0
            print(
                f"  {done:>8,}/{total:,}  tagged={tagged:,}  failed={failed}  "
                f"~{rate:.0f}/hr  ETA {eta_h:.1f}h",
                flush=True,
            )

    elapsed = time.time() - t0
    print(f"\n[done] {tagged:,} tagged  {failed} failed  in {elapsed/3600:.2f}h", flush=True)


if __name__ == "__main__":
    main()
