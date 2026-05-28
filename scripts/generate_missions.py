#!/usr/bin/env python3
"""
scripts/generate_missions.py

Generate 1-2 sentence mission descriptions for scored orgs that have none,
using Qwen2.5-32B-Instruct via llama-server Vulkan1 (port 11437).

Input:  registry_enriched rows where merit_score IS NOT NULL and mission IS NULL
Output: mission text written back to registry_enriched
        mission_source = 'ai_generated' (requires column — see below)

Scope: ~252K scored orgs. At batch=20, ~60 tok/s → ~18-22 hours.
Resumable: skips EINs already having mission text.

Usage:
    python3 scripts/generate_missions.py
    python3 scripts/generate_missions.py --limit 100      # test run
    python3 scripts/generate_missions.py --all-orgs       # include unscored too
    python3 scripts/generate_missions.py --workers 2      # parallel batches
"""

import sqlite3, json, time, argparse, sys, re, zlib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

DB_PATH    = Path.home() / "meritgiving" / "data" / "merit_registry.db"
GEN_URL    = "http://127.0.0.1:11437/v1/chat/completions"
MODEL      = "Qwen2.5-32B-Instruct-Q4_K_M"
BATCH_SIZE = 20
MISSION_SOURCE = "ai_ntee"   # marks generated vs scraped missions

_NTEE_LABELS = {
    "A": "arts, culture, and humanities",
    "B": "education",
    "C": "environment and conservation",
    "D": "animal welfare",
    "E": "health care",
    "F": "mental health and counseling",
    "G": "disease research and medical services",
    "H": "medical research",
    "I": "crime, legal, and justice",
    "J": "employment and job training",
    "K": "food, agriculture, and nutrition",
    "L": "housing and shelter",
    "M": "public safety and disaster relief",
    "N": "recreation, sports, and leisure",
    "O": "youth development",
    "P": "human services",
    "Q": "international and foreign affairs",
    "R": "civil rights and social action",
    "S": "community improvement",
    "T": "philanthropy and grantmaking",
    "U": "science and technology",
    "V": "social science",
    "W": "public benefit",
    "X": "religion and faith",
    "Y": "mutual benefit and membership",
    "Z": "general nonprofit",
}

_write_lock = Lock()
_written    = 0
_errors     = 0


def _ensure_column(conn: sqlite3.Connection):
    """Add mission_source column if it doesn't exist."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(registry_enriched)")}
    if "mission_source" not in cols:
        conn.execute("ALTER TABLE registry_enriched ADD COLUMN mission_source TEXT")
        conn.commit()


def _extract_web_context(html_bytes: bytes, max_chars: int = 500) -> str:
    """Extract best text snippet from compressed HTML for LLM context."""
    try:
        html = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        return ""
    for pattern in [
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']{20,})["\']',
        r'<meta[^>]+content=["\']([^"\']{20,})["\'][^>]+property=["\']og:description["\']',
        r'<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\']([^"\']{20,})["\']',
        r'<meta[^>]+content=["\']([^"\']{20,})["\'][^>]+name=["\']twitter:description["\']',
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{20,})["\']',
        r'<meta[^>]+content=["\']([^"\']{20,})["\'][^>]+name=["\']description["\']',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            text = re.sub(r'\s+', ' ', m.group(1)).strip()
            if len(text) >= 30:
                return text[:max_chars]
    # Body text fallback
    body = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    return body[:max_chars]


def _get_web_context(eins: list[str], conn: sqlite3.Connection) -> dict[str, str]:
    """Returns {ein: text_snippet} for orgs with cached page HTML."""
    results: dict[str, str] = {}
    for ein in eins:
        row = conn.execute(
            "SELECT html_gz FROM page_cache WHERE ein=? AND html_gz IS NOT NULL ORDER BY fetched_at DESC LIMIT 1",
            (ein,)
        ).fetchone()
        if row and row[0]:
            try:
                html_bytes = zlib.decompress(row[0])
                snippet = _extract_web_context(html_bytes)
                if snippet:
                    results[ein] = snippet
            except Exception:
                pass
    return results


_FEW_SHOT = """\
Examples — the org NAME is the primary clue; website_context (when present) takes priority:

name="Springfield Meals on Wheels" sector="human services" location="Springfield, IL"
→ Delivers hot meals to homebound elderly and disabled residents across Springfield.

name="Boys & Girls Club of Greater Milwaukee" sector="youth development" location="Milwaukee, WI"
→ Provides after-school programs, mentorship, and safe spaces for young people in Milwaukee.

name="Habitat for Humanity of Greater Baton Rouge" sector="housing and shelter" location="Baton Rouge, LA"
website_context="Building simple, decent, affordable housing for families in need in the Greater Baton Rouge area since 1987."
→ Builds and rehabilitates affordable homes for low-income families across the Greater Baton Rouge area.

name="Trout Unlimited — Rocky Mountain Chapter" sector="environment" location="Denver, CO"
→ Protects and restores cold-water fisheries and trout habitat across the Rocky Mountain region.

name="St. Vincent de Paul Society of Omaha" sector="human services" location="Omaha, NE"
→ Operates food pantries, clothing assistance, and emergency financial aid for people in need in Omaha.

name="Rotary Club of San Jose Foundation" sector="philanthropy" location="San Jose, CA"
→ Awards community grants and supports international development projects through the Rotary Club network.

name="ACTIVE RETIREMENT ASSOCIATION" sector="human services" location="Durham, NH"
→ Connects older adults with social activities, fitness programs, and volunteer opportunities in Durham.

