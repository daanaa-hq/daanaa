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
import urllib.error
import urllib.request
from math import radians, cos, sin, asin, sqrt
from pathlib import Path

import html as _htmllib
from flask import Flask, request, jsonify, send_file, send_from_directory, Response, redirect
from flask_cors import CORS

app = Flask(__name__, static_folder=None)
# Restrict CORS to the production origins. The SPA is served same-origin, so
# this only governs cross-origin API calls — no need to allow the whole web.
CORS(app, origins=["https://daanaa.org", "https://www.daanaa.org"],
     supports_credentials=False)


@app.after_request
def set_security_headers(response):
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
CLAIMS_DIR   = Path(os.environ.get('CLAIMS_DIR', '/data/claims'))
FRONTEND_DIR = Path(os.environ.get('FRONTEND_DIR', '/opt/daanaa/frontend/dist'))

_json_cache: dict = {}
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
        return _json_cache[key]
    if not path.exists():
        return None
    try:
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        _json_cache[key] = data
        return data
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None


def get_search_db():
    fts_path = DATA_DIR / 'search.db'
    if not fts_path.exists():
        return None
    conn = sqlite3.connect(str(fts_path), timeout=10)
    conn.row_factory = sqlite3.Row
    # Serve cold page reads from the OS page cache; big win on filter scans.
    conn.execute("PRAGMA mmap_size=1073741824")
    return conn


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
    row = conn.execute(
        "SELECT lat, lon, city, state_id FROM zip_codes WHERE UPPER(city)=? LIMIT 1",
        (near.upper(),)
    ).fetchone()
    if row:
        return row["lat"], row["lon"], row["city"], row["state_id"]
    return None


def _fts_where(q: str, state: str = '') -> tuple:
    """Build base FTS WHERE conditions and params for q + state.
    Returns (conditions, params, detected_zip_or_None)."""
    # Extract a trailing 5-digit zip from the query so it can drive proximity.
    detected_zip = None
    words = q.split()
    if words and re.match(r'^\d{5}$', words[-1]):
        detected_zip = words[-1]
        words = words[:-1]
    fts_q = ' '.join(f'{w}*' for w in words if w) or ' '.join(f'{w}*' for w in q.split() if w)
    conditions: list = ["s.ein = o.EIN", "org_fts MATCH ?"]
    params: list = [fts_q]
    if state:
        conditions.append("o.STATE = ?")
        params.append(state)
    return conditions, params, detected_zip


def _cat_rev_conditions(ntee_list, sub_list, min_rev, max_rev, alias=''):
    """Category + revenue WHERE fragments, mirroring the home daanaa_api
    semantics: any ticked category (NTEE1) or subcategory (NTEECC prefix)
    matches, AND revenue within [min_rev, max_rev]. The old code took only
    the first character of the ntee param, so 'R,I' matched nothing and
    revenue was ignored entirely (0-results bug on production, 2026-06-09)."""
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
    if min_rev is not None:
        conds.append(f"{alias}total_revenue >= ?")
        params.append(min_rev)
    if max_rev is not None:
        conds.append(f"{alias}total_revenue <= ?")
        params.append(max_rev)
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
    COALESCE keeps NULLs last (and, per the 2026-06-09 note, avoids the score
    index forcing a row-by-row probe on filtered browses)."""
    o = (order or '').strip().lower()
    if sort in ('name', 'organization_name'):
        d = 'DESC' if o == 'desc' else 'ASC'
        return f"{alias}organization_name {d}"
    if sort in ('revenue', 'total_revenue'):
        d = 'ASC' if o == 'asc' else 'DESC'
        return f"COALESCE({alias}total_revenue, -1) {d}"
    # default + explicit merit_score
    d = 'ASC' if o == 'asc' else 'DESC'
    return f"COALESCE({alias}merit_score, -1) {d}"


# Legal posture (2026-06-10): no donation links on public surfaces. Donate data
# stays internal; strip it from every payload — including precomputed files
# generated before the policy change.
_DONATE_FIELDS = (
    'donate_url', 'donate_platform', 'donate_url_status', 'donate_confidence',
    'donate_source_page', 'donate_identity_match', 'donate_human_review',
    'donate_checked_at',
)

def _strip_donate(d: dict) -> dict:
    for k in _DONATE_FIELDS:
        d.pop(k, None)
    badges = d.get('data_badges')
    if isinstance(badges, dict):
        badges.pop('donate', None)
    return d


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
    return _strip_donate(d)


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
        return _strip_donate(data)

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
    claims_file = CLAIMS_DIR / f"{ein}.json"
    if not claims_file.exists():
        return org_data
    try:
        with open(claims_file) as f:
            claims = json.load(f)
        org_data['claim_status'] = claims.get('status')
        org_data['verified_at']  = claims.get('verified_at')
        org_data['verified_fields'] = claims.get('verified_fields', {})
    except Exception:
        pass
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
    try:
        page     = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', PER_PAGE_DEFAULT))))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid page or per_page parameter'}), 400
    hidden_gem         = request.args.get('hidden_gem', '').strip() == '1'
    needs_funding      = request.args.get('needs_funding', '').strip() == '1'
    has_website        = request.args.get('has_website', '').strip() == '1'
    open_to_volunteers = request.args.get('open_to_volunteers', '').strip() == '1'
    order = request.args.get('order', '').strip()
    tier  = request.args.get('tier', '').strip()
    min_rev = request.args.get('min_revenue', type=float)
    max_rev = request.args.get('max_revenue', type=float)
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
                              hidden_gem, needs_funding, has_website, order, tier,
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
    if any_filter or multi_select or min_rev is not None or max_rev is not None:
        return _db_filter_browse(ntee_list, sub_list, min_rev, max_rev,
                                 state, sort, page, per_page,
                                 hidden_gem, needs_funding, has_website, order, tier,
                                 open_to_volunteers=open_to_volunteers,
                                 nearby_zips=nearby_zips, nearby_meta=nearby_meta)

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
                      hidden_gem, needs_funding, has_website, order='', tier='',
                      open_to_volunteers=False, nearby_zips=None, nearby_meta=None):
    """Query orgs table directly with filter conditions but no FTS match."""
    conn = get_search_db()
    if not conn:
        return jsonify({'organizations': [], 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page})
    try:
        conditions, params = _cat_rev_conditions(ntee_list, sub_list, min_rev, max_rev)
        if state:
            conditions.append("STATE = ?")
            params.append(state)
        if hidden_gem:
            conditions.append("is_hidden_gem = 1")
        if needs_funding:
            conditions.append("months_of_reserve IS NOT NULL AND months_of_reserve < 6")
        if has_website:
            conditions.append("website IS NOT NULL AND website != '' AND website_status = 'ok'")
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
        rows = conn.execute(
            f"SELECT * FROM registry_enriched {where} ORDER BY {order_by} LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
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
                   hidden_gem, needs_funding, has_website, order='', tier='',
                   open_to_volunteers=False, nearby_zips=None, nearby_meta=None):
    """FTS search against search.db orgs table, returns full org objects."""
    conn = get_search_db()
    if not conn:
        return jsonify({'organizations': [], 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page, 'search_type': 'fts'})
    try:
        conditions, params = _fts_where(q, state)
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

        count_sql = f"""
            SELECT COUNT(*) FROM org_fts s, registry_enriched o
            WHERE {' AND '.join(conditions)}
        """
        total = conn.execute(count_sql, params).fetchone()[0]

        offset = (page - 1) * per_page
        params_page = params + [per_page, offset]
        rows_sql = f"""
            SELECT o.* FROM org_fts s, registry_enriched o
            WHERE {' AND '.join(conditions)}
            ORDER BY {order}
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(rows_sql, params_page).fetchall()
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
    merged.sort(key=lambda o: o.get('merit_score') or 0, reverse=True)
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

