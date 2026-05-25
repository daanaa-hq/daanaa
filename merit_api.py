#!/usr/bin/env python3
"""
MeritGiving API — Serves registry_enriched to frontend
"""
import sqlite3, os, json, functools, time, hashlib, threading
import numpy as np
import requests as _http
from flask import Flask, jsonify, request, g, abort, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')

# Scoring methodology version — the formula/algorithm. Changes rarely, and
# only when the scoring logic itself changes (not on data refreshes). The
# score-computation DATE is read dynamically from score_snapshots.
METHODOLOGY_VERSION = "v1"

# ── Response cache ─────────────────────────────────────────────────────────────
# Simple in-process time-keyed cache. Keys are strings, values are (payload, ts).
# TTLs chosen per endpoint volatility. No external dependency (no Redis).
_CACHE: dict = {}
_CACHE_TTL = {
    'ntee':   7200,   # 2 h — static category list
    'stats':   900,   # 15 min — aggregate counts
    'sector': 1800,   # 30 min — reserve health breakdown
    'search':  300,   # 5 min — directory search results
    'org':     600,   # 10 min — individual org detail
}

def _ck(ns: str, *parts) -> str:
    raw = ns + ':' + ':'.join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def _cget(key: str, ttl_ns: str):
    entry = _CACHE.get(key)
    if entry and (time.time() - entry[1]) < _CACHE_TTL.get(ttl_ns, 300):
        return entry[0]
    return None

def _cset(key: str, value):
    _CACHE[key] = (value, time.time())

# ── Embedding index (lazy-loaded, module-level singleton) ──────────────────────
# Loaded once on first use. ~1.6 GB for 545K orgs × 768-dim float32.
# Falls back gracefully when the build job hasn't completed yet.
_emb_matrix: np.ndarray | None = None   # (N, 768) L2-normalised float32
_emb_eins:   list | None       = None   # parallel EIN list, index = row
_emb_index:  dict | None       = None   # EIN → row index
_emb_lock = threading.Lock()
_emb_loaded = False

OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
OLLAMA_EMBED_MODEL = "nomic-embed-text"
_NTEE_LABELS = {
    "A":"arts culture humanities","B":"education","C":"environment",
    "D":"animal welfare","E":"health care","F":"mental health",
    "G":"disease medical","H":"medical research","I":"crime legal",
    "J":"employment job training","K":"food agriculture nutrition",
    "L":"housing shelter","M":"public safety disaster","N":"recreation sports",
    "O":"youth development","P":"human services family",
    "Q":"international","R":"civil rights advocacy","S":"community improvement",
    "T":"philanthropy grantmaking","U":"science technology","V":"social science",
    "W":"public benefit","X":"religion faith","Y":"mutual benefit",
}

def _load_embeddings():
    global _emb_matrix, _emb_eins, _emb_index, _emb_loaded
    with _emb_lock:
        if _emb_loaded:
            return
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            rows = conn.execute(
                "SELECT ein, vector FROM org_embeddings ORDER BY rowid"
            ).fetchall()
            conn.close()
            if not rows:
                return
            eins = [r[0] for r in rows]
            mat  = np.frombuffer(
                b"".join(r[1] for r in rows), dtype=np.float32
            ).reshape(len(rows), -1)
            _emb_eins   = eins
            _emb_index  = {e: i for i, e in enumerate(eins)}
            _emb_matrix = mat
            _emb_loaded = True
            print(f"[embeddings] loaded {len(eins):,} vectors ({mat.shape[1]}-dim)", flush=True)
        except Exception as e:
            print(f"[embeddings] load failed: {e}", flush=True)

def _get_org_vec(ein: str) -> np.ndarray | None:
    if not _emb_loaded:
        _load_embeddings()
    if _emb_index is None:
        return None
    idx = _emb_index.get(ein)
    return _emb_matrix[idx] if idx is not None else None