Rules:
- If website_context is present, use it — prefer the org's own words over sector inference.
- Read the NAME first — it usually says what the org does.
- Sector confirms the category; use it when the name is ambiguous.
- One sentence, present tense.
- Do NOT start the sentence with the org name or any part of it — not even "The [Name]...".
- Do NOT use the words "likely", "probably", "presumably", or "appears to".
- Do NOT use: "is dedicated to", "strives to", "committed to", "passionate about".
- Do NOT invent specific statistics, dollar amounts, or named programs.
- If the name is just a person's name or acronym, infer from sector + location.
- If the name restates an obvious fact (e.g. "Community Food Bank"), describe the WORK, not the name.
"""


def _build_prompt(batch: list[dict], web_ctx: dict[str, str]) -> str:
    lines = []
    for org in batch:
        ntee_label = _NTEE_LABELS.get(org.get("NTEE1") or "Z", "general nonprofit")
        rev = org.get("total_revenue")
        size = f"${rev:,.0f} annual revenue" if rev else "small community"
        ein = org["EIN"]
        ctx = web_ctx.get(ein, "")
        ctx_field = f', "website_context": "{ctx[:400].replace(chr(34), chr(39))}"' if ctx else ""
        lines.append(
            f'  {{"ein": "{ein}", '
            f'"name": "{org["organization_name"]}", '
            f'"sector": "{ntee_label}", '
            f'"location": "{org.get("CITY","")}, {org.get("STATE","")}", '
            f'"size": "{size}"{ctx_field}}}'
        )
    orgs_json = "[\n" + ",\n".join(lines) + "\n]"

    return (
        _FEW_SHOT + "\n"
        "Now write mission sentences for these organizations. "
        'Return ONLY a JSON array: [{"ein": "...", "mission": "..."}]\n\n'
        "Organizations:\n" + orgs_json
    )


def _call_llm(batch: list[dict], web_ctx: dict[str, str]) -> tuple[dict[str, str], str]:
    """Returns ({ein: mission_text}, mission_source) for the batch."""
    source = "ai_web" if web_ctx else "ai_ntee"
    prompt = _build_prompt(batch, web_ctx)
    # Smaller batches when context is present (larger prompt per org)
    effective_batch = len(batch)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You output only raw JSON arrays. No markdown, no explanation, no code blocks."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max(600, 70 * effective_batch),
    }
    try:
        r = requests.post(GEN_URL, json=payload, timeout=180)
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        content = msg.get("content") or msg.get("reasoning_content") or ""
        m = re.search(r"\[.*\]", content, re.DOTALL)
        content = m.group() if m else content
        parsed = json.loads(content)
        if isinstance(parsed, list):
            items = parsed
        elif isinstance(parsed, dict):
            items = next((v for v in parsed.values() if isinstance(v, list)), [])
        else:
            return {}, source
        return (
            {item["ein"]: item["mission"].strip() for item in items
             if "ein" in item and "mission" in item and item["mission"].strip()},
            source,
        )
    except Exception:
        return {}, source


def _write_batch(results: dict[str, str], conn: sqlite3.Connection, source: str):
    global _written, _errors
    if not results:
        _errors += BATCH_SIZE
        return
    with _write_lock:
        conn.executemany(
            "UPDATE registry_enriched SET mission=?, mission_source=? WHERE EIN=?",
            [(mission, source, ein) for ein, mission in results.items()]
        )
        conn.commit()
        _written += len(results)
        _errors  += BATCH_SIZE - len(results)


def run(limit=None, workers=1, all_orgs=False):
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_column(conn)

    scope = "" if all_orgs else "AND merit_score IS NOT NULL"
    query = f"""
        SELECT EIN, organization_name, NTEE1, CITY, STATE, total_revenue
        FROM registry_enriched
        WHERE (mission IS NULL OR mission = '') {scope}
        ORDER BY merit_score DESC NULLS LAST
        {'LIMIT ' + str(limit) if limit else ''}
    """
    rows = [dict(r) for r in conn.execute(query)]
    total = len(rows)

    if not total:
        print("Nothing to generate.", flush=True)
        conn.close()
        return

    scope_label = "all orgs" if all_orgs else "scored orgs"
    print(f"Generating missions for {total:,} {scope_label}  model={MODEL}  batch={BATCH_SIZE}  workers={workers}", flush=True)

    batches = [rows[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    start   = time.time()

    def process(batch):
        eins = [o["EIN"] for o in batch]
        web_ctx = _get_web_context(eins, conn)
        results, source = _call_llm(batch, web_ctx)
        _write_batch(results, conn, source)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(process, b) for b in batches]
        for i, _ in enumerate(as_completed(futs), 1):
            elapsed  = time.time() - start
            rate     = _written / elapsed if elapsed > 0 else 0
            pct      = (_written + _errors) / total * 100
            eta      = (total - _written - _errors) / rate / 60 if rate > 0 else 0
            print(
                f"\r  [{pct:5.1f}%] {_written:,} written  {_errors:,} errors  "
                f"{rate:.0f}/sec  ETA {eta:.1f}m",
                end="", flush=True
            )

    elapsed = time.time() - start
    print(f"\n\nDone in {elapsed/60:.1f} min — {_written:,} missions written, {_errors:,} errors", flush=True)
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit",    type=int, help="Test run limit")
    ap.add_argument("--workers",  type=int, default=1)
    ap.add_argument("--all-orgs", action="store_true", help="Include unscored orgs too")
    args = ap.parse_args()
    run(limit=args.limit, workers=args.workers, all_orgs=args.all_orgs)
