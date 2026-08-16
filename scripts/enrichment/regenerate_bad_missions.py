#!/usr/bin/env python3
"""
regenerate_bad_missions.py — Rewrite worst-quality missions using Claude Haiku 4.5.

Targets:
  1. Missions containing banned phrases (committed to, strives to, etc.)
  2. Generic copy-paste missions appearing 10+ times across orgs
  3. Templated patterns (Provides X services in Y, etc.)

Writes back with mission_source='ai_haiku'. Leaves good missions untouched.
Capped at --budget USD (default $10) to prevent runaway spend.

Usage:
    python3 scripts/regenerate_bad_missions.py
    python3 scripts/regenerate_bad_missions.py --limit 100   # test run
    python3 scripts/regenerate_bad_missions.py --budget 5    # tighter cap
    python3 scripts/regenerate_bad_missions.py --dry-run     # print samples, no API calls
"""

import sqlite3, json, os, pathlib, time, argparse, urllib.request, urllib.error, re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BASE     = pathlib.Path.home() / "meritgiving"
DB       = BASE / "data/merit_registry.db"
HAIKU    = "claude-haiku-4-5-20251001"
API_URL  = "https://api.anthropic.com/v1/messages"
BATCH    = 20

_write_lock = threading.Lock()
_written    = 0
_errors     = 0
_spend      = 0.0   # running cost estimate

# Haiku pricing (per 1M tokens)
COST_INPUT  = 0.80
COST_OUTPUT = 4.00

BANNED_PHRASES = [
    "is dedicated to", "strives to", "committed to", "passionate about",
    "aims to", "seeks to", "is a nonprofit", "was founded",
    "works to provide", "focuses on providing", "makes a difference",
    "serves the community of",
]

GENERIC_PATTERNS = [
    "Provides%services in%",
    "Supports%through community service%",
    "Provides%programs and services for%",
]

_NTEE_LABELS = {
    "A": "arts, culture & humanities", "B": "education", "C": "environment",
    "D": "animal welfare", "E": "health care", "F": "mental health",
    "G": "disease research & prevention", "H": "medical research",
    "I": "crime & legal services", "J": "employment", "K": "food & agriculture",
    "L": "housing & shelter", "M": "public safety", "N": "recreation & sports",
    "O": "youth development", "P": "human services", "Q": "international affairs",
    "R": "civil rights & advocacy", "S": "community development",
    "T": "philanthropy & grantmaking", "U": "science & technology",
    "V": "social science", "W": "public affairs", "X": "religion",
    "Y": "mutual benefit & membership", "Z": "unknown",
}

_FEW_SHOT = """\
Examples:

name="Springfield Meals on Wheels" sector="human services" location="Springfield, IL"
→ Delivers hot meals to homebound elderly and disabled residents across Springfield.

name="Boys & Girls Club of Greater Milwaukee" sector="youth development" location="Milwaukee, WI"
→ Provides after-school programs, mentorship, and safe spaces for young people in Milwaukee.

name="Rotary Club of San Jose Foundation" sector="philanthropy" location="San Jose, CA"
→ Awards community grants and supports international development projects through the Rotary Club network.

name="Trout Unlimited — Rocky Mountain Chapter" sector="environment" location="Denver, CO"
→ Protects and restores cold-water fisheries and trout habitat across the Rocky Mountain region.

name="ACTIVE RETIREMENT ASSOCIATION" sector="human services" location="Durham, NH"
→ Connects older adults with social activities, fitness programs, and volunteer opportunities in Durham.

Rules:
- Read the NAME first — it usually says what the org does.
- One sentence, present tense, specific to this org.
- Do NOT start with the org name.
- Do NOT use: "is dedicated to", "strives to", "committed to", "passionate about",
  "aims to", "seeks to", "is a nonprofit", "was founded", "makes a difference".
- Do NOT repeat the same mission for different orgs in the same batch.
- Do NOT invent statistics, dollar amounts, or named programs.
- If the name is ambiguous, use sector + location to infer.
"""

_SYSTEM = f"""You rewrite nonprofit mission descriptions that are generic or low quality.
{_FEW_SHOT}
Respond ONLY with a JSON array. Each element: {{"ein": "...", "mission": "..."}}
No other text. No markdown."""


def _load_dotenv():
    env = BASE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip()


def _api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return key if len(key) > 20 else None


def _build_prompt(batch: list[dict]) -> str:
    lines = []
    for org in batch:
        ntee  = (org.get("NTEE1") or "Z")[0].upper()
        label = _NTEE_LABELS.get(ntee, "general nonprofit")
        city  = (org.get("CITY") or "").title()
        lines.append(
            f'  {{"ein": "{org["EIN"]}", '
            f'"name": "{org["organization_name"]}", '
            f'"sector": "{label}", '
            f'"location": "{city}, {org.get("STATE", "")}", '
            f'"old_mission": "{org["mission"][:120].replace(chr(34), chr(39))}"}}'
        )
    orgs_json = "[\n" + ",\n".join(lines) + "\n]"
    return (
        "Rewrite these nonprofit missions. Each is currently too generic or uses banned phrases. "
        "Use the org name and location to write something specific.\n\n"
        f"Orgs:\n{orgs_json}\n\n"
        "Respond with a JSON array: [{\"ein\": \"...\", \"mission\": \"...\"}, ...]"
    )


