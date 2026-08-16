#!/usr/bin/env python3
"""
regenerate_pta_missions.py — Rewrite PTA/PTO missions using school name extracted
from org name + address context.

The generator previously produced copy-paste missions for school PTAs
("Advocates for parents, teachers, and students in California" × 49 orgs).
This script extracts the school name embedded in the org name and builds
a school-specific mission for each.

Targets: PTA/PTO orgs with generic or copy-paste missions.
Model: claude-haiku-4-5-20251001
Source tag: ai_haiku
Budget cap: --budget (default $8)

Usage:
    python3 scripts/regenerate_pta_missions.py
    python3 scripts/regenerate_pta_missions.py --limit 40   # test run
    python3 scripts/regenerate_pta_missions.py --dry-run
"""

import sqlite3, json, os, pathlib, re, time, argparse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BASE    = pathlib.Path.home() / "meritgiving"
DB      = BASE / "data/merit_registry.db"
HAIKU   = "claude-haiku-4-5-20251001"
API_URL = "https://api.anthropic.com/v1/messages"
BATCH   = 20

COST_INPUT  = 0.80   # per 1M tokens
COST_OUTPUT = 4.00

_write_lock = threading.Lock()
_written    = 0
_errors     = 0
_spend      = 0.0

# Copy-paste missions we know are wrong for individual school PTAs
_GENERIC_PTA_MISSIONS = [
    "advocates for parents, teachers, and students",
    "supports parent and teacher involvement in education",
    "advocates for parent and teacher involvement in education",
    "supports educational programs and activities",
    "supports educational programs and initiatives",
    "supports parents, teachers, and students",
    "provides support for educational programs",
    "supports the educational needs of students",
    "supports educational initiatives and programs",
]

# Suffixes to strip when extracting the school name from the org name
_PTA_SUFFIXES = re.compile(
    r'\s+(?:PTA|PTO|'
    r'PARENT[\s-]TEACHER[\s-](?:ORGANIZATION|ASSOCIATION|STUDENT ORGANIZATION|GROUP|CLUB)?|'
    r'PARENT[\s-]TEACHER[\s-]?CLUB|'
    r'PARENT[\s-]TEACHER|'
    r'PARENTS[\s-]AND[\s-]TEACHERS|'
    r'PARENTS[\s-]TEACHERS[\s-](?:AND[\s-])?STUDENTS?|'
    r'PARENT[\s-]FACULTY[\s-]ASSOCIATION|'
    r'HOME[\s-]?AND[\s-]?SCHOOL[\s-](?:ASSOCIATION|CLUB)|'
    r'FAMILY[\s-]TEACHER[\s-](?:ORGANIZATION|ASSOCIATION)'
    r').*$',
    re.IGNORECASE,
)

_STATE_PTA_RE = re.compile(
    r'^PTA\s+(?:CONGRESS|STATE\s+CONGRESS|NATIONAL\s+CONGRESS)|'
    r'CONGRESS\s+OF\s+PARENTS|'
    r'STATE\s+(?:PTA|PTO)\b',
    re.IGNORECASE,
)


def extract_school_name(org_name: str) -> str:
    """Pull the school name from an org name like 'Lincoln Elementary PTO'."""
    cleaned = _PTA_SUFFIXES.sub("", org_name).strip()
    # Remove trailing commas, dashes, "INC", "OF", etc.
    cleaned = re.sub(r'[\s,\-]+(?:INC|LLC|OF|THE|AT|FOR)[\s,\-]*$', '', cleaned, flags=re.IGNORECASE).strip()
    return cleaned.title() if cleaned else org_name.title()


def is_state_or_national(org_name: str) -> bool:
    """True for state/national PTA bodies — different prompt needed."""
    return bool(_STATE_PTA_RE.search(org_name))


_SYSTEM = """\
You write specific, accurate mission descriptions for school Parent Teacher Organizations.
Each org represents a specific school. Use the school name and city to write a distinct,
school-specific mission — never a generic template that could apply to any PTA.

Rules:
- Always name the school explicitly in the mission.
- One sentence, present tense.
- Do NOT start with the school or org name.
- Do NOT use: "is dedicated to", "strives to", "committed to", "advocates for parents teachers and students".
- Do NOT write the same mission for different schools.
- Vary the opening verb: Supports / Raises funds for / Organizes events for / Connects families at / Partners with teachers at / Builds community at / etc.

Respond ONLY with a JSON array: [{"ein": "...", "mission": "..."}, ...]
No markdown, no other text."""

_STATE_SYSTEM = """\
You write specific mission descriptions for state-level Parent Teacher Association bodies.
These are umbrella organizations representing thousands of local PTAs statewide.

Rules:
- One sentence, present tense.
- Mention the state explicitly.
- Do NOT use: "is dedicated to", "strives to", "committed to".
- Vary the opening verb.

Respond ONLY with a JSON array: [{"ein": "...", "mission": "..."}, ...]
No markdown, no other text."""


