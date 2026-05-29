#!/usr/bin/env python3
"""
regenerate_chapter_orgs.py — Rewrite copy-paste missions for franchise/chapter orgs.

Clusters handled:
  rotary      — Rotary clubs and foundations (city extracted from name)
  vfw         — VFW posts, American Legion posts, auxiliaries (post + city)
  farm_bureau — County farm bureaus (city as county-seat proxy)
  union       — Labor unions / NTEE J locals (union type + city)
  fire        — Volunteer fire departments and districts (district name)
  intl        — NTEE Q international orgs with generic missions (org-name inference)
  lions       — Lions Club chapters (city extracted from name)
  masonic     — Masonic lodges, Shriners, Elks, Odd Fellows (lodge type + city)
  greek       — Greek-letter sororities and fraternities (org name + chapter + city)
  alumni      — University/college alumni associations (institution + city)

Each cluster uses a pattern-specific prompt so Haiku can't produce the
same mission for two chapters in different cities.

Usage:
    python3 scripts/regenerate_chapter_orgs.py
    python3 scripts/regenerate_chapter_orgs.py --cluster rotary
    python3 scripts/regenerate_chapter_orgs.py --dry-run
    python3 scripts/regenerate_chapter_orgs.py --limit 60 --cluster vfw
"""

import sqlite3, json, os, pathlib, re, time, argparse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BASE    = pathlib.Path.home() / "meritgiving"
DB      = BASE / "data/merit_registry.db"
HAIKU   = "claude-haiku-4-5-20251001"
API_URL = "https://api.anthropic.com/v1/messages"
BATCH   = 20
COST_IN = 0.80   # per 1M tokens
COST_OUT= 4.00

_lock    = threading.Lock()
_written = 0
_errors  = 0
_spend   = 0.0


# ── extractors ────────────────────────────────────────────────────────────────

_STRIP_ROTARY = re.compile(
    r'\b(ROTARY\s+)?CLUB\s+OF\s+|\s+(ROTARY|CLUB|FOUNDATION|FUND|INC|LLC|'
    r'SCHOLARSHIP|MEMORIAL|CHARITABLE|EDUCATIONAL|INTERNATIONAL|DISTRICT)[\s\.,].*$',
    re.IGNORECASE,
)
def extract_rotary_city(org_name: str, db_city: str) -> str:
    cleaned = _STRIP_ROTARY.sub('', org_name).replace('ROTARY', '').strip(' -,.')
    return cleaned.title() if len(cleaned) > 3 else db_city.title()


_POST_RE = re.compile(r'(?:POST|UNIT|CHAPTER|DETACHMENT)\s*#?\s*(\d+)', re.IGNORECASE)
def extract_vfw_info(org_name: str) -> tuple[str, str | None]:
    """Returns (org_type, post_number_or_None)."""
    m = _POST_RE.search(org_name)
    post = f"Post {m.group(1)}" if m else None
    name_up = org_name.upper()
    if 'AUXILIARY' in name_up:
        org_type = 'American Legion Auxiliary' if 'LEGION' in name_up else 'VFW Auxiliary'
    elif 'AMERICAN LEGION' in name_up:
        org_type = 'American Legion'
    elif 'AMVETS' in name_up:
        org_type = 'AMVETS'
    elif 'DAV' in name_up or 'DISABLED AMERICAN' in name_up:
        org_type = 'DAV'
    else:
        org_type = 'VFW'
    return org_type, post


_STRIP_FIRE = re.compile(
    r'\s+(?:VOLUNTEER\s+)?(?:FIRE\s+)?(?:DEPARTMENT|DEPT|DISTRICT|COMPANY|'
    r'ASSOCIATION|ASSOC|CORPS|RELIEF|FIREMANS?|FIREFIGHTERS?)[\s\.,].*$',
    re.IGNORECASE,
)
_STRIP_FIRE2 = re.compile(r'\s+(?:INC|LLC|INCORPORATED|NO\b|NO\.|#\d+).*$', re.IGNORECASE)
def extract_fire_area(org_name: str) -> str:
    cleaned = _STRIP_FIRE.sub('', org_name)
    cleaned = _STRIP_FIRE2.sub('', cleaned).strip(' -,.')
    return cleaned.title() if len(cleaned) > 3 else org_name.title()


