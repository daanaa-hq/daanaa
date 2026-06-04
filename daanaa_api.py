#!/usr/bin/env python3
"""
Daanaa API — Peer-context nonprofit directory backend
Serves registry_enriched + v4 scores to frontend
"""
import sqlite3, os, json, functools, time, hashlib, hmac, threading, re, secrets
import numpy as np
import requests as _http
from flask import Flask, jsonify, request, g, abort, send_from_directory, Blueprint
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def _real_ip() -> str:
    # Cloudflare sets CF-Connecting-IP; fall back to X-Forwarded-For, then REMOTE_ADDR.
    # Without this, every request appears to come from Cloudflare's IP and rate limiting
    # is useless (all visitors share one bucket).
    return (
        request.headers.get('CF-Connecting-IP') or
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or
        get_remote_address()
    )

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')

# Scoring methodology version — the formula/algorithm. Changes rarely, and
# only when the scoring logic itself changes (not on data refreshes). The
# score-computation DATE is read dynamically from score_snapshots.
METHODOLOGY_VERSION = "v1"

# ── Legal Disclosures ──────────────────────────────────────────────────────────
# Attached to all responses containing scores
SCORE_DISCLAIMER = (
    "⚠️ Financial Health is a peer-group ranking relative to similar organizations. "
    "It does NOT evaluate mission impact, program quality, governance, or legitimacy. "
    "Always verify information independently before donating. "
    "See daanaa.org/methodology for full limitations."
)

UNSCORED_DISCLOSURE = (
    "🔍 No Financial Data Available: This organization lacks revenue/expense data in IRS records. "
    "This does NOT indicate unhealthiness. Verify directly: check IRS.gov 501(c)(3) status, "
    "ask for Form 990, or contact them. "
    "Help us score them: claim a page and add financial data at daanaa.org/for-nonprofits"
)

SELF_REPORTED_DISCLAIMER = (
    "⚠️ Self-Reported Data: This financial information was submitted by the organization. "
    "We have NOT independently verified these figures. Recommend requesting Form 990 directly. "
    "Daanaa assumes no liability for accuracy."
)

BETA_WEBSITE_DISCLOSURE = (
    "🔍 Website discovered via heuristic search and verified to exist, but NOT confirmed by the organization. "
    "Always verify on their official channels before using. "
    "Organizations can claim and update their information at daanaa.org/for-nonprofits"
)

BETA_DONATION_LINK_DISCLOSURE = (
    "🔍 Donation link discovered automatically and NOT verified by the organization. "
    "Always confirm this link on their official website before giving. "
    "Help us verify: claim your profile at daanaa.org/for-nonprofits"
)

