#!/usr/bin/env python3
"""
MeritGiving API — Serves registry_enriched to frontend
"""
import sqlite3, os, json, functools, struct
import numpy as np
from flask import Flask, jsonify, request, g, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Scoring methodology version — the formula/algorithm. Changes rarely, and
# only when the scoring logic itself changes (not on data refreshes). The
# score-computation DATE is read dynamically from score_snapshots.
METHODOLOGY_VERSION = "v1"

# Lazy-loaded semantic search components (only initialised on first use)
_embed_model = None
_vec_ready   = None   # True/False/None (None = not yet checked)

def _get_embed_model():
    global _embed_model, _vec_ready
    if _vec_ready is False:
        return None
    if _embed_model is not None:
        return _embed_model
    try:
        import sqlite_vec
        from sentence_transformers import SentenceTransformer
        import torch
        # CPU only: we encode one query sentence per request (~50ms).
        # GPU would help document embedding (already done at build time) but
        # causes ROCm multi-process contention across gunicorn workers.
        _embed_model = SentenceTransformer("BAAI/bge-large-en-v1.5", device="cpu")
        _vec_ready = True
        print("[semantic] model loaded on cpu")
    except Exception as e:
        print(f"[semantic] not available: {e}")
        _vec_ready = False
    return _embed_model

app = Flask(__name__)

# Restrict CORS to known origins; add production domain when deploying
_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",
    "https://meritgiving.org",
    "https://www.meritgiving.org",
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
        try:
            import sqlite_vec
            db.enable_load_extension(True)
            sqlite_vec.load(db)
            db.enable_load_extension(False)
        except Exception:
            pass
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
    db = get_db()
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('q', '').strip()[:200]
    ntee = request.args.get('ntee', '').strip().upper()[:2]
    sub = request.args.get('sub', '').strip().upper()[:4]   # NTEECC subcategory e.g. E21
    state = request.args.get('state', '').strip().upper()[:2]
    min_rev = request.args.get('min_revenue', type=float)
    max_rev = request.args.get('max_revenue', type=float)
    min_pct = request.args.get('min_percentile', type=float)
    min_merit_tier = request.args.get('min_merit_tier', '').strip()
    hidden_gem = request.args.get('hidden_gem', '').strip() == '1'
    cause = request.args.get('cause', '').strip()[:60]
    sort_by = request.args.get('sort', 'total_revenue')
    order = request.args.get('order', 'desc')

    offset = (page - 1) * per_page

    # Always restrict to 501(c)(3) orgs with deductible donations
    where_clauses = list(_DEDUCTIBILITY_FILTER.split(" AND "))
    params = []

    if search:
        # Split into words — each must appear independently in name, city, or EIN
        # This makes search word-order-independent and lets users search "Khan Foundation" or "Foundation Khan"
        words = [w for w in search.split() if w]
        for word in words:
            where_clauses.append("(organization_name LIKE ? OR EIN LIKE ? OR CITY LIKE ?)")
            params.extend([f'%{word}%', f'%{word}%', f'%{word}%'])
    if ntee:
        where_clauses.append("NTEE1 = ?")
        params.append(ntee)
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
    if cause:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM json_each(cause_tags) WHERE value LIKE ?)"
        )
        params.append(f'%{cause}%')

    _TIER_HIERARCHY = ['Beacon', 'Lantern', 'Flame', 'Ember', 'Spark']
    if min_merit_tier and min_merit_tier in _TIER_HIERARCHY:
        idx = _TIER_HIERARCHY.index(min_merit_tier)
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
               months_of_reserve, net_assets, total_expenses,
               employee_count, ruling_date, zipcode, is_hidden_gem, cause_tags,
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

    return jsonify({
        "organizations": orgs,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    })

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
    org['total_revenue_formatted'] = f"${org['total_revenue']:,.0f}" if org['total_revenue'] else None

    # Parse JSON text columns → Python lists
    if org.get('cause_tags'):
        try:
            org['cause_tags'] = json.loads(org['cause_tags'])
        except (json.JSONDecodeError, TypeError):
            org['cause_tags'] = None

    # Similar orgs: prefer same NTEECC + revenue_band, fall back to NTEE1
    peer_group = org.get('peer_group') or ''
    if ':' in peer_group:
        # e.g. "B24:Medium" — match subcategory + band
        nteecc_part, band_part = peer_group.split(':', 1)
        similar = db.execute("""
            SELECT EIN, organization_name, CITY, STATE, total_revenue,
                   ntee1_percentile, peer_percentile, peer_group, revenue_band,
                   latest_tax_year, data_source, updated_at,
                   merit_tier, merit_score, merit_band
            FROM registry_enriched
            WHERE NTEECC LIKE ? AND revenue_band = ? AND EIN != ?
            ORDER BY ABS(COALESCE(peer_percentile, 50) - ?) ASC
            LIMIT 5
        """, (nteecc_part + '%', band_part, ein_clean,
              org.get('peer_percentile') or org.get('ntee1_percentile', 50))).fetchall()
    else:
        similar = db.execute("""
            SELECT EIN, organization_name, CITY, STATE, total_revenue,
                   ntee1_percentile, peer_percentile, peer_group, revenue_band,
                   latest_tax_year, data_source, updated_at,
                   merit_tier, merit_score, merit_band
            FROM registry_enriched
            WHERE NTEE1 = ? AND EIN != ?
            ORDER BY ABS(COALESCE(peer_percentile, ntee1_percentile, 50) - ?) ASC
            LIMIT 5
        """, (org.get('NTEE1'), ein_clean,
              org.get('peer_percentile') or org.get('ntee1_percentile', 50))).fetchall()
    org['similar_organizations'] = [dict(r) for r in similar]

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

    return jsonify({"categories": categories})