_UNION_TYPES = [
    (r'COMMUNICATION\s+WORKERS', 'Communication Workers of America'),
    (r'UNITED\s+STEEL\s*WORKERS|STEELWORKERS', 'United Steelworkers'),
    (r'AUTO\s+(AEROSPACE|WORKERS)|UAW', 'United Auto Workers'),
    (r'TEAMSTERS?|IBT\b', 'Teamsters'),
    (r'ELECTRICAL\s+WORKERS|IBEW\b', 'IBEW (Electrical Workers)'),
    (r'SERVICE\s+EMPLOYEES|SEIU\b', 'SEIU'),
    (r'POSTAL\s+WORKERS|NALC\b', 'Postal Workers'),
    (r'TEACHERS?\s+(FEDERATION|UNION|ASSOC)|AFT\b', 'Teachers Union'),
    (r'STATE\s+(COUNTY|MUNICIPAL)|AFSCME\b', 'AFSCME'),
    (r'CARPENTERS', 'Carpenters Union'),
    (r'PLUMBERS|PIPEFITTERS', 'Plumbers & Pipefitters Union'),
    (r'OPERATING\s+ENGINEERS', 'Operating Engineers Union'),
    (r'PAINTERS\s+(AND\s+)?ALLIED|IUPAT\b', 'Painters Union'),
    (r'MACHINISTS|IAM\b', 'Machinists Union'),
    (r'RETAIL\s+(CLERKS|WORKERS)|UFCW\b', 'Retail Workers Union'),
]
_LOCAL_RE = re.compile(r'LOCAL\s*#?\s*(\d+)', re.IGNORECASE)
def extract_union_info(org_name: str) -> tuple[str, str | None]:
    union_type = 'labor union'
    for pattern, label in _UNION_TYPES:
        if re.search(pattern, org_name, re.IGNORECASE):
            union_type = label
            break
    m = _LOCAL_RE.search(org_name)
    local = f"Local {m.group(1)}" if m else None
    return union_type, local


_STRIP_LIONS = re.compile(
    r'\b(?:LIONS?\s+)?CLUB\s+OF\s+|\s+(?:LIONS?|CLUBS?|FOUNDATION|FUND|INC|LLC|'
    r'INTERNATIONAL|DISTRICT|ASSOCIATION)[\s\.,].*$',
    re.IGNORECASE,
)
_GENERIC_LIONS_RE = re.compile(r'\b(?:INTERNATIONAL|ASSOCIATION|OF\s*$)', re.IGNORECASE)
def extract_lions_city(org_name: str, db_city: str) -> str:
    # Most Lions chapters use "INTERNATIONAL ASSOCIATION OF LIONS CLUBS" as their
    # legal name — city is only in the DB, not the name
    cleaned = _STRIP_LIONS.sub('', org_name)
    cleaned = re.sub(r'\bLIONS?\b', '', cleaned, flags=re.IGNORECASE).strip(' -,.')
    if not cleaned or len(cleaned) <= 3 or _GENERIC_LIONS_RE.search(cleaned):
        return db_city.title()
    return cleaned.title()


_LODGE_RE = re.compile(r'(?:LODGE|CHAPTER|COMMANDERY|COURT)\s*(?:NO\.?|#)?\s*(\d+)', re.IGNORECASE)
def extract_masonic_info(org_name: str) -> tuple[str, str | None]:
    m = _LODGE_RE.search(org_name)
    lodge_num = f"No. {m.group(1)}" if m else None
    name_up = org_name.upper()
    if 'EASTERN STAR' in name_up:
        lodge_type = 'Order of the Eastern Star'
    elif 'SHRINER' in name_up or 'SHRINE' in name_up:
        lodge_type = 'Shriners'
    elif 'ELKS' in name_up or 'BENEVOLENT AND PROTECTIVE ORDER' in name_up:
        lodge_type = 'Elks Lodge'
    elif 'MOOSE' in name_up or 'LOYAL ORDER' in name_up:
        lodge_type = 'Loyal Order of Moose'
    elif 'PYTHIAS' in name_up:
        lodge_type = 'Knights of Pythias'
    elif 'COLUMBUS' in name_up or 'COLUMB' in name_up:
        lodge_type = 'Knights of Columbus'
    elif 'ODD' in name_up and 'FELLOW' in name_up:
        lodge_type = 'Odd Fellows Lodge'
    elif 'REBEKAH' in name_up:
        lodge_type = "Rebekah Lodge (Odd Fellows women's branch)"
    else:
        lodge_type = 'Masonic Lodge'
    return lodge_type, lodge_num