def _embed_query(text: str) -> np.ndarray | None:
    try:
        r = _http.post(OLLAMA_EMBED_URL,
                       json={"model": OLLAMA_EMBED_MODEL, "input": [text]},
                       timeout=10)
        r.raise_for_status()
        vec = np.array(r.json()["embeddings"][0], dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec
    except Exception:
        return None

def _vec_similar(query_vec: np.ndarray, exclude_ein: str, limit: int) -> list[str]:
    """Cosine similarity search. Returns top-N EINs (excluding the query org)."""
    scores = _emb_matrix @ query_vec          # dot product = cosine (L2-normed)
    excl   = _emb_index.get(exclude_ein, -1)
    if excl >= 0:
        scores[excl] = -1.0
    top_idx = np.argpartition(scores, -limit)[-limit:]
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]
    return [_emb_eins[i] for i in top_idx]


app = Flask(__name__)

# Restrict CORS to known origins; add production domain when deploying
_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://100.74.118.100:3000",
    "http://100.74.118.100:5173",
    "http://100.74.118.100:5174",
    "http://100.74.118.100:5175",
    "https://daanaa.org",
    "https://www.daanaa.org",
]
CORS(app, origins=_ALLOWED_ORIGINS, supports_credentials=False)

# Rate limiting — backs off abusive callers without blocking normal use
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per minute", "2000 per hour"],
    storage_uri="memory://",
)

DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")

# Admin key — set MERIT_ADMIN_KEY env var before starting the API.
# Any endpoint decorated with @require_admin_key will return 401 if it's missing or wrong.
_ADMIN_KEY = os.environ.get("MERIT_ADMIN_KEY", "")

