#!/usr/bin/env python3
"""
Flask API for Daanaa droplet — serves precomputed JSON files + SQLite search.

Browse:  precomputed gzipped JSON (fast, no DB)
Search:  FTS5 via search.db (all 1.8M orgs)
Detail:  precomputed org file → fallback to search.db orgs table
"""

import gzip
import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from math import radians, cos, sin, asin, sqrt
from pathlib import Path

import html as _htmllib
from flask import Flask, request, jsonify, send_file, send_from_directory, Response, redirect
from flask_cors import CORS

try:
    import boto3
    S3_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    S3_AVAILABLE = False
    boto3 = None

app = Flask(__name__, static_folder=None)
# Restrict CORS to the production origins. The SPA is served same-origin, so
# this only governs cross-origin API calls — no need to allow the whole web.
CORS(app, origins=["https://daanaa.org", "https://www.daanaa.org"],
     supports_credentials=False)

# Log S3 enrichment availability at startup
if S3_AVAILABLE:
    print("[INFO] S3 enrichment layer: AVAILABLE (Phase 2a)", flush=True)
else:
    print("[INFO] S3 enrichment layer: NOT AVAILABLE (boto3 missing or AWS creds not set)", flush=True)


@app.after_request
def set_security_headers(response):
    # ── Cache policy (2026-07-16 loading-speed pass) ──────────────────────
    # /assets/* are content-hashed by Vite: immutable forever → Cloudflare
    # edge-caches them globally (was 4h default + MISS). HTML must always
    # revalidate so a deployed SPA update is picked up immediately — a stale
    # cached index.html referencing purged chunk names 404s the whole app.
    if request.path.startswith('/assets/'):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif response.mimetype == 'text/html':
        response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # CSP must allow Firebase/Google Sign-In origins (daanaa.org serves the auth
    # popup). Mirrors daanaa_api.py so prod and home server stay consistent.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://apis.google.com https://daanaa-af9c2.firebaseapp.com https://stats.daanaa.org https://plausible.io; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "connect-src 'self' https://daanaa.org https://www.daanaa.org "
        "https://stats.daanaa.org https://plausible.io "
        "https://identitytoolkit.googleapis.com "
        "https://securetoken.googleapis.com "
        "https://www.googleapis.com; "
        "frame-src https://accounts.google.com https://daanaa-af9c2.firebaseapp.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    # HSTS — daanaa.org is HTTPS-only via Cloudflare.
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


DATA_DIR     = Path(os.environ.get('PRECOMPUTE_DIR', '/data/precompute/v1'))
# CLAIMS_DIR is DEAD CODE (no code writes to it; see merge_claims docstring).
# Retained for historical clarity; no production deployments should use it.
CLAIMS_DIR   = Path(os.environ.get('CLAIMS_DIR', '/data/claims'))
FRONTEND_DIR = Path(os.environ.get('FRONTEND_DIR', '/opt/daanaa/frontend/dist'))

# Bounded LRU: org-detail traffic covers 1.76M distinct files, so an
# unbounded cache grows until the 2GB box swaps and the search.db loses its
# page cache (2026-07-18: 13s searches with a correct query plan). The cap
# keeps hot content/browse files resident while org pages churn through.
_JSON_CACHE_MAX = 512
_json_cache: "OrderedDict[str, object]" = OrderedDict()
_multi_cache: dict = {}

_TOP_STATES = ['CA', 'TX', 'NY', 'FL', 'PA', 'OH', 'IL', 'GA', 'NC', 'MI',
               'NJ', 'VA', 'WA', 'TN', 'AZ', 'CO', 'MN', 'MO', 'IN', 'MA']
_ALL_NTEE1  = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

PER_PAGE_DEFAULT = 25


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_json_gz(path):
    path = Path(path)
    key = str(path)
    if key in _json_cache:
        _json_cache.move_to_end(key)
        return _json_cache[key]
    if not path.exists():
        return None
    try:
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        _json_cache[key] = data
        while len(_json_cache) > _JSON_CACHE_MAX:
            _json_cache.popitem(last=False)
        return data
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None


class _PersistentConn:
    """Wraps the shared per-worker sqlite connection; .close() is a no-op so
    existing `finally: conn.close()` call sites don't tear it down. Lifecycle
    is handled by get_search_db()'s inode check (reopens after atomic swap)."""
    __slots__ = ('_c',)

    def __init__(self, c):
        self._c = c

    def __getattr__(self, name):
        return getattr(self._c, name)

    def close(self):
        pass


_search_conn = None
_search_db_ino = None


def get_search_db():
    """Per-worker persistent connection (2026-07-16 speed pass).

    Opening sqlite per request threw away the page cache on every search.
    We keep one connection per gunicorn worker and check the file inode per
    request: the nightly deploy replaces search.db via atomic mv (new inode),
    which triggers a clean reopen — no stale data, no service restart needed.
    """
    global _search_conn, _search_db_ino, _SEARCH_DB_HAS_CLAIMS
    fts_path = DATA_DIR / 'search.db'
    try:
        ino = fts_path.stat().st_ino
    except OSError:
        return None
    if _search_conn is not None and ino == _search_db_ino:
        return _search_conn
    if _search_conn is not None:
        try:
            _search_conn._c.close()
        except Exception:
            pass
        _SEARCH_DB_HAS_CLAIMS = None  # re-detect against the new file
    conn = sqlite3.connect(str(fts_path), timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Serve cold page reads from the OS page cache; big win on filter scans.
    conn.execute("PRAGMA mmap_size=1073741824")
    conn.execute("PRAGMA cache_size=-65536")   # 64MB page cache per worker
    conn.execute("PRAGMA query_only=1")        # this API never writes search.db
    _search_conn = _PersistentConn(conn)
    _search_db_ino = ino
    return _search_conn


# Cached at first use: org_claims is excluded from search.db for privacy (sync_db.sh),
# so the volunteer filter gracefully returns no matches when the table is absent.
_SEARCH_DB_HAS_CLAIMS: bool | None = None

def _search_db_has_org_claims(conn) -> bool:
    """Return True if org_claims table is present in search.db (cached)."""
    global _SEARCH_DB_HAS_CLAIMS
    if _SEARCH_DB_HAS_CLAIMS is None:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='org_claims'"
        ).fetchone()
        _SEARCH_DB_HAS_CLAIMS = row is not None
    return _SEARCH_DB_HAS_CLAIMS


def _haversine_mi(lat1, lon1, lat2, lon2):
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))


def _zips_within_radius(conn, lat, lon, radius_mi):
    dlat = radius_mi / 69.0
    dlon = radius_mi / (69.0 * cos(radians(lat)))
    rows = conn.execute(
        "SELECT zip, lat, lon FROM zip_codes WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
        (lat - dlat, lat + dlat, lon - dlon, lon + dlon)
    ).fetchall()
    return {r["zip"] for r in rows if _haversine_mi(lat, lon, r["lat"], r["lon"]) <= radius_mi}


_STATE_NAME_TO_ABBR = {
    'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
    'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
    'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID',
    'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
    'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
    'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
    'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
    'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
    'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
    'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
    'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
    'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
    'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC',
    'PUERTO RICO': 'PR',
}

def _resolve_location(conn, near_raw):
    """Resolve free-text location to (lat, lon, city, state). Returns None if unresolvable."""
    near = near_raw.strip()
    if near.isdigit() and len(near) == 5:
        row = conn.execute("SELECT lat, lon, city, state_id FROM zip_codes WHERE zip=?", (near,)).fetchone()
        if row:
            return row["lat"], row["lon"], row["city"], row["state_id"]
    m = re.match(r'^(.+?)[,\s]+([A-Z]{2})$', near.upper())
    if m:
        city_q, state_q = m.group(1).strip(), m.group(2)
        row = conn.execute(
            "SELECT lat, lon, city, state_id FROM zip_codes WHERE UPPER(city)=? AND state_id=? LIMIT 1",
            (city_q, state_q)
        ).fetchone()
        if row:
            return row["lat"], row["lon"], row["city"], row["state_id"]
    # Full state name ("Houston Texas", "Houston, New York"): users type this
    # constantly and it used to be silently ignored (filter looked applied,
    # did nothing — 2026-07-10). Match the trailing state name, map to the
    # 2-letter code zip_codes actually stores.
    up = near.upper()
    for full, abbr in _STATE_NAME_TO_ABBR.items():
        if up.endswith(' ' + full) or up.endswith(',' + full) or up.endswith(', ' + full):
            city_q = up[: len(up) - len(full)].rstrip(' ,').strip()
            if city_q:
                row = conn.execute(
                    "SELECT lat, lon, city, state_id FROM zip_codes WHERE UPPER(city)=? AND state_id=? LIMIT 1",
                    (city_q, abbr)
                ).fetchone()
                if row:
                    return row["lat"], row["lon"], row["city"], row["state_id"]
    row = conn.execute(
        "SELECT lat, lon, city, state_id FROM zip_codes WHERE UPPER(city)=? LIMIT 1",
        (near.upper(),)
    ).fetchone()
    if row:
        return row["lat"], row["lon"], row["city"], row["state_id"]
    return None


# ── FTS5 query sanitization ────────────────────────────────────────────────
# KEEP IN SYNC with daanaa_api.py:_sanitize_fts_query — this file ships alone
# to the droplet, so the function is duplicated rather than imported.
# tests/test_search_quality.py exercises both copies against hostile queries.
# Apostrophes FUSE ("L'Anse" → "LAnse"): IRS stores "L'ANSE" as "LANSE".
_FTS5_APOS  = re.compile(r"['’`]")
_FTS5_STRIP = re.compile(r'[^\w\s]', re.UNICODE)
_FTS5_NOISE = frozenset({
    'nonprofit', 'nonprofits', 'charity', 'charities',
    'organization', 'organizations', '501c3', 'ngo',
    'find', 'search', 'best', 'top', 'local', 'near',
    'metro', 'greater', 'region', 'area',
})

def _sanitize_fts_query(text: str) -> str:
    """Donor text → valid FTS5 MATCH expression.

    FTS5 assigns syntax meaning to -, :, /, parens and quotes: "4-H" parsed
    as column-NOT ("no such column: H"), "St. Jude's" as a syntax error. On
    this edge the exception was swallowed into silent 0 results — a donor
    typing a real org's real name saw an empty page (2026-07-18 audit).
    """
    clean = _FTS5_STRIP.sub(' ', _FTS5_APOS.sub('', text))
    words = [w for w in clean.split() if w.lower() not in _FTS5_NOISE]
    # Single-char tokens (the "4"/"H" of "4-H") survive only alongside other
    # tokens — a lone "a"* would prefix-scan the whole index.
    if len(words) >= 2:
        words = words[:12]
    else:
        words = [w for w in words if len(w) >= 2]
    if not words:
        return '""'
    # Double-quoted tokens keep donor-typed AND/OR/NOT literal, not operators.
    # Single-char tokens match EXACTLY (no star): '"n"*' range-scans every
    # n-word in the term dictionary — 15s+ timeouts on this 2GB box.
    return ' '.join(f'"{w}"*' if len(w) >= 2 else f'"{w}"' for w in words)


# ── Corpus-vocabulary typo correction (zero-result rescue) ─────────────────
# KEEP IN SYNC with scripts/search_typo.py (single-file deploy). Runs ONLY
# when a search returned nothing — the happy path never pays for it. The
# dictionary is our own org_name vocabulary via fts5vocab: corrections can
# only point at words that exist in real org names. Hard 150ms budget.
_TYPO_ALPHA = 'abcdefghijklmnopqrstuvwxyz'
_TYPO_BUDGET_S = 0.15
_TYPO_PREFER = 10
_typo_conn = None
_typo_ino = None


def _get_typo_conn():
    """Read-only conn WITHOUT query_only (temp fts5vocab creation counts as a
    write, which PRAGMA query_only blocks). Tracks the search.db inode — the
    nightly deploy swaps the file via atomic mv."""
    global _typo_conn, _typo_ino
    fts_path = DATA_DIR / 'search.db'
    try:
        ino = fts_path.stat().st_ino
    except OSError:
        return None
    if _typo_conn is not None and ino == _typo_ino:
        return _typo_conn
    if _typo_conn is not None:
        try:
            _typo_conn.close()
        except Exception:
            pass
    try:
        conn = sqlite3.connect(f"file:{fts_path}?mode=ro", uri=True,
                               timeout=5, check_same_thread=False)
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS temp.org_vocab "
                     "USING fts5vocab('main', 'org_fts', 'col')")
    except sqlite3.OperationalError:
        return None
    _typo_conn, _typo_ino = conn, ino
    return conn