def _get_real_total(state: str = '') -> int:
    """Return the true org count from search.db, cached indefinitely per state."""
    key = state or '_all'
    if key in _real_total_cache:
        return _real_total_cache[key]
    conn = get_search_db()
    if not conn:
        return 0
    try:
        if state:
            n = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE STATE = ?", (state,)).fetchone()[0]
        else:
            n = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
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
    org_data = merge_claims(org_data, ein)
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
        conditions, params, _zip = _fts_where(query, state)
        cat_conds, cat_params = _cat_rev_conditions(
            [x.strip()[:1] for x in ntee.split(',') if x.strip()], [], None, None, alias='o.')
        conditions.extend(cat_conds)
        params.extend(cat_params)
        params.append(limit)
        sql = (f"SELECT o.EIN, o.organization_name, o.NTEE1, o.NTEECC, o.CITY, o.STATE, o.mission, o.merit_score "
               f"FROM org_fts s, registry_enriched o WHERE {' AND '.join(conditions)} LIMIT ?")
        rows = conn.execute(sql, params).fetchall()
        results = [dict(r) for r in rows]
        return jsonify({'results': results, 'query': query,
                        'total': len(results), 'mode': 'fts'})
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
        conditions, params, _zip = _fts_where(q, state)
        cat_conds, cat_params = _cat_rev_conditions(
            [x.strip()[:1] for x in ntee.split(',') if x.strip()], [], None, None, alias='o.')
        conditions.extend(cat_conds)
        params.extend(cat_params)

        total = conn.execute(
            f"SELECT COUNT(*) FROM org_fts s, registry_enriched o WHERE {' AND '.join(conditions)}", params
        ).fetchone()[0]
        offset = (page - 1) * per_page
        sql = (f"SELECT o.* FROM org_fts s, registry_enriched o "
               f"WHERE {' AND '.join(conditions)} "
               f"ORDER BY COALESCE(o.merit_score, -1) DESC "
               f"LIMIT ? OFFSET ?")
        rows = conn.execute(sql, params + [per_page, offset]).fetchall()
        orgs = [_row_to_org(r) for r in rows]
        pages = max(1, (total + per_page - 1) // per_page)
        return jsonify({'organizations': orgs, 'query': q,
                        'total': total, 'pages': pages,
                        'page': page, 'per_page': per_page, 'search_type': 'fts'})
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

LIVE_UPSTREAM = os.environ.get('CLAIM_UPSTREAM', 'http://127.0.0.1:5001')


def _live_proxy(path: str):
    """Generic transparent proxy to the home-server backend on :5001."""
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
        return e.read(), e.code, {
            'Content-Type': e.headers.get('Content-Type', 'application/json')
        }
    except Exception:
        return jsonify({'error': 'Service temporarily unavailable.'}), 503


@app.route('/api/volunteer-events', methods=['GET'])
@app.route('/api/volunteer-events/<int:event_id>', methods=['PATCH', 'DELETE'])
def volunteer_events_proxy(event_id=None):
    path = f"/api/volunteer-events/{event_id}" if event_id else "/api/volunteer-events"
    return _live_proxy(path)


@app.route('/api/org/<ein>/volunteer-events', methods=['GET', 'POST'])
def org_volunteer_events_proxy(ein):
    return _live_proxy(f"/api/org/{ein}/volunteer-events")


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
    'privacy': '/legal',
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
        '@type': 'Organization',
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
    'security', 'privacy', 'meet-the-invisible', 'invisible',
}

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