_GREEK_STRIP = re.compile(
    r'\s+(?:SORORITY|FRATERNITY|CHAPTER|FOUNDATION|INC|LLC|EDUCATIONAL|HOUSE|CORP).*$',
    re.IGNORECASE,
)
def extract_greek_info(org_name: str) -> tuple[str, str, str | None]:
    greek_org = _GREEK_STRIP.sub('', org_name).strip().title()
    m = re.search(r'([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+)?)\s+CHAPTER', org_name, re.IGNORECASE)
    chapter = m.group(1).title() if m else None
    name_up = org_name.upper()
    if any(w in name_up for w in ['SOROR', 'WOMEN', 'WOMEN\'S']):
        org_type = 'sorority'
    elif any(w in name_up for w in ['FRATERN', 'BROTHERS', 'MEN\'S']):
        org_type = 'fraternity'
    else:
        org_type = 'chapter'
    return greek_org, org_type, chapter


_STRIP_ALUMNI = re.compile(
    r'\s+(?:ALUMNI|ALUMNAE|ALUM)\s+(?:ASSOCIATION|CLUB|CHAPTER|NETWORK|FOUNDATION|SOCIETY|GROUP)?.*$',
    re.IGNORECASE,
)
def extract_alumni_institution(org_name: str, db_city: str) -> str:
    cleaned = _STRIP_ALUMNI.sub('', org_name).strip()
    cleaned = re.sub(r'\s+(?:ALUMNI|ALUMNAE|ALUM).*$', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'\s+(?:INC|LLC|THE|OF|AT|FOR)[\s,]*$', '', cleaned, flags=re.IGNORECASE).strip()
    return cleaned.title() if len(cleaned) > 3 else db_city.title()


# ── cluster definitions ───────────────────────────────────────────────────────

CLUSTERS = {

'rotary': dict(
    label="Rotary clubs & foundations",
    where="""
        organization_name LIKE '%ROTARY%'
        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 3
        )
    """,
    system="""\
Write specific, location-grounded missions for Rotary clubs and foundations.
Each chapter serves a distinct city or region. Make each mission unique by
referencing the city and what Rotary chapters specifically do locally.

Rules:
- Name the city explicitly.
- One sentence, present tense.
- Do NOT start with the org name.
- Vary the verb: Awards / Funds / Organizes / Supports / Connects / Sponsors.
- Do NOT use "is dedicated to", "strives to", "committed to".
- Do NOT write the same sentence for two different cities.

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'rotary_chapter': extract_rotary_city(org['organization_name'], org['CITY'] or ''),
        'city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
        'type': 'foundation' if 'FOUNDATION' in org['organization_name'].upper() or 'FUND' in org['organization_name'].upper() else 'club',
    },
),

'vfw': dict(
    label="VFW / American Legion posts",
    where="""
        (organization_name LIKE '%VFW%'
         OR organization_name LIKE '%VETERANS OF FOREIGN%'
         OR organization_name LIKE '%AMERICAN LEGION%'
         OR organization_name LIKE '%AMVETS%')
        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 5
        )
    """,
    system="""\
Write specific missions for veterans service organizations: VFW posts,
American Legion posts, their auxiliaries, and AMVETS.
Each post serves a specific community. Reference the org type, post number
(if known), and city to produce a unique mission for every record.

Rules:
- Name the city explicitly.
- One sentence, present tense.
- Mention the specific org type (VFW, American Legion, Auxiliary, AMVETS).
- Vary the opening: Supports / Serves / Provides / Honors / Connects / Advocates for.
- Do NOT write the same sentence for two different posts.
- Do NOT use "is dedicated to", "strives to", "committed to".

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'org_type': extract_vfw_info(org['organization_name'])[0],
        'post': extract_vfw_info(org['organization_name'])[1],
        'city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
    },
),

'farm_bureau': dict(
    label="County Farm Bureaus",
    where="""
        organization_name LIKE '%FARM BUREAU%'
        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 3
        )
    """,
    system="""\
Write specific missions for county and state Farm Bureau organizations.
Each serves farmers and rural families in a specific county or region.
Use the county/city and state to write a unique, locally-grounded mission.

Rules:
- Name the county or city explicitly.
- One sentence, present tense.
- Vary the opening: Advocates for / Supports / Represents / Promotes / Connects.
- Include what Farm Bureaus actually do: advocacy, insurance, education, marketing.
- Do NOT use "is dedicated to", "strives to", "committed to".
- Do NOT write the same sentence for two different counties.

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'county_city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
        'name': org['organization_name'].title(),
    },
),

'union': dict(
    label="Labor unions / NTEE J locals",
    where="""
        NTEE1 = 'J'
        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 5
        )
    """,
    system="""\
