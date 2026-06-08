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
MODEL      = "Qwen2.5-14B-Instruct-Q4_K_M"
BATCH_SIZE      = 20   # orgs per LLM call — 20 fits within 4096 tok/slot (-np 5, ctx 20480)
BATCH_SIZE_WEB  = 8    # smaller batch when web context is included (longer prompts)
TOKENS_PER_ORG  = 80   # output token budget per org
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


_BOILERPLATE_RE = re.compile(
    r'^welcome\b|official (website|site|page)|home ?page|'
    r'^this (website|site|page)\b|^copyright\b|'
    r'^\s*[\w\s]+\s*\|\s*[\w\s]+\s*\|',  # nav breadcrumb "Home | About | Contact"
    re.IGNORECASE,
)

def _is_boilerplate(text: str) -> bool:
    """Return True if the snippet is CMS filler rather than org mission context."""
    if len(text) < 50:
        return True
    return bool(_BOILERPLATE_RE.search(text))


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
            if len(text) >= 30 and not _is_boilerplate(text):
                return text[:max_chars]
    # Body text fallback — strip chrome, take first meaningful paragraph
    body = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    if _is_boilerplate(body[:200]):
        return ""
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
- Do NOT use: "is dedicated to", "strives to", "committed to", "passionate about", "aims to", "works to provide", "seeks to", "focuses on providing", "is a nonprofit", "was founded", "makes a difference", "serves the community of".
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
        city = (org.get("CITY") or "").title()  # DB stores cities in ALL CAPS
        lines.append(
            f'  {{"ein": "{ein}", '
            f'"name": "{org["organization_name"]}", '
            f'"sector": "{ntee_label}", '
            f'"location": "{city}, {org.get("STATE","")}", '
            f'"size": "{size}"{ctx_field}}}'
        )
    orgs_json = "[\n" + ",\n".join(lines) + "\n]"

    return (
        _FEW_SHOT + "\n"
        "Now write mission sentences for these organizations. "
        'Return ONLY a JSON array: [{"ein": "...", "mission": "..."}]\n\n'
        "Organizations:\n" + orgs_json
    )


def _call_llm(batch: list[dict], web_ctx: dict[str, str]) -> dict[str, str]:
    """Returns {ein: mission_text} for the batch. Source is tracked per-org in _write_batch."""
    prompt = _build_prompt(batch, web_ctx)
    n = len(batch)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You output only raw JSON arrays. No markdown, no explanation, no code blocks."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max(400, TOKENS_PER_ORG * n),
    }
    try:
        r = requests.post(GEN_URL, json=payload, timeout=600)
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
            return {}
        return {
            item["ein"]: item["mission"].strip() for item in items
            if "ein" in item and "mission" in item and item["mission"].strip()
        }
    except Exception:
        return {}


def _write_batch(results: dict[str, str], conn: sqlite3.Connection, web_ctx: dict[str, str], batch_size: int):
    """Write missions with per-org source: ai_web if that org had web context, else ai_ntee."""
    global _written, _errors
    if not results:
        _errors += batch_size
        return
    with _write_lock:
        conn.executemany(
            "UPDATE registry_enriched SET mission=?, mission_source=? WHERE EIN=?",
            [
                (mission, "ai_web" if ein in web_ctx else "ai_ntee", ein)
                for ein, mission in results.items()
            ]
        )
        conn.commit()
        _written += len(results)
        _errors  += batch_size - len(results)


def run(limit=None, workers=1, all_orgs=False, upgrade_templates=False):
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_column(conn)

    scope = "" if all_orgs else "AND re.merit_score IS NOT NULL"
    mission_filter = "(re.mission IS NULL OR re.mission = '' OR re.mission_source = 'template_ntee')" \
                     if upgrade_templates else "(re.mission IS NULL OR re.mission = '')"
    # Prioritise orgs that already have a cached web page: web_context yields
    # far better missions (ai_web) than NTEE-only inference (ai_ntee). Process
    # those first so GPU time produces the highest-quality missions up front.
    query = f"""
        SELECT re.EIN, re.organization_name, re.NTEE1, re.CITY, re.STATE, re.total_revenue
        FROM registry_enriched re
        LEFT JOIN (SELECT DISTINCT ein FROM page_cache WHERE html_gz IS NOT NULL) pc
          ON pc.ein = re.EIN
        WHERE {mission_filter} {scope}
          AND re.source NOT IN ('IRS_BMF', 'bmf_stub')
        ORDER BY (pc.ein IS NULL), re.merit_score DESC NULLS LAST
        {'LIMIT ' + str(limit) if limit else ''}
    """
    rows = [dict(r) for r in conn.execute(query)]
    total = len(rows)

    if not total:
        print("Nothing to generate.", flush=True)
        conn.close()
        return

    scope_label = "all orgs" if all_orgs else ("template upgrades" if upgrade_templates else "scored orgs")
    print(f"Generating missions for {total:,} {scope_label}  model={MODEL}  workers={workers}", flush=True)

    # Pre-check which EINs have cached pages so we can use smaller batches for those
    cached_eins = set(
        r[0] for r in conn.execute(
            "SELECT DISTINCT ein FROM page_cache WHERE html_gz IS NOT NULL"
        ).fetchall()
    )

    # Build batches with adaptive sizing: smaller batches for web-context orgs
    batches = []
    i = 0
    while i < total:
        # If this org has a cached page, use smaller batch
        bs = BATCH_SIZE_WEB if rows[i]["EIN"] in cached_eins else BATCH_SIZE
        batches.append(rows[i:i+bs])
        i += bs

    conn.close()  # main thread conn done; each worker opens its own
    start = time.time()

    def process(batch):
        # Each thread needs its own connection — sharing one across threads
        # causes SQLITE_MISUSE even with check_same_thread=False.
        tconn = sqlite3.connect(DB_PATH, timeout=30)
        tconn.row_factory = sqlite3.Row
        try:
            eins = [o["EIN"] for o in batch]
            web_ctx = _get_web_context(eins, tconn)
            results = _call_llm(batch, web_ctx)
            _write_batch(results, tconn, web_ctx, len(batch))
        finally:
            tconn.close()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(process, b) for b in batches]
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                fut.result()  # surface exceptions instead of silently losing them
            except Exception as exc:
                print(f"\n  [batch error] {exc}", flush=True)
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
    ap.add_argument("--limit",             type=int, help="Test run limit")
    ap.add_argument("--workers",           type=int, default=1)
    ap.add_argument("--all-orgs",          action="store_true", help="Include unscored orgs too")
    ap.add_argument("--upgrade-templates", action="store_true", help="Replace template_ntee missions with AI-generated ones")
    ap.add_argument("--url",               type=str, help="Override inference endpoint URL")
    ap.add_argument("--model",             type=str, help="Override model name")
    args = ap.parse_args()
    if args.url:
        GEN_URL = args.url
    if args.model:
        MODEL = args.model
    run(limit=args.limit, workers=args.workers, all_orgs=args.all_orgs,
        upgrade_templates=args.upgrade_templates)
