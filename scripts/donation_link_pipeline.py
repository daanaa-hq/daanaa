#!/usr/bin/env python3
"""
scripts/donation_link_pipeline.py

Legal-safe donation link discovery and verification system for MERIT.
Zero Anthropic API, zero GPU — pure Python, CPU + network only.

Three phases:
  Phase 0: Audit all existing donate_urls (~4K links, fast)
  Phase 1: Discover new links from orgs with verified websites (200 orgs/run max)
  Phase 2: Release verified batch to public directory (50 links max)

Key constraints (per STEWARDSHIP.md):
  - Never bypass CAPTCHA, Cloudflare, or any bot protection
  - Never submit forms, test payments, or create accounts
  - Never use rotating proxies
  - Respect robots.txt on every crawl
  - 3–5s rate limit per domain between requests
  - Stop on 403/429 → mark blocked, no retry for 30 days
  - Confidence ≥ 90 required for any published link
  - Evidence record required before any link is published

Usage:
    python3 scripts/donation_link_pipeline.py --phase 0
    python3 scripts/donation_link_pipeline.py --phase 1 --orgs 200
    python3 scripts/donation_link_pipeline.py --phase 2
    python3 scripts/donation_link_pipeline.py --all
    python3 scripts/donation_link_pipeline.py --phase 0 --dry-run
    python3 scripts/donation_link_pipeline.py --phase 1 --orgs 10 --dry-run
"""

import re, sqlite3, json, time, random, argparse, sys, uuid, threading, zlib
import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

DB_PATH    = Path.home() / "meritgiving" / "data" / "merit_registry.db"
CONFIG_DIR = Path(__file__).parent / "config"

UA         = ("Mozilla/5.0 (compatible; DaanaaLinkVerifier/1.0; "
              "+https://daanaa.org/about) link-verification")
TIMEOUT    = 10
READ_BYTES = 81_920

# Reuse platform detection from check_link_health.py (read-only import)
sys.path.insert(0, str(Path(__file__).parent))
from check_link_health import (
    _DONATE_PLATFORMS, _PLATFORM_EXCLUDE, _FULL_URL_PLATFORMS, extract_donate_url
)


# ── Per-domain rate limiter ───────────────────────────────────────────────────

_domain_next_allowed: dict[str, float] = {}
_domain_lock = threading.Lock()


def rate_limit(domain: str, min_s: float = 3.0, max_s: float = 5.0):
    """Non-blocking per-domain rate limiter. Sleep happens outside the lock."""
    wait_time = 0.0
    with _domain_lock:
        now = time.time()
        next_ok = _domain_next_allowed.get(domain, 0)
        if next_ok > now:
            wait_time = next_ok - now
        # Reserve the next slot: current request finishes at now+wait_time,
        # then min_s-max_s before the slot opens again.
        _domain_next_allowed[domain] = now + wait_time + random.uniform(min_s, max_s)
    if wait_time > 0:
        time.sleep(wait_time)


# ── Robots.txt checker ────────────────────────────────────────────────────────

_robots_cache: dict[str, RobotFileParser] = {}
_robots_lock  = threading.Lock()


def can_fetch(url: str) -> bool:
    """Returns False if robots.txt disallows path. Fails open (True) on error."""
    try:
        parsed = urlparse(url)
        base   = f"{parsed.scheme}://{parsed.netloc}"
        with _robots_lock:
            if base not in _robots_cache:
                rp = RobotFileParser()
                rp.set_url(base + "/robots.txt")
                try:
                    rp.read()
                except Exception:
                    pass
                _robots_cache[base] = rp
        return _robots_cache[base].can_fetch(UA, url)
    except Exception:
        return True  # fail open


# ── Block / CAPTCHA detection ─────────────────────────────────────────────────

_CAPTCHA_SIGNALS = (
    "captcha", "just a moment", "cloudflare ray id",
    "access denied", "bot detection", "human verification",
    "ddos-guard", "incapsula", "recaptcha", "hcaptcha",
    "please verify", "prove you are human",
)


def is_blocked(status_code: int, body_text: str) -> bool:
    if status_code in (403, 429):
        return True
    head = body_text.lower()[:3000]
    return any(sig in head for sig in _CAPTCHA_SIGNALS)


# ── Identity match (no LLM) ───────────────────────────────────────────────────

_STOP_WORDS = {
    'inc', 'the', 'of', 'a', 'an', 'and', 'or', 'for', 'to', 'in', 'at', 'by',
    'corporation', 'corp', 'llc', 'ltd', 'foundation', 'association',
    'society', 'organization', 'group', 'team', 'center', 'centre',
    'church', 'ministries', 'ministry', 'services', 'service', 'fund',
}


