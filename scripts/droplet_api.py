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
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=None)
CORS(app)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
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


def _fts_where(q: str, state: str = '') -> tuple:
    """Build base FTS WHERE conditions and params for q + state."""
    fts_q = ' '.join(f'{w}*' for w in q.split() if w)
    conditions: list = ["s.ein = o.EIN", "org_search MATCH ?"]
    params: list = [fts_q]
    if state:
        conditions.append("o.STATE = ?")
        params.append(state)
    return conditions, params


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
    return d


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
        return data

    # Fallback: serve from search.db orgs table (IRS_BMF / bmf_stub orgs)
    conn = get_search_db()
    if not conn:
        return None
    try:
        row = conn.execute("SELECT * FROM orgs WHERE EIN = ?", (ein,)).fetchone()
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
    hidden_gem    = request.args.get('hidden_gem', '').strip() == '1'
    needs_funding = request.args.get('needs_funding', '').strip() == '1'
    has_website   = request.args.get('has_website', '').strip() == '1'
    direct_link   = request.args.get('direct_link', '').strip() == '1'
    min_rev = request.args.get('min_revenue', type=float)
    max_rev = request.args.get('max_revenue', type=float)
    # Comma-separated multi-select, same contract as the home daanaa_api:
    # ntee=R,I (category letters) and sub=E21,A82 (NTEECC prefixes), OR-combined.
    ntee_list = [x.strip()[:1] for x in ntee.split(',') if x.strip()][:26]
    sub_list  = [x.strip()[:4] for x in sub.split(',') if x.strip()][:40]

    # ── Text search: route to FTS ──────────────────────────────────────────
    if q and len(q) >= 2:
        return _fts_directory(q, ntee_list, sub_list, min_rev, max_rev,
                              state, sort, page, per_page,
                              hidden_gem, needs_funding, has_website, direct_link)

    # ── Filter browse: DB query when flags, revenue, or multi-select used ───
    any_filter = hidden_gem or needs_funding or has_website or direct_link
    multi_select = len(ntee_list) > 1 or len(sub_list) > 1 or (ntee_list and sub_list)
    if any_filter or multi_select or min_rev is not None or max_rev is not None:
        return _db_filter_browse(ntee_list, sub_list, min_rev, max_rev,
                                 state, sort, page, per_page,
                                 hidden_gem, needs_funding, has_website, direct_link)

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
                      hidden_gem, needs_funding, has_website, direct_link):
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
        if direct_link:
            conditions.append("donate_url IS NOT NULL AND donate_url != ''")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        _SORT_MAP = {'name': 'organization_name ASC'}
        # COALESCE instead of NULLS LAST: same ordering, but the non-indexable
        # expression stops SQLite walking the score index and probing the
        # filter row-by-row (6s → 0.2s on OR'd category filters, 2026-06-09).
        order = _SORT_MAP.get(sort, 'COALESCE(merit_score, -1) DESC')

        total = conn.execute(f"SELECT COUNT(*) FROM orgs {where}", params).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT * FROM orgs {where} ORDER BY {order} LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
        orgs = [_row_to_org(r) for r in rows]
        pages = max(1, (total + per_page - 1) // per_page)
        return jsonify({'organizations': orgs, 'total': total,
                        'page': page, 'per_page': per_page, 'pages': pages})
    except Exception as e:
        print(f"DB filter browse error: {e}")
        return jsonify({'organizations': [], 'total': 0, 'pages': 0,
                        'page': page, 'per_page': per_page})
    finally:
        conn.close()


def _fts_directory(q, ntee_list, sub_list, min_rev, max_rev,
                   state, sort, page, per_page,
                   hidden_gem, needs_funding, has_website, direct_link):
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
        if direct_link:
            conditions.append("o.donate_url IS NOT NULL AND o.donate_url != ''")

        order = "COALESCE(o.merit_score, -1) DESC"
        if sort == 'name':
            order = "o.organization_name ASC"

        count_sql = f"""
            SELECT COUNT(*) FROM org_search s, orgs o
            WHERE {' AND '.join(conditions)}
        """
        total = conn.execute(count_sql, params).fetchone()[0]

        offset = (page - 1) * per_page
        params_page = params + [per_page, offset]
        rows_sql = f"""
            SELECT o.* FROM org_search s, orgs o
            WHERE {' AND '.join(conditions)}
            ORDER BY {order}
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(rows_sql, params_page).fetchall()
        orgs = [_row_to_org(r) for r in rows]
        pages = max(1, (total + per_page - 1) // per_page)
        return jsonify({'organizations': orgs, 'total': total,
                        'page': page, 'per_page': per_page,
                        'pages': pages, 'search_type': 'fts'})
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
            n = conn.execute("SELECT COUNT(*) FROM orgs WHERE STATE = ?", (state,)).fetchone()[0]
        else:
            n = conn.execute("SELECT COUNT(*) FROM orgs").fetchone()[0]
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
    record = {}
    for field in ('total_revenue', 'total_expenses', 'net_assets', 'employee_count',
                  'program_expense_pct', 'months_of_reserve', 'latest_tax_year'):
        if org_data.get(field) is not None:
            record[field] = org_data[field]
    financials = [record] if record.get('latest_tax_year') else []
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
        conditions, params = _fts_where(query, state)
        cat_conds, cat_params = _cat_rev_conditions(
            [x.strip()[:1] for x in ntee.split(',') if x.strip()], [], None, None, alias='o.')
        conditions.extend(cat_conds)
        params.extend(cat_params)
        params.append(limit)
        sql = (f"SELECT o.EIN as ein, o.organization_name, o.NTEE1, o.NTEECC, o.CITY, o.STATE, o.mission, o.merit_score "
               f"FROM org_search s, orgs o WHERE {' AND '.join(conditions)} LIMIT ?")
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
        conditions, params = _fts_where(q, state)
        cat_conds, cat_params = _cat_rev_conditions(
            [x.strip()[:1] for x in ntee.split(',') if x.strip()], [], None, None, alias='o.')
        conditions.extend(cat_conds)
        params.extend(cat_params)

        total = conn.execute(
            f"SELECT COUNT(*) FROM org_search s, orgs o WHERE {' AND '.join(conditions)}", params
        ).fetchone()[0]
        offset = (page - 1) * per_page
        sql = (f"SELECT o.* FROM org_search s, orgs o "
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


# ── Frontend SPA ─────────────────────────────────────────────────────────────

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    if FRONTEND_DIR.exists():
        full = FRONTEND_DIR / path
        if full.is_file():
            return send_from_directory(FRONTEND_DIR, path)
        index = FRONTEND_DIR / 'index.html'
        if index.exists():
            return send_file(index)
    return 'Not found', 404


if __name__ == '__main__':
    print(f"Data dir: {DATA_DIR} ({'exists' if DATA_DIR.exists() else 'MISSING'})")
    app.run(host='0.0.0.0', port=5000, debug=False)