_DEDUCTIBILITY_FILTER = (
    "(subsection = '3' OR subsection IS NULL OR subsection = '')"
    " AND (deductibility != '2' OR deductibility IS NULL OR deductibility = '')"
)

@app.route('/api/stats')
@limiter.exempt
def stats():
    db = get_db()
    f = _DEDUCTIBILITY_FILTER
    fin_count = db.execute("SELECT COUNT(*) FROM propublica_financials").fetchone()[0]
    reserve_stats = db.execute(f"""
        SELECT
            COUNT(CASE WHEN months_of_reserve IS NOT NULL THEN 1 END) as has_reserve,
            COUNT(CASE WHEN months_of_reserve < 0 THEN 1 END) as insolvent,
            COUNT(CASE WHEN months_of_reserve >= 0 AND months_of_reserve < 3 THEN 1 END) as at_risk,
            COUNT(CASE WHEN months_of_reserve >= 3 AND months_of_reserve < 12 THEN 1 END) as minimal,
            COUNT(CASE WHEN months_of_reserve >= 12 THEN 1 END) as healthy
        FROM registry_enriched WHERE {f}
    """).fetchone()
    return jsonify({
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
    })

@app.route('/api/sector-health')
@limiter.exempt
def sector_health():
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

    return jsonify({"sectors": result})

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


@app.route('/api/search/semantic')
@limiter.limit("30 per minute")
def semantic_search():
    """
    Natural-language search across all orgs using BAAI/bge-large-en-v1.5 embeddings.
    Returns orgs ranked by semantic similarity to the query.

    Query params:
        q        — required, natural language query (e.g. "food banks helping families in Texas")
        limit    — max results (default 20, max 50)
        ntee     — optional NTEE1 filter letter
        state    — optional two-letter state filter
    """
    q = request.args.get('q', '').strip()[:500]
    if not q:
        return jsonify({"error": "q is required"}), 400

    limit  = min(request.args.get('limit', 20, type=int), 50)
    ntee   = request.args.get('ntee', '').strip().upper()[:2]
    state  = request.args.get('state', '').strip().upper()[:2]

    model = _get_embed_model()
    if model is None:
        return jsonify({"error": "Semantic search not yet available — embeddings are still being built."}), 503

    # Check embeddings table exists and has rows
    db = get_db()
    try:
        count = db.execute("SELECT COUNT(*) FROM org_embeddings_meta").fetchone()[0]
        if count == 0:
            return jsonify({"error": "Embeddings not yet built. Run scripts/build_embeddings.py first."}), 503
    except Exception:
        return jsonify({"error": "Embeddings not yet built. Run scripts/build_embeddings.py first."}), 503

    # Encode query (CPU, ~50ms for one sentence)
    try:
        vec = model.encode([q], normalize_embeddings=True)[0]
        vec_bytes = struct.pack(f"{len(vec)}f", *vec.tolist())
    except Exception as e:
        return jsonify({"error": f"Query encoding failed: {e}"}), 500

    # KNN search — fetch more than needed so we can filter by ntee/state
    k_fetch = min(limit * 5, 250)
    try:
        knn_rows = db.execute("""
            SELECT e.ein, distance
            FROM org_embeddings e
            WHERE embedding MATCH ? AND k = ?
            ORDER BY distance
        """, (vec_bytes, k_fetch)).fetchall()
    except Exception as ex:
        return jsonify({"error": f"Vector search failed: {ex}"}), 500

    if not knn_rows:
        return jsonify({"results": [], "query": q, "mode": "semantic"})

    # Hydrate with org details and apply optional filters
    eins = [r["ein"] for r in knn_rows]
    dist_map = {r["ein"]: float(r["distance"]) for r in knn_rows}

    placeholders = ",".join("?" * len(eins))
    where_extra = ""
    extra_params = []
    if ntee:
        where_extra += " AND NTEE1 = ?"
        extra_params.append(ntee)
    if state:
        where_extra += " AND STATE = ?"
        extra_params.append(state)

    rows = db.execute(f"""
        SELECT EIN, organization_name, NTEE1, CITY, STATE,
               total_revenue, ntee1_percentile,
               latest_tax_year, data_source, mission
        FROM registry_enriched
        WHERE EIN IN ({placeholders}){where_extra}
    """, eins + extra_params).fetchall()

    # Sort by vector distance (lower = more similar)
    results = sorted(
        [dict(r) for r in rows],
        key=lambda r: dist_map.get(r["EIN"], 999)
    )[:limit]

    for r in results:
        r["similarity_score"] = round(1 - dist_map.get(r["EIN"], 1), 4)
        r["total_revenue_formatted"] = f"${r['total_revenue']:,.0f}" if r.get("total_revenue") else None

    return jsonify({
        "results":       results,
        "query":         q,
        "mode":          "semantic",
        "total_indexed": count,
    })


@app.route('/api/search/semantic/status')
@limiter.exempt
def semantic_status():
    """How many orgs are embedded so far."""
    db = get_db()
    try:
        indexed = db.execute("SELECT COUNT(*) FROM org_embeddings_meta").fetchone()[0]
        total   = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
        return jsonify({
            "indexed": indexed,
            "total":   total,
            "pct":     round(indexed / total * 100, 1) if total else 0,
            "ready":   indexed > 10000,
        })
    except Exception:
        return jsonify({"indexed": 0, "total": 0, "pct": 0, "ready": False})


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