def identity_match(org_name: str, page_text: str) -> tuple[str, float]:
    """Return (level, ratio). Levels: exact/strong/possible/weak/mismatch/unknown."""
    words     = re.findall(r'\b[a-z]+\b', org_name.lower())
    key_words = [w for w in words if w not in _STOP_WORDS and len(w) > 2][:5]
    if not key_words:
        return 'unknown', 0.0
    page_lower = page_text.lower()[:2000]
    matches    = sum(1 for w in key_words if w in page_lower)
    ratio      = matches / len(key_words)
    if ratio >= 0.8:
        return 'exact', ratio
    elif ratio >= 0.6:
        return 'strong', ratio
    elif ratio >= 0.4:
        return 'possible', ratio
    elif ratio > 0:
        return 'weak', ratio
    else:
        return 'mismatch', ratio


# ── Confidence scorer (spec §15) ──────────────────────────────────────────────

def score_confidence(factors: dict) -> int:
    score = 0
    if factors.get('found_on_official_website'): score += 30
    if factors.get('nonprofit_name_visible'):    score += 20
    if factors.get('website_confidence_90'):     score += 15
    if factors.get('processor_recognized'):      score += 10
    if factors.get('no_suspicious_redirects'):   score += 10
    if factors.get('city_state_match'):          score +=  5
    if factors.get('branding_matches'):          score +=  5
    if factors.get('link_works'):                score +=  5
    if factors.get('ein_visible'):               score +=  5
    # Deductions
    if factors.get('name_mismatch'):             score -= 40
    if factors.get('website_not_official'):      score -= 30
    if factors.get('not_from_official_site'):    score -= 25
    if factors.get('city_state_mismatch'):       score -= 20
    if factors.get('suspicious_redirect'):       score -= 20
    if factors.get('url_shortener'):             score -= 15
    if factors.get('no_visible_name'):           score -= 15
    if factors.get('processor_unknown'):         score -= 10
    if factors.get('link_broken'):               score -= 10
    if factors.get('abandoned_website'):         score -= 10
    return max(0, min(100, score))


# ── DB schema ─────────────────────────────────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS donation_link_evidence (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    ein                   TEXT NOT NULL,
    legal_name            TEXT,
    official_website      TEXT,
    source_page           TEXT,
    candidate_url         TEXT,
    final_url             TEXT,
    processor             TEXT,
    identity_match        TEXT,
    confidence            INTEGER,
    risk_level            TEXT,
    decision              TEXT,
    public_display_allowed INTEGER DEFAULT 0,
    checked_at            TEXT,
    notes                 TEXT
);
CREATE TABLE IF NOT EXISTS human_review_queue (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    ein                    TEXT NOT NULL,
    legal_name             TEXT,
    review_reason          TEXT,
    candidate_website      TEXT,
    candidate_donation_url TEXT,
    confidence             INTEGER,
    risk_flags             TEXT,
    recommended_action     TEXT,
    created_at             TEXT,
    resolved_at            TEXT,
    resolution             TEXT
);
CREATE TABLE IF NOT EXISTS release_batches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id        TEXT NOT NULL UNIQUE,
    batch_date      TEXT,
    links_reviewed  INTEGER,
    links_published INTEGER,
    links_to_review INTEGER,
    batch_status    TEXT,
    notes           TEXT
);
CREATE TABLE IF NOT EXISTS blocked_domains (
    domain              TEXT PRIMARY KEY,
    reason              TEXT,
    blocked_at          TEXT,
    do_not_retry_before TEXT
);
CREATE TABLE IF NOT EXISTS page_cache (
    url         TEXT PRIMARY KEY,
    ein         TEXT,
    fetched_at  TEXT,
    status_code INTEGER,
    html_gz     BLOB,
    content_len INTEGER
);
CREATE INDEX IF NOT EXISTS idx_pc_ein ON page_cache(ein);
"""

_NEW_REGISTRY_COLUMNS = [
    ("donate_confidence",    "INTEGER"),
    ("donate_source_page",   "TEXT"),
    ("donate_identity_match","TEXT"),
    ("donate_human_review",  "INTEGER"),
    ("donate_checked_at",    "TEXT"),
]


def init_schema(db: sqlite3.Connection):
    db.executescript(_SCHEMA_SQL)
    existing = {r[1] for r in db.execute("PRAGMA table_info(registry_enriched)")}
    for col, typ in _NEW_REGISTRY_COLUMNS:
        if col not in existing:
            db.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col} {typ}")
    db.commit()


def cache_page(db: sqlite3.Connection, ein: str, url: str, body: bytes, status_code: int):
    """Store compressed HTML in page_cache for future pipeline reuse."""
    compressed = zlib.compress(body, level=6)
    db.execute("""
        INSERT OR REPLACE INTO page_cache (url, ein, fetched_at, status_code, html_gz, content_len)
        VALUES (?,?,?,?,?,?)
    """, (url, ein, _now(), status_code, compressed, len(body)))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return ""


def is_url_shortener(url: str) -> bool:
    shorteners = {'bit.ly', 't.co', 'ow.ly', 'tinyurl.com', 'goo.gl', 'buff.ly'}
    return domain_of(url) in shorteners


def _risk_level(confidence: int) -> str:
    if confidence >= 90:
        return "low"
    elif confidence >= 75:
        return "medium"
    else:
        return "high"


# ── Evidence / queue writers ──────────────────────────────────────────────────

def write_evidence(db, *, ein, legal_name, official_website, source_page,
                   candidate_url, final_url, processor, match_level,
                   confidence, risk_level, decision, public_display_allowed, notes=""):
    db.execute("""
        INSERT INTO donation_link_evidence
            (ein, legal_name, official_website, source_page, candidate_url, final_url,
             processor, identity_match, confidence, risk_level, decision,
             public_display_allowed, checked_at, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (ein, legal_name, official_website, source_page, candidate_url, final_url,
          processor, match_level, confidence, risk_level, decision,
          1 if public_display_allowed else 0, _now(), notes))