def _typo_doc(conn, term):
    row = conn.execute(
        "SELECT doc FROM temp.org_vocab WHERE term = ? AND col = 'org_name'",
        (term,)).fetchone()
    return row[0] if row else 0


def _typo_edit1(tok):
    for i in range(len(tok)):
        yield tok[:i] + tok[i + 1:]
        if i < len(tok) - 1:
            yield tok[:i] + tok[i + 1] + tok[i] + tok[i + 2:]
        for c in _TYPO_ALPHA:
            if c != tok[i]:
                yield tok[:i] + c + tok[i + 1:]
    for i in range(len(tok) + 1):
        for c in _TYPO_ALPHA:
            yield tok[:i] + c + tok[i:]


def _typo_correct_query(text):
    conn = _get_typo_conn()
    if conn is None:
        return None
    deadline = time.time() + _TYPO_BUDGET_S
    toks = _FTS5_STRIP.sub(' ', _FTS5_APOS.sub('', text)).split()[:6]
    if not toks:
        return None
    out, changed = [], False
    for tok in toks:
        low = tok.lower()
        if len(low) < 3 or time.time() > deadline:
            out.append(tok)
            continue
        own = _typo_doc(conn, low)
        best, best_doc = None, 0
        seen = {low}
        for v in _typo_edit1(low):
            if time.time() > deadline:
                break
            if len(v) < 2 or v in seen:
                continue
            seen.add(v)
            d = _typo_doc(conn, v)
            if d > best_doc:
                best, best_doc = v, d
        if best and best_doc >= max(_TYPO_PREFER * own, _TYPO_PREFER):
            out.append(best.upper() if tok.isupper() else best)
            changed = True
        else:
            out.append(tok)
    return ' '.join(out) if changed else None


def _fts_where(q: str, state: str = '', conn=None) -> tuple:
    """Build base FTS WHERE conditions and params for q + state.
    Returns (conditions, params, detected_zip_or_None).
    If conn is provided, resolves zip to city name so FTS can find orgs."""
    detected_zip = None
    words = q.split()
    # Extract any standalone 5-digit zip from any position in the query.
    non_zip_words = []
    for w in words:
        if re.match(r'^\d{5}$', w) and detected_zip is None:
            detected_zip = w
        else:
            non_zip_words.append(w)

    zip_city = None
    zip_state = None
    if detected_zip and conn:
        zrow = conn.execute(
            "SELECT city, state_id FROM zip_codes WHERE zip=?", (detected_zip,)
        ).fetchone()
        if zrow:
            zip_city = zrow["city"]
            zip_state = zrow["state_id"]

    # Build FTS query: if bare zip (no other keywords), search by resolved city.
    # If mixed ("food bank 97701"), keep keywords and append city to help location.
    if non_zip_words:
        fts_terms = non_zip_words
        if zip_city and zip_city.lower() not in ' '.join(non_zip_words).lower():
            fts_terms = non_zip_words + [zip_city]
    elif zip_city:
        fts_terms = [zip_city]
    else:
        # Unknown zip or no conn: fall back to raw query so we return something
        fts_terms = words

    fts_q = _sanitize_fts_query(' '.join(w for w in fts_terms if w))
    conditions: list = ["s.ein = o.EIN", "org_fts MATCH ?"]
    params: list = [fts_q]
    # State filter: prefer explicit param, fall back to zip-resolved state
    resolved_state = state or zip_state or ''
    if resolved_state:
        conditions.append("o.STATE = ?")
        params.append(resolved_state)
    return conditions, params, detected_zip


def _cat_rev_conditions(ntee_list, sub_list, min_rev, max_rev, alias='', verified_revenue_only=False):
    """Category + revenue WHERE fragments, mirroring the home daanaa_api
    semantics: any ticked category (NTEE1) or subcategory (NTEECC prefix)
    matches, AND revenue within [min_rev, max_rev]. The old code took only
    the first character of the ntee param, so 'R,I' matched nothing and
    revenue was ignored entirely (0-results bug on production, 2026-06-09).

    verified_revenue_only: if True, exclude orgs with NULL revenue. Default False
    includes all orgs (Stewardship Principle 4)."""
    conds: list = []
    params: list = []
    cat_parts: list = []
    if ntee_list:
        cat_parts.append(f"{alias}NTEE1 IN ({','.join('?' * len(ntee_list))})")
        params.extend(ntee_list)
    for s in sub_list:
        # GLOB not LIKE: case-sensitive so SQLite can drive it from the
        # NTEECC index (values are already uppercase); LIKE forces a scan.
        cat_parts.append(f"{alias}NTEECC GLOB ?")
        params.append(s + '*')
    if cat_parts:
        conds.append('(' + ' OR '.join(cat_parts) + ')')
    # Revenue filter: include no-data orgs by default (stewardship), optionally exclude them
    if min_rev is not None or max_rev is not None:
        rev_parts = []
        if not verified_revenue_only:
            rev_parts.append(f"{alias}total_revenue IS NULL")
        # Range conditions (min AND max) in a subgroup
        range_parts = []
        if min_rev is not None:
            range_parts.append(f"{alias}total_revenue >= ?")
            params.append(min_rev)
        if max_rev is not None:
            range_parts.append(f"{alias}total_revenue <= ?")
            params.append(max_rev)
        if range_parts:
            rev_parts.append('(' + ' AND '.join(range_parts) + ')')
        conds.append('(' + ' OR '.join(rev_parts) + ')')
    return conds, params


# Visibility level (lamp tier) filter. The DB stores a wider set of historical
# tier names than the 4 the UI shows, so map each display tier to its DB values.
_TIER_DB_VALUES = {
    'beacon': ('Beacon',),
    'torch':  ('Torch', 'Lantern', 'Flame'),
    'candle': ('Candle', 'Ember', 'Glow'),
    'spark':  ('Spark', 'Seed'),
}


def _tier_condition(tier: str, alias: str = ''):
    """WHERE fragment + params for a visibility-level filter, or (None, [])."""
    vals = _TIER_DB_VALUES.get((tier or '').strip().lower())
    if not vals:
        return None, []
    return f"{alias}merit_tier IN ({','.join('?' * len(vals))})", list(vals)


def _order_clause(sort: str, order: str, alias: str = '') -> str:
    """ORDER BY body honoring an asc/desc direction. Name defaults A-Z,
    revenue/score default high-first; an explicit order param overrides.
    Unspecified sort falls back to neutral name order (2026-07-04: browse must
    never imply a ranking; merit_score sort is explicit opt-in only).
    COALESCE keeps NULLs last (and, per the 2026-06-09 note, avoids the score
    index forcing a row-by-row probe on filtered browses).
    Random sort returns empty string; shuffle happens in-memory after fetch."""
    o = (order or '').strip().lower()
    if sort == 'random':
        # Shuffle handled in-memory after fetch, not in SQL
        return ""
    if sort in ('revenue', 'total_revenue'):
        d = 'ASC' if o == 'asc' else 'DESC'
        return f"COALESCE({alias}total_revenue, -1) {d}"
    if sort == 'merit_score':
        d = 'ASC' if o == 'asc' else 'DESC'
        return f"COALESCE({alias}merit_score, -1) {d}"
    # default + explicit name sort
    d = 'DESC' if o == 'desc' else 'ASC'
    return f"{alias}organization_name {d}"


# Peer benchmark stats per (archetype, band) — mirrors enrich_api_responses.py
_V5_BENCHMARKS = {
    ('donation_funded', 'micro'):         {'p25': 6.2,   'p50': 19.2, 'p75': 61.8,  'hr': 49.0},
    ('donation_funded', 'professional'):  {'p25': 4.7,   'p50': 12.9, 'p75': 32.8,  'hr': 54.6},
    ('donation_funded', 'established'):   {'p25': 4.5,   'p50': 11.4, 'p75': 26.4,  'hr': 51.2},
    ('fee_for_service', 'micro'):         {'p25': 8.0,   'p50': 21.0, 'p75': 40.0,  'hr': 50.0},
    ('fee_for_service', 'professional'):  {'p25': 5.0,   'p50': 10.0, 'p75': 20.0,  'hr': 45.0},
    ('fee_for_service', 'established'):   {'p25': 4.0,   'p50': 8.8,  'p75': 18.0,  'hr': 42.0},
    ('endowment', 'micro'):               {'p25': 120.0, 'p50': 120.0,'p75': 120.0, 'hr': 98.0},
    ('endowment', 'professional'):        {'p25': 120.0, 'p50': 120.0,'p75': 120.0, 'hr': 99.0},
    ('endowment', 'established'):         {'p25': 120.0, 'p50': 120.0,'p75': 120.0, 'hr': 99.0},
}


def _assemble_v5_context(d: dict) -> dict | None:
    """Build the v5_context dict from individual v5 columns in a search.db row."""
    d.pop('merit_archetype_v5', None)          # integer index — not used directly
    arch_label = d.pop('merit_archetype_v5_label', None)
    band_key   = d.pop('merit_band_v5', None)  # already a string key (micro/professional/established)
    band_label = d.pop('merit_band_v5_label', None)
    score      = d.pop('merit_score_v5', None)
    health     = d.pop('merit_health_signal_v5', None)
    peer_group = d.pop('merit_peer_group_v5', None)
    peer_count = d.pop('merit_peer_count_v5', None)
    reserves   = d.get('months_of_reserve')

    if not arch_label or score is None or not health:
        return None

    # Derive canonical arch_key from label for _V5_BENCHMARKS lookup
    lbl = (arch_label or '').lower()
    if 'donation' in lbl:
        arch_key = 'donation_funded'
    elif 'fee' in lbl or 'service' in lbl:
        arch_key = 'fee_for_service'
    else:
        arch_key = 'endowment'

    bench = _V5_BENCHMARKS.get((arch_key, band_key), {})
    p50 = bench.get('p50', 0)

    if health == 'HEALTHY':
        health_desc = 'Above the typical level for similar organizations, suggesting solid financial stability.'
    elif health == 'STABLE':
        health_desc = 'Close to the typical level for similar organizations, showing steady financial management.'
    else:
        health_desc = 'Below the typical level for similar organizations. This organization may be in a growth phase or operating lean by design.'

    if reserves and p50:
        explanation = (
            f"This organization is a {arch_label} nonprofit with a budget in the {band_label} range. "
            f"Looking at its financial reserves: Organizations like this one typically keep about {int(p50)} months "
            f"of operating costs in reserve. This one has {reserves:.1f} months. {health_desc} "
            f"This comparison is based on public IRS 990 data from {(peer_count or 0):,} similar organizations."
        )
    elif reserves:
        explanation = (
            f"This organization is a {arch_label} nonprofit with a budget in the {band_label} range. "
            f"It currently holds {reserves:.1f} months of operating costs in reserve. "
            f"Peer reserve benchmarks are not yet available for this funding model. "
            f"This context is based on public IRS 990 data."
        )
    else:
        explanation = "Financial data not available from IRS Form 990."

    return {
        'archetype': {'key': arch_key, 'label': arch_label},
        'band': {'key': band_key, 'label': band_label},
        'peer_group': {'label': peer_group, 'org_count': peer_count},
        'score': {'percentile': int(score) if score is not None else 0, 'health_signal': health},
        'benchmarks': {
            'reserves_months': {
                'p25': bench.get('p25', 0), 'p50': p50,
                'p75': bench.get('p75', 0), 'your_value': reserves,
            },
            'healthy_rate_peer': bench.get('hr', 0),
        },
        'donor_explanation': explanation,
    }


def _row_to_org(row) -> dict:
    """Convert a search.db orgs row to the org dict the frontend expects."""
    d = dict(row)
    cause = d.get('cause_tags')
    if isinstance(cause, str) and cause:
        try:
            d['cause_tags'] = json.loads(cause)
        except Exception:
            d['cause_tags'] = []
    d['is_hidden_gem'] = bool(d.get('is_hidden_gem'))
    d['data_badges'] = {'mission': d.get('mission_source')}
    # Assemble v5_context from v5 columns (present after search.db rebuild with v5 fields)
    if 'merit_archetype_v5' in d:
        d['v5_context'] = _assemble_v5_context(d)
    return d


