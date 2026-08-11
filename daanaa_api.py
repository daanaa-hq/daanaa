#!/usr/bin/env python3
"""
Daanaa API — Peer-context nonprofit directory backend
Serves registry_enriched + v4 scores to frontend
"""
import sqlite3, os, json, functools, time, hashlib, hmac, threading, re, secrets, logging, sys
import urllib.parse
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timezone, timedelta
import traceback
from difflib import get_close_matches

# Sentry error tracking — activate by setting SENTRY_DSN env var.
try:
    import sentry_sdk
    _sentry_dsn = os.environ.get("SENTRY_DSN", "")
    if _sentry_dsn:
        sentry_sdk.init(
            dsn=_sentry_dsn,
            traces_sample_rate=0.1,   # 10% of requests traced
            profiles_sample_rate=0.05,
            environment=os.environ.get("DAANAA_ENV", "production"),
            release=os.environ.get("GIT_COMMIT", "unknown"),
            # Never capture PII — no user emails, IPs, or request bodies in Sentry
            send_default_pii=False,
        )
except ImportError:
    pass  # Sentry optional
import numpy as np
import requests as _http
from flask import Flask, jsonify, request, g, abort, send_from_directory, Blueprint
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

# P6 Phase 3 Issue #8: Cache invalidation system (20x staleness improvement)
try:
    from cache_manager import CacheManager, write_invalidation_marker
    _cache_manager_available = True
except ImportError:
    _cache_manager_available = False
    # Fallback: basic dict cache if CacheManager not available
    class CacheManager:
        def __init__(self, **kwargs):
            self.data = {}
            self.ttl = {}
        def set(self, key, value, ttl=600, scope="org"):
            self.data[f"{scope}:{key}"] = (value, time.time() + ttl)
        def get(self, key, scope="org"):
            full_key = f"{scope}:{key}"
            if full_key in self.data:
                val, exp = self.data[full_key]
                if time.time() < exp:
                    return val
                del self.data[full_key]
            return None
    def write_invalidation_marker(scope, marker_dir="/tmp"):
        pass  # No-op fallback

try:
    from ntee_synonyms import expand_query_with_synonyms
except ImportError:
    def expand_query_with_synonyms(q):
        return q  # Fallback: return query as-is if synonyms not available

# IRS Eligibility Helper — Phase 2 integration
try:
    from scripts.irs_eligibility_helper import (
        initialize_helper as init_irs_eligibility,
        get_eligibility_fields,
        should_show_profile_publicly,
    )
    _irs_eligibility_available = True
except Exception as e:
    _irs_eligibility_available = False
    print(f"[Startup] ⚠ IRS eligibility helper not available: {e}", file=sys.stderr)
    # Fallback functions if helper unavailable
    def get_eligibility_fields(ein):
        return {
            "irs_eligibility_status": "unknown",
            "irs_eligibility_checked_at": None,
            "irs_eligibility_sources": [],
            "irs_eligibility_explanation": "Helper unavailable"
        }
    def should_show_profile_publicly(ein):
        return True

# Search Phase 2: intent classifier (loaded at startup for preload safety)
try:
    from scripts.search_intent_classifier import SearchIntentClassifier
    _classifier_available = True
    print(f"[Startup] ✓ SearchIntentClassifier imported successfully", file=sys.stderr)
except Exception as e:
    _classifier_available = False
    print(f"[Startup] ✗ Failed to import SearchIntentClassifier: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
_classifier_instance = None  # lazy per-worker instance (created on first search)

# Search Phase 2: semantic reranker (lazy per-worker, only for cause queries)
try:
    from scripts.search_semantic_reranker import SearchSemanticReranker
    _reranker_available = True
    print(f"[Startup] ✓ SearchSemanticReranker imported successfully", file=sys.stderr)
except Exception as e:
    _reranker_available = False
    print(f"[Startup] ✗ Failed to import SearchSemanticReranker: {type(e).__name__}: {e}", file=sys.stderr)
_reranker_instance = None  # lazy per-worker instance (created on first cause query)

# Intent signals and event discovery (additive, feature-flagged)
try:
    import intent_layer
    _intent_available = True
    print(f"[Startup] ✓ intent_layer imported successfully", file=sys.stderr)
except Exception as e:
    _intent_available = False
    print(f"[Startup] ✗ Failed to import intent_layer: {type(e).__name__}: {e}", file=sys.stderr)

try:
    import event_discovery_engine
    _discovery_available = True
    print(f"[Startup] ✓ event_discovery_engine imported successfully", file=sys.stderr)
except Exception as e:
    _discovery_available = False
    print(f"[Startup] ✗ Failed to import event_discovery_engine: {type(e).__name__}: {e}", file=sys.stderr)

# Profile contexts and shared context management
try:
    from scripts import profile_contexts
    _profile_contexts_available = True
    print(f"[Startup] ✓ profile_contexts imported successfully", file=sys.stderr)
except Exception as e:
    _profile_contexts_available = False
    print(f"[Startup] ✗ Failed to import profile_contexts: {type(e).__name__}: {e}", file=sys.stderr)


def _ensure_student_service_columns(db_path: str):
    """Add student service columns to existing tables if they don't exist.

    SQLite doesn't support IF NOT EXISTS in ALTER TABLE, so we check first
    and add columns only if missing.
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # Helper to check if column exists
        def column_exists(table_name, col_name):
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                cols = {row[1] for row in cursor.fetchall()}
                return col_name in cols
            except:
                return False

        # Add columns to volunteer_hours if missing
        if column_exists('volunteer_hours', 'student_id') == False:
            try:
                cursor.execute("ALTER TABLE volunteer_hours ADD COLUMN student_id TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass

        if column_exists('volunteer_hours', 'student_school_ein') == False:
            try:
                cursor.execute("ALTER TABLE volunteer_hours ADD COLUMN student_school_ein TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass

        if column_exists('volunteer_hours', 'parental_consent_given') == False:
            try:
                cursor.execute("ALTER TABLE volunteer_hours ADD COLUMN parental_consent_given BOOLEAN DEFAULT 0")
                conn.commit()
            except sqlite3.OperationalError:
                pass

        # Add column to nonprofit_accounts if missing
        if column_exists('nonprofit_accounts', 'parent_school_ein') == False:
            try:
                cursor.execute("ALTER TABLE nonprofit_accounts ADD COLUMN parent_school_ein TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
    finally:
        conn.close()


def _run_migrations(db_path: str):
    """Run pending database migrations from migrations/ directory.

    Statement-level tolerance (2026-07-12, see LESSONS.md): migrations
    002 and 003 both CREATE TABLE org_nonprofit_updates with different
    schemas. On a fresh DB, 002 runs first and "wins" (CREATE TABLE IF
    NOT EXISTS no-ops for 003), so 003's own CREATE INDEX on a
    003-only column then fails with "no such column". The old code had
    no per-statement handling, so that exception propagated out, left
    `conn` open (never committed/closed — a leaked lock on db_path), and
    silently abandoned every later migration file including 004/phase3.
    A concurrent connection to the same file (e.g. the next call in this
    same startup) could then transiently hit "database is locked" until
    the leaked connection was garbage-collected. Catching per-statement
    and always closing the connection fixes both the schema-collision
    symptom and the connection leak that caused it.
    """
    migration_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    if not os.path.isdir(migration_dir):
        return

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # Get list of already-run migrations from metadata table (if it exists)
        try:
            cursor.execute('SELECT migration_name FROM _migration_log')
            run_migrations = {row[0] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            # Create log table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS _migration_log (
                    migration_name TEXT PRIMARY KEY,
                    run_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            run_migrations = set()

        # Run .sql files in alphabetical order
        for filename in sorted(os.listdir(migration_dir)):
            if not filename.endswith('.sql'):
                continue

            if filename in run_migrations:
                continue

            migration_path = os.path.join(migration_dir, filename)
            with open(migration_path, 'r') as f:
                sql = f.read()

            # Execute migration (can be multiple statements). Continue past a
            # failing statement instead of aborting the whole file — a
            # collision on one CREATE/ALTER must not block every later
            # migration file from running.
            for statement in sql.split(';'):
                stmt = statement.strip()
                if stmt:
                    try:
                        cursor.execute(stmt)
                    except sqlite3.OperationalError as e:
                        _logger.warning(f'Migration statement skipped in {filename}: {e}')

            # Log that we ran it
            cursor.execute('INSERT INTO _migration_log (migration_name) VALUES (?)', (filename,))
            _logger.info(f'Ran migration: {filename}')

        conn.commit()
    except Exception as e:
        _logger.error(f'Migration error: {e}', exc_info=True)
        # Don't fail startup — migrations are best-effort
    finally:
        conn.close()

# Add scripts directory to path for email service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
try:
    from email_service import (
        get_email_service,
        hours_verified_email,
        hours_rejected_email,
        claim_received_email,
        claim_verified_email,
    )
except ImportError:
    get_email_service = None
    claim_received_email = None
    claim_verified_email = None

try:
    from nonprofit_portal_endpoints import register_nonprofit_endpoints, register_phase3_endpoints
except ImportError:
    register_nonprofit_endpoints = None
    register_phase3_endpoints = None

_logger = logging.getLogger(__name__)

# Firebase token verification using public keys — no service account file required.
# Firebase publishes its signing certs at a well-known URL; cached for 1 hour.
import jwt as _pyjwt

_FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', 'daanaa-af9c2')
_FIRESTORE_PROJECT_ID = os.environ.get('FIRESTORE_PROJECT_ID', 'daanaa-af9c2')
_FIRESTORE_API_KEY = os.environ.get('FIRESTORE_API_KEY', '')
_FIRESTORE_BASE_URL = f'https://firestore.googleapis.com/v1/projects/{_FIRESTORE_PROJECT_ID}/databases/(default)/documents'

_FIREBASE_PUBKEYS_URL = (
    'https://www.googleapis.com/robot/v1/metadata/x509/'
    'securetoken@system.gserviceaccount.com'
)
_firebase_pubkeys: dict = {}
_firebase_pubkeys_expires: float = 0.0

# E2E wallet rate limiting: simple in-memory per-IP counter (no deps).
import collections as _collections
_wallet_rate: dict = _collections.defaultdict(list)
_WALLET_RATE_LIMIT = 10   # POST per minute per IP
_WALLET_MAX_BYTES = 65536  # 64KB max payload


def _get_firebase_pubkeys() -> dict:
    global _firebase_pubkeys, _firebase_pubkeys_expires
    if time.time() < _firebase_pubkeys_expires and _firebase_pubkeys:
        return _firebase_pubkeys
    try:
        resp = _http.get(_FIREBASE_PUBKEYS_URL, timeout=5)
        resp.raise_for_status()
        _firebase_pubkeys = resp.json()
        cc = resp.headers.get('Cache-Control', '')
        max_age = 3600
        for part in cc.split(','):
            part = part.strip()
            if part.startswith('max-age='):
                try: max_age = int(part.split('=')[1])
                except ValueError: pass
        _firebase_pubkeys_expires = time.time() + max_age
    except Exception:
        pass
    return _firebase_pubkeys


def _require_firebase_user() -> str:
    """Verify Firebase ID token via Firebase public certs. Returns firebase_uid or aborts 401."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        abort(401)
    token = auth_header[7:]
    try:
        from cryptography.x509 import load_pem_x509_certificate
        header = _pyjwt.get_unverified_header(token)
        kid = header.get('kid', '')
        pubkeys = _get_firebase_pubkeys()
        if kid not in pubkeys:
            abort(401)
        cert = load_pem_x509_certificate(pubkeys[kid].encode())
        pub_key = cert.public_key()
        decoded = _pyjwt.decode(
            token, pub_key,
            algorithms=['RS256'],
            audience=_FIREBASE_PROJECT_ID,
            issuer=f'https://securetoken.google.com/{_FIREBASE_PROJECT_ID}',
        )
        uid = decoded.get('sub', '')
        if not uid:
            abort(401)
        return uid
    except Exception:
        abort(401)


def _firestore_value(val) -> dict:
    """Convert Python value to Firestore value format."""
    if val is None:
        return {'nullValue': None}
    elif isinstance(val, bool):
        return {'booleanValue': val}
    elif isinstance(val, (int, float)):
        return {'doubleValue': float(val)} if isinstance(val, float) else {'integerValue': str(val)}
    elif isinstance(val, str):
        return {'stringValue': val}
    elif isinstance(val, list):
        return {'arrayValue': {'values': [_firestore_value(v) for v in val]}}
    elif isinstance(val, dict):
        return {'mapValue': {'fields': {k: _firestore_value(v) for k, v in val.items()}}}
    else:
        return {'stringValue': str(val)}


def _firestore_unpack(fval: dict):
    """Convert Firestore value format to Python value."""
    if 'nullValue' in fval:
        return None
    elif 'booleanValue' in fval:
        return fval['booleanValue']
    elif 'integerValue' in fval:
        return int(fval['integerValue'])
    elif 'doubleValue' in fval:
        return float(fval['doubleValue'])
    elif 'stringValue' in fval:
        return fval['stringValue']
    elif 'arrayValue' in fval:
        return [_firestore_unpack(v) for v in fval['arrayValue'].get('values', [])]
    elif 'mapValue' in fval:
        return {k: _firestore_unpack(v) for k, v in fval['mapValue'].get('fields', {}).items()}
    elif 'timestampValue' in fval:
        return fval['timestampValue']
    return None


def _firestore_get(collection: str, document: str, user_id: str = None) -> dict:
    """Fetch a document from Firestore. If user_id is provided, prepends it to path."""
    try:
        if user_id:
            path = f'{user_id}/{collection}/{document}'
        else:
            path = f'{collection}/{document}'

        url = f'{_FIRESTORE_BASE_URL}/{path}'
        resp = _http.get(url, params={'key': _FIRESTORE_API_KEY}, timeout=5)

        if resp.status_code == 404:
            return None
        resp.raise_for_status()

        doc = resp.json()
        if 'fields' not in doc:
            return None

        return {k: _firestore_unpack(v) for k, v in doc['fields'].items()}
    except Exception as e:
        _logger.error(f"Firestore GET error: {e}")
        return None


def _firestore_set(collection: str, document: str, data: dict, user_id: str = None, merge: bool = False) -> bool:
    """Set a document in Firestore."""
    try:
        if user_id:
            path = f'{user_id}/{collection}/{document}'
        else:
            path = f'{collection}/{document}'

        url = f'{_FIRESTORE_BASE_URL}/{path}'
        body = {
            'fields': {k: _firestore_value(v) for k, v in data.items()}
        }

        params = {'key': _FIRESTORE_API_KEY}
        if merge:
            params['updateMask.fieldPaths'] = list(data.keys())

        resp = _http.patch(url, json=body, params=params, timeout=5)
        resp.raise_for_status()
        return True
    except Exception as e:
        _logger.error(f"Firestore SET error: {e}")
        return False


def _firestore_delete(collection: str, document: str, user_id: str = None) -> bool:
    """Delete a document from Firestore."""
    try:
        if user_id:
            path = f'{user_id}/{collection}/{document}'
        else:
            path = f'{collection}/{document}'

        url = f'{_FIRESTORE_BASE_URL}/{path}'
        resp = _http.delete(url, params={'key': _FIRESTORE_API_KEY}, timeout=5)
        resp.raise_for_status()
        return True
    except Exception as e:
        _logger.error(f"Firestore DELETE error: {e}")
        return False


def _firestore_list(collection: str, user_id: str = None) -> list:
    """List all documents in a collection."""
    try:
        if user_id:
            path = f'{user_id}/{collection}'
        else:
            path = collection

        url = f'{_FIRESTORE_BASE_URL}/{path}'
        resp = _http.get(url, params={'key': _FIRESTORE_API_KEY}, timeout=5)
        resp.raise_for_status()

        data = resp.json()
        docs = data.get('documents', [])

        return [{
            'id': doc['name'].split('/')[-1],
            **{k: _firestore_unpack(v) for k, v in doc.get('fields', {}).items()}
        } for doc in docs]
    except Exception as e:
        _logger.error(f"Firestore LIST error: {e}")
        return []


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
    "Financial Health compares an organization with similar ones in its peer group. "
    "It does not measure mission impact, program quality, governance, or legitimacy. "
    "Please verify anything that matters to you before giving. "
    "Our full method and its limits are at daanaa.org/methodology."
)

UNSCORED_DISCLOSURE = (
    "We do not have IRS revenue or expense data for this organization yet. "
    "That is common for smaller and newer groups, and it says nothing about their health or their work. "
    "To learn more, check their 501(c)(3) status on IRS.gov, ask them for a recent Form 990, or reach out directly. "
    "If you run this organization, you can claim its page and add your numbers at daanaa.org/for-nonprofits."
)

SELF_REPORTED_DISCLAIMER = (
    "These figures were shared by the organization itself. "
    "We have not independently checked them, so if the numbers matter to your decision, "
    "we suggest asking for a recent Form 990. "
    "Daanaa is not responsible for the accuracy of self-reported information."
)

BETA_WEBSITE_DISCLOSURE = (
    "We found this website through an automated search and confirmed it loads, "
    "but the organization has not verified it with us. "
    "Please double-check it through their official channels before relying on it. "
    "Organizations can claim and update their details at daanaa.org/for-nonprofits."
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

# P6 Phase 3 Issue #8: Initialize cache manager for event-driven invalidation
_cache = CacheManager(marker_dir="/tmp")

def _ck(ns: str, *parts) -> str:
    raw = ns + ':' + ':'.join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def _cget(key: str, ttl_ns: str):
    """Get from cache (uses CacheManager for TTL + event invalidation)"""
    ttl = _CACHE_TTL.get(ttl_ns, 300)
    return _cache.get(key, scope=ttl_ns, ttl=ttl)

def _cset(key: str, value):
    """Set in cache and write invalidation marker"""
    # Store with automatic TTL based on key scope
    # Infer scope from common cache patterns
    scope = 'org' if key.startswith('org:') else 'search'
    for scope_name, ttl in _CACHE_TTL.items():
        if key.startswith(scope_name):
            scope = scope_name
            break
    _cache.set(key, value, ttl=_CACHE_TTL.get(scope, 300), scope=scope)
    # Write marker for pipeline to pick up
    write_invalidation_marker(scope)

def _int_arg(name: str, default: int, lo: int = 0, hi: int = 1000) -> int:
    """Read an int query param, clamped to [lo, hi]; bad input → default
    (a stray ?limit=abc must never become a bare 500)."""
    try:
        return max(lo, min(int(request.args.get(name, default)), hi))
    except (TypeError, ValueError):
        return default

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

# Strip EVERYTHING that isn't a word character or whitespace. FTS5 assigns
# syntax meaning to far more than quotes and parens: '-' is column-NOT
# ("TRIPLE-CORD" → error "no such column: CORD"), ':' is a column filter,
# '/' is a syntax error. The old narrower strip list let hyphenated org names
# crash 4.3% of small-org self-searches (2026-07-18 audit).
# Apostrophes FUSE instead of split: IRS stores "L'ANSE" as "LANSE" and
# "O'BRIEN" as "OBRIEN", so "L'Anse" must become the token "LAnse", not "L Anse".
_FTS5_APOS  = re.compile(r"['’`]")
_FTS5_STRIP = re.compile(r'[^\w\s]', re.UNICODE)

# Words people commonly type before/around a location or cause that don't
# appear in org records — stripping them prevents 0-result dead ends.
# 'metro' and 'greater' are geographic modifiers: "Portland metro" / "Greater LA"
# — the metro column stores "Portland-Vancouver-Hillsboro, OR-WA", not "metro Portland"
_FTS5_NOISE = frozenset({
    'nonprofit', 'nonprofits', 'charity', 'charities',
    'organization', 'organizations', '501c3', 'ngo',
    'find', 'search', 'best', 'top', 'local', 'near',
    'metro', 'greater', 'region', 'area',
})

# Detect a standalone 5-digit US zip code anywhere in a query string.
_ZIP_RE = re.compile(r'\b(\d{5})\b')

def _extract_zip(text: str) -> tuple[str, str | None]:
    """Return (text_without_zip, zip_code_or_None).
    Strips the first 5-digit zip found so FTS doesn't choke on numbers."""
    m = _ZIP_RE.search(text)
    if not m:
        return text, None
    return (text[:m.start()] + text[m.end():]).strip(), m.group(1)

def _sanitize_fts_query(text: str) -> str:
    """Convert a donor query string to a valid FTS5 MATCH expression.

    Handles the common location search patterns that would otherwise error
    or return 0 results:
      - 'Bend, OR'             comma stripped → 'Bend* or*'
      - 'St. Louis MO'         period stripped → 'St* Louis* MO*'
      - "L'Anse MI"            apostrophe stripped → 'L* Anse* MI*'
      - 'Bend OR'              OR lowercased → 'Bend* or*' (not boolean op)
      - 'nonprofits in Bend'   noise word stripped → 'in* Bend*'
      - 'Portland metro'       metro stripped → 'Portland*'
      - 'Greater Portland'     greater stripped → 'Portland*'
      - 'food bank 97701'      zip stripped by caller (_extract_zip) before here
      - 'find charities near'  noise words stripped → fallback empty query
    """
    clean = _FTS5_STRIP.sub(' ', _FTS5_APOS.sub('', text))
    words = [w for w in clean.split() if w.lower() not in _FTS5_NOISE]
    # Single-char tokens (the "4" and "H" of "4-H") survive only alongside
    # other tokens — a lone "a"* would prefix-scan the whole index.
    if len(words) >= 2:
        words = words[:12]
    else:
        words = [w for w in words if len(w) >= 2]
    if not words:
        return '""'
    # Double-quote every token: AND/OR/NOT/NEAR typed by a donor stay literal
    # words, never operators. '"tok"*' is FTS5 phrase-prefix syntax.
    # Single-char tokens match EXACTLY (no star): the "N" of "N A B S" is the
    # token "n" in the org's own name, and '"n"*' would range-scan every
    # n-word in the term dictionary — 15s+ timeouts on the 2GB droplet.
    return ' '.join(f'"{w}"*' if len(w) >= 2 else f'"{w}"' for w in words)

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

# DB_PATH must be defined HERE, not further down (2026-08-08). _load_embeddings()
# references it and is called during startup at module scope, well before the old
# definition site ~40 lines below. Python resolves globals at call time, so that
# call raised NameError -- swallowed by the startup try/except, which printed
# "[embeddings] load failed" and continued. Net effect: all 546K embeddings
# silently failed to load on every boot and semantic search ran degraded, while
# startup reported "✓ Embeddings loaded, search ready".
DB_PATH = os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/merit_registry.db"))

# Run database migrations on startup
_db_path = DB_PATH
_run_migrations(_db_path)
_ensure_student_service_columns(_db_path)

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
CORS(app, origins=_ALLOWED_ORIGINS, supports_credentials=True)

# Rate limiting — backs off abusive callers without blocking normal use
limiter = Limiter(
    key_func=_real_ip,
    app=app,
    default_limits=["200 per minute", "2000 per hour"],
    storage_uri="memory://",
)

# Pre-load embeddings on startup to avoid cold-start delay
# This blocks startup by ~5s but makes first query instant instead of 7s
print("[startup] Pre-loading 546K embeddings for semantic search...", flush=True)
try:
    _load_embeddings()
    # _load_embeddings() catches its OWN exceptions internally and never
    # re-raises (see its body) -- it prints "[embeddings] load failed" and
    # returns normally either way. So this try/except can never actually
    # fire, and a blind "call it, print success" here reports success
    # unconditionally regardless of outcome. That is the deeper version of
    # the 2026-08-08 embeddings incident: fixing the one known failure cause
    # (DB_PATH ordering) did not fix this shape, which would silently
    # misreport the NEXT failure the same way. Check the real outcome.
    if _emb_loaded:
        print("[startup] ✓ Embeddings loaded, search ready", flush=True)
    else:
        print("[startup] ⚠ Embeddings did not load — see [embeddings] log line above; search degraded to keyword-only", flush=True)
except Exception as e:
    print(f"[startup] ⚠ Embedding pre-load failed: {e}", flush=True)

# Initialize IRS Eligibility Helper for Phase 2
if _irs_eligibility_available:
    try:
        # Repository-relative manifest path (not hard-coded home directory)
        repo_root = os.path.dirname(os.path.abspath(__file__))
        manifest_path = os.path.join(repo_root, "data/irs_authority/v6_eligibility/eligibility_manifest.json")
        init_irs_eligibility(
            db_path=_db_path,
            manifest_path=manifest_path
        )
        print("[startup] ✓ IRS eligibility helper initialized", flush=True)
    except Exception as e:
        print(f"[startup] ⚠ IRS eligibility helper initialization failed: {e}", flush=True)

# Register nonprofit portal endpoints
if register_nonprofit_endpoints:
    register_nonprofit_endpoints(app)

# Register Phase 3 endpoints (letter credits, donor tracking, impact dashboard)
if register_phase3_endpoints:
    register_phase3_endpoints(app)

# JSON error handler — return proper JSON for API endpoints instead of HTML error pages
@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(error):
    """Return JSON errors for API endpoints, HTML for others."""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': error.description or 'Request failed',
            'status': error.code
        }), error.code
    # For non-API endpoints, let Flask handle the error normally
    return error

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
# Default: true (scores are on). Toggle: ENABLE_SCORES=false python3 daanaa_api.py
ENABLE_SCORES: bool = os.environ.get("ENABLE_SCORES", "true").lower() == "true"

# ENABLE_V4_SCORES=true → include v4.0 financial health scores (financial_health,
# operating_model, revenue_band, peer_cell_size) in org responses.
# Default: true (v4 scores enabled). Toggle: ENABLE_V4_SCORES=false python3 daanaa_api.py
ENABLE_V4_SCORES: bool = os.environ.get("ENABLE_V4_SCORES", "true").lower() == "true"

# ENABLE_V4_METRICS=true → include detailed metrics_json and percentiles_json
# in v4 responses (transparency/audit trail). Default: false.
ENABLE_V4_METRICS: bool = os.environ.get("ENABLE_V4_METRICS", "false").lower() == "true"

# ── Intent & Event Discovery (Phase 2, additive, feature-flagged) ────────────────
# ENABLE_INTENT_SIGNALS=true → record anonymous workflow signals (volunteer, give, etc.)
# Keep this OFF until event_claiming system is stable. Default: false.
ENABLE_INTENT_SIGNALS: bool = os.environ.get("ENABLE_INTENT_SIGNALS", "false").lower() == "true"

# ENABLE_EVENT_DISCOVERY=true → run event discovery engine and populate review queue.
# Keep this OFF until claiming system is stable. Default: false.
ENABLE_EVENT_DISCOVERY: bool = os.environ.get("ENABLE_EVENT_DISCOVERY", "false").lower() == "true"

# ── Profile Contexts (Phase 3, additive, feature-flagged) ────────────────
# ENABLE_PROFILE_CONTEXTS=true → support shared contexts (household, DAF, business).
# Default: false. Enable after claiming system + intent/discovery stabilize.
ENABLE_PROFILE_CONTEXTS: bool = os.environ.get("ENABLE_PROFILE_CONTEXTS", "false").lower() == "true"

_SCORE_FIELDS = ("merit_score", "merit_tier", "merit_band")
_V4_FIELDS = ("financial_health", "operating_model", "revenue_band", "peer_cell_size")

# Legal posture (2026-06-10): Daanaa is a discovery platform, not a fundraising
# platform. Donation link data is internal-only (claim flow + admin) and must
# never appear in a public response. Enforced here at the serialization choke
# point so SELECT * routes can't leak it. Guarded by tests/test_no_public_donation_fields.py.
_DONATE_FIELDS = (
    "donate_url", "donate_platform", "donate_url_status", "donate_confidence",
    "donate_source_page", "donate_identity_match", "donate_human_review",
    "donate_checked_at", "donate_ineligible_reason", "donate_confirmed",
)

def _strip_scores(org: dict) -> dict:
    """Public-response scrub: null score fields when ENABLE_SCORES is false.
    Applied to every public org payload. Donate fields are now returned for
    frontend display (AI-assisted status, org can claim to verify)."""
    # Note: _DONATE_FIELDS are now returned publicly (2026-07-05 decision).
    # Backend extracts donate links nightly; frontend displays with 'ai_suggested'
    # status. Orgs can claim/verify in the claim flow. Legal posture: discovery
    # platform, hand-off to org's own processor (never handle funds).
    if ENABLE_SCORES:
        return org
    return {k: (None if k in _SCORE_FIELDS else v) for k, v in org.items()}

def _attach_v4_scores(org: dict, v4_row: sqlite3.Row | None) -> dict:
    """V4 scores disabled (v5 only). Returns org unchanged."""
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
_claim_secret_raw = (
    os.environ.get("DAANAA_CLAIM_SECRET")
    or os.environ.get("DAANAA_ADMIN_KEY")
)
if not _claim_secret_raw:
    if os.environ.get("DAANAA_PROD"):
        # Fail closed: a known dev secret in prod = forgeable claim-verify tokens.
        raise RuntimeError(
            "DAANAA_PROD is set but neither DAANAA_CLAIM_SECRET nor "
            "DAANAA_ADMIN_KEY is configured — refusing to start with the dev secret."
        )
    _claim_secret_raw = "daanaa-dev-claim-secret"
_CLAIM_SECRET = _claim_secret_raw.encode()

# Booking secret for event signup cancellation tokens — scoped separately so
# cancellation tokens cannot be confused with claim-verify tokens.
_BOOKING_SECRET = os.environ.get("DAANAA_BOOKING_SECRET", _claim_secret_raw).encode()

def _make_booking_token(event_id: int, email: str, nonce: str) -> str:
    return hmac.new(_BOOKING_SECRET, f"booking:{event_id}:{email}:{nonce}".encode(), hashlib.sha256).hexdigest()[:32]

def _make_event_short_id() -> str:
    return secrets.token_urlsafe(6)  # 8 url-safe base64 chars

def _make_verify_token(ein: str, pin: str) -> str:
    """Return HMAC-SHA256 hex token for the given EIN + PIN pair."""
    return hmac.new(_CLAIM_SECRET, f"{ein}:{pin}".encode(), hashlib.sha256).hexdigest()

def _make_approve_token(cp_id: int) -> str:
    """HMAC-signed one-click approve token scoped to a specific community partner ID."""
    secret = (_ADMIN_KEY or "dev").encode()
    return hmac.new(secret, f"approve-partner:{cp_id}".encode(), hashlib.sha256).hexdigest()


def _triage_partner_application(data: dict) -> str:
    """
    Ask the local LLM to review a new community partner application and return
    a brief assessment (2-4 sentences). Non-fatal: returns empty string on error.
    Runs synchronously but quickly — the LLM is local and fast.
    """
    try:
        prompt = (
            "You are reviewing a new business application to join the Daanaa Impact Network — "
            "a community of partners who offer genuine benefits to US nonprofits. "
            "Review the application below and provide a 2-4 sentence assessment covering: "
            "(1) whether the offer is clear and genuinely useful for nonprofits, "
            "(2) any red flags (vague, inflated, or unverifiable claims), and "
            "(3) a confidence level: HIGH / MEDIUM / LOW that this is a good-faith submission.\n\n"
            f"Business: {data.get('business_name', '')}\n"
            f"Category: {data.get('category', '')}\n"
            f"Offer: {data.get('offer', '')}\n"
            f"Reach: {data.get('service_area_type', '')}\n"
            f"Location: {data.get('location_city', '')} {data.get('location_state', '')} {data.get('location_country', '')}\n"
            f"Website: {data.get('website_url', '') or '(not provided)'}\n"
            f"Notes: {data.get('notes', '') or '(none)'}\n\n"
            "Assessment:"
        )
        resp = _http.post(
            "http://localhost:11437/v1/chat/completions",
            json={
                "model": "qwen2.5-32b",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.3,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return ""


# Admin key — set DAANAA_ADMIN_KEY env var before starting the API.
# Backward compatible with old MERIT_ADMIN_KEY env var name.
_ADMIN_KEY = (
    os.environ.get("DAANAA_ADMIN_KEY", "")
    or os.environ.get("MERIT_ADMIN_KEY", "")  # backward compat
)

def _check_admin_auth():
    """Check admin auth header; abort(401) if invalid."""
    provided = request.headers.get("X-Admin-Key", "")
    if not provided or not hmac.compare_digest(provided, _ADMIN_KEY):
        abort(401)

def require_admin_key(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        _check_admin_auth()
        return f(*args, **kwargs)
    return wrapper

def require_admin():
    """Callable guard for inline auth checks in route handlers."""
    _check_admin_auth()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH, timeout=30)
        db.row_factory = sqlite3.Row
        # 9.6 GB catalog: mmap serves cold page reads from the OS page cache
        # instead of read() syscalls, plus a 64 MB page cache per connection.
        # Biggest win on first-hit queries after a restart or cache expiry.
        db.execute("PRAGMA mmap_size=2147483648")
        db.execute("PRAGMA cache_size=-64000")
        db.execute("PRAGMA busy_timeout=30000")
        if _LIVE_SPLIT:
            db.execute("ATTACH DATABASE ? AS live", (LIVE_DB_PATH,))
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def log_audit_event(event_type: str, org_ein: str = None, user_auth: str = None,
                   user_role: str = None, success: bool = True, error_code: str = None,
                   **extra_fields):
    """
    Log compliance-friendly audit event (NO PII).

    Fields logged: event_type, timestamp, user_auth (Firebase UID), user_role, org_ein (EIN only),
    success, error_code, IP (anonymized), user agent (category only).

    Privacy invariants enforced:
    - NO email addresses, names, or full IPs
    - NO donor data or giving history
    - NO wallet data or balances
    - EIN-only org identification
    - Firebase UID or 'anonymous'
    """
    try:
        # Anonymize IP: zero last octet
        client_ip = request.remote_addr or 'unknown'
        try:
            parts = client_ip.split('.')
            if len(parts) == 4:
                parts[-1] = '0'
                ip_anon = '.'.join(parts)
            else:
                ip_anon = 'unknown'
        except:
            ip_anon = 'unknown'

        # Categorize user agent (NO full string)
        ua_string = (request.user_agent.string or '').lower()
        if 'mobile' in ua_string or 'android' in ua_string or 'iphone' in ua_string:
            ua_category = 'mobile'
        elif 'mozilla' in ua_string or 'chrome' in ua_string or 'safari' in ua_string:
            ua_category = 'browser'
        else:
            ua_category = 'unknown'

        # Prepare audit record (only these fields; no others)
        db = get_db()
        db.execute("""
            INSERT INTO audit_log (
                event_type, timestamp, user_auth, user_role, org_ein,
                ip_address_anonymized, user_agent_category,
                success, error_code,
                hours_submitted, hours_approved, status, volunteer_event_id, volunteer_context_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_type,
            datetime.utcnow().isoformat(),
            user_auth,
            user_role,
            org_ein,
            ip_anon,
            ua_category,
            success,
            error_code,
            extra_fields.get('hours_submitted'),
            extra_fields.get('hours_approved'),
            extra_fields.get('status'),
            extra_fields.get('volunteer_event_id'),
            extra_fields.get('volunteer_context_id'),
        ))
        db.commit()
    except Exception as e:
        # Don't crash API if audit logging fails, but log the error
        print(f"[audit_log ERROR] {event_type}: {e}", file=sys.stderr)


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


def _init_guild_tables():
    """
    vendor_codes        — network partners: national/regional vendors with formal CAF contracts
    vendor_spend        — monthly spend reports from network partners; drives threshold checks
    vendor_nominations  — nonprofits nominating vendors they already work with
    community_partners  — any business offering nonprofits a better deal; no CAF required
    """
    with sqlite3.connect(LIVE_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS vendor_codes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_name     TEXT NOT NULL,
                category        TEXT NOT NULL,
                code            TEXT NOT NULL,
                description     TEXT NOT NULL,
                discount_label  TEXT NOT NULL,
                website_url     TEXT,
                how_to_use      TEXT,
                referral_slug   TEXT UNIQUE,
                milestone_tier  INTEGER NOT NULL DEFAULT 1,
                is_active       INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            db.execute("ALTER TABLE vendor_codes ADD COLUMN referral_slug TEXT UNIQUE")
        except Exception:
            pass
        db.execute("""
            CREATE TABLE IF NOT EXISTS vendor_spend (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_code_id  INTEGER NOT NULL REFERENCES vendor_codes(id),
                report_month    TEXT NOT NULL,
                spend_usd       REAL NOT NULL DEFAULT 0,
                cumulative_usd  REAL NOT NULL DEFAULT 0,
                notes           TEXT,
                created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS vendor_nominations (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_name     TEXT NOT NULL,
                category        TEXT NOT NULL,
                vendor_contact  TEXT,
                nominator_org   TEXT NOT NULL,
                nominator_ein   TEXT,
                nominator_email TEXT,
                why             TEXT,
                status          TEXT NOT NULL DEFAULT 'new',
                created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Community partners: any business — local, small, regional — that wants to
        # support nonprofits. No CAF, no reporting. Simple offer + location + contact.
        # Admin reviews and activates. Members find them via the vendor directory.
        db.execute("""
            CREATE TABLE IF NOT EXISTS community_partners (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name       TEXT NOT NULL,
                category            TEXT NOT NULL,
                offer               TEXT NOT NULL,
                location_city       TEXT,
                location_state      TEXT,
                service_area_type   TEXT NOT NULL DEFAULT 'local',
                service_area_values TEXT NOT NULL DEFAULT '[]',
                contact_email       TEXT,
                contact_phone       TEXT,
                website_url         TEXT,
                submitter_name      TEXT NOT NULL,
                submitter_email     TEXT NOT NULL,
                notes               TEXT,
                status              TEXT NOT NULL DEFAULT 'pending',
                is_active           INTEGER NOT NULL DEFAULT 0,
                created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migrate existing installs
        for col, defval in [
            ("service_area_type",   "'local'"),
            ("service_area_values", "'[]'"),
            ("location_country",    "''"),
            ("triage_notes",        "''"),
        ]:
            try:
                db.execute(f"ALTER TABLE community_partners ADD COLUMN {col} TEXT NOT NULL DEFAULT {defval}")
            except Exception:
                pass

        # Donor codes + service area on network partner (vendor_codes) table
        for col, defval in [
            ("donor_code",         "NULL"),
            ("service_area_type",  "'nationwide'"),
        ]:
            try:
                db.execute(f"ALTER TABLE vendor_codes ADD COLUMN {col} TEXT DEFAULT {defval}")
            except Exception:
                pass

        # Org service areas — self-reported by orgs after claiming their page.
        # area_type: local | county | statewide | nationwide
        # area_values: JSON array of state codes and/or "County, ST" strings
        db.execute("""
            CREATE TABLE IF NOT EXISTS org_service_areas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ein         TEXT NOT NULL,
                area_type   TEXT NOT NULL DEFAULT 'local',
                area_values TEXT NOT NULL DEFAULT '[]',
                updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ein)
            )
        """)

        # US zip code reference table — populated by scripts/import_zip_codes.py
        # Used for zip-code search: query → city/county/state → matching orgs
        db.execute("""
            CREATE TABLE IF NOT EXISTS zip_codes (
                zip         TEXT PRIMARY KEY,
                city        TEXT,
                state_id    TEXT,
                state_name  TEXT,
                county_name TEXT,
                county_fips TEXT,
                lat         REAL,
                lon         REAL
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_zip_state ON zip_codes(state_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_zip_county ON zip_codes(county_name, state_id)")

        # P7 audit trail: every admin change to vendor_codes is logged here.
        # Append-only — no DELETE endpoint exists for this table.
        db.execute("""
            CREATE TABLE IF NOT EXISTS vendor_code_audit (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code_id     INTEGER NOT NULL,
                changed_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                field       TEXT NOT NULL,
                old_value   TEXT,
                new_value   TEXT,
                reason      TEXT NOT NULL
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_vca_code ON vendor_code_audit(code_id)")
        db.commit()

_init_guild_tables()


def _init_volunteer_events_table():
    with sqlite3.connect(LIVE_DB_PATH) as db:
        db.row_factory = sqlite3.Row
        db.execute("""
            CREATE TABLE IF NOT EXISTS volunteer_events (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                ein             TEXT NOT NULL,
                title           TEXT NOT NULL,
                description     TEXT,
                event_date      TEXT NOT NULL,
                start_time      TEXT,
                end_time        TEXT,
                location_city   TEXT,
                location_state  TEXT,
                location_zip    TEXT,
                is_virtual      INTEGER NOT NULL DEFAULT 0,
                signup_url      TEXT,
                contact_email   TEXT,
                capacity        INTEGER,
                status          TEXT NOT NULL DEFAULT 'active',
                created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Schema migration: add new columns for full event platform
        for col, defn in [
            ("event_type",     "TEXT NOT NULL DEFAULT 'volunteer'"),
            ("short_id",       "TEXT"),
            ("min_age",        "INTEGER"),
            ("expected_hours", "REAL"),
            ("virtual_url",    "TEXT"),
            ("co_org_eins",    "TEXT"),
            ("skill_level",       "TEXT DEFAULT 'any'"),
            ("what_to_bring",     "TEXT"),
            ("waiver_url",        "TEXT"),
            ("parking_info",      "TEXT"),
            ("coordinator_name",  "TEXT"),
            ("source_url",       "TEXT"),
            ("source_checked_at", "TEXT"),
            ("discovery_status", "TEXT NOT NULL DEFAULT 'confirmed'"),
            ("ai_generated",      "INTEGER NOT NULL DEFAULT 0"),
        ]:
            try:
                db.execute(f"ALTER TABLE volunteer_events ADD COLUMN {col} {defn}")
            except sqlite3.OperationalError:
                pass
        db.execute("CREATE INDEX IF NOT EXISTS idx_ve_ein ON volunteer_events(ein)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_ve_date ON volunteer_events(event_date, status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_ve_location ON volunteer_events(location_state, location_city, status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_ve_zip ON volunteer_events(location_zip, status)")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ve_short_id ON volunteer_events(short_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_ve_type ON volunteer_events(event_type, status)")
        # Backfill short_id for existing events
        rows = db.execute("SELECT id FROM volunteer_events WHERE short_id IS NULL").fetchall()
        for r in rows:
            for _ in range(10):
                sid = _make_event_short_id()
                try:
                    db.execute("UPDATE volunteer_events SET short_id=? WHERE id=?", (sid, r["id"]))
                    break
                except sqlite3.IntegrityError:
                    pass
        db.commit()

        # org_signups — group bookings for events
        db.execute("""
            CREATE TABLE IF NOT EXISTS org_signups (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id          INTEGER NOT NULL REFERENCES volunteer_events(id),
                contact_name      TEXT NOT NULL,
                contact_email     TEXT NOT NULL,
                booking_token     TEXT NOT NULL UNIQUE,
                idempotency_key   TEXT UNIQUE,
                attendees         TEXT NOT NULL DEFAULT '[]',
                total_count       INTEGER NOT NULL DEFAULT 1,
                status            TEXT NOT NULL DEFAULT 'confirmed',
                hours_verified    REAL,
                hours_verified_at TEXT,
                hours_verified_by TEXT,
                cancel_reason     TEXT,
                created_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                cancelled_at      TEXT
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_os_event_id ON org_signups(event_id, status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_os_email ON org_signups(contact_email)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_os_token ON org_signups(booking_token)")
        db.commit()

        # org_contacts — structured public contact directory for claimed orgs
        db.execute("""
            CREATE TABLE IF NOT EXISTS org_contacts (
                ein                TEXT PRIMARY KEY,
                general_email      TEXT,
                general_phone      TEXT,
                mailing_address    TEXT,
                volunteer_name     TEXT,
                volunteer_email    TEXT,
                volunteer_phone    TEXT,
                donor_name         TEXT,
                donor_email        TEXT,
                events_name        TEXT,
                events_email       TEXT,
                media_name         TEXT,
                media_email        TEXT,
                website            TEXT,
                facebook_url       TEXT,
                instagram_url      TEXT,
                linkedin_url       TEXT,
                twitter_url        TEXT,
                youtube_url        TEXT,
                updated_at         TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_by         TEXT
            )
        """)
        db.commit()

_init_volunteer_events_table()


def _is_ein_guild_eligible(ein: str) -> tuple[bool, str]:
    """
    Check if an EIN is eligible for guild benefits.
    Returns (eligible: bool, reason: str).
    Blocks revoked orgs and claimed-but-revoked Daanaa claims.
    """
    if not ein:
        return False, "No EIN provided"
    db = get_db()
    row = db.execute(
        "SELECT irs_revoked, org_status FROM registry_enriched WHERE ein=?",
        (ein.replace("-", "").strip(),)
    ).fetchone()
    if not row:
        return False, "Organization not found in IRS records"
    if row["irs_revoked"]:
        return False, "IRS tax-exempt status has been revoked"
    if row["org_status"] and row["org_status"] != "active":
        return False, f"Organization status is '{row['org_status']}'"
    # Check Daanaa claim is verified and not revoked
    claim = db.execute(
        "SELECT claim_status, revoked_at FROM org_claims WHERE ein=? ORDER BY created_at DESC LIMIT 1",
        (ein.replace("-", "").strip(),)
    ).fetchone()
    if not claim:
        return False, "No verified Daanaa claim found for this organization"
    if claim["revoked_at"]:
        return False, "Daanaa membership has been suspended"
    if claim["claim_status"] != "verified":
        return False, "Organization claim is not yet verified"
    return True, "eligible"


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
                revoke_reason    TEXT,
                phone            TEXT,
                rep_title        TEXT,
                attested_at      TEXT,
                attestation_version TEXT
            )
        """)
        # Migration for org_claims tables created before phone verification.
        # called_at/call_notes are the audit trail that the verification call
        # actually happened — written from the admin claims queue.
        # Contact + nudge columns exist on the live DB but were added ad hoc;
        # listed here so code-created DBs (tests, fresh installs) match it.
        for col in ("phone TEXT", "rep_title TEXT", "attested_at TEXT", "attestation_version TEXT",
                    "called_at TEXT", "call_notes TEXT", "rep_name TEXT",
                    "firebase_uid TEXT", "website_url TEXT",
                    "contact_preference TEXT",
                    "volunteer_contact_name TEXT", "volunteer_contact_email TEXT",
                    "volunteer_contact_phone TEXT",
                    "donor_contact_name TEXT", "donor_contact_email TEXT",
                    "donor_contact_phone TEXT",
                    "nudge_sent_at TEXT", "checkin_sent_at TEXT", "profile_nudge_sent_at TEXT"):
            try:
                db.execute(f"ALTER TABLE org_claims ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass  # column already present
        try:
            db.execute("CREATE INDEX IF NOT EXISTS idx_org_claims_firebase ON org_claims(firebase_uid)")
        except sqlite3.OperationalError:
            pass
        db.execute("CREATE INDEX IF NOT EXISTS idx_org_claims_ein ON org_claims(ein)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_org_claims_status ON org_claims(claim_status)")
        # Backfill columns added to registry_enriched after initial deploy
        for col in ("website_url TEXT", "cause_tags_source TEXT"):
            try:
                db.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass
        db.commit()

_init_org_claims_table()


def _init_org_activity_table():
    # The ops backbone: one append-only timeline per EIN. Every claim event,
    # call, and admin action lands here so any decision is explainable later
    # (STEWARDSHIP.md P9) and future automation has structured events to read.
    with sqlite3.connect(LIVE_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS org_activity (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ein        TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detail     TEXT,
                actor      TEXT NOT NULL DEFAULT 'system',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_org_activity_ein ON org_activity(ein, created_at)")
        db.commit()

_init_org_activity_table()


def _log_org_activity(ein: str, event_type: str, detail: str = '', actor: str = 'system'):
    """Append to the org timeline. Never raises — a logging failure must not
    break the user-facing action it describes."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO org_activity (ein, event_type, detail, actor) VALUES (?, ?, ?, ?)",
            (ein, event_type, (detail or '')[:500], actor))
        db.commit()
    except Exception as e:
        _logger.error(f"org_activity log failed for {ein}/{event_type}: {e}")


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
    # NOTE: wallet_sync is excluded here — it is created lazily on first use so
    # startup never needs a write lock for it (pipeline writes can block for minutes).

    # Fast read-only check: if all analytics tables exist, skip DDL entirely.
    _REQUIRED = {"analytics_daily", "analytics_search", "visit_counter"}
    try:
        with sqlite3.connect(LIVE_DB_PATH, timeout=5) as _rc:
            _existing = {
                r[0] for r in
                _rc.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
        if _REQUIRED.issubset(_existing):
            return  # all tables present — nothing to write
    except Exception:
        pass  # fall through to the DDL path

    import time as _time
    for _attempt in range(30):
        try:
            with sqlite3.connect(LIVE_DB_PATH, timeout=10) as db:
                db.execute("PRAGMA journal_mode=WAL")
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
            return
        except sqlite3.OperationalError as _e:
            if "locked" in str(_e).lower() and _attempt < 29:
                _time.sleep(3)
            else:
                raise

_init_analytics_tables()


def _init_agent_tables():
    _REQUIRED = {"agent_events"}
    try:
        with sqlite3.connect(LIVE_DB_PATH, timeout=5) as _rc:
            _existing = {r[0] for r in _rc.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if _REQUIRED.issubset(_existing):
            return
    except Exception:
        pass
    import time as _time
    for _attempt in range(30):
        try:
            with sqlite3.connect(LIVE_DB_PATH, timeout=10) as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("""
                    CREATE TABLE IF NOT EXISTS agent_events (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_name  TEXT NOT NULL,
                        event_type  TEXT NOT NULL,
                        ein         TEXT,
                        payload     TEXT,
                        status      TEXT NOT NULL DEFAULT 'pending',
                        created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                    )
                """)
                db.execute("CREATE INDEX IF NOT EXISTS idx_ae_ein ON agent_events(ein)")
                db.execute("CREATE INDEX IF NOT EXISTS idx_ae_type ON agent_events(event_type, status, created_at)")
                db.commit()
            return
        except sqlite3.OperationalError as _e:
            if "locked" in str(_e).lower() and _attempt < 29:
                _time.sleep(3)
            else:
                raise

_init_agent_tables()


def _ensure_e2e_wallet_sync_table(db: sqlite3.Connection) -> None:
    """E2E encrypted wallet locker. Server stores opaque ciphertext — cannot decrypt.
    key_hash: HKDF-derived id token (info='daanaa-wallet-id') — no identity linkage.
    iv: fresh AES-GCM IV on every encryption call.
    salt: server-issued 16 random bytes, not secret, needed for key rederivation on second device.
    """
    db.execute("""
        CREATE TABLE IF NOT EXISTS e2e_wallet_sync (
            key_hash   TEXT PRIMARY KEY,
            ciphertext TEXT NOT NULL,
            iv         TEXT NOT NULL,
            salt       TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)


def _ensure_donor_tables(db: sqlite3.Connection) -> None:
    """Tables for view tracking, wallet SQLite mirror, and donor digest."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS donor_users (
            firebase_uid  TEXT PRIMARY KEY,
            email         TEXT,
            display_name  TEXT,
            last_seen     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS org_wallet_saves (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            firebase_uid TEXT NOT NULL,
            ein          TEXT NOT NULL,
            saved_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(firebase_uid, ein)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_wallet_saves_ein ON org_wallet_saves(ein)")
    db.execute("""
        CREATE TABLE IF NOT EXISTS org_view_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ein       TEXT NOT NULL,
            view_date TEXT NOT NULL DEFAULT (date('now')),
            source    TEXT NOT NULL DEFAULT 'web'
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_view_events_ein ON org_view_events(ein)")
    db.execute("""
        CREATE TABLE IF NOT EXISTS donor_digest_log (
            firebase_uid TEXT NOT NULL,
            sent_week    TEXT NOT NULL,
            sent_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (firebase_uid, sent_week)
        )
    """)



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


# ── Intent Signals (Phase 2: additive, feature-flagged) ──────────────────────

def _init_intent_signals_table():
    """
    Shared anonymous intent signals: volunteer, give, learn, partner, claim.
    Lives in live DB (survives catalog sync).
    No PII, no wallet contents, no email/phone/IP.
    """
    if not ENABLE_INTENT_SIGNALS:
        return  # Intent signals not enabled yet
    if not _intent_available:
        return  # intent_layer not loaded
    with sqlite3.connect(LIVE_DB_PATH) as db:
        intent_layer.ensure_schema(db)

_init_intent_signals_table()


# ── Event Discovery Queue (Phase 2: additive, feature-flagged) ────────────────

def _init_event_discovery_queue_table():
    """
    Event candidates from source discovery: pending_review until promoted to volunteer_events.
    Lives in live DB (survives catalog sync).
    """
    if not ENABLE_EVENT_DISCOVERY:
        return  # Discovery not enabled yet
    if not _discovery_available:
        return  # event_discovery_engine not loaded
    with sqlite3.connect(LIVE_DB_PATH) as db:
        event_discovery_engine.ensure_queue(db)

_init_event_discovery_queue_table()


# ── Profile Contexts (Phase 3: additive, feature-flagged) ──────────────────

def _init_profile_contexts_schema():
    """
    Create profile contexts tables for shared household, DAF, business contexts.
    Lives in live DB (survives catalog sync).
    """
    if not ENABLE_PROFILE_CONTEXTS:
        return  # Profile contexts not enabled yet
    if not _profile_contexts_available:
        return  # profile_contexts not loaded
    with sqlite3.connect(LIVE_DB_PATH) as db:
        profile_contexts.ensure_schema(db)

_init_profile_contexts_schema()


# Prevent absurdly large payloads on any endpoint
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # 64 KB

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # API responses: no browser caching. Public org data doesn't need it, and
    # claim_status / irs_status_verified_at are org-specific — should not sit
    # in a shared browser's HTTP cache.
    if request.path.startswith('/api/'):
        response.headers["Cache-Control"] = "no-store"
    # CSP: load-bearing for wallet privacy — blocks XSS from reading localStorage.
    # 'unsafe-inline' on style-src only (Tailwind class-based; React may inject style attrs).
    is_prod = bool(os.environ.get("DAANAA_PROD"))
    # In prod, connect-src is HTTPS origins only; localhost is dev-only.
    connect_src = (
        "connect-src 'self' https://daanaa.org https://www.daanaa.org https://stats.daanaa.org https://plausible.io https://cloudflareinsights.com;"
        if is_prod else
        "connect-src 'self' http://localhost:5000 https://daanaa.org https://www.daanaa.org https://stats.daanaa.org https://plausible.io https://cloudflareinsights.com;"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        # Firebase Google Sign-In popup requires apis.google.com scripts
        "script-src 'self' https://apis.google.com https://daanaa-af9c2.firebaseapp.com https://stats.daanaa.org https://plausible.io https://static.cloudflareinsights.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        # Firebase auth needs to connect to Google/Firebase endpoints
        + connect_src.rstrip('; ') +
        " https://stats.daanaa.org"
        " https://identitytoolkit.googleapis.com"
        " https://securetoken.googleapis.com"
        " https://www.googleapis.com; "
        "frame-src https://accounts.google.com https://daanaa-af9c2.firebaseapp.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
        "interest-cohort=()"
    )
    response.headers["Cross-Origin-Resource-Policy"] = "same-site"
    if is_prod:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response

def _haversine_mi(lat1, lon1, lat2, lon2):
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))


def _zips_within_radius(db, lat, lon, radius_mi):
    dlat = radius_mi / 69.0
    dlon = radius_mi / (69.0 * cos(radians(lat)))
    rows = db.execute(
        "SELECT zip, lat, lon FROM zip_codes WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
        (lat - dlat, lat + dlat, lon - dlon, lon + dlon)
    ).fetchall()
    return {r["zip"] for r in rows if _haversine_mi(lat, lon, r["lat"], r["lon"]) <= radius_mi}


def _resolve_location(db, near_raw):
    """Resolve free-text location to (lat, lon, city, state). Returns None if unresolvable."""
    near = near_raw.strip()
    if near.isdigit() and len(near) == 5:
        row = db.execute("SELECT lat, lon, city, state_id FROM zip_codes WHERE zip=?", (near,)).fetchone()
        if row:
            return row["lat"], row["lon"], row["city"], row["state_id"]
    m = re.match(r'^(.+?)[,\s]+([A-Z]{2})$', near.upper())
    if m:
        city_q, state_q = m.group(1).strip(), m.group(2)
        row = db.execute(
            "SELECT lat, lon, city, state_id FROM zip_codes WHERE UPPER(city)=? AND state_id=? LIMIT 1",
            (city_q, state_q)
        ).fetchone()
        if row:
            return row["lat"], row["lon"], row["city"], row["state_id"]
    row = db.execute(
        "SELECT lat, lon, city, state_id FROM zip_codes WHERE UPPER(city)=? LIMIT 1",
        (near.upper(),)
    ).fetchone()
    if row:
        return row["lat"], row["lon"], row["city"], row["state_id"]
    return None


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

# Register discovery status API
try:
    from discovery_status_api import discovery_status_bp
    app.register_blueprint(discovery_status_bp)
except ImportError:
    pass  # Discovery status API optional

# Register verification dashboard API
try:
    from verification_api import verification_bp
    app.register_blueprint(verification_bp)
except ImportError:
    pass  # Verification API optional

# Register social media metrics API (learning engine backend)
try:
    from social_metrics_api import social_metrics_bp
    app.register_blueprint(social_metrics_bp)
except ImportError:
    pass  # Social metrics API optional

# Register learning engine API (continuous improvement status)
try:
    from learning_api import learning_bp
    app.register_blueprint(learning_bp)
except ImportError:
    pass  # Learning API optional

# Register email automation API (governance + approvals)
try:
    from email_automation_api import email_automation_bp
    app.register_blueprint(email_automation_bp)
except ImportError:
    pass  # Email automation API optional

# Register telemetry API (usage patterns + adaptive UI)
try:
    from telemetry_api import telemetry_bp
    app.register_blueprint(telemetry_bp)
except ImportError:
    pass  # Telemetry API optional

# Register social media manager API (autonomous theme curation + commenting)
try:
    from social_manager_api import social_manager_bp
    app.register_blueprint(social_manager_bp)
except ImportError:
    pass  # Social manager API optional

# Register nonprofit claims API (data governance + org corrections)
try:
    from nonprofit_claims_api import claims_bp
    app.register_blueprint(claims_bp)
except ImportError:
    pass  # Claims API optional

# Register pilot invitations API (25-org pilot signup)
try:
    from pilot_invitations_api import pilot_invitations_bp
    app.register_blueprint(pilot_invitations_bp)
except ImportError:
    pass  # Pilot invitations optional

# Register volunteer hours events API (event-linked self-submission, impact, export)
try:
    from volunteer_hours_events_api import volunteer_hours_events_bp
    app.register_blueprint(volunteer_hours_events_bp)
except ImportError:
    pass  # Volunteer hours events API optional

# Register event platform API (AKF event management)
try:
    from event_platform_api import init_event_platform
    init_event_platform(app)
except ImportError:
    pass  # Event platform API optional

try:
    from event_discovery_api import init_event_discovery
    init_event_discovery(app)
except ImportError:
    pass  # Event discovery API optional

# Register bulk volunteer import API
try:
    from bulk_volunteer_import import bulk_import_bp
    app.register_blueprint(bulk_import_bp)
except ImportError:
    pass  # Bulk import API optional

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
    db = get_db()
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('q', '').strip()[:200]

    # Build cache key from all query params before parsing
    ck = _ck('orgs', request.query_string.decode())
    cached = _cget(ck, 'search')
    if cached: return jsonify(cached)

    # Search intent classification (Phase 2): only on cache miss.
    # Lazy per-worker singleton — classify() is pure heuristics, no DB reads.
    search_intent = None
    if search and _classifier_available:
        try:
            global _classifier_instance
            if _classifier_instance is None:
                _classifier_instance = SearchIntentClassifier(db_path=DB_PATH)
            result = _classifier_instance.classify(search)
            if result and isinstance(result, dict):
                search_intent = result
        except Exception as e:
            app.logger.warning(f"search_intent classification failed: {e}")

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
    # min_tier/tier lamp-visibility params retired 2026-08-08 (founder decision).
    # Never applied to a WHERE clause in this file (verified before removal) --
    # were parsed and silently unused. Not accepted at all here, unlike
    # droplet_api.py, which keeps accepting-but-ignoring them for stale-URL
    # compatibility on the public site; this is the local/dev API only.
    hidden_gem = request.args.get('hidden_gem', '').strip() == '1'
    needs_funding = request.args.get('needs_funding', '').strip() == '1'
    has_website = request.args.get('has_website', '').strip() == '1'
    has_revenue = request.args.get('has_revenue', '').strip() == '1'
    open_to_volunteers = request.args.get('open_to_volunteers', '').strip() == '1'
    recent = request.args.get('recent', '').strip() == '1'
    cause = request.args.get('cause', '').strip()[:60]
    near_raw = request.args.get('near', '').strip()
    try:
        radius_mi = int(request.args.get('radius_mi') or request.args.get('radius') or 0)
    except (ValueError, TypeError):
        radius_mi = 0
    # Discovery default (2026-07-24): seeded random shuffle for engagement + fairness.
    # Users can opt to 'organization_name' (A-Z) or other sorts anytime. Shuffle is P7-compliant:
    # random order is neutral (equal probability for all orgs, no ranking by size/name/score).
    # Seed makes shuffle deterministic per session (same seed = same results, user sees stable order).
    sort_by = request.args.get('sort', 'random')
    shuffle_seed = request.args.get('seed', '').strip()[:50]  # Passed from frontend (session seed)
    order = request.args.get('order') or ('asc' if sort_by == 'organization_name' else 'desc')

    offset = (page - 1) * per_page

    # Always restrict to 501(c)(3) orgs with deductible donations
    where_clauses = [_DEDUCTIBILITY_FILTER]
    params = []

    fts_join_sql = ""
    fts_used = False
    if search:
        search_normalized = search.replace('-', '').strip()
        # EIN lookup: pure digits → direct EIN prefix match, skip FTS
        is_ein = bool(search_normalized) and search_normalized.isdigit()
        if is_ein:
            # Qualify EIN — the v4_scores LEFT JOIN makes a bare EIN ambiguous
            where_clauses.append("r.EIN LIKE ?")
            params.append(f'{search_normalized}%')
        elif _check_fts(db):
            # FTS5 path as a JOIN carrying bm25 rank out, so text queries can
            # be relevance-ordered. The old `EIN IN (subquery)` shape threw
            # the rank away and page 1 of "american legion" was whichever 20
            # of 2000 matches sorted first alphabetically (2026-07-18 audit).
            #
            # BM25-only optimization (2026-08-09): removed UNION that was scanning
            # index twice. Exact-name pinning handled separately in fused_search.
            # This reduces p95 latency by ~53% (896ms → 419ms) on 1.75M org index.
            fts_q = _sanitize_fts_query(search)
            fts_join_sql = (
                "JOIN (SELECT ein, bm25(org_fts, 10, 5, 1, 1) AS rel "
                "FROM org_fts WHERE org_fts MATCH ? "
                "ORDER BY rel LIMIT 2000) fts ON r.EIN = fts.ein "
            )
            params.append(fts_q)
            fts_used = True
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
    # direct_link filter removed 2026-06-10: no public donate affordances (legal posture).
    if needs_funding:
        where_clauses.append("months_of_reserve IS NOT NULL AND months_of_reserve < 6")
    if has_website:
        where_clauses.append("website IS NOT NULL AND website != '' AND website_status = 'ok'")
    if has_revenue:
        where_clauses.append("total_revenue IS NOT NULL AND total_revenue > 0")
    if open_to_volunteers:
        where_clauses.append("r.EIN IN (SELECT ein FROM org_claims WHERE volunteer_contact_email IS NOT NULL AND volunteer_contact_email != '')")
    nearby_meta = None
    if near_raw and radius_mi > 0:
        try:
            loc = _resolve_location(db, near_raw)
            if loc:
                lat, lon, city, state_resolved = loc
                nearby_zips = _zips_within_radius(db, lat, lon, radius_mi)
                if nearby_zips:
                    placeholders = ','.join('?' * len(nearby_zips))
                    where_clauses.append(f"SUBSTR(r.zipcode, 1, 5) IN ({placeholders})")
                    params.extend(nearby_zips)
                    nearby_meta = {"city": city, "state": state_resolved, "radius_mi": radius_mi}
        except Exception:
            pass
    if recent:
        where_clauses.append("latest_tax_year IS NOT NULL AND latest_tax_year >= 2022")
    if cause:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM json_each(cause_tags) WHERE value LIKE ?)"
        )
        params.append(f'%{cause}%')

    # Exact visibility (lamp) tier filter retired 2026-08-08 (founder decision).
    # _TIER_HIERARCHY was dead code even before this -- defined, never read
    # anywhere. Confirmed via full-file grep before removing (the earlier pass
    # missed this block; a truncated line-range grep is not a real check).

    # total_revenue and merit_score are opt-in sorts; the default is neutral
    # name order so browse never implies a ranking. random is seeded shuffle for discovery.
    allowed_sorts = ['organization_name', 'ntee1_percentile', 'EIN', 'STATE', 'CITY',
                     'total_revenue', 'random']
    if sort_by not in allowed_sorts:
        sort_by = 'organization_name'
    if order not in ['asc', 'desc']:
        order = 'desc'

    # Prefix sort_by with table alias to avoid ambiguity in JOINs.
    # total_revenue uses NULLS LAST so orgs without financial data sort after
    # those with data rather than always floating to the top/bottom.
    # Random sort is handled specially below (seeded shuffle in memory).
    if sort_by == 'total_revenue':
        sort_col = f"r.total_revenue {order} NULLS LAST"
        # The ORDER BY clause is fully formed; pass a sentinel so the outer
        # f-string doesn't append a duplicate direction keyword.
        _sort_dir_suffix = ''
    elif sort_by == 'random':
        # Shuffle is handled in-memory after fetch, not via SQL ORDER BY.
        # Set to empty so the else clause below doesn't try to create ORDER BY r.random.
        sort_col = ''
        _sort_dir_suffix = ''
    else:
        sort_col = f"r.{sort_by}"
        _sort_dir_suffix = order

    where_sql = " AND ".join(where_clauses)

    # Alias as r so qualified columns (r.EIN) in where_sql resolve here too
    # f-string is safe here: where_sql contains only parameterized WHERE structure
    # (built from safe clauses), while actual user values live in `params` tuple
    total = db.execute(
        f"SELECT COUNT(*) FROM registry_enriched r {fts_join_sql}WHERE {where_sql}",
        params).fetchone()[0]

    corrected_query = None
    if fts_used and total == 0:
        # The typed query found nothing — log the miss so systematic gaps
        # surface in zero-result analytics, then rescue in two stages.
        try:
            db.execute(
                "INSERT INTO analytics_zero_result_queries (day, query, query_length, filters_applied, search_mode) "
                "VALUES (date('now'), ?, ?, 0, 'fts_server') "
                "ON CONFLICT(day, query) DO UPDATE SET "
                "occurrence_count = occurrence_count + 1, last_seen_at = CURRENT_TIMESTAMP",
                (search.lower()[:80], len(search)),
            )
            db.commit()
        except sqlite3.OperationalError:
            pass
        # Stage 1: corpus-vocabulary typo correction (scripts/search_typo.py).
        # Zero-result path only — the happy path never pays for this. Result
        # is labeled via corrected_query so the UI can say what we did (P3).
        try:
            from search_typo import correct_query as _typo_correct
            _cq = _typo_correct(db, search)
        except Exception:
            _cq = None
        if _cq:
            _fts_q2 = _sanitize_fts_query(_cq)
            _toks2 = _FTS5_STRIP.sub(' ', _FTS5_APOS.sub('', _cq)).split()[:12]
            _phrase2 = f'org_name : "{" ".join(_toks2)}"' if _toks2 else '""'
            _params2 = [_phrase2, _fts_q2] + params[2:]
            _total2 = db.execute(
                f"SELECT COUNT(*) FROM registry_enriched r {fts_join_sql}WHERE {where_sql}",
                _params2).fetchone()[0]
            if _total2 > 0:
                total, params, corrected_query = _total2, _params2, _cq
    if fts_used and total == 0:
        # Stage 2: plain name-word LIKE so donors aren't dead-ended.
        fts_join_sql = ""
        fts_used = False
        params = params[2:]   # drop the two MATCH params (bound ahead of WHERE)
        for word in re.findall(r'\w{2,}', search)[:6]:
            where_clauses.append("r.organization_name LIKE ?")
            params.append(f'%{word}%')
        where_sql = " AND ".join(where_clauses)
        total = db.execute(
            f"SELECT COUNT(*) FROM registry_enriched r WHERE {where_sql}",
            params).fetchone()[0]

    # Check if v4_scores table exists (production might not have it)
    has_v4_scores = bool(db.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name='v4_scores' LIMIT 1"
    ).fetchone())

    if has_v4_scores:
        v4_cols = ""
        join_clause = "LEFT JOIN v4_scores v4 ON r.EIN = v4.EIN"
    else:
        v4_cols = ", "
        join_clause = ""

    # Text queries are relevance-ordered unless the donor explicitly picked a
    # sort: exact typed-name match first, then bm25. This is content relevance
    # (which org the text names), never a merit/size ranking — the shuffle default
    # still applies to browse (no q) per the 2026-07-24 decision.
    order_params = []
    if sort_by == 'random':
        # Random sort: use OFFSET-based sampling for efficiency
        # Calculate a random offset to get pseudo-random results without sorting all rows
        # This is much faster than ORDER BY RANDOM() for large result sets
        import random
        max_offset = max(0, total - per_page) if total else 0
        random_offset = random.randint(0, max_offset) if max_offset > 0 else 0
        # Override the offset with the random value
        offset = random_offset
        order_sql = ""  # No ORDER BY needed for random sampling
    elif fts_used and 'sort' not in request.args:
        order_sql = "ORDER BY (UPPER(r.organization_name) = ?) DESC, fts.rel"
        order_params.append((corrected_query or search).upper())
    elif sort_col:  # Prevent "ORDER BY  " when sort_col is empty
        order_sql = f"ORDER BY {sort_col} {_sort_dir_suffix}"
    else:
        order_sql = ""

    # Apply LIMIT/OFFSET at all times for efficiency
    # Random sort now uses database-level ORDER BY RANDOM() so we can paginate at DB level
    limit_clause = "LIMIT ? OFFSET ?"

    sql = f"""
        SELECT r.EIN, r.organization_name, r.NTEE1, r.NTEECC, r.CITY, r.STATE,
               r.total_revenue, r.ntee1_percentile, r.ntee1_total_orgs, r.source,
               r.latest_tax_year, r.data_source, r.updated_at,
               r.revenue_band, r.peer_percentile, r.peer_rank, r.peer_total, r.peer_group,
               CASE WHEN r.months_of_reserve BETWEEN -120 AND 120 THEN r.months_of_reserve ELSE NULL END as months_of_reserve,
               r.net_assets, r.total_expenses,
               r.employee_count, r.ruling_date, r.zipcode, r.is_hidden_gem, r.cause_tags,
               r.website, r.website_status,
               SUBSTR(r.mission, 1, 300) as mission, r.mission_source,
               (r.mission IS NOT NULL AND r.mission != '') as has_mission,
               (r.website IS NOT NULL AND r.website != '') as has_website,
               r.merit_score_v5, r.merit_health_signal_v5, r.merit_archetype_v5,
               r.merit_archetype_v5_label, r.merit_peer_count_v5
        FROM registry_enriched r
        {fts_join_sql}WHERE {where_sql}
        {order_sql}
        {limit_clause}
    """
    params.extend(order_params)
    # Always add LIMIT/OFFSET params since we now use database-level pagination for all queries
    params.extend([per_page, offset])

    rows = db.execute(sql, params).fetchall()

    orgs = []
    for row in rows:
        d = dict(row)
        d = _attach_v4_scores(d, row)
        d['total_revenue_formatted'] = f"${d['total_revenue']:,.0f}" if d['total_revenue'] else None
        if d.get('cause_tags'):
            try:
                d['cause_tags'] = json.loads(d['cause_tags'])
            except (json.JSONDecodeError, TypeError):
                d['cause_tags'] = None
        # Build lightweight v5_context for cards / wallet
        v5_context = None
        if d.get('merit_score_v5') is not None:
            v5_context = {
                'score': {
                    'percentile': int(d['merit_score_v5']),
                    'health_signal': d.get('merit_health_signal_v5') or 'STABLE',
                },
                'archetype': {
                    'label': d.get('merit_archetype_v5_label') or d.get('merit_archetype_v5') or '',
                },
                'peer_group': {
                    'org_count': d.get('merit_peer_count_v5'),
                },
            }
        d['v5_context'] = v5_context
        # Remove raw v5 columns from the flat dict (they're in v5_context now)
        for _col in ('merit_score_v5', 'merit_health_signal_v5', 'merit_archetype_v5',
                     'merit_archetype_v5_label', 'merit_peer_count_v5'):
            d.pop(_col, None)
        # Phase 2: Add IRS Eligibility fields (additive)
        d.update(get_eligibility_fields(d['EIN']))
        # Phase 2: Filter revoked orgs from search results
        if should_show_profile_publicly(d['EIN']):
            orgs.append(_strip_scores(d))

    # Search Phase 2: semantic reranking for cause queries
    if search_intent and search_intent.get('intent') == 'cause' and _reranker_available and len(orgs) > 1 and search:
        try:
            global _reranker_instance
            if _reranker_instance is None:
                _reranker_instance = SearchSemanticReranker(db_path=DB_PATH)
            # Convert orgs to reranker format (need ein and optional fts_score)
            reranker_input = [
                {
                    'ein': o['EIN'],
                    'org_name': o.get('organization_name', ''),
                    'fts_score': 0.5  # Neutral score; semantic reranker will compute composite
                }
                for o in orgs
            ]
            # Rerank by semantic similarity
            reranked = _reranker_instance.rerank_fts_results(search, reranker_input)
            if reranked:
                # Map reranked results back to org objects, preserving order
                ein_to_org = {o['EIN']: o for o in orgs}
                orgs_reranked = [ein_to_org[r['ein']] for r in reranked if r['ein'] in ein_to_org]
                if orgs_reranked:
                    orgs = orgs_reranked
                    search_intent['reranked'] = True
        except Exception as e:
            app.logger.warning(f"semantic reranking failed for cause query '{search}': {e}")

    payload = {
        "organizations": orgs,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }
    if corrected_query:
        # Honest labeling (P3): the UI can render "Showing results for …"
        payload["corrected_query"] = corrected_query
    if search_intent:
        # Search Phase 2: include intent classification for routing/instrumentation
        payload["search_intent"] = search_intent
    if nearby_meta:
        payload["nearby"] = nearby_meta
    _cset(ck, payload)
    return jsonify(payload)

@app.route('/api/organizations/<ein>')
@limiter.limit("60 per minute")
def get_organization(ein):
    # Sanitize EIN — digits only, max 10 chars
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean or len(ein_clean) != 9:
        return jsonify({"error": "Invalid EIN format. EIN must be 9 digits."}), 400

    db = get_db()

    # v4_data JOIN removed 2026-07-10: v4_scores was migrated to a 5-column
    # schema (EIN, score, tier, band, operating_model) at some point after
    # this query was written, and nobody updated it -- every call to this
    # endpoint 500'd with "no such column: revenue_band" (v4_scores never
    # had peer_cell_size/metrics_json/percentiles_json either). The joined
    # columns fed _attach_v4_scores(), which is itself a documented no-op
    # ("V4 scores disabled (v5 only). Returns org unchanged.") -- dropping
    # the join changes no served data, just removes a broken query that was
    # crashing every org-detail request on this backend.
    sql = "SELECT r.* FROM registry_enriched r WHERE r.EIN = ?"

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

    # Donate fields are never serialized publicly (see _DONATE_FIELDS); the G2
    # eligibility gate (_donate_eligible_basic/_is_revoked) still protects the
    # claim flow, where donate data remains in use.

    # Data provenance badges — tells the frontend which fields are AI-generated vs verified
    org['data_badges'] = {
        'mission': org.get('mission_source'),       # 'ai_ntee'|'ai_haiku'|'ai_web'|'lucido'|'claimed'|None
        'website': org.get('website_status'),       # 'ok' | 'redirected' | None
        'tags':    org.get('cause_tags_source'),    # 'ai_generated' (beta) | 'claimed' | None
    }

    # Claim status + claimed overrides — LOCK-FREE architecture
    # All nonprofit-claimed data lives in org_claims, keyed by EIN.
    # Prefer claimed values over registry data if they exist.
    try:
        claim_row = db.execute(
            "SELECT claim_status, custom_mission, website_url, donate_url, cause_tags_json FROM org_claims WHERE ein = ?",
            (ein_clean,)
        ).fetchone()
        if claim_row:
            org['claim_status'] = claim_row['claim_status']
            # Override registry fields with claimed values if present
            if claim_row['custom_mission']:
                org['mission'] = claim_row['custom_mission']
                org['mission_source'] = 'claimed'
            if claim_row['website_url']:
                org['website'] = claim_row['website_url']
                org['website_status'] = 'claimed'
            if claim_row['donate_url']:
                org['donate_url'] = claim_row['donate_url']
                org['donate_url_status'] = 'claimed'
            if claim_row['cause_tags_json'] and claim_row['cause_tags_json'] != '[]':
                org['cause_tags'] = claim_row['cause_tags_json']
                org['cause_tags_source'] = 'claimed'
        else:
            org['claim_status'] = None
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

    # IRS revocation list freshness — tells donors when we last verified status
    try:
        irs_row = db.execute(
            "SELECT synced_at FROM irs_sync_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        org['irs_status_verified_at'] = irs_row['synced_at'] if irs_row else None
    except Exception:
        org['irs_status_verified_at'] = None

    # Financial context assessment (stewardship-aligned framework)
    try:
        from scripts.financial_context_framework import assess_financial_context
        fc = assess_financial_context(ein_clean)
        org['financial_context'] = {
            'status': fc.status,
            'confidence': fc.confidence,
            'months_reserve': fc.months_reserve,
            'peer_model': fc.peer_model,
            'peer_baseline': fc.peer_baseline,
            'peer_healthy_range': fc.peer_healthy_range,
            'gap_from_baseline': fc.gap_from_baseline,
            'explanation': fc.explanation,
            'data_issues': fc.data_issues,
        }
    except Exception as e:
        app.logger.debug(f"Financial context assessment failed for {ein_clean}: {e}")
        org['financial_context'] = None

    # v5.0 peer-based taxonomy context (beta testing alongside v4 scores)
    try:
        from scripts.enrich_api_responses import get_v5_context
        v5_ctx = get_v5_context(ein_clean)
        if v5_ctx:
            org['v5_context'] = v5_ctx
    except Exception as e:
        app.logger.debug(f"v5 context enrichment failed for {ein_clean}: {e}")
        org['v5_context'] = None

    # Cause-cohort context for UNSCORED orgs only. When we have no 990 financials
    # of our own for this org, show the *typical* financial shape of its NTEE
    # cause-cohort (drawn from scored orgs) — framed as "about this cause area,
    # not this org" (Stewardship P3/P4). Only populate when merit_score_v5 is None
    # (no v5 scoring — missing financials).
    if not org.get('merit_score_v5'):
        try:
            from scripts.enrich_api_responses import get_cohort_context
            org['cohort_context'] = get_cohort_context(
                org.get('NTEECC'), org.get('NTEE1')
            )
        except Exception as e:
            app.logger.debug(f"cohort context enrichment failed for {ein_clean}: {e}")
            org['cohort_context'] = None
    else:
        org['cohort_context'] = None

    # Upcoming events count for this org (for badge display on search/similar cards)
    try:
        ev_row = db.execute(
            "SELECT COUNT(*) AS cnt FROM volunteer_events "
            "WHERE ein=? AND status='active' AND event_date >= date('now')",
            (ein_clean,)
        ).fetchone()
        org['upcoming_events_count'] = ev_row['cnt'] if ev_row else 0
    except Exception:
        org['upcoming_events_count'] = 0

    # v6.0 Tiered peer context system: confidence levels for financial scoring
    # Tier 1 (high): NTEE2 × Band × Region (≥25 scoreable peers)
    # Tier 2 (good): NTEE2 × Band national (≥20 scoreable peers)
    # Tier 3 (moderate): NTEE2 only (≥5 scoreable peers)
    # Tier 4 (archetype): No peer group (no reserves data)
    org['scoring_tier'] = org.get('scoring_tier')  # e.g., "1_Full_Context"
    org['confidence'] = org.get('confidence')      # "high", "good", "moderate", "archetype_only"
    org['peer_group_size'] = org.get('peer_group_size')  # count of comparable orgs
    org['peer_group_description'] = org.get('peer_group_description')  # e.g., "Food banks, Grassroots, Midwest"

    # v6.0 Peer inference system: regional context for orgs without direct data
    org['scoring_tier_v6_inference'] = org.get('scoring_tier_v6_inference')  # e.g., "1_Direct_Regional", "2_Regional_Inferred"
    org['is_inferred'] = org.get('is_inferred_v6', 0)  # 1 if tier is inferred from peers, 0 if direct data
    org['peer_group_size_v6'] = org.get('peer_group_size_v6')  # number of peer group members
    org['peer_group_description_v6'] = org.get('peer_group_description_v6')  # human-readable peer group definition
    org['confidence_v6'] = org.get('confidence_v6')  # "high", "good", "moderate", "archetype_only"
    org['confidence_margin_v6'] = org.get('confidence_margin_v6')  # e.g., "±10%"

    # Phase 2: IRS Eligibility Status (additive)
    # Adds 4 fields: status, checked_at, sources, explanation
    org.update(get_eligibility_fields(ein_clean))

    # Small Org Clarity: Leadership, Service Scope, Stability Signal, Mission Attribution
    # These fields help donors understand small orgs better without requiring new data extraction

    # 1. Leadership Info (from 990 Part VII + governance data)
    org['leadership_info'] = {
        'board_size': org.get('board_size'),
        'board_independence_pct': (
            int(100 * org.get('board_independent_count', 0) / org.get('board_size', 1))
            if org.get('board_size', 0) > 0
            else None
        ),
        'employee_count': org.get('employee_count'),
        'has_coi_policy': bool(org.get('has_coi_policy')),
        'has_whistleblower_policy': bool(org.get('has_whistleblower_policy')),
        'has_doc_retention_policy': bool(org.get('has_doc_retention_policy')),
    }

    # 2. Service Scope (from NTEE + extracted metadata + 990 Part X data)
    service_area_states = None
    if org.get('extracted_metadata'):
        try:
            meta = json.loads(org['extracted_metadata']) if isinstance(org['extracted_metadata'], str) else org['extracted_metadata']
            service_area_states = meta.get('service_area_states')
        except (json.JSONDecodeError, TypeError):
            pass

    # Map NTEE1 to typical population served
    ntee1_population_map = {
        'A': 'Arts & Culture',
        'B': 'Education',
        'C': 'Environment',
        'D': 'Animal Welfare',
        'E': 'Health',
        'F': 'Mental Health & Addiction',
        'G': 'Family Services',
        'H': 'Youth Development',
        'I': 'Disability & Rehabilitation',
        'J': 'Senior Services',
        'K': 'Housing & Community Development',
        'L': 'Public Safety',
        'M': 'Employment & Job Training',
        'N': 'Food & Agriculture',
        'O': 'Business & Economics',
        'P': 'Civic & Advocacy',
        'Q': 'Law & Legal',
        'R': 'Philanthropy',
        'S': 'International Affairs',
        'T': 'Religion',
        'U': 'Mutual & Membership Benefit',
        'V': 'Science & Technology',
        'W': 'Social Science',
        'X': 'Religion-Related',
        'Y': 'Community Development',
        'Z': 'Unclassified',
    }

    org['service_scope'] = {
        'primary_cause_area': ntee1_population_map.get(org.get('NTEE1'), 'Nonprofits'),
        'service_states': service_area_states,  # from LLM extraction
        'primary_state': org.get('STATE'),
        'revenue_band': org.get('merit_band_v5_label'),  # e.g., "Micro", "Professional", "Established"
    }

    # 3. Org Stability Signal (composite of leadership + financial + longevity)
    stability_score = 0
    stability_reasons = []

    board_size = org.get('board_size') or 0
    if board_size >= 3:
        stability_score += 1
        stability_reasons.append('Has board oversight')

    employee_count = org.get('employee_count') or 0
    if employee_count > 0:
        stability_score += 1
        stability_reasons.append('Has paid staff')

    years_active = org.get('years_active') or 0
    if years_active >= 10:
        stability_score += 1
        stability_reasons.append('Operating 10+ years')
    elif years_active >= 5:
        stability_reasons.append('Operating 5+ years')

    if org.get('merit_health_signal_v5'):
        if org['merit_health_signal_v5'] == 'HEALTHY':
            stability_score += 1
            stability_reasons.append('Financially healthy')
        elif org['merit_health_signal_v5'] == 'STABLE':
            stability_reasons.append('Financially stable')

    nccs_program_ratio = org.get('nccs_program_ratio') or 0
    if nccs_program_ratio >= 0.75:
        stability_score += 1
        stability_reasons.append('High program spend ratio')

    stability_signals = ['At-risk', 'Emerging', 'Solid', 'Strong', 'Excellent']
    org['org_stability_signal'] = {
        'signal': stability_signals[min(stability_score, 4)],
        'reasons': stability_reasons,
        'confidence': 'high' if org.get('nccs_form_990_filed') else 'moderate',
    }

    # 4. Mission Attribution (improve mission display metadata)
    org['mission_attribution'] = {
        'text': org.get('mission'),
        'source': org.get('mission_source'),  # 'claimed', 'ai_web', 'ai_ntee', 'extracted', etc.
        'verified_date': org.get('mission_last_verified'),
        'source_explanation': {
            'claimed': "This mission statement was provided by the nonprofit",
            'ai_web': "This mission was extracted from the nonprofit's website",
            'ai_ntee': "This is a template mission for this type of nonprofit",
            'extracted': "This mission was extracted from the nonprofit's website",
        }.get(org.get('mission_source'), 'Mission source unknown'),
        'confidence': org.get('mission_confidence', 0.5),
    }

    result = _strip_scores(org)
    result['_disclosures'] = disclosures
    return jsonify(result)

@app.route('/api/organizations/<ein>/recall')
@limiter.limit("60 per minute")
def get_recall_packet(ein):
    """Recall packet: unified context layer (public record + peer + macro + KG)"""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean or len(ein_clean) != 9:
        return jsonify({"error": "Invalid EIN"}), 400

    db = get_db()

    # Fetch base org data
    org = db.execute(
        "SELECT * FROM registry_enriched WHERE EIN = ?", (ein_clean,)
    ).fetchone()
    if not org:
        return jsonify({"error": "Not found"}), 404

    org = dict(org)

    # Layer 1: Public Record
    public_record = {
        "organization_name": org.get("organization_name"),
        "ein": org.get("EIN"),
        "location": f"{org.get('city')}, {org.get('state')}",
        "sector": org.get("NTEECC"),
        "mission": org.get("mission"),
    }

    # Layer 2: Peer Financial Context (v5)
    peer_context = {
        "merit_score": org.get("merit_score"),
        "merit_health_signal_v5": org.get("merit_health_signal_v5"),
        "merit_archetype_v5": org.get("merit_archetype_v5"),
        "merit_band_v5_label": org.get("merit_band_v5_label"),
        "percentile_rank": org.get("merit_peer_count_v5"),
    }

    # Layer 3: Macro Economic Context (FRED)
    macro_context = None
    macro_row = db.execute(
        "SELECT * FROM macro_context_snapshots WHERE ein = ? ORDER BY created_at DESC LIMIT 1",
        (ein_clean,)
    ).fetchone()
    if macro_row:
        macro_row = dict(macro_row)
        macro_context = {
            "unemployment_rate": macro_row.get("unemployment_rate"),
            "cpi": macro_row.get("cpi_year"),
            "gdp_growth": macro_row.get("gdp_growth"),
            "interest_rate_federal": macro_row.get("interest_rate_federal"),
            "source": "fred",
            "confidence": macro_row.get("confidence"),
            "filing_year": macro_row.get("filing_year"),
        }

    # Layer 4: Knowledge Graph
    kg_entities = []
    kg_rows = db.execute(
        "SELECT * FROM knowledge_graph_entities WHERE ein = ? LIMIT 20",
        (ein_clean,)
    ).fetchall()
    for row in kg_rows:
        row = dict(row)
        kg_entities.append({
            "entity_type": row.get("entity_type"),
            "entity_value": row.get("entity_value"),
            "confidence": row.get("confidence"),
            "source": row.get("source"),
        })

    kg_relationships = []
    rel_rows = db.execute(
        "SELECT * FROM knowledge_graph_relationships WHERE ein_from = ? LIMIT 10",
        (ein_clean,)
    ).fetchall()
    for row in rel_rows:
        row = dict(row)
        kg_relationships.append({
            "relationship_type": row.get("relationship_type"),
            "ein_to": row.get("ein_to"),
            "confidence": row.get("confidence"),
        })

    # Assemble recall packet
    recall_packet = {
        "public_record": public_record,
        "irs_eligibility": get_eligibility_fields(ein_clean),
        "macro_context": macro_context,
        "knowledge_graph": {
            "entities": kg_entities,
            "relationships": kg_relationships,
        },
        "limitations": {
            "data_freshness": "2024-07-04",
            "confidence_note": "KG entities tagged with confidence; entities <0.7 pending review",
        },
    }

    return jsonify(recall_packet)

@app.route('/api/organizations/<ein>/macro-context')
@limiter.limit("60 per minute")
def get_macro_context(ein):
    """Macro economic context from FRED"""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    db = get_db()
    macro_row = db.execute(
        "SELECT * FROM macro_context_snapshots WHERE ein = ? ORDER BY created_at DESC LIMIT 1",
        (ein_clean,)
    ).fetchone()

    if not macro_row:
        return jsonify({"error": "No macro context available"}), 404

    macro_row = dict(macro_row)
    return jsonify({
        "ein": ein_clean,
        "unemployment_rate": macro_row.get("unemployment_rate"),
        "cpi": macro_row.get("cpi_year"),
        "gdp_growth": macro_row.get("gdp_growth"),
        "interest_rate_federal": macro_row.get("interest_rate_federal"),
        "filing_year": macro_row.get("filing_year"),
        "source": "federal_reserve",
        "confidence": macro_row.get("confidence"),
    })

@app.route('/api/organizations/<ein>/knowledge-graph')
@limiter.limit("60 per minute")
def get_knowledge_graph(ein):
    """Knowledge graph entities and relationships"""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    db = get_db()

    entities = []
    entity_rows = db.execute(
        "SELECT * FROM knowledge_graph_entities WHERE ein = ? LIMIT 50",
        (ein_clean,)
    ).fetchall()
    for row in entity_rows:
        row = dict(row)
        entities.append({
            "entity_type": row.get("entity_type"),
            "entity_value": row.get("entity_value"),
            "confidence": row.get("confidence"),
            "source": row.get("source"),
        })

    relationships = []
    rel_rows = db.execute(
        "SELECT * FROM knowledge_graph_relationships WHERE ein_from = ? LIMIT 50",
        (ein_clean,)
    ).fetchall()
    for row in rel_rows:
        row = dict(row)
        relationships.append({
            "relationship_type": row.get("relationship_type"),
            "ein_to": row.get("ein_to"),
            "confidence": row.get("confidence"),
        })

    return jsonify({
        "ein": ein_clean,
        "entities": entities,
        "relationships": relationships,
        "total_entities": len(entities),
        "total_relationships": len(relationships),
    })

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
    # propublica_financials was removed; serve single-year data from registry_enriched
    row = db.execute("""
        SELECT latest_tax_year, total_revenue, total_expenses, total_assets,
               total_liabilities, net_assets
        FROM registry_enriched
        WHERE EIN = ?
        LIMIT 1
    """, (ein_clean,)).fetchone()

    if not row or row['latest_tax_year'] is None:
        return jsonify({"ein": ein_clean, "financials": [], "total": 0})

    record = {
        "tax_prd_yr": row["latest_tax_year"],
        "totrevenue": row["total_revenue"],
        "totfuncexpns": row["total_expenses"],
        "totassetsend": row["total_assets"],
        "totliabend": row["total_liabilities"],
        "totnetassetend": row["net_assets"],
        "totcntrbgfts": None,
        "totprgmrevnue": None,
        "compnsatncurrofcr": None,
        "pdf_url": None,
    }
    return jsonify({
        "ein": ein_clean,
        "financials": [record],
        "total": 1,
    })

@app.route('/api/organizations/<ein>/financial-context')
@limiter.limit("60 per minute")
def get_financial_context_v6(ein):
    """
    V6 Financial Context endpoint.

    Returns comprehensive peer context using the v6 foundation.
    Uses v6 by default; ENABLE_V6_FINANCIAL_CONTEXT=false is an emergency rollback switch.

    Response includes:
    - organization_ein
    - methodology_version
    - data_status
    - ntee_code, ntee_level
    - geography_scope, geography_value
    - funding_archetype
    - revenue_band
    - selected_tier (Tier 1-5)
    - peer_group_description
    - organization_metric (months of reserve)
    - peer statistics (median, p25, p75, counts)
    - confidence and limitations
    - conditional_band_context (for Tier 2 without revenue)
    """

    ENABLE_V6 = os.environ.get('ENABLE_V6_FINANCIAL_CONTEXT', 'true').lower() == 'true'

    if not ENABLE_V6:
        return jsonify({
            'error': 'v6 financial context not yet enabled',
            'message': 'This endpoint is in development. Please check back soon.'
        }), 503

    # Sanitize EIN
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean or len(ein_clean) != 9:
        return jsonify({"error": "Invalid EIN format"}), 400

    try:
        from scripts.v6_financial_context_api import get_v6_financial_context
        db = get_db()
        context = get_v6_financial_context(db, ein_clean)

        if context is None:
            return jsonify({
                'organization_ein': ein_clean,
                'data_status': 'not_found',
                'message': 'Organization not found in v6 financial context'
            }), 404

        # Add metadata
        context['retrieved_at'] = datetime.utcnow().isoformat() + 'Z'
        context['endpoint_version'] = 'v6_foundation_2026-07-27'

        return jsonify(context)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'ein': ein_clean
        }), 500

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
# Only active tax-deductible 501(c)(3). Revoked orgs stay in registry_enriched
# (rows untouched, reversible) but are hidden from browse/search: donations to
# auto-revoked orgs are not tax-deductible, so listing them with tier badges
# would violate Principle 3. Direct /api/organizations/<ein> access still works
# and the donate gate (_is_revoked) independently fails closed.
_DEDUCTIBILITY_FILTER = (
    "subsection = '3' AND deductibility = '1' "
    "AND COALESCE(irs_revoked, 0) != 1 "
    "AND COALESCE(org_status, '') != 'revoked'"
)


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
        "scores_last_updated": (db.execute(
            "SELECT MAX(snapshot_date) FROM score_snapshots"
        ).fetchone()[0] if db.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='score_snapshots'"
        ).fetchone()[0] else None),
        "financial_records": financial_records,
        "with_reserve_data": agg["has_reserve"],
        "reserve_health": {
            "insolvent": agg["insolvent"],
            "at_risk": agg["at_risk"],
            "minimal": agg["minimal"],
            "healthy": agg["healthy"],
        },
        "irs_status_verified_at": (lambda r: r["synced_at"] if r else None)(
            db.execute("SELECT synced_at FROM irs_sync_log ORDER BY id DESC LIMIT 1").fetchone()
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='irs_sync_log'").fetchone()
            else None
        ),
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

    payload = {
        "generated_at": datetime.utcnow().isoformat() + 'Z',
        "sectors": result
    }
    _cset('sector_health', payload)
    return jsonify(payload)

@app.route('/api/scoring-runs')
@limiter.limit("20 per minute")
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

    # Audit log: volunteer interest submitted (no PII, anonymous signal)
    log_audit_event(
        event_type='volunteer_interest_submitted',
        org_ein=ein,
        user_auth='anonymous',
        success=True
    )

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


@app.route('/api/v5_feedback', methods=['POST'])
@limiter.limit("10 per minute; 50 per hour")
def submit_v5_feedback():
    # Week 3 beta feedback collection: structured form for v5 peer taxonomy.
    # All fields are optional except clarity and preference, which are booleans.
    # No identity tracking; anonymous aggregation only.
    data = request.get_json(silent=True) or {}
    ein = str(data.get('ein', '')).strip()[:20]
    org_name = str(data.get('org_name', '')).strip()[:200]
    archetype = str(data.get('archetype', '')).strip()[:80]
    clarity = data.get('clarity')  # boolean: true = clear, false = not clear
    clarity_reason = str(data.get('clarity_reason', '')).strip()[:1000] or None
    preference = data.get('preference')  # boolean: true = prefer peer, false = prefer single
    ntee_funding = str(data.get('ntee_funding', '')).strip()[:100] or None
    other_feedback = str(data.get('other_feedback', '')).strip()[:2000] or None
    timestamp = str(data.get('timestamp', '')).strip()[:50] or None

    if clarity is None or preference is None:
        return jsonify({'error': 'clarity and preference required'}), 400

    db = get_db()
    db.execute(
        """INSERT INTO v5_feedback (ein, org_name, archetype, clarity, clarity_reason,
           preference, ntee_funding, other_feedback, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ein, org_name, archetype, clarity, clarity_reason, preference, ntee_funding, other_feedback, timestamp),
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
        # T12 Phase 1: Extended search metrics for zero-result analysis
        query_length = int(data.get('query_length', 0)) if isinstance(data.get('query_length'), int) else 0
        result_count = int(data.get('result_count', 0)) if isinstance(data.get('result_count'), int) else 0
        zero_results = 1 if data.get('zero_results') == 'yes' else 0
        filters_applied = int(data.get('filters_applied', 0)) if isinstance(data.get('filters_applied'), int) else 0
        search_mode = str(data.get('mode', 'keyword')).strip().lower()[:20]
        if query_length > 0 or filters_applied > 0:
            db.execute(
                "INSERT INTO analytics_search_metrics (day, query_length, result_count, zero_results, filters_applied, search_mode) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(day, query_length, result_count, zero_results, filters_applied) DO UPDATE SET "
                "search_mode = excluded.search_mode",
                (day, query_length, result_count, zero_results, filters_applied, search_mode),
            )
            # Log zero-result queries for pattern discovery
            if zero_results and term:
                db.execute(
                    "INSERT INTO analytics_zero_result_queries (day, query, query_length, filters_applied, search_mode) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(day, query) DO UPDATE SET "
                    "occurrence_count = occurrence_count + 1, last_seen_at = CURRENT_TIMESTAMP",
                    (day, term, query_length, filters_applied, search_mode),
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
        app.logger.exception("financial-data submission failed")
        return jsonify({"error": "Submission failed. Please try again."}), 500


@app.route('/api/org/<ein>/submission-status', methods=['GET'])
@limiter.limit("60 per minute")
def org_submission_status(ein):
    """Check if org has submitted data and when it will be scored."""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    db = get_db()

    # Check if already scored. financial_health lives on registry_enriched,
    # not v4_scores (fixed 2026-07-10 -- v4_scores is a 5-column table:
    # EIN, score, tier, band, operating_model; financial_health and the
    # 'visibility_tier' key name here were stale references to a schema
    # that no longer exists, so this endpoint 500'd for any scored EIN).
    scored = db.execute(
        """SELECT v4.tier, r.financial_health
           FROM v4_scores v4 JOIN registry_enriched r ON r.EIN = v4.EIN
           WHERE v4.EIN = ?""",
        (ein_clean,)
    ).fetchone()
    if scored:
        return jsonify({
            "status": "scored",
            "visibility_tier": scored['tier'],
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
    limit = _int_arg('limit', 20, hi=50)

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


# ── Admin: claims queue ────────────────────────────────────────────────────
# The founder's phone-verification worklist. Everything here is PII and stays
# behind the admin key. mark_called writes the audit trail that the identity
# call happened; revoke requires a written reason and starts the 45-day
# cooldown via revoked_at (enforced in claim_start).

_CLAIM_STATUSES = {'pending', 'verified', 'active', 'revoked', 'letter_sent'}


@app.route('/api/admin/today', methods=['GET'])
@require_admin_key
def admin_today():
    """The daily worklist — the system says what needs attention so nothing
    is scanned for or remembered. Buckets: claims waiting for the
    verification call, and called claims whose PIN expires within 2 days."""
    db = get_db()
    to_call = [dict(r) for r in db.execute("""
        SELECT c.ein, r.organization_name, c.rep_name, c.rep_title, c.phone, c.created_at,
               CAST(julianday('now') - julianday(c.created_at) AS INTEGER) AS days_waiting
        FROM org_claims c LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status = 'pending' AND c.called_at IS NULL
        ORDER BY c.created_at ASC""").fetchall()]
    pin_expiring = [dict(r) for r in db.execute("""
        SELECT c.ein, r.organization_name, c.rep_name, c.email, c.pin_expires_at,
               CAST(julianday(c.pin_expires_at) - julianday('now') AS INTEGER) AS days_left
        FROM org_claims c LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status = 'pending' AND c.called_at IS NOT NULL
          AND datetime(c.pin_expires_at) < datetime('now', '+2 days')
        ORDER BY c.pin_expires_at ASC""").fetchall()]
    return jsonify({
        'to_call': to_call,
        'pin_expiring': pin_expiring,
        'counts': {'to_call': len(to_call), 'pin_expiring': len(pin_expiring)},
    })


@app.route('/api/admin/activity/<ein>', methods=['GET'])
@require_admin_key
def admin_org_activity(ein):
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    db = get_db()
    rows = db.execute(
        "SELECT event_type, detail, actor, created_at FROM org_activity "
        "WHERE ein = ? ORDER BY created_at DESC LIMIT 100", (ein,)).fetchall()
    return jsonify({'activity': [dict(r) for r in rows]})


@app.route('/api/admin/claims', methods=['GET'])
@require_admin_key
def admin_claims_list():
    status = request.args.get('status', '').strip()
    where, params = '', []
    if status in _CLAIM_STATUSES:
        where = 'WHERE c.claim_status = ?'
        params.append(status)
    db = get_db()
    rows = db.execute(
        f"""SELECT c.ein, c.email, c.phone, c.rep_name, c.rep_title, c.pin, c.pin_expires_at,
                   c.claim_status, c.created_at, c.attested_at, c.attestation_version,
                   c.verified_at, c.called_at, c.call_notes, c.revoked_at, c.revoke_reason,
                   r.organization_name, r.CITY, r.STATE
            FROM org_claims c
            LEFT JOIN registry_enriched r ON r.EIN = c.ein
            {where}
            ORDER BY c.created_at DESC LIMIT 200""", params).fetchall()
    return jsonify({'claims': [dict(r) for r in rows], 'total': len(rows)})


@app.route('/api/admin/claims/<ein>', methods=['PATCH'])
@require_admin_key
def admin_claims_update(ein):
    data   = request.get_json(silent=True) or {}
    action = (data.get('action') or '').strip()
    ein    = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()
    if not db.execute("SELECT 1 FROM org_claims WHERE ein = ?", (ein,)).fetchone():
        return jsonify({"error": "No claim found for this EIN"}), 404

    if action == 'mark_called':
        notes = (data.get('notes') or '').strip()[:1000]
        db.execute(
            "UPDATE org_claims SET called_at = datetime('now'), call_notes = ? WHERE ein = ?",
            (notes, ein))
        db.commit()
        _log_org_activity(ein, 'call_logged', notes, actor='admin')
        return jsonify({"status": "called"})

    if action == 'revoke':
        reason = (data.get('reason') or '').strip()[:500]
        if not reason:
            return jsonify({"error": "A written reason is required to revoke a claim"}), 400
        db.execute(
            "UPDATE org_claims SET claim_status = 'revoked', revoked_at = datetime('now'), "
            "revoke_reason = ? WHERE ein = ?", (reason, ein))
        db.commit()
        _log_org_activity(ein, 'claim_revoked', reason, actor='admin')
        return jsonify({"status": "revoked"})

    return jsonify({"error": "Unknown action. Use mark_called or revoke."}), 400


def _normalize_spoken_url(raw: str) -> str:
    """Phone callers say 'ourorg.org', not 'https://ourorg.org' — prefix the
    scheme on a bare domain so the shared http(s)-only guard can accept it.
    Anything that doesn't look like a domain passes through unchanged (and
    the guard then drops it)."""
    u = (raw or '').strip()
    if u and not u.lower().startswith(('http://', 'https://')) \
            and re.match(r'^[a-z0-9]', u, re.IGNORECASE) \
            and '.' in u.split('/')[0] and ' ' not in u:
        return 'https://' + u
    return u


def _normalize_public_url(raw) -> str:
    """Server-side mirror of frontend/src/utils/externalLink.ts normalizeExternalUrl
    (T11 gap 2, EXECUTION_HANDOFF_2026_07_12.md). Every endpoint that persists a
    caller-supplied URL (org claims, guild vendor codes, community partner
    applications) must call this — not just startswith(http) — so a URL a UI
    bug or a direct API call slips past is never stored: rejects javascript:/
    data:/mailto: schemes, bare "https://" with no host, and any hostname with
    no dot (e.g. "https://localhost"). Bare domains get "https://" prefixed.
    """
    u = (raw or '').strip()[:500]
    if not u:
        return ''
    u = _normalize_spoken_url(u)
    try:
        parsed = urllib.parse.urlsplit(u)
    except ValueError:
        return ''
    if parsed.scheme not in ('http', 'https'):
        return ''
    if not parsed.hostname or '.' not in parsed.hostname:
        return ''
    return u


@app.route('/api/admin/concierge/confirm', methods=['POST'])
@require_admin_key
def admin_concierge_confirm():
    """Operator confirms a concierge-call Quick-Start draft (pilot T2).

    DISCLOSURE STANDARD (Stewardship Board 2026-07-11):
    Before confirming any profile via this endpoint, the human operator on
    the call MUST disclose to the organization that Daanaa prepared a draft
    using publicly available information. Recommended language:

      "Hello, this is ____ from Daanaa. We've prepared a draft of your
       public nonprofit profile using publicly available information to save
       your team time. We'd like to review it with you, make any corrections
       you feel are appropriate, and only publish enhancements you approve."

    This endpoint itself does NOT make the disclosure (the human does via
    phone). The endpoint exists only to record that the human has confirmed
    the organization's consent AFTER the disclosure. AI is infrastructure,
    never deception. Remain unobtrusive, never undisclosed.

    TECHNICAL BOUNDARY:
    Writes through the SAME field-update semantics as /api/claim/update
    (shared _sanitize/_write helpers — never forked), authenticated by the
    admin key. The org's verification token is NEVER accepted or replayed
    on this path. Verification boundary (stewardship P3): only claims
    already 'verified' or 'active' can be written — everything else is 403
    and no field changes. The human operator confirms every write (P10).
    """
    data = request.get_json(silent=True) or {}

    # This path never handles org credentials — reject them outright rather
    # than silently ignoring, so a miswired client fails loudly.
    if any(k in data for k in ('verification_token', 'token', 'pin')):
        return jsonify({'error': 'This endpoint never accepts org verification credentials'}), 400

    ein = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    call_sid = re.sub(r'[^A-Za-z0-9_-]', '', data.get('call_sid') or '')[:64]
    operator_note = (data.get('operator_note') or '').strip()[:500]
    if not ein:
        return jsonify({'error': 'EIN required'}), 400
    if not call_sid:
        return jsonify({'error': 'call_sid required — every concierge write must trace to a call'}), 400

    db = get_db()
    row = db.execute('SELECT claim_status FROM org_claims WHERE ein = ?', (ein,)).fetchone()
    if not row or row['claim_status'] not in ('verified', 'active'):
        # Hard verification boundary: the concierge path completes profiles
        # for verified orgs; it must never become a verification bypass.
        return jsonify({'error': 'Organization claim is not verified. '
                                 'Concierge writes require a verified claim.'}), 403

    # Map Quick-Start field names onto the claim editor's schema, then run
    # the exact same sanitization the editor uses.
    f = _sanitize_claim_profile_fields({
        'custom_mission':   data.get('mission'),
        'donate_confirmed': data.get('donate_confirmed', False),
        'donate_url':       _normalize_spoken_url(data.get('donate_url') or ''),
        'website_url':      _normalize_spoken_url(data.get('website') or ''),
    })
    written = _write_claimed_fields_to_registry(db, ein, f)

    # Public contact — same unified-contact semantics as /api/claim/contacts.
    contact_email = (data.get('contact_email') or '').strip()[:254] or None
    contact_phone = (data.get('contact_phone') or '').strip()[:30] or None
    if contact_email or contact_phone:
        db.execute("""
            UPDATE org_claims
            SET contact_preference='unified',
                volunteer_contact_email=?, volunteer_contact_phone=?,
                donor_contact_email=?, donor_contact_phone=?
            WHERE ein=?
        """, (contact_email, contact_phone, contact_email, contact_phone, ein))
        written.append('contact')

    volunteer_note = (data.get('volunteer_note') or '').strip()[:300] or None
    if volunteer_note:
        written.append('volunteer_note')

    # Provenance on org_claims — source, call linkage, attestation version,
    # operator summary. No schema change: structured into call_notes, with
    # the full record in org_activity (explainable later, P9).
    if f['custom_mission']:
        db.execute("UPDATE org_claims SET custom_mission=? WHERE ein=?",
                   (f['custom_mission'], ein))
    if f['website_url']:
        db.execute("UPDATE org_claims SET website_url=? WHERE ein=?",
                   (f['website_url'], ein))
    if f['donate_confirmed'] and f['donate_url']:
        db.execute("UPDATE org_claims SET donate_confirmed=1 WHERE ein=?", (ein,))
    note = f"source=concierge_call; call_sid={call_sid}; attestation={CLAIM_ATTESTATION_VERSION}"
    if volunteer_note:
        note += f"; volunteer_note={volunteer_note}"
    if operator_note:
        note += f"; operator_note={operator_note}"
    db.execute(
        "UPDATE org_claims SET called_at=datetime('now'), call_notes=? WHERE ein=?",
        (note[:1000], ein))
    db.commit()

    # Evict org cache entries for this EIN (same as claim_update)
    stale = [k for k in _CACHE if ein in k]
    for k in stale:
        _CACHE.pop(k, None)

    _log_org_activity(ein, 'concierge_draft_confirmed',
                      f"call_sid={call_sid}; fields={','.join(written) or 'none'}; "
                      f"note={operator_note}", actor='admin')
    return jsonify({'success': True, 'saved': written})


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
    limit  = _int_arg('limit', 200, hi=500)
    offset = _int_arg('offset', 0, hi=10_000_000)
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

# Version tag for the attestation text the claimant agreed to. The full text of
# each version is recorded in docs/CLAIM-ATTESTATIONS.md — bump this whenever
# that text changes so every stored claim is traceable to the exact wording.
CLAIM_ATTESTATION_VERSION = "2026-06-11.v1"


def _send_daanaa_email(to_addr: str, subject: str, body: str,
                       html: str | None = None, from_addr: str = "verify@daanaa.org"):
    """Send platform email via the email_agent Gmail token, in a daemon thread
    so callers never block or fail on mail problems. All communication stays
    within daanaa.org (founder directive 2026-06-11): from_addr must be one of
    the 9 live send-as aliases. `body` is the plain-text part; pass `html` for
    a rich alternative (org-facing mail should always include one)."""
    def _send():
        try:
            import base64
            from email.message import EmailMessage
            from scripts.email_agent.oauth import gmail_service
            msg = EmailMessage()
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.set_content(body)
            if html:
                msg.add_alternative(html, subtype="html")
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()
        except Exception as e:
            _logger.error(f"daanaa email to {to_addr} failed: {e}")

    threading.Thread(target=_send, daemon=True).start()


def _format_phone(phone: str) -> str:
    """Render a US phone number as (XXX) XXX-XXXX for display; anything that
    isn't 10 digits (or 11 with a leading 1) passes through as entered."""
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone


def _send_volunteer_interest_email(contact_email: str, contact_name: str, event_title: str, volunteer_email: str):
    """Notify nonprofit volunteer coordinator when someone expresses interest."""
    body = f"""Hi {contact_name},

Someone has expressed interest in volunteering for "{event_title}" through Daanaa.

Volunteer email: {volunteer_email}

Log in to your Daanaa nonprofit dashboard to see more details and connect with them.

Best,
Daanaa Team
"""
    _send_daanaa_email(
        contact_email,
        f"New volunteer interest in {event_title}",
        body,
        from_addr="hello@daanaa.org"
    )


def _notify_admin_new_claim(ein: str, org_name: str, email: str, phone: str, title: str, pin: str,
                            rep_name: str = ''):
    """Email the admin when a claim comes in. Phase 1 verification is a phone
    call, so the email carries everything needed to make it — including the
    PIN to read out once identity is confirmed."""
    to_addr = os.environ.get("DAANAA_ADMIN_NOTIFY_EMAIL", "orgs@daanaa.org")
    _send_daanaa_email(
        to_addr,
        f"[Daanaa claim] {org_name} ({ein})",
        f"New page claim — call to verify, then read them the PIN.\n\n"
        f"Organization: {org_name}\n"
        f"EIN:          {ein}\n"
        f"Name:         {rep_name or '(not given)'}\n"
        f"Contact:      {email}\n"
        f"Phone:        {_format_phone(phone)}\n"
        f"Title/role:   {title}\n"
        f"PIN:          {pin}  (expires in 7 days)\n\n"
        f"Org page:     https://daanaa.org/org/{ein}\n"
        f"They enter the PIN at https://daanaa.org/claim/verify?ein={ein}&email={email}\n",
    )


def _claim_received_email_body(org_name: str, ein: str, phone: str, rep_name: str = '') -> str:
    """Plain-text part of the confirmation the claiming org receives. No PIN
    here — the PIN is given on the verification call, which is the whole point
    of the call. Copy rules: human voice, no hyphens, no dashes."""
    first = rep_name.split()[0] if rep_name.strip() else ''
    return (
        f"Hello{' ' + first if first else ''},\n\n"
        f"Thank you for claiming {org_name} (EIN {ein}) on Daanaa.\n\n"
        f"Here is what happens next. A member of our team will call you at "
        f"{_format_phone(phone)} within a few business days to confirm that you represent the "
        f"organization. On that call we will give you a 6 digit PIN.\n\n"
        f"When you have your PIN, enter it at https://daanaa.org/claim/verify?ein={ein} "
        f"and your page opens for editing. The PIN stays good for 7 days.\n\n"
        f"A couple of things worth knowing. Daanaa is a free public directory of "
        f"nonprofits built from IRS records. We never charge organizations and we "
        f"never handle donations. Your phone number and email are used only for "
        f"this verification and neither is shown publicly.\n\n"
        f"If you did not submit this claim, reply to this email and we will cancel it.\n\n"
        f"Warmly,\n"
        f"The Daanaa team\n"
        f"verify@daanaa.org · daanaa.org\n"
    )


def _claim_received_email_html(org_name: str, ein: str, phone: str, rep_name: str = '') -> str:
    """Rich HTML part. Brand: deep navy, soft gold, Georgia serif, hosted logo.
    Inline styles only — email clients strip everything else."""
    verify_url = f"https://daanaa.org/claim/verify?ein={ein}"
    gold, navy, grey = "#C9A96E", "#1a1a2e", "#5a6472"
    step_style = (
        f"display:inline-block;width:26px;height:26px;line-height:26px;border-radius:50%;"
        f"background:{gold};color:{navy};font-weight:bold;text-align:center;"
        f"font-size:14px;margin-right:12px;"
    )
    steps = [
        f"A member of our team calls you at <strong>{_format_phone(phone)}</strong> within a few business days.",
        "On the call we confirm your role and give you a 6 digit PIN.",
        f"You enter the PIN at <a href=\"{verify_url}\" style=\"color:{gold};\">daanaa.org/claim/verify</a> and your page opens for editing.",
    ]
    steps_html = "".join(
        f"<tr><td style='vertical-align:top;padding:8px 0;'><span style='{step_style}'>{i}</span></td>"
        f"<td style='vertical-align:middle;padding:8px 0;font-size:15px;line-height:1.6;color:{navy};'>{s}</td></tr>"
        for i, s in enumerate(steps, 1)
    )
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#F4EFE4;font-family:Georgia,'Times New Roman',serif;">
  <div style="max-width:560px;margin:0 auto;padding:32px 16px;">
    <div style="background:{navy};border-radius:16px 16px 0 0;text-align:center;padding:32px 24px 24px;">
      <img src="https://daanaa.org/logo.png" alt="Daanaa" width="72" height="72" style="display:block;margin:0 auto 12px;">
      <div style="color:{gold};font-size:26px;letter-spacing:0.06em;">Daanaa</div>
      <div style="color:#b8bfc9;font-size:12px;margin-top:4px;">A public directory of nonprofits, built from IRS records</div>
    </div>
    <div style="height:3px;background:linear-gradient(90deg,transparent,{gold} 30%,#D4B87A 50%,{gold} 70%,transparent);"></div>
    <div style="background:#ffffff;border-radius:0 0 16px 16px;padding:36px 36px 28px;">
      <h1 style="font-size:22px;font-style:italic;color:{navy};margin:0 0 6px;">We received your claim</h1>
      <p style="font-size:16px;color:{navy};margin:0 0 4px;"><strong>{org_name}</strong></p>
      <p style="font-size:13px;color:{grey};margin:0 0 24px;">EIN {ein}</p>
      <p style="font-size:15px;line-height:1.65;color:{navy};margin:0 0 20px;">
        Hello{' ' + rep_name.split()[0] if rep_name.strip() else ''}, and thank you for claiming your page. Here is what happens next.
      </p>
      <table style="border-collapse:collapse;margin:0 0 24px;">{steps_html}</table>
      <p style="font-size:13px;line-height:1.65;color:{grey};margin:0 0 8px;">
        The PIN stays good for 7 days. Your phone number and email are used only
        for this verification and neither is shown publicly.
      </p>
      <p style="font-size:13px;line-height:1.65;color:{grey};margin:0 0 24px;">
        Daanaa is free for organizations. We never charge for a listing or a claim
        and we never handle donations.
      </p>
      <p style="font-size:14px;line-height:1.6;color:{navy};margin:0;">
        Warmly,<br>The Daanaa team
      </p>
    </div>
    <p style="text-align:center;font-size:11px;color:{grey};margin:20px 0 0;line-height:1.6;">
      You are receiving this because a claim for {org_name} was submitted at daanaa.org.<br>
      If that was not you, reply to this email and we will cancel it.<br>
      <a href="https://daanaa.org" style="color:{gold};">daanaa.org</a> · verify@daanaa.org
    </p>
  </div>
</body></html>"""


def _send_claim_received_email(ein: str, org_name: str, email: str, phone: str, rep_name: str = ''):
    _send_daanaa_email(email, f"We received your claim for {org_name}",
                       _claim_received_email_body(org_name, ein, phone, rep_name),
                       html=_claim_received_email_html(org_name, ein, phone, rep_name),
                       from_addr="Daanaa <verify@daanaa.org>")


@app.route('/api/claim/start', methods=['POST'])
@limiter.limit("3 per hour")
def claim_start():
    data  = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    email = (data.get('email') or '').strip()[:254]
    phone = (data.get('phone') or '').strip()[:30]
    name  = (data.get('name') or '').strip()[:120]
    title = (data.get('title') or '').strip()[:100]

    if not ein or not email or '@' not in email:
        return jsonify({"error": "EIN and valid email are required"}), 400
    if len(''.join(c for c in phone if c.isdigit())) < 10:
        return jsonify({"error": "A valid phone number is required. We call it to verify your claim."}), 400
    if not name:
        return jsonify({"error": "Your name is required. The attestations below are signed by a person."}), 400
    if not title:
        return jsonify({"error": "Your title or role at the organization is required"}), 400
    # Attestations are a legal requirement — enforced here, not just by the form
    if not (data.get('attested_authority') is True and data.get('attested_legal') is True):
        return jsonify({"error": "Both attestations are required to submit a claim"}), 400

    db  = get_db()
    row = db.execute(
        "SELECT EIN, organization_name, street_address, CITY, STATE, zipcode FROM registry_enriched WHERE EIN = ?",
        (ein,)
    ).fetchone()
    if not row:
        return jsonify({"error": "Organization not found"}), 404

    org_name    = row['organization_name']
    street      = row['street_address'] or ''
    irs_address = f"{street}, {row['CITY'] or ''}, {row['STATE'] or ''} {row['zipcode'] or ''}".strip(", ")

    existing = db.execute(
        "SELECT claim_status, revoked_at FROM org_claims WHERE ein = ?", (ein,)
    ).fetchone()
    if existing and existing['claim_status'] in ('active', 'verified'):
        return jsonify({"error": "This organization has already been claimed"}), 409
    if existing and existing['claim_status'] == 'letter_sent':
        return jsonify({"error": "A verification letter was already sent. Check your mail or contact orgs@daanaa.org to resend."}), 409
    if existing and existing['claim_status'] == 'revoked':
        # Legal review requirement: a revoked claim sits out 45 days before
        # the EIN can be claimed again.
        in_cooldown = db.execute(
            "SELECT datetime('now') < datetime(?, '+45 days') AS cooling",
            (existing['revoked_at'],)
        ).fetchone()
        if existing['revoked_at'] and in_cooldown['cooling']:
            return jsonify({"error": "A previous claim on this organization was revoked. "
                                     "New claims are accepted 45 days after revocation — "
                                     "contact orgs@daanaa.org if you believe this is an error."}), 403

    pin            = str(secrets.randbelow(900000) + 100000)
    pin_expires_at = db.execute("SELECT datetime('now', '+7 days')").fetchone()[0]

    db.execute("""
        INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at, claim_status,
                                phone, rep_name, rep_title, attested_at, attestation_version)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, datetime('now'), ?)
        ON CONFLICT(ein) DO UPDATE SET
            email=excluded.email, pin=excluded.pin,
            pin_expires_at=excluded.pin_expires_at,
            phone=excluded.phone, rep_name=excluded.rep_name,
            rep_title=excluded.rep_title,
            attested_at=excluded.attested_at,
            attestation_version=excluded.attestation_version,
            claim_status='pending', letter_sent_at=NULL, lob_letter_id=NULL,
            revoked_at=NULL, revoke_reason=NULL
    """, (ein, email, irs_address, pin, pin_expires_at, phone, name, title, CLAIM_ATTESTATION_VERSION))
    db.commit()

    _log_org_activity(ein, 'claim_submitted', f"{name} ({title}), {email}", actor='org')
    _notify_admin_new_claim(ein, org_name, email, phone, title, pin, rep_name=name)
    _send_claim_received_email(ein, org_name, email, phone, rep_name=name)

    # Phase 2 (postal verification via Lob) only runs once a Lob key is
    # configured AND the org has a street address. Phase 1: the claim stays
    # 'pending' and the admin verifies by phone.
    claim_status = "pending"
    if os.environ.get("LOB_API_KEY") and street:
        try:
            import sys
            sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent / 'scripts'))
            from send_claim_letter import send_claim_letter
            address = {'street': street, 'city': row['CITY'] or '',
                       'state': row['STATE'] or '', 'zip': row['zipcode'] or ''}
            letter_id = send_claim_letter(ein, org_name, address, pin)
            if letter_id and not letter_id.startswith("log:"):
                claim_status = "letter_sent"
                db.execute(
                    "UPDATE org_claims SET claim_status=?, letter_sent_at=datetime('now'), lob_letter_id=? WHERE ein=?",
                    (claim_status, letter_id, ein)
                )
                db.commit()
        except Exception as e:
            _logger.error(f"send_claim_letter failed for {ein}: {e}")

    # Friendly address preview (first line only for privacy)
    preview = f"{street}, {row['CITY']}, {row['STATE']}" if street else irs_address
    return jsonify({"status": claim_status, "org_name": org_name, "address_preview": preview})


@app.route('/api/claim/login', methods=['POST'])
@limiter.limit("5 per hour")
def claim_login():
    """Re-entry magic link for a verified claimant who lost their edit link.
    Security properties: the link only ever goes to the email on file from the
    verified claim (never the address the requester typed), unverified claims
    get nothing, and the response is identical whether or not a claim exists
    so this endpoint cannot probe which orgs are claimed."""
    data  = request.get_json(silent=True) or {}
    value = (data.get('ein_or_email') or '').strip()[:254]
    # One response for every outcome — never confirm or deny a claim exists.
    neutral = {"status": "sent",
               "message": "If this matches a claimed page, the edit link is on its way to the email on file."}
    if not value:
        return jsonify(neutral)

    digits = ''.join(c for c in value if c.isdigit())
    db = get_db()
    if len(digits) >= 9:
        row = db.execute(
            "SELECT ein, email, pin, rep_name FROM org_claims "
            "WHERE ein = ? AND claim_status IN ('verified', 'active')", (digits[:10],)).fetchone()
    else:
        row = db.execute(
            "SELECT ein, email, pin, rep_name FROM org_claims "
            "WHERE lower(email) = lower(?) AND claim_status IN ('verified', 'active')", (value,)).fetchone()
    if not row:
        return jsonify(neutral)

    org = db.execute("SELECT organization_name FROM registry_enriched WHERE EIN = ?",
                     (row['ein'],)).fetchone()
    org_name = org['organization_name'] if org else 'your organization'
    first = (row['rep_name'] or '').split(' ')[0]
    token = _make_verify_token(row['ein'], row['pin'])
    _send_daanaa_email(
        row['email'],
        f"Your Daanaa edit link for {org_name}",
        f"Hello{' ' + first if first else ''},\n\n"
        f"Here is your link to edit the {org_name} page on Daanaa:\n\n"
        f"https://daanaa.org/claim/edit?ein={row['ein']}&token={token}\n\n"
        f"This link is personal to your claim. If you did not ask for it, you can "
        f"ignore this email and nothing changes.\n\n"
        f"Warmly,\nThe Daanaa team\nverify@daanaa.org · daanaa.org\n",
        from_addr="Daanaa <verify@daanaa.org>",
    )
    _log_org_activity(row['ein'], 'login_link_sent', f"edit link emailed to {row['email']}", actor='org')
    return jsonify(neutral)


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
        return jsonify({"error": "PIN has expired. Please submit a new claim request at daanaa.org/for-nonprofits."}), 410

    db.execute(
        "UPDATE org_claims SET claim_status='verified', verified_at=datetime('now') WHERE ein=?",
        (ein,)
    )
    db.commit()
    _log_org_activity(ein, 'pin_verified', 'PIN entered, page unlocked for editing', actor='org')

    org = db.execute(
        "SELECT organization_name, mission, donate_url FROM registry_enriched WHERE EIN=?", (ein,)
    ).fetchone()

    org_name = org['organization_name'] if org else ""

    rep_email = row['email'] if 'email' in row.keys() else None
    if rep_email:
        _rname = (row['rep_name'] if 'rep_name' in row.keys() else None) or 'there'
        portal_url = f"https://daanaa.org/nonprofit/{ein}/portal"
        _send_daanaa_email(
            rep_email,
            f"Your Daanaa page for {org_name} is verified",
            f"Hi {_rname},\n\n"
            f"Great news — {org_name} is verified on Daanaa.\n\n"
            f"You can update your mission, add programs, and manage your page from your portal:\n"
            f"{portal_url}\n\n"
            f"A few things worth doing first:\n"
            f"  - Add or confirm your mission statement (it's what donors read first)\n"
            f"  - Check that your service area and cause tags are accurate\n"
            f"  - If anything on your IRS record looks off, use 'Report an issue' on your page\n\n"
            f"Questions? Reply to this email.\n\n"
            f"The Daanaa Team\n"
            f"  daanaa.org · hello@daanaa.org",
            from_addr="Daanaa <hello@daanaa.org>",
        )

    return jsonify({
        "status": "verified",
        "ein": ein,
        "org_name": org_name,
        "current_mission": org['mission'] if org else None,
        "current_donate_url": org['donate_url'] if org else None,
        "irs_address": row['irs_address'],
        "verification_token": _make_verify_token(ein, row['pin']),
    })


@app.route('/api/claim/link-firebase', methods=['POST'])
@limiter.limit("20 per hour")
def claim_link_firebase():
    """
    After PIN verification, link a Firebase UID to the org's claim.
    Body: { ein, verification_token }
    Auth: Bearer <firebase-id-token>
    """
    uid  = _require_firebase_user()
    data = request.get_json(silent=True) or {}
    ein  = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('verification_token') or '').strip()[:64]
    if not ein or not token:
        return jsonify({'error': 'ein and verification_token required'}), 400
    db  = get_db()
    row = db.execute('SELECT pin, claim_status FROM org_claims WHERE ein=?', (ein,)).fetchone()
    if not row or row['claim_status'] == 'revoked':
        return jsonify({'error': 'Claim not found'}), 404
    if not _verify_claim_token(ein, token):
        return jsonify({'error': 'Invalid verification token'}), 403
    db.execute('UPDATE org_claims SET firebase_uid=? WHERE ein=?', (uid, ein))
    db.commit()
    _log_org_activity(ein, 'firebase_linked', f'Firebase UID linked to claim', actor='org')
    return jsonify({'ok': True})


@app.route('/api/claim/my-orgs', methods=['GET'])
@limiter.limit("60 per minute")
def claim_my_orgs():
    """Return all verified claims belonging to the authenticated Firebase user."""
    uid = _require_firebase_user()
    db  = get_db()
    rows = db.execute(
        """SELECT c.ein, c.claim_status, c.verified_at, r.organization_name, r.city, r.state
           FROM org_claims c
           LEFT JOIN registry_enriched r ON r.EIN = c.ein
           WHERE c.firebase_uid = ? AND c.claim_status != 'revoked'
           ORDER BY c.verified_at DESC""",
        (uid,)
    ).fetchall()
    return jsonify({'orgs': [dict(r) for r in rows]})


@app.route('/api/claim/portal-token', methods=['GET'])
@limiter.limit("30 per minute")
def claim_portal_token():
    """
    Return a fresh verification_token for an org the Firebase user has already claimed.
    No PIN required — Firebase auth proves identity.
    Query param: ?ein=<ein>
    """
    uid = _require_firebase_user()
    ein = ''.join(c for c in (request.args.get('ein') or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'ein required'}), 400
    db  = get_db()
    row = db.execute(
        'SELECT pin, claim_status FROM org_claims WHERE ein=? AND firebase_uid=?',
        (ein, uid)
    ).fetchone()
    if not row:
        return jsonify({'error': 'No linked claim found for this org'}), 404
    if row['claim_status'] == 'revoked':
        return jsonify({'error': 'This claim has been revoked'}), 403
    return jsonify({
        'ein': ein,
        'verification_token': _make_verify_token(ein, row['pin']),
    })


def _sanitize_claim_profile_fields(data: dict) -> dict:
    """Sanitize the claim editor's profile fields (one source of truth).

    Shared by /api/claim/update (org rep, verification token) and
    /api/admin/concierge/confirm (operator, admin key) so the two paths can
    never drift on what a claim may write or how values are cleaned (P3/P7).
    """
    donate_url  = _normalize_public_url(data.get('donate_url'))
    website_url = _normalize_public_url(data.get('website_url'))
    return {
        'custom_mission':     (data.get('custom_mission') or '').strip()[:300],
        'custom_description': (data.get('custom_description') or '').strip()[:500],
        'cause_tags_json':    (data.get('cause_tags_json') or '[]').strip(),
        'donate_confirmed':   bool(data.get('donate_confirmed', False)),
        'donate_url':         donate_url,
        'website_url':        website_url,
    }


def _write_claimed_fields_to_registry(db, ein: str, f: dict) -> list:
    """Store sanitized claim fields in org_claims (LOCK-FREE, no registry writes).

    All nonprofit-claimed data stays in org_claims, keyed by EIN. API responses
    JOIN org_claims + registry_enriched and prefer claimed values. This avoids
    write locks on the immutable IRS data.

    Donate URL flips to 'claimed' only with an explicit confirm — same guard
    for every caller. Returns the list of fields written (for instrumentation).
    Caller commits.
    """
    written = []
    # Build update dict with only non-null fields
    updates = {}
    if f['custom_mission']:
        updates['custom_mission'] = f['custom_mission']
        written.append('mission')
    if f['website_url']:
        updates['website_url'] = f['website_url']
        written.append('website')
    if f['donate_url'] and f['donate_confirmed']:
        updates['donate_url'] = f['donate_url']
        written.append('donate_url')
    if f['cause_tags_json'] and f['cause_tags_json'] != '[]':
        updates['cause_tags_json'] = f['cause_tags_json']
        written.append('cause_tags')

    # Write all claimed fields to org_claims in one operation
    if updates:
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [ein]
        db.execute(f"UPDATE org_claims SET {set_clause} WHERE ein = ?", values)

    # Mark status fields in registry_enriched when claimed
    if f['donate_url'] and f['donate_confirmed']:
        db.execute("UPDATE registry_enriched SET donate_url_status='claimed', donate_confidence=95 WHERE EIN=?", (ein,))
    if f['website_url']:
        db.execute("UPDATE registry_enriched SET website_status='claimed' WHERE EIN=?", (ein,))
    if f['custom_mission']:
        db.execute("UPDATE registry_enriched SET mission_source='claimed' WHERE EIN=?", (ein,))

    return written


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

    f = _sanitize_claim_profile_fields(data)

    try:
        # Update org_claims record
        db.execute("""
            UPDATE org_claims
            SET claim_status     = 'verified',
                verified_at      = datetime('now'),
                custom_mission   = ?,
                custom_description = ?,
                donate_confirmed = ?,
                website_url      = ?
            WHERE ein = ?
        """, (f['custom_mission'] or None, f['custom_description'] or None,
              int(f['donate_confirmed']), f['website_url'] or None, ein))

        _write_claimed_fields_to_registry(db, ein, f)

        db.commit()
        # Evict org cache entries for this EIN
        stale = [k for k in _CACHE if ein in k]
        for k in stale:
            _CACHE.pop(k, None)
        return jsonify({
            'success': True,
            'message': 'Saved. Your public page updates within 24 hours (usually sooner).'
        }), 200

    except Exception as e:
        app.logger.exception('claim profile update failed')
        return jsonify({'error': 'Update failed. Please try again.'}), 500


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
    return jsonify({
        "status": "updated",
        "message": "Saved. Your public page updates within 24 hours (usually sooner)."
    })


@app.route('/api/claim/contacts', methods=['PATCH'])
@limiter.limit("20 per minute")
def claim_contacts_update():
    """Update nonprofit contact preferences for volunteers/donors."""
    data = request.get_json(silent=True) or {}
    ein  = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    pin  = ''.join(c for c in (data.get('pin') or '') if c.isdigit())[:6]

    if not ein or not pin:
        return jsonify({"error": "EIN and PIN are required"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM org_claims WHERE ein=?", (ein,)).fetchone()
    if not row or row['pin'] != pin or row['claim_status'] not in ('verified', 'active'):
        return jsonify({"error": "Not authorized — verify your PIN first"}), 403

    # Contact preference: 'unified' (all contacts same) or 'separate' (different contacts)
    contact_preference = data.get('contact_preference', 'unified')
    if contact_preference not in ('unified', 'separate'):
        contact_preference = 'unified'

    # If unified, use the primary email/phone for all
    if contact_preference == 'unified':
        contact_name = (data.get('contact_name') or '').strip() or None
        contact_email = (data.get('contact_email') or '').strip() or None
        contact_phone = (data.get('contact_phone') or '').strip() or None

        db.execute("""
            UPDATE org_claims
            SET contact_preference=?,
                volunteer_contact_name=?, volunteer_contact_email=?, volunteer_contact_phone=?,
                donor_contact_name=?, donor_contact_email=?, donor_contact_phone=?
            WHERE ein=?
        """, (
            contact_preference,
            contact_name, contact_email, contact_phone,
            contact_name, contact_email, contact_phone,
            ein
        ))
    else:
        # Separate contacts for volunteers and donors
        vol_name = (data.get('volunteer_contact_name') or '').strip() or None
        vol_email = (data.get('volunteer_contact_email') or '').strip() or None
        vol_phone = (data.get('volunteer_contact_phone') or '').strip() or None
        donor_name = (data.get('donor_contact_name') or '').strip() or None
        donor_email = (data.get('donor_contact_email') or '').strip() or None
        donor_phone = (data.get('donor_contact_phone') or '').strip() or None

        db.execute("""
            UPDATE org_claims
            SET contact_preference=?,
                volunteer_contact_name=?, volunteer_contact_email=?, volunteer_contact_phone=?,
                donor_contact_name=?, donor_contact_email=?, donor_contact_phone=?
            WHERE ein=?
        """, (
            contact_preference,
            vol_name, vol_email, vol_phone,
            donor_name, donor_email, donor_phone,
            ein
        ))

    db.commit()
    return jsonify({"status": "updated", "contact_preference": contact_preference}), 200


# ── Tier 2 privacy controls (Charter promise 9, Library Document 011) ─────────
# Everything a claimant entrusted to Daanaa is exportable and deletable by them.
# The public IRS record is not theirs to delete and remains untouched.

# Secret material never leaves the server, not even to its owner: the PIN is a
# live credential, and exporting it would turn every export into a phishing prize.
_CLAIM_SECRET_FIELDS = {'pin', 'pin_expires_at'}


def _authorize_claimant(db, ein: str, token: str):
    """Shared auth for claimant data endpoints — same contract as /api/claim/update.

    Returns (row, None) on success or (None, (response, status)) on failure.
    """
    row = db.execute('SELECT * FROM org_claims WHERE ein = ?', (ein,)).fetchone()
    if not row:
        return None, (jsonify({'error': 'No claim found for this EIN'}), 404)
    if row['claim_status'] == 'revoked':
        return None, (jsonify({'error': 'This claim has been revoked'}), 403)
    stored_pin = row['pin']
    if token != stored_pin and token != _make_verify_token(ein, stored_pin):
        return None, (jsonify({'error': 'Verification token is invalid or expired'}), 403)
    return row, None


@app.route('/api/claim/my-data', methods=['POST'])
@limiter.limit("10 per minute")
def claim_my_data_export():
    """Export every entrusted (Tier 2) field the claimant has given Daanaa."""
    data  = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('verification_token') or '').strip()[:64]
    if not ein or not token:
        return jsonify({'error': 'EIN and verification_token required'}), 400

    db = get_db()
    row, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    entrusted = {k: row[k] for k in row.keys() if k not in _CLAIM_SECRET_FIELDS}
    return jsonify({
        'ein': ein,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'entrusted_data': entrusted,
        'note': ('This is everything your organization has entrusted to Daanaa. '
                 'Public IRS data is not included; it remains public record. '
                 'You can delete all of this at any time via /api/claim/my-data/delete.'),
    })


@app.route('/api/claim/my-data/delete', methods=['POST'])
@limiter.limit("5 per minute")
def claim_my_data_delete():
    """Delete the claimant's entrusted data entirely. Public record remains."""
    data  = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('verification_token') or '').strip()[:64]
    if not ein or not token:
        return jsonify({'error': 'EIN and verification_token required'}), 400

    db = get_db()
    row, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    db.execute("DELETE FROM org_claims WHERE ein = ?", (ein,))
    db.commit()

    # Claimed overrides must vanish from public pages immediately
    stale = [k for k in _CACHE if ein in k]
    for k in stale:
        _CACHE.pop(k, None)

    # Audit that a deletion happened — never what was deleted (no PII in the log)
    _log_org_activity(ein, 'claim_data_deleted',
                      'entrusted data deleted at claimant request', actor='org')

    return jsonify({
        'success': True,
        'message': ('All data your organization entrusted to Daanaa has been deleted. '
                    'Your public IRS record remains, as it is public record. '
                    'You are welcome to claim your profile again at any time.'),
    })


@app.route('/api/claim/ai-derived', methods=['POST'])
@limiter.limit("20 per minute")
def claim_ai_derived():
    """Show a claimant exactly what was derived about their org, with provenance.

    Stewardship P9/P10 + Library Doc 005: AI-generated facts are labeled at the
    level of the individual fact, and the organization can always override them.
    The AI value stays visible next to any override — comparison, not erasure.
    """
    data  = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('verification_token') or '').strip()[:64]
    if not ein or not token:
        return jsonify({'error': 'EIN and verification_token required'}), 400

    db = get_db()
    claim, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    org = db.execute(
        """SELECT mission, mission_source, cause_tags, website, website_status,
                  donate_url, donate_confidence, donate_url_status
           FROM registry_enriched WHERE EIN = ?""", (ein,)).fetchone()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    _AI_MISSION_SOURCES = ('ai_ntee', 'ai_generated')
    mission_source = org['mission_source'] or 'unknown'
    derived = [
        {
            'field': 'mission',
            'value': org['mission'],
            'source': mission_source,
            'is_ai': mission_source in _AI_MISSION_SOURCES,
            'explanation': (
                'This summary was written by our AI from your IRS filings and category.'
                if mission_source in _AI_MISSION_SOURCES else
                'This summary came from your own public materials.'),
            'your_override': claim['custom_mission'],
            'how_to_override': 'Edit your mission in your profile editor; your words replace ours everywhere.',
        },
        {
            'field': 'cause_tags',
            'value': org['cause_tags'],
            'source': 'ai_extracted',
            'is_ai': True,
            'explanation': 'These tags were extracted by AI from your IRS category and public description.',
            'your_override': claim['cause_tags_json'] if 'cause_tags_json' in claim.keys() else None,
            'how_to_override': 'Set your own cause tags in your profile editor.',
        },
        {
            'field': 'website',
            'value': org['website'],
            'source': f"discovered ({org['website_status'] or 'unchecked'})",
            'is_ai': True,
            'explanation': 'Found by our automated discovery pipeline and verified by status checks.',
            'your_override': claim['website_url'] if 'website_url' in claim.keys() else None,
            'how_to_override': 'Confirm or correct your website in your profile editor.',
        },
        {
            'field': 'donate_url',
            'value': org['donate_url'],
            'source': f"discovered ({org['donate_url_status'] or 'unchecked'}, "
                      f"confidence {org['donate_confidence'] or 0:.0f})",
            'is_ai': True,
            'explanation': 'Found by automated search of your website; marked beta until you confirm it.',
            'your_override': claim['donate_url'] if 'donate_url' in claim.keys() else None,
            'how_to_override': 'Confirm your donation link in your profile editor to remove the beta label.',
        },
    ]
    return jsonify({
        'ein': ein,
        'derived': derived,
        'note': ('Everything here was derived from public sources or by AI, and is '
                 'labeled with where it came from. Your overrides always win, and '
                 'the derived value stays visible to you for comparison.'),
    })


def _fetch_orgs_by_eins(db, eins: list[str], active_only: bool = False) -> list[dict]:
    if not eins:
        return []
    cols = """r.EIN, r.organization_name, r.CITY, r.STATE, r.total_revenue,
              r.ntee1_percentile, r.peer_percentile, r.peer_group, r.revenue_band,
              r.latest_tax_year, r.data_source, r.updated_at"""
    placeholders = ",".join("?" * len(eins))
    # active_only=True enforces the same deductibility + revocation filter used by
    # /api/organizations so revoked orgs can't surface via vector/semantic paths.
    dedup_clause = f" AND {_DEDUCTIBILITY_FILTER}" if active_only else ""
    rows = db.execute(
        f"""SELECT {cols} FROM registry_enriched r
            WHERE r.EIN IN ({placeholders}){dedup_clause}""", eins
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
              r.latest_tax_year, r.data_source, r.updated_at"""

    # ── Vector path ────────────────────────────────────────────────────────────
    vec = _get_org_vec(ein_clean)
    if vec is not None and _emb_matrix is not None:
        top_eins = _vec_similar(vec, ein_clean, limit)
        results  = _fetch_orgs_by_eins(db, top_eins, active_only=True)
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


# ── Partner inquiries ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------
# Guild: vendor discount codes + spend tracking
# Public endpoint returns active codes for the member dashboard.
# Admin endpoints manage codes and log monthly spend reports.
# Independence rule (P7): codes are published equally; no vendor can pay for
# better placement. The market decides which vendor members use.
# ---------------------------------------------------------------------------

@app.route('/api/guild/benefits')
@limiter.limit("120 per minute")
def guild_benefits():
    """Active vendor discount codes — public; powers the member dashboard."""
    db = get_db()
    rows = db.execute(
        "SELECT id, vendor_name, category, code, description, discount_label, "
        "website_url, how_to_use, milestone_tier "
        "FROM vendor_codes WHERE is_active=1 ORDER BY category, vendor_name"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/guild/member-count')
@limiter.limit("120 per minute")
def guild_member_count():
    """Live count of verified claimed orgs — shown on ForVendors as proof of distribution."""
    try:
        db = get_db()
        row = db.execute(
            "SELECT COUNT(*) AS n FROM org_claims WHERE claim_status='verified'"
        ).fetchone()
        return jsonify({"member_count": row["n"] if row else 0})
    except Exception:
        return jsonify({"member_count": 0})


@app.route('/api/admin/guild/codes', methods=['GET'])
@require_admin_key
def admin_guild_codes_list():
    require_admin()
    db = get_db()
    rows = db.execute(
        "SELECT vc.*, "
        "  (SELECT SUM(spend_usd) FROM vendor_spend vs WHERE vs.vendor_code_id=vc.id) AS total_spend "
        "FROM vendor_codes vc ORDER BY vc.category, vc.vendor_name"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/guild/codes', methods=['POST'])
@require_admin_key
def admin_guild_codes_create():
    require_admin()
    data = request.get_json(silent=True) or {}
    required = ('vendor_name', 'category', 'code', 'description', 'discount_label')
    for f in required:
        if not (data.get(f) or '').strip():
            return jsonify({"error": f"Missing required field: {f}"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO vendor_codes (vendor_name, category, code, description, "
        "discount_label, website_url, how_to_use, milestone_tier, is_active) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            data['vendor_name'].strip()[:200],
            data['category'].strip()[:100],
            data['code'].strip()[:100],
            data['description'].strip()[:500],
            data['discount_label'].strip()[:100],
            _normalize_public_url(data.get('website_url')),
            (data.get('how_to_use') or '').strip()[:500],
            int(data.get('milestone_tier', 1)),
            1 if data.get('is_active', True) else 0,
        )
    )
    db.commit()
    row = db.execute("SELECT * FROM vendor_codes WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route('/api/admin/guild/codes/<int:code_id>', methods=['PATCH'])
@require_admin_key
def admin_guild_codes_update(code_id):
    require_admin()
    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip()
    if not reason:
        return jsonify({"error": "reason is required for audit trail (P7)"}), 400
    allowed = ('vendor_name', 'category', 'code', 'description', 'discount_label',
               'website_url', 'how_to_use', 'milestone_tier', 'is_active')
    sets, params = [], []
    for f in allowed:
        if f in data:
            sets.append(f"{f}=?")
            params.append(data[f])
    if not sets:
        return jsonify({"error": "Nothing to update"}), 400
    db = get_db()
    before = db.execute("SELECT * FROM vendor_codes WHERE id=?", (code_id,)).fetchone()
    if not before:
        return jsonify({"error": "Not found"}), 404
    before = dict(before)
    sets.append("updated_at=CURRENT_TIMESTAMP")
    params.append(code_id)
    db.execute(f"UPDATE vendor_codes SET {', '.join(sets)} WHERE id=?", params)
    # Log every changed field to the P7 audit trail
    for f in allowed:
        if f in data and str(data[f]) != str(before.get(f, '')):
            db.execute(
                "INSERT INTO vendor_code_audit (code_id, field, old_value, new_value, reason) "
                "VALUES (?,?,?,?,?)",
                (code_id, f, str(before.get(f, '')), str(data[f]), reason)
            )
    db.commit()
    row = db.execute("SELECT * FROM vendor_codes WHERE id=?", (code_id,)).fetchone()
    return jsonify(dict(row))


@app.route('/api/admin/guild/audit')
@require_admin_key
def admin_guild_audit():
    """P7 audit trail: last 100 vendor code changes."""
    require_admin()
    db = get_db()
    rows = db.execute(
        "SELECT a.*, vc.vendor_name FROM vendor_code_audit a "
        "LEFT JOIN vendor_codes vc ON vc.id=a.code_id "
        "ORDER BY a.changed_at DESC LIMIT 100"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/guild/codes/<int:code_id>/spend', methods=['POST'])
@require_admin_key
def admin_guild_spend_report(code_id):
    """Log a vendor's monthly spend report and check milestone thresholds."""
    require_admin()
    data = request.get_json(silent=True) or {}
    month   = (data.get('report_month') or '').strip()[:7]   # YYYY-MM
    spend   = float(data.get('spend_usd', 0))
    notes   = (data.get('notes') or '').strip()[:500]
    if not month or spend < 0:
        return jsonify({"error": "report_month (YYYY-MM) and spend_usd are required"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM vendor_codes WHERE id=?", (code_id,)).fetchone()
    if not row:
        return jsonify({"error": "Vendor code not found"}), 404

    prev = db.execute(
        "SELECT COALESCE(MAX(cumulative_usd), 0) AS cum FROM vendor_spend WHERE vendor_code_id=?",
        (code_id,)
    ).fetchone()['cum']
    cumulative = prev + spend

    db.execute(
        "INSERT INTO vendor_spend (vendor_code_id, report_month, spend_usd, cumulative_usd, notes) "
        "VALUES (?,?,?,?,?)",
        (code_id, month, spend, cumulative, notes)
    )
    db.commit()
    return jsonify({
        "vendor_code_id": code_id,
        "report_month": month,
        "spend_usd": spend,
        "cumulative_usd": cumulative,
        "current_tier": row['milestone_tier'],
        "note": "Update milestone_tier via PATCH /api/admin/guild/codes/<id> when threshold is reached.",
    })


@app.route('/api/guild/nominate', methods=['POST'])
@limiter.limit("10 per hour")
def guild_nominate():
    """
    Nonprofit members nominate vendors they already work with.
    Sends a warm-lead email to partners@ with the org's name as social proof,
    then stores the nomination for follow-up tracking.
    """
    data = request.get_json(silent=True) or {}
    vendor_name    = (data.get('vendor_name') or '').strip()[:200]
    category       = (data.get('category') or 'Other').strip()[:100]
    vendor_contact = (data.get('vendor_contact') or '').strip()[:254]
    nominator_org  = (data.get('nominator_org') or '').strip()[:200]
    nominator_ein  = (data.get('nominator_ein') or '').strip()[:20]
    nominator_email= (data.get('nominator_email') or '').strip()[:254]
    why            = (data.get('why') or '').strip()[:1000]

    if not vendor_name:
        return jsonify({"error": "Vendor name is required"}), 400
    if not nominator_org:
        return jsonify({"error": "Your organization name is required"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO vendor_nominations "
        "(vendor_name, category, vendor_contact, nominator_org, nominator_ein, nominator_email, why) "
        "VALUES (?,?,?,?,?,?,?)",
        (vendor_name, category, vendor_contact, nominator_org, nominator_ein, nominator_email, why)
    )
    db.commit()

    _send_daanaa_email(
        "partners@daanaa.org",
        f"[Guild nomination] {vendor_name} ({category}) — recommended by {nominator_org}",
        f"A Daanaa guild member has nominated a vendor.\n\n"
        f"Vendor:          {vendor_name}\n"
        f"Category:        {category}\n"
        f"Vendor contact:  {vendor_contact or '(not provided)'}\n\n"
        f"Nominated by:    {nominator_org}\n"
        f"EIN:             {nominator_ein or '(not provided)'}\n"
        f"Their email:     {nominator_email or '(not provided)'}\n\n"
        f"Why they recommend them:\n{why or '(not provided)'}\n",
        from_addr="Daanaa <partners@daanaa.org>",
    )
    return jsonify({"status": "received"})


@app.route('/api/guild/referral/<slug>')
@limiter.limit("120 per minute")
def guild_referral_page(slug):
    """
    Vendor referral endpoint — returns the vendor's deal info so the
    frontend can render a co-branded landing page at /guild/<slug>.
    Vendors share this URL with their nonprofit customers.
    """
    slug = slug.lower().strip()[:80]
    db = get_db()
    row = db.execute(
        "SELECT id, vendor_name, category, description, discount_label, website_url, how_to_use "
        "FROM vendor_codes WHERE referral_slug=? AND is_active=1",
        (slug,)
    ).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@app.route('/api/admin/guild/nominations', methods=['GET'])
@require_admin_key
def admin_guild_nominations():
    require_admin()
    db = get_db()
    rows = db.execute(
        "SELECT * FROM vendor_nominations ORDER BY created_at DESC LIMIT 200"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/guild/nominations/<int:nom_id>', methods=['PATCH'])
@require_admin_key
def admin_guild_nomination_update(nom_id):
    require_admin()
    data = request.get_json(silent=True) or {}
    status = (data.get('status') or '').strip()
    if status not in ('new', 'contacted', 'joined', 'declined'):
        return jsonify({"error": "status must be one of: new, contacted, joined, declined"}), 400
    db = get_db()
    db.execute("UPDATE vendor_nominations SET status=? WHERE id=?", (status, nom_id))
    db.commit()
    row = db.execute("SELECT * FROM vendor_nominations WHERE id=?", (nom_id,)).fetchone()
    return jsonify(dict(row))


@app.route('/api/guild/eligibility')
@limiter.limit("60 per minute")
def guild_eligibility():
    """
    Check whether an EIN is eligible for guild benefits.
    GET /api/guild/eligibility?ein=<ein>
    Returns {eligible: bool, reason: str}.
    Called by the member dashboard before showing the guild tab.
    """
    ein = (request.args.get('ein') or '').strip().replace('-', '')
    eligible, reason = _is_ein_guild_eligible(ein)
    return jsonify({"eligible": eligible, "reason": reason})


@app.route('/api/guild/community-partner', methods=['POST'])
@limiter.limit("10 per hour")
def guild_community_partner_apply():
    """
    Any business — local, small, regional — applies to be listed as a
    community partner. Admin reviews and activates. No CAF, no reporting.
    """
    data = request.get_json(silent=True) or {}
    required = ('business_name', 'category', 'offer', 'submitter_name', 'submitter_email')
    for f in required:
        if not (data.get(f) or '').strip():
            return jsonify({"error": f"Missing required field: {f}"}), 400
    submitter_email = (data.get('submitter_email') or '').strip()
    if '@' not in submitter_email:
        return jsonify({"error": "Invalid email"}), 400
    db = get_db()
    import json as _json
    valid_reach = {'local', 'regional', 'statewide', 'nationwide', 'multi_state', 'online'}
    area_type = (data.get('service_area_type') or 'local').strip()
    if area_type not in valid_reach:
        area_type = 'local'
    area_values_raw = data.get('service_area_values')
    if isinstance(area_values_raw, list):
        area_values = _json.dumps(area_values_raw[:50])
    else:
        area_values = '[]'

    location_country = (data.get('location_country') or '').strip()[:100]
    triage = _triage_partner_application(data)

    cur = db.execute(
        "INSERT INTO community_partners "
        "(business_name, category, offer, location_city, location_state, location_country, "
        "service_area_type, service_area_values, "
        "contact_email, contact_phone, website_url, submitter_name, submitter_email, notes, triage_notes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            data['business_name'].strip()[:200],
            data['category'].strip()[:100],
            data['offer'].strip()[:500],
            (data.get('location_city') or '').strip()[:100],
            (data.get('location_state') or '').strip()[:50],
            location_country,
            area_type,
            area_values,
            (data.get('contact_email') or '').strip()[:200],
            (data.get('contact_phone') or '').strip()[:50],
            _normalize_public_url(data.get('website_url')),
            data['submitter_name'].strip()[:200],
            submitter_email[:200],
            (data.get('notes') or '').strip()[:1000],
            triage[:1000],
        )
    )
    db.commit()

    location_display = ' '.join(filter(None, [
        (data.get('location_city') or '').strip(),
        (data.get('location_state') or '').strip(),
        location_country,
    ])) or '(not provided)'
    triage_section = f"\n─── Agent review ───\n{triage}\n────────────────────\n" if triage else ""

    _send_daanaa_email(
        submitter_email,
        f"We received your application — {data['business_name'].strip()}",
        f"Hi {data['submitter_name'].strip()},\n\n"
        f"Thanks for applying to join the Daanaa Impact Network.\n\n"
        f"We review every application manually. If your offer is a good fit for nonprofits "
        f"in our directory, we'll be in touch within a few business days.\n\n"
        f"What you submitted:\n"
        f"  Business: {data['business_name'].strip()}\n"
        f"  Category: {data['category'].strip()}\n"
        f"  Offer:    {data['offer'].strip()}\n\n"
        f"Questions? Reply to this email.\n\n"
        f"The Daanaa Team\n"
        f"  daanaa.org · partners@daanaa.org",
        from_addr="Daanaa <partners@daanaa.org>",
    )
    _send_daanaa_email(
        "partners@daanaa.org",
        f"[Community partner] {data['business_name'].strip()} applied to join the network",
        f"A business has applied to join the Daanaa Impact Network as a community partner.\n"
        f"{triage_section}\n"
        f"Business:      {data['business_name'].strip()}\n"
        f"Category:      {data['category'].strip()}\n"
        f"Offer:         {data['offer'].strip()}\n"
        f"Reach:         {area_type}\n"
        f"Location:      {location_display}\n"
        f"Website:       {(data.get('website_url') or '').strip() or '(not provided)'}\n"
        f"Contact email: {(data.get('contact_email') or '').strip() or '(not provided)'}\n"
        f"Contact phone: {(data.get('contact_phone') or '').strip() or '(not provided)'}\n"
        f"Submitter:     {data['submitter_name'].strip()} <{submitter_email}>\n"
        f"Notes:         {(data.get('notes') or '').strip() or '(none)'}\n\n"
        f"One-click approve: https://daanaa.org/api/admin/guild/approve-partner/{cur.lastrowid}?token={_make_approve_token(cur.lastrowid)}\n\n"
        f"(Or manually: PATCH /api/admin/guild/community-partners/{cur.lastrowid} {{\"is_active\": 1, \"status\": \"active\"}})",
        from_addr="Daanaa <partners@daanaa.org>",
    )
    return jsonify({"ok": True, "id": cur.lastrowid}), 201


@app.route('/api/guild/directory')
@limiter.limit("120 per minute")
def guild_directory():
    """
    Combined directory: network partners (vendor_codes) + community partners.
    Optional filters: ?category=&state= for community partners.
    Powers the member-facing vendor directory and the /for-vendors directory preview.
    """
    db = get_db()
    category = (request.args.get('category') or '').strip()
    state = (request.args.get('state') or '').strip()

    # Network partners — national/regional with shared codes
    net_q = (
        "SELECT id, vendor_name AS business_name, category, discount_label AS offer, "
        "description, website_url, how_to_use, 'network' AS partner_type, "
        "NULL AS location_city, NULL AS location_state "
        "FROM vendor_codes WHERE is_active=1"
    )
    net_params: list = []
    if category:
        net_q += " AND category=?"
        net_params.append(category)

    # Community partners — local/small, admin-activated
    com_q = (
        "SELECT id, business_name, category, offer, "
        "NULL AS description, website_url, NULL AS how_to_use, "
        "'community' AS partner_type, location_city, location_state "
        "FROM community_partners WHERE is_active=1"
    )
    com_params: list = []
    if category:
        com_q += " AND category=?"
        com_params.append(category)
    if state:
        com_q += " AND (location_state=? OR location_state IS NULL OR location_state='')"
        com_params.append(state)

    network = [dict(r) for r in db.execute(net_q, net_params).fetchall()]
    community = [dict(r) for r in db.execute(com_q, com_params).fetchall()]
    return jsonify({"network": network, "community": community})


@app.route('/api/impact')
@limiter.limit("60 per minute")
def impact_stats():
    """
    Public impact scorecard for the Daanaa impact network.
    Cached 1 hour — these numbers move slowly.
    """
    cache_key = _ck("impact", "stats")
    cached = _cget(cache_key, "stats")
    if cached:
        return jsonify(cached)

    db = get_db()

    orgs_indexed = db.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked=0 AND org_status='active'"
    ).fetchone()[0]

    orgs_claimed = db.execute(
        "SELECT COUNT(DISTINCT ein) FROM org_claims WHERE claim_status='verified' AND revoked_at IS NULL"
    ).fetchone()[0]

    states_row = db.execute(
        "SELECT COUNT(DISTINCT state) FROM registry_enriched WHERE irs_revoked=0 AND state IS NOT NULL"
    ).fetchone()
    states_covered = states_row[0] if states_row else 0

    ntee_row = db.execute(
        "SELECT COUNT(DISTINCT nteecc) FROM registry_enriched WHERE irs_revoked=0 AND nteecc IS NOT NULL"
    ).fetchone()
    ntee_categories = ntee_row[0] if ntee_row else 0

    network_partners = db.execute(
        "SELECT COUNT(*) FROM vendor_codes WHERE is_active=1"
    ).fetchone()[0]

    community_partners = db.execute(
        "SELECT COUNT(*) FROM community_partners WHERE is_active=1"
    ).fetchone()[0]

    # States covered by community partners
    cp_states = db.execute(
        "SELECT COUNT(DISTINCT location_state) FROM community_partners "
        "WHERE is_active=1 AND location_state IS NOT NULL AND location_state != ''"
    ).fetchone()[0]

    result = {
        "orgs_indexed": orgs_indexed,
        "orgs_claimed": orgs_claimed,
        "states_covered": states_covered,
        "ntee_categories": ntee_categories,
        "network_partners": network_partners,
        "community_partners": community_partners,
        "community_partner_states": cp_states,
        "total_partners": network_partners + community_partners,
    }
    _cset(cache_key, result)
    return jsonify(result)


@app.route('/api/impact/summary', methods=['GET'])
@limiter.limit("60 per minute")
def impact_summary():
    """
    Per-org or period-based impact summary: donations, volunteer hours, and
    community contribution metrics. Used by the ImpactWidget on org profile pages.

    Query params:
    - period: 'day' | 'month' (default) | 'year' | 'all'
    - org_ein: (optional) specific org, if omitted returns platform totals
    """
    period = request.args.get('period', 'month').lower()
    org_ein = request.args.get('org_ein', '').strip()

    if period not in ('day', 'month', 'year', 'all'):
        period = 'month'

    # Determine time window (for per-org summaries in future; currently returns zeros)
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    if period == 'day':
        start_date = (now - timedelta(days=1)).isoformat()
    elif period == 'month':
        start_date = (now - timedelta(days=30)).isoformat()
    elif period == 'year':
        start_date = (now - timedelta(days=365)).isoformat()
    else:
        start_date = None

    db = get_db()

    # Query funding history from wallet/claims system (currently placeholder)
    # In production, this would aggregate from org_claims, wallet records, etc.
    # For now, return the structure with zeros until backend logging is implemented
    donation_data = {
        'donation_attributed': 0,
        'donation_count': 0,
        'volunteer_hours': 0,
        'volunteer_reports': 0,
        'volunteer_value': 0,
        'partnership_savings': 0,
        'unique_orgs': 0 if org_ein else 0,
        'last_updated': now.isoformat(),
        'period': period,
    }

    return jsonify(donation_data)


def admin_community_partners_list():
    require_admin()
    db = get_db()
    rows = db.execute(
        "SELECT * FROM community_partners ORDER BY created_at DESC LIMIT 500"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/guild/partners-review', methods=['GET'])
@require_admin_key
def admin_partners_review():
    """
    View all pending and rejected partners for follow-up and coaching.
    Use this to identify patterns, reach out to improve applications, and help partners succeed.
    """
    require_admin()
    db = get_db()
    status = request.args.get('status', '').strip()  # 'pending' or 'rejected'

    query = "SELECT * FROM community_partners WHERE is_active=0"
    params = []

    if status in ('pending', 'rejected'):
        query += " AND status=?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT 200"

    rows = db.execute(query, params).fetchall()

    # Summary stats
    total_pending = db.execute(
        "SELECT COUNT(*) FROM community_partners WHERE is_active=0 AND status='pending'"
    ).fetchone()[0]
    total_rejected = db.execute(
        "SELECT COUNT(*) FROM community_partners WHERE is_active=0 AND status='rejected'"
    ).fetchone()[0]
    total_active = db.execute(
        "SELECT COUNT(*) FROM community_partners WHERE is_active=1"
    ).fetchone()[0]

    return jsonify({
        'stats': {
            'pending': total_pending,
            'rejected': total_rejected,
            'active': total_active,
        },
        'partners': [dict(r) for r in rows],
    })


@app.route('/api/admin/guild/community-partners/<int:cp_id>', methods=['PATCH'])
@require_admin_key
def admin_community_partner_update(cp_id):
    require_admin()
    data = request.get_json(silent=True) or {}
    sets, params = [], []
    allowed = ('status', 'is_active', 'business_name', 'category', 'offer',
               'location_city', 'location_state', 'contact_email', 'contact_phone',
               'website_url', 'notes')
    for field in allowed:
        if field in data:
            sets.append(f"{field}=?")
            params.append(data[field])
    if not sets:
        return jsonify({"error": "No fields to update"}), 400
    params.append(cp_id)
    db = get_db()
    db.execute(f"UPDATE community_partners SET {', '.join(sets)} WHERE id=?", params)
    db.commit()
    row = db.execute("SELECT * FROM community_partners WHERE id=?", (cp_id,)).fetchone()
    return jsonify(dict(row))


@app.route('/api/admin/guild/approve-partner/<int:cp_id>', methods=['GET'])
@require_admin_key
def admin_community_partner_approve(cp_id):
    """
    One-click approve link sent in the notification email.
    Validates a signed token so no admin header is required — works directly from inbox.
    GET /api/admin/guild/approve-partner/<id>?token=<hmac>
    """
    provided = request.args.get('token', '')
    expected = _make_approve_token(cp_id)
    if not provided or not hmac.compare_digest(provided, expected):
        abort(401)
    db = get_db()
    row = db.execute("SELECT * FROM community_partners WHERE id=?", (cp_id,)).fetchone()
    if not row:
        abort(404)
    if row['is_active']:
        return (
            "<html><body style='font-family:sans-serif;padding:2rem'>"
            f"<h2>Already active</h2><p>{row['business_name']} is already in the network.</p>"
            "</body></html>", 200
        )
    db.execute(
        "UPDATE community_partners SET is_active=1, status='active' WHERE id=?", (cp_id,)
    )
    db.commit()
    _send_daanaa_email(
        row['submitter_email'],
        f"Welcome to the Daanaa Impact Network — {row['business_name']}",
        f"Hi {row['submitter_name']},\n\n"
        f"Your business has been approved and is now listed in the Daanaa Impact Network.\n\n"
        f"Business: {row['business_name']}\n"
        f"Category: {row['category']}\n"
        f"Offer: {row['offer']}\n\n"
        f"Nonprofits in your area will be able to see your offer when they visit the Daanaa network directory.\n\n"
        f"Thank you for supporting the nonprofit community.\n\n"
        f"The Daanaa Team\n"
        f"  daanaa.org · partners@daanaa.org",
        from_addr="Daanaa <partners@daanaa.org>",
    )
    return (
        "<html><body style='font-family:sans-serif;padding:2rem;max-width:480px;margin:auto'>"
        f"<h2 style='color:#1a3a5c'>Approved!</h2>"
        f"<p><strong>{row['business_name']}</strong> is now active in the Daanaa Impact Network.</p>"
        f"<p>A welcome email has been sent to {row['submitter_email']}.</p>"
        "</body></html>", 200
    )


# ---------------------------------------------------------------------------
# Partner / vendor inquiry (existing — vendors and payment processors)
# ---------------------------------------------------------------------------

# Vendors, payment processors, and foundations reach us via /partners. The
# inquiry is mail, not data: nothing is stored server side, it routes to the
# partners@ alias and we reply by hand. Independence rule (STEWARDSHIP.md P7):
# nothing about this path may ever touch scores, rankings, or visibility.

_PARTNER_TYPES = {
    "Payment processing", "Services for nonprofits",
    "Community foundation or network", "Other",
    # Guild vendor categories (from /for-vendors page)
    "Insurance", "Printing and marketing", "Travel and fuel",
    "Food and catering", "Software and technology", "Office supplies and shipping",
}


@app.route('/api/partner/contact', methods=['POST'])
@limiter.limit("5 per hour")
def partner_contact():
    data = request.get_json(silent=True) or {}
    org_name = (data.get('org_name') or '').strip()[:200]
    name     = (data.get('name') or '').strip()[:120]
    email    = (data.get('email') or '').strip()[:254]
    ptype    = (data.get('partner_type') or 'Other').strip()
    message  = (data.get('message') or '').strip()
    source   = (data.get('source') or 'partners').strip()[:40]

    if not name:
        return jsonify({"error": "Please tell us your name"}), 400
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({"error": "A valid email is required so we can reply"}), 400
    if not message:
        return jsonify({"error": "Please include a short message"}), 400
    if len(message) > 5000:
        return jsonify({"error": "Please keep the message under 5000 characters"}), 400
    if ptype not in _PARTNER_TYPES:
        ptype = "Other"

    page_label = "vendor guild (/for-vendors)" if source == "vendor_guild" else "partners (/partners)"
    _send_daanaa_email(
        "partners@daanaa.org",
        f"[{'Vendor guild' if source == 'vendor_guild' else 'Partner'} inquiry] {org_name or name} ({ptype})",
        f"New inquiry from daanaa.org — source: {page_label}\n\n"
        f"Organization: {org_name or '(not given)'}\n"
        f"Name:         {name}\n"
        f"Email:        {email}\n"
        f"Type:         {ptype}\n\n"
        f"Message:\n{message}\n",
        from_addr="Daanaa <partners@daanaa.org>",
    )
    return jsonify({"status": "received"})


@app.route('/api/organizations/<ein>/similar')
@limiter.limit("60 per minute")
def get_similar_organizations(ein):
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    try:
        limit = _int_arg('limit', 6, hi=12)
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


# ── Typo tolerance helper (T12 Phase 2) ────────────────────────────────────────
def _typo_tolerance_search(query: str, db) -> list[str]:
    """Fuzzy-match query against org names when FTS returns zero results.

    Used as a fallback when keyword search fails (likely due to typos).
    Returns EINs of the best fuzzy matches (up to 5).

    Example: "aniaml rescue" → "Animal Rescue" orgs via difflib similarity.
    """
    try:
        # Fetch all org names (cached in memory on first call)
        if not hasattr(_typo_tolerance_search, '_org_names_cache'):
            rows = db.execute("SELECT EIN, organization_name FROM registry_enriched WHERE organization_name IS NOT NULL").fetchall()
            _typo_tolerance_search._org_names_cache = {dict(r)['organization_name']: dict(r)['EIN'] for r in rows}

        org_names = list(_typo_tolerance_search._org_names_cache.keys())

        # Get close matches (cutoff=0.50 = 50% similarity, aggressive for typo tolerance)
        # Returns up to 10 candidates to maximize recall
        matches = get_close_matches(query, org_names, n=10, cutoff=0.50)
        if matches:
            return [_typo_tolerance_search._org_names_cache[name] for name in matches[:5]]
    except Exception as e:
        app.logger.debug(f"typo_tolerance_search error: {e}")

    return []


# ── Semantic search ────────────────────────────────────────────────────────────
@app.route('/api/search/semantic')
@limiter.limit("30 per minute")
def semantic_search():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({"error": "q param required"}), 400
    try:
        limit = _int_arg('limit', 10, hi=25)
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
    results  = [_strip_scores(r) for r in _fetch_orgs_by_eins(db, top_eins, active_only=True)]
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

    # ── Zip code intercept ────────────────────────────────────────────────────
    # Detect a 5-digit zip anywhere in the query ("97701", "food bank 97701",
    # "Bend OR 97701"). Resolve it to city+state via zip_codes table, substitute
    # the city name into the FTS query, and surface a "zip_resolved" banner in
    # the UI ("Showing results near Bend, OR").
    zip_meta: dict | None = None
    area_eins: list[str] = []
    q, detected_zip = _extract_zip(q)
    if detected_zip:
        db_zip = get_db()
        zrow = db_zip.execute("SELECT * FROM zip_codes WHERE zip=?", (detected_zip,)).fetchone()
        if zrow:
            zrow = dict(zrow)
            zip_meta = zrow
            # Replace zip with city name so FTS finds orgs in that city.
            # For bare zip ("97701") q is empty — set q to city.
            # For mixed query ("food bank 97701") q has keywords — append city.
            city = zrow.get('city', '')
            if city:
                q = f"{q} {city}".strip() if q and city.lower() not in q.lower() else (q or city)
        elif not q:
            q = detected_zip   # unknown zip, no city: use raw digits as FTS fallback
            state = zrow.get('state_id', '')
            county = zrow.get('county_name', '')
            # Find orgs whose service area includes this state or county
            if state:
                try:
                    sa_rows = db_zip.execute(
                        "SELECT ein FROM org_service_areas WHERE "
                        "area_type='nationwide' OR "
                        "(area_type='statewide' AND area_values LIKE ?) OR "
                        "(area_type IN ('county','local') AND area_values LIKE ?)",
                        (f'%"{state}"%', f'%"{county}%"')
                    ).fetchall()
                    area_eins = [r[0] for r in sa_rows]
                except sqlite3.OperationalError:
                    area_eins = []

    ck = _ck('fused', q, zip_meta['zip'] if zip_meta else '')
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

    # ── Path 1b: Semantic reranking of FTS results (T12 Phase 4) ──────────────
    # If FTS returned results, optionally rerank by semantic similarity for better
    # relevance (e.g., "food assistance" ranks above generic "nonprofit" matches)
    if kw_eins and len(kw_eins) >= 5:  # Only rerank if we have meaningful FTS results
        if not _emb_loaded:
            _load_embeddings()
        if _emb_matrix is not None and len(_emb_matrix) > 0:
            vec = _embed_query(q)
            if vec is not None:
                # Rerank FTS results by semantic similarity to query
                from numpy import dot
                from numpy.linalg import norm
                kw_sim_scores = {}
                # Row lookup MUST go through _emb_index (EIN → matrix row).
                # The old code did int(ein) as a row index: EINs are 9-digit
                # tax IDs, so nearly all fell outside the matrix (rerank was
                # a silent no-op) and leading-zero EINs read a DIFFERENT
                # org's vector (fixed 2026-07-18).
                for ein in kw_eins:
                    row_i = _emb_index.get(ein) if _emb_index else None
                    if row_i is not None:
                        org_vec = _emb_matrix[row_i]
                        # Cosine similarity: dot / (norm1 * norm2)
                        sim = dot(vec, org_vec) / (norm(vec) * norm(org_vec) + 1e-9)
                        kw_sim_scores[ein] = sim
                # Re-sort kw_eins by semantic similarity (descending)
                if kw_sim_scores:
                    kw_eins_reranked = sorted(kw_eins, key=lambda e: kw_sim_scores.get(e, -1), reverse=True)
                    app.logger.info(f"semantic_reranking: q='{q}' reranked {len(kw_sim_scores)}/{len(kw_eins)} FTS results")
                    kw_eins = kw_eins_reranked

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

    # Exact-name pin: a donor who types an org's name (or a distinctive part
    # of it) must see that org first, not a bm25/semantic neighbor. Phrase
    # match on the name column; +1.0 dominates any RRF sum (max ≈ 0.033).
    name_words = _FTS5_STRIP.sub(' ', _FTS5_APOS.sub('', q)).split()
    if name_words and _check_fts(db):
        phrase = ' '.join(name_words[:12])
        try:
            for r in db.execute(
                'SELECT ein FROM org_fts WHERE org_fts MATCH ? LIMIT 25',
                (f'org_name : "{phrase}"',)
            ).fetchall():
                rrf[r[0]] = rrf.get(r[0], 0.0) + 1.0
        except sqlite3.OperationalError:
            pass

    fused_eins = sorted(rrf, key=lambda e: rrf[e], reverse=True)

    # ── Inject zip-area matches at the top of results ─────────────────────────
    if zip_meta and area_eins:
        # Orgs that self-report serving this area get a strong synthetic score
        area_set = set(area_eins)
        for ein in area_eins:
            if ein not in rrf:
                rrf[ein] = 0.04   # Below surge boosts (0.05) but above normal RRF
        # Re-sort to pull area matches forward without discarding keyword/semantic matches
        fused_eins = sorted(rrf, key=lambda e: rrf[e], reverse=True)

    # ── Apply surge boosts (event-driven: add relevant orgs even if not in keyword/semantic) ─────────────
    # Check if there are active boosts for this query's detected event.
    # The surge tables exist only after agent_surge_monitor.py has run — search
    # must work without them (this 500'd every fused search when they were absent).
    try:
        active_boosts = db.execute("""
            SELECT DISTINCT b.ein, b.relevance_score, s.event_type
            FROM surge_boosts b
            JOIN surge_detections s ON b.surge_id = s.id
            WHERE b.status = 'active'
              AND b.expires_at > datetime('now')
              AND (? LIKE '%' || s.query || '%' OR s.query LIKE '%' || ? || '%')
        """, (q, q)).fetchall()
    except sqlite3.OperationalError:
        active_boosts = []

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

    # ── Typo tolerance fallback (T12 Phase 2) ──────────────────────────────────
    # If FTS + semantic returned too few results, try fuzzy matching on org names
    # to catch typos and abbreviations that FTS might miss
    if len(fused_eins) < 5:
        typo_eins = _typo_tolerance_search(q, db)
        if typo_eins:
            # Blend: preserve high-scoring FTS results, add fuzzy matches for coverage
            existing_set = set(fused_eins)
            for ein in typo_eins:
                if ein not in existing_set:
                    fused_eins.append(ein)
                    if len(fused_eins) >= RESULT_N:
                        break
            if typo_eins:
                app.logger.info(f"typo_tolerance: q='{q}' kw={len(kw_eins)} + fuzzy={len(typo_eins)} -> {len(fused_eins)} total")

    # ── NTEE synonym expansion (T12 Phase 3) ───────────────────────────────────
    # If still too few results, expand query with nonprofit category synonyms
    # (e.g., "animal rescue" → also search "animal shelter", "pet adoption", etc.)
    if len(fused_eins) < 5:
        synonyms = expand_query_with_synonyms(q)
        if len(synonyms) > 1:  # More than just the original query
            existing_set = set(fused_eins)
            syn_eins = []
            for syn_q in synonyms[1:]:  # Skip the first (original query)
                if len(fused_eins) >= RESULT_N:
                    break
                try:
                    fts_q = _sanitize_fts_query(syn_q)
                    rows = db.execute(
                        "SELECT ein FROM org_fts WHERE org_fts MATCH ? "
                        "ORDER BY bm25(org_fts, 10, 5, 1, 1) LIMIT ?",
                        (fts_q, CAND_N)
                    ).fetchall()
                    for r in rows:
                        ein = r[0]
                        if ein not in existing_set:
                            fused_eins.append(ein)
                            syn_eins.append(ein)
                            if len(fused_eins) >= RESULT_N:
                                break
                except Exception:
                    pass
            if syn_eins:
                app.logger.info(f"synonym_expansion: q='{q}' synonyms={synonyms[1:]} added={len(syn_eins)} -> {len(fused_eins)} total")

    # ── Fetch org details (deductible 501c3s only) ────────────────────────────
    fetch_n = min(RESULT_N * 3, len(fused_eins))
    if not fused_eins:
        return jsonify({"results": [], "query": q, "mode": "fused", "total": 0})

    placeholders = ",".join("?" * fetch_n)
    # v4 JOIN removed 2026-07-10: same schema-drift bug as get_organization()
    # (v4_scores is now 5 columns: EIN, score, tier, band, operating_model --
    # peer_cell_size never existed). This 500'd /api/search on every query.
    # The joined columns fed _attach_v4_scores(), a documented no-op, and
    # weren't referenced anywhere downstream in this function.
    cols = """r.EIN, r.organization_name, r.NTEE1, r.CITY, r.STATE, r.total_revenue,
              r.ntee1_percentile, r.peer_percentile, r.peer_group, r.revenue_band,
              r.latest_tax_year, r.data_source, r.merit_tier, r.merit_score, r.merit_band,
              CASE WHEN r.months_of_reserve BETWEEN -120 AND 120
                   THEN r.months_of_reserve ELSE NULL END as months_of_reserve,
              r.net_assets, r.is_hidden_gem, r.cause_tags,
              SUBSTR(r.mission, 1, 300) as mission, r.mission_source,
              (r.mission IS NOT NULL AND r.mission != '') as has_mission,
              (r.website  IS NOT NULL AND r.website  != '') as has_website"""
    rows = db.execute(
        f"""SELECT {cols} FROM registry_enriched r
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
    out: dict = {"results": results, "query": q, "mode": mode, "total": len(results)}
    if zip_meta:
        out["zip_resolved"] = {
            "zip": zip_meta["zip"],
            "city": zip_meta.get("city"),
            "state": zip_meta.get("state_id"),
            "county": zip_meta.get("county_name"),
        }
    _cset(ck, out)
    return jsonify(out)


# ── Zip code lookup ────────────────────────────────────────────────────────

@app.route('/api/zip/<zip_code>')
@limiter.limit("120 per minute")
def zip_lookup(zip_code: str):
    """
    GET /api/zip/60614  → {zip, city, state_id, county_name, lat, lon}
    Powers frontend zip-code typeahead and search routing.
    Returns 404 if zip is not in the reference table (run import_zip_codes.py first).
    """
    z = zip_code.strip()
    if not z.isdigit() or len(z) != 5:
        return jsonify({"error": "Invalid zip code"}), 400
    db = get_db()
    row = db.execute("SELECT * FROM zip_codes WHERE zip=?", (z,)).fetchone()
    if not row:
        return jsonify({"error": "Zip code not found"}), 404
    return jsonify(dict(row))


# ── Service area endpoints ──────────────────────────────────────────────────

@app.route('/api/org/<ein>/service-area', methods=['GET'])
@limiter.limit("120 per minute")
def org_service_area_get(ein: str):
    """Return an org's self-reported service area. Public."""
    clean = ein.replace('-', '').strip()
    db = get_db()
    row = db.execute(
        "SELECT area_type, area_values, updated_at FROM org_service_areas WHERE ein=?",
        (clean,)
    ).fetchone()
    if not row:
        return jsonify({"area_type": None, "area_values": [], "updated_at": None})
    d = dict(row)
    try:
        d['area_values'] = json.loads(d['area_values'])
    except (json.JSONDecodeError, TypeError):
        d['area_values'] = []
    return jsonify(d)


@app.route('/api/org/<ein>/service-area', methods=['PUT'])
@limiter.limit("30 per hour")
def org_service_area_put(ein: str):
    """
    Orgs set their self-reported reach level after claiming their page.
    area_type: local | regional | statewide | nationwide | international
    area_values:
      regional    → ["Cook County, IL", "DuPage County, IL"] (free-text, ≤10 items)
      statewide   → ["IL", "WI"]  (US state abbreviations, ≤50)
      international → ["KE", "UG", "TZ"]  (ISO 3166-1 alpha-2, ≤50)
      local / nationwide → [] (empty — donor sees city from IRS address or "nationwide")
    Auth: verification_token (claim flow) OR admin key.
    """
    clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not clean:
        return jsonify({"error": "Invalid EIN"}), 400
    data  = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    db = get_db()

    # Auth: claim token OR admin key
    if token:
        if not _verify_claim_token(clean, token):
            return jsonify({"error": "Invalid verification token"}), 403
    else:
        try:
            require_admin()
        except Exception:
            return jsonify({"error": "verification_token or admin key required"}), 403

    valid_types = {'local', 'regional', 'statewide', 'nationwide', 'international'}
    area_type = (data.get('area_type') or 'local').strip()
    if area_type not in valid_types:
        return jsonify({"error": f"area_type must be one of {sorted(valid_types)}"}), 400

    area_values = data.get('area_values', [])
    if not isinstance(area_values, list):
        return jsonify({"error": "area_values must be a list"}), 400

    # Sanitise and cap per type
    max_items = {'regional': 10, 'statewide': 50, 'international': 50}.get(area_type, 0)
    area_values = [str(v).strip()[:100] for v in area_values if str(v).strip()][:max_items]

    db.execute("""
        INSERT INTO org_service_areas (ein, area_type, area_values, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(ein) DO UPDATE SET
            area_type=excluded.area_type,
            area_values=excluded.area_values,
            updated_at=excluded.updated_at
    """, (clean, area_type, json.dumps(area_values)))
    db.commit()
    return jsonify({"ok": True, "ein": clean, "area_type": area_type, "area_values": area_values})


# ── Volunteer events ───────────────────────────────────────────────────────

def _verify_claim_token(ein: str, token: str) -> bool:
    """Return True if token is a valid verification token for a non-revoked claim."""
    db = get_db()
    row = db.execute("SELECT pin, claim_status FROM org_claims WHERE ein=?", (ein,)).fetchone()
    if not row or row["claim_status"] == "revoked":
        return False
    stored_pin = row["pin"]
    return token == stored_pin or token == _make_verify_token(ein, stored_pin)


def _format_event(row, signup_count: int = 0) -> dict:
    keys = row.keys() if hasattr(row, 'keys') else []
    return {
        "id":             row["id"],
        "ein":            row["ein"],
        "title":          row["title"],
        "description":    row["description"],
        "event_date":     row["event_date"],
        "start_time":     row["start_time"],
        "end_time":       row["end_time"],
        "location_city":  row["location_city"],
        "location_state": row["location_state"],
        "location_zip":   row["location_zip"],
        "is_virtual":     bool(row["is_virtual"]),
        "signup_url":     row["signup_url"],
        "contact_email":  row["contact_email"],
        "capacity":       row["capacity"],
        "status":         row["status"],
        "created_at":     row["created_at"],
        "updated_at":     row["updated_at"],
        # New fields (graceful fallback for rows created before migration)
        "event_type":     row["event_type"] if "event_type" in keys else "volunteer",
        "short_id":       row["short_id"]   if "short_id"   in keys else None,
        "min_age":        row["min_age"]    if "min_age"     in keys else None,
        "expected_hours": row["expected_hours"] if "expected_hours" in keys else None,
        "skill_level":      row["skill_level"]      if "skill_level"      in keys else "any",
        "what_to_bring":    row["what_to_bring"]    if "what_to_bring"    in keys else None,
        "waiver_url":       row["waiver_url"]       if "waiver_url"       in keys else None,
        "parking_info":     row["parking_info"]     if "parking_info"     in keys else None,
        "coordinator_name": row["coordinator_name"] if "coordinator_name" in keys else None,
        "signup_count":     signup_count,
        "source_url":       row["source_url"] if "source_url" in keys else None,
        "source_checked_at": row["source_checked_at"] if "source_checked_at" in keys else None,
        "discovery_status": row["discovery_status"] if "discovery_status" in keys else "confirmed",
        "ai_generated":     bool(row["ai_generated"]) if "ai_generated" in keys else False,
    }


@app.route('/api/volunteer-events', methods=['GET'])
@limiter.limit("120 per minute")
def volunteer_events_search():
    """Public search for events by location/date/cause/type. No auth required."""
    db = get_db()
    zip_code    = (request.args.get('zip')        or '').strip()[:10]
    city        = (request.args.get('city')       or '').strip()[:100]
    state       = (request.args.get('state')      or '').strip()[:2].upper()
    date_from   = (request.args.get('date_from')  or '').strip()[:10]
    date_to     = (request.args.get('date_to')    or '').strip()[:10]
    ntee        = (request.args.get('ntee')       or '').strip()[:1].upper()
    event_type  = (request.args.get('event_type') or '').strip()[:20]
    virtual     = request.args.get('virtual') in ('1', 'true')
    limit_val   = _int_arg('limit',  50, hi=100)
    offset_val  = _int_arg('offset',  0, hi=10_000_000)

    valid_event_types = {'volunteer', 'community', 'fundraiser', 'networking'}
    if event_type not in valid_event_types:
        event_type = ''

    where, params = ["ve.status='active'", "ve.event_date >= date('now')", "COALESCE(r.irs_revoked,0) != 1", "COALESCE(r.org_status,'') != 'revoked'"], []
    if zip_code:
        where.append("ve.location_zip=?"); params.append(zip_code)
    elif city and state:
        where.append("lower(ve.location_city)=lower(?) AND ve.location_state=?")
        params += [city, state]
    elif state:
        where.append("ve.location_state=?"); params.append(state)
    if virtual:
        where.append("ve.is_virtual=1")
    if date_from:
        where.append("ve.event_date >= ?"); params.append(date_from)
    if date_to:
        where.append("ve.event_date <= ?"); params.append(date_to)
    if ntee:
        where.append("r.ntee1=?"); params.append(ntee)
    if event_type:
        where.append("ve.event_type=?"); params.append(event_type)
    sql = (
        "SELECT ve.*, r.organization_name AS org_name, r.mission AS org_mission, "
        "(SELECT COALESCE(SUM(total_count),0) FROM org_signups "
        " WHERE event_id=ve.id AND status='confirmed') AS signup_count "
        "FROM volunteer_events ve "
        "LEFT JOIN registry_enriched r ON ve.ein=r.EIN "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY ve.event_date ASC, ve.start_time ASC "
        "LIMIT ? OFFSET ?"
    )
    rows = db.execute(sql, params + [limit_val, offset_val]).fetchall()
    events = []
    for row in rows:
        e = _format_event(row, signup_count=row["signup_count"])
        e["organization_name"] = row["org_name"]
        e["org_mission"]       = row["org_mission"]
        events.append(e)
    return jsonify({"events": events, "count": len(events)})


@app.route('/api/org/<ein>/volunteer-events', methods=['GET'])
@limiter.limit("120 per minute")
def org_volunteer_events_list(ein: str):
    """Public: all active/upcoming events for a given org."""
    clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not clean:
        return jsonify({"events": []})
    db = get_db()
    include_past = request.args.get('all') == '1'
    if include_past:
        rows = db.execute(
            "SELECT * FROM volunteer_events WHERE ein=? AND status != 'cancelled' "
            "ORDER BY event_date DESC LIMIT 50", (clean,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM volunteer_events WHERE ein=? AND status='active' "
            "AND event_date >= date('now') ORDER BY event_date ASC LIMIT 20", (clean,)
        ).fetchall()
    return jsonify({"events": [_format_event(r) for r in rows]})


@app.route('/api/org/<ein>/volunteer-events', methods=['POST'])
@limiter.limit("20 per minute")
def org_volunteer_events_create(ein: str):
    """Create a volunteer event. Requires valid verification_token for this EIN."""
    clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not clean:
        return jsonify({"error": "Invalid EIN"}), 400

    data  = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]
    if not token or not _verify_claim_token(clean, token):
        return jsonify({"error": "Invalid or missing verification token"}), 403

    title      = (data.get('title')       or '').strip()[:200]
    event_date = (data.get('event_date')  or '').strip()[:10]
    if not title or not event_date:
        return jsonify({"error": "title and event_date are required"}), 400

    import re
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', event_date):
        return jsonify({"error": "event_date must be YYYY-MM-DD"}), 400

    description    = (data.get('description')    or '').strip()[:1000]
    start_time     = (data.get('start_time')     or '').strip()[:5] or None
    end_time       = (data.get('end_time')       or '').strip()[:5] or None
    location_city  = (data.get('location_city')  or '').strip()[:100] or None
    location_state = (data.get('location_state') or '').strip()[:2].upper() or None
    location_zip   = (data.get('location_zip')   or '').strip()[:10] or None
    is_virtual     = bool(data.get('is_virtual', False))
    signup_url     = (data.get('signup_url')     or '').strip()[:500] or None
    contact_email  = (data.get('contact_email')  or '').strip()[:200] or None
    capacity       = data.get('capacity')
    if capacity is not None:
        try:
            capacity = max(1, int(capacity))
        except (ValueError, TypeError):
            capacity = None
    valid_skill_levels = {'any', 'beginner', 'intermediate', 'skilled'}
    skill_level    = (data.get('skill_level') or 'any').strip()[:20]
    if skill_level not in valid_skill_levels:
        skill_level = 'any'
    what_to_bring    = (data.get('what_to_bring')    or '').strip()[:500] or None
    waiver_url       = (data.get('waiver_url')       or '').strip()[:500] or None
    parking_info     = (data.get('parking_info')     or '').strip()[:300] or None
    coordinator_name = (data.get('coordinator_name') or '').strip()[:200] or None

    if signup_url and not signup_url.startswith(('http://', 'https://')):
        signup_url = None
    if waiver_url and not waiver_url.startswith(('http://', 'https://')):
        waiver_url = None

    db = get_db()
    cur = db.execute("""
        INSERT INTO volunteer_events
            (ein, title, description, event_date, start_time, end_time,
             location_city, location_state, location_zip, is_virtual,
             signup_url, contact_email, capacity, status,
             skill_level, what_to_bring, waiver_url, parking_info, coordinator_name)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'active',?,?,?,?,?)
    """, (clean, title, description or None, event_date, start_time, end_time,
          location_city, location_state, location_zip, int(is_virtual),
          signup_url, contact_email, capacity,
          skill_level, what_to_bring, waiver_url, parking_info, coordinator_name))
    db.commit()
    event_id = cur.lastrowid
    row = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    return jsonify(_format_event(row)), 201


@app.route('/api/volunteer-events/<int:event_id>', methods=['PATCH'])
@limiter.limit("30 per minute")
def volunteer_event_update(event_id: int):
    """Update a volunteer event. Requires verification_token matching the event's EIN."""
    data  = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    db  = get_db()
    row = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return jsonify({"error": "Event not found"}), 404
    if not token or not _verify_claim_token(row["ein"], token):
        return jsonify({"error": "Invalid or missing verification token"}), 403
    if row["status"] == "expired":
        return jsonify({"error": "Cannot update an expired event"}), 400

    allowed = {"title", "description", "event_date", "start_time", "end_time",
               "location_city", "location_state", "location_zip", "is_virtual",
               "signup_url", "contact_email", "capacity", "status",
               "skill_level", "what_to_bring", "waiver_url", "parking_info",
               "coordinator_name"}
    valid_statuses = {"active", "filled", "cancelled"}
    valid_skill_levels = {"any", "beginner", "intermediate", "skilled"}
    updates, vals = [], []
    for field in allowed:
        if field not in data:
            continue
        val = data[field]
        if field == "status":
            if val not in valid_statuses:
                return jsonify({"error": f"status must be one of {valid_statuses}"}), 400
        if field == "skill_level":
            if val not in valid_skill_levels:
                val = "any"
        if field == "is_virtual":
            val = int(bool(val))
        if field in ("signup_url", "waiver_url") and val and not str(val).startswith(('http://', 'https://')):
            continue
        updates.append(f"{field}=?"); vals.append(val)

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    updates.append("updated_at=CURRENT_TIMESTAMP")
    db.execute(f"UPDATE volunteer_events SET {', '.join(updates)} WHERE id=?", vals + [event_id])
    db.commit()
    row = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    return jsonify(_format_event(row))


@app.route('/api/volunteer-events/<int:event_id>', methods=['DELETE'])
@limiter.limit("20 per minute")
def volunteer_event_delete(event_id: int):
    """Cancel a volunteer event. Requires verification_token matching the event's EIN."""
    data  = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    db  = get_db()
    row = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return jsonify({"error": "Event not found"}), 404
    if not token or not _verify_claim_token(row["ein"], token):
        return jsonify({"error": "Invalid or missing verification token"}), 403

    db.execute(
        "UPDATE volunteer_events SET status='cancelled', updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (event_id,)
    )
    db.commit()
    return jsonify({"ok": True, "id": event_id, "status": "cancelled"})


# ── Events: public discovery & detail ─────────────────────────────────────

def _event_signup_count(db, event_id: int) -> int:
    row = db.execute(
        "SELECT COALESCE(SUM(total_count),0) AS n FROM org_signups WHERE event_id=? AND status='confirmed'",
        (event_id,),
    ).fetchone()
    return row["n"] if row else 0


@app.route('/api/events/<int:event_id>', methods=['GET'])
@limiter.limit("120 per minute")
def event_detail(event_id: int):
    """Public single-event detail with signup count (no attendee names)."""
    db = get_db()
    row = db.execute(
        "SELECT ve.*, r.organization_name AS org_name, r.mission AS org_mission, "
        "r.ntee1 AS org_ntee "
        "FROM volunteer_events ve "
        "LEFT JOIN registry_enriched r ON ve.ein=r.EIN "
        "WHERE ve.id=?",
        (event_id,),
    ).fetchone()
    if not row:
        return jsonify({"error": "Event not found"}), 404
    e = _format_event(row, signup_count=_event_signup_count(db, event_id))
    e["org_name"]    = row["org_name"]
    e["org_mission"] = row["org_mission"]
    return jsonify(e)


@app.route('/e/<short_id>', methods=['GET'])
def event_short_redirect(short_id: str):
    """Short URL: /e/{short_id} → 301 → /events/{id}. Used in QR codes and SMS."""
    if not re.match(r'^[A-Za-z0-9_-]{6,16}$', short_id):
        return jsonify({"error": "Not found"}), 404
    db = get_db()
    row = db.execute("SELECT id FROM volunteer_events WHERE short_id=?", (short_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    from flask import redirect
    return redirect(f"/events/{row['id']}", code=301)


@app.route('/api/events/<int:event_id>/qr.png', methods=['GET'])
@limiter.limit("30 per minute")
def event_qr_code(event_id: int):
    """Generate a QR code PNG pointing to this event's short URL."""
    import io
    import qrcode
    import qrcode.constants
    db = get_db()
    row = db.execute(
        "SELECT id, short_id, status FROM volunteer_events WHERE id=?", (event_id,)
    ).fetchone()
    if not row:
        return jsonify({"error": "Event not found"}), 404
    url = (f"https://daanaa.org/e/{row['short_id']}" if row["short_id"]
           else f"https://daanaa.org/events/{event_id}")
    qr = qrcode.QRCode(
        version=None, box_size=10, border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d2033", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers['Content-Type']  = 'image/png'
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp


@app.route('/api/events/<int:event_id>/calendar.ics', methods=['GET'])
@limiter.limit("60 per minute")
def event_ical(event_id: int):
    """iCal download for any event. Works with Google, Outlook, and Apple Calendar."""
    db = get_db()
    row = db.execute(
        "SELECT ve.*, r.organization_name AS org_name "
        "FROM volunteer_events ve LEFT JOIN registry_enriched r ON ve.ein=r.EIN "
        "WHERE ve.id=?",
        (event_id,),
    ).fetchone()
    if not row or row["status"] == "cancelled":
        return jsonify({"error": "Event not found"}), 404

    ev_date    = row["event_date"]
    start_time = row["start_time"] or "09:00"
    end_time   = row["end_time"] or (
        f"{int(start_time.split(':')[0])+1:02d}:{start_time.split(':')[1]}"
    )
    dtstart = f"{ev_date.replace('-','')}T{start_time.replace(':','')}00"
    dtend   = f"{ev_date.replace('-','')}T{end_time.replace(':','')}00"

    location = "Virtual event" if row["is_virtual"] else ", ".join(
        filter(None, [row["location_city"], row["location_state"], row["location_zip"]])
    )
    desc = (row["description"] or "").replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,')
    org_name = row["org_name"] or "Unknown Organization"
    url  = f"https://daanaa.org/events/{event_id}"

    ical = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Daanaa//daanaa.org//EN\r\n"
        "CALSCALE:GREGORIAN\r\nMETHOD:PUBLISH\r\nBEGIN:VEVENT\r\n"
        f"UID:event-{event_id}@daanaa.org\r\n"
        f"DTSTART:{dtstart}\r\nDTEND:{dtend}\r\n"
        f"SUMMARY:{row['title']}\r\n"
        f"DESCRIPTION:{desc}\r\n"
        f"LOCATION:{location}\r\nURL:{url}\r\n"
        f"ORGANIZER;CN={org_name}:mailto:events@daanaa.org\r\n"
        "STATUS:CONFIRMED\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    )
    resp = make_response(ical)
    resp.headers['Content-Type']        = 'text/calendar; charset=utf-8'
    resp.headers['Content-Disposition'] = f'attachment; filename="event-{event_id}.ics"'
    return resp


# ── Events: public signup ──────────────────────────────────────────────────

@app.route('/api/events/<int:event_id>/signup', methods=['POST'])
@limiter.limit("20 per minute")
def event_signup_create(event_id: int):
    """Group signup for an event. No auth required. Returns HMAC booking token for cancellation."""
    data = request.get_json(silent=True) or {}

    contact_name  = (data.get('contact_name') or '').strip()[:200]
    contact_email = (data.get('contact_email') or '').strip()[:200].lower()
    if not contact_name or not contact_email:
        return jsonify({"error": "contact_name and contact_email are required"}), 400
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', contact_email):
        return jsonify({"error": "Invalid email address"}), 400

    attendees_raw = data.get('attendees') or []
    if not isinstance(attendees_raw, list):
        return jsonify({"error": "attendees must be a list"}), 400

    valid_age_groups = {'child', 'teen', 'adult', 'senior'}
    attendees = []
    for a in attendees_raw[:50]:
        if not isinstance(a, dict):
            continue
        name = (a.get('name') or '').strip()[:200]
        age_group = (a.get('age_group') or 'adult').strip()
        if age_group not in valid_age_groups:
            age_group = 'adult'
        if name:
            attendees.append({'name': name, 'age_group': age_group})

    if not attendees:
        attendees = [{'name': contact_name, 'age_group': 'adult'}]

    total_count = len(attendees)

    db = get_db()
    row = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return jsonify({"error": "Event not found"}), 404
    if row["status"] in ('cancelled', 'expired'):
        return jsonify({"error": "This event is no longer accepting signups"}), 400
    if "discovery_status" in row.keys() and row["discovery_status"] != "confirmed":
        return jsonify({"error": "This event has not been confirmed by the organization", "status": "unconfirmed", "source_url": row["source_url"] if "source_url" in row.keys() else None}), 409
    from datetime import datetime as _dt
    if row["event_date"] < _dt.utcnow().strftime("%Y-%m-%d"):
        return jsonify({"error": "This event has already passed"}), 400

    # Min age enforcement
    row_keys = row.keys() if hasattr(row, 'keys') else []
    min_age = row["min_age"] if "min_age" in row_keys else None
    if min_age and min_age >= 13:
        child_count = sum(1 for a in attendees if a['age_group'] == 'child')
        if child_count and min_age >= 13:
            return jsonify({"error": f"Attendees must be at least {min_age} years old"}), 400

    # Capacity check
    if row["capacity"] is not None:
        confirmed = db.execute(
            "SELECT COALESCE(SUM(total_count),0) AS n FROM org_signups "
            "WHERE event_id=? AND status='confirmed'",
            (event_id,),
        ).fetchone()["n"]
        spots_left = row["capacity"] - confirmed
        if total_count > spots_left:
            return jsonify({"error": f"Only {max(0, spots_left)} spot(s) remaining"}), 400

    # Idempotency
    ikey = (data.get('idempotency_key') or '').strip()[:64] or None
    if ikey:
        existing = db.execute(
            "SELECT booking_token FROM org_signups WHERE idempotency_key=?", (ikey,)
        ).fetchone()
        if existing:
            return jsonify({"booking_token": existing["booking_token"], "idempotent": True}), 200

    nonce         = secrets.token_hex(8)
    booking_token = _make_booking_token(event_id, contact_email, nonce)

    try:
        db.execute("""
            INSERT INTO org_signups
                (event_id, contact_name, contact_email, booking_token,
                 idempotency_key, attendees, total_count, status)
            VALUES (?,?,?,?,?,?,?,'confirmed')
        """, (event_id, contact_name, contact_email, booking_token,
              ikey, json.dumps(attendees), total_count))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Could not complete signup. Please try again."}), 409

    cancel_url = f"https://daanaa.org/events/{event_id}?cancel={booking_token}"
    event_url  = f"https://daanaa.org/events/{event_id}"
    org_name_row = db.execute(
        "SELECT organization_name FROM registry_enriched WHERE EIN=?", (row["ein"],)
    ).fetchone()
    org_display = org_name_row["organization_name"] if org_name_row else "the organization"

    attendee_names = ", ".join(a['name'] for a in attendees)
    keys = row.keys() if hasattr(row, 'keys') else []
    what_to_bring_val  = row["what_to_bring"]  if "what_to_bring"  in keys else None
    parking_info_val   = row["parking_info"]   if "parking_info"   in keys else None
    waiver_url_val     = row["waiver_url"]     if "waiver_url"     in keys else None
    coord_name         = row["coordinator_name"] if "coordinator_name" in keys else None

    # Prep details for volunteer confirmation
    prep_block = ""
    if what_to_bring_val:
        prep_block += f"\nWhat to bring: {what_to_bring_val}"
    if parking_info_val:
        prep_block += f"\nParking / transit: {parking_info_val}"
    if waiver_url_val:
        prep_block += f"\nWaiver required: {waiver_url_val}"

    # Volunteer confirmation email
    _send_daanaa_email(
        contact_email,
        f"You're confirmed — {row['title']}",
        f"Hi {contact_name},\n\nYou're signed up for {row['title']}.\n\n"
        f"Date: {row['event_date']}\n"
        f"Organizer: {org_display}\n"
        f"Attending: {attendee_names}"
        f"{prep_block}\n\n"
        f"Event page: {event_url}\n\n"
        f"Need to cancel? Visit: {cancel_url}\n\n"
        f"Your contact info was shared with the organizer only. "
        f"Daanaa does not retain it after the event.\n\n— Daanaa team",
        from_addr="events@daanaa.org",
    )

    # Notify the volunteer coordinator / ED so they know someone signed up
    notify_email = row["contact_email"] if "contact_email" in keys else None
    if notify_email:
        coord_display = coord_name or "there"
        party_summary = f"{contact_name}" + (
            f" + {total_count - 1} more" if total_count > 1 else ""
        )
        portal_url = f"https://daanaa.org/nonprofit/portal"
        _send_daanaa_email(
            notify_email,
            f"New signup — {row['title']}",
            f"Hi {coord_display},\n\n"
            f"{party_summary} just signed up for {row['title']} on {row['event_date']}.\n\n"
            f"Total confirmed: {_event_signup_count(db, event_id)}\n"
            f"Event page: {event_url}\n"
            f"View all signups: {portal_url}\n\n"
            f"— Daanaa team",
            from_addr="events@daanaa.org",
        )

    return jsonify({
        "ok": True,
        "booking_token": booking_token,
        "total_count": total_count,
        "cancel_url": cancel_url,
    }), 201


@app.route('/api/events/<int:event_id>/cancel-booking', methods=['POST'])
@limiter.limit("20 per minute")
def event_signup_cancel(event_id: int):
    """Cancel a signup via HMAC booking token. No auth required — token IS the proof."""
    data  = request.get_json(silent=True) or {}
    token = (data.get('booking_token') or request.args.get('cancel') or '').strip()[:64]
    if not token:
        return jsonify({"error": "booking_token required"}), 400

    db  = get_db()
    row = db.execute(
        "SELECT * FROM org_signups WHERE booking_token=? AND event_id=?",
        (token, event_id),
    ).fetchone()
    if not row:
        return jsonify({"error": "Booking not found"}), 404
    if row["status"] == "cancelled":
        return jsonify({"ok": True, "already_cancelled": True}), 200

    reason = (data.get('reason') or '').strip()[:200] or None
    db.execute(
        "UPDATE org_signups SET status='cancelled', cancelled_at=CURRENT_TIMESTAMP, "
        "cancel_reason=? WHERE id=?",
        (reason, row["id"]),
    )
    db.commit()
    return jsonify({"ok": True})


# ── Events: org portal (Firebase auth) ────────────────────────────────────

def _assert_org_claim(uid: str, ein: str, db) -> None:
    """Abort 403 if Firebase uid does not own a verified claim for ein."""
    if not db.execute(
        "SELECT 1 FROM org_claims WHERE ein=? AND firebase_uid=? "
        "AND claim_status IN ('verified','active') AND revoked_at IS NULL",
        (ein, uid),
    ).fetchone():
        abort(403)


@app.route('/api/portal/events', methods=['GET'])
@limiter.limit("60 per minute")
def portal_events_list():
    """Firebase-auth: list events for the org's verified claim."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in (request.args.get('ein') or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({"error": "ein required"}), 400
    db = get_db()
    _assert_org_claim(uid, ein, db)
    include_past = request.args.get('all') == '1'
    if include_past:
        rows = db.execute(
            "SELECT *, (SELECT COALESCE(SUM(total_count),0) FROM org_signups "
            "WHERE event_id=volunteer_events.id AND status='confirmed') AS signup_count "
            "FROM volunteer_events WHERE ein=? ORDER BY event_date DESC LIMIT 100",
            (ein,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT *, (SELECT COALESCE(SUM(total_count),0) FROM org_signups "
            "WHERE event_id=volunteer_events.id AND status='confirmed') AS signup_count "
            "FROM volunteer_events WHERE ein=? AND status NOT IN ('cancelled','expired') "
            "AND event_date >= date('now') ORDER BY event_date ASC LIMIT 50",
            (ein,),
        ).fetchall()
    return jsonify({"events": [_format_event(r, r["signup_count"]) for r in rows]})


@app.route('/api/portal/events', methods=['POST'])
@limiter.limit("20 per minute")
def portal_events_create():
    """Firebase-auth: create a new event. Replaces token-based creation for portal users."""
    uid  = _require_firebase_user()
    data = request.get_json(silent=True) or {}
    ein  = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({"error": "ein required"}), 400
    db = get_db()
    _assert_org_claim(uid, ein, db)

    title      = (data.get('title')      or '').strip()[:200]
    event_date = (data.get('event_date') or '').strip()[:10]
    if not title or not event_date:
        return jsonify({"error": "title and event_date are required"}), 400
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', event_date):
        return jsonify({"error": "event_date must be YYYY-MM-DD"}), 400

    event_type     = (data.get('event_type') or 'volunteer').strip()[:20]
    if event_type not in ('volunteer', 'community', 'fundraiser', 'networking'):
        event_type = 'volunteer'
    description    = (data.get('description')    or '').strip()[:2000]
    start_time     = (data.get('start_time')     or '').strip()[:5] or None
    end_time       = (data.get('end_time')       or '').strip()[:5] or None
    location_city  = (data.get('location_city')  or '').strip()[:100] or None
    location_state = (data.get('location_state') or '').strip()[:2].upper() or None
    location_zip   = (data.get('location_zip')   or '').strip()[:10] or None
    is_virtual     = bool(data.get('is_virtual', False))
    virtual_url    = (data.get('virtual_url')    or '').strip()[:500] or None
    contact_email  = (data.get('contact_email')  or '').strip()[:200] or None
    capacity       = data.get('capacity')
    min_age        = data.get('min_age')
    expected_hours = data.get('expected_hours')
    co_org_eins    = data.get('co_org_eins') or None

    if capacity is not None:
        try: capacity = max(1, int(capacity))
        except (ValueError, TypeError): capacity = None
    if min_age is not None:
        try: min_age = max(0, int(min_age))
        except (ValueError, TypeError): min_age = None
    if expected_hours is not None:
        try: expected_hours = round(float(expected_hours), 1)
        except (ValueError, TypeError): expected_hours = None
    if virtual_url and not virtual_url.startswith(('http://', 'https://')):
        virtual_url = None

    # Generate a unique short_id
    short_id = None
    for _ in range(10):
        candidate = _make_event_short_id()
        if not db.execute("SELECT 1 FROM volunteer_events WHERE short_id=?", (candidate,)).fetchone():
            short_id = candidate
            break

    cur = db.execute("""
        INSERT INTO volunteer_events
            (ein, title, description, event_date, start_time, end_time,
             location_city, location_state, location_zip, is_virtual, virtual_url,
             contact_email, capacity, status, event_type, short_id, min_age,
             expected_hours, co_org_eins)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'active',?,?,?,?,?)
    """, (ein, title, description or None, event_date, start_time, end_time,
          location_city, location_state, location_zip, int(is_virtual), virtual_url,
          contact_email, capacity, event_type, short_id, min_age, expected_hours,
          json.dumps(co_org_eins) if isinstance(co_org_eins, list) else None))
    db.commit()
    row = db.execute("SELECT * FROM volunteer_events WHERE id=?", (cur.lastrowid,)).fetchone()
    _log_org_activity(ein, 'event_created', f'Event created: {title}', actor='org')
    return jsonify(_format_event(row)), 201


@app.route('/api/portal/events/<int:event_id>', methods=['PATCH'])
@limiter.limit("30 per minute")
def portal_events_update(event_id: int):
    """Firebase-auth: update an event owned by the authenticated org."""
    uid  = _require_firebase_user()
    data = request.get_json(silent=True) or {}
    db   = get_db()
    row  = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return jsonify({"error": "Event not found"}), 404
    _assert_org_claim(uid, row["ein"], db)
    if row["status"] in ('cancelled', 'expired'):
        return jsonify({"error": "Cannot update a cancelled or expired event"}), 400

    allowed = {
        "title", "description", "event_date", "start_time", "end_time",
        "location_city", "location_state", "location_zip", "is_virtual",
        "virtual_url", "contact_email", "capacity", "status",
        "event_type", "min_age", "expected_hours", "discovery_status",
    }
    valid_statuses   = {"active", "filled", "cancelled"}
    valid_event_types = {"volunteer", "community", "fundraiser", "networking"}
    valid_discovery_statuses = {"confirmed", "unconfirmed"}
    updates, vals = [], []
    for field in allowed:
        if field not in data:
            continue
        val = data[field]
        if field == "status" and val not in valid_statuses:
            return jsonify({"error": f"status must be one of {sorted(valid_statuses)}"}), 400
        if field == "event_type" and val not in valid_event_types:
            return jsonify({"error": f"event_type must be one of {sorted(valid_event_types)}"}), 400
        if field == "discovery_status" and val not in valid_discovery_statuses:
            return jsonify({"error": f"discovery_status must be one of {sorted(valid_discovery_statuses)}"}), 400
        if field == "is_virtual":
            val = int(bool(val))
        if field == "virtual_url" and val and not str(val).startswith(('http://', 'https://')):
            continue
        updates.append(f"{field}=?")
        vals.append(val)

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    updates.append("updated_at=CURRENT_TIMESTAMP")
    db.execute(f"UPDATE volunteer_events SET {', '.join(updates)} WHERE id=?", vals + [event_id])
    db.commit()
    row = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    return jsonify(_format_event(row, signup_count=_event_signup_count(db, event_id)))


@app.route('/api/portal/events/<int:event_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
def portal_events_cancel(event_id: int):
    """Firebase-auth: cancel an event and notify all confirmed signups."""
    uid  = _require_firebase_user()
    data = request.get_json(silent=True) or {}
    db   = get_db()
    row  = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return jsonify({"error": "Event not found"}), 404
    _assert_org_claim(uid, row["ein"], db)
    if row["status"] == "cancelled":
        return jsonify({"ok": True, "already_cancelled": True}), 200

    cancel_reason = (data.get('reason') or '').strip()[:500]
    db.execute(
        "UPDATE volunteer_events SET status='cancelled', updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (event_id,),
    )
    db.commit()

    # Notify confirmed signups
    signups = db.execute(
        "SELECT contact_name, contact_email FROM org_signups "
        "WHERE event_id=? AND status='confirmed'",
        (event_id,),
    ).fetchall()
    org_name_row = db.execute(
        "SELECT organization_name FROM registry_enriched WHERE EIN=?", (row["ein"],)
    ).fetchone()
    org_display = org_name_row["organization_name"] if org_name_row else "the organization"
    reason_line = f"\nReason: {cancel_reason}" if cancel_reason else ""
    for s in signups:
        _send_daanaa_email(
            s["contact_email"],
            f"Event cancelled — {row['title']}",
            f"Hi {s['contact_name']},\n\n"
            f"Unfortunately, {row['title']} on {row['event_date']} has been cancelled "
            f"by {org_display}.{reason_line}\n\n"
            f"We're sorry for the inconvenience. You can find other events at "
            f"https://daanaa.org/volunteer\n\n— Daanaa team",
            from_addr="events@daanaa.org",
        )
    _log_org_activity(row["ein"], 'event_cancelled', f'Event cancelled: {row["title"]}', actor='org')
    return jsonify({"ok": True, "notified": len(signups)})


@app.route('/api/portal/events/<int:event_id>/attendees', methods=['GET'])
@limiter.limit("60 per minute")
def portal_event_attendees(event_id: int):
    """Firebase-auth: list signups for an event (contact info + attendee list)."""
    uid = _require_firebase_user()
    db  = get_db()
    row = db.execute("SELECT ein FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return jsonify({"error": "Event not found"}), 404
    _assert_org_claim(uid, row["ein"], db)
    signups = db.execute(
        "SELECT * FROM org_signups WHERE event_id=? ORDER BY created_at ASC", (event_id,)
    ).fetchall()
    out = []
    for s in signups:
        try:
            attendees = json.loads(s["attendees"] or "[]")
        except (json.JSONDecodeError, TypeError):
            attendees = []
        out.append({
            "id":              s["id"],
            "contact_name":    s["contact_name"],
            "contact_email":   s["contact_email"],
            "attendees":       attendees,
            "total_count":     s["total_count"],
            "status":          s["status"],
            "hours_verified":  s["hours_verified"],
            "hours_verified_at": s["hours_verified_at"],
            "created_at":      s["created_at"],
        })
    return jsonify({"signups": out, "total": sum(s["total_count"] for s in signups
                                                  if s["status"] == "confirmed")})


@app.route('/api/portal/events/<int:event_id>/verify-hours', methods=['POST'])
@limiter.limit("30 per minute")
def portal_verify_hours(event_id: int):
    """Firebase-auth: verify volunteer hours for one or more signups after the event."""
    uid  = _require_firebase_user()
    data = request.get_json(silent=True) or {}
    db   = get_db()
    event = db.execute("SELECT * FROM volunteer_events WHERE id=?", (event_id,)).fetchone()
    if not event:
        return jsonify({"error": "Event not found"}), 404
    _assert_org_claim(uid, event["ein"], db)

    # Payload: {"verifications": [{"signup_id": 1, "hours": 3.0, "attended": true}]}
    verifications = data.get("verifications") or []
    if not isinstance(verifications, list):
        return jsonify({"error": "verifications must be a list"}), 400

    updated = 0
    for v in verifications:
        if not isinstance(v, dict):
            continue
        signup_id = v.get("signup_id")
        attended  = bool(v.get("attended", True))
        hours     = v.get("hours")
        if hours is not None:
            try: hours = round(float(hours), 1)
            except (ValueError, TypeError): hours = None

        new_status = "attended" if attended else "no_show"
        db.execute(
            "UPDATE org_signups SET status=?, hours_verified=?, "
            "hours_verified_at=CURRENT_TIMESTAMP, hours_verified_by=? "
            "WHERE id=? AND event_id=?",
            (new_status, hours, uid, signup_id, event_id),
        )
        updated += db.execute("SELECT changes()").fetchone()[0]

    db.commit()
    return jsonify({"ok": True, "updated": updated})


# ── Org contacts: public directory ─────────────────────────────────────────

# Public fields shown on the org detail page (never internal rep info)
_PUBLIC_CONTACT_FIELDS = (
    "general_email", "general_phone", "mailing_address",
    "volunteer_name", "volunteer_email",
    "events_name", "events_email",
    "media_name", "media_email",
    "donor_name", "donor_email",
    "website",
    "facebook_url", "instagram_url", "linkedin_url", "twitter_url", "youtube_url",
)
_ALL_CONTACT_FIELDS = _PUBLIC_CONTACT_FIELDS + ("volunteer_phone",)


@app.route('/api/org/<ein>/contacts', methods=['GET'])
@limiter.limit("120 per minute")
def org_contacts_public(ein: str):
    """Public: structured contact directory for a claimed org."""
    clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not clean:
        return jsonify({"error": "Invalid EIN"}), 400
    db  = get_db()
    row = db.execute("SELECT * FROM org_contacts WHERE ein=?", (clean,)).fetchone()
    if not row:
        return jsonify({"contacts": {}})
    return jsonify({"contacts": {f: row[f] for f in _PUBLIC_CONTACT_FIELDS if row[f]}})


@app.route('/api/portal/contacts', methods=['GET'])
@limiter.limit("60 per minute")
def portal_contacts_get():
    """Firebase-auth: full contact record for the org."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in (request.args.get('ein') or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({"error": "ein required"}), 400
    db = get_db()
    _assert_org_claim(uid, ein, db)
    row = db.execute("SELECT * FROM org_contacts WHERE ein=?", (ein,)).fetchone()
    if not row:
        return jsonify({"contacts": {}})
    return jsonify({"contacts": dict(row)})


@app.route('/api/portal/contacts', methods=['PUT'])
@limiter.limit("20 per minute")
def portal_contacts_update():
    """Firebase-auth: upsert contact directory for a claimed org."""
    uid  = _require_firebase_user()
    data = request.get_json(silent=True) or {}
    ein  = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({"error": "ein required"}), 400
    db = get_db()
    _assert_org_claim(uid, ein, db)

    # Allowed writable fields and max lengths
    writable = {
        "general_email": 200, "general_phone": 30, "mailing_address": 500,
        "volunteer_name": 200, "volunteer_email": 200, "volunteer_phone": 30,
        "donor_name": 200, "donor_email": 200,
        "events_name": 200, "events_email": 200,
        "media_name": 200, "media_email": 200,
        "website": 500,
        "facebook_url": 500, "instagram_url": 500, "linkedin_url": 500,
        "twitter_url": 500, "youtube_url": 500,
    }

    fields, vals = [], []
    for field, maxlen in writable.items():
        if field not in data:
            continue
        val = (data[field] or '').strip()[:maxlen] or None
        # Validate URL fields
        if field.endswith('_url') and val and not val.startswith(('http://', 'https://')):
            continue
        # Basic email validation
        if field.endswith('_email') and val and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', val):
            continue
        fields.append(field)
        vals.append(val)

    if not fields:
        return jsonify({"error": "No valid fields provided"}), 400

    set_clause = ", ".join(f"{f}=?" for f in fields)
    set_clause += ", updated_at=CURRENT_TIMESTAMP, updated_by=?"
    vals += [uid, ein]
    db.execute(
        f"INSERT INTO org_contacts (ein) VALUES (?) ON CONFLICT(ein) DO NOTHING", (ein,)
    )
    db.execute(f"UPDATE org_contacts SET {set_clause} WHERE ein=?", vals)
    db.commit()
    _log_org_activity(ein, 'contacts_updated', 'Contact directory updated', actor='org')
    row = db.execute("SELECT * FROM org_contacts WHERE ein=?", (ein,)).fetchone()
    return jsonify({"contacts": dict(row)})


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


# ── Research Dashboard API ────────────────────────────────────────────────────
# These endpoints power the /research presentation dashboard. They serve only
# aggregate public IRS data (no PII, no donor data), so they are public — the
# old passcode/session gate was removed 2026-06-09 (audit Session 2): the
# frontend reads a static snapshot anyway, and the passcode lived in source.

@app.route('/api/research/summary/operating-models')
@limiter.exempt
def research_operating_models():
    """Operating model distribution chart data."""
    valid_models = [
        'Activity_Programming',
        'Direct_Delivery',
        'Community_Human_Services',
        'Clinical_Reimbursement',
        'Emergency_Logistics',
        'Cause_Advocacy_Research',
        'Intermediary_Public_Benefit',
        'Faith_Community',
        'Membership_Mutual_Benefit',
    ]

    db = get_db()
    rows = db.execute("""
        SELECT operating_model, count, pct_of_total, avg_revenue, median_peer_percentile, period
        FROM research_operating_model_summary
        WHERE period = (SELECT MAX(period) FROM research_operating_model_summary)
          AND operating_model IN ({})
        ORDER BY
          CASE operating_model
            WHEN 'Activity_Programming' THEN 0
            WHEN 'Direct_Delivery' THEN 1
            WHEN 'Community_Human_Services' THEN 2
            WHEN 'Clinical_Reimbursement' THEN 3
            WHEN 'Emergency_Logistics' THEN 4
            WHEN 'Cause_Advocacy_Research' THEN 5
            WHEN 'Intermediary_Public_Benefit' THEN 6
            WHEN 'Faith_Community' THEN 7
            WHEN 'Membership_Mutual_Benefit' THEN 8
          END
    """.format(','.join(['?']*len(valid_models))), valid_models).fetchall()

    return jsonify({
        'chart_type': 'bar',
        'data': [
            {
                'operating_model': r['operating_model'],
                'count': r['count'],
                'pct_of_total': round(r['pct_of_total'], 1),
                'avg_revenue': r['avg_revenue'],
                'median_peer_percentile': r['median_peer_percentile']
            }
            for r in rows
        ],
        'last_updated': rows[0]['period'] if rows else None
    })

@app.route('/api/research/summary/revenue-bands')
@limiter.exempt
def research_revenue_bands():
    """Revenue band matrix by operating model."""
    valid_models = [
        'Activity_Programming',
        'Direct_Delivery',
        'Community_Human_Services',
        'Clinical_Reimbursement',
        'Emergency_Logistics',
        'Cause_Advocacy_Research',
        'Intermediary_Public_Benefit',
        'Faith_Community',
        'Membership_Mutual_Benefit',
    ]

    db = get_db()
    rows = db.execute("""
        SELECT operating_model, revenue_band_number, count, pct_of_total, avg_peer_percentile, avg_months_reserve, period
        FROM research_revenue_band_summary
        WHERE period = (SELECT MAX(period) FROM research_revenue_band_summary)
          AND operating_model IN ({})
        ORDER BY
          CASE operating_model
            WHEN 'Activity_Programming' THEN 0
            WHEN 'Direct_Delivery' THEN 1
            WHEN 'Community_Human_Services' THEN 2
            WHEN 'Clinical_Reimbursement' THEN 3
            WHEN 'Emergency_Logistics' THEN 4
            WHEN 'Cause_Advocacy_Research' THEN 5
            WHEN 'Intermediary_Public_Benefit' THEN 6
            WHEN 'Faith_Community' THEN 7
            WHEN 'Membership_Mutual_Benefit' THEN 8
          END,
          revenue_band_number
    """.format(','.join(['?']*len(valid_models))), valid_models).fetchall()

    return jsonify({
        'chart_type': 'matrix',
        'data': [
            {
                'operating_model': r['operating_model'],
                'revenue_band_number': r['revenue_band_number'],
                'count': r['count'],
                'pct_of_total': round(r['pct_of_total'], 2),
                'avg_peer_percentile': r['avg_peer_percentile'],
                'avg_months_reserve': r['avg_months_reserve']
            }
            for r in rows
        ],
        'last_updated': rows[0]['period'] if rows else None
    })

@app.route('/api/research/summary/lamp-tiers')
@limiter.exempt
def research_lamp_tiers():
    """Lamp tier (Beacon/Torch/Candle/Spark) distribution."""
    db = get_db()
    rows = db.execute("""
        SELECT merit_tier, count, pct_of_total, avg_revenue, avg_financial_health_score,
               pct_with_website, avg_peer_percentile, period
        FROM research_lamp_tier_summary
        WHERE period = (SELECT MAX(period) FROM research_lamp_tier_summary)
        ORDER BY
            CASE merit_tier
                WHEN 'Beacon' THEN 1
                WHEN 'Torch' THEN 2
                WHEN 'Candle' THEN 3
                WHEN 'Spark' THEN 4
            END
    """).fetchall()

    return jsonify({
        'chart_type': 'pie',
        'data': [
            {
                'merit_tier': r['merit_tier'],
                'count': r['count'],
                'pct_of_total': round(r['pct_of_total'], 1),
                'avg_revenue': r['avg_revenue'],
                'score': r['avg_financial_health_score'],
                'web_pct': r['pct_with_website']
            }
            for r in rows
        ],
        'last_updated': rows[0]['period'] if rows else None
    })

@app.route('/api/research/summary/data-coverage')
@limiter.exempt
def research_data_coverage():
    """Data availability across key fields."""
    db = get_db()
    rows = db.execute("""
        SELECT data_type, total_orgs, has_data, pct_covered, period
        FROM research_data_coverage_summary
        WHERE period = (SELECT MAX(period) FROM research_data_coverage_summary)
        ORDER BY pct_covered DESC
    """).fetchall()

    return jsonify({
        'chart_type': 'bar',
        'data': [
            {
                'data_type': r['data_type'],
                'total_orgs': r['total_orgs'],
                'has_data': r['has_data'],
                'pct_covered': round(r['pct_covered'], 1)
            }
            for r in rows
        ],
        'last_updated': rows[0]['period'] if rows else None
    })

@app.route('/api/research/summary/categories')
@limiter.exempt
def research_categories():
    """NTEE1 category distribution."""
    db = get_db()
    rows = db.execute("""
        SELECT ntee1, ntee_label, count, pct_of_total, avg_revenue, avg_peer_percentile,
               pct_beacon, pct_torch, pct_candle, pct_spark, period
        FROM research_category_summary
        WHERE period = (SELECT MAX(period) FROM research_category_summary)
        ORDER BY count DESC
    """).fetchall()

    return jsonify({
        'chart_type': 'bar',
        'data': [
            {
                'ntee1': r['ntee1'],
                'ntee_label': r['ntee_label'],
                'count': r['count'],
                'pct_of_total': round(r['pct_of_total'], 1),
                'avg_revenue': r['avg_revenue'],
                'avg_peer_percentile': r['avg_peer_percentile'],
                'pct_beacon': r['pct_beacon'],
                'pct_torch': r['pct_torch'],
                'pct_candle': r['pct_candle'],
                'pct_spark': r['pct_spark']
            }
            for r in rows
        ],
        'last_updated': rows[0]['period'] if rows else None
    })

@app.route('/api/research/summary/states')
@limiter.exempt
def research_states():
    """State-level distribution."""
    db = get_db()
    rows = db.execute("""
        SELECT state, count, pct_of_total, avg_revenue, avg_peer_percentile, pct_with_website, period
        FROM research_state_summary
        WHERE period = (SELECT MAX(period) FROM research_state_summary)
        ORDER BY count DESC LIMIT 10
    """).fetchall()

    return jsonify({
        'chart_type': 'bar',
        'data': [
            {
                'state': r['state'],
                'count': r['count'],
                'pct': round(r['pct_of_total'], 1),
                'avg_revenue': r['avg_revenue'],
                'avg_peer_percentile': r['avg_peer_percentile']
            }
            for r in rows
        ],
        'last_updated': rows[0]['period'] if rows else None
    })

@app.route('/api/research/summary/spending-by-model')
@limiter.exempt
def research_spending_by_model():
    """Program spending distribution by operating model."""
    valid_models = [
        'Activity_Programming',
        'Direct_Delivery',
        'Community_Human_Services',
        'Clinical_Reimbursement',
        'Emergency_Logistics',
        'Cause_Advocacy_Research',
        'Intermediary_Public_Benefit',
        'Faith_Community',
        'Membership_Mutual_Benefit',
    ]

    db = get_db()

    def _percentile(sorted_vals, q):
        """Linear-interpolation percentile (q in 0..1) on a pre-sorted list."""
        if not sorted_vals:
            return None
        if len(sorted_vals) == 1:
            return sorted_vals[0]
        pos = q * (len(sorted_vals) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(sorted_vals) - 1)
        frac = pos - lo
        return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac

    data = []
    for model in valid_models:
        vals = [
            row['p'] for row in db.execute(
                """
                SELECT CAST(r.program_expense_pct AS FLOAT) as p
                FROM v4_scores v
                LEFT JOIN registry_enriched r ON v.EIN = r.EIN
                WHERE v.operating_model = ?
                  AND r.program_expense_pct IS NOT NULL
                ORDER BY r.program_expense_pct
                """,
                [model],
            ).fetchall()
        ]
        if not vals:
            continue
        median = _percentile(vals, 0.5)
        p25 = _percentile(vals, 0.25)
        p75 = _percentile(vals, 0.75)
        data.append({
            'operating_model': model,
            'count': len(vals),
            'median_program_spend': round(median, 1) if median is not None else None,
            'p25_program_spend': round(p25, 1) if p25 is not None else None,
            'p75_program_spend': round(p75, 1) if p75 is not None else None,
        })

    return jsonify({'data': data})

@app.route('/api/research/metadata')
@limiter.exempt
def research_metadata():
    """Metadata about the research dataset."""
    db = get_db()
    total_orgs = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    period = db.execute("SELECT MAX(period) FROM research_operating_model_summary").fetchone()[0]

    return jsonify({
        'total_organizations': total_orgs,
        'data_period': period,
        'version': 'v1.0',
        'generated_at': datetime.now().isoformat(),
        'disclaimer': 'This dashboard reflects public data available to Daanaa at the time of processing. It does not measure impact, quality, worth, trust, or endorsement.'
    })


# ── Frontend static serving ────────────────────────────────────────────────
# ── Impact Wallet (Firestore) ────────────────────────────────────────────────
def claim_phone_callback():
    """
    Twilio incoming voice webhook.
    Verifies webhook signature and logs call attempt.
    Returns TwiML instructions for the caller.
    """
    # Verify Twilio request signature for security
    _auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
    if _auth_token:
        validator = RequestValidator(_auth_token)
        if not validator.validate(request.base_url, request.form or {},
                                  request.headers.get('X-Twilio-Signature', '')):
            app.logger.warning(f"Invalid Twilio signature from {request.remote_addr}")
            abort(403)

    from_phone = (request.form.get('From') or '').strip()
    call_sid = (request.form.get('CallSid') or '').strip()

    app.logger.info(f"[Twilio Voice] Incoming call from {from_phone}, CallSid={call_sid}")

    db = get_db()
    # Look up if this phone is associated with a claim
    claim = db.execute(
        "SELECT ein, rep_name, organization_name FROM org_claims "
        "LEFT JOIN registry_enriched ON org_claims.ein = registry_enriched.EIN "
        "WHERE phone = ? AND claim_status IN ('pending', 'verified', 'active')",
        (from_phone,)
    ).fetchone()

    # Log the call attempt
    if claim:
        db.execute(
            "UPDATE org_claims SET called_at=datetime('now'), call_notes=? WHERE phone=?",
            (f"CallSid: {call_sid}, from {from_phone}", from_phone)
        )
        db.commit()
        org_name = claim['organization_name'] or 'your organization'
        first_name = (claim['rep_name'] or '').split(' ')[0] or 'there'
        _log_org_activity(claim['ein'], 'phone_verification_started',
                         f"Call from {from_phone}, CallSid={call_sid}", actor='system')

    # Return TwiML response
    resp = VoiceResponse()
    resp.say(f"Thank you for verifying your nonprofit claim with Daanaa.", voice='woman')
    resp.say("Please wait for an agent or leave a message.", voice='woman')
    resp.record(max_length=60, action='/api/claim/phone-record', method='POST')

    return str(resp), 200, {'Content-Type': 'text/xml'}


@app.route('/api/claim/phone-record', methods=['POST'])
def claim_phone_record():
    """
    Handle the recording from an incoming voice call.
    Stores the recording reference and notifies admin.
    """
    call_sid = (request.form.get('CallSid') or '').strip()
    from_phone = (request.form.get('From') or '').strip()
    recording_sid = (request.form.get('RecordingSid') or '').strip()

    app.logger.info(f"[Twilio Voice] Recording saved: {recording_sid} for {call_sid}")

    db = get_db()
    claim = db.execute(
        "SELECT ein, rep_name, email FROM org_claims WHERE phone = ?",
        (from_phone,)
    ).fetchone()

    if claim:
        notes = f"Recording: {recording_sid}"
        db.execute(
            "UPDATE org_claims SET call_notes=? WHERE ein=?",
            (notes, claim['ein'])
        )
        db.commit()

        # Notify admin of the call + recording
        _send_daanaa_email(
            os.environ.get('ADMIN_EMAIL', 'orgs@daanaa.org'),
            f"Claim Verification Call from {from_phone}",
            f"Recording available: https://api.twilio.com/2010-04-01/Accounts/{os.environ.get('TWILIO_ACCOUNT_SID')}/Recordings/{recording_sid}\n\n"
            f"Claimant: {claim['rep_name']}\n"
            f"Email: {claim['email']}\n"
            f"CallSid: {call_sid}",
            from_addr="Daanaa <verify@daanaa.org>"
        )

    resp = VoiceResponse()
    resp.say("Thank you. Your recording has been saved. Goodbye.", voice='woman')
    resp.hangup()

    return str(resp), 200, {'Content-Type': 'text/xml'}


@app.route('/api/voice/support', methods=['POST'])
def voice_support_inbound():
    """
    Inbound voice call handler for general nonprofit support.
    All calls transfer to founder's personal number (+1-347-937-3555).
    Phase A: Founder takes all calls directly.
    """
    from_phone = (request.form.get('From') or '').strip()
    call_sid = (request.form.get('CallSid') or '').strip()

    app.logger.info(f"[Support Call] Incoming from {from_phone}, CallSid={call_sid}")

    # Log the call attempt
    db = get_db()
    try:
        db.execute(
            """INSERT INTO support_calls (from_phone, call_sid, received_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (from_phone, call_sid)
        )
        db.commit()
    except sqlite3.OperationalError:
        # Table doesn't exist yet; skip logging for now
        pass

    # Return TwiML response: transfer to founder's phone
    resp = VoiceResponse()
    resp.say("Thank you for calling Daanaa. Connecting you now.", voice='woman')
    resp.dial('+1-347-937-3555')  # Founder's personal number

    return str(resp), 200, {'Content-Type': 'text/xml'}


@app.route('/api/claim/sms-callback', methods=['POST'])
def claim_sms_callback():
    """
    Twilio incoming SMS webhook.
    Verifies webhook signature and logs SMS attempt.
    Returns TwiML response (SMS reply).
    """
    # Verify Twilio request signature
    _auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
    if _auth_token:
        validator = RequestValidator(_auth_token)
        if not validator.validate(request.base_url, request.form or {},
                                  request.headers.get('X-Twilio-Signature', '')):
            app.logger.warning(f"Invalid Twilio signature from {request.remote_addr}")
            abort(403)

    from_phone = (request.form.get('From') or '').strip()
    body = (request.form.get('Body') or '').strip()
    message_sid = (request.form.get('MessageSid') or '').strip()

    app.logger.info(f"[Twilio SMS] Incoming from {from_phone}: {body[:50]}")

    db = get_db()
    claim = db.execute(
        "SELECT ein, rep_name, pin FROM org_claims WHERE phone = ? AND claim_status IN ('pending', 'verified', 'active')",
        (from_phone,)
    ).fetchone()

    if not claim:
        resp = MessagingResponse()
        resp.message("We don't have a pending claim for this phone number. "
                    "Visit daanaa.org/for-nonprofits to start a claim.")
        return str(resp), 200, {'Content-Type': 'text/xml'}

    # Log the SMS attempt
    db.execute(
        "UPDATE org_claims SET called_at=datetime('now'), call_notes=? WHERE ein=?",
        (f"SMS received: {body[:100]}", claim['ein'])
    )
    db.commit()
    _log_org_activity(claim['ein'], 'sms_verification_attempt',
                     f"SMS from {from_phone}: {body[:100]}", actor='system')

    # Simple PIN validation from SMS
    sms_input = ''.join(c for c in body if c.isdigit())
    if hmac.compare_digest(sms_input, claim['pin']):
        # PIN matches! Mark claim as verified
        db.execute(
            "UPDATE org_claims SET claim_status='verified', verified_at=datetime('now') WHERE ein=?",
            (claim['ein'],)
        )
        db.commit()
        _log_org_activity(claim['ein'], 'pin_verified_via_sms',
                         f"PIN verified via SMS from {from_phone}", actor='system')

        resp = MessagingResponse()
        resp.message("Your PIN has been verified! Visit the edit link in your email to manage your organization page.")
        return str(resp), 200, {'Content-Type': 'text/xml'}
    else:
        resp = MessagingResponse()
        resp.message("That PIN is not correct. Please check your verification letter and try again.")
        return str(resp), 200, {'Content-Type': 'text/xml'}


def nonprofit_pending_verifications(ein: str):
    """List volunteer hours pending verification for a nonprofit.

    Requires: X-Verification-Token header (nonprofit claim token)
    Returns: List of volunteer_hour_logs where nonprofit_ein matches and status='logged'
    """
    try:
        token = _require_nonprofit_token()
        db = get_db()

        # Verify the nonprofit owns this EIN (via the claim system)
        claim = db.execute(
            "SELECT * FROM org_claims WHERE EIN = ? AND status = 'verified'",
            (ein,)
        ).fetchone()
        if not claim:
            return jsonify({'error': 'Nonprofit not verified or EIN mismatch'}), 403

        # Query nonprofit_pending_verifications keyed by EIN
        pending = _firestore_list('nonprofit_pending_verifications', user_id=ein)
        # Filter to only pending status (in case some were already verified)
        pending = [p for p in pending if p.get('status') == 'pending']
        pending = sorted(pending, key=lambda x: x.get('created_at', ''), reverse=True)

        return jsonify({'pending_verifications': pending, 'total': len(pending)}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        _logger.error(f"Error fetching pending verifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/nonprofit/<ein>/verify-hours/<log_id>', methods=['POST'])
def nonprofit_verify_hours(ein: str, log_id: str):
    """RETIRED legacy path (Firestore volunteer_hour_logs/confirmations).

    Replaced 2026-07-22 by the canonical volunteer_hours flow so no second
    store of volunteer hour records can drift from the single source of truth.
    Use POST /api/nonprofit/<ein>/volunteer/<hour_id>/approve (Firebase auth
    + verified org claim). Existing Firestore data is untouched — read-only
    history, no new writes."""
    return jsonify({
        'error': 'This endpoint has been retired',
        'use': 'POST /api/nonprofit/<ein>/volunteer/<hour_id>/approve',
    }), 410


# ── Vendor Partnership Reviews ──────────────────────────────────────────
# Fully automated, zero-touch moderation. Nonprofits rate vendors (1-5 stars),
# optionally report savings. Public display is anonymous; vendor sees nonprofit
# name in private dashboard. AI validates: valid star, plausible savings, no spam.

def _ai_validate_rating(stars: int, savings: int, nonprofit_ein: str) -> tuple[bool, str]:
    """
    Validate rating: star range, savings plausibility, spam patterns.
    Returns (is_valid, reason_if_invalid).
    """
    if not isinstance(stars, int) or stars < 1 or stars > 5:
        return False, "Star rating must be 1-5"
    if not isinstance(savings, int) or savings < 0 or savings > 999999:
        return False, "Savings must be 0-999999"
    # Basic spam check: nonprofit exists
    db = get_db()
    org = db.execute("SELECT EIN FROM registry_enriched WHERE EIN = ?", (nonprofit_ein,)).fetchone()
    if not org:
        return False, "Nonprofit not found in registry"
    return True, ""


def _aggregate_vendor_stats(vendor_id: str):
    """Recalculate and cache aggregated stats for a vendor."""
    db = get_db()
    stats = db.execute("""
        SELECT
            ROUND(AVG(stars), 2) as avg_rating,
            COUNT(*) as rating_count,
            SUM(savings_amount) as total_savings,
            COUNT(CASE WHEN savings_amount > 0 THEN 1 END) as nonprofits_contributed
        FROM vendor_ratings
        WHERE vendor_id = ?
    """, (vendor_id,)).fetchone()

    if not stats:
        stats = (None, 0, 0, 0)

    avg_rating, rating_count, total_savings, nonprofits_contributed = stats
    db.execute("""
        INSERT INTO vendor_stats (vendor_id, avg_rating, rating_count, total_savings, nonprofits_contributed, last_aggregated_at, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(vendor_id) DO UPDATE SET
            avg_rating = ?,
            rating_count = ?,
            total_savings = ?,
            nonprofits_contributed = ?,
            last_aggregated_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
    """, (vendor_id, avg_rating, rating_count or 0, total_savings or 0, nonprofits_contributed or 0,
          avg_rating, rating_count or 0, total_savings or 0, nonprofits_contributed or 0))
    db.commit()


@app.route('/api/vendors', methods=['GET'])
@app.route('/api/vendors/', methods=['GET'])
def get_vendors():
    """List all active vendors with aggregated stats."""
    db = get_db()
    vendors = db.execute("""
        SELECT v.*, s.avg_rating, s.rating_count, s.total_savings
        FROM vendors v
        LEFT JOIN vendor_stats s ON v.vendor_id = s.vendor_id
        WHERE v.active = 1
        ORDER BY s.avg_rating DESC, v.created_at DESC
    """).fetchall()

    result = []
    for row in vendors:
        result.append({
            'vendor_id': row['vendor_id'],
            'name': row['name'],
            'category': row['category'],
            'description': row['description'],
            'website': row['website'],
            'logo_url': row['logo_url'],
            'discount_code': row['discount_code'],
            'discount_description': row['discount_description'],
            'avg_rating': row['avg_rating'],
            'rating_count': row['rating_count'] or 0,
            'total_savings': row['total_savings'] or 0,
        })

    return jsonify({'vendors': result})


@app.route('/api/vendors/<vendor_id>', methods=['GET'])
def get_vendor(vendor_id: str):
    """Get vendor detail with stats."""
    db = get_db()
    vendor = db.execute("""
        SELECT v.*, s.avg_rating, s.rating_count, s.total_savings
        FROM vendors v
        LEFT JOIN vendor_stats s ON v.vendor_id = s.vendor_id
        WHERE v.vendor_id = ? AND v.active = 1
    """, (vendor_id,)).fetchone()

    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404

    return jsonify({
        'vendor_id': vendor['vendor_id'],
        'name': vendor['name'],
        'category': vendor['category'],
        'description': vendor['description'],
        'contact_email': vendor['contact_email'],
        'website': vendor['website'],
        'logo_url': vendor['logo_url'],
        'discount_code': vendor['discount_code'],
        'discount_description': vendor['discount_description'],
        'avg_rating': vendor['avg_rating'],
        'rating_count': vendor['rating_count'] or 0,
        'total_savings': vendor['total_savings'] or 0,
    })


@app.route('/api/vendors/<vendor_id>/ratings', methods=['POST'])
def submit_vendor_rating(vendor_id: str):
    """
    Submit a rating for a vendor.
    Requires Firebase auth (nonprofit_ein from token).
    Auto-validates and publishes if passes checks.

    {
        "stars": 1-5,
        "savings_amount": 0-999999 (optional)
    }
    """
    try:
        # Require Firebase auth
        token = _require_firebase_token()
        nonprofit_ein = token.get('uid', '')

        if not nonprofit_ein:
            return jsonify({'error': 'Authentication required'}), 401

        db = get_db()

        # Vendor must exist
        vendor = db.execute("SELECT vendor_id FROM vendors WHERE vendor_id = ? AND active = 1",
                           (vendor_id,)).fetchone()
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404

        data = request.get_json() or {}
        stars = data.get('stars')
        savings_amount = data.get('savings_amount', 0)

        # Coerce to int
        try:
            stars = int(stars) if stars is not None else None
            savings_amount = int(savings_amount) if savings_amount else 0
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid stars or savings_amount'}), 400

        # AI validation
        is_valid, reason = _ai_validate_rating(stars, savings_amount, nonprofit_ein)
        if not is_valid:
            return jsonify({'error': reason}), 400

        # Check for duplicate (nonprofit can only rate each vendor once, but can update)
        existing = db.execute(
            "SELECT rating_id FROM vendor_ratings WHERE vendor_id = ? AND nonprofit_ein = ?",
            (vendor_id, nonprofit_ein)
        ).fetchone()

        if existing:
            # Update existing rating
            rating_id = existing['rating_id']
            db.execute("""
                UPDATE vendor_ratings
                SET stars = ?, savings_amount = ?, updated_at = CURRENT_TIMESTAMP
                WHERE rating_id = ?
            """, (stars, savings_amount, rating_id))
            db.commit()
            action = 'updated'
        else:
            # Create new rating (auto-published, no moderation queue)
            rating_id = secrets.token_urlsafe(16)
            db.execute("""
                INSERT INTO vendor_ratings (rating_id, vendor_id, nonprofit_ein, stars, savings_amount)
                VALUES (?, ?, ?, ?, ?)
            """, (rating_id, vendor_id, nonprofit_ein, stars, savings_amount))
            db.commit()
            action = 'created'

        # Recalculate vendor stats
        _aggregate_vendor_stats(vendor_id)

        return jsonify({
            'success': True,
            'rating_id': rating_id,
            'action': action,
            'stars': stars,
            'savings_amount': savings_amount,
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        _logger.error(f"Error submitting vendor rating: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/vendors/<vendor_id>/ratings', methods=['GET'])
def get_vendor_ratings(vendor_id: str):
    """
    Get all ratings for a vendor (public view, anonymous).
    Returns: list of {stars, savings_amount, created_at} (no nonprofit name).
    """
    db = get_db()
    ratings = db.execute("""
        SELECT stars, savings_amount, created_at
        FROM vendor_ratings
        WHERE vendor_id = ?
        ORDER BY created_at DESC
    """, (vendor_id,)).fetchall()

    return jsonify({
        'ratings': [
            {
                'stars': r['stars'],
                'savings_amount': r['savings_amount'],
                'created_at': r['created_at'],
            }
            for r in ratings
        ]
    })


@app.route('/api/vendors/<vendor_id>/stats', methods=['GET'])
def get_vendor_stats(vendor_id: str):
    """Get aggregated stats for a vendor."""
    db = get_db()
    stats = db.execute("""
        SELECT avg_rating, rating_count, total_savings, nonprofits_contributed
        FROM vendor_stats
        WHERE vendor_id = ?
    """, (vendor_id,)).fetchone()

    if not stats:
        return jsonify({
            'avg_rating': None,
            'rating_count': 0,
            'total_savings': 0,
            'nonprofits_contributed': 0,
        })

    return jsonify({
        'avg_rating': stats['avg_rating'],
        'rating_count': stats['rating_count'],
        'total_savings': stats['total_savings'],
        'nonprofits_contributed': stats['nonprofits_contributed'],
    })


# ── Nonprofit Hour Verification (Simplified API) ────────────────────────────

@app.route('/api/nonprofit/hours-pending', methods=['GET'])
@limiter.limit("60 per minute")
def nonprofit_hours_pending():
    """RETIRED legacy path (volunteer_hour_logs table).

    Replaced 2026-07-22 by the canonical volunteer_hours flow. Use
    GET /api/nonprofit/<ein>/volunteer/list?status=pending. The old
    volunteer_hour_logs table is retained read-only for history; no new
    records are created there."""
    return jsonify({
        'error': 'This endpoint has been retired',
        'use': 'GET /api/nonprofit/<ein>/volunteer/list?status=pending',
    }), 410


@app.route('/api/nonprofit/verify-hours', methods=['POST'])
def nonprofit_verify_hours_action():
    """RETIRED legacy path (volunteer_hour_logs + volunteer_hour_confirmations).

    Replaced 2026-07-22 by the canonical volunteer_hours approve/reject flow
    (which carries the audit trail, the 30-day lock, and the single idempotent
    bridge into public aggregates). Old tables are retained read-only for
    history; no new records are created there."""
    return jsonify({
        'error': 'This endpoint has been retired',
        'use': 'POST /api/nonprofit/<ein>/volunteer/<hour_id>/approve or /reject',
    }), 410


# ── QA Testing Hub ──────────────────────────────────────────────────────────
# Serves QA test documents, report templates, and submission form
# Accessible at: https://daanaa.org/qa/

@app.route('/qa', defaults={'path': ''})
@app.route('/qa/<path:path>')
def serve_qa(path):
    """Serve QA testing hub: documents, credentials, and report submission."""
    QA_DIR = '/opt/daanaa/qa'
    if not os.path.exists(QA_DIR):
        return jsonify({'error': 'QA hub not available'}), 404

    # Default to index.html if no path
    if not path:
        return send_from_directory(QA_DIR, 'index.html')

    # Serve requested file
    if os.path.exists(os.path.join(QA_DIR, path)):
        return send_from_directory(QA_DIR, path)

    # File not found
    abort(404)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, 'index.html')


# ── Vendor self-service portal ───────────────────────────────────────────────
# Vendors are businesses that serve nonprofits. They self-register, manage
# their own listing, and pay for premium placement. Nonprofits always free.

def _ensure_vendor_portal_schema():
    """Add firebase_uid + portal columns to vendors table if not present."""
    db = get_db()
    existing = {row[1] for row in db.execute("PRAGMA table_info(vendors)").fetchall()}
    migrations = [
        ("firebase_uid",   "TEXT"),
        ("tagline",        "TEXT"),
        ("services",       "TEXT"),   # JSON array
        ("service_areas",  "TEXT"),   # JSON array
        ("founded_year",   "INTEGER"),
        ("team_size",      "TEXT"),
        ("portal_status",  "TEXT DEFAULT 'pending'"),  # pending|active|suspended
        ("portal_notes",   "TEXT"),
        ("approved_at",    "TEXT"),
    ]
    for col, typedef in migrations:
        if col not in existing:
            db.execute(f"ALTER TABLE vendors ADD COLUMN {col} {typedef}")
    db.execute("CREATE INDEX IF NOT EXISTS idx_vendors_firebase ON vendors(firebase_uid)")
    db.commit()


@app.route('/api/vendor/apply', methods=['POST'])
@limiter.limit("5 per hour")
def vendor_apply():
    """
    Vendor self-registers. Creates a pending listing.
    Requires Firebase auth. Idempotent — existing vendor returns their record.

    Body:
      name, category, description, tagline, website, contact_email,
      contact_phone, service_areas (list), discount_description
    """
    uid = _require_firebase_user()
    _ensure_vendor_portal_schema()
    db = get_db()

    # Idempotent — if they already applied, return their record
    existing = db.execute(
        "SELECT vendor_id, portal_status FROM vendors WHERE firebase_uid=?", (uid,)
    ).fetchone()
    if existing:
        return jsonify({
            "vendor_id": existing["vendor_id"],
            "portal_status": existing["portal_status"],
            "message": "Application already on file",
        })

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()[:100]
    category = (data.get("category") or "").strip()[:60]
    description = (data.get("description") or "").strip()[:500]
    tagline = (data.get("tagline") or "").strip()[:120]
    website = (data.get("website") or "").strip()[:200]
    contact_email = (data.get("contact_email") or "").strip()[:100]
    contact_phone = (data.get("contact_phone") or "").strip()[:30]
    service_areas = data.get("service_areas") or []
    discount_description = (data.get("discount_description") or "").strip()[:300]

    if not name or not category or not contact_email:
        return jsonify({"error": "name, category, and contact_email are required"}), 400

    vendor_id = secrets.token_urlsafe(10)
    db.execute("""
        INSERT INTO vendors
          (vendor_id, firebase_uid, name, category, description, tagline, website,
           contact_email, contact_phone, service_areas, discount_description,
           portal_status, active, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,'pending',0,datetime('now'),datetime('now'))
    """, (vendor_id, uid, name, category, description, tagline, website,
          contact_email, contact_phone, json.dumps(service_areas), discount_description))
    db.commit()

    # Notify the team
    _log_org_activity(vendor_id, "vendor_apply",
                      f"New vendor application: {name} ({category})", actor="vendor")

    # Send confirmation email to the applicant
    if get_email_service:
        try:
            svc = get_email_service()
            svc.send(
                contact_email,
                f"We received your Daanaa vendor application: {name}",
                f"""<p>Hi,</p>
<p>We received your application to join the Daanaa Vendor Network as <strong>{name}</strong>.</p>
<p>Our team reviews all applications within 2 business days. We'll email you at {contact_email} with next steps.</p>
<p>In the meantime, you can reach us at <a href="mailto:partners@daanaa.org">partners@daanaa.org</a>.</p>
<p>The Daanaa Team</p>""",
                f"Hi,\n\nWe received your vendor application for {name}. "
                f"We review applications within 2 business days and will email you next steps.\n\n"
                f"Questions? partners@daanaa.org\n\nThe Daanaa Team",
            )
        except Exception as _e:
            _logger.warning(f"vendor apply email failed: {_e}")

    return jsonify({
        "vendor_id": vendor_id,
        "portal_status": "pending",
        "message": "Application received. We review within 2 business days.",
    }), 201


@app.route('/api/vendor/me', methods=['GET'])
@limiter.limit("60 per minute")
def vendor_me():
    """Return the authenticated vendor's own listing and stats."""
    uid = _require_firebase_user()
    _ensure_vendor_portal_schema()
    db = get_db()

    row = db.execute("""
        SELECT v.*, s.avg_rating, s.rating_count, s.total_savings, s.nonprofits_contributed
        FROM vendors v
        LEFT JOIN vendor_stats s ON v.vendor_id = s.vendor_id
        WHERE v.firebase_uid = ?
    """, (uid,)).fetchone()

    if not row:
        return jsonify({"error": "No vendor account found. Apply at /api/vendor/apply"}), 404

    return jsonify({
        "vendor_id": row["vendor_id"],
        "portal_status": row["portal_status"],
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "tagline": row["tagline"],
        "website": row["website"],
        "contact_email": row["contact_email"],
        "contact_phone": row["contact_phone"],
        "service_areas": json.loads(row["service_areas"] or "[]"),
        "discount_description": row["discount_description"],
        "discount_code": row["discount_code"],
        "logo_url": row["logo_url"],
        "active": bool(row["active"]),
        "approved_at": row["approved_at"],
        "created_at": row["created_at"],
        "stats": {
            "avg_rating": row["avg_rating"],
            "rating_count": row["rating_count"] or 0,
            "total_savings": row["total_savings"] or 0,
            "nonprofits_contributed": row["nonprofits_contributed"] or 0,
        },
    })


@app.route('/api/vendor/me', methods=['PATCH'])
@limiter.limit("20 per hour")
def vendor_me_update():
    """
    Vendor updates their own listing.
    Only allowed fields — vendor cannot change portal_status or active flag.
    """
    uid = _require_firebase_user()
    _ensure_vendor_portal_schema()
    db = get_db()

    vendor = db.execute(
        "SELECT vendor_id, portal_status FROM vendors WHERE firebase_uid=?", (uid,)
    ).fetchone()
    if not vendor:
        return jsonify({"error": "No vendor account found"}), 404

    data = request.get_json(silent=True) or {}
    allowed = {
        "name": str, "description": str, "tagline": str,
        "website": str, "contact_phone": str, "discount_description": str,
    }
    updates = {}
    for field, cast in allowed.items():
        if field in data:
            updates[field] = cast(data[field])[:500] if data[field] else ""

    if "service_areas" in data and isinstance(data["service_areas"], list):
        updates["service_areas"] = json.dumps(data["service_areas"][:20])

    if not updates:
        return jsonify({"error": "No updatable fields provided"}), 400

    set_clause = ", ".join(f"{k}=?" for k in updates)
    db.execute(
        f"UPDATE vendors SET {set_clause}, updated_at=datetime('now') WHERE firebase_uid=?",
        (*updates.values(), uid),
    )
    db.commit()
    return jsonify({"ok": True, "updated": list(updates.keys())})


@app.route('/api/admin/vendor/<vendor_id>/approve', methods=['POST'])
@limiter.limit("30 per minute")
def admin_vendor_approve(vendor_id: str):
    """Admin approves a vendor application — makes them active and visible."""
    _require_admin()
    _ensure_vendor_portal_schema()
    db = get_db()
    vendor = db.execute(
        "SELECT vendor_id, name, contact_email FROM vendors WHERE vendor_id=?", (vendor_id,)
    ).fetchone()
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    db.execute("""
        UPDATE vendors SET portal_status='active', active=1,
        approved_at=datetime('now'), updated_at=datetime('now')
        WHERE vendor_id=?
    """, (vendor_id,))
    db.commit()

    # Notify vendor
    if get_email_service and vendor["contact_email"]:
        try:
            get_email_service().send(
                vendor["contact_email"],
                f"Your Daanaa vendor listing is live: {vendor['name']}",
                f"""<p>Hi,</p>
<p>Your vendor listing for <strong>{vendor['name']}</strong> is now live on Daanaa.</p>
<p>Nonprofits in our network can now find you, leave ratings, and request your discount code.</p>
<p>Manage your listing at <a href="https://daanaa.org/vendor/dashboard">daanaa.org/vendor/dashboard</a>.</p>
<p>The Daanaa Team</p>""",
                f"Hi,\n\nYour vendor listing for {vendor['name']} is live on Daanaa. "
                f"Manage it at https://daanaa.org/vendor/dashboard\n\nThe Daanaa Team",
            )
        except Exception as _e:
            _logger.warning(f"vendor approve email failed: {_e}")

    return jsonify({"ok": True, "vendor_id": vendor_id, "status": "active"})


# ── Intent & Event Discovery Admin (Phase 2) ──────────────────────────────────

@app.route('/api/admin/discovery/queue', methods=['GET'])
@require_admin_key
def admin_discovery_queue():
    """Admin: view event discovery candidates pending review."""
    if not ENABLE_EVENT_DISCOVERY or not _discovery_available:
        return jsonify({'error': 'Event discovery not enabled'}), 403

    db = get_db()
    status = request.args.get('status', 'pending_review').strip()
    limit = min(int(request.args.get('limit', '50')), 500)
    offset = int(request.args.get('offset', '0'))

    # Validate status to prevent SQL injection
    valid_statuses = ('pending_review', 'approved', 'rejected', 'expired')
    if status not in valid_statuses:
        status = 'pending_review'

    rows = db.execute(f"""
        SELECT id, ein, source_url, title, event_date, evidence, status,
               last_checked_at, reviewed_at
        FROM event_discovery_queue
        WHERE status=?
        ORDER BY last_checked_at DESC
        LIMIT ? OFFSET ?
    """, (status, limit, offset)).fetchall()

    total = db.execute(
        f"SELECT COUNT(*) as count FROM event_discovery_queue WHERE status=?",
        (status,)
    ).fetchone()['count']

    return jsonify({
        'status': status,
        'candidates': [dict(r) for r in rows],
        'total': total,
        'limit': limit,
        'offset': offset
    })


@app.route('/api/admin/discovery/queue/<int:candidate_id>/review', methods=['POST'])
@require_admin_key
def admin_discovery_review(candidate_id: int):
    """Admin: approve, reject, or defer an event discovery candidate."""
    if not ENABLE_EVENT_DISCOVERY or not _discovery_available:
        return jsonify({'error': 'Event discovery not enabled'}), 403

    data = request.get_json(silent=True) or {}
    decision = data.get('decision', '').strip()
    notes = data.get('notes', '').strip()[:500]

    if decision not in ('approved', 'rejected', 'deferred'):
        return jsonify({'error': 'decision must be: approved, rejected, or deferred'}), 400

    db = get_db()
    candidate = db.execute(
        "SELECT * FROM event_discovery_queue WHERE id=?", (candidate_id,)
    ).fetchone()

    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404

    if decision == 'approved':
        # Promote to volunteer_events (unconfirmed, awaiting nonprofit claim)
        event_id = secrets.randbelow(1000000)
        db.execute("""
            INSERT INTO volunteer_events (
                event_id, ein, title, event_date, location_city, location_state,
                discovery_status, source_url, ai_generated, claim_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            candidate['ein'],
            candidate['title'],
            candidate['event_date'],
            'Unknown',
            'Unknown',
            'ai_generated',
            candidate['source_url'],
            1,
            'unconfirmed'
        ))

    db.execute("""
        UPDATE event_discovery_queue
        SET status=?, reviewed_at=datetime('now')
        WHERE id=?
    """, (decision, candidate_id))
    db.commit()

    return jsonify({
        'success': True,
        'candidate_id': candidate_id,
        'decision': decision,
        'notes': notes
    })


@app.route('/api/admin/intent/summary', methods=['GET'])
@require_admin_key
def admin_intent_summary():
    """Admin: aggregate intent signals (counts only, no PII)."""
    if not ENABLE_INTENT_SIGNALS or not _intent_available:
        return jsonify({'error': 'Intent signals not enabled'}), 403

    db = get_db()
    ein = request.args.get('ein', '').strip()[:10]
    event_id = request.args.get('event_id', '')

    try:
        if event_id:
            event_id = int(event_id)
        else:
            event_id = None
    except (ValueError, TypeError):
        event_id = None

    # Use intent_layer to get aggregate summary
    if not (ein or event_id):
        return jsonify({'error': 'ein or event_id required'}), 400

    summary = intent_layer.summarize_intent(
        db,
        ein=ein if ein else None,
        event_id=event_id if event_id else None
    )

    return jsonify({
        'ein': ein if ein else None,
        'event_id': event_id if event_id else None,
        'signals': summary
    })


# ── Profile Contexts (Phase 3) ────────────────────────────────────────────────

@app.route('/api/profile-contexts', methods=['GET'])
@limiter.limit("60 per minute")
def get_profile_contexts():
    """Get all shared contexts for the authenticated user."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    db = get_db()

    try:
        contexts = profile_contexts.get_user_contexts(db, uid)
        return jsonify({'contexts': contexts})
    except Exception as e:
        _logger.error(f"get_profile_contexts error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts', methods=['POST'])
@limiter.limit("10 per minute")
def create_profile_context():
    """Create a new shared context (household, DAF, business, other)."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    data = request.get_json(silent=True) or {}

    context_type = data.get('context_type', '').strip().lower()
    display_name = (data.get('display_name') or '').strip()[:100]
    description = (data.get('description') or '').strip()[:500]

    if context_type not in profile_contexts.CONTEXT_TYPES:
        return jsonify({'error': f'Invalid context_type. Must be one of: {", ".join(profile_contexts.CONTEXT_TYPES)}'}), 400

    db = get_db()

    try:
        context_id = profile_contexts.create_context(
            db,
            created_by_uid=uid,
            context_type=context_type,
        )

        context = profile_contexts.get_context_detail(db, context_id)

        # Audit log: profile context created
        log_audit_event(
            event_type='profile_context_created',
            user_auth=uid,
            user_role='lead',
            volunteer_context_id=context_id,
            success=True
        )

        return jsonify({
            'success': True,
            'context_id': context_id,
            'context': dict(context)
        }), 201

    except Exception as e:
        _logger.error(f"create_profile_context error: {e}")

        # Audit log: profile context creation failed
        log_audit_event(
            event_type='profile_context_created',
            user_auth=uid,
            user_role='lead',
            success=False,
            error_code='CREATION_FAILED'
        )

        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts/<context_id>/members', methods=['GET'])
@limiter.limit("60 per minute")
def get_context_members(context_id: str):
    """Get all members of a context (requires membership)."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    db = get_db()

    try:
        # Check access
        if not profile_contexts.can_access_context(db, context_id, uid):
            return jsonify({'error': 'Unauthorized'}), 403

        members = profile_contexts.get_context_members(db, context_id, uid)
        return jsonify({'members': [dict(m) for m in members]})

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        _logger.error(f"get_context_members error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts/<context_id>/members', methods=['POST'])
@limiter.limit("10 per minute")
def add_context_member(context_id: str):
    """Add a member to a context (requires lead or support role)."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    data = request.get_json(silent=True) or {}

    target_uid = data.get('firebase_uid', '').strip()
    role = data.get('role', 'member').strip().lower()

    if not target_uid:
        return jsonify({'error': 'firebase_uid is required'}), 400
    if role not in profile_contexts.ROLES:
        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(profile_contexts.ROLES)}'}), 400

    db = get_db()

    try:
        # Check access (must be lead or support)
        if not profile_contexts.can_access_context(db, context_id, uid, min_role='support'):
            return jsonify({'error': 'Unauthorized (requires lead or support role)'}), 403

        invitation_id = profile_contexts.invite_member(
            db,
            context_id=context_id,
            invited_uid=target_uid,
            role=role,
            invited_by_uid=uid,
        )

        # Audit log: member invited
        log_audit_event(
            event_type='member_invited',
            user_auth=uid,
            user_role='support',
            volunteer_context_id=context_id,
            success=True
        )

        return jsonify({'success': True, 'invitation_id': invitation_id, 'invited_uid': target_uid, 'role': role}), 201

    except ValueError as e:
        # Audit log: invitation failed (value error)
        log_audit_event(
            event_type='member_invited',
            user_auth=uid,
            user_role='support',
            volunteer_context_id=context_id,
            success=False,
            error_code='NOT_FOUND'
        )
        return jsonify({'error': str(e)}), 404
    except PermissionError as e:
        # Audit log: invitation failed (permission denied)
        log_audit_event(
            event_type='member_invited',
            user_auth=uid,
            user_role='support',
            volunteer_context_id=context_id,
            success=False,
            error_code='UNAUTHORIZED'
        )
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        _logger.error(f"add_context_member error: {e}")
        # Audit log: invitation failed (unexpected error)
        log_audit_event(
            event_type='member_invited',
            user_auth=uid,
            user_role='support',
            volunteer_context_id=context_id,
            success=False,
            error_code='INTERNAL_ERROR'
        )
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts/invitations/pending', methods=['GET'])
@limiter.limit("60 per minute")
def get_pending_invitations():
    """Get pending invitations for the current user."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    db = get_db()

    try:
        invitations = profile_contexts.get_user_invitations(db, uid)
        return jsonify({'invitations': [dict(inv) for inv in invitations]})
    except Exception as e:
        _logger.error(f"get_pending_invitations error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts/invitations/<invitation_id>/accept', methods=['POST'])
@limiter.limit("10 per minute")
def accept_context_invitation(invitation_id: str):
    """Accept a pending invitation to join a context."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    db = get_db()

    try:
        profile_contexts.accept_invitation(db, invitation_id=invitation_id, accepting_uid=uid)
        return jsonify({'success': True, 'invitation_id': invitation_id}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        _logger.error(f"accept_context_invitation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts/invitations/<invitation_id>/reject', methods=['POST'])
@limiter.limit("10 per minute")
def reject_context_invitation(invitation_id: str):
    """Reject a pending invitation to join a context."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    db = get_db()

    try:
        profile_contexts.reject_invitation(db, invitation_id=invitation_id, rejecting_uid=uid)
        return jsonify({'success': True, 'invitation_id': invitation_id}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        _logger.error(f"reject_context_invitation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts/<context_id>/members/<target_uid>', methods=['PATCH'])
@limiter.limit("10 per minute")
def update_context_member(context_id: str, target_uid: str):
    """Update a member's role in a context (requires lead role)."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    data = request.get_json(silent=True) or {}

    new_role = data.get('role', '').strip().lower()

    if not new_role:
        return jsonify({'error': 'role is required'}), 400
    if new_role not in profile_contexts.ROLES:
        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(profile_contexts.ROLES)}'}), 400

    db = get_db()

    try:
        # Check access (must be lead)
        if not profile_contexts.can_access_context(db, context_id, uid, min_role='lead'):
            return jsonify({'error': 'Unauthorized (requires lead role)'}), 403

        profile_contexts.update_member_role(
            db,
            context_id=context_id,
            firebase_uid=target_uid,
            new_role=new_role,
            changed_by_uid=uid,
        )

        return jsonify({'success': True, 'firebase_uid': target_uid, 'role': new_role})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        _logger.error(f"update_context_member error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts/<context_id>/members/<target_uid>', methods=['DELETE'])
@limiter.limit("10 per minute")
def remove_context_member(context_id: str, target_uid: str):
    """Remove a member from a context (requires lead or support role)."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    db = get_db()

    try:
        # Check access (must be lead or support)
        if not profile_contexts.can_access_context(db, context_id, uid, min_role='support'):
            return jsonify({'error': 'Unauthorized (requires lead or support role)'}), 403

        profile_contexts.remove_member(
            db,
            context_id=context_id,
            firebase_uid=target_uid,
            removed_by_uid=uid,
        )

        return jsonify({'success': True, 'firebase_uid': target_uid, 'status': 'removed'})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        _logger.error(f"remove_context_member error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile-contexts/<context_id>/archive', methods=['POST'])
@limiter.limit("10 per minute")
def archive_context(context_id: str):
    """Archive a context (requires lead role)."""
    if not ENABLE_PROFILE_CONTEXTS or not _profile_contexts_available:
        return jsonify({'error': 'Profile contexts not enabled'}), 403

    uid = _require_firebase_user()
    db = get_db()

    try:
        # Check access (must be lead)
        if not profile_contexts.can_access_context(db, context_id, uid, min_role='lead'):
            return jsonify({'error': 'Unauthorized (requires lead role)'}), 403

        profile_contexts.archive_context(db, context_id=context_id, archived_by_uid=uid)

        return jsonify({'success': True, 'context_id': context_id, 'status': 'archived'})

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        _logger.error(f"archive_context error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Org view tracking ─────────────────────────────────────────────────────────

@app.route('/api/org/<ein>/view', methods=['POST'])
@limiter.limit("30 per minute")
def track_org_view(ein):
    """Anonymous page view counter. Called fire-and-forget by org detail page."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if len(ein) != 9:
        return '', 204
    db = get_db()
    _ensure_donor_tables(db)
    db.execute("INSERT INTO org_view_events (ein) VALUES (?)", (ein,))
    db.commit()
    return '', 204


@app.route('/api/org/<ein>/view-stats', methods=['GET'])
@limiter.limit("60 per minute")
def org_view_stats(ein):
    """Aggregate view + wallet-save counts for nonprofit dashboard. Requires claim."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if len(ein) != 9:
        return jsonify({'error': 'Invalid EIN'}), 400
    db = get_db()
    claim = db.execute(
        "SELECT 1 FROM org_claims WHERE ein=? AND firebase_uid=? "
        "AND claim_status IN ('verified','active') AND revoked_at IS NULL",
        (ein, uid),
    ).fetchone()
    if not claim:
        return jsonify({'error': 'Unauthorized'}), 403
    _ensure_donor_tables(db)
    vrow = db.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN view_date >= date('now','-30 days') THEN 1 ELSE 0 END) AS d30,
            SUM(CASE WHEN view_date >= date('now','-7 days')  THEN 1 ELSE 0 END) AS d7
        FROM org_view_events WHERE ein=?
    """, (ein,)).fetchone()
    wrow = db.execute(
        "SELECT COUNT(*) AS n FROM org_wallet_saves WHERE ein=?", (ein,)
    ).fetchone()
    return jsonify({
        'ein': ein,
        'views_total': vrow['total'] or 0,
        'views_30d':   vrow['d30']   or 0,
        'views_7d':    vrow['d7']    or 0,
        'wallet_saves': wrow['n'] if wrow else 0,
    }), 200


@app.route('/api/org/<ein>/grants', methods=['GET'])
@limiter.limit("30 per minute")
def org_grants(ein):
    """Federal grant opportunities discovered for this org. Requires claim."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if len(ein) != 9:
        return jsonify({'error': 'Invalid EIN'}), 400
    db = get_db()
    claim = db.execute(
        "SELECT 1 FROM org_claims WHERE ein=? AND firebase_uid=? "
        "AND claim_status IN ('verified','active') AND revoked_at IS NULL",
        (ein, uid),
    ).fetchone()
    if not claim:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        rows = db.execute("""
            SELECT grant_id, title, agency, close_date, cfda, url, found_at
            FROM grant_opportunities
            WHERE ein=?
            ORDER BY found_at DESC
            LIMIT 10
        """, (ein,)).fetchall()
    except Exception:
        # Table not yet created (agent hasn't run)
        return jsonify({'grants': []}), 200

    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=7)
    grants = []
    for r in rows:
        close_str = r['close_date'] or ''
        if close_str:
            try:
                close_dt = datetime.strptime(close_str, "%m/%d/%Y")
                if close_dt < cutoff:
                    continue
            except ValueError:
                pass
        grants.append({
            'grant_id': r['grant_id'],
            'title': r['title'],
            'agency': r['agency'],
            'close_date': close_str,
            'cfda': r['cfda'],
            'url': r['url'],
        })
    return jsonify({'grants': grants}), 200

@app.route('/api/org/<ein>/guild', methods=['GET'])
@limiter.limit("60 per minute")
def org_guild_membership(ein):
    """Get guild (partner) membership for an org.

    Returns: {guild_id, guild_name, slug, tier, benefits: [{tier, feature_name, description}]}
    Empty object {} if no membership.
    """
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if len(ein) != 9:
        return jsonify({}), 200

    db = get_db()

    try:
        # Query membership + guild info
        row = db.execute('''
            SELECT g.guild_id, g.name, g.slug, g.website, gm.tier
            FROM guild_membership gm
            JOIN guild g ON gm.guild_id = g.guild_id
            WHERE gm.ein=?
        ''', (ein,)).fetchone()

        if not row:
            return jsonify({}), 200

        guild_id, guild_name, slug, website, tier = row['guild_id'], row['name'], row['slug'], row['website'], row['tier']

        # Get benefits for this guild + tier
        benefits = db.execute('''
            SELECT tier, feature_name, description
            FROM guild_benefits
            WHERE guild_id=? AND tier=?
            ORDER BY tier, feature_name
        ''', (guild_id, tier)).fetchall()

        return jsonify({
            'guild_id': guild_id,
            'guild_name': guild_name,
            'slug': slug,
            'website': website,
            'tier': tier,
            'benefits': [dict(b) for b in benefits],
        }), 200

    except Exception as e:
        # Table not yet created or other error — return empty
        return jsonify({}), 200

@app.route('/api/guild/<slug>', methods=['GET'])
@limiter.limit("60 per minute")
def guild_detail(slug: str):
    """Get guild (partner) info + member organizations.

    Response: {
      guild_id, name, slug, website,
      benefits: {free: [], pro: [], enterprise: []},
      members: [{ein, organization_name, city, state}]
    }
    """
    slug = (slug or '').lower().strip()
    if not slug:
        return jsonify({'error': 'Guild not found'}), 404

    db = get_db()

    try:
        # Get guild info
        guild = db.execute(
            'SELECT guild_id, name, slug, website FROM guild WHERE slug=?',
            (slug,)
        ).fetchone()

        if not guild:
            return jsonify({'error': 'Guild not found'}), 404

        guild_id = guild['guild_id']

        # Get benefits by tier
        benefits_rows = db.execute('''
            SELECT tier, feature_name, description
            FROM guild_benefits
            WHERE guild_id=?
            ORDER BY tier, feature_name
        ''', (guild_id,)).fetchall()

        benefits = {'free': [], 'pro': [], 'enterprise': []}
        for row in benefits_rows:
            tier = row['tier']
            if tier in benefits:
                benefits[tier].append({
                    'feature_name': row['feature_name'],
                    'description': row['description'],
                })

        # Get member orgs (limit 50)
        members_rows = db.execute('''
            SELECT r.EIN, r.organization_name, r.city, r.state
            FROM guild_membership gm
            JOIN registry_enriched r ON gm.ein = r.EIN
            WHERE gm.guild_id=?
            ORDER BY r.organization_name
            LIMIT 50
        ''', (guild_id,)).fetchall()

        members = [dict(m) for m in members_rows]

        return jsonify({
            'guild_id': guild_id,
            'name': guild['name'],
            'slug': guild['slug'],
            'website': guild['website'],
            'benefits': benefits,
            'member_count': len(members),
            'members': members,
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error loading guild: {str(e)}'}), 500

@app.route('/api/wallet/init', methods=['POST'])
def e2e_wallet_init():
    """Issue a random salt for a new wallet. Salt is not secret.

    Route decorator was accidentally dropped in ffcb46f7731 (2026-06-21) —
    that commit's message explicitly lists /api/wallet/init as preserved,
    and the shipped frontend (WalletContext.tsx) still POSTs here for new
    wallet creation. Restored 2026-07-10; guarded by test_wallet_e2e.py.
    """
    import base64 as _b64
    salt = _b64.b64encode(secrets.token_bytes(16)).decode()
    return jsonify({'salt': salt})


@app.route('/api/wallet/token', methods=['POST'])
def e2e_wallet_token():
    """Issue short-lived JWT for wallet sync (security fix: no raw key bytes in browser).

    POST { keyHash }  → { token, expiresIn }

    Token is httpOnly-safe and expires in 5 minutes.
    Used by WalletContext to sync without storing raw AES key bytes in sessionStorage.
    """
    body = request.get_json(silent=True) or {}
    key_hash = body.get('keyHash', '')

    if not key_hash or len(key_hash) != 64 or not all(c in '0123456789abcdef' for c in key_hash):
        return jsonify({'error': 'invalid key_hash'}), 400

    db = get_db()
    _ensure_e2e_wallet_sync_table(db)

    # Verify wallet exists
    row = db.execute(
        'SELECT 1 FROM e2e_wallet_sync WHERE key_hash=?',
        [key_hash]
    ).fetchone()
    if not row:
        return jsonify({'error': 'wallet not found'}), 404

    # Issue JWT: payload = {keyHash, exp, iat}
    import base64 as _b64
    secret = os.environ.get('WALLET_JWT_SECRET', os.urandom(32).hex())
    now = int(time.time())
    token = _pyjwt.encode(
        {'keyHash': key_hash, 'exp': now + 300, 'iat': now},  # 5-min expiry
        secret,
        algorithm='HS256'
    )

    return jsonify({'token': token, 'expiresIn': 300})


@app.route('/api/wallet/sync', methods=['GET', 'POST', 'DELETE'])
def e2e_wallet_sync():
    """Dumb ciphertext locker. Server cannot read wallet contents.

    GET  ?keyHash=<hex64> | Authorization: Bearer <token>  → { found, ciphertext, iv, salt, updatedAt }
    POST { keyHash, ... } | Authorization: Bearer <token>  → { ok }
    DELETE { keyHash } | Authorization: Bearer <token>     → { ok }

    Supports both legacy keyHash in body + new JWT auth (security fix).
    """
    import base64 as _b64

    # Extract keyHash: try JWT first, fall back to body/query
    key_hash = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            secret = os.environ.get('WALLET_JWT_SECRET', '')
            if secret:
                payload = _pyjwt.decode(token, secret, algorithms=['HS256'])
                key_hash = payload.get('keyHash', '')
        except Exception:
            pass  # Fall through to body/query parsing

    # Fall back: extract from body/query string (legacy)
    if not key_hash:
        if request.method == 'GET':
            body = {}
            key_hash = request.args.get('keyHash', '')
        else:
            body = request.get_json(silent=True) or {}
            key_hash = body.get('keyHash', '')
    else:
        body = request.get_json(silent=True) or {}

    if not key_hash or len(key_hash) != 64 or not all(c in '0123456789abcdef' for c in key_hash):
        return jsonify({'error': 'invalid key_hash'}), 400

    db = get_db()
    _ensure_e2e_wallet_sync_table(db)

    if request.method == 'POST':
        ip = request.remote_addr or 'unknown'
        now = time.time()
        window = [t for t in _wallet_rate[ip] if now - t < 60]
        if len(window) >= _WALLET_RATE_LIMIT:
            return jsonify({'error': 'rate limit exceeded'}), 429
        _wallet_rate[ip] = window + [now]

        ct = body.get('ciphertext', '')
        iv = body.get('iv', '')
        salt = body.get('salt', '')
        if not ct or not iv or not salt:
            return jsonify({'error': 'missing fields'}), 400
        if len(ct) > _WALLET_MAX_BYTES:
            return jsonify({'error': 'payload too large'}), 400

        db.execute(
            'INSERT INTO e2e_wallet_sync (key_hash, ciphertext, iv, salt, updated_at)'
            ' VALUES (?, ?, ?, ?, ?)'
            ' ON CONFLICT(key_hash) DO UPDATE SET'
            ' ciphertext=excluded.ciphertext, iv=excluded.iv, updated_at=excluded.updated_at',
            [key_hash, ct, iv, salt, int(time.time())]
        )
        db.commit()
        return jsonify({'ok': True})

    if request.method == 'DELETE':
        db.execute('DELETE FROM e2e_wallet_sync WHERE key_hash=?', [key_hash])
        db.commit()
        return jsonify({'ok': True})

    # GET
    row = db.execute(
        'SELECT ciphertext, iv, salt, updated_at FROM e2e_wallet_sync WHERE key_hash=?',
        [key_hash]
    ).fetchone()
    if not row:
        return jsonify({'found': False}), 404
    return jsonify({'found': True, 'ciphertext': row[0], 'iv': row[1],
                    'salt': row[2], 'updatedAt': row[3]})


def _lean_entry(entry: dict) -> dict:
    """Strip deprecated/derived fields — only persist what's needed for cross-device restore."""
    lean: dict = {
        'ein': entry.get('ein', ''),
        'bookmarkedAt': entry.get('bookmarkedAt', 0),
    }
    if entry.get('inFunding') is not None:
        lean['inFunding'] = bool(entry['inFunding'])
    if entry.get('inVolunteering') is not None:
        lean['inVolunteering'] = bool(entry['inVolunteering'])
    if entry.get('donations'):
        lean['donations'] = [
            {
                'id': d.get('id', ''),
                'amount': d.get('amount', 0),
                'date': d.get('date', ''),
                'notes': d.get('notes', '') or '',
                'helpedDaanaa': bool(d.get('helpedDaanaa', False)),
                'letterRequested': bool(d.get('letterRequested', False)),
            }
            for d in entry['donations'] if d.get('id') and d.get('amount')
        ]
    if entry.get('volunteerHours'):
        lean['volunteerHours'] = [
            {
                'id': v.get('id', ''),
                'hours': v.get('hours', 0),
                'date': v.get('date', ''),
                'notes': v.get('notes', '') or '',
                'helpedDaanaa': bool(v.get('helpedDaanaa', False)),
            }
            for v in entry['volunteerHours'] if v.get('id') and v.get('hours')
        ]
    return lean


def _get_dynamo_table():
    """Return DynamoDB Table resource. Raises if not configured."""
    import boto3
    region = os.environ.get('AWS_REGION', 'us-east-1')
    table_name = os.environ.get('WALLET_DYNAMO_TABLE', 'daanaa_wallets')
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=region,
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    )
    return dynamodb.Table(table_name)


def _firebase_uid_from_request() -> str:
    """Verify Firebase ID token from Authorization header, return uid."""
    from firebase_admin import auth as fb_auth
    token = request.headers.get('Authorization', '').split(' ')[-1]
    if not token:
        raise ValueError('missing token')
    decoded = fb_auth.verify_id_token(token)
    return decoded['uid']


@app.route('/api/wallet/backup', methods=['POST'])
def backup_wallet():
    """Back up wallet to DynamoDB (lean format, Firebase auth required)."""
    user_id = _require_firebase_user()

    data = request.json or {}
    raw_entries = data.get('entries', [])
    if not raw_entries:
        return jsonify({'error': 'No entries to backup'}), 400

    lean = [_lean_entry(e) for e in raw_entries if e.get('ein')]
    backed_at = datetime.now().isoformat()

    try:
        table = _get_dynamo_table()
        table.put_item(Item={
            'user_id': user_id,
            'entries': json.dumps(lean, separators=(',', ':')),
            'entry_count': len(lean),
            'updated_at': backed_at,
            'version': 1,
        })
        return jsonify({'success': True, 'backed_up_at': backed_at, 'entry_count': len(lean)}), 200
    except Exception as dynamo_err:
        # Fallback: SQLite (local dev / DynamoDB not yet provisioned)
        logging.warning('DynamoDB backup failed, falling back to SQLite: %s', dynamo_err)
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS wallet_backups (
                    user_id TEXT PRIMARY KEY,
                    entries TEXT NOT NULL,
                    backed_up_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute(
                'INSERT OR REPLACE INTO wallet_backups (user_id, entries, backed_up_at) VALUES (?, ?, ?)',
                (user_id, json.dumps(lean), backed_at),
            )
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'backed_up_at': backed_at, 'entry_count': len(lean)}), 200
        except Exception as e:
            return jsonify({'error': f'Backup failed: {e}'}), 500


@app.route('/api/wallet/restore', methods=['GET'])
def restore_wallet():
    """Restore wallet from DynamoDB (Firebase auth required)."""
    user_id = _require_firebase_user()

    try:
        table = _get_dynamo_table()
        resp = table.get_item(Key={'user_id': user_id})
        item = resp.get('Item')
        if not item:
            return jsonify({'entries': [], 'found': False}), 200
        entries = json.loads(item['entries'])
        return jsonify({'entries': entries, 'found': True, 'updated_at': item.get('updated_at')}), 200
    except Exception as dynamo_err:
        # Fallback: SQLite
        logging.warning('DynamoDB restore failed, falling back to SQLite: %s', dynamo_err)
        try:
            conn = sqlite3.connect(DB_PATH)
            row = conn.execute('SELECT entries FROM wallet_backups WHERE user_id = ?', (user_id,)).fetchone()
            conn.close()
            if not row:
                return jsonify({'entries': [], 'found': False}), 200
            entries = json.loads(row[0])
            return jsonify({'entries': entries, 'found': True}), 200
        except Exception as e:
            return jsonify({'error': f'Restore failed: {e}'}), 500


@app.route('/api/wallet/donation-receipt', methods=['POST'])
def generate_donation_receipt():
    """Disabled: Daanaa does not issue tax receipts. Receipts come from the nonprofit directly."""
    return jsonify({
        'error': 'Daanaa does not generate tax receipts. '
                 'Contact the nonprofit directly for an official acknowledgment letter.'
    }), 410

def _generate_donation_receipt_disabled():
    """Archived: was generating IRS receipt PDFs from user-supplied wallet data without
    verifying the donation occurred. Disabled — see DECISIONS.md 2026-07-02."""
    try:
        from scripts.letter_generator import generate_donation_letter

        data = request.json or {}
        org_name = data.get('org_name', '').strip()
        ein = data.get('ein', '').strip()
        amount = data.get('amount', 0)
        donation_date = data.get('date', '').strip()
        donor_name = data.get('donor_name', 'Honored Donor').strip()

        if not all([org_name, ein, amount, donation_date]):
            return jsonify({'error': 'Missing required fields'}), 400

        pdf_bytes = generate_donation_letter(
            nonprofit_name=org_name,
            nonprofit_ein=ein,
            donor_name=donor_name,
            amount=amount,
            donation_date=donation_date,
            nonprofit_address=org_name
        )

        from io import BytesIO
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'receipt_{ein}_{donation_date.split("T")[0]}.pdf'
        )
    except ImportError:
        return jsonify({'error': 'PDF generation service unavailable'}), 503
    except Exception as e:
        return jsonify({'error': f'Failed to generate receipt: {str(e)}'}), 500


# ── Community Impact Logging ───────────────────────────────────────────────────

@app.route('/api/impact/log', methods=['POST'])
@limiter.limit("100 per hour")
def log_impact():
    """Log opted-in giving/volunteer activity for community impact tracking.

    No user ID required—anonymous. Donation/volunteer is logged server-side
    for daily aggregation and monthly community reporting.

    Payload:
      - ein: str (9-digit)
      - type: 'giving' | 'volunteer'
      - amount: int (cents) — for giving only
      - hours: float — for volunteer only
      - date: str (ISO date)
    """
    try:
        data = request.get_json()
        ein = data.get('ein', '').strip()
        log_type = data.get('type', '').lower()
        amount = data.get('amount')
        hours = data.get('hours')
        log_date = data.get('date', datetime.now().isoformat().split('T')[0])

        # Validation
        if not ein or not re.match(r'^\d{9}$', ein):
            return jsonify({'error': 'Invalid EIN'}), 400
        if log_type not in ('giving', 'volunteer'):
            return jsonify({'error': 'Invalid type'}), 400
        if log_type == 'giving' and (not isinstance(amount, (int, float)) or amount < 1):
            return jsonify({'error': 'Invalid amount'}), 400
        if log_type == 'volunteer' and (not isinstance(hours, (int, float)) or hours < 0.25):
            return jsonify({'error': 'Invalid hours'}), 400

        # Insert into impact_logs. Schema note: org_ein/impact_type/amount are
        # NOT NULL legacy columns and id is INTEGER AUTOINCREMENT — the old
        # INSERT here supplied a TEXT id and skipped the NOT NULLs, so every
        # wallet impact sync failed with a datatype/constraint error.
        # source='wallet_optin' distinguishes these from the nonprofit-approved
        # bridge records (source='volunteer_hours_event').
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        numeric_value = amount if log_type == 'giving' else hours

        cursor.execute('''
            INSERT INTO impact_logs (org_ein, impact_type, amount, ein, type, hours, log_date, source, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'wallet_optin', 0)
        ''', (ein, log_type, numeric_value, ein, log_type,
              hours if log_type == 'volunteer' else None, log_date))
        log_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'log_id': log_id}), 201
    except Exception as e:
        logging.error(f'Impact log error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/impact/community-stats', methods=['GET'])
@limiter.limit("100 per hour")
def get_community_stats():
    """Get aggregated community impact stats (updated daily)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get latest aggregate (today or most recent date)
        cursor.execute('''
            SELECT total_dollars, total_hours, donation_count, volunteer_count,
                   org_count, active_volunteers, aggregate_date
            FROM impact_aggregates
            ORDER BY aggregate_date DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()

        if not row:
            # No aggregates yet — compute from raw logs
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                  COALESCE(SUM(amount), 0) as total_dollars,
                  COALESCE(SUM(hours), 0) as total_hours,
                  SUM(CASE WHEN type='giving' THEN 1 ELSE 0 END) as donation_count,
                  SUM(CASE WHEN type='volunteer' THEN 1 ELSE 0 END) as volunteer_count,
                  COUNT(DISTINCT ein) as org_count
                FROM impact_logs
            ''')
            stats_row = cursor.fetchone()
            conn.close()
            if stats_row:
                total_dollars, total_hours, donation_count, volunteer_count, org_count = stats_row
                from volunteer_hours_events_api import VOLUNTEER_HOURLY_VALUE
                volunteer_hourly_value = VOLUNTEER_HOURLY_VALUE  # single documented source
                lifetime_value = total_dollars + int(total_hours * volunteer_hourly_value)
                return jsonify({
                    'total_dollars': total_dollars or 0,
                    'total_hours': round(total_hours or 0, 2),
                    'donation_count': donation_count or 0,
                    'volunteer_count': volunteer_count or 0,
                    'org_count': org_count or 0,
                    'active_volunteers': volunteer_count or 0,
                    'lifetime_value': lifetime_value,
                    'as_of_date': datetime.now().isoformat().split('T')[0],
                }), 200
            else:
                return jsonify({
                    'total_dollars': 0, 'total_hours': 0, 'donation_count': 0,
                    'volunteer_count': 0, 'org_count': 0, 'active_volunteers': 0,
                    'lifetime_value': 0, 'as_of_date': datetime.now().isoformat().split('T')[0],
                }), 200

        total_dollars, total_hours, donation_count, volunteer_count, org_count, active_volunteers, aggregate_date = row
        from volunteer_hours_events_api import VOLUNTEER_HOURLY_VALUE
        volunteer_hourly_value = VOLUNTEER_HOURLY_VALUE  # single documented source
        lifetime_value = total_dollars + int(total_hours * volunteer_hourly_value)

        return jsonify({
            'total_dollars': total_dollars,
            'total_hours': round(total_hours, 2),
            'donation_count': donation_count,
            'volunteer_count': volunteer_count,
            'org_count': org_count,
            'active_volunteers': active_volunteers,
            'lifetime_value': lifetime_value,
            'as_of_date': aggregate_date,
        }), 200
    except Exception as e:
        logging.error(f'Community stats error: {e}')
        return jsonify({'error': str(e)}), 500


# ── Nonprofit Dashboard: Donor Interest Analytics ────────────────────────────

@app.route('/api/wallet/report-bookmark', methods=['POST'])
def report_bookmark():
    """
    Anonymous opt-in bookmark analytics collection.

    Clients call this when a user bookmarks an org to populate the nonprofit
    dashboard with donor interest metrics. Completely anonymized, no user tracking,
    respects privacy-first design (Stewardship Principle #2).

    POST body: { "ein": "123456789", "causes": ["Food Justice", "Community Empowerment"],
                 "state": "CA", "city": "San Francisco" }
    """
    try:
        data = request.get_json() or {}
        ein = data.get('ein', '').strip()
        causes = data.get('causes', []) or []
        state = data.get('state', 'XX')[:2].upper()
        city = data.get('city', 'Unknown')[:50]

        if not ein or len(ein) != 9 or not ein.isdigit():
            return jsonify({'error': 'Invalid EIN'}), 400

        db = get_db()
        cursor = db.cursor()

        # wallet_analytics has no UNIQUE constraints, so ON CONFLICT upserts
        # are rejected by SQLite — use update-then-insert instead.

        # Record root bookmark (for org total count)
        updated = cursor.execute('''
            UPDATE wallet_analytics
               SET bookmark_count = bookmark_count + 1,
                   last_updated = CURRENT_TIMESTAMP
             WHERE ein = ? AND cause_tag IS NULL AND location_state IS NULL
        ''', (ein,)).rowcount
        if updated == 0:
            cursor.execute(
                'INSERT INTO wallet_analytics (ein, bookmark_count) VALUES (?, 1)',
                (ein,))

        # Record by cause (if causes provided)
        for cause in causes[:5]:  # Max 5 causes per bookmark to prevent spam
            cause = str(cause).strip()[:100]
            if cause:
                updated = cursor.execute('''
                    UPDATE wallet_analytics
                       SET bookmark_count = bookmark_count + 1,
                           last_updated = CURRENT_TIMESTAMP
                     WHERE ein = ? AND cause_tag = ?
                ''', (ein, cause)).rowcount
                if updated == 0:
                    cursor.execute(
                        'INSERT INTO wallet_analytics (ein, cause_tag, bookmark_count) VALUES (?, ?, 1)',
                        (ein, cause))

        # Record by location (if provided)
        if state != 'XX' and city != 'Unknown':
            updated = cursor.execute('''
                UPDATE wallet_analytics
                   SET bookmark_count = bookmark_count + 1,
                       last_updated = CURRENT_TIMESTAMP
                 WHERE ein = ? AND location_state = ? AND location_city = ?
            ''', (ein, state, city)).rowcount
            if updated == 0:
                cursor.execute(
                    'INSERT INTO wallet_analytics (ein, location_state, location_city, bookmark_count) VALUES (?, ?, ?, 1)',
                    (ein, state, city))

        db.commit()
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        _logger.error(f'Bookmark report error: {e}')
        return jsonify({'error': 'Failed to record bookmark'}), 500


@app.route('/api/nonprofit/<ein>/volunteer/submit', methods=['POST'])
@limiter.limit("30 per hour")
def nonprofit_volunteer_submit(ein: str):
    """Submit volunteer hours for approval.

    Request: {volunteer_name, volunteer_email, hours, service_date, activity_description}
    Response: {claim_code, claim_url}
    """
    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]

    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    # Verify ownership
    db = get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid)
    ).fetchone()

    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    data = request.get_json(silent=True) or {}
    name = (data.get('volunteer_name') or '').strip()
    email = (data.get('volunteer_email') or '').strip()
    hours = float(data.get('hours') or 0)
    service_date = (data.get('service_date') or '').strip()
    activity = (data.get('activity_description') or '').strip()

    if not all([name, email, hours > 0, service_date, activity]):
        return jsonify({'error': 'All fields required'}), 400

    import uuid
    claim_code = f"VOL-{uuid.uuid4().hex[:12].upper()}"

    try:
        db.execute('''
            INSERT INTO volunteer_hours (
                id, nonprofit_ein, volunteer_name, volunteer_email,
                hours, service_date, activity_description, status, submitted_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        ''', (claim_code, ein, name, email, hours, service_date, activity,
              datetime.now().isoformat(), datetime.now().isoformat()))
        db.commit()

        # Record intent signal: volunteer expressed interest
        if _intent_available:
            try:
                intent_layer.record_intent(db, kind='volunteer', source='volunteer_submission', ein=ein)
            except Exception as intent_err:
                _logger.warning(f"Intent recording failed (non-fatal): {intent_err}")
    except Exception as e:
        return jsonify({'error': f'Submit failed: {str(e)}'}), 500

    return jsonify({'claim_code': claim_code, 'claim_url': f'https://daanaa.org/volunteer/claim?code={claim_code}'}), 201

@app.route('/api/volunteer/claim', methods=['POST'])
@limiter.limit("30 per hour")
def volunteer_claim_hours():
    """Volunteer claims hours they completed.

    Request: {code, email}
    Response: {status: 'claimed'}
    """
    data = request.get_json(silent=True) or {}
    code = (data.get('code') or '').strip()
    email = (data.get('email') or '').strip()

    if not code or not email:
        return jsonify({'error': 'Code and email required'}), 400

    db = get_db()
    hours = db.execute(
        'SELECT id, nonprofit_ein, volunteer_email FROM volunteer_hours WHERE id=?',
        (code,)
    ).fetchone()

    if not hours:
        return jsonify({'error': 'Invalid claim code'}), 404

    if hours['volunteer_email'].lower() != email.lower():
        return jsonify({'error': 'Email does not match'}), 403

    try:
        db.execute(
            'UPDATE volunteer_hours SET status=? WHERE id=?',
            ('confirmed', code)
        )
        db.commit()

        # Record intent: volunteer action started (hours claimed)
        if _intent_available:
            try:
                intent_layer.record_intent(db, kind='volunteer', source='volunteer_claim', ein=hours['nonprofit_ein'], evidence={'claim_code': code})
            except Exception as intent_err:
                _logger.warning(f"Intent recording failed (non-fatal): {intent_err}")
    except Exception as e:
        return jsonify({'error': f'Claim failed: {str(e)}'}), 500

    return jsonify({'status': 'claimed', 'message': 'Hours claimed. Nonprofit will review.'}), 200

@app.route('/api/nonprofit/<ein>/volunteer/pending', methods=['GET'])
def nonprofit_pending_approvals(ein: str):
    """Get pending volunteer hours awaiting nonprofit approval.

    Response: [{id, volunteer_name, volunteer_email, hours, service_date, activity_description, status}]
    """
    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]

    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid)
    ).fetchone()

    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    hours = db.execute('''
        SELECT id, volunteer_name, volunteer_email, hours, service_date, activity_description, status
        FROM volunteer_hours
        WHERE nonprofit_ein=? AND status IN ("confirmed", "pending")
        ORDER BY submitted_at DESC
    ''', (ein,)).fetchall()

    return jsonify([dict(h) for h in hours]), 200

@app.route('/api/nonprofit/<ein>/volunteer/<hour_id>/approve', methods=['POST'])
@limiter.limit("60 per hour")
def nonprofit_approve_hours(ein: str, hour_id: str):
    """Approve submitted volunteer hours."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]

    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid)
    ).fetchone()

    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    try:
        row = db.execute(
            'SELECT hours, service_date, status, locked_at FROM volunteer_hours WHERE id=? AND nonprofit_ein=?',
            (hour_id, ein)
        ).fetchone()
        if not row:
            return jsonify({'error': 'Submission not found'}), 404
        if row['status'] == 'approved':
            # Idempotent: double-click / retry never re-bridges a second
            # aggregate impact record (and _bridge_to_impact_logs is itself
            # keyed on hour_id as a second line of defense).
            return jsonify({'status': 'approved', 'already_approved': True}), 200
        # locked_at stores the FUTURE date the record becomes immutable
        # (set to approval time + 30 days); locked only once that date passes.
        if row['locked_at'] and row['locked_at'] <= datetime.now().isoformat():
            return jsonify({'error': 'This submission is locked (30-day edit window has passed)'}), 409

        approved_at = datetime.now().isoformat()
        db.execute(
            'UPDATE volunteer_hours SET status=?, approved_by=?, approved_at=?, '
            'locked_at=? WHERE id=? AND nonprofit_ein=?',
            ('approved', uid, approved_at,
             (datetime.now() + timedelta(days=30)).isoformat(), hour_id, ein)
        )
        try:
            from volunteer_hours_events_api import _audit, _bridge_to_impact_logs
            _audit(db, hour_id, 'approved', uid)
            _bridge_to_impact_logs(db, ein, row['hours'], row['service_date'], hour_id)
        except ImportError:
            pass  # volunteer_hours_events_api optional

        # Queue approval notification (after commit)
        db.commit()

        # Record intent: volunteer action verified (nonprofit approved hours)
        if _intent_available:
            try:
                intent_layer.record_intent(db, kind='volunteer', source='volunteer_approval', ein=ein, evidence={'hours': row['hours'], 'hour_id': hour_id})
            except Exception as intent_err:
                _logger.warning(f"Intent recording failed (non-fatal): {intent_err}")

        try:
            from volunteer_notifications import create_approval_notification
            full_hour = db.execute(
                'SELECT volunteer_email, hours, service_date FROM volunteer_hours WHERE id=?',
                (hour_id,)
            ).fetchone()
            if full_hour:
                full_org = db.execute("SELECT organization_name FROM registry_enriched WHERE EIN=?", (ein,)).fetchone()
                org_name = (full_org["organization_name"] if full_org else None) or "Organization"
                create_approval_notification(db, hour_id, full_hour["volunteer_email"],
                                             ein, org_name, full_hour["hours"],
                                             full_hour["service_date"], is_test=False)
        except ImportError:
            pass  # volunteer_notifications optional
    except Exception as e:
        return jsonify({'error': f'Approval failed: {str(e)}'}), 500

    return jsonify({'status': 'approved'}), 200

@app.route('/api/nonprofit/<ein>/volunteer/<hour_id>/reject', methods=['POST'])
@limiter.limit("60 per hour")
def nonprofit_reject_hours(ein: str, hour_id: str):
    """Reject submitted volunteer hours."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]

    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip()

    db = get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid)
    ).fetchone()

    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    try:
        row = db.execute(
            'SELECT status, locked_at FROM volunteer_hours WHERE id=? AND nonprofit_ein=?',
            (hour_id, ein)
        ).fetchone()
        if not row:
            return jsonify({'error': 'Submission not found'}), 404
        # locked_at is the future immutability date (approval + 30 days);
        # rejection is blocked only after that window has actually passed.
        if row['locked_at'] and row['locked_at'] <= datetime.now().isoformat():
            return jsonify({'error': 'This submission is locked (30-day edit window has passed)'}), 409

        db.execute(
            'UPDATE volunteer_hours SET status=?, rejected_by=?, rejected_at=?, rejection_reason=? WHERE id=? AND nonprofit_ein=?',
            ('rejected', uid, datetime.now().isoformat(), reason, hour_id, ein)
        )
        try:
            from volunteer_hours_events_api import _audit, _unbridge_from_impact_logs
            _audit(db, hour_id, 'rejected', uid, {'reason': reason} if reason else None)
            # If this submission was previously approved, its aggregate impact
            # record must be withdrawn — rejected hours contribute nothing.
            _unbridge_from_impact_logs(db, hour_id)
        except ImportError:
            pass  # volunteer_hours_events_api optional

        # Queue rejection notification (after commit)
        db.commit()
        try:
            from volunteer_notifications import create_rejection_notification
            full_hour = db.execute(
                'SELECT volunteer_email FROM volunteer_hours WHERE id=?',
                (hour_id,)
            ).fetchone()
            if full_hour:
                full_org = db.execute("SELECT organization_name FROM registry_enriched WHERE EIN=?", (ein,)).fetchone()
                org_name = (full_org["organization_name"] if full_org else None) or "Organization"
                create_rejection_notification(db, hour_id, full_hour["volunteer_email"],
                                              ein, org_name, reason, is_test=False)
        except ImportError:
            pass  # volunteer_notifications optional
    except Exception as e:
        return jsonify({'error': f'Rejection failed: {str(e)}'}), 500

    return jsonify({'status': 'rejected'}), 200


# ── DASHBOARD V2 ENDPOINTS ──────────────────────────────────────────────────

@app.route('/api/nonprofit/<ein>/volunteer/analytics', methods=['GET'])
@limiter.limit("60 per hour")
def nonprofit_volunteer_analytics(ein: str):
    """Analytics data for dashboard V2: trends, retention, impact."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]

    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid)
    ).fetchone()

    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    timeframe = request.args.get('timeframe', '6m')
    months_back = {'3m': 3, '6m': 6, '1y': 12}.get(timeframe, 6)

    # Hours by month (last N months)
    hours_by_month = db.execute(f'''
        SELECT
            strftime('%Y-%m', service_date) as month,
            SUM(hours) as total
        FROM volunteer_hours
        WHERE nonprofit_ein=? AND status='approved'
          AND service_date >= date('now', '-{months_back} months')
        GROUP BY month
        ORDER BY month
    ''', (ein,)).fetchall()

    # Hours by task type (all time)
    hours_by_task = db.execute('''
        SELECT
            COALESCE(task_type, 'other') as task_type,
            SUM(hours) as total
        FROM volunteer_hours
        WHERE nonprofit_ein=? AND status='approved'
        GROUP BY task_type
        ORDER BY total DESC
    ''', (ein,)).fetchall()

    # New volunteers by month
    volunteer_growth = db.execute(f'''
        SELECT
            strftime('%Y-%m', MIN(submitted_at)) as month,
            COUNT(DISTINCT volunteer_email) as count
        FROM volunteer_hours
        WHERE nonprofit_ein=? AND status='approved'
          AND submitted_at >= date('now', '-{months_back} months')
        GROUP BY month
        ORDER BY month
    ''', (ein,)).fetchall()

    # Retention rate (volunteers with 2+ submissions)
    all_volunteers = db.execute(
        'SELECT COUNT(DISTINCT volunteer_email) FROM volunteer_hours WHERE nonprofit_ein=? AND status="approved"',
        (ein,)
    ).fetchone()[0]

    returning = db.execute(
        'SELECT COUNT(DISTINCT volunteer_email) FROM (SELECT volunteer_email, COUNT(*) as cnt FROM volunteer_hours WHERE nonprofit_ein=? AND status="approved" GROUP BY volunteer_email HAVING cnt > 1)',
        (ein,)
    ).fetchone()[0]

    retention_rate = (returning / all_volunteers * 100) if all_volunteers > 0 else 0

    # Avg hours per volunteer
    avg_hours = db.execute(
        'SELECT AVG(hours) FROM (SELECT SUM(hours) as hours FROM volunteer_hours WHERE nonprofit_ein=? AND status="approved" GROUP BY volunteer_email)',
        (ein,)
    ).fetchone()[0] or 0

    return jsonify({
        'data': {
            'hours_by_month': [{'label': r['month'], 'value': r['total'] or 0} for r in hours_by_month],
            'hours_by_task_type': [{'label': r['task_type'], 'value': r['total'] or 0} for r in hours_by_task],
            'volunteer_growth': [{'label': r['month'], 'value': r['count'] or 0} for r in volunteer_growth],
            'retention_rate': retention_rate,
            'avg_hours_per_volunteer': avg_hours,
        }
    }), 200


@app.route('/api/nonprofit/<ein>/volunteer/directory', methods=['GET'])
@limiter.limit("60 per hour")
def nonprofit_volunteer_directory(ein: str):
    """Volunteer directory: all volunteers with stats."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]

    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid)
    ).fetchone()

    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    # Get all volunteers with their stats
    volunteers = db.execute('''
        SELECT
            volunteer_email as email,
            volunteer_name as name,
            SUM(hours) as total_hours,
            COUNT(*) as submissions_count,
            MAX(service_date) as last_service_date,
            CASE WHEN MAX(service_date) >= date('now', '-30 days') THEN 'active' ELSE 'inactive' END as status,
            GROUP_CONCAT(DISTINCT COALESCE(task_type, 'other')) as task_types
        FROM volunteer_hours
        WHERE nonprofit_ein=? AND status='approved'
        GROUP BY volunteer_email
        ORDER BY total_hours DESC
    ''', (ein,)).fetchall()

    return jsonify({
        'data': [{
            'email': v['email'],
            'name': v['name'],
            'total_hours': v['total_hours'] or 0,
            'submissions_count': v['submissions_count'] or 0,
            'last_service_date': v['last_service_date'],
            'status': v['status'],
            'avg_task_type': v['task_types'].split(',')[0] if v['task_types'] else 'other'
        } for v in volunteers]
    }), 200


@app.route('/api/nonprofit/dashboard/<claim_token>', methods=['GET'])
def nonprofit_dashboard_legacy(claim_token: str):
    """Legacy base64-token route, permanently retired (weak auth). Use POST
    /api/nonprofit/dashboard with EIN + verification_token instead."""
    return jsonify({'error': 'This endpoint has been replaced',
                    'use': 'POST /api/nonprofit/dashboard'}), 410


def _dashboard_financial_narrative(row) -> str:
    """Encouraging, honest framing of the org's financial context.

    Board condition (2026-07-13): the narrative encourages and never wounds.
    Facts are never hidden — the signal and numbers ship alongside — but the
    language is mission-aligned: nonprofits run lean by design. "Need support"
    invites action; "caution" shames for healthy behavior.
    """
    signal = row['merit_health_signal_v5'] or 'UNKNOWN'
    band = row['merit_band_v5_label'] or 'your size group'
    archetype = row['merit_archetype_v5_label'] or 'your funding model'
    peers = row['merit_peer_count_v5'] or 0
    peer_phrase = f"compared with {peers} organizations that share your funding model and size" if peers else "within your peer group"

    if signal == 'HEALTHY':
        return (f"Your finances show a healthy pattern {peer_phrase}. "
                f"As a {archetype} organization in the {band} range, your "
                "fundamentals are working — steady resources supporting steady "
                "mission work. That consistency is worth naming: it is rarer "
                "than it looks.")
    if signal == 'STABLE':
        return (f"Your finances show a steady pattern {peer_phrase}. "
                f"{archetype} organizations in the {band} range often run "
                "close to their means, and holding stable there takes real "
                "discipline. You are keeping the mission funded — that is the "
                "job, and you are doing it.")
    if signal in ('CAUTION', 'NEED_SUPPORT', 'MAY_NEED_SUPPORT'):
        return (f"Your organization is ready for more supporters {peer_phrase}. "
                f"Many {archetype} organizations in the {band} range are "
                "growing their mission work and actively seeking supporters like "
                "you. Your peer view shows how similar organizations reach supporters, "
                "and your profile tools help more people discover your work.")
    return (f"We don't have enough recent public financial data to describe "
            f"your position {peer_phrase}. That is a data gap, not a judgment — "
            "many organizations your size file simplified returns.")


@app.route('/api/nonprofit/dashboard', methods=['POST'])
@limiter.limit("30 per minute")
def nonprofit_self_dashboard():  # 'nonprofit_dashboard' endpoint name is taken
                                 # by the dormant portal stub (GET 401)
    """Self-discovery dashboard for verified claimants (pilot core surface).

    Financial context in plain language, peer context (public Tier 1 data
    only), donor interest aggregates, profile completeness. Auth matches
    /api/claim/update: EIN + verification token.
    """
    data  = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('verification_token') or '').strip()[:64]
    if not ein or not token:
        return jsonify({'error': 'EIN and verification_token required'}), 400

    db = get_db()
    claim, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    org = db.execute(
        """SELECT organization_name, CITY, STATE, NTEE1, total_revenue,
                  mission, website, website_status, donate_url,
                  donate_url_status, is_hidden_gem,
                  merit_score_v5, merit_archetype_v5_label, merit_band_v5_label,
                  merit_health_signal_v5, merit_peer_group_v5, merit_peer_count_v5
           FROM registry_enriched WHERE EIN = ?""", (ein,)).fetchone()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    # ── Financial context (Tier 1, plain language) ────────────────────────
    financial_context = {
        'health_signal': org['merit_health_signal_v5'],
        'archetype': org['merit_archetype_v5_label'],
        'band': org['merit_band_v5_label'],
        'peer_count': org['merit_peer_count_v5'],
        'is_hidden_gem': bool(org['is_hidden_gem']),
        'narrative': _dashboard_financial_narrative(org),
    }

    # ── Peer context: up to 5 orgs in the same peer cell, public data only ─
    peers = []
    if org['merit_peer_group_v5']:
        rows = db.execute(
            """SELECT organization_name, CITY, STATE, total_revenue,
                      merit_health_signal_v5, website
               FROM registry_enriched
               WHERE merit_peer_group_v5 = ? AND EIN != ?
               ORDER BY ABS(COALESCE(total_revenue,0) - ?) LIMIT 5""",
            (org['merit_peer_group_v5'], ein, org['total_revenue'] or 0)
        ).fetchall()
        peers = [{
            'name': r['organization_name'],
            'city': r['CITY'], 'state': r['STATE'],
            'revenue': r['total_revenue'],
            'health_signal': r['merit_health_signal_v5'],
            'website': r['website'],
        } for r in rows]
    peer_context = {
        'peers': peers,
        'note': ('These are organizations with your funding model and size, '
                 'closest to you in revenue — from public IRS data, shown for '
                 'context, not competition.'),
    }

    # ── Donor interest: aggregate bookmarks (graceful when table absent) ───
    bookmarks_now = bookmarks_prev = 0
    try:
        bookmarks_now = db.execute(
            "SELECT COALESCE(SUM(bookmark_count),0) FROM wallet_analytics "
            "WHERE ein=? AND last_updated >= date('now','start of month')",
            (ein,)).fetchone()[0]
        bookmarks_prev = db.execute(
            "SELECT COALESCE(SUM(bookmark_count),0) FROM wallet_analytics "
            "WHERE ein=? AND last_updated >= date('now','-1 month','start of month') "
            "AND last_updated < date('now','start of month')",
            (ein,)).fetchone()[0]
    except sqlite3.OperationalError:
        pass
    donor_interest = {
        'bookmarks_this_month': bookmarks_now,
        'bookmarks_last_month': bookmarks_prev,
        'note': ('Bookmarks are anonymous, aggregate counts of people saving '
                 'your organization on Daanaa. They signal interest, not '
                 'commitments — a starting point, not a promise.'),
    }

    # ── Profile completeness: actionable, encouraging ─────────────────────
    # Donor-visible statuses are beta/claimed (the same gate the org page
    # uses — see frontend actionRow.ts). The old check required 'verified',
    # a value that never occurs in production, so every org was told its
    # working donate link was unconfirmed (bug found 2026-07-17).
    donate_live = (org['donate_url_status'] in ('beta', 'claimed', 'verified')
                   and bool(org['donate_url']))
    checks = {
        'mission': bool(org['mission'] or claim['custom_mission']),
        'website_verified': org['website_status'] == 'ok',
        'donate_link_verified': donate_live,
    }
    missing = [k for k, v in checks.items() if not v]
    if not missing:
        profile_narrative = ('Your public profile is complete — mission, '
                             'website, and donation link are all verified. '
                             'Donors who find you can act on what they find.')
    else:
        friendly = {'mission': 'a mission statement in your own words',
                    'website_verified': 'a confirmed website',
                    'donate_link_verified': 'a confirmed donation link'}
        profile_narrative = ('One small step with real payoff: adding ' +
                             ' and '.join(friendly[m] for m in missing) +
                             ' helps donors who discover you take the next '
                             'step with confidence.')
    profile = {'checks': checks, 'narrative': profile_narrative}

    # ── Page health: exactly what a donor sees and whether it works ───────
    # Mirrors the donor-side rendering gates so the org sees the truth of
    # its own public page, not internal pipeline states.
    website_shown = (org['website_status'] == 'ok'
                     or (bool(org['website']) and org['website_status'] is None))
    page_health = {
        'public_page_url': f"https://daanaa.org/org/{ein}",
        'mission': {
            'shown': bool(org['mission'] or claim['custom_mission']),
            'text': (claim['custom_mission'] or org['mission'] or None),
            'source': ('yours' if claim['custom_mission'] else
                       'derived from public records' if org['mission'] else None),
        },
        'website': {
            'url': org['website'],
            'shown_to_donors': website_shown,
            'status': org['website_status'],
        },
        'donate_link': {
            'url': org['donate_url'],
            'shown_to_donors': donate_live,
            'status': org['donate_url_status'],
            'note': ('Donors see a Donate button that goes straight to this '
                     'link — money never passes through Daanaa.'
                     if donate_live else
                     'No donation link is live on your page yet. Donors see '
                     'your EIN and mailing address instead, so they can still '
                     'give by check or through their own bank or fund.'),
        },
    }

    return jsonify({
        'ein': ein,
        'organization_name': org['organization_name'],
        'page_health': page_health,
        'financial_context': financial_context,
        'peer_context': peer_context,
        'donor_interest': donor_interest,
        'profile': profile,
        'derived_data': ('See what our AI derived about you, and correct it, '
                         'via POST /api/claim/ai-derived'),
    })


@app.route('/api/email/unsubscribe', methods=['GET', 'POST'])
@limiter.limit("30 per minute")
def email_unsubscribe():
    """One-click unsubscribe (RFC 8058) — listmonk-learned compliance layer.

    GET renders a tiny confirm page and NEVER unsubscribes (mail scanners
    prefetch GET links; auto-unsubscribing on GET silently removes real
    subscribers). POST — from the confirm button or a mail client's
    one-click header — verifies the HMAC token and suppresses the address.
    """
    from email_service import verify_unsubscribe_token, suppress_email
    email = (request.args.get('e') or '').strip().lower()[:254]
    token = (request.args.get('t') or '').strip()[:64]
    if not email or not token:
        return jsonify({'error': 'missing e or t'}), 400
    if not verify_unsubscribe_token(email, token):
        return jsonify({'error': 'invalid token'}), 403

    if request.method == 'GET':
        return (
            f"<!doctype html><meta name='robots' content='noindex'>"
            f"<title>Unsubscribe — Daanaa</title>"
            f"<div style='font-family:sans-serif;max-width:28rem;margin:4rem auto'>"
            f"<h2>Unsubscribe from Daanaa emails?</h2>"
            f"<p>{email} will stop receiving campaign emails. "
            f"Account emails you request (like claim verification) still arrive.</p>"
            f"<form method='post' action='/api/email/unsubscribe?e={email}&t={token}'>"
            f"<button type='submit' style='padding:.6rem 1.2rem'>Unsubscribe</button>"
            f"</form></div>", 200, {'Content-Type': 'text/html'})

    suppress_email(email, reason='unsubscribed')
    return jsonify({'status': 'unsubscribed', 'email': email})


@app.route('/api/nonprofit/activity-feed', methods=['POST'])
@limiter.limit("30 per minute")
def nonprofit_activity_feed():
    """Consolidated "what changed" feed (Benevity pattern, task #15).

    One place a nonprofit leader sees what happened to their presence:
    link verifications, donor interest, data refreshes, volunteer activity,
    plus the org_activity log. Synthesized from existing timestamped data so
    the feed is rich from day one. Encouraging plain language only (P5).
    Auth matches /api/nonprofit/dashboard: EIN + verification token.
    """
    data  = request.get_json(silent=True) or {}
    ein   = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
    token = (data.get('verification_token') or '').strip()[:64]
    if not ein or not token:
        return jsonify({'error': 'EIN and verification_token required'}), 400

    db = get_db()
    claim, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    org = db.execute(
        """SELECT organization_name, donate_url, donate_url_status,
                  donate_checked_at, website, website_status,
                  website_checked_at, updated_at
           FROM registry_enriched WHERE EIN = ?""", (ein,)).fetchone()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    events = []

    def _add(ts, etype, message):
        if ts:
            events.append({'ts': ts, 'type': etype, 'message': message})

    # Donate link check — the single highest-value fact for an org.
    if org['donate_checked_at']:
        if org['donate_url_status'] in ('beta', 'claimed', 'verified') and org['donate_url']:
            _add(org['donate_checked_at'], 'donate_link',
                 'Your donation link was checked and is live on your public '
                 'page — donors can give directly.')
        else:
            _add(org['donate_checked_at'], 'donate_link',
                 'We looked for a donation link for your page. None is live '
                 'yet — donors currently see your EIN and mailing address. '
                 'You can add a link from your dashboard.')

    if org['website_checked_at']:
        _add(org['website_checked_at'], 'website',
             'Your website was checked and loads for donors.'
             if org['website_status'] == 'ok' else
             'We checked your website link and could not confirm it loads — '
             'worth a quick look from your dashboard.')

    if org['updated_at']:
        _add(org['updated_at'], 'data_refresh',
             'Your public profile data was refreshed from IRS and public '
             'records.')

    # Donor interest: anonymous aggregate only (P2) — never who, only how many.
    try:
        row = db.execute(
            "SELECT COALESCE(SUM(bookmark_count),0), MAX(last_updated) "
            "FROM wallet_analytics WHERE ein=? AND "
            "last_updated >= date('now','start of month')", (ein,)).fetchone()
        if row and row[0]:
            _add(row[1], 'donor_interest',
                 f'{row[0]} '
                 f'{"person" if row[0] == 1 else "people"} saved your '
                 'organization to their giving wallet this month. Anonymous, '
                 'aggregate interest — a good sign people are finding you.')
    except sqlite3.OperationalError:
        pass

    # Volunteer submissions awaiting review — an action the org can take now.
    try:
        row = db.execute(
            "SELECT COUNT(*), MAX(created_at) FROM volunteer_hours "
            "WHERE nonprofit_ein=? AND status='pending'", (ein,)).fetchone()
        if row and row[0]:
            _add(row[1], 'volunteer',
                 f'{row[0]} volunteer hour '
                 f'{"submission is" if row[0] == 1 else "submissions are"} '
                 'waiting for your confirmation.')
    except sqlite3.OperationalError:
        pass

    # Real activity log (claims, profile edits, corrections).
    try:
        for r in db.execute(
                "SELECT event_type, detail, created_at FROM org_activity "
                "WHERE ein=? ORDER BY created_at DESC LIMIT 15", (ein,)):
            _add(r['created_at'], r['event_type'],
                 r['detail'] or r['event_type'].replace('_', ' ').capitalize())
    except sqlite3.OperationalError:
        pass

    events.sort(key=lambda e: e['ts'], reverse=True)
    return jsonify({
        'ein': ein,
        'organization_name': org['organization_name'],
        'events': events[:30],
        'note': ('Everything here comes from your own public presence and '
                 'anonymous aggregate donor interest — no individual donor '
                 'is ever identified.'),
    })


# ── Volunteer interest counter ────────────────────────────────────────────────
# Anonymous aggregate: counts how many people expressed interest in volunteering
# at each org. No user IDs stored — just a tally. Only surfaces to claimed orgs
# when count >= 5 (prevents re-identification at count=1). Rate-limited per-worker
# in-memory (low-stakes feature; per-worker is good enough to deter obvious abuse).

_volunteer_rate: dict[str, list[float]] = {}

def _vol_rate_ok(ip: str, limit: int = 20, window: int = 3600) -> bool:
    import time as _time
    now = _time.time()
    hits = [t for t in _volunteer_rate.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        return False
    _volunteer_rate[ip] = hits + [now]
    return True

def _ensure_volunteer_interest_table(db: sqlite3.Connection) -> None:
    db.execute('''CREATE TABLE IF NOT EXISTS volunteer_interest
                  (EIN TEXT PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0)''')

@app.route('/api/volunteer-interest/<ein>', methods=['POST', 'DELETE'])
def volunteer_interest(ein: str):
    import re as _re2
    if not _re2.match(r'^\d{9}$', ein):
        return jsonify({'error': 'invalid EIN'}), 400
    ip = request.remote_addr or 'unknown'
    if not _vol_rate_ok(ip):
        return jsonify({'error': 'rate limit'}), 429
    db = get_db()
    _ensure_volunteer_interest_table(db)
    if request.method == 'POST':
        db.execute('''INSERT INTO volunteer_interest (EIN, count) VALUES (?, 1)
                      ON CONFLICT(EIN) DO UPDATE SET count = count + 1''', (ein,))
        # Email volunteer contact if available
        data = request.get_json() or {}
        volunteer_email = data.get('email', '').strip()
        event_title = data.get('event_title', 'an event').strip()

        org_claim = db.execute(
            'SELECT volunteer_contact_email, volunteer_contact_name FROM org_claims WHERE EIN = ?',
            (ein,)
        ).fetchone()

        if org_claim and org_claim[0]:  # volunteer_contact_email exists
            contact_email = org_claim[0]
            contact_name = org_claim[1] or 'Volunteer Coordinator'
            try:
                _send_volunteer_interest_email(
                    contact_email=contact_email,
                    contact_name=contact_name,
                    event_title=event_title,
                    volunteer_email=volunteer_email
                )
            except Exception as e:
                logger.warning(f'Failed to send volunteer interest email to {contact_email}: {e}')
    else:
        db.execute('''UPDATE volunteer_interest SET count = MAX(0, count - 1)
                      WHERE EIN = ?''', (ein,))
    db.commit()
    row = db.execute('SELECT count FROM volunteer_interest WHERE EIN = ?', (ein,)).fetchone()
    return jsonify({'ein': ein, 'count': row[0] if row else 0}), 200

@app.route('/api/volunteer-interest/<ein>', methods=['GET'])
def volunteer_interest_get(ein: str):
    """For claimed org dashboards — returns count only if >= 5 (privacy threshold)."""
    import re as _re2
    if not _re2.match(r'^\d{9}$', ein):
        return jsonify({'error': 'invalid EIN'}), 400
    db = get_db()
    _ensure_volunteer_interest_table(db)
    row = db.execute('SELECT count FROM volunteer_interest WHERE EIN = ?', (ein,)).fetchone()
    count = row[0] if row else 0
    return jsonify({'ein': ein, 'count': count if count >= 5 else None, 'threshold': 5}), 200


# ── Phase 9: Nonprofit Peer Network (Keystone) ───────────────────────────────

@app.route('/api/nonprofit/<ein>/peers', methods=['GET'])
def nonprofit_find_peers(ein: str):
    """Find similar orgs (peers by cause, size, geography, focus)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    cause = request.args.get('cause', '')
    state = request.args.get('state', '')
    size = request.args.get('size', '')  # micro, professional, established

    db = get_db()
    org = db.execute(
        "SELECT NTEE1, STATE, total_revenue, merit_band_v5_label FROM registry_enriched WHERE EIN=?",
        (ein,)
    ).fetchone()

    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    # Build peer query: similar cause, geography, size
    query = """
        SELECT DISTINCT re.EIN, re.organization_name, re.NTEE1, re.STATE, re.total_revenue,
               re.merit_band_v5_label, re.merit_score_v5, re.mission
        FROM registry_enriched re
        WHERE re.EIN != ?
          AND re.NTEE1 = ?
          AND (? = '' OR re.STATE = ?)
          AND (? = '' OR re.merit_band_v5_label = ?)
        ORDER BY re.merit_score_v5 DESC
        LIMIT 20
    """

    rows = db.execute(query, (ein, org[0], state, state, size, size)).fetchall()

    peers = []
    for row in rows:
        peers.append({
            'ein': row[0],
            'name': row[1],
            'cause': row[2],
            'state': row[3],
            'revenue': row[4],
            'size_bracket': row[5],
            'financial_context_score': row[6],
            'mission': row[7]
        })

    return jsonify({'ein': ein, 'peer_count': len(peers), 'peers': peers}), 200


@app.route('/api/nonprofit/<ein>/connect', methods=['POST'])
def nonprofit_request_connection(ein: str):
    """Request peer connection with another org."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    data = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    if not token:
        return jsonify({'error': 'verification_token required'}), 400

    db = get_db()
    row, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    peer_ein = ''.join(c for c in data.get('peer_ein', '') if c.isdigit())[:10]
    connection_type = (data.get('connection_type') or 'learning_peer').strip()
    context = (data.get('context_note') or '').strip()[:500]

    if not peer_ein or connection_type not in ('peer_mentor', 'collab_partner', 'learning_peer', 'sector_neighbor'):
        return jsonify({'error': 'peer_ein and valid connection_type required'}), 400

    # Check if peer exists
    peer = db.execute("SELECT organization_name FROM registry_enriched WHERE EIN=?", (peer_ein,)).fetchone()
    if not peer:
        return jsonify({'error': 'Peer organization not found'}), 404

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    try:
        db.execute(
            """INSERT INTO nonprofit_peer_connections
               (ein_from, ein_to, connection_type, status, initiated_by, initiated_at, context_note)
               VALUES (?, ?, ?, 'pending', ?, ?, ?)""",
            (ein, peer_ein, connection_type, ein, now, context)
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Connection already requested or exists'}), 409

    return jsonify({
        'ein_from': ein,
        'ein_to': peer_ein,
        'peer_name': peer[0],
        'connection_type': connection_type,
        'status': 'pending',
        'message': 'Connection request sent. Peer org will be notified.'
    }), 201


@app.route('/api/nonprofit/<ein>/connections', methods=['GET'])
def nonprofit_list_connections(ein: str):
    """List all peer connections (incoming + outgoing)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    status = request.args.get('status', 'active')  # active, pending, all

    db = get_db()

    status_filter = f"AND status='{status}'" if status != 'all' else ""

    query = f"""
        SELECT ein_from, ein_to, connection_type, status, initiated_at
        FROM nonprofit_peer_connections
        WHERE (ein_from = ? OR ein_to = ?) {status_filter}
        ORDER BY initiated_at DESC
    """

    rows = db.execute(query, (ein, ein)).fetchall()

    connections = []
    for row in rows:
        is_initiator = row[0] == ein
        other_ein = row[1] if is_initiator else row[0]
        org = db.execute("SELECT organization_name FROM registry_enriched WHERE EIN=?", (other_ein,)).fetchone()

        connections.append({
            'org_ein': other_ein,
            'org_name': org[0] if org else 'Unknown',
            'type': row[2],
            'status': row[3],
            'you_initiated': is_initiator,
            'created_at': row[4]
        })

    return jsonify({'ein': ein, 'connections': connections}), 200


@app.route('/api/nonprofit/<ein>/case-study', methods=['POST'])
def nonprofit_publish_case_study(ein: str):
    """Publish a case study (what worked, what we learned)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    data = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    if not token:
        return jsonify({'error': 'verification_token required'}), 400

    db = get_db()
    row, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    title = (data.get('title') or '').strip()[:200]
    problem = (data.get('problem_statement') or '').strip()
    solution = (data.get('solution_description') or '').strip()
    results = (data.get('results_achieved') or '').strip()
    lessons = (data.get('lessons_learned') or '').strip()
    author_name = (data.get('author_name') or 'Organization').strip()[:100]
    author_title = (data.get('author_title') or '').strip()[:100]

    if not all([title, problem, solution, results, lessons]):
        return jsonify({'error': 'All fields required (title, problem, solution, results, lessons)'}), 400

    if any(len(x) < 20 for x in [problem, solution, results, lessons]):
        return jsonify({'error': 'Descriptions must be at least 20 characters'}), 400

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    db.execute(
        """INSERT INTO nonprofit_case_studies
           (ein, title, problem_statement, solution_description, results_achieved, lessons_learned,
            author_name, author_title, published_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ein, title, problem, solution, results, lessons, author_name, author_title, now)
    )
    db.commit()

    study = db.execute(
        "SELECT id FROM nonprofit_case_studies WHERE ein=? ORDER BY id DESC LIMIT 1",
        (ein,)
    ).fetchone()

    return jsonify({
        'id': study[0],
        'ein': ein,
        'title': title,
        'published_at': now,
        'message': 'Case study published. Other orgs will learn from your experience.'
    }), 201


@app.route('/api/nonprofit/case-studies', methods=['GET'])
def nonprofit_list_case_studies():
    """List published case studies (searchable by cause, challenge)."""
    cause = request.args.get('cause', '')
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', 20, type=int)

    db = get_db()

    query = """
        SELECT cs.id, cs.ein, re.organization_name, cs.title,
               cs.problem_statement, cs.results_achieved, cs.published_at, cs.helpful_count
        FROM nonprofit_case_studies cs
        JOIN registry_enriched re ON cs.ein = re.EIN
        WHERE 1=1
    """
    params = []

    if cause:
        query += " AND re.NTEE1 = ?"
        params.append(cause)

    if keyword:
        keyword_pattern = f"%{keyword}%"
        query += " AND (cs.title LIKE ? OR cs.problem_statement LIKE ? OR cs.solution_description LIKE ?)"
        params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

    query += " ORDER BY cs.published_at DESC LIMIT ?"
    params.append(limit)

    rows = db.execute(query, params).fetchall()

    studies = []
    for row in rows:
        studies.append({
            'id': row[0],
            'ein': row[1],
            'org_name': row[2],
            'title': row[3],
            'problem': row[4],
            'results': row[5],
            'published_at': row[6],
            'helpful_count': row[7]
        })

    return jsonify({'count': len(studies), 'case_studies': studies}), 200


# ── Phase 4: Nonprofit Content (Voice Amplification) ─────────────────────────

@app.route('/api/nonprofit/<ein>/content', methods=['POST'])
def nonprofit_create_content(ein: str):
    """Create/publish content for nonprofit (impact story, program, volunteer need, leadership).

    Requires organization verification token (same as claim flow).
    """
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    data = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    if not ein or not token:
        return jsonify({'error': 'EIN and verification_token required'}), 400

    db = get_db()
    row, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    content_type = (data.get('content_type') or '').strip()
    title = (data.get('title') or '').strip()[:200]
    body = (data.get('body') or '').strip()

    if content_type not in ('impact_story', 'program', 'volunteer_need', 'leadership'):
        return jsonify({'error': 'invalid content_type'}), 400
    if not title or not body:
        return jsonify({'error': 'title and body required'}), 400
    if len(body) < 50 or len(body) > 5000:
        return jsonify({'error': 'body must be 50-5000 characters'}), 400

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    author_email = row['email']
    author_name = (data.get('author_name') or 'Organization').strip()[:100]
    status = 'published' if data.get('publish', False) else 'draft'

    db.execute(
        """INSERT INTO nonprofit_content
           (ein, content_type, title, body, author_email, author_name, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ein, content_type, title, body, author_email, author_name, status, now, now)
    )
    db.commit()

    result = db.execute(
        "SELECT id, version, status FROM nonprofit_content WHERE ein=? AND content_type=? ORDER BY id DESC LIMIT 1",
        (ein, content_type)
    ).fetchone()

    return jsonify({
        'id': result[0],
        'ein': ein,
        'content_type': content_type,
        'title': title,
        'status': result[2],
        'version': result[1],
        'message': 'Content created. Visit your dashboard to publish.' if status == 'draft' else 'Content published.'
    }), 201


@app.route('/api/nonprofit/<ein>/content', methods=['GET'])
def nonprofit_list_content(ein: str):
    """List all published content for org (public endpoint)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()
    rows = db.execute(
        """SELECT id, content_type, title, body, published_at, author_name, version
           FROM nonprofit_content
           WHERE ein=? AND status='published'
           ORDER BY published_at DESC""",
        (ein,)
    ).fetchall()

    content = []
    for row in rows:
        content.append({
            'id': row[0],
            'type': row[1],
            'title': row[2],
            'body': row[3],
            'published_at': row[4],
            'author': row[5],
            'version': row[6]
        })

    return jsonify({'ein': ein, 'content': content}), 200


@app.route('/api/nonprofit/<ein>/content/<int:content_id>', methods=['PUT'])
def nonprofit_edit_content(ein: str, content_id: int):
    """Edit nonprofit content (creates new version, archives old)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    data = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    if not token:
        return jsonify({'error': 'verification_token required'}), 400

    db = get_db()
    row, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    # Fetch current content
    content = db.execute(
        "SELECT id, ein, body, version FROM nonprofit_content WHERE id=?",
        (content_id,)
    ).fetchone()

    if not content or content[1] != ein:
        return jsonify({'error': 'Content not found or unauthorized'}), 404

    new_body = (data.get('body') or '').strip()
    if not new_body or len(new_body) < 50 or len(new_body) > 5000:
        return jsonify({'error': 'body must be 50-5000 characters'}), 400

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    new_version = content[3] + 1

    # Archive old version
    db.execute(
        "INSERT INTO nonprofit_content_versions (content_id, version, body, archived_at) VALUES (?, ?, ?, ?)",
        (content_id, content[3], content[2], now)
    )

    # Update with new version
    db.execute(
        "UPDATE nonprofit_content SET body=?, version=?, updated_at=? WHERE id=?",
        (new_body, new_version, now, content_id)
    )
    db.commit()

    return jsonify({
        'id': content_id,
        'version': new_version,
        'message': 'Content updated. Old version archived.'
    }), 200


@app.route('/api/nonprofit/<ein>/content/<int:content_id>/publish', methods=['POST'])
def nonprofit_publish_content(ein: str, content_id: int):
    """Publish draft content."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    data = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    if not token:
        return jsonify({'error': 'verification_token required'}), 400

    db = get_db()
    row, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    content = db.execute(
        "SELECT id, ein, status FROM nonprofit_content WHERE id=?",
        (content_id,)
    ).fetchone()

    if not content or content[1] != ein:
        return jsonify({'error': 'Content not found or unauthorized'}), 404

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    db.execute(
        "UPDATE nonprofit_content SET status='published', published_at=? WHERE id=?",
        (now, content_id)
    )
    db.commit()

    return jsonify({'id': content_id, 'status': 'published', 'published_at': now}), 200


# ── PHASE 10: Sector Health Diagnostics ────────────────────────────────────────

@app.route('/api/sector/<cause_area>/health', methods=['GET'])
def sector_health_snapshot(cause_area: str):
    """Get cause area health metrics (org count, revenue, financial health distribution)."""
    cause_area = cause_area.upper().strip()[:2]  # NTEE1 code

    db = get_db()

    # Get most recent snapshot
    snapshot = db.execute(
        """SELECT id, snapshot_date, org_count, total_revenue_millions, median_revenue,
                  avg_financial_health_score, healthy_pct, stable_pct, caution_pct,
                  growth_rate, median_reserve_months, leadership_turnover_pct,
                  created_org_count, closed_org_count
           FROM sector_health_snapshots
           WHERE cause_area = ?
           ORDER BY snapshot_date DESC
           LIMIT 1""",
        (cause_area,)
    ).fetchone()

    if not snapshot:
        # Return null snapshot if none exists (not an error, just new cause area)
        return jsonify({
            'cause_area': cause_area,
            'status': 'no_data',
            'message': 'No health data yet for this cause area'
        }), 200

    return jsonify({
        'cause_area': cause_area,
        'snapshot_date': snapshot[1],
        'metrics': {
            'org_count': snapshot[2],
            'total_revenue_millions': snapshot[3],
            'median_revenue': snapshot[4],
            'avg_financial_health_score': snapshot[5],
            'distribution': {
                'healthy_pct': snapshot[6],
                'stable_pct': snapshot[7],
                'caution_pct': snapshot[8]
            },
            'growth_rate_yoy': snapshot[9],
            'median_reserve_months': snapshot[10],
            'leadership_turnover_pct': snapshot[11],
            'new_orgs_this_period': snapshot[12],
            'closed_orgs_this_period': snapshot[13]
        }
    }), 200


@app.route('/api/sector/<cause_area>/coverage-gaps', methods=['GET'])
def sector_coverage_gaps(cause_area: str):
    """Identify service gaps in a cause area (by region, service type, population)."""
    cause_area = cause_area.upper().strip()[:2]
    service_type = request.args.get('service_type', '')  # direct_service, policy, research, capacity_building

    db = get_db()

    query = "SELECT id, cause_area, geographic_region, service_type, target_population, coverage_assessment, org_count_in_gap, population_served_estimate, notes, last_assessed FROM sector_coverage_gaps WHERE cause_area = ?"
    params = [cause_area]

    if service_type:
        query += " AND service_type = ?"
        params.append(service_type)

    query += " ORDER BY coverage_assessment ASC, last_assessed DESC"

    rows = db.execute(query, params).fetchall()

    gaps = []
    for row in rows:
        gaps.append({
            'id': row[0],
            'region': row[2],
            'service_type': row[3],
            'target_population': row[4],
            'coverage_level': row[5],  # strong, moderate, weak, none
            'orgs_in_gap': row[6],
            'population_estimate': row[7],
            'notes': row[8],
            'last_assessed': row[9]
        })

    return jsonify({
        'cause_area': cause_area,
        'gap_count': len(gaps),
        'gaps': gaps
    }), 200


@app.route('/api/sector/<cause_area>/collaboration-signals', methods=['GET'])
def sector_collaboration_signals(cause_area: str):
    """Find orgs with overlapping missions for co-funding or coordination."""
    cause_area = cause_area.upper().strip()[:2]
    min_strength = float(request.args.get('min_strength', 0.4))  # 0-1

    db = get_db()

    # Find all pairs of orgs in this cause area with high collaboration potential
    rows = db.execute(
        """SELECT cs.ein_1, cs.ein_2, cs.collaboration_strength,
                  cs.target_population_overlap, cs.geographic_overlap,
                  cs.suggested_action,
                  r1.organization_name, r2.organization_name
           FROM sector_collaboration_signals cs
           JOIN registry_enriched r1 ON r1.EIN = cs.ein_1
           JOIN registry_enriched r2 ON r2.EIN = cs.ein_2
           WHERE r1.NTEE1 = ? AND r2.NTEE1 = ?
             AND cs.collaboration_strength >= ?
             AND cs.funding_opportunity = 1
           ORDER BY cs.collaboration_strength DESC
           LIMIT 50""",
        (cause_area, cause_area, min_strength)
    ).fetchall()

    opportunities = []
    for row in rows:
        opportunities.append({
            'org_1': {
                'ein': row[0],
                'name': row[6]
            },
            'org_2': {
                'ein': row[1],
                'name': row[7]
            },
            'collaboration_strength': row[2],
            'target_population_overlap': row[3],
            'geographic_overlap': row[4],
            'suggested_action': row[5]
        })

    return jsonify({
        'cause_area': cause_area,
        'opportunity_count': len(opportunities),
        'opportunities': opportunities
    }), 200


@app.route('/api/sector/research', methods=['GET'])
def sector_research_browse():
    """Browse published sector research datasets."""
    cause_area = request.args.get('cause_area', '')
    data_type = request.args.get('data_type', '')  # financial_trends, movement_health, impact_analysis, funder_flows, leadership_pipeline
    limit = min(int(request.args.get('limit', 20)), 100)

    db = get_db()

    query = "SELECT id, research_name, cause_area, data_type, description, methodology, findings_summary, published_at, org_count_analyzed, years_covered, download_url FROM sector_research_datasets WHERE published_at IS NOT NULL"
    params = []

    if cause_area:
        query += " AND cause_area = ?"
        params.append(cause_area)

    if data_type:
        query += " AND data_type = ?"
        params.append(data_type)

    query += " ORDER BY published_at DESC LIMIT ?"
    params.append(limit)

    rows = db.execute(query, params).fetchall()

    datasets = []
    for row in rows:
        datasets.append({
            'id': row[0],
            'name': row[1],
            'cause_area': row[2],
            'data_type': row[3],
            'description': row[4],
            'methodology': row[5],
            'findings_summary': row[6],
            'published_at': row[7],
            'org_count_analyzed': row[8],
            'years_covered': row[9],
            'download_url': row[10]
        })

    return jsonify({
        'research_count': len(datasets),
        'datasets': datasets
    }), 200


@app.route('/api/sector/<cause_area>/funding-flows', methods=['GET'])
def sector_funding_flows(cause_area: str):
    """Analyze funding source distribution and concentration in a cause area."""
    cause_area = cause_area.upper().strip()[:2]
    period = request.args.get('period', '2026-Q2')  # e.g., '2026-Q2', '2025-FY'

    db = get_db()

    rows = db.execute(
        """SELECT period, funding_source, total_funding_millions, top_funder_ein,
                  top_funder_pct, concentration_score
           FROM sector_funding_flows
           WHERE cause_area = ? AND (? = '' OR period = ?)
           ORDER BY funding_source ASC""",
        (cause_area, period if period else '', period)
    ).fetchall()

    flows = []
    total_millions = 0

    for row in rows:
        flows.append({
            'funding_source': row[1],  # individual, foundation, government, corporate
            'total_funding_millions': row[2],
            'top_funder_ein': row[3],
            'top_funder_pct': row[4],
            'concentration_score': row[5]  # Gini coefficient, 0-1
        })
        if row[2]:
            total_millions += row[2]

    return jsonify({
        'cause_area': cause_area,
        'period': row[0] if rows else period,
        'total_funding_millions': total_millions,
        'funding_flows': flows,
        'analysis': {
            'summary': f'{len(flows)} funding sources tracked',
            'concentration_note': 'Higher concentration_score indicates funding is concentrated in fewer funders'
        }
    }), 200


# ── PHASE 5: Trust Verification ────────────────────────────────────────────────

@app.route('/api/nonprofit/<ein>/verifications', methods=['GET'])
def nonprofit_get_verifications(ein: str):
    """Get all verifications for an org (public, shows badge credibility)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    # Get all active verifications
    rows = db.execute(
        """SELECT verification_type, status, confidence_score, verified_at, expires_at, notes
           FROM nonprofit_verifications
           WHERE ein = ? AND status IN ('verified', 'expired')
           ORDER BY verified_at DESC""",
        (ein,)
    ).fetchall()

    verifications = []
    for row in rows:
        verifications.append({
            'type': row[0],
            'status': row[1],
            'confidence': row[2],
            'verified_at': row[3],
            'expires_at': row[4],
            'notes': row[5]
        })

    # Get badges
    badges = db.execute(
        """SELECT badge_type, badge_name, badge_description, earned_at
           FROM nonprofit_badges
           WHERE ein = ? AND is_active = 1
           ORDER BY display_order ASC""",
        (ein,)
    ).fetchall()

    badge_list = []
    for row in badges:
        badge_list.append({
            'type': row[0],
            'name': row[1],
            'description': row[2],
            'earned_at': row[3]
        })

    return jsonify({
        'ein': ein,
        'verification_count': len(verifications),
        'badge_count': len(badge_list),
        'verifications': verifications,
        'badges': badge_list
    }), 200


@app.route('/api/nonprofit/<ein>/verify/<verification_type>', methods=['POST'])
def nonprofit_start_verification(ein: str, verification_type: str):
    """Request verification of a specific claim (website, donation link, mission, etc)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    data = request.get_json(silent=True) or {}
    token = (data.get('verification_token') or '').strip()[:64]

    if not token:
        return jsonify({'error': 'verification_token required'}), 400

    if verification_type not in ('website_active', 'donate_link_verified', 'mission_claimed', 'leadership_verified', 'financial_filed'):
        return jsonify({'error': 'invalid verification_type'}), 400

    db = get_db()
    row, err = _authorize_claimant(db, ein, token)
    if err:
        return err

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    try:
        db.execute(
            """INSERT INTO nonprofit_verifications
               (ein, verification_type, status, verification_method, created_at, updated_at)
               VALUES (?, ?, 'pending', 'self_attested', ?, ?)""",
            (ein, verification_type, now, now)
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Verification already in progress for this type'}), 409

    # Log in audit trail
    db.execute(
        """INSERT INTO verification_audit_log
           (ein, action, actor, reason, created_at)
           VALUES (?, 'verification_started', 'nonprofit', ?, ?)""",
        (ein, f'Requested {verification_type} verification', now)
    )
    db.commit()

    return jsonify({
        'ein': ein,
        'verification_type': verification_type,
        'status': 'pending',
        'message': 'Verification request submitted. We will review within 48 hours.'
    }), 201


@app.route('/api/nonprofit/<ein>/verification-timeline', methods=['GET'])
def nonprofit_verification_timeline(ein: str):
    """Get chronological verification timeline for transparency."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    rows = db.execute(
        """SELECT event, event_type, status, result, details, created_at
           FROM verification_timeline
           WHERE ein = ?
           ORDER BY created_at DESC""",
        (ein,)
    ).fetchall()

    timeline = []
    for row in rows:
        timeline.append({
            'event': row[0],
            'type': row[1],
            'status': row[2],
            'result': row[3],
            'details': row[4],
            'timestamp': row[5]
        })

    return jsonify({
        'ein': ein,
        'event_count': len(timeline),
        'timeline': timeline
    }), 200


@app.route('/api/nonprofit/<ein>/badge-progress', methods=['GET'])
def nonprofit_badge_progress(ein: str):
    """Show which badges org is eligible for and progress toward each."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    # Get org details
    org = db.execute(
        "SELECT organization_name, website, donate_url FROM registry_enriched WHERE EIN=?",
        (ein,)
    ).fetchone()

    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    # Check eligibility for each badge type
    progress = {}

    # Verified Org: website active + donate link + mission
    website_v = db.execute(
        "SELECT status FROM nonprofit_verifications WHERE ein=? AND verification_type='website_active'",
        (ein,)
    ).fetchone()
    donate_v = db.execute(
        "SELECT status FROM nonprofit_verifications WHERE ein=? AND verification_type='donate_link_verified'",
        (ein,)
    ).fetchone()
    mission_v = db.execute(
        "SELECT status FROM nonprofit_verifications WHERE ein=? AND verification_type='mission_claimed'",
        (ein,)
    ).fetchone()

    # `row and row[0]=='verified'` returns None (not False) when row is None,
    # because Python's `and` yields the first falsy operand -- and sum() cannot
    # add None to an int. nonprofit_verifications is currently empty, so every
    # lookup returns None and this endpoint 500'd for EVERY org (found 2026-08-08
    # while checking the nonprofit dashboard). Coerce explicitly.
    def _is_verified(row):
        return bool(row) and row[0] == 'verified'

    verified_steps = sum([_is_verified(website_v), _is_verified(donate_v), _is_verified(mission_v)])
    progress['verified_org'] = {
        'name': 'Verified Organization',
        'description': 'Claims verified: website active, donation link working, mission current',
        'progress': f'{verified_steps}/3',
        'earned': verified_steps == 3
    }

    # Active Mission: mission claimed and on website
    mission_claimed = mission_v and mission_v[0] == 'verified'
    progress['active_mission'] = {
        'name': 'Active Mission',
        'description': 'Mission statement verified on organization website',
        'progress': '1/1' if mission_claimed else '0/1',
        'earned': mission_claimed
    }

    # Financial Health: 990 filed in last 2 years
    financial_v = db.execute(
        "SELECT status FROM nonprofit_verifications WHERE ein=? AND verification_type='financial_filed'",
        (ein,)
    ).fetchone()
    progress['financial_health'] = {
        'name': 'Financial Health',
        'description': 'Recent 990 Form filed on public record',
        'progress': '1/1' if financial_v and financial_v[0]=='verified' else '0/1',
        'earned': financial_v and financial_v[0]=='verified'
    }

    # Responsive: replies to queries within 30 days
    progress['responsive'] = {
        'name': 'Responsive',
        'description': 'Responds to donor inquiries and verifications promptly',
        'progress': 'In Progress',
        'earned': False
    }

    return jsonify({
        'ein': ein,
        'org_name': org[0],
        'badge_progress': progress,
        'total_badges_earned': sum([1 for v in progress.values() if v['earned']])
    }), 200


# ── PHASE 6: Donor Learning System ────────────────────────────────────────────

@app.route('/api/donor/learning-resources', methods=['GET'])
def get_learning_resources():
    """Browse learning resources (research, case studies, guides)."""
    cause_area = request.args.get('cause_area', '')
    resource_type = request.args.get('type', '')
    limit = min(int(request.args.get('limit', 20)), 100)

    db = get_db()

    query = "SELECT id, resource_type, title, description, cause_area, url, published_at, view_count FROM learning_resources WHERE source IN ('daanaa', 'external_partner')"
    params = []

    if cause_area:
        query += " AND cause_area = ?"
        params.append(cause_area)

    if resource_type:
        query += " AND resource_type = ?"
        params.append(resource_type)

    query += " ORDER BY published_at DESC LIMIT ?"
    params.append(limit)

    rows = db.execute(query, params).fetchall()

    resources = []
    for row in rows:
        resources.append({
            'id': row[0],
            'type': row[1],
            'title': row[2],
            'description': row[3],
            'cause': row[4],
            'url': row[5],
            'published_at': row[6],
            'views': row[7]
        })

    return jsonify({
        'resource_count': len(resources),
        'resources': resources
    }), 200


@app.route('/api/donor/cohorts', methods=['GET'])
def get_donor_cohorts():
    """Find learning cohorts by topic or focus."""
    topic = request.args.get('topic', '')
    cohort_type = request.args.get('type', '')

    db = get_db()

    query = "SELECT id, cohort_name, cohort_topic, cohort_type, member_count, duration_weeks, start_date, description FROM donor_learning_cohorts WHERE status='active'"
    params = []

    if topic:
        query += " AND cohort_topic = ?"
        params.append(topic)

    if cohort_type:
        query += " AND cohort_type = ?"
        params.append(cohort_type)

    query += " ORDER BY start_date DESC LIMIT 20"

    rows = db.execute(query, params).fetchall()

    cohorts = []
    for row in rows:
        cohorts.append({
            'id': row[0],
            'name': row[1],
            'topic': row[2],
            'type': row[3],
            'members': row[4],
            'duration_weeks': row[5],
            'start_date': row[6],
            'description': row[7]
        })

    return jsonify({
        'cohort_count': len(cohorts),
        'cohorts': cohorts
    }), 200


@app.route('/api/donor/<donor_id>/impact-summary', methods=['GET'])
def donor_impact_summary(donor_id: str):
    """Get personal impact summary (giving, learning, outcomes achieved)."""
    donor_id = donor_id[:64]

    db = get_db()

    # Giving summary
    giving = db.execute(
        "SELECT SUM(intent_amount_estimate), COUNT(DISTINCT ein) FROM donor_giving_intent WHERE donor_id=? AND status='completed'",
        (donor_id,)
    ).fetchone()

    total_giving = giving[0] or 0
    org_count = giving[1] or 0

    # Impact summary
    outcomes = db.execute(
        """SELECT outcome_type, SUM(outcome_value) FROM impact_tracking
           WHERE donor_id=? AND report_source IN ('org_reported', 'third_party')
           GROUP BY outcome_type""",
        (donor_id,)
    ).fetchall()

    impact = {}
    for row in outcomes:
        impact[row[0]] = row[1]

    # Learning summary
    resources_engaged = db.execute(
        "SELECT COUNT(DISTINCT resource_id) FROM learning_engagement WHERE donor_id=? AND engagement_type='completed'",
        (donor_id,)
    ).fetchone()

    cohort_count = db.execute(
        "SELECT COUNT(DISTINCT cohort_id) FROM cohort_participants WHERE donor_id=? AND status='completed'",
        (donor_id,)
    ).fetchone()

    return jsonify({
        'donor_id': donor_id,
        'giving_summary': {
            'total_amount': total_giving,
            'orgs_supported': org_count,
            'engagement_level': 'active' if org_count > 0 else 'exploring'
        },
        'impact_summary': {
            'outcomes': impact,
            'message': f'Your giving has supported impact across {len(impact)} outcome areas'
        },
        'learning_summary': {
            'resources_completed': resources_engaged[0] or 0,
            'cohorts_completed': cohort_count[0] or 0,
            'message': f'You\'ve engaged with {(resources_engaged[0] or 0) + (cohort_count[0] or 0)} learning opportunities'
        }
    }), 200


@app.route('/api/donor/<donor_id>/org-impact/<ein>', methods=['GET'])
def donor_org_impact(donor_id: str, ein: str):
    """Get impact from a specific organization you support."""
    donor_id = donor_id[:64]
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    # Get org info
    org = db.execute(
        "SELECT organization_name, mission FROM registry_enriched WHERE EIN=?",
        (ein,)
    ).fetchone()

    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    # Get impact outcomes
    outcomes = db.execute(
        """SELECT outcome_type, outcome_value, outcome_unit, outcome_timeframe, last_reported
           FROM impact_tracking WHERE donor_id=? AND ein=?
           ORDER BY last_reported DESC""",
        (donor_id, ein)
    ).fetchall()

    impact_list = []
    for row in outcomes:
        impact_list.append({
            'outcome': row[0],
            'value': row[1],
            'unit': row[2],
            'timeframe': row[3],
            'last_reported': row[4]
        })

    return jsonify({
        'donor_id': donor_id,
        'ein': ein,
        'org_name': org[0],
        'mission': org[1],
        'impact_outcomes': impact_list,
        'summary': f'{len(impact_list)} impact outcomes tracked from your support'
    }), 200


# Route removed 2026-08-08. GET /api/donor/<donor_id>/giving-profile served
# donor cause_interests/giving_style/size_preference for ANY donor_id with no
# authentication -- live in production, reachable, and violates the explicit
# architecture principle enforced by test_wallet_routes_require_firebase_auth:
# "No giving/donation routes may exist -- those stay in localStorage only."
# donor_learning_profiles held 0 rows at removal time (verified 2026-08-08), so
# no donor data is known to have been exposed. Confirmed unused by any frontend
# caller before removal. The donor_learning_profiles table itself is untouched
# -- dropping/migrating it is a data decision outside this fix's scope.



# ── PHASE 11: Financial Health Coaching ────────────────────────────────────────

@app.route('/api/nonprofit/<ein>/financial-health', methods=['GET'])
def nonprofit_financial_health(ein: str):
    """Get financial health assessment (reserves, volatility, concentration, signal)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    health = db.execute(
        """SELECT assessment_date, reserve_ratio, reserve_months_ideal, reserve_trend,
                  revenue_volatility, expense_trend, revenue_concentration, funder_diversity_score,
                  health_signal, signal_confidence
           FROM nonprofit_financial_health WHERE ein=?
           ORDER BY assessment_date DESC LIMIT 1""",
        (ein,)
    ).fetchone()

    if not health:
        return jsonify({'status': 'no_data', 'message': 'Health assessment not yet available for this org'}), 200

    return jsonify({
        'ein': ein,
        'assessment_date': health[0],
        'reserves': {
            'current_months': health[1],
            'ideal_months': health[2],
            'status': health[3],
            'message': f'{health[1]:.1f} months reserves (target: {health[2]} months)'
        },
        'revenue_quality': {
            'volatility_score': health[4],
            'expense_growth_rate': health[5],
            'funder_concentration': health[6],
            'diversity_score': health[7],
            'interpretation': 'Higher diversity = lower risk'
        },
        'overall_signal': health[8],
        'confidence': health[9],
        'signal_color': {
            'HEALTHY': 'green',
            'STABLE': 'blue',
            'CAUTION': 'yellow',
            'NEED_SUPPORT': 'yellow',
            'MAY_NEED_SUPPORT': 'yellow',
            'CRISIS': 'red'
        }.get(health[8], 'gray')
    }), 200


@app.route('/api/nonprofit/<ein>/financial-guidance', methods=['GET'])
def nonprofit_financial_guidance(ein: str):
    """Get personalized financial health guidance and recommendations."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    guidance = db.execute(
        """SELECT guidance_type, current_status, recommendation, urgency_level, peer_comparison, action_link
           FROM financial_health_guidance WHERE ein=?
           ORDER BY urgency_level DESC, created_at DESC""",
        (ein,)
    ).fetchall()

    if not guidance:
        return jsonify({'guidance_count': 0, 'guidance': []}), 200

    guid_list = []
    for row in guidance:
        guid_list.append({
            'type': row[0],
            'current_status': row[1],
            'recommendation': row[2],
            'urgency': row[3],
            'peer_context': row[4],
            'action_link': row[5]
        })

    return jsonify({
        'ein': ein,
        'guidance_count': len(guid_list),
        'guidance': guid_list
    }), 200


@app.route('/api/nonprofit/<ein>/stress-tests', methods=['GET'])
def nonprofit_stress_tests(ein: str):
    """Run financial stress tests (what if scenarios)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    tests = db.execute(
        """SELECT test_type, test_scenario, current_reserves_months, post_shock_reserves_months,
                  survival_months, risk_level, mitigation_strategies
           FROM financial_stress_tests WHERE ein=?
           ORDER BY risk_level DESC""",
        (ein,)
    ).fetchall()

    if not tests:
        return jsonify({'test_count': 0, 'tests': []}), 200

    test_list = []
    for row in tests:
        test_list.append({
            'scenario': row[0],
            'description': row[1],
            'current_reserves': row[2],
            'reserves_after_shock': row[3],
            'months_you_could_operate': row[4],
            'risk_level': row[5],
            'recommendations': row[6]  # JSON
        })

    return jsonify({
        'ein': ein,
        'test_count': len(test_list),
        'stress_tests': test_list,
        'summary': f'Your org is resilient in {len([t for t in test_list if t["risk_level"] in ("low", "moderate")])} of {len(test_list)} scenarios'
    }), 200


@app.route('/api/nonprofit/<ein>/peer-benchmark', methods=['GET'])
def nonprofit_peer_benchmark(ein: str):
    """Compare financial metrics against peer organizations."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    metric = request.args.get('metric', '')  # reserve_ratio, revenue_volatility, etc.

    db = get_db()

    benchmarks = db.execute(
        """SELECT metric_type, your_value, peer_median, peer_25th_percentile,
                  peer_75th_percentile, your_rank, peer_total, interpretation
           FROM peer_benchmarking WHERE ein=?""",
        (ein,)
    ).fetchall()

    if metric:
        benchmarks = [b for b in benchmarks if b[0] == metric]

    if not benchmarks:
        return jsonify({'benchmark_count': 0, 'benchmarks': []}), 200

    bench_list = []
    for row in benchmarks:
        bench_list.append({
            'metric': row[0],
            'your_value': row[1],
            'peer_statistics': {
                'median': row[2],
                'bottom_quartile': row[3],
                'top_quartile': row[4]
            },
            'your_rank': f'{row[5]} of {row[6]}',
            'percentile': int((row[5] / row[6]) * 100) if row[6] else 0,
            'interpretation': row[7]
        })

    return jsonify({
        'ein': ein,
        'benchmark_count': len(bench_list),
        'benchmarks': bench_list,
        'peer_context': 'You\'re being compared against orgs in your cause area, size bracket, and region'
    }), 200


@app.route('/api/nonprofit/<ein>/financial-goals', methods=['GET'])
def nonprofit_financial_goals(ein: str):
    """Get financial goals and progress toward them."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    goals = db.execute(
        """SELECT goal_type, goal_description, goal_target, goal_deadline,
                  current_progress, progress_percent, status
           FROM financial_goal_tracking WHERE ein=? AND status IN ('new', 'active')
           ORDER BY goal_deadline ASC""",
        (ein,)
    ).fetchall()

    goal_list = []
    for row in goals:
        goal_list.append({
            'type': row[0],
            'description': row[1],
            'target': row[2],
            'deadline': row[3],
            'current_progress': row[4],
            'progress_percent': row[5],
            'status': row[6]
        })

    return jsonify({
        'ein': ein,
        'goal_count': len(goal_list),
        'goals': goal_list
    }), 200


@app.route('/api/nonprofit/<ein>/financial-coaching', methods=['GET'])
def nonprofit_coaching_history(ein: str):
    """Get financial coaching history and recommendations."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    sessions = db.execute(
        """SELECT session_type, topic, coach_type, session_notes, recommendations, status, completed_at
           FROM financial_health_coaching_sessions WHERE ein=?
           ORDER BY completed_at DESC LIMIT 5""",
        (ein,)
    ).fetchall()

    session_list = []
    for row in sessions:
        session_list.append({
            'type': row[0],
            'topic': row[1],
            'coach': row[2],
            'notes': row[3],
            'recommendations': row[4],  # JSON
            'status': row[5],
            'completed_at': row[6]
        })

    return jsonify({
        'ein': ein,
        'session_count': len(session_list),
        'recent_sessions': session_list
    }), 200


# ── PHASE 7: Institutional Memory ──────────────────────────────────────────────

@app.route('/api/nonprofit/<ein>/timeline', methods=['GET'])
def nonprofit_timeline(ein: str):
    """Get organizational timeline (founding, leadership, milestones, crises)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    events = db.execute(
        """SELECT event_date, event_type, event_title, event_description, impact, sources
           FROM org_timeline WHERE ein=?
           ORDER BY event_date DESC""",
        (ein,)
    ).fetchall()

    timeline = []
    for row in events:
        timeline.append({
            'date': row[0],
            'type': row[1],
            'title': row[2],
            'description': row[3],
            'impact': row[4],
            'sources': row[5]  # JSON
        })

    return jsonify({
        'ein': ein,
        'event_count': len(timeline),
        'timeline': timeline
    }), 200


@app.route('/api/nonprofit/<ein>/leadership-history', methods=['GET'])
def nonprofit_leadership_history(ein: str):
    """Get leadership history and transitions."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    leaders = db.execute(
        """SELECT leader_name, position, start_date, end_date, tenure_years,
                  background, accomplishments, successor_name
           FROM org_leadership_history WHERE ein=?
           ORDER BY start_date DESC""",
        (ein,)
    ).fetchall()

    history = []
    for row in leaders:
        history.append({
            'name': row[0],
            'position': row[1],
            'tenure': {
                'start': row[2],
                'end': row[3],
                'years': row[4]
            },
            'background': row[5],
            'accomplishments': row[6],
            'successor': row[7]
        })

    return jsonify({
        'ein': ein,
        'leader_count': len(history),
        'leadership_history': history
    }), 200


@app.route('/api/nonprofit/<ein>/knowledge-base', methods=['GET'])
def nonprofit_knowledge_base(ein: str):
    """Access organizational knowledge base (processes, contacts, history)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    knowledge_type = request.args.get('type', '')

    db = get_db()

    query = "SELECT knowledge_type, topic, content, owner_name, owner_contact, criticality, last_updated FROM org_knowledge_base WHERE ein=?"
    params = [ein]

    if knowledge_type:
        query += " AND knowledge_type = ?"
        params.append(knowledge_type)

    query += " ORDER BY criticality DESC, last_updated DESC"

    rows = db.execute(query, params).fetchall()

    knowledge = []
    for row in rows:
        knowledge.append({
            'type': row[0],
            'topic': row[1],
            'content': row[2],
            'owner': row[3],
            'owner_contact': row[4],
            'criticality': row[5],
            'last_updated': row[6]
        })

    return jsonify({
        'ein': ein,
        'knowledge_count': len(knowledge),
        'knowledge_base': knowledge
    }), 200


@app.route('/api/nonprofit/<ein>/decision-log', methods=['GET'])
def nonprofit_decision_log(ein: str):
    """Get decision log and organizational learning."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    decisions = db.execute(
        """SELECT decision_date, decision_title, decision_context, decision_details,
                  decision_maker, rationale, outcomes, lessons
           FROM org_decision_log WHERE ein=?
           ORDER BY decision_date DESC LIMIT 20""",
        (ein,)
    ).fetchall()

    log = []
    for row in decisions:
        log.append({
            'date': row[0],
            'title': row[1],
            'context': row[2],
            'decision': row[3],
            'maker': row[4],
            'rationale': row[5],
            'outcomes': row[6],
            'lessons': row[7]
        })

    return jsonify({
        'ein': ein,
        'decision_count': len(log),
        'decisions': log
    }), 200


@app.route('/api/nonprofit/<ein>/board-evolution', methods=['GET'])
def nonprofit_board_evolution(ein: str):
    """Track board composition and governance evolution."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    snapshots = db.execute(
        """SELECT snapshot_date, board_size, board_composition, board_diversity_score,
                  key_committees, governance_improvements
           FROM board_evolution WHERE ein=?
           ORDER BY snapshot_date DESC""",
        (ein,)
    ).fetchall()

    evolution = []
    for row in snapshots:
        evolution.append({
            'date': row[0],
            'board_size': row[1],
            'composition': row[2],  # JSON
            'diversity_score': row[3],
            'committees': row[4],  # JSON
            'improvements': row[5]
        })

    return jsonify({
        'ein': ein,
        'snapshot_count': len(evolution),
        'board_evolution': evolution
    }), 200


# ── PHASE 8: Services Marketplace ──────────────────────────────────────────────

@app.route('/api/marketplace/providers', methods=['GET'])
def marketplace_providers():
    """Browse service providers (consultants, trainers, vendors)."""
    category = request.args.get('category', '')
    availability = request.args.get('availability', 'available')
    limit = min(int(request.args.get('limit', 20)), 100)

    db = get_db()

    query = "SELECT id, provider_name, service_category, specialization, experience_level, hourly_rate_low, hourly_rate_high, rating, testimonials_count FROM nonprofit_service_providers WHERE marketplace_status='active'"
    params = []

    if category:
        query += " AND service_category = ?"
        params.append(category)

    if availability:
        query += " AND availability = ?"
        params.append(availability)

    query += " ORDER BY rating DESC LIMIT ?"
    params.append(limit)

    rows = db.execute(query, params).fetchall()

    providers = []
    for row in rows:
        providers.append({
            'id': row[0],
            'name': row[1],
            'category': row[2],
            'specialization': row[3],
            'experience': row[4],
            'rate_range': f'${row[5]}-{row[6]}/hr',
            'rating': row[7],
            'testimonials': row[8]
        })

    return jsonify({'provider_count': len(providers), 'providers': providers}), 200


# ── PHASE 12: Succession Planning ──────────────────────────────────────────────

@app.route('/api/nonprofit/<ein>/succession-readiness', methods=['GET'])
def nonprofit_succession_readiness(ein: str):
    """Get succession planning readiness assessment."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    readiness = db.execute(
        """SELECT assessment_date, leadership_pipeline_strength, board_strength,
                  knowledge_transfer_status, organizational_readiness_score, risk_level,
                  risk_factors, action_items
           FROM succession_readiness WHERE ein=?""",
        (ein,)
    ).fetchone()

    if not readiness:
        return jsonify({'status': 'no_assessment'}), 200

    return jsonify({
        'ein': ein,
        'assessment_date': readiness[0],
        'readiness_scores': {
            'leadership_pipeline': readiness[1],
            'board_strength': readiness[2],
            'knowledge_transfer': readiness[3],
            'overall_readiness': readiness[4]
        },
        'risk_level': readiness[5],
        'risk_factors': readiness[6],  # JSON
        'action_items': readiness[7]  # JSON
    }), 200


@app.route('/api/nonprofit/<ein>/transition-timeline', methods=['GET'])
def nonprofit_transition_timeline(ein: str):
    """Get leadership transition plan and timeline."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]

    db = get_db()

    timeline = db.execute(
        """SELECT outgoing_leader_name, incoming_leader_name, transition_start_date,
                  transition_end_date, phase, milestones, knowledge_transfer_plan
           FROM transition_timeline WHERE ein=?
           ORDER BY transition_start_date DESC LIMIT 1""",
        (ein,)
    ).fetchone()

    if not timeline:
        return jsonify({'status': 'no_transition'}), 200

    return jsonify({
        'ein': ein,
        'outgoing_leader': timeline[0],
        'incoming_leader': timeline[1],
        'transition_period': {
            'start': timeline[2],
            'end': timeline[3]
        },
        'current_phase': timeline[4],
        'milestones': timeline[5],  # JSON
        'knowledge_transfer_plan': timeline[6]
    }), 200


# ── PHASE 13: Impact Measurement ───────────────────────────────────────────────

@app.route('/api/cause/<cause_area>/outcome-templates', methods=['GET'])
def cause_outcome_templates(cause_area: str):
    """Get outcome measurement templates for a cause area."""
    cause_area = cause_area.upper().strip()[:2]
    program_type = request.args.get('program_type', '')

    db = get_db()

    query = "SELECT id, outcome_framework, description, key_metrics, measurement_methods, difficulty_to_measure FROM cause_outcome_templates WHERE cause_area=?"
    params = [cause_area]

    if program_type:
        query += " AND program_type = ?"
        params.append(program_type)

    rows = db.execute(query, params).fetchall()

    templates = []
    for row in rows:
        templates.append({
            'id': row[0],
            'framework': row[1],
            'description': row[2],
            'key_metrics': row[3],  # JSON
            'measurement_methods': row[4],  # JSON
            'difficulty': row[5]
        })

    return jsonify({'template_count': len(templates), 'templates': templates}), 200


@app.route('/api/nonprofit/<ein>/impact-report', methods=['GET'])
def nonprofit_impact_report(ein: str):
    """Get nonprofit's impact outcomes (anonymized for research)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    period = request.args.get('period', '')

    db = get_db()

    query = "SELECT reporting_period, program_name, outcome_type, outcome_value, outcome_unit, confidence_level, measurement_method FROM nonprofit_impact_reports WHERE ein=?"
    params = [ein]

    if period:
        query += " AND reporting_period = ?"
        params.append(period)

    query += " ORDER BY reported_at DESC"

    rows = db.execute(query, params).fetchall()

    outcomes = []
    for row in rows:
        outcomes.append({
            'period': row[0],
            'program': row[1],
            'outcome': row[2],
            'value': row[3],
            'unit': row[4],
            'confidence': row[5],
            'method': row[6]
        })

    return jsonify({'ein': ein, 'outcome_count': len(outcomes), 'outcomes': outcomes}), 200


@app.route('/api/nonprofit/<ein>/dashboard/overview', methods=['GET'])
def nonprofit_dashboard_overview(ein: str):
    """Nonprofit overview dashboard: what needs attention, volunteer summary, profile health,
    upcoming events, and recent activity. Requires Firebase auth. Returns only org-specific data."""
    from volunteer_hours_events_api import VOLUNTEER_HOURLY_VALUE

    uid = _require_firebase_user()
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = get_db()

    # Verify user has claimed this org
    claim = db.execute(
        "SELECT claim_status FROM org_claims WHERE ein=? AND firebase_uid=? "
        "AND claim_status IN ('active', 'verified') AND revoked_at IS NULL",
        (ein, uid)
    ).fetchone()
    if not claim:
        return jsonify({'error': 'Not authorized for this organization'}), 403

    # Org basics
    org = db.execute(
        "SELECT EIN, organization_name, mission, website, donate_url, street_address, CITY, STATE FROM registry_enriched WHERE EIN=?",
        (ein,)
    ).fetchone()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    org_name = org['organization_name'] or 'Unnamed Organization'

    # Last profile update (from org_claims or registry_enriched update timestamp)
    last_update = db.execute(
        "SELECT MAX(verified_at) as updated FROM org_claims WHERE ein=?",
        (ein,)
    ).fetchone()
    last_profile_update = last_update['updated'] if last_update['updated'] else None
    days_since_update = 999
    if last_profile_update:
        days_since_update = (datetime.now() - datetime.fromisoformat(last_profile_update)).days

    # Attention items
    pending_approvals = db.execute(
        "SELECT COUNT(*) as cnt FROM volunteer_hours WHERE nonprofit_ein=? AND status='pending'",
        (ein,)
    ).fetchone()['cnt']

    profile_gaps = 0
    gaps = []
    if not org['mission'] or len(str(org['mission']).strip()) < 10:
        profile_gaps += 1
        gaps.append('mission')
    if not org['donate_url']:
        profile_gaps += 1
        gaps.append('donation_link')

    # Volunteer summary
    now = datetime.now()
    this_month = now.strftime('%Y-%m')
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')

    vol_this = db.execute(
        "SELECT COALESCE(SUM(hours), 0) as h FROM volunteer_hours WHERE nonprofit_ein=? AND status='approved' AND substr(service_date, 1, 7)=?",
        (ein, this_month)
    ).fetchone()['h']

    vol_last = db.execute(
        "SELECT COALESCE(SUM(hours), 0) as h FROM volunteer_hours WHERE nonprofit_ein=? AND status='approved' AND substr(service_date, 1, 7)=?",
        (ein, last_month)
    ).fetchone()['h']

    trend_percent = 0
    if vol_last > 0:
        trend_percent = round((vol_this - vol_last) / vol_last * 100, 1)

    pending_count = db.execute(
        "SELECT COUNT(*) as cnt FROM volunteer_hours WHERE nonprofit_ein=? AND status='pending'",
        (ein,)
    ).fetchone()['cnt']

    approved_count = db.execute(
        "SELECT COUNT(*) as cnt FROM volunteer_hours WHERE nonprofit_ein=? AND status='approved'",
        (ein,)
    ).fetchone()['cnt']

    rejected_count = db.execute(
        "SELECT COUNT(*) as cnt FROM volunteer_hours WHERE nonprofit_ein=? AND status='rejected'",
        (ein,)
    ).fetchone()['cnt']

    # Top volunteers this month
    top_vols = db.execute(
        f"""SELECT volunteer_name, SUM(hours) as total_hours FROM volunteer_hours
            WHERE nonprofit_ein=? AND status='approved' AND substr(service_date, 1, 7)=?
            GROUP BY volunteer_name ORDER BY total_hours DESC LIMIT 3""",
        (ein, this_month)
    ).fetchall()
    top_volunteers = [{'name': v['volunteer_name'], 'hours': v['total_hours']} for v in top_vols]

    # Upcoming events (next 30 days)
    upcoming = db.execute(
        """SELECT id AS event_id, title, event_date FROM volunteer_events
           WHERE ein=? AND event_date BETWEEN date('now') AND date('now', '+30 days')
           ORDER BY event_date ASC LIMIT 5""",
        (ein,)
    ).fetchall()

    upcoming_events = []
    for evt in upcoming:
        evt_date = datetime.fromisoformat(evt['event_date']).date()
        days_until = (evt_date - datetime.now().date()).days
        upcoming_events.append({
            'event_id': evt['event_id'],
            'title': evt['title'],
            'date': evt['event_date'],
            'days_until': days_until
        })

    # Profile health (completeness)
    completeness_score = 0
    fields_max = 8
    if org['organization_name']: completeness_score += 1
    if org['EIN']: completeness_score += 1
    if org['mission'] and len(str(org['mission']).strip()) >= 10: completeness_score += 1
    if org['website']: completeness_score += 1
    if org['donate_url']: completeness_score += 1
    if org['street_address']: completeness_score += 1
    if org['CITY']: completeness_score += 1
    if org['STATE']: completeness_score += 1

    completeness_percent = round((completeness_score / fields_max) * 100)

    return jsonify({
        'organization': {
            'ein': org['EIN'],
            'name': org_name,
            'mission': org['mission'],
            'website': org['website'],
            'last_profile_update': last_profile_update,
            'days_since_update': days_since_update
        },
        'attention': {
            'pending_approvals': pending_approvals,
            'profile_gaps': profile_gaps,
            'missing_fields': gaps,
            'needs_review': days_since_update > 90
        },
        'volunteer_summary': {
            'this_month_hours': round(vol_this, 1),
            'last_month_hours': round(vol_last, 1),
            'trend_percent': trend_percent,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'top_volunteers': top_volunteers,
            'labor_value_this_month': round(vol_this * VOLUNTEER_HOURLY_VALUE, 2)
        },
        'profile_health': {
            'completeness_percent': completeness_percent,
            'missing_fields': gaps
        },
        'upcoming_events': upcoming_events,
        'recent_activity': {
            'has_events': len(upcoming_events) > 0
        }
    }), 200


@app.route('/api/cause/<cause_area>/impact-benchmarks', methods=['GET'])
def cause_impact_benchmarks(cause_area: str):
    """Get peer benchmarks for impact outcomes in a cause area."""
    cause_area = cause_area.upper().strip()[:2]
    outcome_type = request.args.get('outcome_type', '')

    db = get_db()

    query = "SELECT outcome_type, program_type, median_outcome_value, percentile_25, percentile_75, org_count_reporting, year_reported FROM peer_outcome_benchmarks WHERE cause_area=?"
    params = [cause_area]

    if outcome_type:
        query += " AND outcome_type = ?"
        params.append(outcome_type)

    rows = db.execute(query, params).fetchall()

    benchmarks = []
    for row in rows:
        benchmarks.append({
            'outcome': row[0],
            'program_type': row[1],
            'median': row[2],
            'peer_range': [row[3], row[4]],
            'orgs_reporting': row[5],
            'year': row[6]
        })

    return jsonify({'benchmark_count': len(benchmarks), 'benchmarks': benchmarks}), 200


# ── Profile Correction & Provenance ──

@app.route('/api/nonprofit/<ein>/profile/editable', methods=['GET'])
def nonprofit_profile_editable(ein: str):
    """Get editable profile fields for nonprofit with current values, sources, and edit history."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = get_db()

    # Verify authorization
    claim = db.execute(
        "SELECT claim_status FROM org_claims WHERE ein=? AND firebase_uid=?",
        (ein, uid)
    ).fetchone()
    if not claim or claim['claim_status'] not in ('active', 'verified'):
        return jsonify({'error': 'Not authorized'}), 403

    org = db.execute(
        "SELECT EIN, organization_name, mission, mission_source, website, website_source, donate_url, donate_url_source FROM registry_enriched WHERE EIN=?",
        (ein,)
    ).fetchone()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    supplied = db.execute(
        "SELECT programs_description, service_areas, nonprofit_contact_email FROM nonprofit_supplied_data WHERE ein=?",
        (ein,)
    ).fetchone()

    # Recent edits (last 10)
    edits = db.execute(
        "SELECT field_name, old_value, new_value, created_at, editor_email, reason, approval_status FROM profile_edits WHERE ein=? ORDER BY created_at DESC LIMIT 10",
        (ein,)
    ).fetchall()

    return jsonify({
        'organization': {
            'ein': org['EIN'],
            'name': org['organization_name']
        },
        'editable_fields': {
            'mission': {
                'value': org['mission'] or '',
                'source': org['mission_source'] or 'irs',
                'editable': True,
                'char_limit': 500,
                'char_count': len(str(org['mission'] or ''))
            },
            'website': {
                'value': org['website'] or '',
                'source': org['website_source'] or 'irs',
                'editable': True
            },
            'donate_url': {
                'value': org['donate_url'] or '',
                'source': org['donate_url_source'] or 'irs',
                'editable': True
            },
            'programs': {
                'value': supplied['programs_description'] if supplied else '',
                'source': 'nonprofit_supplied',
                'editable': True,
                'char_limit': 2000
            },
            'service_areas': {
                'value': supplied['service_areas'] if supplied else '',
                'source': 'nonprofit_supplied',
                'editable': True
            }
        },
        'recent_edits': [
            {
                'field': e['field_name'],
                'old_value': e['old_value'],
                'new_value': e['new_value'],
                'date': e['created_at'],
                'editor': e['editor_email'],
                'reason': e['reason'],
                'status': e['approval_status']
            } for e in edits
        ]
    }), 200


@app.route('/api/nonprofit/<ein>/profile/edit', methods=['POST'])
def nonprofit_profile_edit(ein: str):
    """Submit a profile field edit. Requires Firebase auth."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    data = request.get_json(silent=True) or {}
    field_name = (data.get('field_name') or '').strip()
    new_value = (data.get('new_value') or '').strip()
    reason = (data.get('reason') or '').strip()[:500]
    editor_email = (data.get('nonprofit_email') or '').strip()[:254]

    if not field_name or not new_value:
        return jsonify({'error': 'field_name and new_value are required'}), 400

    if field_name not in ('mission', 'website', 'donate_url', 'programs', 'service_areas'):
        return jsonify({'error': 'Invalid field_name'}), 400

    # Validate field lengths
    if field_name == 'mission' and (len(new_value) < 50 or len(new_value) > 500):
        return jsonify({'error': 'Mission must be 50–500 characters'}), 400
    if field_name == 'programs' and (len(new_value) < 50 or len(new_value) > 2000):
        return jsonify({'error': 'Programs must be 50–2000 characters'}), 400

    db = get_db()

    # Verify authorization
    claim = db.execute(
        "SELECT claim_status FROM org_claims WHERE ein=? AND firebase_uid=?",
        (ein, uid)
    ).fetchone()
    if not claim or claim['claim_status'] not in ('active', 'verified'):
        return jsonify({'error': 'Not authorized'}), 403

    # Get current value
    org = db.execute(
        "SELECT mission, website, donate_url FROM registry_enriched WHERE EIN=?",
        (ein,)
    ).fetchone()

    supplied = db.execute(
        "SELECT programs_description, service_areas FROM nonprofit_supplied_data WHERE ein=?",
        (ein,)
    ).fetchone()

    current_value = {
        'mission': org['mission'],
        'website': org['website'],
        'donate_url': org['donate_url'],
        'programs': supplied['programs_description'] if supplied else '',
        'service_areas': supplied['service_areas'] if supplied else ''
    }.get(field_name, '')

    # No-op check: if value unchanged, return success
    if str(current_value or '').strip() == new_value:
        return jsonify({
            'edit_id': 'no-op',
            'status': 'approved',
            'message': 'Field value unchanged'
        }), 200

    # Record edit
    db.execute(
        "INSERT INTO profile_edits (ein, field_name, old_value, new_value, edit_source, editor_email, reason, approval_status, published_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        (ein, field_name, current_value or '', new_value, 'nonprofit', editor_email, reason, 'approved')
    )

    # Update registry_enriched or nonprofit_supplied_data
    now = datetime.now().isoformat()
    if field_name in ('mission', 'website', 'donate_url'):
        db.execute(
            f"UPDATE registry_enriched SET {field_name}=?, {field_name}_source='nonprofit_supplied', {field_name}_last_verified=? WHERE EIN=?",
            (new_value, now, ein)
        )
    else:
        # Ensure nonprofit_supplied_data row exists
        db.execute(
            "INSERT OR IGNORE INTO nonprofit_supplied_data (ein) VALUES (?)",
            (ein,)
        )
        db.execute(
            f"UPDATE nonprofit_supplied_data SET {field_name}=?, last_updated_at=? WHERE ein=?",
            (new_value, now, ein)
        )

    db.commit()

    return jsonify({
        'edit_id': 'e-' + secrets.token_hex(4),
        'status': 'approved',
        'message': f'{field_name.title()} updated. Visible to donors within 5 minutes.'
    }), 200


@app.route('/api/nonprofit/<ein>/profile/history', methods=['GET'])
def nonprofit_profile_history(ein: str):
    """Get full profile edit history for nonprofit."""
    uid = _require_firebase_user()
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = get_db()

    # Verify authorization
    claim = db.execute(
        "SELECT claim_status FROM org_claims WHERE ein=? AND firebase_uid=?",
        (ein, uid)
    ).fetchone()
    if not claim or claim['claim_status'] not in ('active', 'verified'):
        return jsonify({'error': 'Not authorized'}), 403

    edits = db.execute(
        "SELECT field_name, old_value, new_value, created_at, editor_email, reason, approval_status FROM profile_edits WHERE ein=? ORDER BY created_at DESC",
        (ein,)
    ).fetchall()

    return jsonify({
        'ein': ein,
        'changes': [
            {
                'field': e['field_name'],
                'old_value': e['old_value'],
                'new_value': e['new_value'],
                'date': e['created_at'],
                'editor': e['editor_email'],
                'reason': e['reason'],
                'status': e['approval_status']
            } for e in edits
        ]
    }), 200


@app.route('/api/public/nonprofit/<ein>/profile/sources', methods=['GET'])
def public_profile_sources(ein: str):
    """Public: Show data sources and provenance for nonprofit profile."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 404

    db = get_db()
    org = db.execute(
        "SELECT organization_name, mission, mission_source, website, website_source, donate_url, donate_url_source FROM registry_enriched WHERE EIN=?",
        (ein,)
    ).fetchone()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    supplied = db.execute(
        "SELECT programs_description, service_areas FROM nonprofit_supplied_data WHERE ein=?",
        (ein,)
    ).fetchone()

    source_map = {
        'irs': 'Form 990 (IRS)',
        'nonprofit_supplied': 'Nonprofit-supplied',
        'ai_generated': 'AI-generated (Daanaa)',
        'daanaa_corrected': 'Corrected (Daanaa)'
    }

    return jsonify({
        'ein': ein,
        'sources': {
            'organization_name': {
                'value': org['organization_name'],
                'source': 'irs',
                'source_label': 'Form 990 (IRS)',
                'editable': False
            },
            'mission': {
                'value': org['mission'],
                'source': org['mission_source'] or 'irs',
                'source_label': source_map.get(org['mission_source'] or 'irs', 'Unknown'),
                'editable': True
            },
            'website': {
                'value': org['website'],
                'source': org['website_source'] or 'irs',
                'source_label': source_map.get(org['website_source'] or 'irs', 'Unknown'),
                'editable': True
            },
            'donate_url': {
                'value': org['donate_url'],
                'source': org['donate_url_source'] or 'irs',
                'source_label': source_map.get(org['donate_url_source'] or 'irs', 'Unknown'),
                'editable': True
            },
            'programs': {
                'value': supplied['programs_description'] if supplied else None,
                'source': 'nonprofit_supplied',
                'source_label': 'Nonprofit-supplied',
                'editable': True
            }
        }
    }), 200


@app.route('/api/public/nonprofit/<ein>/feedback', methods=['POST'])
def submit_nonprofit_feedback(ein: str):
    """Public: Submit anonymous feedback about an organization (was it helpful?)."""
    ein = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    data = request.get_json(silent=True) or {}
    was_helpful = data.get('was_helpful')
    category = (data.get('feedback_category') or '').strip()[:100]
    message = (data.get('message') or '').strip()[:500]

    if was_helpful is None:
        return jsonify({'error': 'was_helpful is required'}), 400

    db = get_db()

    # Check org exists
    org = db.execute(
        "SELECT EIN FROM registry_enriched WHERE EIN=?", (ein,)
    ).fetchone()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    # Store feedback (anonymous, no IP, no identifiers)
    db.execute(
        "INSERT OR IGNORE INTO nonprofit_feedback (ein, was_helpful, feedback_category, message, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (ein, 1 if was_helpful else 0, category or None, message or None)
    )

    try:
        db.commit()
    except Exception:
        # Table might not exist yet, create it
        db.execute("""
          CREATE TABLE IF NOT EXISTS nonprofit_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ein TEXT NOT NULL,
            was_helpful INTEGER NOT NULL,
            feedback_category TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
          )
        """)
        db.execute(
            "INSERT INTO nonprofit_feedback (ein, was_helpful, feedback_category, message, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (ein, 1 if was_helpful else 0, category or None, message or None)
        )
        db.commit()

    return jsonify({
        'status': 'ok',
        'message': 'Thank you for your feedback'
    }), 200


@app.route('/api/debug/firebase-uid', methods=['GET'])
def debug_firebase_uid():
    """DEBUG ONLY: Return your authenticated Firebase UID (temporary troubleshooting endpoint)"""
    try:
        uid = _require_firebase_user()
        return jsonify({
            'your_firebase_uid': uid,
            'uid_bytes': list(uid.encode('utf-8')),
            'uid_length': len(uid),
            'message': 'Copy this UID and update org_claims.firebase_uid where ein=123456789'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 401


@app.route('/api/research/datasets', methods=['GET'])
def research_datasets():
    """Browse research-grade datasets (aggregated, anonymized)."""
    cause_area = request.args.get('cause_area', '')
    access_level = request.args.get('access', 'public')

    db = get_db()

    query = "SELECT dataset_name, cause_area, description, org_count, years_covered, access_level, download_url, published_at FROM research_grade_datasets WHERE published_at IS NOT NULL AND access_level IN (?, 'public')"
    params = [access_level]

    if cause_area:
        query += " AND cause_area = ?"
        params.append(cause_area)

    query += " ORDER BY published_at DESC LIMIT 20"

    rows = db.execute(query, params).fetchall()

    datasets = []
    for row in rows:
        datasets.append({
            'name': row[0],
            'cause': row[1],
            'description': row[2],
            'orgs': row[3],
            'years': row[4],
            'access': row[5],
            'url': row[6],
            'published': row[7]
        })

    return jsonify({'dataset_count': len(datasets), 'datasets': datasets}), 200


@app.route('/api/organizations/<ein>/signals')
@limiter.limit("60 per minute")
def get_credibility_signals(ein):
    """Credibility signals: IRS verification, data freshness, expense ratio, peer context, completeness, mission alignment."""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({"error": "Invalid EIN"}), 400

    try:
        from scripts.credibility_signals import compute_signals
        result = compute_signals(ein_clean)
        return jsonify(result), 200
    except ImportError:
        # Fallback for droplet (no local scripts available): proxy to localhost
        try:
            import requests
            resp = requests.get(f'http://localhost:5000/api/organizations/{ein_clean}/signals', timeout=5)
            if resp.status_code == 200:
                return jsonify(resp.json()), 200
        except Exception:
            pass
        return jsonify({
            "ein": ein_clean,
            "error": "Signals unavailable on this deployment",
            "signals": [],
            "composite_confidence": 0,
        }), 503
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "ein": ein_clean,
            "error": str(e),
            "signals": [],
            "composite_confidence": 0,
        }), 500


# ── NEEDS NETWORK API (Phase 3B) ────────────────────────────────────────────────

@app.route('/api/needs', methods=['GET'])
@limiter.limit("100 per minute")
def list_needs():
    """Donor-facing: Search funding/volunteer needs by type, location, cause."""
    db = get_db()
    need_type = request.args.get('type', '').upper()  # FUNDING or VOLUNTEER
    primary_state = request.args.get('state', '').upper()[:2]
    cause_area = request.args.get('cause', '').strip()[:60]
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    try:
        where_clauses = ["status = 'published'"]
        params = []

        if need_type in ('FUNDING', 'VOLUNTEER'):
            where_clauses.append("need_type = ?")
            params.append(need_type)

        if primary_state:
            where_clauses.append("service_states LIKE ?")
            params.append(f'%{primary_state}%')

        if cause_area:
            where_clauses.append("cause_area = ?")
            params.append(cause_area)

        where_sql = " AND ".join(where_clauses)
        offset = (page - 1) * per_page

        cursor = db.execute(f"""
            SELECT need_id, ein, need_type, title, description, amount_needed,
                   deadline_date, cause_area, service_states, published_date,
                   click_count, volunteer_interest_count
            FROM needs
            WHERE {where_sql}
            ORDER BY published_date DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        needs = [dict(row) for row in cursor.fetchall()]

        # Get total count
        count_cursor = db.execute(f"SELECT COUNT(*) FROM needs WHERE {where_sql}", params)
        total = count_cursor.fetchone()[0]

        return jsonify({
            "needs": needs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }), 200
    except Exception as e:
        app.logger.error(f"list_needs error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/nonprofits/<ein>/needs', methods=['GET'])
@limiter.limit("60 per minute")
def get_nonprofit_needs(ein):
    """Nonprofit dashboard: List their own Needs (all statuses)."""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean or len(ein_clean) != 9:
        return jsonify({"error": "Invalid EIN"}), 400

    # Verify nonprofit ownership via Firebase JWT (if auth enabled)
    # For now, allow any access (auth to be added in Phase 4)

    try:
        db = get_db()
        cursor = db.execute("""
            SELECT need_id, need_type, title, description, amount_needed,
                   deadline_date, cause_area, service_states, status,
                   published_date, last_confirmed_date, click_count, volunteer_interest_count
            FROM needs
            WHERE ein = ?
            ORDER BY published_date DESC
        """, (ein_clean,))

        needs = [dict(row) for row in cursor.fetchall()]
        return jsonify({"ein": ein_clean, "needs": needs}), 200
    except Exception as e:
        app.logger.error(f"get_nonprofit_needs error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/nonprofits/<ein>/needs', methods=['POST'])
@limiter.limit("20 per minute")
def create_need(ein):
    """Nonprofit dashboard: Submit a new funding or volunteer Need."""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean or len(ein_clean) != 9:
        return jsonify({"error": "Invalid EIN"}), 400

    try:
        data = request.get_json() or {}
        need_type = data.get('need_type', '').upper()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        amount_needed = data.get('amount_needed', type=int)
        deadline_date = data.get('deadline_date')
        cause_area = data.get('cause_area', '').strip()
        service_states = data.get('service_states', [])  # List of state codes

        # Validation
        if need_type not in ('FUNDING', 'VOLUNTEER'):
            return jsonify({"error": "need_type must be FUNDING or VOLUNTEER"}), 400
        if not title:
            return jsonify({"error": "title required"}), 400
        if not description:
            return jsonify({"error": "description required"}), 400
        if need_type == 'FUNDING' and not amount_needed:
            return jsonify({"error": "amount_needed required for FUNDING needs"}), 400

        # Create need
        import uuid
        need_id = str(uuid.uuid4())
        service_states_json = json.dumps(service_states) if service_states else '[]'

        db = get_db()
        db.execute("""
            INSERT INTO needs
            (need_id, ein, need_type, title, description, amount_needed,
             deadline_date, cause_area, service_states, status, published_date,
             last_confirmed_date, freshness_status, click_count, volunteer_interest_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', datetime('now'), datetime('now'), 'confirmed', 0, 0)
        """, (need_id, ein_clean, need_type, title, description, amount_needed,
              deadline_date, cause_area, service_states_json))

        db.commit()

        return jsonify({
            "need_id": need_id,
            "status": "created",
            "message": "Need saved as draft. Publish when ready."
        }), 201

    except Exception as e:
        app.logger.error(f"create_need error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/needs/<need_id>/confirm', methods=['POST'])
@limiter.limit("60 per minute")
def confirm_need_freshness(need_id):
    """Nonprofit re-confirms a Need is still accurate (freshness check)."""
    try:
        db = get_db()

        db.execute("""
            UPDATE needs
            SET last_confirmed_date = datetime('now'),
                freshness_status = 'confirmed'
            WHERE need_id = ?
        """, (need_id,))

        db.commit()

        return jsonify({"need_id": need_id, "status": "confirmed"}), 200
    except Exception as e:
        app.logger.error(f"confirm_need_freshness error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/needs/<need_id>/interest', methods=['POST'])
@limiter.limit("100 per minute")
def record_need_interest(need_id):
    """Track donor interest in a Need (view, save, share, volunteer)."""
    try:
        data = request.get_json() or {}
        interest_type = data.get('type', 'VIEW')  # VIEW, SAVE, SHARE, VOLUNTEER_APPLICATION

        db = get_db()

        # Get need info
        need_row = db.execute("SELECT ein FROM needs WHERE need_id = ?", (need_id,)).fetchone()
        if not need_row:
            return jsonify({"error": "Need not found"}), 404

        ein = need_row['ein']

        # Record aggregate interest (no user PII — Stewardship P2)
        import uuid
        interest_id = str(uuid.uuid4())
        db.execute("""
            INSERT INTO need_donor_interest
            (interest_id, need_id, ein, interest_type, recorded_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (interest_id, need_id, ein, interest_type))

        # Update click/interest counters
        if interest_type == 'VIEW':
            db.execute("UPDATE needs SET click_count = click_count + 1 WHERE need_id = ?", (need_id,))
        elif interest_type == 'VOLUNTEER_APPLICATION':
            db.execute("UPDATE needs SET volunteer_interest_count = volunteer_interest_count + 1 WHERE need_id = ?", (need_id,))

        db.commit()

        return jsonify({"recorded": True, "interest_type": interest_type}), 200
    except Exception as e:
        app.logger.error(f"record_need_interest error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Register student service blueprint ──────────────────────────────────────────

from student_service_api_routes import student_bp
app.register_blueprint(student_bp)

# ── Eager load embeddings ──────────────────────────────────────────────────────

# Eager load so gunicorn --preload populates the matrix in the master process
# before forking workers. Workers inherit via CoW without re-reading the DB.
# DAANAA_SKIP_EMBEDDINGS=1 (tests) avoids the ~2 GB load on import.
if not os.environ.get("DAANAA_SKIP_EMBEDDINGS"):
    _load_embeddings()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