Write specific missions for labor union locals and workforce organizations.
Each local represents workers in a specific trade, industry, and city.
Use the union type, local number (if present), and city.

Rules:
- Name the union type and city explicitly.
- One sentence, present tense.
- Vary the opening: Represents / Advocates for / Negotiates for / Protects / Supports.
- Include what the union does: collective bargaining, worker advocacy, benefits.
- Do NOT use "is dedicated to", "strives to", "committed to".
- Do NOT write the same sentence for two different locals.

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'union_type': extract_union_info(org['organization_name'])[0],
        'local': extract_union_info(org['organization_name'])[1],
        'city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
    },
),

'fire': dict(
    label="Volunteer fire departments",
    where="""
        organization_name LIKE '%FIRE%'
        AND (organization_name LIKE '%VOLUNTEER%'
             OR organization_name LIKE '%DISTRICT%'
             OR organization_name LIKE '%DEPT%'
             OR organization_name LIKE '%DEPARTMENT%')
        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 5
        )
    """,
    system="""\
Write specific missions for volunteer fire departments and fire districts.
Each serves a distinct township, borough, or rural area. Use the area name
from the department name and the city/state to produce a unique mission.

Rules:
- Name the specific area or township explicitly.
- One sentence, present tense.
- Vary the opening: Provides / Protects / Responds to / Serves / Delivers.
- Include: fire suppression, emergency medical response, rescue, community safety.
- Do NOT use "is dedicated to", "strives to", "committed to".
- Do NOT write the same sentence for two different departments.

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'area': extract_fire_area(org['organization_name']),
        'city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
    },
),

'intl': dict(
    label="NTEE Q international orgs",
    where="""
        NTEE1 = 'Q'
        AND organization_name NOT LIKE '%ROTARY%'
        AND organization_name NOT LIKE '%LIONS%'
        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 5
        )
    """,
    system="""\
Write specific missions for international development and humanitarian nonprofits.
Each has a unique focus — use the org name and city to infer the specific work.

Rules:
- One sentence, present tense.
- Be specific to the org name — no generic "provides humanitarian aid" templates.
- Infer the focus from the name (education, water, health, microfinance, etc.).
- Do NOT use "is dedicated to", "strives to", "committed to".

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'name': org['organization_name'].title(),
        'city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
    },
),


'lions': dict(
    label="Lions Club chapters",
    where="""
        (organization_name LIKE '%LIONS CLUB%'
         OR (organization_name LIKE '%LIONS%' AND organization_name LIKE '%INTERNATIONAL%'))
        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 3
        )
    """,
    system="""\
Write specific missions for Lions Club chapters.
Each chapter serves a distinct city or community. Make each mission unique by
referencing the city and Lions Club's specific community programs.

Rules:
- Name the city explicitly.
- One sentence, present tense.
- Do NOT start with the org name.
- Vary the verb: Organizes / Funds / Sponsors / Supports / Connects / Serves.
- Lions programs include: vision care, diabetes awareness, youth leadership, food banks.
- Do NOT use "is dedicated to", "strives to", "committed to".
- Do NOT write the same sentence for two different chapters.

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'lions_chapter': extract_lions_city(org['organization_name'], org['CITY'] or ''),
        'city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
    },
),

'masonic': dict(
    label="Masonic lodges and fraternal orders",
    where="""
        (organization_name LIKE '%MASONIC%'
         OR organization_name LIKE '%FREEMASON%'
         OR organization_name LIKE '%FREE%ACCEPTED MASON%'
         OR organization_name LIKE '%F & AM%'
         OR organization_name LIKE '%F&AM%'
         OR organization_name LIKE '%GRAND LODGE%'
         OR organization_name LIKE '%EASTERN STAR%'
         OR organization_name LIKE '%SHRINER%'
         OR organization_name LIKE '%ELKS LODGE%'
         OR (organization_name LIKE '%ELKS%' AND organization_name LIKE '%ORDER%')
         OR organization_name LIKE '%ODD FELLOW%'
         OR organization_name LIKE '%REBEKAH%'
         OR (organization_name LIKE '%KNIGHTS OF%'
             AND (organization_name LIKE '%COLUMBUS%' OR organization_name LIKE '%PYTHIAS%'))
         OR (organization_name LIKE '%LOYAL ORDER%' AND organization_name LIKE '%MOOSE%'))

        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 5
        )
    """,
    system="""\