# Cause-cohort context table (by_nteecc / by_ntee1 → typical reserves, healthy
# rate, n). Lives next to the API file so it survives data-dir payload swaps;
# DATA_DIR is also checked so a future payload can carry it instead.
_COHORT_CTX = None

def _load_cohort_ctx() -> dict:
    global _COHORT_CTX
    if _COHORT_CTX is None:
        for p in (DATA_DIR / 'cohort_context.json', Path(__file__).resolve().parent / 'cohort_context.json'):
            try:
                if p.exists():
                    _COHORT_CTX = json.loads(p.read_text())
                    break
            except Exception:
                pass
        if _COHORT_CTX is None:
            _COHORT_CTX = {'by_nteecc': {}, 'by_ntee1': {}}
    return _COHORT_CTX


def _attach_cohort_context(data: dict) -> None:
    """Cause-cohort financial context for orgs with no financials of their own.

    Serve-time equivalent of the live API's cohort enrichment (daanaa_api.py →
    enrich_api_responses.get_cohort_context): when the org has no financial
    assessment at all, show the *typical* shape of its NTEE cause-cohort —
    explicitly framed as about the cause area, not this org (Stewardship P3/P4).
    Precomputed JSONs built before 2026-07-16 carry cohort_context=null for
    archetype-but-unscored orgs; we correct at serve time rather than waiting
    for a full precompute rebuild (same pattern as _patch_v5_benchmarks).
    """
    if data.get('cohort_context') is not None:
        return
    # Only fill a genuinely blank financial section — never compete with a
    # real assessment. "Real" means actual numbers (reserves) or a v5 health
    # signal; a v4 tier label with no numbers behind it still renders an empty
    # financial panel (V5Context returns null without a health_signal), so it
    # must not block the cohort fallback — 37K orgs hit that empty state.
    if data.get('months_of_reserve') is not None:
        return
    v5_score = (data.get('v5_context') or {}).get('score') or {}
    if v5_score.get('health_signal'):
        return
    ctx = _load_cohort_ctx()
    nteecc, ntee1 = data.get('NTEECC'), data.get('NTEE1')
    b = ctx.get('by_nteecc', {}).get(nteecc) if nteecc else None
    if b:
        data['cohort_context'] = {**b, 'level': 'subcategory', 'ntee_code': nteecc}
        return
    b = ctx.get('by_ntee1', {}).get(ntee1) if ntee1 else None
    if b:
        data['cohort_context'] = {**b, 'level': 'broad', 'ntee_code': ntee1}


def _patch_v5_benchmarks(data: dict) -> None:
    """Back-fill zero benchmark values in precomputed files from the hardcoded table.

    Precomputed JSONs were generated before the benchmark table was populated, so
    many have p25=p50=p75=0.  We correct them at serve time rather than waiting for
    a full precompute rebuild.
    """
    v5 = data.get('v5_context')
    if not isinstance(v5, dict):
        return
    bench = v5.get('benchmarks', {})
    rm = bench.get('reserves_months', {})
    if rm.get('p75', 0) != 0:
        return  # already has real data

    arch_label = (v5.get('archetype') or {}).get('label', '')
    band_key   = (v5.get('band') or {}).get('key') or ''
    lbl = arch_label.lower()
    if 'donation' in lbl:
        arch_key = 'donation_funded'
    elif 'fee' in lbl or 'service' in lbl:
        arch_key = 'fee_for_service'
    elif 'endowment' in lbl:
        arch_key = 'endowment'
    else:
        return  # unknown archetype — leave as-is

    real = _V5_BENCHMARKS.get((arch_key, band_key))
    if not real:
        return

    rm.update({'p25': real['p25'], 'p50': real['p50'], 'p75': real['p75']})
    bench['healthy_rate_peer'] = real['hr']

    # Regenerate donor_explanation only when it still contains the stale "0 months" wording
    explanation = v5.get('donor_explanation', '')
    if 'about 0 months' in explanation or '0 months of operating costs' in explanation:
        reserves  = data.get('months_of_reserve')
        p50       = real['p50']
        band_lbl  = (v5.get('band') or {}).get('label', '')
        peer_count = (v5.get('peer_group') or {}).get('org_count', 0)
        health    = (v5.get('score') or {}).get('health_signal', '')
        if health == 'HEALTHY':
            health_desc = 'Above the typical level for similar organizations, suggesting solid financial stability.'
        elif health == 'STABLE':
            health_desc = 'Close to the typical level for similar organizations, showing steady financial management.'
        else:
            health_desc = 'Below the typical level for similar organizations. This organization may be in a growth phase or operating lean by design.'
        if reserves and p50:
            v5['donor_explanation'] = (
                f"This organization is a {arch_label} nonprofit with a budget in the {band_lbl} range. "
                f"Organizations like this one typically keep about {int(p50)} months of operating costs "
                f"in reserve. This one has {reserves:.1f} months. {health_desc} "
                f"This comparison is based on public IRS 990 data from {peer_count:,} similar organizations."
            )


def _fetch_s3_enrichment(ein: str) -> dict:
    """Fetch contact + programs enrichment data from S3 (Phase 2a).

    Returns dict with 'contact' and 'programs' keys, or empty dict if S3 unavailable.
    """
    enrichment = {}

    if not S3_AVAILABLE:
        return enrichment

    try:
        s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-2'))
        bucket = os.environ.get('DAANAA_ENRICHMENT_BUCKET', 'daanaa-nonprofit-data')

        # Fetch contact data
        try:
            response = s3.get_object(Bucket=bucket, Key=f'enrichment/contact/{ein}.json')
            enrichment['contact'] = json.loads(response['Body'].read())
        except:
            pass  # S3 NoSuchKey is expected for orgs without enrichment

        # Fetch programs data
        try:
            response = s3.get_object(Bucket=bucket, Key=f'enrichment/programs/{ein}.json')
            enrichment['programs'] = json.loads(response['Body'].read())
        except:
            pass

    except Exception as e:
        # Silent fail: S3 unavailable or credentials missing - just don't include enrichment
        pass

    return enrichment


def load_org_detail(ein: str) -> dict | None:
    """Load org detail: precomputed file first, then search.db fallback."""
    ein_prefix = ein[:3]
    org_file = DATA_DIR / 'orgs' / ein_prefix / f"{ein}.json.gz"
    data = load_json_gz(org_file)
    if data:
        if 'data_badges' not in data or data['data_badges'] is None:
            data['data_badges'] = {'mission': data.get('mission_source')}
        elif isinstance(data.get('data_badges'), dict) and 'mission' not in data['data_badges']:
            data['data_badges']['mission'] = data.get('mission_source')
        _patch_v5_benchmarks(data)
        _attach_cohort_context(data)
        return data

    # Fallback: serve from search.db registry_enriched table (IRS_BMF / bmf_stub orgs)
    conn = get_search_db()
    if not conn:
        return None
    try:
        row = conn.execute("SELECT * FROM registry_enriched WHERE EIN = ?", (ein,)).fetchone()
        return _row_to_org(row) if row else None
    except Exception:
        return None
    finally:
        conn.close()


def merge_claims(org_data: dict, ein: str) -> dict:
    """DEAD CODE (retained for historical clarity, P9).

    This function read org-claimed data (mission, website, donate URL) from
    CLAIMS_DIR (local JSON files), which was an early design pattern for live
    profile edits. However, no code in the repository ever WRITES to CLAIMS_DIR.

    Claimed data is now stored in the `org_claims` table in the local registry DB
    (daanaa_api.py), which is read at merge time and used to override public fields.
    The droplet API serves precompute static JSON files (no live registry reads).

    Org profile edits → org_claims row in home DB → included in next nightly
    precompute build → static JSON deployed to droplet. This is a multi-hour
    latency path by design (sandboxed write to precompute, not live writes to the
    serving layer). See DECISIONS.md 2026-07-18 for the board decision to defer
    live-push infrastructure pending proper sandboxing.

    This function is a no-op; it always returns org_data unchanged. It is not
    removed to preserve git history and prevent confusion if someone searches
    for this pattern later.
    """
    # Dead code: CLAIMS_DIR is never written to. This function always no-ops.
    return org_data


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok' if DATA_DIR.exists() else 'degraded',
        'version': 'precompute-v2',
        'data_dir': str(DATA_DIR),
        'data_exists': DATA_DIR.exists(),
    })


@app.route('/api/stats')
def stats():
    data = load_json_gz(DATA_DIR / 'content/homepage.json.gz')
    if data:
        return jsonify(data.get('stats', {}))
    return jsonify({'total_organizations': 0}), 503


@app.route('/api/organizations')
def get_organizations():
    ntee     = request.args.get('ntee', '').strip().upper()
    sub      = request.args.get('sub', '').strip().upper()
    state    = request.args.get('state', '').strip().upper()
    q        = request.args.get('q', '').strip()
    sort     = request.args.get('sort', '').strip()
    shuffle_seed = request.args.get('seed', '').strip()[:50]  # Session seed for seeded random shuffle
    try:
        page     = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', PER_PAGE_DEFAULT))))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid page or per_page parameter'}), 400
    hidden_gem         = request.args.get('hidden_gem', '').strip() == '1'
    needs_funding      = request.args.get('needs_funding', '').strip() == '1'
    has_website        = request.args.get('has_website', '').strip() == '1'
    has_revenue        = request.args.get('has_revenue', '').strip() == '1'
    open_to_volunteers = request.args.get('open_to_volunteers', '').strip() == '1'
    order = request.args.get('order', '').strip()
    tier  = request.args.get('tier', '').strip()
    min_rev = request.args.get('min_revenue', type=float)
    max_rev = request.args.get('max_revenue', type=float)
    verified_revenue_only = request.args.get('verified_revenue', '').strip() == '1'
    # Comma-separated multi-select, same contract as the home daanaa_api:
    # ntee=R,I (category letters) and sub=E21,A82 (NTEECC prefixes), OR-combined.
    ntee_list = [x.strip()[:1] for x in ntee.split(',') if x.strip()][:26]
    sub_list  = [x.strip()[:4] for x in sub.split(',') if x.strip()][:40]

    # ── Proximity: resolve near/radius → zip set ──────────────────────────
    nearby_zips: set = set()
    nearby_meta: dict | None = None
    near_raw = request.args.get('near', '').strip()
    try:
        radius_mi = int(request.args.get('radius_mi') or request.args.get('radius') or 0)
    except (ValueError, TypeError):
        radius_mi = 0
    if near_raw and radius_mi > 0:
        _conn = get_search_db()
        if _conn:
            try:
                loc = _resolve_location(_conn, near_raw)
                if loc:
                    lat, lon, city, state_resolved = loc
                    nearby_zips = _zips_within_radius(_conn, lat, lon, radius_mi)
                    nearby_meta = {"city": city, "state": state_resolved, "radius_mi": radius_mi}
            finally:
                _conn.close()

    # ── Text search: route to FTS ──────────────────────────────────────────
    if q and len(q) >= 2:
        return _fts_directory(q, ntee_list, sub_list, min_rev, max_rev,
                              state, sort, page, per_page,
                              hidden_gem, needs_funding, has_website, has_revenue, shuffle_seed, order, tier,
                              open_to_volunteers=open_to_volunteers,
                              nearby_zips=nearby_zips, nearby_meta=nearby_meta)

    # ── Hidden gems: static files (no other signals) ──────────────────────────
    if (hidden_gem and not q and not ntee and not sub and not state and
        not needs_funding and not has_website and not open_to_volunteers and not bool(tier) and
        not nearby_zips and min_rev is None and max_rev is None):
        gems_file = DATA_DIR / 'browse' / 'hidden_gems' / f"ALL_{page}.json.gz"
        data = load_json_gz(gems_file)
        if data:
            return jsonify(data)
        # Fall through to DB query if file not found

    # ── Filter browse: DB query when flags, revenue, or multi-select used ───
    any_filter = hidden_gem or needs_funding or has_website or open_to_volunteers or bool(tier) or bool(nearby_zips)
    multi_select = len(ntee_list) > 1 or len(sub_list) > 1 or (ntee_list and sub_list)
    # Explicit non-name sort must hit the DB — the precompute files below are
    # baked in name order and ignore sort/order (bug found 2026-07-17: the
    # directory sort dropdown was a no-op on plain browse).
    explicit_sort = (sort and sort != 'organization_name') or order.lower() == 'desc'
    if any_filter or multi_select or explicit_sort or min_rev is not None or max_rev is not None:
        return _db_filter_browse(ntee_list, sub_list, min_rev, max_rev,
                                 state, sort, page, per_page,
                                 hidden_gem, needs_funding, has_website, has_revenue, shuffle_seed, order, tier,
                                 open_to_volunteers=open_to_volunteers,
                                 nearby_zips=nearby_zips, nearby_meta=nearby_meta,
                                 verified_revenue_only=verified_revenue_only)

    # ── Browse: precomputed files ──────────────────────────────────────────
    category = sub if sub else ntee
    ntee1        = None
    nteecc_filter = None
    if category:
        if len(category) == 1:
            ntee1 = category
        elif len(category) >= 2 and category[0].isalpha():
            ntee1 = category[0]
            nteecc_filter = category

    if not ntee1:
        return _multi_category_page(state, page, per_page)

    if not state:
        all_file_1 = DATA_DIR / 'browse' / ntee1 / "ALL_1.json.gz"
        if all_file_1.exists():
            if nteecc_filter:
                return _filtered_orgs(ntee1, 'ALL', nteecc_filter, page, per_page)
            all_file = DATA_DIR / 'browse' / ntee1 / f"ALL_{page}.json.gz"
            data = load_json_gz(all_file)
            if data:
                return jsonify(data)
        return _multi_state_page(ntee1, nteecc_filter, page, per_page)

    if nteecc_filter:
        return _filtered_orgs(ntee1, state, nteecc_filter, page, per_page)

    browse_file = DATA_DIR / 'browse' / ntee1 / f"{state}_{page}.json.gz"
    data = load_json_gz(browse_file)
    if data:
        return jsonify(data)

    return jsonify({'organizations': [], 'total': 0, 'pages': 0,
                    'page': page, 'per_page': per_page})