def _build_prompt(batch: list[dict]) -> tuple[str, str]:
    """Returns (prompt, system) — uses school-specific system for school PTAs."""
    # Split batch: school-level vs state/national
    school_orgs = [o for o in batch if not is_state_or_national(o["organization_name"])]
    state_orgs  = [o for o in batch if is_state_or_national(o["organization_name"])]

    # Use whichever type dominates the batch
    if len(school_orgs) >= len(state_orgs):
        orgs   = school_orgs + state_orgs
        system = _SYSTEM
    else:
        orgs   = state_orgs + school_orgs
        system = _STATE_SYSTEM

    lines = []
    for org in orgs:
        school = extract_school_name(org["organization_name"])
        city   = (org.get("CITY") or "").title()
        state  = org.get("STATE", "")
        addr   = org.get("address") or ""
        # Include address when it contains a school name clue (e.g. "123 Lincoln Ave")
        addr_field = f', "address": "{addr[:60]}"' if addr and not addr.startswith("None") else ""
        lines.append(
            f'  {{"ein": "{org["EIN"]}", '
            f'"school_name": "{school}", '
            f'"city": "{city}, {state}"{addr_field}}}'
        )

    prompt = (
        "Write a specific mission for each school PTA/PTO. "
        "Use the school_name and city to make each mission unique.\n\n"
        "[\n" + ",\n".join(lines) + "\n]\n\n"
        "Return JSON array: [{\"ein\": \"...\", \"mission\": \"...\"}, ...]"
    )
    return prompt, system


def _call_haiku(batch: list[dict]) -> dict[str, str]:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if len(key) < 20:
        return {}
    prompt, system = _build_prompt(batch)
    payload = json.dumps({
        "model": HAIKU,
        "max_tokens": 1500,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    for attempt in range(4):
        req = urllib.request.Request(
            API_URL, data=payload,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data  = json.loads(resp.read())
                text  = data["content"][0]["text"].strip()
                usage = data.get("usage", {})
                cost  = (usage.get("input_tokens", 0) / 1e6 * COST_INPUT +
                         usage.get("output_tokens", 0) / 1e6 * COST_OUTPUT)
                global _spend
                with _write_lock:
                    _spend += cost
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
                time.sleep(5 * (2 ** attempt))
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
    generic_clause = " OR ".join([
        f"LOWER(mission) LIKE '%{p}%'" for p in _GENERIC_PTA_MISSIONS
    ])
    # Also catch copy-paste missions (10+ orgs share same text)
    query = f"""
        SELECT re.EIN, re.organization_name, re.NTEE1, re.CITY, re.STATE, re.address, re.mission
        FROM registry_enriched re
        WHERE (
            UPPER(re.organization_name) LIKE '%PTA%'
            OR UPPER(re.organization_name) LIKE '%PTO%'
            OR UPPER(re.organization_name) LIKE '%PARENT TEACHER%'
            OR UPPER(re.organization_name) LIKE '%PARENT-TEACHER%'
        )
        AND re.mission IS NOT NULL AND re.mission != ''
        AND (
            ({generic_clause})
            OR re.mission IN (
                SELECT mission FROM registry_enriched
                WHERE mission IS NOT NULL AND mission != ''
                GROUP BY mission HAVING COUNT(*) >= 10
            )
        )
        ORDER BY re.merit_score DESC NULLS LAST
        {'LIMIT ' + str(limit) if limit else ''}
    """
    return [dict(r) for r in conn.execute(query)]


def run(limit=None, workers=2, budget=8.0, dry_run=False):
    env = BASE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip()

    if not dry_run and len(os.environ.get("ANTHROPIC_API_KEY", "")) < 20:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        return

    conn = sqlite3.connect(DB, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    rows  = _load_targets(conn, limit)
    total = len(rows)

    if not total:
        print("No PTA/PTO missions to regenerate.")
        return

    # Cost estimate
    calls    = total // BATCH + 1
    est_cost = (calls * 1200 / 1e6 * COST_INPUT) + (calls * 1000 / 1e6 * COST_OUTPUT)
    print(f"PTA/PTO mission regeneration — {HAIKU}")
    print(f"Targets: {total:,}  Batches: {calls}  workers: {workers}  budget: ${budget:.2f}")
    print(f"Estimated cost: ${est_cost:.2f}")

    if dry_run:
        print("\n--- DRY RUN SAMPLES ---")
        for org in rows[:12]:
            school = extract_school_name(org["organization_name"])
            print(f"  ORG:    {org['organization_name']} ({org['CITY']}, {org['STATE']})")
            print(f"  SCHOOL: {school}")
            print(f"  OLD:    {org['mission']}")
            print()
        return

    batches = [rows[i:i+BATCH] for i in range(0, total, BATCH)]
    start   = time.time()

    def process(batch):
        global _spend
        with _write_lock:
            if _spend >= budget:
                return
        results = _call_haiku(batch)
        _write_batch(results, conn)
        elapsed   = time.time() - start
        rate      = _written / elapsed if elapsed > 0 else 0
        remaining = total - _written - _errors
        eta       = remaining / rate / 60 if rate > 0 else 0
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
    print(f"\nDone in {elapsed:.1f} min — {_written:,} PTA missions rewritten  ${_spend:.2f} spent")
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit",   type=int,   default=None)
    ap.add_argument("--workers", type=int,   default=2)
    ap.add_argument("--budget",  type=float, default=8.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(limit=args.limit, workers=args.workers, budget=args.budget, dry_run=args.dry_run)