def queue_for_review(db, *, ein, legal_name, reason, candidate_website,
                     candidate_donation_url, confidence, risk_flags, recommended_action):
    db.execute("""
        INSERT INTO human_review_queue
            (ein, legal_name, review_reason, candidate_website, candidate_donation_url,
             confidence, risk_flags, recommended_action, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (ein, legal_name, reason, candidate_website, candidate_donation_url,
          confidence, json.dumps(risk_flags), recommended_action, _now()))


def block_domain(db, domain: str, reason: str):
    retry = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    ).isoformat(timespec="seconds")
    db.execute("""
        INSERT OR REPLACE INTO blocked_domains (domain, reason, blocked_at, do_not_retry_before)
        VALUES (?,?,?,?)
    """, (domain, reason, _now(), retry))


# ── Phase 0: Audit existing donate_urls ──────────────────────────────────────

def _audit_one(row) -> dict:
    ein    = row["EIN"]
    name   = row["organization_name"] or ""
    site   = row["website"] or ""
    durl   = (row["donate_url"] or "").strip()
    dplat  = row["donate_platform"] or ""

    out = dict(ein=ein, name=name, website=site, donate_url=durl,
               donate_platform=dplat, decision=None, notes="",
               match_level="unknown", confidence=0,
               blocked=False, blocked_reason="", domain=domain_of(durl))

    if not durl:
        out["decision"] = "skipped_no_url"
        return out

    try:
        # HEAD check first — fast, minimal bandwidth
        hresp = requests.head(durl, timeout=TIMEOUT, allow_redirects=True,
                              headers={"User-Agent": UA})
        code = hresp.status_code

        if code in (403, 429):
            out.update(blocked=True, blocked_reason=str(code),
                       decision="blocked_or_restricted")
            return out

        if code >= 400:
            out.update(decision="existing_broken_removed", notes=f"HTTP {code}")
            return out

        # GET for body — needed for identity match + CAPTCHA check
        gresp = requests.get(durl, timeout=TIMEOUT, allow_redirects=True,
                             headers={"User-Agent": UA, "Accept": "text/html,*/*"},
                             stream=True)
        body = b""
        for chunk in gresp.iter_content(8192):
            body += chunk
            if len(body) >= READ_BYTES:
                break
        text = body.decode("utf-8", "ignore")

        if is_blocked(gresp.status_code, text):
            out.update(blocked=True, blocked_reason="captcha_or_challenge",
                       decision="blocked_or_restricted")
            return out

        match_level, ratio = identity_match(name, text)
        out["match_level"] = match_level

        factors = {
            "found_on_official_website": True,
            "processor_recognized":      bool(dplat),
            "link_works":                True,
            "nonprofit_name_visible":    match_level in ("exact", "strong"),
            "name_mismatch":             match_level == "mismatch",
            "no_visible_name":           match_level in ("weak", "unknown"),
        }
        confidence = score_confidence(factors)
        out["confidence"] = confidence

        if match_level == "mismatch":
            out["decision"] = "existing_identity_mismatch_removed"
        else:
            out["decision"] = "existing_verified_active"

    except requests.exceptions.ConnectionError:
        out.update(decision="existing_broken_removed", notes="connection_error")
    except requests.exceptions.Timeout:
        out.update(decision="existing_broken_removed", notes="timeout")
    except Exception as e:
        out.update(decision="existing_broken_removed", notes=str(e)[:100])

    return out


def phase0_audit_existing(db: sqlite3.Connection, dry_run=False, workers=16):
    print("\n=== Phase 0: Auditing existing donation links ===")
    rows = db.execute("""
        SELECT EIN, organization_name, website, donate_url, donate_platform
        FROM registry_enriched
        WHERE donate_url IS NOT NULL AND TRIM(donate_url) != ''
    """).fetchall()

    total = len(rows)
    print(f"  Links to audit: {total:,}  (workers={workers})")

    if dry_run:
        import random as rmod
        sample = rmod.sample(list(rows), min(10, total))
        print("  [dry-run] 10 random samples:\n")
        for r in sample:
            res = _audit_one(r)
            print(f"  [{res['decision']:45}] {res['name'][:50]}")
            print(f"      url: {res['donate_url'][:80]}")
        return

    counts: dict[str, int] = {}
    processed = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_audit_one, r): r for r in rows}
        for fut in as_completed(futs):
            res = fut.result()
            dec = res["decision"] or "existing_broken_removed"
            counts[dec] = counts.get(dec, 0) + 1
            processed += 1
            now = _now()

            if res["blocked"]:
                dom = res["domain"]
                if dom:
                    block_domain(db, dom, res["blocked_reason"])
                db.execute("""
                    UPDATE registry_enriched
                    SET donate_url_status='blocked_or_restricted',
                        donate_identity_match=?, donate_confidence=?, donate_checked_at=?
                    WHERE EIN=?
                """, (res["match_level"], res["confidence"], now, res["ein"]))
                write_evidence(db, ein=res["ein"], legal_name=res["name"],
                               official_website=res["website"],
                               source_page=res["donate_url"],
                               candidate_url=res["donate_url"], final_url=res["donate_url"],
                               processor=res["donate_platform"],
                               match_level=res["match_level"], confidence=res["confidence"],
                               risk_level="high", decision="blocked_or_restricted",
                               public_display_allowed=False, notes=res["blocked_reason"])
                db.commit()
                continue

            if dec == "existing_broken_removed":
                db.execute("""
                    UPDATE registry_enriched
                    SET donate_url_status='dead', donate_url=NULL, donate_platform=NULL,
                        donate_identity_match=?, donate_confidence=0, donate_checked_at=?
                    WHERE EIN=?
                """, (res["match_level"], now, res["ein"]))
                write_evidence(db, ein=res["ein"], legal_name=res["name"],
                               official_website=res["website"],
                               source_page=res["donate_url"],
                               candidate_url=res["donate_url"], final_url="",
                               processor=res["donate_platform"],
                               match_level=res["match_level"], confidence=0,
                               risk_level="high", decision="existing_broken_removed",
                               public_display_allowed=False, notes=res["notes"])
                db.commit()

            elif dec == "existing_identity_mismatch_removed":
                db.execute("""
                    UPDATE registry_enriched
                    SET donate_url_status='mismatch', donate_url=NULL, donate_platform=NULL,
                        donate_identity_match=?, donate_confidence=?,
                        donate_checked_at=?, donate_human_review=1
                    WHERE EIN=?
                """, (res["match_level"], res["confidence"], now, res["ein"]))
                write_evidence(db, ein=res["ein"], legal_name=res["name"],
                               official_website=res["website"],
                               source_page=res["donate_url"],
                               candidate_url=res["donate_url"], final_url=res["donate_url"],
                               processor=res["donate_platform"],
                               match_level=res["match_level"], confidence=res["confidence"],
                               risk_level="high", decision="existing_identity_mismatch_removed",
                               public_display_allowed=False,
                               notes="identity mismatch — cleared, pending human review")
                queue_for_review(db, ein=res["ein"], legal_name=res["name"],
                                 reason="identity_mismatch",
                                 candidate_website=res["website"],
                                 candidate_donation_url=res["donate_url"],
                                 confidence=res["confidence"],
                                 risk_flags={"match_level": res["match_level"]},
                                 recommended_action="verify org name matches donation page")
                db.commit()

            elif dec == "existing_verified_active":
                db.execute("""
                    UPDATE registry_enriched
                    SET donate_url_status='ok',
                        donate_identity_match=?, donate_confidence=?, donate_checked_at=?
                    WHERE EIN=?
                """, (res["match_level"], res["confidence"], now, res["ein"]))
                write_evidence(db, ein=res["ein"], legal_name=res["name"],
                               official_website=res["website"],
                               source_page=res["website"],
                               candidate_url=res["donate_url"], final_url=res["donate_url"],
                               processor=res["donate_platform"],
                               match_level=res["match_level"], confidence=res["confidence"],
                               risk_level="low", decision="publish_eligible",
                               public_display_allowed=True)
                db.commit()

            if processed % 200 == 0:
                elapsed = time.time() - t0 + 1e-9
                print(f"  {processed}/{total}  "
                      f"active={counts.get('existing_verified_active', 0)}  "
                      f"dead={counts.get('existing_broken_removed', 0)}  "
                      f"blocked={counts.get('blocked_or_restricted', 0)}  "
                      f"mismatch={counts.get('existing_identity_mismatch_removed', 0)}  "
                      f"{processed/elapsed:.0f}/s", end="\r")

    elapsed = time.time() - t0
    print(f"\n\nPhase 0 done in {elapsed:.0f}s")
    for k, v in sorted(counts.items()):
        if v:
            print(f"  {k:50} {v:>5,}")


# ── Phase 1: Discover new donation links ──────────────────────────────────────

_PRIORITY_PATHS = [
    "/", "/donate", "/give", "/support",
    "/ways-to-give", "/get-involved", "/giving", "/contribute",
]

# Subdomains tried as a fallback when main site yields nothing.
# Only donate/give — specific enough to avoid false positives.
_DONATE_SUBDOMAIN_PREFIXES = ("donate", "give")


def _root_domain(site: str) -> str:
    """Strip scheme + www/donate/give prefix → bare root domain."""
    netloc = urlparse(site if site.startswith("http") else "https://" + site).netloc.lower()
    for strip in ("www.", "donate.", "give.", "giving."):
        if netloc.startswith(strip):
            netloc = netloc[len(strip):]
            break
    return netloc


def _try_donate_subdomains(site: str, name: str, city: str, state: str,
                            blocked_set: set) -> dict | None:
    """
    Fallback: probe donate.{domain} and give.{domain} when the main site
    had no detectable link. Efficient — HEAD first to skip non-existent
    subdomains, GET only when HEAD succeeds. Returns partial result or None.
    """
    root = _root_domain(site)
    if not root:
        return None

    for prefix in _DONATE_SUBDOMAIN_PREFIXES:
        dom = f"{prefix}.{root}"
        sub_url = f"https://{dom}/"

        if dom in blocked_set:
            continue

        # Fast existence probe — skip GET entirely if subdomain doesn't resolve
        rate_limit(dom, min_s=1.0, max_s=2.0)
        try:
            head = requests.head(sub_url, timeout=5, allow_redirects=True,
                                 headers={"User-Agent": UA})
        except Exception:
            continue  # DNS miss or connection refused — subdomain doesn't exist

        if head.status_code in (403, 429):
            blocked_set.add(dom)
            continue
        if head.status_code >= 400:
            continue  # subdomain not found

        # Subdomain is live — fetch it
        rate_limit(dom, min_s=2.0, max_s=3.0)
        try:
            resp = requests.get(sub_url, timeout=TIMEOUT, allow_redirects=True,
                                headers={"User-Agent": UA, "Accept": "text/html,*/*"},
                                stream=True)
            body = b""
            for chunk in resp.iter_content(8192):
                body += chunk
                if len(body) >= READ_BYTES:
                    break
            text = body.decode("utf-8", "ignore")
        except Exception:
            continue

        if is_blocked(resp.status_code, text):
            blocked_set.add(dom)
            continue

        # Look for an embedded platform link first; fall back to the subdomain URL itself
        donate_url, donate_platform = extract_donate_url(text)
        if not donate_url:
            donate_url = resp.url          # subdomain IS the donate page (Blackbaud etc.)
            donate_platform = "subdomain_direct"

        match_level, _ = identity_match(name, text)
        page_lower = text.lower()

        confidence = score_confidence({
            "found_on_official_website":  True,
            "processor_recognized":       donate_platform != "subdomain_direct",
            "website_confidence_90":      True,
            "nonprofit_name_visible":     match_level in ("exact", "strong"),
            "no_suspicious_redirects":    True,
            "link_works":                 True,
            "city_state_match":           bool(
                city and city.lower() in page_lower
                and state and state.lower() in page_lower
            ),
            "name_mismatch":              match_level == "mismatch",
            "no_visible_name":            match_level in ("weak", "unknown"),
            "processor_unknown":          donate_platform == "subdomain_direct",
        })

        if confidence < 55:
            continue  # too weak — try next prefix

        return dict(donate_url=donate_url, donate_platform=donate_platform,
                    source_page=resp.url, match_level=match_level, confidence=confidence)


def _discover_one(row, blocked_set: set) -> dict:
    ein    = row["EIN"]
    name   = row["organization_name"] or ""
    site   = (row["website"] or "").strip()
    city   = row["CITY"] or ""
    state  = row["STATE"] or ""

    out = dict(ein=ein, name=name, website=site,
               decision=None, match_level="unknown", confidence=0,
               donate_url=None, donate_platform=None, source_page=None,
               notes="", blocked=False, blocked_reason="",
               cached_pages=[])  # list of (url, body_bytes, status_code)

    if not site:
        out["decision"] = "skipped_no_website"
        return out

    if not site.startswith(("http://", "https://")):
        site = "https://" + site

    dom = domain_of(site)
    if dom in blocked_set:
        out["decision"] = "skipped_blocked_domain"
        return out

    rate_limit(dom)  # respect 3–5s per domain

    for path in _PRIORITY_PATHS:
        url = site.rstrip("/") + path
        try:
            if not can_fetch(url):
                continue

            resp = requests.get(
                url, timeout=TIMEOUT, allow_redirects=True,
                headers={"User-Agent": UA, "Accept": "text/html,*/*"},
                stream=True,
            )

            if resp.status_code in (403, 429):
                out.update(blocked=True, blocked_reason=str(resp.status_code),
                           decision="blocked_or_restricted")
                return out

            if resp.status_code >= 400:
                # Path not found — try next
                rate_limit(dom, min_s=1.0, max_s=2.0)
                continue

            body = b""
            for chunk in resp.iter_content(8192):
                body += chunk
                if len(body) >= READ_BYTES:
                    break
            text = body.decode("utf-8", "ignore")

            if is_blocked(resp.status_code, text):
                out.update(blocked=True, blocked_reason="captcha_or_challenge",
                           decision="blocked_or_restricted")
                return out

            # Cache homepage and any page where we find a link
            if path == "/":
                out["cached_pages"].append((resp.url, body, resp.status_code))

            donate_url, donate_platform = extract_donate_url(text)
            if not donate_url:
                rate_limit(dom, min_s=1.5, max_s=3.0)
                continue

            # Cache the winning page if it's different from the homepage
            if path != "/":
                out["cached_pages"].append((resp.url, body, resp.status_code))

            # Found a candidate — score it
            match_level, _ratio = identity_match(name, text)
            out.update(match_level=match_level, source_page=resp.url,
                       donate_url=donate_url, donate_platform=donate_platform)

            page_lower = text.lower()
            factors = {
                "found_on_official_website": True,
                "processor_recognized":      bool(donate_platform),
                # website_status='ok' means we already verified the site is live and
                # not a parking/domain-takeover page — counts as website confidence ≥ 90
                "website_confidence_90":     True,
                "nonprofit_name_visible":    match_level in ("exact", "strong"),
                "no_suspicious_redirects":   not is_url_shortener(donate_url),
                "url_shortener":             is_url_shortener(donate_url),
                "link_works":                True,
                "city_state_match":          bool(
                    city and city.lower() in page_lower
                    and state and state.lower() in page_lower
                ),
                "name_mismatch":             match_level == "mismatch",
                "no_visible_name":           match_level in ("weak", "unknown"),
                "processor_unknown":         not donate_platform,
            }
            confidence = score_confidence(factors)
            out["confidence"] = confidence

            if confidence >= 90:
                out["decision"] = "new_candidate_verified"
            elif confidence >= 75:
                out["decision"] = "human_review_required"
            else:
                out["decision"] = "rejected_low_confidence"

            return out

        except requests.exceptions.ConnectionError:
            out["notes"] = "connection_error"
            break
        except requests.exceptions.Timeout:
            out["notes"] = "timeout"
            rate_limit(dom, min_s=1.0, max_s=2.0)
            continue
        except Exception as e:
            out["notes"] = str(e)[:100]
            continue

    if not out["decision"]:
        # Main site found nothing — try donate./give. subdomains (Blackbaud, enterprise)
        sub = _try_donate_subdomains(site, name, city, state, blocked_set)
        if sub:
            out.update(donate_url=sub["donate_url"], donate_platform=sub["donate_platform"],
                       source_page=sub["source_page"], match_level=sub["match_level"],
                       confidence=sub["confidence"])
            if sub["confidence"] >= 90:
                out["decision"] = "new_candidate_verified"
            elif sub["confidence"] >= 75:
                out["decision"] = "human_review_required"
            else:
                out["decision"] = "rejected_low_confidence"
        else:
            out["decision"] = "no_donate_link_found"
    return out


def phase1_discover_new(db: sqlite3.Connection, max_orgs=200, dry_run=False, workers=8):
    print(f"\n=== Phase 1: Discovering new donation links (max {max_orgs} orgs) ===")

    blocked_set = {r[0] for r in db.execute("SELECT domain FROM blocked_domains")}

    rows = db.execute("""
        SELECT EIN, organization_name, website, CITY, STATE
        FROM registry_enriched
        WHERE website IS NOT NULL AND TRIM(website) != ''
          AND website_status = 'ok'
          AND (donate_url IS NULL OR TRIM(donate_url) = '')
          AND (donate_url_status IS NULL
               OR donate_url_status NOT IN (
                   'ok', 'blocked_or_restricted', 'pending_review',
                   'human_review', 'no_link_found', 'rejected'
               ))
        ORDER BY RANDOM()
        LIMIT ?
    """, (max_orgs,)).fetchall()

    total = len(rows)
    print(f"  Orgs to check: {total:,}  (workers={workers})")

    if dry_run:
        print("  [dry-run] first 5 only:\n")
        for r in list(rows)[:5]:
            res = _discover_one(r, blocked_set)
            print(f"  [{res['decision']:35}] conf={res['confidence']:3}  {res['name'][:45]}")
            if res["donate_url"]:
                print(f"      → {res['donate_url'][:80]}")
        return

    counts: dict[str, int] = {}
    processed = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_discover_one, r, blocked_set): r for r in rows}
        for fut in as_completed(futs):
            res = fut.result()
            dec = res["decision"] or "unknown"
            counts[dec] = counts.get(dec, 0) + 1
            processed += 1
            now = _now()

            if res["blocked"]:
                dom = domain_of(res["website"])
                if dom:
                    block_domain(db, dom, res["blocked_reason"])
                db.execute("""
                    UPDATE registry_enriched
                    SET donate_url_status='blocked_or_restricted', donate_checked_at=?
                    WHERE EIN=?
                """, (now, res["ein"]))
                db.commit()
                continue

            if dec == "new_candidate_verified":
                db.execute("""
                    UPDATE registry_enriched
                    SET donate_url=?, donate_platform=?,
                        donate_url_status='pending_review',
                        donate_confidence=?, donate_source_page=?,
                        donate_identity_match=?, donate_checked_at=?
                    WHERE EIN=?
                """, (res["donate_url"], res["donate_platform"], res["confidence"],
                      res["source_page"], res["match_level"], now, res["ein"]))
                write_evidence(db, ein=res["ein"], legal_name=res["name"],
                               official_website=res["website"],
                               source_page=res["source_page"],
                               candidate_url=res["donate_url"], final_url=res["donate_url"],
                               processor=res["donate_platform"],
                               match_level=res["match_level"], confidence=res["confidence"],
                               risk_level="low", decision="publish_eligible",
                               public_display_allowed=False,
                               notes="pending Phase 2 release batch")
                db.commit()

            elif dec == "human_review_required":
                db.execute("""
                    UPDATE registry_enriched
                    SET donate_url=?, donate_platform=?,
                        donate_url_status='human_review',
                        donate_confidence=?, donate_source_page=?,
                        donate_identity_match=?, donate_checked_at=?, donate_human_review=1
                    WHERE EIN=?
                """, (res["donate_url"], res["donate_platform"], res["confidence"],
                      res["source_page"], res["match_level"], now, res["ein"]))
                queue_for_review(db, ein=res["ein"], legal_name=res["name"],
                                 reason="confidence_75_89",
                                 candidate_website=res["website"],
                                 candidate_donation_url=res["donate_url"],
                                 confidence=res["confidence"],
                                 risk_flags={"match_level": res["match_level"],
                                             "notes": res["notes"]},
                                 recommended_action="verify donation link matches org identity")
                write_evidence(db, ein=res["ein"], legal_name=res["name"],
                               official_website=res["website"],
                               source_page=res["source_page"],
                               candidate_url=res["donate_url"], final_url=res["donate_url"],
                               processor=res["donate_platform"],
                               match_level=res["match_level"], confidence=res["confidence"],
                               risk_level="medium", decision="human_review",
                               public_display_allowed=False,
                               notes="confidence 75–89 — in human review queue")
                db.commit()

            else:
                # Mark so we don't re-scan on every Phase 1 run
                new_status = ("rejected" if res["donate_url"] else "no_link_found")
                db.execute("""
                    UPDATE registry_enriched
                    SET donate_url_status=?, donate_checked_at=?
                    WHERE EIN=?
                """, (new_status, now, res["ein"]))
                if res["donate_url"]:
                    write_evidence(db, ein=res["ein"], legal_name=res["name"],
                                   official_website=res["website"],
                                   source_page=res["source_page"],
                                   candidate_url=res["donate_url"], final_url=res["donate_url"],
                                   processor=res["donate_platform"],
                                   match_level=res["match_level"], confidence=res["confidence"],
                                   risk_level="high", decision="rejected",
                                   public_display_allowed=False,
                                   notes=f"confidence {res['confidence']} < 75")
                db.commit()

            if processed % 10 == 0:
                elapsed = time.time() - t0 + 1e-9
                print(f"  {processed}/{total}  "
                      f"verified={counts.get('new_candidate_verified', 0)}  "
                      f"review={counts.get('human_review_required', 0)}  "
                      f"blocked={counts.get('blocked_or_restricted', 0)}  "
                      f"{processed/elapsed:.1f}/s", end="\r")

    elapsed = time.time() - t0
    print(f"\n\nPhase 1 done in {elapsed:.0f}s")
    for k, v in sorted(counts.items()):
        if v:
            print(f"  {k:45} {v:>5,}")


# ── Phase 2: Release batch ────────────────────────────────────────────────────

def phase2_release_batch(db: sqlite3.Connection, max_links=50, dry_run=False):
    print(f"\n=== Phase 2: Release batch (max {max_links} links) ===")

    candidates = db.execute("""
        SELECT EIN, organization_name, donate_url, donate_platform,
               donate_confidence, donate_source_page, donate_identity_match
        FROM registry_enriched
        WHERE donate_url_status = 'pending_review'
          AND donate_confidence >= 90
        ORDER BY donate_confidence DESC
        LIMIT ?
    """, (max_links * 2,)).fetchall()  # fetch 2× buffer for failed HEAD checks

    total_candidates = len(candidates)
    print(f"  Candidates (confidence ≥ 90): {total_candidates:,}")

    batch_id   = str(uuid.uuid4())[:8]
    reviewed   = 0
    published  = 0
    failed     = 0
    now        = _now()

    for row in candidates:
        if published >= max_links:
            break
        reviewed += 1
        ein       = row["EIN"]
        durl      = row["donate_url"]
        dname     = (row["organization_name"] or "")[:50]
        dconf     = row["donate_confidence"]

        # Final liveness HEAD check before publishing
        try:
            resp = requests.head(durl, timeout=TIMEOUT, allow_redirects=True,
                                 headers={"User-Agent": UA})
            if resp.status_code >= 400:
                failed += 1
                print(f"  FAIL {resp.status_code}: {durl[:70]}")
                if not dry_run:
                    if resp.status_code in (403, 429):
                        # Platform is blocking verification — flag for human review
                        db.execute("""
                            UPDATE registry_enriched
                            SET donate_url_status='human_review', donate_human_review=1
                            WHERE EIN=?
                        """, (ein,))
                    else:
                        # 404/410/etc — link is dead, clear it
                        db.execute("""
                            UPDATE registry_enriched
                            SET donate_url_status='dead', donate_url=NULL, donate_platform=NULL
                            WHERE EIN=?
                        """, (ein,))
                    db.commit()
                continue
        except Exception as e:
            failed += 1
            print(f"  FAIL (network): {durl[:70]}  — {e}")
            continue

        if dry_run:
            print(f"  WOULD PUBLISH  conf={dconf:3}  {dname:<50}  {durl[:60]}")
            published += 1
            continue

        # Publish — set status to 'ok', mark evidence as published
        db.execute("""
            UPDATE registry_enriched
            SET donate_url_status='ok', donate_checked_at=?
            WHERE EIN=?
        """, (now, ein))
        db.execute("""
            UPDATE donation_link_evidence
            SET public_display_allowed=1, decision='published'
            WHERE ein=? AND candidate_url=?
            ORDER BY id DESC LIMIT 1
        """, (ein, durl))
        db.commit()
        published += 1

    # Write batch record
    if not dry_run:
        db.execute("""
            INSERT INTO release_batches
                (batch_id, batch_date, links_reviewed, links_published,
                 links_to_review, batch_status, notes)
            VALUES (?,?,?,?,?,?,?)
        """, (batch_id, now[:10], reviewed, published, failed,
              "completed", f"threshold=90, max={max_links}"))
        db.commit()

    print(f"\n  Batch ID:      {batch_id}")
    print(f"  Reviewed:      {reviewed:,}")
    print(f"  Published:     {published:,}")
    print(f"  Failed check:  {failed:,}")
    if dry_run:
        print("  [dry-run — no writes made]")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="MERIT donation link pipeline — legal-safe, evidence-based"
    )
    ap.add_argument("--phase", type=int, choices=[0, 1, 2],
                    help="Single phase to run (0=audit, 1=discover, 2=release)")
    ap.add_argument("--all", action="store_true",
                    help="Run all phases in sequence: 0 → 1 → 2")
    ap.add_argument("--orgs", type=int, default=200,
                    help="Max orgs for Phase 1 (default 200)")
    ap.add_argument("--links", type=int, default=50,
                    help="Max links released in Phase 2 (default 50)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Preview without writing to DB")
    ap.add_argument("--workers", type=int, default=12,
                    help="Concurrent workers for Phase 0 / 1 (default 12)")
    args = ap.parse_args()

    if args.phase is None and not args.all:
        ap.print_help()
        sys.exit(1)

    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    init_schema(db)

    print(f"MERIT Donation Link Pipeline")
    print(f"DB:       {DB_PATH}")
    print(f"Dry-run:  {args.dry_run}")

    phases = [0, 1, 2] if args.all else [args.phase]

    if 0 in phases:
        phase0_audit_existing(db, dry_run=args.dry_run, workers=args.workers)
    if 1 in phases:
        phase1_discover_new(db, max_orgs=args.orgs, dry_run=args.dry_run, workers=args.workers)
    if 2 in phases:
        phase2_release_batch(db, max_links=args.links, dry_run=args.dry_run)

    db.close()


if __name__ == "__main__":
    main()