# ── Response cache ─────────────────────────────────────────────────────────────
# Simple in-process time-keyed cache. Keys are strings, values are (payload, ts).
# TTLs chosen per endpoint volatility. No external dependency (no Redis).
_CACHE: dict = {}
_CACHE_TTL = {
    'ntee':   7200,   # 2 h — static category list
    'stats':   900,   # 15 min — aggregate counts
    'sector': 1800,   # 30 min — reserve health breakdown
    'search': 1800,   # 30 min — directory search results (was 5m; search patterns repeat frequently)
    'org':    1800,   # 30 min — individual org detail (was 10m)
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

# ── Embedding index (eager-loaded at startup, module-level singleton) ──────────
# Loaded once in gunicorn master (--preload) then CoW-shared across workers.
# ~7.4 GB for 1.8M orgs × 1024-dim float32. Falls back gracefully if missing.
_emb_matrix: np.ndarray | None = None   # (N, 768) L2-normalised float32
_emb_eins:   list | None       = None   # parallel EIN list, index = row
_emb_index:  dict | None       = None   # EIN → row index
_emb_lock = threading.Lock()
_emb_loaded = False

VULKAN_EMBED_URL  = "http://127.0.0.1:11436/v1/embeddings"   # llama-server Vulkan1 (primary)
OLLAMA_EMBED_URL  = "http://localhost:11434/api/embed"         # Ollama fallback
OLLAMA_EMBED_MODEL = "mxbai-embed-large"

# ── FTS5 full-text search ───────────────────────────────────────────────────────
# Set True once we confirm org_fts exists. Checked at first search request.
_fts_available: bool | None = None  # None = not yet checked

_FTS5_STRIP = re.compile(r'[*"^(){}|<>&~\[\]]')

def _sanitize_fts_query(text: str) -> str:
    """Convert a donor query string to FTS5 MATCH syntax.
    Each word becomes a prefix token (cancer* matches cancer, cancers).
    Multiple words are implicitly ANDed by FTS5."""
    clean = _FTS5_STRIP.sub(' ', text)
    words = [w.strip() for w in clean.split() if len(w.strip()) >= 2]
    if not words:
        return '""'
    return ' '.join(f'{w}*' for w in words)

def _check_fts(db: sqlite3.Connection) -> bool:
    global _fts_available
    if _fts_available is not None:
        return _fts_available
    try:
        db.execute("SELECT COUNT(*) FROM org_fts LIMIT 1")
        _fts_available = True
    except Exception:
        _fts_available = False
    return _fts_available

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
    """Load scored-org embeddings into RAM.

    Scoped to orgs with a merit_score (~546K) to keep peak RAM under 3 GB.
    Pre-allocates the numpy matrix and streams the cursor row-by-row to avoid
    the double-peak that fetchall() causes (raw bytes + array simultaneously).
    """
    global _emb_matrix, _emb_eins, _emb_index, _emb_loaded
    with _emb_lock:
        if _emb_loaded:
            return
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            # Count first so we can pre-allocate
            n, dim = conn.execute(
                "SELECT COUNT(*), MAX(dim) FROM org_embeddings e "
                "JOIN registry_enriched r ON e.ein = r.EIN "
                "WHERE r.merit_score IS NOT NULL"
            ).fetchone()
            if not n:
                conn.close()
                return
            mat  = np.empty((n, dim), dtype=np.float32)
            eins = []
            cur  = conn.execute(
                "SELECT e.ein, e.vector FROM org_embeddings e "
                "JOIN registry_enriched r ON e.ein = r.EIN "
                "WHERE r.merit_score IS NOT NULL "
                "ORDER BY e.rowid"
            )
            for i, (ein, vec) in enumerate(cur):
                mat[i] = np.frombuffer(vec, dtype=np.float32)
                eins.append(ein)
            conn.close()
            _emb_eins   = eins
            _emb_index  = {e: i for i, e in enumerate(eins)}
            _emb_matrix = mat
            _emb_loaded = True
            print(f"[embeddings] loaded {len(eins):,} scored vectors ({dim}-dim)", flush=True)
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
    """Embed a query string via llama-server Vulkan1, falling back to Ollama."""
    # Primary: llama-server on port 11436 (mxbai-embed-large, Vulkan1 / R9700)
    try:
        r = _http.post(VULKAN_EMBED_URL,
                       json={"model": "mxbai-embed-large", "input": text},
                       timeout=5)
        r.raise_for_status()
        vec = np.array(r.json()["data"][0]["embedding"], dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec
    except Exception:
        pass
    # Fallback: Ollama
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
    key_func=_real_ip,
    app=app,
    default_limits=["200 per minute", "2000 per hour"],
    storage_uri="memory://",
)

DB_PATH = os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/merit_registry.db"))

# User-generated / write-path data lives in a SEPARATE database so the daily
# catalog sync (which overwrites DB_PATH from the home pipeline) never wipes it.
# On the droplet LIVE_DB_PATH points to data/daanaa_live.db; locally it defaults
# to DB_PATH (single-file, no split). When the two differ, get_db() ATTACHes the
# live DB as `live` and bare table names resolve there (the catalog must NOT
# contain these tables — the sync drops them). No per-query rewrites needed.
LIVE_DB_PATH = os.environ.get("LIVE_DB_PATH", DB_PATH)
_LIVE_SPLIT = os.path.abspath(LIVE_DB_PATH) != os.path.abspath(DB_PATH)

# ── Feature flags ─────────────────────────────────────────────────────────────
# ENABLE_SCORES=false → null out merit_score / merit_tier / merit_band in all
# org responses. Allows a clean no-scores preview of the directory.
# Default: true (scores are on). Toggle: ENABLE_SCORES=false python3 merit_api.py
ENABLE_SCORES: bool = os.environ.get("ENABLE_SCORES", "true").lower() == "true"

# ENABLE_V4_SCORES=true → include v4.0 financial health scores (financial_health,
# operating_model, revenue_band, peer_cell_size) in org responses.
# Default: true (v4 scores enabled). Toggle: ENABLE_V4_SCORES=false python3 merit_api.py
ENABLE_V4_SCORES: bool = os.environ.get("ENABLE_V4_SCORES", "true").lower() == "true"

# ENABLE_V4_METRICS=true → include detailed metrics_json and percentiles_json
# in v4 responses (transparency/audit trail). Default: false.
ENABLE_V4_METRICS: bool = os.environ.get("ENABLE_V4_METRICS", "false").lower() == "true"

_SCORE_FIELDS = ("merit_score", "merit_tier", "merit_band")
_V4_FIELDS = ("financial_health", "operating_model", "revenue_band", "peer_cell_size")

def _strip_scores(org: dict) -> dict:
    """Null out score fields in an org dict when ENABLE_SCORES is false."""
    if ENABLE_SCORES:
        return org
    return {k: (None if k in _SCORE_FIELDS else v) for k, v in org.items()}

def _attach_v4_scores(org: dict, v4_row: sqlite3.Row | None) -> dict:
    """Attach v4.0 financial health scores to org response if available and enabled."""
    if not ENABLE_V4_SCORES or v4_row is None:
        return org
    v4 = dict(v4_row)
    org['visibility_tier'] = v4.get('visibility_tier')
    org['financial_health'] = v4.get('financial_health')
    org['operating_model'] = v4.get('operating_model')
    org['revenue_band'] = v4.get('revenue_band')
    org['peer_cell_size'] = v4.get('peer_cell_size')
    if ENABLE_V4_METRICS and v4.get('metrics_json'):
        try:
            org['v4_metrics'] = json.loads(v4['metrics_json'])
        except (json.JSONDecodeError, TypeError):
            pass
    return org

# ─────────────────────────────────────────────────────────────────────────────

# Claim verification — opaque HMAC token so raw PIN never appears in URLs.
# Set DAANAA_CLAIM_SECRET in production; falls back to admin key then dev default.
_CLAIM_SECRET = (
    os.environ.get("DAANAA_CLAIM_SECRET")
    or os.environ.get("DAANAA_ADMIN_KEY")
    or "daanaa-dev-claim-secret"
).encode()

def _make_verify_token(ein: str, pin: str) -> str:
    """Return HMAC-SHA256 hex token for the given EIN + PIN pair."""
    return hmac.new(_CLAIM_SECRET, f"{ein}:{pin}".encode(), hashlib.sha256).hexdigest()

# Admin key — set DAANAA_ADMIN_KEY env var before starting the API.
# Backward compatible with old MERIT_ADMIN_KEY env var name.
# Any endpoint decorated with @require_admin_key will return 401 if it's missing or wrong.
_ADMIN_KEY = (
    os.environ.get("DAANAA_ADMIN_KEY", "")
    or os.environ.get("MERIT_ADMIN_KEY", "")  # backward compat
)

def require_admin_key(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        provided = request.headers.get("X-Admin-Key", "")
        if not _ADMIN_KEY or not hmac.compare_digest(provided, _ADMIN_KEY):
            abort(401)
        return f(*args, **kwargs)
    return wrapper

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        if _LIVE_SPLIT:
            db.execute("ATTACH DATABASE ? AS live", (LIVE_DB_PATH,))
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def _init_waitlist_table():
    with sqlite3.connect(LIVE_DB_PATH) as db:
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
    with sqlite3.connect(LIVE_DB_PATH) as db:
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


def _init_donate_handoffs_table():
    # Anonymous, aggregate-only impact signal: a daily per-org tally of "give"
    # hand-offs. NO donor identity, NO IP, NO amount, NO link to any wallet —
    # just a count of how often a donate hand-off was initiated. INTERNAL ONLY:
    # never surface per-org counts publicly (that would create popularity /
    # social-pressure mechanics — STEWARDSHIP principles 2 and 5). Used only for
    # aggregate realized-impact measurement.
    with sqlite3.connect(LIVE_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS donate_handoffs (
                ein    TEXT NOT NULL,
                day    TEXT NOT NULL,
                count  INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (ein, day)
            )
        """)
        db.commit()

_init_donate_handoffs_table()


def _init_org_interest_table():
    # Anonymous demand signal: how many people expressed intent to DONATE or
    # VOLUNTEER for an org (especially unclaimed ones). Aggregate count only —
    # NO donor identity, NO IP, NO contact info. Shown ONLY to the organization
    # when it claims its page (a reason to claim + a starting point), never
    # publicly (avoids social-pressure / popularity mechanics, principles 2 & 5).
    with sqlite3.connect(LIVE_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS org_interest (
                ein    TEXT NOT NULL,
                kind   TEXT NOT NULL,
                count  INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (ein, kind)
            )
        """)
        db.commit()

_init_org_interest_table()


def _init_org_claims_table():
    with sqlite3.connect(LIVE_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS org_claims (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                ein              TEXT NOT NULL UNIQUE,
                email            TEXT NOT NULL,
                irs_address      TEXT NOT NULL,
                pin              TEXT NOT NULL,
                pin_expires_at   TEXT NOT NULL,
                letter_sent_at   TEXT,
                lob_letter_id    TEXT,
                claim_status     TEXT DEFAULT 'pending',
                verified_at      TEXT,
                custom_mission   TEXT,
                custom_description TEXT,
                donate_confirmed INTEGER DEFAULT 0,
                processor_auth   INTEGER DEFAULT 0,
                created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
                revoked_at       TEXT,
                revoke_reason    TEXT
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_org_claims_ein ON org_claims(ein)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_org_claims_status ON org_claims(claim_status)")
        db.commit()

_init_org_claims_table()


def _init_feedback_table():
    # Site feedback: a free-text message, an OPTIONAL email (only if the visitor
    # wants to be kept posted), and the page they were on. No IP, no tracking, no
    # identity. Anonymous by default. Lives in the live DB (survives catalog sync).
    with sqlite3.connect(LIVE_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT,
                message     TEXT NOT NULL,
                email       TEXT,
                page        TEXT,
                status      TEXT NOT NULL DEFAULT 'new',
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migration for feedback tables created before `category` existed.
        try:
            db.execute("ALTER TABLE feedback ADD COLUMN category TEXT")
        except sqlite3.OperationalError:
            pass  # column already present
        db.commit()

_init_feedback_table()


def _init_analytics_tables():
    # Privacy-first, FIRST-PARTY, AGGREGATE-ONLY analytics. No cookies, no IP, no
    # persistent ID, no individual session record. We count events, never people.
    #   analytics_daily  — per-day per-path event counts + summed dwell seconds
    #   analytics_search — per-day search-term counts (what people look for)
    #   visit_counter    — a single hidden (admin-only) running tally; "sessions"
    #                      is incremented once per browser session via a
    #                      sessionStorage flag (no server-side identity at all).
    with sqlite3.connect(LIVE_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS analytics_daily (
                day          TEXT NOT NULL,
                path         TEXT NOT NULL,
                event_type   TEXT NOT NULL,
                count        INTEGER NOT NULL DEFAULT 0,
                dwell_secs   INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (day, path, event_type)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS analytics_search (
                day    TEXT NOT NULL,
                term   TEXT NOT NULL,
                count  INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (day, term)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS visit_counter (
                metric  TEXT PRIMARY KEY,
                count   INTEGER NOT NULL DEFAULT 0
            )
        """)
        db.execute("INSERT OR IGNORE INTO visit_counter (metric, count) VALUES ('pageviews', 0)")
        db.execute("INSERT OR IGNORE INTO visit_counter (metric, count) VALUES ('sessions', 0)")
        db.commit()

_init_analytics_tables()


def _init_revoked_eins_table():
    # IRS Automatic Revocation of Exemption list. An org here has LOST its tax-
    # exempt status — we must NEVER present a donate path for it (G2 gate). This
    # is CATALOG/reference data (lives in DB_PATH, synced from the home pipeline
    # by scripts/ingest_auto_revocation.py), NOT user-write data — so it is not
    # in the live-DB split. Empty until the ingestion script populates it.
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS revoked_eins (
                ein                     TEXT PRIMARY KEY,
                revocation_date         TEXT,
                revocation_posting_date TEXT,
                source                  TEXT DEFAULT 'irs_auto_revocation'
            )
        """)
        db.commit()

_init_revoked_eins_table()

# Prevent absurdly large payloads on any endpoint
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # 64 KB

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # CSP: load-bearing for wallet privacy — blocks XSS from reading localStorage.
    # 'unsafe-inline' on style-src only (Tailwind class-based; React may inject style attrs).
    is_prod = bool(os.environ.get("DAANAA_PROD"))
    # In prod, connect-src is HTTPS origins only; localhost is dev-only.
    connect_src = (
        "connect-src 'self' https://daanaa.org https://www.daanaa.org; "
        if is_prod else
        "connect-src 'self' http://localhost:5000 https://daanaa.org https://www.daanaa.org; "
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        + connect_src +
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    if is_prod:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response

@app.route('/health')
@limiter.exempt
def health():
    return jsonify({"status": "ok", "db_exists": os.path.exists(DB_PATH)})

# ── API v1 seam ───────────────────────────────────────────────────────────────
# /api/v1/ is the versioning anchor for future native (Capacitor) clients.
# Full v1 migration of all endpoints is scheduled for Gate 2.
# For now, /api/v1/health establishes the contract shape:
#   { "version": "1", "data": <payload>, "meta": {} }
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

@api_v1.route('/health')
@limiter.exempt
def v1_health():
    return jsonify({
        "version": "1",
        "data": {"status": "ok", "db_exists": os.path.exists(DB_PATH)},
        "meta": {}
    })

app.register_blueprint(api_v1)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/log/search', methods=['POST'])
@limiter.limit("500 per minute")
def log_search():
    """Log a search query for surge detection. Called by frontend after search."""
    data = request.get_json(silent=True) or {}
    query = (data.get('q') or '').strip()[:200]
    clicked_ein = (data.get('clicked_ein') or '').strip()[:10]
    donated = bool(data.get('donated', False))

    if not query:
        return jsonify({"error": "q required"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO search_events (query, clicked_ein, donated) VALUES (?, ?, ?)",
        (query, clicked_ein or None, donated)
    )
    db.commit()

    return jsonify({"status": "logged"})


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
    # NTEECC subcategories, comma-separated e.g. "E21,A82". Combined with the
    # category list using OR (any ticked category or subcategory matches).
    sub_raw = request.args.get('sub', '').strip().upper()
    sub_list = [s.strip()[:4] for s in sub_raw.split(',') if s.strip()][:40]
    state = request.args.get('state', '').strip().upper()[:2]
    min_rev = request.args.get('min_revenue', type=float)
    max_rev = request.args.get('max_revenue', type=float)
    min_pct = request.args.get('min_percentile', type=float)
    min_tier = request.args.get('min_tier', '').strip()
    if min_tier == 'Glow':  # frontend alias for DB name Ember
        min_tier = 'Ember'
    hidden_gem = request.args.get('hidden_gem', '').strip() == '1'
    direct_link = request.args.get('direct_link', '').strip() == '1'
    needs_funding = request.args.get('needs_funding', '').strip() == '1'
    has_website = request.args.get('has_website', '').strip() == '1'
    recent = request.args.get('recent', '').strip() == '1'
    cause = request.args.get('cause', '').strip()[:60]
    sort_by = request.args.get('sort', 'merit_score')
    order = request.args.get('order', 'desc')

    offset = (page - 1) * per_page

    # Always restrict to 501(c)(3) orgs with deductible donations
    where_clauses = [_DEDUCTIBILITY_FILTER]
    params = []

    if search:
        search_normalized = search.replace('-', '').strip()
        # EIN lookup: pure digits → direct EIN prefix match, skip FTS
        is_ein = bool(search_normalized) and search_normalized.isdigit()
        if is_ein:
            # Qualify EIN — the v4_scores LEFT JOIN makes a bare EIN ambiguous
            where_clauses.append("r.EIN LIKE ?")
            params.append(f'{search_normalized}%')
        elif _check_fts(db):
            # FTS5 path: match on org content, join back via EIN (rowid misaligns)
            fts_q = _sanitize_fts_query(search)
            where_clauses.append(
                "r.EIN IN (SELECT ein FROM org_fts WHERE org_fts MATCH ? "
                "ORDER BY bm25(org_fts, 10, 5, 1, 1) LIMIT 2000)"
            )
            params.append(fts_q)
        else:
            # Fallback: name-only LIKE (city field excluded to avoid false matches)
            words = [w for w in search_normalized.split() if w]
            for word in words:
                where_clauses.append("organization_name LIKE ?")
                params.append(f'%{word}%')
    # Category + subcategory scope: match orgs in ANY ticked NTEE1 category OR
    # ANY ticked NTEECC subcategory (single combined OR group).
    if ntee_list or sub_list:
        scope_parts, scope_params = [], []
        if ntee_list:
            ph = ','.join('?' * len(ntee_list))
            scope_parts.append(f"NTEE1 IN ({ph})")
            scope_params.extend(ntee_list)
        if sub_list:
            likes = ' OR '.join(['NTEECC LIKE ?'] * len(sub_list))
            scope_parts.append(f"({likes})")
            scope_params.extend([s + '%' for s in sub_list])
        where_clauses.append('(' + ' OR '.join(scope_parts) + ')')
        params.extend(scope_params)
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
        where_clauses.append(
            "donate_url IS NOT NULL AND donate_url != '' "
            "AND donate_url_status IN ('ok','beta','live','claimed','blocked_or_restricted')"
        )
    if needs_funding:
        where_clauses.append("months_of_reserve IS NOT NULL AND months_of_reserve < 6")
    if has_website:
        where_clauses.append("website IS NOT NULL AND website != '' AND website_status = 'ok'")
    if recent:
        where_clauses.append("latest_tax_year IS NOT NULL AND latest_tax_year >= 2022")
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
        sort_by = 'merit_score'
    if order not in ['asc', 'desc']:
        order = 'desc'

    # Prefix sort_by with table alias to avoid ambiguity in JOINs
    sort_col = f"r.{sort_by}"
    if sort_by in ['total_revenue', 'organization_name', 'ntee1_percentile', 'merit_score', 'EIN', 'STATE', 'CITY']:
        sort_col = f"r.{sort_by}"

    where_sql = " AND ".join(where_clauses)

    # Alias as r so qualified columns (r.EIN) in where_sql resolve here too
    total = db.execute(f"SELECT COUNT(*) FROM registry_enriched r WHERE {where_sql}", params).fetchone()[0]

    # Check if v4_scores table exists (production might not have it)
    has_v4_scores = bool(db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='v4_scores' LIMIT 1"
    ).fetchone())

    if has_v4_scores:
        v4_cols = ", v4.visibility_tier, v4.financial_health, v4.operating_model, v4.revenue_band as v4_revenue_band, v4.peer_cell_size, v4.metrics_json, v4.percentiles_json"
        join_clause = "LEFT JOIN v4_scores v4 ON r.EIN = v4.EIN"
    else:
        v4_cols = ", NULL as visibility_tier, NULL as financial_health, NULL as operating_model, NULL as v4_revenue_band, NULL as peer_cell_size, NULL as metrics_json, NULL as percentiles_json"
        join_clause = ""

    sql = f"""
        SELECT r.EIN, r.organization_name, r.NTEE1, r.NTEECC, r.CITY, r.STATE,
               r.total_revenue, r.ntee1_percentile, r.ntee1_total_orgs, r.source,
               r.latest_tax_year, r.data_source, r.updated_at,
               r.revenue_band, r.peer_percentile, r.peer_rank, r.peer_total, r.peer_group,
               r.merit_tier, r.merit_score, r.merit_band,
               CASE WHEN r.months_of_reserve BETWEEN -120 AND 120 THEN r.months_of_reserve ELSE NULL END as months_of_reserve,
               r.net_assets, r.total_expenses,
               r.employee_count, r.ruling_date, r.zipcode, r.is_hidden_gem, r.cause_tags,
               r.donate_url, r.donate_platform, r.donate_url_status, r.subsection, r.deductibility,
               SUBSTR(r.mission, 1, 300) as mission, r.mission_source,
               (r.mission IS NOT NULL AND r.mission != '') as has_mission,
               (r.website IS NOT NULL AND r.website != '') as has_website
               {v4_cols}
        FROM registry_enriched r
        {join_clause}
        WHERE {where_sql}
        ORDER BY {sort_col} {order}
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])
    rows = db.execute(sql, params).fetchall()

    orgs = []
    for row in rows:
        d = dict(row)
        d = _attach_v4_scores(d, row)
        d['total_revenue_formatted'] = f"${d['total_revenue']:,.0f}" if d['total_revenue'] else None
        # Official-sources gate on the card's give affordance (cheap check; the
        # per-EIN revocation lookup runs on the org-detail page, not the list).
        if not _donate_eligible_basic(d.get('subsection'), d.get('deductibility'))[0]:
            d['donate_url'] = None
            d['donate_platform'] = None
            d['donate_url_status'] = None
        d.pop('subsection', None)
        d.pop('deductibility', None)
        if d.get('cause_tags'):
            try:
                d['cause_tags'] = json.loads(d['cause_tags'])
            except (json.JSONDecodeError, TypeError):
                d['cause_tags'] = None
        orgs.append(_strip_scores(d))

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

    # Check if v4_scores table exists
    has_v4_scores = bool(db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='v4_scores' LIMIT 1"
    ).fetchone())

    if has_v4_scores:
        # Use subquery to avoid column name conflicts between registry_enriched and v4_scores
        sql = """SELECT r.*,
                        v4_data.visibility_tier,
                        v4_data.financial_health,
                        v4_data.operating_model,
                        v4_data.revenue_band as v4_revenue_band,
                        v4_data.peer_cell_size,
                        v4_data.metrics_json,
                        v4_data.percentiles_json
                 FROM registry_enriched r
                 LEFT JOIN (
                    SELECT EIN, visibility_tier, financial_health, operating_model,
                           revenue_band, peer_cell_size, metrics_json, percentiles_json
                    FROM v4_scores
                 ) v4_data ON r.EIN = v4_data.EIN
                 WHERE r.EIN = ?"""
    else:
        sql = """SELECT r.*,
                        NULL as visibility_tier, NULL as financial_health, NULL as operating_model, NULL as v4_revenue_band,
                        NULL as peer_cell_size, NULL as metrics_json, NULL as percentiles_json
                 FROM registry_enriched r
                 WHERE r.EIN = ?"""

    row = db.execute(sql, (ein_clean,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404

    org = dict(row)
    org = _attach_v4_scores(org, row)
    # Clamp sentinel values written by the pipeline (-999, 999) to null
    mor = org.get('months_of_reserve')
    if mor is not None and not (-120 <= mor <= 120):
        org['months_of_reserve'] = None
    org['total_revenue_formatted'] = f"${org['total_revenue']:,.0f}" if org['total_revenue'] else None
    org['has_mission'] = bool(org.get('mission') and str(org['mission']).strip())
    org['has_website'] = bool(org.get('website') and str(org['website']).strip())

    # G2 / official-sources gate: never present a donate path for a non-deductible,
    # non-501(c)(3), or IRS-auto-revoked org. Fail closed — null the donate fields
    # so the frontend can't render a "give" affordance, and record why.
    eligible, reason = _donate_eligible_basic(org.get('subsection'), org.get('deductibility'))
    if eligible and _is_revoked(db, ein_clean):
        eligible, reason = False, 'irs_auto_revoked'
    if not eligible:
        org['donate_url'] = None
        org['donate_platform'] = None
        org['donate_url_status'] = None
        org['donate_ineligible_reason'] = reason

    # Data provenance badges — tells the frontend which fields are AI-generated vs verified
    org['data_badges'] = {
        'mission': org.get('mission_source'),       # 'ai_ntee'|'ai_haiku'|'ai_web'|'lucido'|'claimed'|None
        'donate':  org.get('donate_url_status'),    # 'beta' | 'provider' | 'claimed' | None
        'website': org.get('website_status'),       # 'ok' | 'redirected' | None
        'tags':    org.get('cause_tags_source'),    # 'ai_generated' (beta) | 'claimed' | None
    }

    # Claim status — check org_claims table (graceful fallback if table not yet created)
    try:
        claim_row = db.execute(
            "SELECT claim_status FROM org_claims WHERE ein = ?", (ein_clean,)
        ).fetchone()
        org['claim_status'] = claim_row['claim_status'] if claim_row else None
    except Exception:
        org['claim_status'] = None

    # Parse JSON text columns → Python lists
    if org.get('cause_tags'):
        try:
            org['cause_tags'] = json.loads(org['cause_tags'])
        except (json.JSONDecodeError, TypeError):
            org['cause_tags'] = None

    # Similar orgs: NTEECC+band (specific) → NTEE1+band → NTEE1 only
    _sim_results, _ = _find_similar_orgs(db, ein_clean, org, limit=5)
    org['similar_organizations'] = _sim_results

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

    # Add appropriate disclosures based on org's scoring status
    disclosures = {}
    if org.get('financial_health'):
        disclosures['score_disclaimer'] = SCORE_DISCLAIMER
    else:
        disclosures['unscored_disclosure'] = UNSCORED_DISCLOSURE

    # Beta disclosure: website discovered via heuristic, not org-verified
    if org.get('website_status') == 'beta':
        disclosures['website_disclosure'] = BETA_WEBSITE_DISCLOSURE

    # Beta disclosure: donation link discovered via heuristic, not org-verified
    if org.get('donate_url_status') == 'beta':
        disclosures['donate_link_disclosure'] = BETA_DONATION_LINK_DISCLOSURE

    result = _strip_scores(org)
    result['_disclosures'] = disclosures
    return jsonify(result)

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
_DEDUCTIBILITY_FILTER = "subsection = '3' AND deductibility = '1'"  # Only active tax-deductible 501(c)(3)


def _donate_eligible_basic(subsection, deductibility):
    # Official-sources-only gate (cheap, no DB). A donate path may only be
    # presented as authoritative for a confirmed, tax-deductible 501(c)(3).
    # Fail closed on anything else. Returns (eligible: bool, reason: str|None).
    if str(subsection or '') != '3':
        return False, 'not_501c3'
    if str(deductibility or '') == '2':
        return False, 'not_tax_deductible'
    return True, None


def _is_revoked(db, ein):
    # True if the EIN is on the IRS Automatic Revocation list (G2). Indexed
    # primary-key lookup; safe to call per org-detail request.
    ein = ''.join(c for c in str(ein or '') if c.isdigit())[:10]
    if not ein:
        return False
    try:
        return db.execute("SELECT 1 FROM revoked_eins WHERE ein = ?", (ein,)).fetchone() is not None
    except Exception:
        return False  # table missing → fail OPEN on revocation only; basic gate still applies

@app.route('/api/ntee-coverage')
@limiter.limit("30 per minute")
def ntee_coverage():
    """Per-category visibility coverage for qualified orgs — drives the
    light-reveal visual. Returns real counts so brightness reflects true data."""
    cached = _cget('ntee_coverage', 'ntee')
    if cached: return jsonify(cached)
    db = get_db()
    rows = db.execute(f"""
        SELECT NTEE1 as code,
               COUNT(*) as total,
               SUM(CASE WHEN mission IS NOT NULL THEN 1 ELSE 0 END) as with_mission,
               SUM(CASE WHEN merit_score IS NOT NULL THEN 1 ELSE 0 END) as scored,
               SUM(CASE WHEN mission IS NOT NULL AND merit_score IS NOT NULL THEN 1 ELSE 0 END) as visible
        FROM registry_enriched
        WHERE {_DEDUCTIBILITY_FILTER} AND NTEE1 IS NOT NULL
        GROUP BY NTEE1
    """).fetchall()
    categories = []
    for row in rows:
        d = dict(row)
        total = d['total'] or 0
        d['coverage'] = round(d['visible'] / total, 4) if total else 0.0
        categories.append(d)
    payload = {"categories": categories}
    _cset('ntee_coverage', payload)
    return jsonify(payload)

@app.route('/api/stats')
@limiter.limit("60 per minute")
def stats():
    cached = _cget('stats', 'stats')
    if cached: return jsonify(cached)
    db = get_db()
    f = _DEDUCTIBILITY_FILTER
    # Single pass over registry_enriched for all aggregate stats
    agg = db.execute(f"""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN total_revenue > 0 THEN 1 END) as with_revenue,
            ROUND(SUM(CASE WHEN total_revenue > 0 THEN total_revenue ELSE 0 END), 0) as revenue_sum,
            ROUND(AVG(CASE WHEN total_revenue > 0 THEN total_revenue END), 0) as avg_revenue,
            COUNT(CASE WHEN months_of_reserve BETWEEN -120 AND 120 THEN 1 END) as has_reserve,
            COUNT(CASE WHEN months_of_reserve BETWEEN -120 AND 0 THEN 1 END) as insolvent,
            COUNT(CASE WHEN months_of_reserve > 0 AND months_of_reserve < 6 THEN 1 END) as at_risk,
            COUNT(CASE WHEN months_of_reserve >= 6 AND months_of_reserve < 12 THEN 1 END) as minimal,
            COUNT(CASE WHEN months_of_reserve >= 12 THEN 1 END) as healthy
        FROM registry_enriched WHERE {f}
    """).fetchone()
    top_states = [dict(r) for r in db.execute(f"""
        SELECT STATE, COUNT(*) as count FROM registry_enriched
        WHERE {f} AND STATE IS NOT NULL GROUP BY STATE ORDER BY count DESC LIMIT 5
    """).fetchall()]
    # propublica_financials is excluded from the lean web DB (kept only on the
    # home/full instance). Fall back to the count of orgs with financial data so
    # the stats endpoint never 500s on the production droplet.
    try:
        financial_records = db.execute("SELECT COUNT(*) FROM propublica_financials").fetchone()[0]
    except sqlite3.OperationalError:
        financial_records = agg["with_revenue"]
    payload = {
        "total_organizations": agg["total"],
        "with_revenue": agg["with_revenue"],
        "total_revenue_sum": agg["revenue_sum"],
        "avg_revenue": agg["avg_revenue"],
        "top_states": top_states,
        "methodology_version": METHODOLOGY_VERSION,
        "scores_last_updated": db.execute(
            "SELECT MAX(snapshot_date) FROM score_snapshots"
        ).fetchone()[0],
        "financial_records": financial_records,
        "with_reserve_data": agg["has_reserve"],
        "reserve_health": {
            "insolvent": agg["insolvent"],
            "at_risk": agg["at_risk"],
            "minimal": agg["minimal"],
            "healthy": agg["healthy"],
        },
    }
    _cset('stats', payload)
    return jsonify(payload)

@app.route('/api/sector-health')
@limiter.limit("30 per minute")
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
@limiter.limit("5 per minute; 20 per hour")
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


@app.route('/api/handoff', methods=['POST'])
@limiter.limit("20 per minute")
def donate_handoff():
    # Anonymous realized-impact signal. We accept ONLY an EIN and increment a
    # daily count. No identity, no IP, no amount, no wallet link. This records
    # that a give hand-off happened, never who did it or what they gave.
    data = request.get_json(silent=True) or {}
    ein  = ''.join(c for c in str(data.get('ein', '')) if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'ein required'}), 400
    day = time.strftime('%Y-%m-%d')
    db = get_db()
    db.execute(
        "INSERT INTO donate_handoffs (ein, day, count) VALUES (?, ?, 1) "
        "ON CONFLICT(ein, day) DO UPDATE SET count = count + 1",
        (ein, day),
    )
    db.commit()
    return ('', 204)


@app.route('/api/interest', methods=['POST'])
@limiter.limit("20 per minute")
def org_interest_signal():
    # Anonymous demand signal toward an org. Accept ONLY an EIN and a kind.
    # No identity, no contact, no IP. The org sees the tally only on claim.
    data = request.get_json(silent=True) or {}
    ein  = ''.join(c for c in str(data.get('ein', '')) if c.isdigit())[:10]
    kind = str(data.get('kind', '')).strip().lower()
    if not ein or kind not in ('donate', 'volunteer'):
        return jsonify({'error': "ein and kind ('donate'|'volunteer') required"}), 400
    db = get_db()
    db.execute(
        "INSERT INTO org_interest (ein, kind, count) VALUES (?, ?, 1) "
        "ON CONFLICT(ein, kind) DO UPDATE SET count = count + 1",
        (ein, kind),
    )
    db.commit()
    return ('', 204)


@app.route('/api/interest/<ein>')
def org_interest_counts(ein):
    # Readback of the anonymous demand tally for an org, for the claim flow to
    # show the organization ("3 people wanted to give, 1 to volunteer"). Counts
    # only — never who. Intentionally not joined into public org responses.
    ein = ''.join(c for c in str(ein) if c.isdigit())[:10]
    db = get_db()
    rows = db.execute(
        "SELECT kind, count FROM org_interest WHERE ein = ?", (ein,)
    ).fetchall()
    out = {'donate': 0, 'volunteer': 0}
    for r in rows:
        if r['kind'] in out:
            out[r['kind']] = r['count']
    return jsonify(out)


import re as _re
_ID_SEG = _re.compile(r'/(\d{2,}|[0-9a-f]{8,})(?=/|$)', _re.I)

def _normalize_path(p: str) -> str:
    # Collapse high-cardinality IDs to a route shape so analytics_daily stays
    # small and never stores a specific org/EIN as a per-row key.
    #   /org/123456789 -> /org/:id   ;  /category/A -> /category/:id
    if not p.startswith('/'):
        p = '/' + p
    p = p.split('?')[0].split('#')[0]
    p = _ID_SEG.sub('/:id', p)
    return p[:120] or '/'


@app.route('/api/feedback', methods=['POST'])
@limiter.limit("5 per minute; 20 per hour")
def submit_feedback():
    # Anonymous site feedback. message required; email OPTIONAL (only if the
    # visitor wants to be kept posted). No IP, no tracking, no identity.
    data     = request.get_json(silent=True) or {}
    message  = str(data.get('message', '')).strip()[:4000]
    email    = str(data.get('email', '')).strip()[:200] or None
    page     = str(data.get('page', '')).strip()[:300] or None
    category = str(data.get('category', '')).strip().lower()[:40] or None
    if not message:
        return jsonify({'error': 'message required'}), 400
    if email and ('@' not in email or '.' not in email.split('@')[-1]):
        return jsonify({'error': 'invalid email'}), 400
    db = get_db()
    db.execute(
        "INSERT INTO feedback (category, message, email, page) VALUES (?, ?, ?, ?)",
        (category, message, email, page),
    )
    db.commit()
    return ('', 204)


# Bounded allow-list so the analytics beacon can't be used to write arbitrary
# high-cardinality data. Paths are normalized to route shapes, not raw URLs.
_EVENT_TYPES = {'pageview', 'search', 'give_click', 'save_org', 'compare', 'wallet_export'}


@app.route('/api/event', methods=['POST'])
@limiter.limit("60 per minute")
def track_event():
    # First-party, aggregate-only analytics. We count events, never people.
    # No cookie, no IP, no persistent ID, no individual session row. Fired via
    # sendBeacon. A 'session' flag (sessionStorage) lets the client mark one
    # session-start per browser session — still no server-side identity.
    data  = request.get_json(silent=True) or {}
    etype = str(data.get('type', '')).strip().lower()
    if etype not in _EVENT_TYPES:
        return ('', 204)  # silently ignore unknown types; never error a beacon
    day  = time.strftime('%Y-%m-%d')
    path = _normalize_path(str(data.get('path', '/'))[:120])
    dwell = data.get('dwell')
    dwell = int(dwell) if isinstance(dwell, (int, float)) and 0 <= dwell <= 86400 else 0
    db = get_db()
    db.execute(
        "INSERT INTO analytics_daily (day, path, event_type, count, dwell_secs) "
        "VALUES (?, ?, ?, 1, ?) "
        "ON CONFLICT(day, path, event_type) DO UPDATE SET "
        "count = count + 1, dwell_secs = dwell_secs + excluded.dwell_secs",
        (day, path, etype, dwell),
    )
    if etype == 'pageview':
        db.execute("UPDATE visit_counter SET count = count + 1 WHERE metric = 'pageviews'")
        if data.get('new_session'):
            db.execute("UPDATE visit_counter SET count = count + 1 WHERE metric = 'sessions'")
    if etype == 'search':
        term = str(data.get('term', '')).strip().lower()[:80]
        if term:
            db.execute(
                "INSERT INTO analytics_search (day, term, count) VALUES (?, ?, 1) "
                "ON CONFLICT(day, term) DO UPDATE SET count = count + 1",
                (day, term),
            )
    db.commit()
    return ('', 204)


# ─────────────────────────────────────────────────────────────────────────────
# ORG SELF-REPORTING: Unscored orgs submit financial data to get scored
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/org/submit-financial-data', methods=['POST'])
@limiter.limit("10 per hour")
def org_submit_data():
    """Org submits its revenue + expenses to get scored via Tier D (self-reported)."""
    data = request.get_json(silent=True) or {}
    ein = str(data.get('ein', '')).strip()
    revenue = data.get('revenue')
    expenses = data.get('expenses')
    email = str(data.get('email', '')).strip()
    org_name = str(data.get('organization_name', '')).strip()

    # Validate inputs
    if not ein or not ein.isdigit():
        return jsonify({"error": "Invalid EIN"}), 400
    if not revenue or not expenses:
        return jsonify({"error": "Revenue and expenses required"}), 400
    try:
        revenue = float(revenue)
        expenses = float(expenses)
        if revenue <= 0 or expenses <= 0:
            return jsonify({"error": "Revenue and expenses must be positive"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric values"}), 400

    db = get_db()

    # Check org exists in registry
    org = db.execute(
        "SELECT EIN, organization_name FROM registry_enriched WHERE EIN = ?",
        (ein,)
    ).fetchone()
    if not org:
        return jsonify({"error": "Organization not found in registry"}), 404

    # Check already scored
    scored = db.execute(
        "SELECT EIN FROM v4_scores WHERE EIN = ?", (ein,)
    ).fetchone()
    if scored:
        return jsonify({"error": "Organization already has v4 score"}), 409

    # Insert submission
    try:
        db.execute(
            """INSERT OR REPLACE INTO org_submissions
               (EIN, organization_name, submitted_revenue, submitted_expenses,
                submitter_email, submitted_at, status)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'pending')""",
            (ein, org_name or org['organization_name'], revenue, expenses, email)
        )
        db.commit()
        return jsonify({
            "status": "submitted",
            "message": "Thank you! We'll review and score your organization soon.",
            "ein": ein
        }), 201
    except Exception as e:
        return jsonify({"error": f"Submission failed: {str(e)}"}), 500


@app.route('/api/org/<ein>/submission-status', methods=['GET'])
@limiter.limit("60 per minute")
def org_submission_status(ein):
    """Check if org has submitted data and when it will be scored."""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    db = get_db()

    # Check if already scored
    scored = db.execute(
        "SELECT visibility_tier, financial_health FROM v4_scores WHERE EIN = ?",
        (ein_clean,)
    ).fetchone()
    if scored:
        return jsonify({
            "status": "scored",
            "visibility_tier": scored['visibility_tier'],
            "financial_health": scored['financial_health']
        }), 200

    # Check submission status
    submission = db.execute(
        """SELECT submitted_at, status, submitted_revenue, submitted_expenses
           FROM org_submissions WHERE EIN = ?""",
        (ein_clean,)
    ).fetchone()

    if submission:
        return jsonify({
            "status": submission['status'],
            "submitted_at": submission['submitted_at'],
            "next_action": "We review submissions weekly and score them using our fair peer-based methodology."
        }), 200

    # Not submitted yet
    return jsonify({
        "status": "not_submitted",
        "message": "Organization hasn't submitted financial data yet. Visit /org/<ein>/claim to submit."
    }), 200


@app.route('/api/unscored-search', methods=['GET'])
@limiter.limit("60 per minute")
def unscored_search():
    """Search for unscored orgs by name/location to include in results with 'unscored' marker."""
    query = request.args.get('q', '').strip()
    ntee1 = request.args.get('ntee1', '').upper().strip()
    state = request.args.get('state', '').upper().strip()
    limit = min(int(request.args.get('limit', 20)), 50)

    if not query and not ntee1 and not state:
        return jsonify({"error": "Provide search terms (q, ntee1, or state)"}), 400

    db = get_db()
    where_parts = ["r.EIN NOT IN (SELECT EIN FROM v4_scores)"]
    params = []

    if query:
        where_parts.append("(r.organization_name LIKE ? OR r.website LIKE ?)")
        q_wild = f"%{query}%"
        params.extend([q_wild, q_wild])
    if ntee1:
        where_parts.append("r.NTEE1 = ?")
        params.append(ntee1)
    if state:
        where_parts.append("r.STATE = ?")
        params.append(state)

    where_sql = " AND ".join(where_parts)
    rows = db.execute(
        f"""SELECT r.EIN, r.organization_name, r.CITY, r.STATE, r.NTEE1,
                  r.total_revenue, r.website, r.mission
           FROM registry_enriched r
           WHERE {where_sql}
           LIMIT ?""",
        params + [limit]
    ).fetchall()

    results = []
    for row in rows:
        results.append({
            "EIN": row['EIN'],
            "organization_name": row['organization_name'],
            "location": f"{row['CITY']}, {row['STATE']}",
            "NTEE1": row['NTEE1'],
            "revenue": row['total_revenue'],
            "website": row['website'],
            "mission": row['mission'],
            "visibility_tier": "Unscored",
            "financial_health": None,
            "marker": "No financial data available in IRS records"
        })

    return jsonify({
        "results": results,
        "count": len(results),
        "disclosure": UNSCORED_DISCLOSURE,
        "call_to_action": "Help us score unscored organizations: claim a page and add financial data at daanaa.org/for-nonprofits"
    }), 200


@app.route('/api/admin/analytics', methods=['GET'])
@require_admin_key
def admin_analytics():
    # Hidden (admin-only) aggregate dashboard data. Never exposed publicly.
    db = get_db()
    totals = {r['metric']: r['count'] for r in
              db.execute("SELECT metric, count FROM visit_counter").fetchall()}
    top_pages = [dict(r) for r in db.execute(
        "SELECT path, SUM(count) AS views, SUM(dwell_secs) AS dwell "
        "FROM analytics_daily WHERE event_type='pageview' "
        "GROUP BY path ORDER BY views DESC LIMIT 25").fetchall()]
    top_searches = [dict(r) for r in db.execute(
        "SELECT term, SUM(count) AS n FROM analytics_search "
        "GROUP BY term ORDER BY n DESC LIMIT 30").fetchall()]
    last_14 = [dict(r) for r in db.execute(
        "SELECT day, SUM(count) AS views FROM analytics_daily "
        "WHERE event_type='pageview' GROUP BY day ORDER BY day DESC LIMIT 14").fetchall()]
    return jsonify({
        'totals': totals,
        'top_pages': top_pages,
        'top_searches': top_searches,
        'daily_pageviews': last_14,
    })


@app.route('/api/admin/feedback', methods=['GET'])
@require_admin_key
def admin_feedback():
    db = get_db()
    rows = [dict(r) for r in db.execute(
        "SELECT id, category, message, email, page, status, created_at "
        "FROM feedback ORDER BY created_at DESC LIMIT 200").fetchall()]
    return jsonify({'feedback': rows, 'total': len(rows)})


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


# ── Claim flow ────────────────────────────────────────────────────────────────

@app.route('/api/claim/start', methods=['POST'])
@limiter.limit("3 per hour")
def claim_start():
    data = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    email = (data.get('email') or '').strip()[:254]

    if not ein or not email or '@' not in email:
        return jsonify({"error": "EIN and valid email are required"}), 400

    db  = get_db()
    row = db.execute(
        "SELECT EIN, organization_name, address, CITY, STATE, zipcode FROM registry_enriched WHERE EIN = ?",
        (ein,)
    ).fetchone()
    if not row:
        return jsonify({"error": "Organization not found"}), 404

    org_name    = row['organization_name']
    irs_address = f"{row['address'] or ''}, {row['CITY'] or ''}, {row['STATE'] or ''} {row['zipcode'] or ''}".strip(", ")

    if not row['address']:
        return jsonify({"error": "No mailing address on file for this organization"}), 422

    # Block if already active/letter_sent in last 30 days
    existing = db.execute(
        "SELECT claim_status, created_at FROM org_claims WHERE ein = ?", (ein,)
    ).fetchone()
    if existing and existing['claim_status'] in ('active', 'verified'):
        return jsonify({"error": "This organization has already been claimed"}), 409
    if existing and existing['claim_status'] == 'letter_sent':
        return jsonify({"error": "A verification letter was already sent. Check your mail or contact orgs@daanaa.org to resend."}), 409

    pin            = str(secrets.randbelow(900000) + 100000)
    pin_expires_at = db.execute("SELECT datetime('now', '+30 days')").fetchone()[0]

    db.execute("""
        INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at, claim_status)
        VALUES (?, ?, ?, ?, ?, 'pending')
        ON CONFLICT(ein) DO UPDATE SET
            email=excluded.email, pin=excluded.pin,
            pin_expires_at=excluded.pin_expires_at,
            claim_status='pending', letter_sent_at=NULL, lob_letter_id=NULL
    """, (ein, email, irs_address, pin, pin_expires_at))
    db.commit()

    # Send letter (Lob or log fallback)
    letter_status = "log_only"
    try:
        import sys
        sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent / 'scripts'))
        from send_claim_letter import send_claim_letter
        address = {'street': row['address'] or '', 'city': row['CITY'] or '',
                   'state': row['STATE'] or '', 'zip': row['zipcode'] or ''}
        letter_id = send_claim_letter(ein, org_name, address, pin)
        if letter_id and not letter_id.startswith("log:"):
            letter_status = "letter_sent"
        db.execute(
            "UPDATE org_claims SET claim_status=?, letter_sent_at=datetime('now'), lob_letter_id=? WHERE ein=?",
            (letter_status, letter_id, ein)
        )
        db.commit()
    except Exception as e:
        app.logger.error(f"send_claim_letter failed for {ein}: {e}")

    # Friendly address preview (first line only for privacy)
    preview = f"{row['address']}, {row['CITY']}, {row['STATE']}" if row['address'] else irs_address
    return jsonify({"status": letter_status, "org_name": org_name, "address_preview": preview})


@app.route('/api/claim/verify', methods=['POST'])
@limiter.limit("10 per minute")
def claim_verify():
    data  = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('token') or '').strip()[:64]   # new: opaque HMAC token
    pin   = ''.join(c for c in (data.get('pin') or '') if c.isdigit())[:6]  # legacy fallback

    if not ein or (not token and not pin):
        return jsonify({"error": "EIN and token (or PIN) are required"}), 400

    db  = get_db()
    row = db.execute(
        "SELECT * FROM org_claims WHERE ein = ?", (ein,)
    ).fetchone()

    if not row:
        return jsonify({"error": "No claim found for this EIN. Start at daanaa.org/for-nonprofits"}), 404

    if token:
        expected = _make_verify_token(ein, row['pin'])
        if not hmac.compare_digest(token, expected):
            return jsonify({"error": "Invalid verification token"}), 401
    else:
        # Legacy PIN path — for letters sent before token rollout
        if not hmac.compare_digest(pin, row['pin']):
            return jsonify({"error": "Incorrect PIN"}), 401

    if row['claim_status'] == 'active':
        return jsonify({"error": "Already claimed"}), 409

    # Check expiry
    expired = db.execute(
        "SELECT datetime('now') > ? as expired", (row['pin_expires_at'],)
    ).fetchone()
    if expired and expired['expired']:
        return jsonify({"error": "PIN has expired. Please request a new letter."}), 410

    db.execute(
        "UPDATE org_claims SET claim_status='verified', verified_at=datetime('now') WHERE ein=?",
        (ein,)
    )
    db.commit()

    org = db.execute(
        "SELECT organization_name, mission, donate_url FROM registry_enriched WHERE EIN=?", (ein,)
    ).fetchone()

    return jsonify({
        "status": "verified",
        "ein": ein,
        "org_name": org['organization_name'] if org else "",
        "current_mission": org['mission'] if org else None,
        "current_donate_url": org['donate_url'] if org else None,
        "irs_address": row['irs_address'],
        "verification_token": _make_verify_token(ein, row['pin']),
    })


@app.route('/api/claim/update', methods=['POST'])
def claim_update():
    """Update claimed org profile — mission, description, cause tags, donate URL."""
    data  = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('verification_token') or '').strip()[:64]

    if not ein or not token:
        return jsonify({'error': 'EIN and verification_token required'}), 400

    db  = get_db()
    row = db.execute('SELECT * FROM org_claims WHERE ein = ?', (ein,)).fetchone()
    if not row:
        return jsonify({'error': 'No claim found for this EIN. Start at /for-nonprofits'}), 404
    if row['claim_status'] == 'revoked':
        return jsonify({'error': 'This claim has been revoked'}), 403

    # Verify token matches stored pin (HMAC or legacy PIN)
    stored_pin  = row['pin']
    valid_token = (token == stored_pin) or (token == _make_verify_token(ein, stored_pin))
    if not valid_token:
        return jsonify({'error': 'Verification token is invalid or expired'}), 403

    custom_mission     = (data.get('custom_mission') or '').strip()[:300]
    custom_description = (data.get('custom_description') or '').strip()[:500]
    cause_tags_json    = (data.get('cause_tags_json') or '[]').strip()
    donate_confirmed   = bool(data.get('donate_confirmed', False))
    donate_url         = (data.get('donate_url') or '').strip()[:500]

    # Validate donate URL if provided
    if donate_url and not donate_url.startswith(('http://', 'https://')):
        donate_url = ''

    try:
        # Update org_claims record
        db.execute("""
            UPDATE org_claims
            SET claim_status     = 'verified',
                verified_at      = datetime('now'),
                custom_mission   = ?,
                custom_description = ?,
                donate_confirmed = ?
            WHERE ein = ?
        """, (custom_mission or None, custom_description or None, int(donate_confirmed), ein))

        # Write custom fields to registry_enriched
        if custom_mission:
            db.execute("""
                UPDATE registry_enriched
                SET mission = ?, mission_source = 'claimed'
                WHERE EIN = ?
            """, (custom_mission, ein))

        if donate_url and donate_confirmed:
            db.execute("""
                UPDATE registry_enriched
                SET donate_url = ?, donate_confidence = 95, donate_url_status = 'claimed'
                WHERE EIN = ?
            """, (donate_url, ein))

        if cause_tags_json and cause_tags_json != '[]':
            db.execute("""
                UPDATE registry_enriched
                SET cause_tags = ?, cause_tags_source = 'claimed'
                WHERE EIN = ?
            """, (cause_tags_json, ein))

        db.commit()
        # Evict org cache entries for this EIN
        stale = [k for k in _CACHE if ein in k]
        for k in stale:
            _CACHE.pop(k, None)
        return jsonify({'success': True, 'message': 'Profile updated'}), 200

    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)[:80]}'}), 500


@app.route('/api/claim/profile', methods=['PATCH'])
@limiter.limit("20 per minute")
def claim_profile_update():
    data = request.get_json(silent=True) or {}
    ein  = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    pin  = ''.join(c for c in (data.get('pin') or '') if c.isdigit())[:6]

    if not ein or not pin:
        return jsonify({"error": "EIN and PIN are required"}), 400

    db  = get_db()
    row = db.execute("SELECT * FROM org_claims WHERE ein=?", (ein,)).fetchone()
    if not row or row['pin'] != pin or row['claim_status'] not in ('verified', 'active'):
        return jsonify({"error": "Not authorized — verify your PIN first"}), 403

    custom_mission      = (data.get('custom_mission') or '').strip()[:1000] or None
    custom_description  = (data.get('custom_description') or '').strip()[:2000] or None
    donate_confirmed    = 1 if data.get('donate_confirmed') else 0
    processor_auth      = 1 if data.get('processor_auth') else 0

    db.execute("""
        UPDATE org_claims
        SET custom_mission=?, custom_description=?, donate_confirmed=?,
            processor_auth=?, claim_status='active'
        WHERE ein=?
    """, (custom_mission, custom_description, donate_confirmed, processor_auth, ein))

    if donate_confirmed:
        db.execute(
            "UPDATE registry_enriched SET donate_url_status='claimed' WHERE EIN=?", (ein,)
        )

    # Write custom mission to registry_enriched with source = 'claimed'
    if custom_mission:
        db.execute(
            "UPDATE registry_enriched SET mission=?, mission_source='claimed' WHERE EIN=?",
            (custom_mission, ein)
        )

    db.commit()
    return jsonify({"status": "updated"})


def _fetch_orgs_by_eins(db, eins: list[str]) -> list[dict]:
    if not eins:
        return []
    cols = """r.EIN, r.organization_name, r.CITY, r.STATE, r.total_revenue,
              r.ntee1_percentile, r.peer_percentile, r.peer_group, r.revenue_band,
              r.latest_tax_year, r.data_source, r.updated_at,
              r.merit_tier, r.merit_score, r.merit_band,
              v4.visibility_tier, v4.financial_health, v4.operating_model, v4.revenue_band as v4_revenue_band,
              v4.peer_cell_size, v4.metrics_json, v4.percentiles_json"""
    placeholders = ",".join("?" * len(eins))
    rows = db.execute(
        f"""SELECT {cols} FROM registry_enriched r
            LEFT JOIN v4_scores v4 ON r.EIN = v4.EIN
            WHERE r.EIN IN ({placeholders})""", eins
    ).fetchall()
    order = {e: i for i, e in enumerate(eins)}
    result = []
    for r in rows:
        org = dict(r)
        org = _attach_v4_scores(org, r)
        result.append(org)
    return sorted(result, key=lambda r: order.get(r["EIN"], 999))


def _find_similar_orgs(db, ein_clean, org, limit=6):
    """Similar orgs: vector cosine similarity when available, SQL bucket fallback."""
    cols = """r.EIN, r.organization_name, r.CITY, r.STATE, r.total_revenue,
              r.ntee1_percentile, r.peer_percentile, r.peer_group, r.revenue_band,
              r.latest_tax_year, r.data_source, r.updated_at,
              r.merit_tier, r.merit_score, r.merit_band,
              v4.visibility_tier, v4.financial_health, v4.operating_model, v4.revenue_band as v4_revenue_band,
              v4.peer_cell_size, v4.metrics_json, v4.percentiles_json"""

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
            SELECT {cols} FROM registry_enriched r
            LEFT JOIN v4_scores v4 ON r.EIN = v4.EIN
            WHERE r.NTEECC = ? AND r.revenue_band = ? AND r.EIN != ?
            ORDER BY ABS(COALESCE(r.peer_percentile, 50) - ?) ASC LIMIT ?
        """, (nteecc, band, ein_clean, pct, limit)).fetchall()
        if len(rows) >= 3:
            return [_attach_v4_scores(dict(r), r) for r in rows], 'nteecc+band'

    if ntee1 and band:
        rows = db.execute(f"""
            SELECT {cols} FROM registry_enriched r
            LEFT JOIN v4_scores v4 ON r.EIN = v4.EIN
            WHERE r.NTEE1 = ? AND r.revenue_band = ? AND r.EIN != ?
            ORDER BY ABS(COALESCE(r.peer_percentile, r.ntee1_percentile, 50) - ?) ASC LIMIT ?
        """, (ntee1, band, ein_clean, pct, limit)).fetchall()
        if len(rows) >= 2:
            return [_attach_v4_scores(dict(r), r) for r in rows], 'ntee1+band'

    if ntee1:
        rows = db.execute(f"""
            SELECT {cols} FROM registry_enriched r
            LEFT JOIN v4_scores v4 ON r.EIN = v4.EIN
            WHERE r.NTEE1 = ? AND r.EIN != ?
            ORDER BY ABS(COALESCE(r.peer_percentile, r.ntee1_percentile, 50) - ?) ASC LIMIT ?
        """, (ntee1, ein_clean, pct, limit)).fetchall()
        return [_attach_v4_scores(dict(r), r) for r in rows], 'ntee1'

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

    diamonds_only = request.args.get('diamonds', '').strip() == '1'

    db = get_db()
    row = db.execute("SELECT * FROM registry_enriched WHERE EIN = ?", (ein_clean,)).fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404

    org = dict(row)
    fetch_limit = limit * 3 if diamonds_only else limit
    results, mode = _find_similar_orgs(db, ein_clean, org, limit=fetch_limit)
    if diamonds_only:
        results = [r for r in results if r.get('is_hidden_gem')][:limit]
    return jsonify({'results': [_strip_scores(r) for r in results], 'mode': mode, 'diamonds_only': diamonds_only})


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
    results  = [_strip_scores(r) for r in _fetch_orgs_by_eins(db, top_eins)]
    return jsonify({"results": results, "query": q, "mode": "semantic", "total": len(results)})


# ── Fused search (RRF: FTS5 keyword + semantic vector) ─────────────────────────
@app.route('/api/search')
@limiter.limit("60 per minute")
def fused_search():
    """Reciprocal Rank Fusion of FTS5 keyword + semantic vector search.

    Returns top results with match_sources=['keyword','semantic'] per org,
    enabling honest "why this appeared" labels in the UI.

    RRF formula: score(d) = Σ 1/(60 + rank_i(d)) across paths.
    k=60 is the standard constant; documents in both paths rank highest.
    """
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({"error": "q param required"}), 400

    ck = _ck('fused', q)
    cached = _cget(ck, 'search')
    if cached:
        return jsonify(cached)

    RRF_K   = 60
    CAND_N  = 100   # candidates from each path before fusion
    RESULT_N = 20   # final fused results

    db = get_db()

    # ── Path 1: FTS5 keyword ─────────────────────────────────────────────────
    kw_eins: list[str] = []
    if _check_fts(db):
        try:
            fts_q = _sanitize_fts_query(q)
            rows = db.execute(
                "SELECT ein FROM org_fts WHERE org_fts MATCH ? "
                "ORDER BY bm25(org_fts, 10, 5, 1, 1) LIMIT ?",
                (fts_q, CAND_N)
            ).fetchall()
            kw_eins = [r[0] for r in rows]
        except Exception:
            kw_eins = []

    # ── FAST PATH: If FTS has enough results, skip semantic (avoid GPU) ─────────
    sem_eins: list[str] = []
    use_fast_path = len(kw_eins) >= RESULT_N  # If FTS has 20+, skip semantic

    if not use_fast_path:
        # ── Path 2: Semantic vector ───────────────────────────────────────────
        if not _emb_loaded:
            _load_embeddings()
        if _emb_matrix is not None and len(_emb_matrix) > 0:
            vec = _embed_query(q)
            if vec is not None:
                sem_eins = _vec_similar(vec, exclude_ein="", limit=CAND_N)

    # ── RRF fusion ────────────────────────────────────────────────────────────
    rrf: dict[str, float] = {}
    kw_set  = set(kw_eins)
    sem_set = set(sem_eins)

    for rank, ein in enumerate(kw_eins, 1):
        rrf[ein] = rrf.get(ein, 0.0) + 1.0 / (RRF_K + rank)
    for rank, ein in enumerate(sem_eins, 1):
        rrf[ein] = rrf.get(ein, 0.0) + 1.0 / (RRF_K + rank)

    fused_eins = sorted(rrf, key=lambda e: rrf[e], reverse=True)

    # ── Apply surge boosts (event-driven: add relevant orgs even if not in keyword/semantic) ─────────────
    # Check if there are active boosts for this query's detected event
    active_boosts = db.execute("""
        SELECT DISTINCT b.ein, b.relevance_score, s.event_type
        FROM surge_boosts b
        JOIN surge_detections s ON b.surge_id = s.id
        WHERE b.status = 'active'
          AND b.expires_at > datetime('now')
          AND (? LIKE '%' || s.query || '%' OR s.query LIKE '%' || ? || '%')
    """, (q, q)).fetchall()

    boost_eins = {dict(b)['ein']: dict(b) for b in active_boosts}

    if boost_eins:
        # ADD boosted orgs to results (not just re-rank existing ones)
        # This is critical for event-driven discovery: during "hurricane", boost disaster relief orgs
        existing_boosted = [e for e in fused_eins if e in boost_eins]
        new_boosted = [e for e in boost_eins if e not in fused_eins]
        # Add synthetic RRF score for new boosted orgs (higher than typical RRF to sort first)
        for ein in new_boosted:
            rrf[ein] = 0.05  # Synthetic boost score (higher than most RRF results)
        # Put existing boosted first, then new boosted, then unboosted
        unboosted = [e for e in fused_eins if e not in boost_eins]
        fused_eins = existing_boosted + new_boosted + unboosted
        # Log that boosts were applied
        app.logger.info(f"search_surge_boost: q='{q}' existing={len(existing_boosted)} new={len(new_boosted)} event_types={set(b['event_type'] for b in boost_eins.values())}")

    # ── Fetch org details (deductible 501c3s only) ────────────────────────────
    fetch_n = min(RESULT_N * 3, len(fused_eins))
    if not fused_eins:
        return jsonify({"results": [], "query": q, "mode": "fused", "total": 0})

    placeholders = ",".join("?" * fetch_n)
    cols = """r.EIN, r.organization_name, r.NTEE1, r.CITY, r.STATE, r.total_revenue,
              r.ntee1_percentile, r.peer_percentile, r.peer_group, r.revenue_band,
              r.latest_tax_year, r.data_source, r.merit_tier, r.merit_score, r.merit_band,
              CASE WHEN r.months_of_reserve BETWEEN -120 AND 120
                   THEN r.months_of_reserve ELSE NULL END as months_of_reserve,
              r.net_assets, r.is_hidden_gem, r.cause_tags,
              r.donate_url, r.donate_platform, r.donate_url_status,
              SUBSTR(r.mission, 1, 300) as mission, r.mission_source,
              (r.mission IS NOT NULL AND r.mission != '') as has_mission,
              (r.website  IS NOT NULL AND r.website  != '') as has_website,
              v4.visibility_tier, v4.financial_health, v4.operating_model, v4.revenue_band as v4_revenue_band,
              v4.peer_cell_size, v4.metrics_json, v4.percentiles_json"""
    rows = db.execute(
        f"""SELECT {cols} FROM registry_enriched r
            LEFT JOIN v4_scores v4 ON r.EIN = v4.EIN
            WHERE r.EIN IN ({placeholders}) AND {_DEDUCTIBILITY_FILTER}""",
        fused_eins[:fetch_n]
    ).fetchall()

    org_map = {dict(r)['EIN']: _attach_v4_scores(dict(r), r) for r in rows}

    results = []
    for ein in fused_eins:
        if len(results) >= RESULT_N:
            break
        org = org_map.get(ein)
        if org is None:
            continue
        # Annotate match sources for "why this appeared" UI label
        sources = []
        if ein in kw_set:
            sources.append('keyword')
        if ein in sem_set:
            sources.append('semantic')
        org['match_sources'] = sources
        org['rrf_score']     = round(rrf[ein], 6)
        # Add surge boost indicator if applicable
        if ein in boost_eins:
            org['surge_boosted'] = True
            org['surge_reason'] = boost_eins[ein].get('event_type', 'event-driven')
        if org.get('cause_tags'):
            try:
                org['cause_tags'] = json.loads(org['cause_tags'])
            except (json.JSONDecodeError, TypeError):
                org['cause_tags'] = None
        results.append(_strip_scores(org))

    # Set mode indicator: fts-only (fast path) or fused (semantic included)
    mode = "fts-only" if use_fast_path else "fused"
    out = {"results": results, "query": q, "mode": mode, "total": len(results)}
    _cset(ck, out)
    return jsonify(out)


# ── Well-known / security ──────────────────────────────────────────────────
@app.route('/.well-known/security.txt')
def security_txt():
    return app.response_class(
        response="""Contact: mailto:security@daanaa.org\nPreferred-Languages: en\nPolicy: https://daanaa.org/legal\nExpires: 2027-06-01T00:00:00.000Z\n""",
        status=200,
        mimetype='text/plain',
    )


# ── Admin: Surge monitoring (human oversight of AI agent actions) ──────────────
@app.route('/api/admin/surge-boosts', methods=['GET'])
@limiter.exempt
def admin_surge_boosts():
    """[ADMIN ONLY] View active surge boosts and metrics. Principle #6/#10: oversight."""
    provided = request.headers.get('X-Admin-Key', '')
    if not _ADMIN_KEY or not hmac.compare_digest(provided, _ADMIN_KEY):
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    boosts = db.execute("""
        SELECT b.id, b.ein, s.query, s.event_type, b.relevance_reason,
               b.boosted_at, b.expires_at, b.status, b.clicks, b.donations, r.organization_name
        FROM surge_boosts b
        JOIN surge_detections s ON b.surge_id = s.id
        LEFT JOIN registry_enriched r ON b.ein = r.EIN
        ORDER BY b.boosted_at DESC LIMIT 100
    """).fetchall()
    return jsonify({"boosts": [dict(b) for b in boosts], "count": len(boosts)})

@app.route('/api/admin/surge-boosts/<int:boost_id>/override', methods=['POST'])
@limiter.exempt
def admin_override_boost(boost_id):
    """[ADMIN ONLY] Pause/override a surge boost. Principle #6: correct mistakes quickly."""
    provided = request.headers.get('X-Admin-Key', '')
    if not _ADMIN_KEY or not hmac.compare_digest(provided, _ADMIN_KEY):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or 'admin override').strip()[:200]
    db = get_db()
    db.execute(
        "UPDATE surge_boosts SET status='overridden', overridden_at=datetime('now'), override_reason=? WHERE id=?",
        (reason, boost_id)
    )
    db.commit()
    app.logger.info(f"admin_override_boost: id={boost_id} reason={reason}")
    return jsonify({"status": "overridden", "boost_id": boost_id})


# ── Frontend static serving ────────────────────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, 'index.html')


# Eager load so gunicorn --preload populates the matrix in the master process
# before forking workers. Workers inherit via CoW without re-reading the DB.
_load_embeddings()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