def _call_haiku(batch: list[dict]) -> dict[str, str]:
    key = _api_key()
    if not key:
        return {}
    prompt = _build_prompt(batch)
    payload = json.dumps({
        "model": HAIKU,
        "max_tokens": 1200,
        "system": _SYSTEM,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    for attempt in range(4):
        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data  = json.loads(resp.read())
                text  = data["content"][0]["text"].strip()
                usage = data.get("usage", {})
                inp   = usage.get("input_tokens", 0)
                out   = usage.get("output_tokens", 0)
                cost  = (inp / 1e6 * COST_INPUT) + (out / 1e6 * COST_OUTPUT)
                global _spend
                with _write_lock:
                    _spend += cost
                # strip optional markdown code fences Haiku sometimes adds
                text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\s*```$', '', text)
                m = re.search(r'\[.*\]', text, re.DOTALL)
                if not m:
                    return {}
                items = json.loads(m.group())
                return {
                    item["ein"]: item["mission"].strip()
                    for item in items
                    if "ein" in item and "mission" in item and item["mission"].strip()
                }
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (2 ** attempt)   # 5s, 10s, 20s, 40s
                time.sleep(wait)
                continue
            return {}
        except Exception:
            return {}
    return {}


def _write_batch(results: dict[str, str], conn: sqlite3.Connection):
    global _written, _errors
    if not results:
        with _write_lock:
            _errors += BATCH
        return
    with _write_lock:
        conn.executemany(
            "UPDATE registry_enriched SET mission=?, mission_source='ai_haiku' WHERE EIN=?",
            [(m, ein) for ein, m in results.items()]
        )
        conn.commit()
        _written += len(results)


def _load_targets(conn: sqlite3.Connection, limit: int | None) -> list[dict]:
    banned_clause = " OR ".join([f"LOWER(mission) LIKE '%{p}%'" for p in BANNED_PHRASES])
    generic_clause = " OR ".join([f"mission LIKE '{p}'" for p in GENERIC_PATTERNS])
    dupe_clause = """
        mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 10
        )
    """
    query = f"""
        SELECT EIN, organization_name, NTEE1, CITY, STATE, mission
        FROM registry_enriched
        WHERE mission IS NOT NULL AND mission != ''
          AND ({banned_clause} OR {generic_clause} OR {dupe_clause})
        ORDER BY merit_score DESC NULLS LAST
        {'LIMIT ' + str(limit) if limit else ''}
    """
    return [dict(r) for r in conn.execute(query)]


def run(limit=None, workers=4, budget=10.0, dry_run=False):
    _load_dotenv()
    if not dry_run and not _api_key():
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        return

    conn = sqlite3.connect(DB, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    rows   = _load_targets(conn, limit)
    total  = len(rows)
    if not total:
        print("Nothing to regenerate.")
        return

    batches = [rows[i:i+BATCH] for i in range(0, total, BATCH)]
    print(f"Regenerating {total:,} worst-quality missions via {HAIKU}")
    print(f"Batches: {len(batches)}  workers: {workers}  budget cap: ${budget:.2f}")
    if dry_run:
        print("\n--- DRY RUN SAMPLES ---")
        for org in rows[:10]:
            print(f"  [{org['NTEE1']}] {org['organization_name']} ({org['CITY']}, {org['STATE']})")
            print(f"  OLD: {org['mission']}")
            print()
        return

    start = time.time()

    def process(batch):
        global _spend
        with _write_lock:
            if _spend >= budget:
                return
        results = _call_haiku(batch)
        _write_batch(results, conn)
        elapsed = time.time() - start
        rate    = _written / elapsed if elapsed > 0 else 0
        remaining = total - _written - _errors
        eta     = remaining / rate / 60 if rate > 0 else 0
        print(
            f"\r  [{_written/total*100:5.1f}%] {_written:,} written  "
            f"{_errors} errors  ${_spend:.2f} spent  ETA {eta:.0f}m",
            end="", flush=True,
        )
        with _write_lock:
            if _spend >= budget:
                print(f"\n  Budget cap ${budget:.2f} reached — stopping.")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(process, b) for b in batches]
        for f in as_completed(futs):
            if _spend >= budget:
                for pending in futs:
                    pending.cancel()
                break

    elapsed = (time.time() - start) / 60
    print(f"\nDone in {elapsed:.1f} min — {_written:,} missions rewritten  ${_spend:.2f} spent")
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit",   type=int,   default=None)
    ap.add_argument("--workers", type=int,   default=2)
    ap.add_argument("--budget",  type=float, default=10.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(limit=args.limit, workers=args.workers, budget=args.budget, dry_run=args.dry_run)