def require_admin_key(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        provided = request.headers.get("X-Admin-Key", "")
        if not _ADMIN_KEY or provided != _ADMIN_KEY:
            abort(401)
        return f(*args, **kwargs)
    return wrapper

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def _init_waitlist_table():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS waitlist (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email       TEXT NOT NULL,
                ein         TEXT,
                source      TEXT NOT NULL DEFAULT 'newsletter',
                status      TEXT NOT NULL DEFAULT 'new',
                notes       TEXT,
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

_init_waitlist_table()


def _init_link_feedback_table():
    # Anonymous org-findability feedback: EIN + reason + timestamp only.
    # No donor identity, no PII, no link to any wallet. This records whether
    # an organization was reachable, never that a donor intended to give.
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS link_feedback (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                EIN         TEXT NOT NULL,
                reason      TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

_init_link_feedback_table()

# Prevent absurdly large payloads on any endpoint
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # 64 KB

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.route('/health')
@limiter.exempt
def health():
    return jsonify({"status": "ok", "db_exists": os.path.exists(DB_PATH)})

@app.route('/api/organizations')
@limiter.limit("100 per minute")
def list_organizations():
    # Build cache key from all query params before parsing
    ck = _ck('orgs', request.query_string.decode())
    cached = _cget(ck, 'search')
    if cached: return jsonify(cached)

    db = get_db()
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('q', '').strip()[:200]
    ntee_raw = request.args.get('ntee', '').strip().upper()
    ntee_list = [x.strip()[:1] for x in ntee_raw.split(',') if x.strip()]
    sub = request.args.get('sub', '').strip().upper()[:4]   # NTEECC subcategory e.g. E21
    state = request.args.get('state', '').strip().upper()[:2]
    min_rev = request.args.get('min_revenue', type=float)
    max_rev = request.args.get('max_revenue', type=float)
    min_pct = request.args.get('min_percentile', type=float)
    min_tier = request.args.get('min_tier', '').strip()
    hidden_gem = request.args.get('hidden_gem', '').strip() == '1'
    direct_link = request.args.get('direct_link', '').strip() == '1'
    needs_funding = request.args.get('needs_funding', '').strip() == '1'
    cause = request.args.get('cause', '').strip()[:60]
    sort_by = request.args.get('sort', 'total_revenue')
    order = request.args.get('order', 'desc')

    offset = (page - 1) * per_page

    # Always restrict to 501(c)(3) orgs with deductible donations
    where_clauses = [_DEDUCTIBILITY_FILTER]
    params = []

    if search:
        # Normalize hyphens out of the search term so "74-6086238" matches EIN "746086238"
        search_normalized = search.replace('-', '')
        words = [w for w in search_normalized.split() if w]
        for word in words:
            where_clauses.append("(organization_name LIKE ? OR EIN LIKE ? OR CITY LIKE ?)")
            params.extend([f'%{word}%', f'%{word}%', f'%{word}%'])
    if ntee_list:
        if len(ntee_list) == 1:
            where_clauses.append("NTEE1 = ?")
            params.append(ntee_list[0])
        else:
            placeholders = ','.join('?' * len(ntee_list))
            where_clauses.append(f"NTEE1 IN ({placeholders})")
            params.extend(ntee_list)
    if sub:
        where_clauses.append("NTEECC LIKE ?")
        params.append(sub + '%')
    if state:
        where_clauses.append("STATE = ?")
        params.append(state)
    if min_rev is not None:
        where_clauses.append("total_revenue >= ?")
        params.append(min_rev)
    if max_rev is not None:
        where_clauses.append("total_revenue <= ?")
        params.append(max_rev)
    if min_pct is not None:
        where_clauses.append("ntee1_percentile >= ?")
        params.append(min_pct)
    if hidden_gem:
        where_clauses.append("is_hidden_gem = 1")
    if direct_link:
        where_clauses.append("donate_url IS NOT NULL AND donate_url != ''")
    if needs_funding:
        where_clauses.append("months_of_reserve IS NOT NULL AND months_of_reserve < 6")
    if cause:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM json_each(cause_tags) WHERE value LIKE ?)"
        )
        params.append(f'%{cause}%')

    _TIER_HIERARCHY = ['Beacon', 'Lantern', 'Flame', 'Ember', 'Spark']
    if min_tier and min_tier in _TIER_HIERARCHY:
        idx = _TIER_HIERARCHY.index(min_tier)
        included = _TIER_HIERARCHY[:idx + 1]
        placeholders = ','.join('?' * len(included))
        where_clauses.append(f'merit_tier IN ({placeholders})')
        params.extend(included)

    allowed_sorts = ['total_revenue', 'organization_name', 'ntee1_percentile', 'merit_score', 'EIN', 'STATE', 'CITY']
    if sort_by not in allowed_sorts:
        sort_by = 'total_revenue'
    if order not in ['asc', 'desc']:
        order = 'desc'

    where_sql = " AND ".join(where_clauses)

    total = db.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {where_sql}", params).fetchone()[0]

    sql = f"""
        SELECT EIN, organization_name, NTEE1, NTEECC, CITY, STATE,
               total_revenue, ntee1_percentile, ntee1_total_orgs, source,
               latest_tax_year, data_source, updated_at,
               revenue_band, peer_percentile, peer_rank, peer_total, peer_group,
               merit_tier, merit_score, merit_band,
               CASE WHEN months_of_reserve BETWEEN -120 AND 120 THEN months_of_reserve ELSE NULL END as months_of_reserve,
               net_assets, total_expenses,
               employee_count, ruling_date, zipcode, is_hidden_gem, cause_tags,
               donate_url, donate_platform, donate_url_status,
               (mission IS NOT NULL AND mission != '') as has_mission,
               (website IS NOT NULL AND website != '') as has_website
        FROM registry_enriched
        WHERE {where_sql}
        ORDER BY {sort_by} {order}
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])
    rows = db.execute(sql, params).fetchall()

    orgs = []
    for row in rows:
        d = dict(row)
        d['total_revenue_formatted'] = f"${d['total_revenue']:,.0f}" if d['total_revenue'] else None
        if d.get('cause_tags'):
            try:
                d['cause_tags'] = json.loads(d['cause_tags'])
            except (json.JSONDecodeError, TypeError):
                d['cause_tags'] = None
        orgs.append(d)

    payload = {
        "organizations": orgs,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }
    _cset(ck, payload)
    return jsonify(payload)

@app.route('/api/organizations/<ein>')
@limiter.limit("60 per minute")
def get_organization(ein):
    # Sanitize EIN — digits only, max 10 chars
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM registry_enriched WHERE EIN = ?", (ein_clean,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404

    org = dict(row)
    # Clamp sentinel values written by the pipeline (-999, 999) to null
    mor = org.get('months_of_reserve')
    if mor is not None and not (-120 <= mor <= 120):
        org['months_of_reserve'] = None
    org['total_revenue_formatted'] = f"${org['total_revenue']:,.0f}" if org['total_revenue'] else None

    # Parse JSON text columns → Python lists
    if org.get('cause_tags'):
        try:
            org['cause_tags'] = json.loads(org['cause_tags'])
        except (json.JSONDecodeError, TypeError):
            org['cause_tags'] = None

    # Similar orgs: NTEECC+band (specific) → NTEE1+band → NTEE1 only
    org['similar_organizations'] = _find_similar_orgs(db, ein_clean, org, limit=5)

    # Rank within NTEE category (national)
    if org.get('NTEE1'):
        rank = db.execute("""
            SELECT
                (SELECT COUNT(*) FROM registry_enriched WHERE NTEE1 = ?) as total_in_cat,
                (SELECT COUNT(*) FROM registry_enriched WHERE NTEE1 = ? AND total_revenue > ?) as higher_count
        """, (org['NTEE1'], org['NTEE1'], org['total_revenue'] or 0)).fetchone()
        if rank:
            org['category_rank'] = rank['higher_count'] + 1
            org['category_total'] = rank['total_in_cat']

    # Rank within state + NTEE (regional context)
    if org.get('NTEE1') and org.get('STATE'):
        state_rank = db.execute("""
            SELECT
                (SELECT COUNT(*) FROM registry_enriched WHERE STATE = ? AND NTEE1 = ?) as total_in_state,
                (SELECT COUNT(*) FROM registry_enriched WHERE STATE = ? AND NTEE1 = ? AND total_revenue > ?) as higher_in_state
        """, (org['STATE'], org['NTEE1'], org['STATE'], org['NTEE1'], org['total_revenue'] or 0)).fetchone()
        if state_rank and state_rank['total_in_state'] > 1:
            org['state_category_rank'] = state_rank['higher_in_state'] + 1
            org['state_category_total'] = state_rank['total_in_state']

    return jsonify(org)

@app.route('/api/organizations/<ein>/score-history')
@limiter.limit("60 per minute")
def get_score_history(ein):
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    db = get_db()
    rows = db.execute("""
        SELECT snapshot_date, peer_percentile, rev_pct, rsv_pct,
               reserve_ratio, total_revenue, total_assets,
               peer_group, group_key, group_size, scorer_version
        FROM score_snapshots
        WHERE EIN = ?
        ORDER BY snapshot_date ASC
    """, (ein_clean,)).fetchall()

    if not rows:
        return jsonify({"ein": ein_clean, "history": [], "total": 0})

    return jsonify({
        "ein": ein_clean,
        "history": [dict(r) for r in rows],
        "total": len(rows),
    })

@app.route('/api/organizations/<ein>/financials')
@limiter.limit("60 per minute")
def get_financials(ein):
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    db = get_db()
    rows = db.execute("""
        SELECT tax_prd_yr, totrevenue, totfuncexpns, totassetsend,
               totliabend, totnetassetend, totcntrbgfts, totprgmrevnue,
               compnsatncurrofcr, pdf_url
        FROM propublica_financials
        WHERE EIN = ?
        ORDER BY tax_prd_yr ASC
    """, (ein_clean,)).fetchall()

    return jsonify({
        "ein": ein_clean,
        "financials": [dict(r) for r in rows],
        "total": len(rows),
    })

@app.route('/api/ntee-categories')
@limiter.exempt
def ntee_categories():
    cached = _cget('ntee_cats', 'ntee')
    if cached: return jsonify(cached)
    db = get_db()
    rows = db.execute("""
        SELECT NTEE1 as code, COUNT(*) as count,
               ROUND(AVG(total_revenue),0) as avg_revenue
        FROM registry_enriched
        WHERE NTEE1 IS NOT NULL
        GROUP BY NTEE1
        ORDER BY count DESC
    """).fetchall()

    names = {
        'A':'Arts, Culture & Humanities','B':'Education','C':'Environment',
        'D':'Animal-Related','E':'Health','F':'Mental Health & Crisis',
        'G':'Voluntary Health Associations','H':'Medical Research',
        'I':'Crime & Legal-Related','J':'Employment',
        'K':'Food, Agriculture & Nutrition','L':'Housing & Shelter',
        'M':'Public Safety','N':'Recreation & Sports',
        'O':'Youth Development','P':'Human Services',
        'Q':'International','R':'Civil Rights & Advocacy',
        'S':'Community Improvement','T':'Philanthropy & Voluntarism',
        'U':'Science & Technology','V':'Social Science',
        'W':'Public & Societal Benefit','X':'Religion-Related',
        'Y':'Mutual & Membership','Z':'Unknown'
    }

    categories = []
    for row in rows:
        d = dict(row)
        d['name'] = names.get(d['code'], f"Category {d['code']}")
        categories.append(d)

    payload = {"categories": categories}
    _cset('ntee_cats', payload)
    return jsonify(payload)

# Only confirmed 501(c)(3) public charities where donations are tax-deductible.
# subsection='3' = 501(c)(3) status per IRS BMF (excludes c4, c6, c7, etc.)
# deductibility!='2' keeps confirmed-deductible (1), by-treaty (4), and unknown (0)
# while excluding the 3,379 orgs the IRS has explicitly marked non-deductible.
# Orgs with null subsection (NCCS-only, unverifiable) are excluded.
_DEDUCTIBILITY_FILTER = "subsection = '3' AND deductibility != '2'"

@app.route('/api/stats')
@limiter.exempt
def stats():
    cached = _cget('stats', 'stats')
    if cached: return jsonify(cached)
    db = get_db()
    f = _DEDUCTIBILITY_FILTER
    fin_count = db.execute("SELECT COUNT(*) FROM propublica_financials").fetchone()[0]
    reserve_stats = db.execute(f"""
        SELECT
            COUNT(CASE WHEN months_of_reserve IS NOT NULL THEN 1 END) as has_reserve,
            COUNT(CASE WHEN months_of_reserve < 0 THEN 1 END) as insolvent,
            COUNT(CASE WHEN months_of_reserve >= 0 AND months_of_reserve < 6 THEN 1 END) as at_risk,
            COUNT(CASE WHEN months_of_reserve >= 6 AND months_of_reserve < 12 THEN 1 END) as minimal,
            COUNT(CASE WHEN months_of_reserve >= 12 THEN 1 END) as healthy
        FROM registry_enriched WHERE {f}
    """).fetchone()
    payload = {
        "total_organizations": db.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {f}").fetchone()[0],
        "with_revenue": db.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {f} AND total_revenue > 0").fetchone()[0],
        "total_revenue_sum": db.execute(f"SELECT ROUND(SUM(total_revenue),0) FROM registry_enriched WHERE {f} AND total_revenue > 0").fetchone()[0],
        "avg_revenue": db.execute(f"SELECT ROUND(AVG(total_revenue),0) FROM registry_enriched WHERE {f} AND total_revenue > 0").fetchone()[0],
        "top_states": [dict(r) for r in db.execute(f"""
            SELECT STATE, COUNT(*) as count FROM registry_enriched
            WHERE {f} AND STATE IS NOT NULL GROUP BY STATE ORDER BY count DESC LIMIT 5
        """).fetchall()],
        "methodology_version": METHODOLOGY_VERSION,
        "scores_last_updated": db.execute(
            "SELECT MAX(snapshot_date) FROM score_snapshots"
        ).fetchone()[0],
        "financial_records": fin_count,
        "with_reserve_data": reserve_stats["has_reserve"] if reserve_stats else 0,
        "reserve_health": {
            "insolvent": reserve_stats["insolvent"] if reserve_stats else 0,
            "at_risk": reserve_stats["at_risk"] if reserve_stats else 0,
            "minimal": reserve_stats["minimal"] if reserve_stats else 0,
            "healthy": reserve_stats["healthy"] if reserve_stats else 0,
        },
    }
    _cset('stats', payload)
    return jsonify(payload)

@app.route('/api/sector-health')
@limiter.exempt
def sector_health():
    cached = _cget('sector_health', 'sector')
    if cached: return jsonify(cached)
    db = get_db()
    f = _DEDUCTIBILITY_FILTER
    rows = db.execute(f"""
        SELECT NTEE1 as code,
               COUNT(*) as total_orgs,
               COUNT(CASE WHEN months_of_reserve IS NOT NULL THEN 1 END) as has_reserve,
               ROUND(AVG(CASE WHEN months_of_reserve > -900 THEN months_of_reserve END), 1) as avg_months_reserve,
               COUNT(CASE WHEN months_of_reserve < 0 THEN 1 END) as insolvent,
               COUNT(CASE WHEN months_of_reserve >= 0 AND months_of_reserve < 3 THEN 1 END) as at_risk,
               COUNT(CASE WHEN months_of_reserve >= 3 AND months_of_reserve < 12 THEN 1 END) as minimal,
               COUNT(CASE WHEN months_of_reserve >= 12 THEN 1 END) as healthy,
               ROUND(AVG(CASE WHEN program_expense_pct IS NOT NULL AND program_expense_pct BETWEEN 0 AND 200 THEN program_expense_pct END), 1) as avg_program_pct,
               ROUND(AVG(CASE WHEN total_revenue > 0 THEN total_revenue END), 0) as avg_revenue
        FROM registry_enriched
        WHERE NTEE1 IS NOT NULL AND {f}
        GROUP BY NTEE1
        ORDER BY total_orgs DESC
    """).fetchall()

    names = {
        'A':'Arts, Culture & Humanities','B':'Education','C':'Environment',
        'D':'Animal-Related','E':'Health','F':'Mental Health & Crisis',
        'G':'Voluntary Health Associations','H':'Medical Research',
        'I':'Crime & Legal-Related','J':'Employment',
        'K':'Food, Agriculture & Nutrition','L':'Housing & Shelter',
        'M':'Public Safety','N':'Recreation & Sports',
        'O':'Youth Development','P':'Human Services',
        'Q':'International','R':'Civil Rights & Advocacy',
        'S':'Community Improvement','T':'Philanthropy & Voluntarism',
        'U':'Science & Technology','V':'Social Science',
        'W':'Public & Societal Benefit','X':'Religion-Related',
        'Y':'Mutual & Membership','Z':'Unknown'
    }

    result = []
    for row in rows:
        d = dict(row)
        d['name'] = names.get(d['code'], f"Category {d['code']}")
        total = d['has_reserve'] or 1
        d['at_risk_pct'] = round((d['insolvent'] + d['at_risk']) / d['total_orgs'] * 100, 1)
        result.append(d)

    payload = {"sectors": result}
    _cset('sector_health', payload)
    return jsonify(payload)

@app.route('/api/scoring-runs')
@limiter.limit("20 per minute")
@require_admin_key
def scoring_runs():
    db = get_db()
    try:
        rows = db.execute(
            """SELECT run_id, scorer_version, started_at, completed_at,
                      input_ein_count, scorable_count, output_ein_count,
                      peer_group_count, score_min, score_max, score_mean,
                      score_median, band_distribution, notes, git_commit
               FROM scoring_runs
               ORDER BY started_at DESC
               LIMIT 50"""
        ).fetchall()
    except Exception:
        return jsonify({"error": "scoring_runs table not yet created — run scripts/scoring_audit.py --backfill-initial"}), 404

    runs = []
    for r in rows:
        d = dict(r)
        if d.get("band_distribution"):
            try:
                d["band_distribution"] = json.loads(d["band_distribution"])
            except Exception:
                pass
        runs.append(d)
    return jsonify({"scoring_runs": runs, "count": len(runs)})


_VALID_SOURCES  = {'newsletter', 'claiming'}
_VALID_STATUSES = {'new', 'contacted', 'converted', 'dismissed'}

@app.route('/api/waitlist', methods=['POST'])
def waitlist_submit():
    data  = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower()[:200]
    ein   = str(data.get('ein',   '')).strip()[:20] or None
    source = str(data.get('source', 'newsletter')).strip()
    if not email or '@' not in email:
        return jsonify({'error': 'valid email required'}), 400
    if source not in _VALID_SOURCES:
        source = 'newsletter'
    db = get_db()
    cur = db.execute(
        "INSERT INTO waitlist (email, ein, source) VALUES (?, ?, ?)",
        (email, ein, source),
    )
    db.commit()
    return jsonify({'ok': True, 'id': cur.lastrowid}), 201


_VALID_LINK_REASONS = {'not_found', 'broken'}

@app.route('/api/link-feedback', methods=['POST'])
@limiter.limit("30 per minute")
def link_feedback_submit():
    # Anonymous. We deliberately accept and store ONLY ein + reason.
    # No email, no IP, no donor data. Only actionable reasons are sent
    # by the client; reject anything else so this stays a findability
    # signal, not behavioral tracking.
    data   = request.get_json(silent=True) or {}
    ein    = ''.join(c for c in str(data.get('ein', '')) if c.isdigit())[:10]
    reason = str(data.get('reason', '')).strip()[:20]
    if not ein or reason not in _VALID_LINK_REASONS:
        return jsonify({'error': 'ein and a valid reason required'}), 400
    db = get_db()
    db.execute(
        "INSERT INTO link_feedback (EIN, reason) VALUES (?, ?)",
        (ein, reason),
    )
    db.commit()
    return ('', 204)


@app.route('/api/admin/waitlist', methods=['GET'])
@require_admin_key
def admin_waitlist_list():
    source = request.args.get('source', '').strip()
    status = request.args.get('status', '').strip()
    limit  = min(int(request.args.get('limit',  200)), 500)
    offset = max(int(request.args.get('offset', 0)),   0)
    where, params = [], []
    if source in _VALID_SOURCES:
        where.append('source = ?'); params.append(source)
    if status in _VALID_STATUSES:
        where.append('status = ?'); params.append(status)
    clause = ('WHERE ' + ' AND '.join(where)) if where else ''
    db = get_db()
    total   = db.execute(f"SELECT COUNT(*) FROM waitlist {clause}", params).fetchone()[0]
    rows    = db.execute(
        f"SELECT * FROM waitlist {clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    return jsonify({'entries': [dict(r) for r in rows], 'total': total})


@app.route('/api/admin/waitlist/<int:wid>', methods=['PATCH'])
@require_admin_key
def admin_waitlist_update(wid):
    data   = request.get_json(silent=True) or {}
    status = str(data.get('status', '')).strip()
    notes  = data.get('notes')
    sets, params = [], []
    if status in _VALID_STATUSES:
        sets.append('status = ?'); params.append(status)
    if notes is not None:
        sets.append('notes = ?'); params.append(str(notes)[:1000])
    if not sets:
        return jsonify({'error': 'nothing to update'}), 400
    params.append(wid)
    db = get_db()
    db.execute(f"UPDATE waitlist SET {', '.join(sets)} WHERE id = ?", params)
    db.commit()
    row = db.execute("SELECT * FROM waitlist WHERE id = ?", (wid,)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(dict(row))


@app.route('/api/admin/waitlist/<int:wid>', methods=['DELETE'])
@require_admin_key
def admin_waitlist_delete(wid):
    db = get_db()
    db.execute("DELETE FROM waitlist WHERE id = ?", (wid,))
    db.commit()
    return jsonify({'ok': True})


def _fetch_orgs_by_eins(db, eins: list[str]) -> list[dict]:
    if not eins:
        return []
    cols = """EIN, organization_name, CITY, STATE, total_revenue,
              ntee1_percentile, peer_percentile, peer_group, revenue_band,
              latest_tax_year, data_source, updated_at,
              merit_tier, merit_score, merit_band"""
    placeholders = ",".join("?" * len(eins))
    rows = db.execute(
        f"SELECT {cols} FROM registry_enriched WHERE EIN IN ({placeholders})", eins
    ).fetchall()
    order = {e: i for i, e in enumerate(eins)}
    return sorted([dict(r) for r in rows], key=lambda r: order.get(r["EIN"], 999))


def _find_similar_orgs(db, ein_clean, org, limit=6):
    """Similar orgs: vector cosine similarity when available, SQL bucket fallback."""
    cols = """EIN, organization_name, CITY, STATE, total_revenue,
              ntee1_percentile, peer_percentile, peer_group, revenue_band,
              latest_tax_year, data_source, updated_at,
              merit_tier, merit_score, merit_band"""

    # ── Vector path ────────────────────────────────────────────────────────────
    vec = _get_org_vec(ein_clean)
    if vec is not None and _emb_matrix is not None:
        top_eins = _vec_similar(vec, ein_clean, limit)
        results  = _fetch_orgs_by_eins(db, top_eins)
        if len(results) >= 3:
            return results, 'vector'

    # ── SQL fallback ───────────────────────────────────────────────────────────
    pct   = org.get('peer_percentile') or org.get('ntee1_percentile', 50) or 50
    nteecc = org.get('NTEECC')
    band   = org.get('revenue_band')
    ntee1  = org.get('NTEE1')

    if nteecc and band:
        rows = db.execute(f"""
            SELECT {cols} FROM registry_enriched
            WHERE NTEECC = ? AND revenue_band = ? AND EIN != ?
            ORDER BY ABS(COALESCE(peer_percentile, 50) - ?) ASC LIMIT ?
        """, (nteecc, band, ein_clean, pct, limit)).fetchall()
        if len(rows) >= 3:
            return [dict(r) for r in rows], 'nteecc+band'

    if ntee1 and band:
        rows = db.execute(f"""
            SELECT {cols} FROM registry_enriched
            WHERE NTEE1 = ? AND revenue_band = ? AND EIN != ?
            ORDER BY ABS(COALESCE(peer_percentile, ntee1_percentile, 50) - ?) ASC LIMIT ?
        """, (ntee1, band, ein_clean, pct, limit)).fetchall()
        if len(rows) >= 2:
            return [dict(r) for r in rows], 'ntee1+band'

    if ntee1:
        rows = db.execute(f"""
            SELECT {cols} FROM registry_enriched
            WHERE NTEE1 = ? AND EIN != ?
            ORDER BY ABS(COALESCE(peer_percentile, ntee1_percentile, 50) - ?) ASC LIMIT ?
        """, (ntee1, ein_clean, pct, limit)).fetchall()
        return [dict(r) for r in rows], 'ntee1'

    return [], 'none'


@app.route('/api/organizations/<ein>/similar')
@limiter.limit("60 per minute")
def get_similar_organizations(ein):
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    try:
        limit = min(int(request.args.get('limit', 6)), 12)
    except (ValueError, TypeError):
        limit = 6

    db = get_db()
    row = db.execute("SELECT * FROM registry_enriched WHERE EIN = ?", (ein_clean,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404

    org = dict(row)
    results, mode = _find_similar_orgs(db, ein_clean, org, limit=limit)
    return jsonify({'results': results, 'mode': mode, 'diamonds_only': False})


# ── Semantic search ────────────────────────────────────────────────────────────
@app.route('/api/search/semantic')
@limiter.limit("30 per minute")
def semantic_search():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({"error": "q param required"}), 400
    try:
        limit = min(int(request.args.get('limit', 10)), 25)
    except (ValueError, TypeError):
        limit = 10

    if not _emb_loaded:
        _load_embeddings()
    if _emb_matrix is None or len(_emb_matrix) == 0:
        return jsonify({"error": "embeddings not ready yet", "results": []}), 503

    vec = _embed_query(q)
    if vec is None:
        return jsonify({"error": "embedding service unavailable"}), 503

    top_eins = _vec_similar(vec, exclude_ein="", limit=limit)
    db = get_db()
    results  = _fetch_orgs_by_eins(db, top_eins)
    return jsonify({"results": results, "query": q, "mode": "semantic", "total": len(results)})


# ── Frontend static serving ────────────────────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, 'index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