Write specific missions for Masonic lodges and fraternal organizations including
Shriners, Elks, Odd Fellows, Rebekahs, Knights of Columbus, and Moose lodges.
Each lodge serves a specific community. Use the lodge type, number, and city.

Rules:
- Name the city and lodge type explicitly.
- One sentence, present tense.
- Do NOT start with "The [name]...".
- Vary the opening: Brings together / Hosts / Supports / Connects / Organizes / Funds.
- Include what these orgs do: fellowship, charitable giving, youth programs, community events.
- Do NOT use "is dedicated to", "strives to", "committed to".
- Do NOT write the same sentence for two different lodges.

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'lodge_type': extract_masonic_info(org['organization_name'])[0],
        'lodge_num': extract_masonic_info(org['organization_name'])[1],
        'city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
    },
),

'greek': dict(
    label="Greek-letter sororities and fraternities",
    where="""
        (organization_name LIKE '%ALPHA PHI%'
         OR organization_name LIKE '%KAPPA DELTA%'
         OR organization_name LIKE '%SIGMA CHI%'
         OR organization_name LIKE '%KAPPA ALPHA%'
         OR organization_name LIKE '%DELTA GAMMA%'
         OR organization_name LIKE '%PI KAPPA%'
         OR organization_name LIKE '%PHI BETA%'
         OR organization_name LIKE '%BETA THETA%'
         OR organization_name LIKE '%LAMBDA CHI%'
         OR organization_name LIKE '%SIGMA ALPHA%'
         OR organization_name LIKE '%DELTA DELTA%'
         OR organization_name LIKE '%GAMMA PHI%'
         OR organization_name LIKE '%PHI MU%'
         OR organization_name LIKE '%ALPHA DELTA%'
         OR organization_name LIKE '%THETA CHI%'
         OR organization_name LIKE '%DELTA TAU%'
         OR organization_name LIKE '%ZETA BETA%'
         OR organization_name LIKE '%PHI GAMMA%'
         OR organization_name LIKE '%SIGMA PHI%')
        AND (organization_name LIKE '%FRATERN%'
             OR organization_name LIKE '%SOROR%'
             OR organization_name LIKE '%CHAPTER%'
             OR NTEE1 = 'Y')
        AND mission IS NOT NULL AND mission != ''
        AND mission_source NOT IN ('ai_haiku','lucido','claimed')
        AND mission IN (
            SELECT mission FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            GROUP BY mission HAVING COUNT(*) >= 5
        )
    """,
    system="""\
Write specific missions for Greek-letter college sororities and fraternities.
Each chapter is at a different college or university. Use the Greek org name,
chapter designation, and city to produce a unique mission for every record.

Rules:
- Name the Greek org (e.g., Alpha Phi, Kappa Delta) and city explicitly.
- One sentence, present tense.
- Do NOT start with the org name.
- Vary the opening: Brings together / Builds / Connects / Supports / Fosters / Develops.
- Greek chapter work includes: academic support, community service, leadership, philanthropy.
- Do NOT use "is dedicated to", "strives to", "committed to".
- Do NOT write the same sentence for two different chapters.

Respond ONLY with JSON array: [{"ein": "...", "mission": "..."}, ...]""",
    build=lambda org: {
        'ein': org['EIN'],
        'greek_org': extract_greek_info(org['organization_name'])[0],
        'org_type': extract_greek_info(org['organization_name'])[1],
        'chapter': extract_greek_info(org['organization_name'])[2],
        'city': (org['CITY'] or '').title(),
        'state': org['STATE'] or '',
    },
),

}  # end CLUSTERS


# ── shared Haiku call ─────────────────────────────────────────────────────────

def _load_env():
    env = BASE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip()