def _db_filter_browse(ntee_list, sub_list, min_rev, max_rev,
                      state, sort, page, per_page,
                      hidden_gem, needs_funding, has_website, has_revenue=False, shuffle_seed='', order='', tier='',
                      open_to_volunteers=False, nearby_zips=None, nearby_meta=None, verified_revenue_only=False):
    """Query orgs table directly with filter conditions but no FTS match."""
    conn = get_search_db()
    if not conn:
        return jsonify({'organizations': [], 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page})
    try:
        conditions, params = _cat_rev_conditions(ntee_list, sub_list, min_rev, max_rev, verified_revenue_only=verified_revenue_only)
        conditions.append(_public_filter(conn))
        if state:
            conditions.append("STATE = ?")
            params.append(state)
        if hidden_gem:
            conditions.append("is_hidden_gem = 1")
        if needs_funding:
            conditions.append("months_of_reserve IS NOT NULL AND months_of_reserve < 6")
        if has_website:
            conditions.append("website IS NOT NULL AND website != '' AND website_status = 'ok'")
        if has_revenue:
            conditions.append("total_revenue IS NOT NULL AND total_revenue > 0")
        if open_to_volunteers and _search_db_has_org_claims(conn):
            conditions.append(
                "EIN IN (SELECT ein FROM org_claims WHERE volunteer_contact_email IS NOT NULL AND volunteer_contact_email != '')"
            )
        if nearby_zips:
            placeholders = ','.join('?' * len(nearby_zips))
            conditions.append(f"SUBSTR(zipcode, 1, 5) IN ({placeholders})")
            params.extend(nearby_zips)
        tier_cond, tier_params = _tier_condition(tier)
        if tier_cond:
            conditions.append(tier_cond)
            params.extend(tier_params)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        # COALESCE instead of NULLS LAST: same ordering, but the non-indexable
        # expression stops SQLite walking the score index and probing the
        # filter row-by-row (6s → 0.2s on OR'd category filters, 2026-06-09).
        order_by = _order_clause(sort, order)

        total = conn.execute(f"SELECT COUNT(*) FROM registry_enriched {where}", params).fetchone()[0]
        offset = (page - 1) * per_page

        # When shuffling with seed, fetch all results and shuffle in-memory
        # Otherwise use LIMIT/OFFSET for pagination
        if sort == 'random' and shuffle_seed:
            query_sql = f"SELECT * FROM registry_enriched {where}"
            if order_by:  # This should be empty for random sort, but just in case
                query_sql += f" ORDER BY {order_by}"
            rows = conn.execute(query_sql, params).fetchall()
        else:
            query_sql = f"SELECT * FROM registry_enriched {where}"
            if order_by:
                query_sql += f" ORDER BY {order_by}"
            query_sql += " LIMIT ? OFFSET ?"
            rows = conn.execute(query_sql, params + [per_page, offset]).fetchall()

        # If seeded shuffle, shuffle rows and then paginate
        if sort == 'random' and shuffle_seed:
            import random
            rng = random.Random(shuffle_seed)
            rows_list = list(rows)
            rng.shuffle(rows_list)
            rows = rows_list[offset:offset + per_page]

        orgs = [_row_to_org(r) for r in rows]
        pages = max(1, (total + per_page - 1) // per_page)
        resp = {'organizations': orgs, 'total': total,
                'page': page, 'per_page': per_page, 'pages': pages}
        if nearby_meta:
            resp['nearby'] = nearby_meta
        return jsonify(resp)
    except Exception as e:
        print(f"DB filter browse error: {e}")
        return jsonify({'organizations': [], 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page})
    finally:
        conn.close()


def _fts_directory(q, ntee_list, sub_list, min_rev, max_rev,
                   state, sort, page, per_page,
                   hidden_gem, needs_funding, has_website, has_revenue=False, shuffle_seed='', order='', tier='',
                   open_to_volunteers=False, nearby_zips=None, nearby_meta=None):
    """FTS search against search.db orgs table, returns full org objects."""
    conn = get_search_db()
    if not conn:
        return jsonify({'organizations': [], 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page, 'search_type': 'fts'})
    try:
        conditions, params, _detected_zip = _fts_where(q, state, conn)
        conditions.append(_public_filter(conn, alias='o.'))
        cat_conds, cat_params = _cat_rev_conditions(
            ntee_list, sub_list, min_rev, max_rev, alias='o.')
        conditions.extend(cat_conds)
        params.extend(cat_params)

        if hidden_gem:
            conditions.append("o.is_hidden_gem = 1")
        if needs_funding:
            conditions.append("o.months_of_reserve IS NOT NULL AND o.months_of_reserve < 6")
        if has_website:
            conditions.append("o.website IS NOT NULL AND o.website != '' AND o.website_status = 'ok'")
        if has_revenue:
            conditions.append("o.total_revenue IS NOT NULL AND o.total_revenue > 0")
        if open_to_volunteers and _search_db_has_org_claims(conn):
            conditions.append(
                "o.EIN IN (SELECT ein FROM org_claims WHERE volunteer_contact_email IS NOT NULL AND volunteer_contact_email != '')"
            )
        if nearby_zips:
            placeholders = ','.join('?' * len(nearby_zips))
            conditions.append(f"SUBSTR(o.zipcode, 1, 5) IN ({placeholders})")
            params.extend(nearby_zips)
        tier_cond, tier_params = _tier_condition(tier, alias='o.')
        if tier_cond:
            conditions.append(tier_cond)
            params.extend(tier_params)

        order = _order_clause(sort, order, alias='o.')

        # Bounded-candidate plan (2026-07-18, same fix as fused_search()
        # 2026-07-16): the old query was an uncapped COUNT(*) over a join of
        # org_fts to registry_enriched (1.87M rows). A common word like
        # "health" matches 170K+ rows, and counting+joining all of them took
        # 15-21s on the droplet — reproduced live, single isolated request,
        # not a concurrency artifact. Same technique: bm25-rank inside FTS5,
        # take a bounded candidate set, only join/filter/sort/count those.
        # conditions[0] is the join clause, conditions[1] the MATCH
        # (param 0); everything after is o.*-only filters, safe to reuse
        # verbatim inside the CTE's WHERE.
        #
        # CROSS JOIN, not a plain/inner JOIN: verified via EXPLAIN QUERY PLAN
        # on the live droplet that a plain JOIN still let SQLite's optimizer
        # flip the join order — it drove from registry_enriched's public-
        # filter index (a near-full-table ~1.85M-row scan, bloom-filtering
        # each row against the small CTE) instead of the reverse, leaving
        # this at 6-8s even with the cap. SQLite does not reorder an explicit
        # CROSS JOIN, which forces it to scan the small CTE first and do a
        # cheap primary-key SEARCH into registry_enriched per candidate —
        # confirmed 0.6s on the droplet with this change.
        fts_q = params[0]
        o_conditions = conditions[2:]
        o_params = params[1:]
        cand_cap = 20000
        o_where = (' AND ' + ' AND '.join(o_conditions)) if o_conditions else ''

        total = conn.execute(
            f"WITH c AS (SELECT ein FROM org_fts WHERE org_fts MATCH ? "
            f"ORDER BY rank LIMIT {cand_cap}) "
            f"SELECT COUNT(*) FROM c CROSS JOIN registry_enriched o ON o.EIN = c.ein "
            f"WHERE 1=1{o_where}",
            [fts_q] + o_params
        ).fetchone()[0]

        offset = (page - 1) * per_page

        # When shuffling with seed, fetch all results and shuffle in-memory
        # Otherwise use LIMIT/OFFSET for pagination
        if sort == 'random' and shuffle_seed:
            rows_sql = (
                f"WITH c AS (SELECT ein FROM org_fts WHERE org_fts MATCH ? "
                f"ORDER BY rank LIMIT {cand_cap}) "
                f"SELECT o.* FROM c CROSS JOIN registry_enriched o ON o.EIN = c.ein "
                f"WHERE 1=1{o_where}"
            )
            rows = conn.execute(rows_sql, [fts_q] + o_params).fetchall()
            # Shuffle in-memory after fetch
            import random
            rng = random.Random(shuffle_seed)
            rows_list = list(rows)
            rng.shuffle(rows_list)
            rows = rows_list[offset:offset + per_page]
        else:
            rows_sql = (
                f"WITH c AS (SELECT ein FROM org_fts WHERE org_fts MATCH ? "
                f"ORDER BY rank LIMIT {cand_cap}) "
                f"SELECT o.* FROM c CROSS JOIN registry_enriched o ON o.EIN = c.ein "
                f"WHERE 1=1{o_where} "
                f"ORDER BY {order} "
                f"LIMIT ? OFFSET ?"
            )
            rows = conn.execute(rows_sql, [fts_q] + o_params + [per_page, offset]).fetchall()

        orgs = [_row_to_org(r) for r in rows]
        pages = max(1, (total + per_page - 1) // per_page)
        resp = {'organizations': orgs, 'total': total,
                'page': page, 'per_page': per_page,
                'pages': pages, 'search_type': 'fts'}
        if nearby_meta:
            resp['nearby'] = nearby_meta
        return jsonify(resp)
    except Exception as e:
        print(f"FTS directory error: {e}")
        return jsonify({'organizations': [], 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page, 'search_type': 'error'})
    finally:
        conn.close()


def _load_state_page1(ntee1, state):
    f = DATA_DIR / 'browse' / ntee1 / f"{state}_1.json.gz"
    data = load_json_gz(f)
    return data['organizations'] if data and data.get('organizations') else []


def _merge_orgs(orgs_lists, per_page, page):
    seen, merged = set(), []
    for orgs in orgs_lists:
        for o in orgs:
            ein = o.get('EIN')
            if ein and ein not in seen:
                seen.add(ein)
                merged.append(o)
    # Neutral name order (2026-07-04): merged browse pages must not imply a
    # score ranking; merit_score sort is explicit opt-in only.
    merged.sort(key=lambda o: (o.get('organization_name') or '').lower())
    total = len(merged)
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    return merged[start:start + per_page], total, pages


def _multi_state_page(ntee1, nteecc_filter, page, per_page):
    cache_key = f"ms:{ntee1}:{nteecc_filter}"
    if cache_key not in _multi_cache:
        _multi_cache[cache_key] = [_load_state_page1(ntee1, s) for s in _TOP_STATES]
    orgs_lists = _multi_cache[cache_key]
    if nteecc_filter:
        orgs_lists = [[o for o in lst if (o.get('NTEECC') or '').upper().startswith(nteecc_filter)]
                      for lst in orgs_lists]
    orgs_page, total, pages = _merge_orgs(orgs_lists, per_page, page)
    return jsonify({'organizations': orgs_page, 'total': total,
                    'page': page, 'per_page': per_page, 'pages': pages})


_real_total_cache: dict = {}

# Public-eligibility filter: browse/filter surfaces must only show active,
# tax-deductible 501(c)(3) orgs (public number 1,729,314), never revoked ones.
# The full registry stays in search.db for org-detail fallback. Fails open to
# no filter when an older search.db artifact lacks the columns.
_PUBLIC_FILTER = ("subsection = '3' AND deductibility = '1' "
                  "AND COALESCE(irs_revoked, 0) != 1 "
                  "AND COALESCE(org_status, '') != 'revoked'")
_public_filter_ok: bool | None = None

def _public_filter(conn, alias: str = '') -> str:
    global _public_filter_ok
    if _public_filter_ok is None:
        try:
            conn.execute(f"SELECT 1 FROM registry_enriched WHERE {_PUBLIC_FILTER} LIMIT 1")
            _public_filter_ok = True
        except Exception:
            _public_filter_ok = False
    if not _public_filter_ok:
        return "1=1"
    if alias:
        return (f"{alias}subsection = '3' AND {alias}deductibility = '1' "
                f"AND COALESCE({alias}irs_revoked, 0) != 1 "
                f"AND COALESCE({alias}org_status, '') != 'revoked'")
    return _PUBLIC_FILTER

def _get_real_total(state: str = '') -> int:
    """Public org count from search.db (active deductible only), cached per state."""
    key = state or '_all'
    if key in _real_total_cache:
        return _real_total_cache[key]
    conn = get_search_db()
    if not conn:
        return 0
    try:
        pf = _public_filter(conn)
        if state:
            n = conn.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {pf} AND STATE = ?", (state,)).fetchone()[0]
        else:
            n = conn.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {pf}").fetchone()[0]
        _real_total_cache[key] = n
        return n
    except Exception:
        return 0
    finally:
        conn.close()


def _multi_category_page(state, page, per_page):
    cache_key = f"mc:{state}"
    if cache_key not in _multi_cache:
        orgs_lists = []
        for ntee1 in _ALL_NTEE1:
            if state:
                orgs = _load_state_page1(ntee1, state)
            else:
                all_f = DATA_DIR / 'browse' / ntee1 / "ALL_1.json.gz"
                data  = load_json_gz(all_f)
                if data and data.get('organizations'):
                    orgs = data['organizations']
                else:
                    orgs = []
                    for s in _TOP_STATES[:5]:
                        orgs.extend(_load_state_page1(ntee1, s))
            orgs_lists.append(orgs)
        _multi_cache[cache_key] = orgs_lists
    orgs_page, _sample_total, _sample_pages = _merge_orgs(_multi_cache[cache_key], per_page, page)
    real_total = _get_real_total(state)
    real_pages = max(1, (real_total + per_page - 1) // per_page)
    return jsonify({'organizations': orgs_page, 'total': real_total,
                    'page': page, 'per_page': per_page, 'pages': real_pages})


def _filtered_orgs(ntee1, state, nteecc_filter, page, per_page):
    matched = []
    for p in range(1, 500):
        data = load_json_gz(DATA_DIR / 'browse' / ntee1 / f"{state}_{p}.json.gz")
        if not data or not data.get('organizations'):
            break
        for org in data['organizations']:
            if (org.get('NTEECC') or '').upper().startswith(nteecc_filter):
                matched.append(org)
        if len(matched) >= per_page * 20:
            break
    total = len(matched)
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    return jsonify({'organizations': matched[start:start + per_page],
                    'total': total, 'page': page, 'per_page': per_page, 'pages': pages})


_EIN_RE = re.compile(r'^\d{9}$')

@app.route('/api/organizations/<ein>')
def get_organization(ein):
    ein = ein.strip().upper()
    if not _EIN_RE.match(ein):
        return jsonify({'error': 'invalid ein'}), 400
    org_data = load_org_detail(ein)
    if not org_data:
        return jsonify({'error': 'org not found'}), 404
    # Note: merge_claims is a no-op (DEAD CODE); see function docstring.
    # Claimed org data (mission, website, donate URL) comes from org_claims in
    # the home DB and is baked into precompute at deploy time.
    org_data = merge_claims(org_data, ein)

    # Optional: load enrichment data from S3 (Phase 2a)
    if request.args.get('include_enrichment') == '1':
        enrichment = _fetch_s3_enrichment(ein)
        if enrichment:
            org_data.update(enrichment)

    return jsonify(org_data)


@app.route('/api/organizations/<ein>/similar')
def get_similar_orgs(ein):
    ein = ein.strip().upper()
    try:
        limit = min(12, int(request.args.get('limit', 9)))
    except (ValueError, TypeError):
        limit = 9
    org_data = load_org_detail(ein)
    if not org_data:
        return jsonify({'results': [], 'mode': 'precomputed', 'diamonds_only': False})
    similar = org_data.get('similar_organizations', [])[:limit]
    return jsonify({'results': similar, 'mode': 'precomputed', 'diamonds_only': False})


@app.route('/api/organizations/<ein>/financials')
def get_financials(ein):
    ein = ein.strip().upper()
    org_data = load_org_detail(ein)
    if not org_data:
        return jsonify({'ein': ein, 'financials': [], 'total': 0})
    # Multi-year history baked into precomputed org JSON by precompute_orgs.py
    financials = org_data.get('financials') or []
    # Fallback: synthesise a single-year record for orgs not yet re-precomputed
    if not financials and org_data.get('latest_tax_year'):
        financials = [{
            'tax_prd_yr':     org_data.get('latest_tax_year'),
            'totrevenue':     org_data.get('total_revenue'),
            'totfuncexpns':   org_data.get('total_expenses'),
            'totnetassetend': org_data.get('net_assets'),
            'totassetsend':   None,
            'totliabend':     org_data.get('total_liabilities'),
            'totcntrbgfts':   None,
            'totprgmrevnue':  None,
            'compnsatncurrofcr': None,
            'pdf_url':        None,
        }]
    return jsonify({'ein': ein, 'financials': financials, 'total': len(financials)})


@app.route('/api/organizations/<ein>/score-history')
def get_score_history(ein):
    return jsonify({'ein': ein.strip().upper(), 'history': [], 'total': 0})


@app.route('/api/search')
def search():
    """Quick-search endpoint (header search bar)."""
    query = request.args.get('q', '').strip()
    try:
        limit = min(50, int(request.args.get('limit', 25)))
    except (ValueError, TypeError):
        limit = 25
    ntee  = request.args.get('ntee', '').strip().upper()
    state = request.args.get('state', '').strip().upper()

    if not query or len(query) < 2:
        return jsonify({'results': [], 'query': query, 'total': 0})

    conn = get_search_db()
    if not conn:
        return jsonify({'results': [], 'query': query, 'total': 0, 'mode': 'unavailable'})

    try:
        conditions, params, _zip = _fts_where(query, state, conn=conn)
        cat_conds, cat_params = _cat_rev_conditions(
            [x.strip()[:1] for x in ntee.split(',') if x.strip()], [], None, None, alias='o.')
        conditions.extend(cat_conds)
        params.extend(cat_params)
        # ORDER BY exact typed name first, then s.rank (bm25) — 2026-07-16
        # searchability pass + 2026-07-19 exact pin. Costs ~ms at this LIMIT.
        sql = (f"SELECT o.EIN, o.organization_name, o.NTEE1, o.NTEECC, o.CITY, o.STATE, o.mission, o.merit_score "
               f"FROM org_fts s, registry_enriched o WHERE {' AND '.join(conditions)} "
               f"ORDER BY (UPPER(o.organization_name) = ?) DESC, s.rank LIMIT ?")
        rows = conn.execute(sql, params + [query.upper(), limit]).fetchall()
        results = [dict(r) for r in rows]
        # Finite-corpus pin: if the typed text IS an org's name (as a phrase in
        # the name column), that org must appear even when bm25 buries it among
        # common-token matches ("N A B S", "BEST SCHOOL" class, 2026-07-19).
        name_toks = _FTS5_STRIP.sub(' ', _FTS5_APOS.sub('', query)).split()[:12]
        if name_toks:
            phrase_params = list(params)
            phrase_params[0] = f'org_name : "{" ".join(name_toks)}"'
            try:
                pin_rows = conn.execute(sql, phrase_params + [query.upper(), 10]).fetchall()
                if pin_rows:
                    pinned = [dict(r) for r in pin_rows]
                    pin_eins = {p['EIN'] for p in pinned}
                    results = pinned + [r for r in results if r['EIN'] not in pin_eins]
                    results = results[:limit]
            except Exception:
                pass  # pin is best-effort; base results already stand
        # Zero-result rescue: corpus-vocabulary typo correction (labeled).
        corrected_query = None
        if not results:
            _cq = _typo_correct_query(query)
            if _cq:
                _params2 = list(params)
                _params2[0] = _sanitize_fts_query(_cq)
                try:
                    rows2 = conn.execute(sql, _params2 + [_cq.upper(), limit]).fetchall()
                    if rows2:
                        results = [dict(r) for r in rows2]
                        corrected_query = _cq
                except Exception:
                    pass
        payload = {'results': results, 'query': query,
                   'total': len(results), 'mode': 'fts'}
        if corrected_query:
            payload['corrected_query'] = corrected_query
        return jsonify(payload)
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'results': [], 'query': query, 'total': 0, 'mode': 'error'})
    finally:
        conn.close()


@app.route('/api/fused-search')
def fused_search():
    """Alias: frontend calls /api/fused-search for the main search bar."""
    q      = request.args.get('q', '').strip()
    ntee   = request.args.get('ntee', '').strip().upper()
    state  = request.args.get('state', '').strip().upper()
    try:
        limit = min(50, int(request.args.get('limit', 20)))
        page  = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid limit or page parameter'}), 400

    per_page = limit
    if not q or len(q) < 2:
        return jsonify({'organizations': [], 'query': q, 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page, 'search_type': 'empty'})

    conn = get_search_db()
    if not conn:
        return jsonify({'organizations': [], 'query': q, 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page, 'search_type': 'unavailable'})

    try:
        conditions, params, _zip = _fts_where(q, state, conn=conn)
        ntee_list = [x.strip()[:1] for x in ntee.split(',') if x.strip()]
        cat_conds, cat_params = _cat_rev_conditions(ntee_list, [], None, None, alias='o.')
        conditions.extend(cat_conds)
        params.extend(cat_params)

        # ── Speed pass 2026-07-16 ─────────────────────────────────────────
        # The old plan sorted EVERY FTS match by merit_score (broad prefix
        # terms match 200K+ rows) and ran an uncapped COUNT over the join:
        # 16-20s per search on the droplet. New plan:
        #   1. bm25-rank inside FTS5 and take a bounded candidate set
        #   2. merit-sort only the candidates (relevance-bounded, <400ms)
        #   3. cap COUNT at 10001 (the UI never pages past that anyway)
        # conditions[0] is the join clause, conditions[1] the MATCH (param 0);
        # everything after is o.* filters usable inside the CTE plan.
        fts_q = params[0]
        o_conditions = conditions[2:]
        o_params = params[1:]
        # State filter also goes INTO the MATCH (state is an indexed FTS
        # column) so the bm25 candidates are already state-correct.
        resolved_state = state or ''
        if not resolved_state:
            for c_i, cond in enumerate(o_conditions):
                if cond == "o.STATE = ?":
                    resolved_state = o_params[c_i]
                    break
        # Sanitize before interpolating into the MATCH string (user input):
        # only a bare 2-letter state token may enter FTS syntax.
        if resolved_state and not re.match(r'^[A-Za-z]{2}$', str(resolved_state)):
            resolved_state = ''
        # state code is double-quoted: "OR" (Oregon) must stay a literal token,
        # not the boolean operator (same class of bug as the hyphen crash).
        fts_match = f'({fts_q}) AND state:"{resolved_state.upper()}"' if resolved_state else fts_q
        # Finite-corpus name-phrase branch: if the typed text IS an org's name,
        # look it up directly in the name column — orgs with generic or spaced-
        # initialism names ("BEST SCHOOL", "N A B S") otherwise rank below the
        # candidate cap among common-token matches (2026-07-19). Noise words
        # stay: "best" is part of the name "BEST SCHOOL".
        _pin_toks = _FTS5_STRIP.sub(' ', _FTS5_APOS.sub('', q)).split()[:12]
        phrase_q = f'org_name : "{" ".join(_pin_toks)}"' if _pin_toks else '""'
        phrase_match = f'({phrase_q}) AND state:"{resolved_state.upper()}"' if resolved_state else phrase_q
        # NTEE category is not an exact-token FTS column — widen the candidate
        # pool when a category filter must be applied after ranking.
        cand_cap = 20000 if ntee_list else 3000

        o_where = (' AND ' + ' AND '.join(o_conditions)) if o_conditions else ''
        # Candidate CTE = name-phrase pins (rel -1e9, always kept) UNION the
        # bm25-ranked pool; ORDER BY rel LIMIT inside keeps pins ahead of the
        # cap, GROUP BY dedupes orgs present in both branches.
        cte = (f"WITH c AS (SELECT ein, MIN(rel) AS rel FROM ("
               f"SELECT ein, -1e9 AS rel FROM org_fts WHERE org_fts MATCH ? "
               f"UNION ALL "
               f"SELECT ein, rank AS rel FROM org_fts WHERE org_fts MATCH ? "
               f"ORDER BY rel LIMIT {cand_cap}"
               f") GROUP BY ein) ")
        # total = matches reachable through pagination (counted INSIDE the
        # bounded candidate set — never an unbounded join). A pure-FTS probe
        # (no join, capped) sets total_capped so the UI can render "N+".
        #
        # CROSS JOIN, not a plain JOIN (2026-07-18): confirmed via EXPLAIN
        # QUERY PLAN on the live droplet that an ntee_list filter (o.NTEE1 = ?,
        # indexed by idx_orgs_ntee1_rev) triggers the same join-order flip
        # found in _fts_directory() — SQLite drives from the indexed o.
        # column and bloom-filters against the small CTE, instead of the
        # reverse. CROSS JOIN pins the join order SQLite must not reorder.
        total = conn.execute(
            cte +
            f"SELECT COUNT(*) FROM c CROSS JOIN registry_enriched o ON o.EIN = c.ein "
            f"WHERE 1=1{o_where}",
            [phrase_match, fts_match] + o_params
        ).fetchone()[0]
        # Zero-result rescue: corpus-vocabulary typo correction, labeled via
        # corrected_query in the response. Happy path never reaches this.
        corrected_query = None
        if total == 0:
            _cq = _typo_correct_query(q)
            if _cq:
                _fts_q2 = _sanitize_fts_query(_cq)
                _toks2 = _FTS5_STRIP.sub(' ', _FTS5_APOS.sub('', _cq)).split()[:12]
                _phr2 = f'org_name : "{" ".join(_toks2)}"' if _toks2 else '""'
                if resolved_state:
                    _fts_q2 = f'({_fts_q2}) AND state:"{resolved_state.upper()}"'
                    _phr2 = f'({_phr2}) AND state:"{resolved_state.upper()}"'
                _total2 = conn.execute(
                    cte +
                    f"SELECT COUNT(*) FROM c CROSS JOIN registry_enriched o ON o.EIN = c.ein "
                    f"WHERE 1=1{o_where}",
                    [_phr2, _fts_q2] + o_params
                ).fetchone()[0]
                if _total2 > 0:
                    total, fts_match, phrase_match = _total2, _fts_q2, _phr2
                    corrected_query = _cq
                    q = _cq   # exact-name pin should reference the corrected text
        fts_probe = conn.execute(
            f"SELECT COUNT(*) FROM (SELECT 1 FROM org_fts WHERE org_fts MATCH ? LIMIT {cand_cap + 1})",
            [fts_match]
        ).fetchone()[0]
        total_capped = fts_probe > cand_cap

        offset = (page - 1) * per_page
        # Exact typed-name match pins first, then phrase pins (c.rel), then
        # the existing order — a donor typing a full org name sees that org
        # above any candidate.
        sql = (cte +
               f"SELECT o.* FROM c CROSS JOIN registry_enriched o ON o.EIN = c.ein "
               f"WHERE 1=1{o_where} "
               f"ORDER BY (UPPER(o.organization_name) = ?) DESC, "
               f"(c.rel <= -1e9) DESC, "
               f"COALESCE(o.merit_score, -1) DESC "
               f"LIMIT ? OFFSET ?")
        rows = conn.execute(sql, [phrase_match, fts_match] + o_params + [q.upper(), per_page, offset]).fetchall()
        orgs = [_row_to_org(r) for r in rows]
        pages = max(1, (total + per_page - 1) // per_page)
        payload = {'organizations': orgs, 'query': q,
                   'total': total, 'total_capped': total_capped, 'pages': pages,
                   'page': page, 'per_page': per_page, 'search_type': 'fts'}
        if corrected_query:
            payload['corrected_query'] = corrected_query
        return jsonify(payload)
    except Exception as e:
        print(f"Fused search error: {e}")
        return jsonify({'organizations': [], 'query': q, 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page, 'search_type': 'error'})
    finally:
        conn.close()


@app.route('/api/sector-health')
def sector_health():
    data = load_json_gz(DATA_DIR / 'content/sector_health.json.gz')
    return jsonify(data if data else {'sectors': []})


@app.route('/api/ntee-categories')
def ntee_categories():
    data = load_json_gz(DATA_DIR / 'content/homepage.json.gz')
    if data:
        return jsonify({'categories': data.get('stats', {}).get('categories', [])})
    return jsonify({'categories': []})


@app.route('/api/how-it-works')
def how_it_works():
    return jsonify(load_json_gz(DATA_DIR / 'content/how_it_works.json.gz') or {})


@app.route('/api/methodology')
def methodology():
    return jsonify(load_json_gz(DATA_DIR / 'content/methodology.json.gz') or {})


@app.route('/api/guides')
def guides():
    return jsonify(load_json_gz(DATA_DIR / 'content/guides.json.gz') or {'articles': []})


# ── Claim flow proxy ─────────────────────────────────────────────────────────
# This API is read-only by design (precompute files, no registry DB). The
# claim endpoints need the writable DB and mail sender on the home server, so
# /api/claim/* is forwarded through a reverse SSH tunnel the home box opens to
# 127.0.0.1:5001 here (unit: daanaa-claim-tunnel on the home box). The SPA
# stays same-origin; if the tunnel is down only claiming degrades (503).

CLAIM_UPSTREAM = os.environ.get('CLAIM_UPSTREAM', 'http://127.0.0.1:5001')
CLAIM_MAX_BODY = 65536  # claim payloads are small JSON; cap before forwarding


@app.route('/api/claim/<path:subpath>', methods=['GET', 'POST', 'PATCH'])
@app.route('/api/partner/<path:subpath>', methods=['POST'])
def claim_proxy(subpath):
    if request.content_length and request.content_length > CLAIM_MAX_BODY:
        return jsonify({"error": "Request too large"}), 413
    url = f"{CLAIM_UPSTREAM}{request.path}"
    if request.query_string:
        url += '?' + request.query_string.decode()
    headers = {'Content-Type': request.headers.get('Content-Type', 'application/json')}
    # Forward Firebase Bearer token so authenticated claim endpoints work
    auth = request.headers.get('Authorization')
    if auth:
        headers['Authorization'] = auth
    # Forward the real visitor IP so the home API's rate limiter buckets per
    # visitor instead of lumping all claims into one droplet bucket.
    real_ip = request.headers.get('CF-Connecting-IP') or request.remote_addr
    if real_ip:
        headers['CF-Connecting-IP'] = real_ip
    body = request.get_data() if request.method in ('POST', 'PATCH') else None
    req = urllib.request.Request(url, data=body, headers=headers, method=request.method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(), resp.status, {'Content-Type': resp.headers.get('Content-Type', 'application/json')}
    except urllib.error.HTTPError as e:
        # Upstream 4xx/5xx are real answers (bad PIN, cooldown) — pass through
        return e.read(), e.code, {'Content-Type': e.headers.get('Content-Type', 'application/json')}
    except Exception:
        return jsonify({"error": "Claiming is briefly unavailable. Please try again in a few minutes."}), 503


# ── Wallet sync proxy ────────────────────────────────────────────────────────
# Wallet auth (Firebase JWT verification) and SQLite storage live on the home
# server. The same reverse SSH tunnel used by claims forwards to :5001 here.

WALLET_UPSTREAM = os.environ.get('WALLET_UPSTREAM', 'http://127.0.0.1:5001')
WALLET_MAX_BODY = 65536


@app.route('/api/wallet', methods=['GET', 'PUT', 'DELETE'])
def wallet_proxy():
    if request.content_length and request.content_length > WALLET_MAX_BODY:
        return jsonify({"error": "Request too large"}), 413
    url = f"{WALLET_UPSTREAM}/api/wallet"
    headers = {'Content-Type': request.headers.get('Content-Type', 'application/json')}
    auth = request.headers.get('Authorization')
    if auth:
        headers['Authorization'] = auth
    body = request.get_data() if request.method == 'PUT' else None
    req = urllib.request.Request(url, data=body, headers=headers, method=request.method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(), resp.status, {'Content-Type': resp.headers.get('Content-Type', 'application/json')}
    except urllib.error.HTTPError as e:
        return e.read(), e.code, {'Content-Type': e.headers.get('Content-Type', 'application/json')}
    except Exception:
        return jsonify({"error": "Wallet sync is briefly unavailable."}), 503


@app.route('/api/wallet/backup', methods=['POST'])
def wallet_backup_proxy():
    """Proxy wallet backup to home-server (DynamoDB write via :5001 tunnel)."""
    if request.content_length and request.content_length > WALLET_MAX_BODY:
        return jsonify({"error": "Request too large"}), 413
    url = f"{WALLET_UPSTREAM}/api/wallet/backup"
    headers = {'Content-Type': 'application/json'}
    auth = request.headers.get('Authorization')
    if auth:
        headers['Authorization'] = auth
    body = request.get_data()
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(), resp.status, {'Content-Type': 'application/json'}
    except urllib.error.HTTPError as e:
        return e.read(), e.code, {'Content-Type': 'application/json'}
    except Exception:
        return jsonify({"error": "Wallet backup is briefly unavailable."}), 503


@app.route('/api/wallet/report-bookmark', methods=['POST'])
def wallet_report_bookmark_proxy():
    """Proxy anonymous bookmark signal to home-server (task #15 donor
    interest metrics; anonymized aggregates only, P2)."""
    if request.content_length and request.content_length > WALLET_MAX_BODY:
        return jsonify({"error": "Request too large"}), 413
    url = f"{WALLET_UPSTREAM}/api/wallet/report-bookmark"
    headers = {'Content-Type': 'application/json'}
    body = request.get_data()
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(), resp.status, {'Content-Type': 'application/json'}
    except urllib.error.HTTPError as e:
        return e.read(), e.code, {'Content-Type': 'application/json'}
    except Exception:
        return jsonify({"error": "Bookmark reporting is briefly unavailable."}), 503


@app.route('/api/wallet/restore', methods=['GET'])
def wallet_restore_proxy():
    """Proxy wallet restore from home-server (DynamoDB read via :5001 tunnel)."""
    url = f"{WALLET_UPSTREAM}/api/wallet/restore"
    headers = {}
    auth = request.headers.get('Authorization')
    if auth:
        headers['Authorization'] = auth
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(), resp.status, {'Content-Type': 'application/json'}
    except urllib.error.HTTPError as e:
        return e.read(), e.code, {'Content-Type': 'application/json'}
    except Exception:
        return jsonify({"error": "Wallet restore is briefly unavailable."}), 503


# ── Live-backend proxy: volunteer events, guild, service area, zip, impact ───
# Routes that require the full SQLite backend are forwarded through the same
# reverse SSH tunnel on :5001 used by claims and wallet.

# LIVE_UPSTREAM routes expensive operations to home server (daanaa_api.py).
# On droplet: use home server hostname or bastion IP.
# In dev: use localhost:5000.
# Environment: LIVE_UPSTREAM or CLAIM_UPSTREAM (for backwards compat).
LIVE_UPSTREAM = os.environ.get('LIVE_UPSTREAM') or os.environ.get('CLAIM_UPSTREAM', 'http://127.0.0.1:5001')


def _live_proxy(path: str):
    """Proxy expensive operations to home-server backend (daanaa_api.py).

    Routes: volunteer workflow, profile contexts, admin analytics, email.
    Timeout: 20s. Preserves auth headers (Authorization, X-Admin-Key).
    """
    url = f"{LIVE_UPSTREAM}{path}"
    if request.query_string:
        url += '?' + request.query_string.decode('utf-8', errors='replace')

    headers = {}
    for hdr in ('Authorization', 'Content-Type', 'X-Admin-Key'):
        val = request.headers.get(hdr)
        if val:
            headers[hdr] = val

    body = request.get_data() or None
    req = urllib.request.Request(url, data=body, headers=headers, method=request.method)

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read(), resp.status, {
                'Content-Type': resp.headers.get('Content-Type', 'application/json')
            }
    except urllib.error.HTTPError as e:
        # Home server returned an error — pass it through
        return e.read(), e.code, {
            'Content-Type': e.headers.get('Content-Type', 'application/json')
        }
    except urllib.error.URLError as e:
        # Network error (home server unreachable)
        print(f"[PROXY ERROR] {path} → {url} | {e}", flush=True)
        return jsonify({'error': 'Home server unavailable', 'detail': str(e)}), 503
    except Exception as e:
        # Unexpected error
        print(f"[PROXY ERROR] {path} | {type(e).__name__}: {e}", flush=True)
        return jsonify({'error': 'Service temporarily unavailable.'}), 503


@app.route('/api/volunteer-events', methods=['GET'])
@app.route('/api/volunteer-events/<int:event_id>', methods=['PATCH', 'DELETE'])
def volunteer_events_proxy(event_id=None):
    path = f"/api/volunteer-events/{event_id}" if event_id else "/api/volunteer-events"
    return _live_proxy(path)


@app.route("/api/volunteer-interest/<ein>", methods=["GET", "POST", "DELETE"])
def volunteer_interest_proxy(ein):
    """Proxy anonymous volunteer interest signals to the live backend."""
    return _live_proxy(f"/api/volunteer-interest/{ein}")

# Event proxy routes disabled 2026-07-24 14:07 — caused timeouts (backend unreachable from droplet)
# These need a live backend service to proxy to; droplet is static-only.
# TODO: Re-enable when central event API is available, or implement local event retrieval from precompute.

# @app.route('/api/org/<ein>/volunteer-events', methods=['GET', 'POST'])
# def org_volunteer_events_proxy(ein):
#     return _live_proxy(f"/api/org/{ein}/volunteer-events")

# @app.route("/e/<short_id>", methods=["GET"])
# def event_short_proxy(short_id):
#     """Proxy short event links to the live event backend."""
#     if not re.match(r"^[A-Za-z0-9_-]{6,16}$", short_id):
#         return "Not found", 404
#     return _live_proxy(f"/e/{short_id}")

# @app.route('/api/events/<int:event_id>', methods=['GET'])
# def event_detail_proxy(event_id):
#     """Public event detail endpoint — proxy to live backend."""
#     return _live_proxy(f"/api/events/{event_id}")

# @app.route("/api/events/<int:event_id>/<path:subpath>", methods=["GET", "POST", "PATCH", "DELETE"])
# def event_subroute_proxy(event_id, subpath):
#     """Proxy event actions and artifacts to the live backend."""
#     return _live_proxy(f"/api/events/{event_id}/{subpath}")



@app.route('/api/profile-contexts', methods=['GET', 'POST'])
@app.route('/api/profile-contexts/<path:subpath>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def profile_contexts_proxy(subpath=None):
    """Profile contexts and member management — feature-flagged, proxy to live."""
    return _live_proxy(request.path)


@app.route('/api/admin/discovery/queue', methods=['GET'])
@app.route('/api/admin/discovery/queue/<int:candidate_id>/review', methods=['POST'])
@app.route('/api/admin/intent/summary', methods=['GET'])
def admin_discovery_intent_proxy(candidate_id=None):
    """Admin analytics for discovery and intent — keep off SPA fallback."""
    return _live_proxy(request.path)


@app.route('/api/org/<ein>/service-area', methods=['GET', 'PUT'])
def service_area_proxy(ein):
    return _live_proxy(f"/api/org/{ein}/service-area")


@app.route('/api/zip/<zip_code>', methods=['GET'])
def zip_proxy(zip_code):
    return _live_proxy(f"/api/zip/{zip_code}")


@app.route('/api/impact', methods=['GET'])
def impact_proxy():
    return _live_proxy("/api/impact")


@app.route('/api/vendors', methods=['GET'])
@app.route('/api/vendors/', methods=['GET'])
def vendors_proxy():
    return _live_proxy("/api/vendors")


@app.route('/api/impact/summary', methods=['GET'])
def impact_summary():
    """Per-org or period-based impact summary. Returns placeholder data."""
    from datetime import datetime
    period = request.args.get('period', 'month').lower()
    if period not in ('day', 'month', 'year', 'all'):
        period = 'month'

    return jsonify({
        'donation_attributed': 0,
        'donation_count': 0,
        'volunteer_hours': 0,
        'volunteer_reports': 0,
        'volunteer_value': 0,
        'partnership_savings': 0,
        'unique_orgs': 0,
        'last_updated': datetime.utcnow().isoformat(),
        'period': period,
    })


@app.route('/api/wallet/funding-history', methods=['POST'])
def log_funding():
    """Log a donation for tax tracking. Returns success response."""
    import uuid
    from datetime import datetime

    try:
        data = request.get_json() or {}
        ein = ''.join(c for c in data.get('ein', '') if c.isdigit())[:10]
        nonprofit_name = str(data.get('nonprofitName', '')).strip()
        amount = data.get('amount')
        date_str = str(data.get('date', '')).strip()

        if not ein or not nonprofit_name or amount is None or amount <= 0 or not date_str:
            return jsonify({'error': 'Invalid input'}), 400

        funding_id = str(uuid.uuid4())
        return jsonify({
            'success': True,
            'id': funding_id,
            'message': f'Recorded ${amount:,.0f} donation to {nonprofit_name} on {date_str}',
        })
    except Exception as e:
        return jsonify({'error': 'Failed to log funding'}), 500


@app.route('/api/wallet/funding-export', methods=['GET'])
def export_funding_csv():
    """Export funding records as CSV. Returns placeholder data."""
    from io import StringIO
    import csv
    from datetime import datetime

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Nonprofit Name', 'EIN', 'Amount', 'Recorded'])
    writer.writerow([])
    writer.writerow(['TOTAL', '', '', '$0'])

    csv_content = output.getvalue()
    return (csv_content, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename="daanaa-donations-{datetime.now().strftime("%Y%m%d")}.csv"'
    })


@app.route('/api/nonprofit/<path:subpath>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def nonprofit_proxy(subpath):
    """Proxy nonprofit endpoints to upstream home server."""
    return _live_proxy(f"/api/nonprofit/{subpath}")


@app.route('/api/guild/<path:subpath>', methods=['GET', 'POST', 'PATCH'])
def guild_proxy(subpath):
    return _live_proxy(f"/api/guild/{subpath}")

# ── Frontend SPA ─────────────────────────────────────────────────────────────

# Per-route meta injection. The SPA sets <title>/og tags client-side, but social
# scrapers (LinkedIn, X, Facebook) and many crawlers don't run JS — they read the
# raw HTML, where every route would otherwise share one static title/og:image.
# We inject route-specific title/description/og into the served HTML so shared
# links and search snippets are accurate. Pure string work; og:image stays the
# site default until per-org cards are generated (separate patch).
_INDEX_CACHE: dict = {}

def _index_html() -> str:
    idx = FRONTEND_DIR / 'index.html'
    if not idx.exists():
        return ''
    mtime = idx.stat().st_mtime
    if _INDEX_CACHE.get('mtime') != mtime:
        _INDEX_CACHE['html'] = idx.read_text(encoding='utf-8')
        _INDEX_CACHE['mtime'] = mtime
    return _INDEX_CACHE['html']

def _inject_meta(doc: str, title: str, desc: str, url: str, jsonld: dict | None = None) -> str:
    t, d, u = _htmllib.escape(title), _htmllib.escape(desc), _htmllib.escape(url)
    doc = re.sub(r'<title>.*?</title>', f'<title>{t}</title>', doc, count=1, flags=re.S)
    for attr, val in (
        (r'<meta name="description" content="', d),
        (r'<meta property="og:title" content="', t),
        (r'<meta property="og:description" content="', d),
        (r'<meta property="og:url" content="', u),
        (r'<meta name="twitter:title" content="', t),
        (r'<meta name="twitter:description" content="', d),
    ):
        doc = re.sub(re.escape(attr) + r'[^"]*"', attr + val + '"', doc, count=1)
    # Canonical: replace the placeholder href so each route advertises its own URL.
    doc = re.sub(r'(<link rel="canonical" href=")[^"]*(")', r'\g<1>' + u + r'\g<2>', doc, count=1)
    # Server-side JSON-LD so Bing and non-JS crawlers see structured data.
    if jsonld:
        import json as _json
        ld_block = f'<script type="application/ld+json">{_json.dumps(jsonld, ensure_ascii=False)}</script>'
        doc = doc.replace('</head>', ld_block + '</head>', 1)
    return doc

# Static (non-org) content routes that benefit from real server-rendered meta.
# Keeps title/description/canonical in the served HTML so crawlers and social
# preview bots don't fall back to the generic homepage shell. Path is stripped
# of slashes; value is (title, description).
_STATIC_META = {
    '': (
        'Daanaa — Find causes near you making a difference.',
        'Discover 1.8+ million active U.S. nonprofits including the ones you\'ve never heard of. Giving Wallet to keep track of your giving for tax season. Private by design, no fees or charges ever !',
    ),
    'methodology': (
        'Methodology — How Daanaa Works',
        'How Daanaa organizes public nonprofit information: data sources, Peer '
        'Financial Context, Lamp Tiers, what we do not measure, data limits, '
        'and answers to common questions.',
    ),
    'directory': (
        'Directory — Explore 1.8M U.S. Nonprofits',
        'Search every IRS-recognized 501(c)(3) by cause, location, and peer '
        'financial context. Independent, donation-neutral, and private by design.',
    ),
    'about': (
        'About Daanaa',
        'Daanaa is an independent civic platform that helps people discover '
        'nonprofits using public IRS data, presented with context and respect.',
    ),
    'charter': (
        'The Daanaa Charter',
        'Ten promises Daanaa makes to the nonprofits and donors it serves: '
        'never a cut of donations, never paid placement, never selling data. '
        'Published so anyone can hold us to them.',
    ),
    'principles': (
        'Our Principles — Daanaa',
        'The stewardship principles behind Daanaa: evidence-based trust signals, '
        'structural donor privacy, and protected independence.',
    ),
    'for-nonprofits': (
        'For Nonprofits — Claim Your Page on Daanaa',
        'Claim and update your organization\'s page on Daanaa for free. Add '
        'your mission, website, and programs. No paid placement, ever.',
    ),
    'security': (
        'Security — Daanaa',
        'How Daanaa protects your data: no tracking, no advertising profiles, '
        'device-first wallet storage, and responsible disclosure.',
    ),
    'legal': (
        'Legal & Privacy — Daanaa',
        'Daanaa terms of service, privacy policy, and data practices. '
        'No advertising profiles. Wallet data stays on your device by default.',
    ),
    'research': (
        'Sector Research — Daanaa',
        'Public data on U.S. nonprofit financial health across sectors. '
        'Drawn from IRS Form 990 filings. Context, not rankings.',
    ),
    'open-data': (
        'Open Data and AI Access — Daanaa',
        'Machine-readable entry points for Daanaa: directory, methodology, '
        'research, sitemap, llms.txt, and open data export links for search '
        'engines and AI systems.',
    ),
    'wallet': (
        'Giving Wallet — Daanaa',
        'Your private bookmarks and giving notes. Stored on your device by default. '
        'No account required. No data shared or used for advertising.',
    ),
    'volunteer': (
        'Volunteer Opportunities — Daanaa',
        'Find volunteer opportunities with nonprofits near you. Browse by cause, '
        'location, and organization type.',
    ),
    'nonprofit': (
        'Nonprofit Portal — Daanaa',
        'Claim and manage your organization page on Daanaa. Free for nonprofits.',
    ),
    'donation': (
        'Donation — Daanaa',
        'Daanaa is a discovery platform. All giving goes directly to the nonprofit. '
        'Daanaa never handles or processes donations.',
    ),
    'partners': (
        'Community Partners — Daanaa',
        'Businesses offering services to nonprofits through the Daanaa Impact Network.',
    ),
    'terms': (
        'Terms of Service — Daanaa',
        'Terms governing use of daanaa.org, operated by EcoMargins Consulting LLC.',
    ),
}

# Legacy paths merged into a single canonical page — answered with a real 301
# so link equity consolidates instead of relying on a client-side JS redirect.
_LEGACY_REDIRECTS = {
    'how-it-works': '/methodology',
    'learn': '/methodology',
    'guides': '/methodology',
    'faq': '/methodology#faq',
    # 'privacy' removed 2026-07-03: the SPA now has a real /privacy page
    # (App.tsx routes it to <Privacy />); redirecting to /legal made it unreachable.
}

# NTEE major-group letter names — mirrors frontend/src/data/ntee.ts so
# /category/<letter> pages get real server-rendered titles for crawlers.
_NTEE_LETTER_NAMES = {
    'A': 'Arts & Culture', 'B': 'Education', 'C': 'Environment', 'D': 'Animals',
    'E': 'Health', 'F': 'Mental Health', 'G': 'Disease Research',
    'H': 'Medical Research', 'I': 'Crime & Legal', 'J': 'Employment',
    'K': 'Food & Nutrition', 'L': 'Housing & Shelter', 'M': 'Public Safety',
    'N': 'Sports & Recreation', 'O': 'Youth Development', 'P': 'Human Services',
    'Q': 'International', 'R': 'Civil Rights', 'S': 'Community',
    'T': 'Philanthropy', 'U': 'Science & Technology', 'V': 'Social Science',
    'W': 'Public Benefit', 'X': 'Faith', 'Y': 'Mutual Benefit', 'Z': 'Unclassified',
}

_HOMEPAGE_JSONLD = {
    '@context': 'https://schema.org',
    '@graph': [
        {
            '@type': 'Organization',
            'name': 'Daanaa',
            'url': 'https://daanaa.org',
            'logo': 'https://daanaa.org/logo.png',
            'description': 'Independent nonprofit discovery platform indexing 1.8M U.S. nonprofits with peer financial context and public IRS data.',
        },
        {
            '@type': 'WebSite',
            'name': 'Daanaa',
            'url': 'https://daanaa.org',
            'potentialAction': {
                '@type': 'SearchAction',
                'target': {
                    '@type': 'EntryPoint',
                    'urlTemplate': 'https://daanaa.org/directory?q={search_term_string}',
                },
                'query-input': 'required name=search_term_string',
            },
        },
    ],
}

def _org_jsonld(org: dict, ein: str) -> dict:
    name = org.get('organization_name') or 'Nonprofit'
    city, state = org.get('CITY'), org.get('STATE')
    ntee_label = org.get('ntee1_label') or org.get('ntee_label') or ''
    ld: dict = {
        '@context': 'https://schema.org',
        # NGO is schema.org's actual nonprofit subtype (fixed 2026-07-10 eng
        # review finding 1B -- "NonprofitOrganization" is not a real schema.org
        # type; NGO is what Google's structured-data docs reference).
        '@type': 'NGO',
        'name': name,
        'url': f'https://daanaa.org/org/{ein}',
        'identifier': ein,
    }
    mission = (org.get('mission') or '').strip()
    if mission:
        ld['description'] = mission[:300]
    if city or state:
        addr: dict = {'@type': 'PostalAddress'}
        if city:
            addr['addressLocality'] = city
        if state:
            addr['addressRegion'] = state
        ld['address'] = addr
    if ntee_label:
        ld['category'] = ntee_label
    website = org.get('website') or org.get('website_final_domain')
    if website:
        ld['sameAs'] = website if website.startswith('http') else f'https://{website}'
    return ld

def _meta_for_path(path: str):
    """Returns (title, description, url, jsonld|None) for crawler-relevant routes, else None."""
    p = (path or '').strip('/')
    if p == '':
        title, desc = _STATIC_META.get('', ('Daanaa — Independent Nonprofit Discovery Platform',
            'Discover causes and organizations using public nonprofit information.'))
        return (title, desc, 'https://daanaa.org/', _HOMEPAGE_JSONLD)
    if p.startswith('org/'):
        ein = p.split('/', 1)[1].split('/')[0].strip().upper()
        org = load_org_detail(ein)
        if org:
            name = org.get('organization_name') or 'Nonprofit'
            city, state = org.get('CITY'), org.get('STATE')
            loc = f"{city}, {state}" if city and state else (state or '')
            mission = (org.get('mission') or '').strip()
            desc = mission[:200] if mission else (
                f"{name}{(' in ' + loc) if loc else ''}: public IRS record, peer "
                f"financial context, and mission on Daanaa.")
            return (f"{name} — Daanaa", desc, f"https://daanaa.org/org/{ein}", _org_jsonld(org, ein))
    if p.startswith('category/'):
        letter = p.split('/', 1)[1].split('/')[0].strip().upper()
        if letter in _NTEE_LETTER_NAMES:
            cat_name = _NTEE_LETTER_NAMES[letter]
            title = f"{cat_name} Organizations — Daanaa"
            desc = f"Discover IRS-recognized nonprofits in {cat_name} with peer financial context and public records."
            return (title, desc, f"https://daanaa.org/category/{letter}", None)
    if p in _STATIC_META:
        title, desc = _STATIC_META[p]
        return (title, desc, f"https://daanaa.org/{p}", None)
    return None

# Known SPA route prefixes — anything not in this set and not a static file returns 404.
# Prevents probe paths (/.env, /.git/config, /backup.zip) from getting a soft 200.
_SPA_PREFIXES = {
    '', 'directory', 'category', 'causes', 'org', 'compare', 'legal',
    'how-it-works', 'wallet', 'giving-wallet', 'for-nonprofits', 'about',
    'principles', 'governance', 'stewardship', 'why-daanaa-exists', 'tiers',
    'methodology', 'sector-health', 'learn', 'guides', 'faq', 'feedback',
    'partners', 'for-vendors', 'vendor-policy', 'terms', 'guild', 'member',
    'volunteer', 'donation', 'research', 'the-invisible-97', 'invisible-preview',
    'nonprofit', 'vendor', 'claim', 'admin',
    'security', 'privacy', 'meet-the-invisible', 'invisible', 'charter',
    'settings', 'event', 'events', 'open-data', 'profile-contexts',
}

@app.route('/api/voice/support', methods=['POST'])
def voice_support_inbound():
    """Inbound voice call handler — transfer to founder's personal phone."""
    from_phone = (request.form.get('From') or '').strip()
    call_sid = (request.form.get('CallSid') or '').strip()

    print(f"[Support Call] Incoming from {from_phone}, CallSid={call_sid}", flush=True)

    # Return TwiML response: play founder's greeting, then transfer to their phone
    # Note: Twilio <Dial> requires E.164 format (no dashes): +13479373555
    # Dial timeout defaults to 30s; ring 60s to give ample time
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>https://daanaa.org/static/greeting.m4a</Play>
  <Dial timeout="60">+13479373555</Dial>
</Response>"""

    return twiml, 200, {'Content-Type': 'application/xml'}


# ── Public Profile Sources ───────────────────────────────────────────────────
# Show data sources and provenance for nonprofit profiles (public endpoint)

@app.route('/api/public/nonprofit/<ein>/profile/sources', methods=['GET'])
def public_profile_sources(ein: str):
    """Public: Show data sources and provenance for nonprofit profile."""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({'error': 'Invalid EIN format'}), 400

    try:
        db = get_search_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503

        org = db.execute(
            "SELECT organization_name, mission FROM registry_enriched WHERE ein = ?",
            (ein_clean,)
        ).fetchone()

        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        org_name = org['organization_name']
        mission = org['mission']

        return jsonify({
            'ein': ein_clean,
            'organization_name': org_name,
            'sources': {
                'mission': {
                    'value': mission,
                    'source': 'IRS Form 990 via ProPublica'
                },
                'financial_data': {
                    'source': 'IRS Form 990'
                }
            }
        })
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


# QA Testing Hub — serves test documents, credentials, and report submission form
@app.route('/qa', defaults={'path': ''})
@app.route('/qa/<path:path>')
def serve_qa(path):
    """Serve QA testing hub from /opt/daanaa/qa."""
    QA_DIR = Path('/opt/daanaa/qa')
    if not QA_DIR.exists():
        return jsonify({'error': 'QA hub not available'}), 404

    if not path:
        qa_index = QA_DIR / 'index.html'
        if qa_index.exists():
            return send_file(str(qa_index))
        return jsonify({'error': 'QA index not found'}), 404

    # Serve requested file
    qa_file = QA_DIR / path
    if qa_file.exists() and qa_file.is_file():
        return send_from_directory(str(QA_DIR), path)

    return jsonify({'error': 'Not found'}), 404


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    if FRONTEND_DIR.exists():
        # 301 legacy/merged routes to their canonical destination.
        target = _LEGACY_REDIRECTS.get((path or '').strip('/'))
        if target:
            return redirect(target, code=301)
        full = FRONTEND_DIR / path
        if full.is_file():
            return send_from_directory(FRONTEND_DIR, path)
        # Only serve the SPA for known client-side routes; everything else is a real 404.
        top = (path or '').strip('/').split('/')[0]
        if top not in _SPA_PREFIXES:
            return 'Not found', 404
        index = FRONTEND_DIR / 'index.html'
        if index.exists():
            meta = _meta_for_path(path)
            if meta:
                return Response(_inject_meta(_index_html(), *meta), mimetype='text/html')
            return send_file(index)
    return 'Not found', 404


def _validate_search_db():
    """Fail loudly if search.db is missing, empty, or invalid. Better to crash
    on startup than silently return 0 search results."""
    fts_path = DATA_DIR / 'search.db'

    # Check existence
    if not fts_path.exists():
        raise RuntimeError(
            f"FATAL: search.db not found at {fts_path}. "
            "Search will not work. Deploy search.db from home server via: "
            "rsync ~/meritgiving/data/merit_registry.db root@droplet:/data/precompute/v1/search.db"
        )

    # Check size (0-byte file is a deployment failure)
    size = fts_path.stat().st_size
    if size == 0:
        raise RuntimeError(
            f"FATAL: search.db is empty (0 bytes) at {fts_path}. "
            "This is a deployment error. Sync from home server: "
            "rsync ~/meritgiving/data/merit_registry.db root@droplet:/data/precompute/v1/search.db"
        )

    # Check that org_fts table exists and has data
    try:
        conn = sqlite3.connect(str(fts_path), timeout=5)
        try:
            # Verify org_fts FTS5 table exists
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='org_fts'"
            ).fetchone()
            if not result:
                raise RuntimeError(
                    f"FATAL: org_fts table not found in search.db. "
                    "This file is corrupted or incompatible. "
                    "Redeploy from home server: "
                    "rsync ~/meritgiving/data/merit_registry.db root@droplet:/data/precompute/v1/search.db"
                )

            # Verify registry_enriched table exists (for orgs view)
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='registry_enriched'"
            ).fetchone()
            if not result:
                raise RuntimeError(
                    f"FATAL: registry_enriched table not found in search.db. "
                    "Database schema is incomplete. Redeploy: "
                    "rsync ~/meritgiving/data/merit_registry.db root@droplet:/data/precompute/v1/search.db"
                )

            # Count rows in org_fts to ensure index is populated
            count = conn.execute("SELECT COUNT(*) FROM org_fts").fetchone()[0]
            if count == 0:
                raise RuntimeError(
                    f"FATAL: org_fts table is empty (0 rows). "
                    "FTS index was not built. Redeploy: "
                    "rsync ~/meritgiving/data/merit_registry.db root@droplet:/data/precompute/v1/search.db"
                )

            print(f"✓ search.db validated: {count:,} organizations in FTS index ({size / (1024**3):.1f} GB)")
        finally:
            conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(
            f"FATAL: search.db is corrupted or unreadable: {e}. "
            "Redeploy from home server: "
            "rsync ~/meritgiving/data/merit_registry.db root@droplet:/data/precompute/v1/search.db"
        )


if __name__ == '__main__':
    print(f"Data dir: {DATA_DIR} ({'exists' if DATA_DIR.exists() else 'MISSING'})")
    try:
        _validate_search_db()
    except RuntimeError as e:
        print(str(e), file=__import__('sys').stderr)
        __import__('sys').exit(1)
    app.run(host='0.0.0.0', port=5000, debug=False)