def _call_haiku(rows: list[dict], system: str, build_fn) -> dict[str, str]:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if len(key) < 20:
        return {}
    items = [build_fn(r) for r in rows]
    prompt = (
        "Write a specific mission for each organization. "
        "Use the fields provided to make each mission distinct.\n\n"
        + json.dumps(items, indent=2)
        + "\n\nReturn JSON array: [{\"ein\": \"...\", \"mission\": \"...\"}, ...]"
    )
    payload = json.dumps({
        "model": HAIKU, "max_tokens": 1500, "system": system,
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
                cost  = (usage.get("input_tokens", 0) / 1e6 * COST_IN +
                         usage.get("output_tokens", 0) / 1e6 * COST_OUT)
                global _spend
                with _lock:
                    _spend += cost
                text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\s*```$', '', text)
                m = re.search(r'\[.*\]', text, re.DOTALL)
                if not m:
                    return {}
                parsed = json.loads(m.group())
                return {
                    item["ein"]: item["mission"].strip()
                    for item in parsed
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


def _write(results: dict[str, str], conn: sqlite3.Connection, batch_size: int):
    global _written, _errors
    if not results:
        with _lock:
            _errors += batch_size
        return
    with _lock:
        conn.executemany(
            "UPDATE registry_enriched SET mission=?, mission_source='ai_haiku' WHERE EIN=?",
            [(m, ein) for ein, m in results.items()]
        )
        conn.commit()
        _written += len(results)


def run_cluster(name: str, cluster: dict, conn: sqlite3.Connection,
                total_target: int, limit: int | None, workers: int,
                budget: float, dry_run: bool, start_time: float):
    rows = [dict(r) for r in conn.execute(
        f"SELECT EIN, organization_name, NTEE1, CITY, STATE, mission "
        f"FROM registry_enriched WHERE {cluster['where']} "
        f"{'LIMIT ' + str(limit) if limit else ''}"
    )]
    if not rows:
        print(f"  {cluster['label']}: nothing to fix")
        return

    if dry_run:
        print(f"\n  --- {cluster['label']} ({len(rows)} orgs) ---")
        for org in rows[:5]:
            built = cluster['build'](org)
            print(f"    {org['organization_name']} ({org['CITY']}, {org['STATE']})")
            print(f"    fields: { {k:v for k,v in built.items() if k != 'ein'} }")
            print(f"    old:    {org['mission'][:80]}")
        return

    batches = [rows[i:i+BATCH] for i in range(0, len(rows), BATCH)]
    print(f"  {cluster['label']}: {len(rows):,} orgs  ({len(batches)} batches)")

    def process(batch):
        global _spend
        with _lock:
            if _spend >= budget:
                return
        results = _call_haiku(batch, cluster['system'], cluster['build'])
        _write(results, conn, len(batch))
        elapsed = time.time() - start_time
        rate    = _written / elapsed if elapsed > 0 else 0
        eta     = (total_target - _written) / rate / 60 if rate > 0 else 0
        print(
            f"\r    [{_written/total_target*100:5.1f}%] {_written:,} written  "
            f"${_spend:.2f}  ETA {eta:.0f}m",
            end="", flush=True,
        )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(process, b) for b in batches]
        for f in as_completed(futs):
            with _lock:
                if _spend >= budget:
                    for p in futs: p.cancel()
                    break
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster", choices=list(CLUSTERS.keys()) + ["all"], default="all")
    ap.add_argument("--limit",   type=int,   default=None)
    ap.add_argument("--workers", type=int,   default=2)
    ap.add_argument("--budget",  type=float, default=15.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    _load_env()
    if not args.dry_run and len(os.environ.get("ANTHROPIC_API_KEY", "")) < 20:
        print("ERROR: ANTHROPIC_API_KEY not set in .env"); return

    conn = sqlite3.connect(DB, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    to_run = CLUSTERS if args.cluster == "all" else {args.cluster: CLUSTERS[args.cluster]}

    # Count total targets
    total = 0
    for name, cl in to_run.items():
        n = conn.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {cl['where']}").fetchone()[0]
        if args.limit: n = min(n, args.limit)
        total += n

    est = (total // BATCH + 1)
    est_cost = est * 1200 / 1e6 * COST_IN + est * 1000 / 1e6 * COST_OUT
    print(f"Chapter org regeneration — {HAIKU}")
    print(f"Clusters: {', '.join(to_run.keys())}  Total targets: {total:,}")
    print(f"Estimated cost: ${est_cost:.2f}  Budget cap: ${args.budget:.2f}")

    start = time.time()
    for name, cluster in to_run.items():
        with _lock:
            if _spend >= args.budget:
                print(f"Budget cap reached — skipping {name}")
                break
        run_cluster(name, cluster, conn, total, args.limit,
                    args.workers, args.budget, args.dry_run, start)

    if not args.dry_run:
        elapsed = (time.time() - start) / 60
        print(f"\nDone in {elapsed:.1f} min — {_written:,} missions rewritten  ${_spend:.2f} spent")
    conn.close()


if __name__ == "__main__":
    main()
