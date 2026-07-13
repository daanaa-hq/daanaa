#!/usr/bin/env python3
"""
Website content validation and fetch for the enrichment pipeline.

Given a CANDIDATE domain (produced by QwenInference.generate_website()'s
LLM guess informed by similar-org context), validates it's really that
org's site via a single fetch + identity_match() check — not a search or
crawl. If confirmed, extracts clean text content for mission-grounding
and looks for a volunteer/get-involved page link.

This is deliberately a single targeted fetch, not the broader crawling
approach (web_finder_agent.py) paused 2026-06-22 for being network-bound —
see DECISIONS.md 2026-07-07 for why this is a different, lighter mechanism.

Uses BeautifulSoup (already a project dependency, bs4>=4.14) for HTML
parsing rather than hand-rolled regex — handles malformed/nested markup
correctly, which real nonprofit websites are full of.
"""
import re
import zlib
import sqlite3
from typing import Optional, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scripts.donate_confidence import identity_match
from scripts.donation_link_pipeline import UA, TIMEOUT, _now

_VOLUNTEER_PATTERNS = re.compile(
    r'volunteer|get[\s-]?involved', re.IGNORECASE
)

_DONATE_PATTERNS = re.compile(
    r'donate|give[\s-]?now|ways[\s-]?to[\s-]?give|support[\s-]?us|make[\s-]?a[\s-]?gift',
    re.IGNORECASE
)


def extract_text_content(html: str) -> str:
    """Strip scripts, styles, and nav/header/footer chrome, returning
    cleaned body text suitable for LLM grounding context."""
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return re.sub(r'\s+', ' ', text).strip()


def find_volunteer_link(html: str, base_url: str) -> Optional[str]:
    """Scan anchor tags for a volunteer/get-involved page link.
    Returns the absolute URL, or None if no such link is found."""
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        link_text = a.get_text(strip=True)
        if _VOLUNTEER_PATTERNS.search(href) or _VOLUNTEER_PATTERNS.search(link_text):
            return urljoin(base_url, href)
    return None


def find_donate_link(html: str, base_url: str) -> Optional[str]:
    """Scan anchor tags on a CONFIRMED org homepage for a donate/give link.

    Mirrors find_volunteer_link() — same already-fetched HTML, zero extra
    network cost. Deliberately does not follow the link or guess subdomains;
    donation_link_pipeline.py's Phase 1 owns deeper discovery (processor
    recognition, subdomain candidates) for orgs where no link is visible here.
    Returns the absolute URL, or None if no such link is found."""
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        link_text = a.get_text(strip=True)
        if _DONATE_PATTERNS.search(href) or _DONATE_PATTERNS.search(link_text):
            return urljoin(base_url, href)
    return None


def _cache_page(db_con: sqlite3.Connection, ein: str, url: str, body: bytes, status_code: int):
    """Store compressed HTML in the shared page_cache table (same schema
    donation_link_pipeline.py uses) so future pipeline runs can reuse it.

    Creates the table if it doesn't exist yet — this module may run before
    donation_link_pipeline.init_schema() has, e.g. in a fresh DB or test
    fixture, and page_cache is shared infrastructure, not owned by either
    caller."""
    db_con.execute("""
        CREATE TABLE IF NOT EXISTS page_cache (
            url         TEXT PRIMARY KEY,
            ein         TEXT,
            fetched_at  TEXT,
            status_code INTEGER,
            html_gz     BLOB,
            content_len INTEGER
        )
    """)
    db_con.execute("CREATE INDEX IF NOT EXISTS idx_pc_ein ON page_cache(ein)")
    compressed = zlib.compress(body, level=6)
    fetched_at = _now()
    db_con.execute("""
        INSERT OR REPLACE INTO page_cache (url, ein, fetched_at, status_code, html_gz, content_len)
        VALUES (?,?,?,?,?,?)
    """, (url, ein, fetched_at, status_code, compressed, len(body)))
    db_con.commit()


def _cached_page_html(db_con: sqlite3.Connection, ein: str, url: str, max_age_days: int = 14) -> Optional[str]:
    """Read a still-fresh cached page for this EIN+URL, decompressed to HTML.

    page_cache has been write-only until now — every pipeline re-fetched even
    when it had already cached the exact page seconds earlier in the same
    run. Returns None on any miss (no row, stale, or table not yet created)
    so the caller's normal fetch path is unchanged when there's nothing to
    reuse.
    """
    try:
        row = db_con.execute(
            "SELECT html_gz, fetched_at FROM page_cache WHERE ein = ? AND url = ?",
            (ein, url)
        ).fetchone()
    except sqlite3.OperationalError:
        return None  # table doesn't exist yet in this DB
    if not row:
        return None
    html_gz, fetched_at = row
    try:
        from datetime import datetime, timedelta, timezone
        # _cache_page's _now() stores a timezone-AWARE UTC isoformat string
        # (donation_link_pipeline._now()) — comparing against a naive
        # datetime.now() raises TypeError, which the broad except below
        # silently swallowed as a cache miss. Every cache read failed this
        # way until caught here: use an aware "now" to match.
        age = datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)
        if age > timedelta(days=max_age_days):
            return None
    except (ValueError, TypeError):
        return None
    try:
        return zlib.decompress(html_gz).decode('utf-8', errors='replace')
    except (zlib.error, AttributeError):
        return None


def fetch_known_website(
    db_con: sqlite3.Connection,
    ein: str,
    org_name: str,
    known_url: str
) -> Optional[Dict]:
    """Fetch an ALREADY-CONFIRMED website (registry_enriched.website with
    website_status IN ('ok','live')) to scan for donate/volunteer links and
    real content for mission-grounding.

    Distinct from validate_and_fetch_website(), which validates a freshly
    GUESSED candidate domain. This function skips the Qwen guess entirely —
    we already know the site is real — and reuses a recent page_cache entry
    when available. Same return shape as validate_and_fetch_website() so
    callers can treat the two interchangeably.

    Returns None on any fetch failure; the caller falls back to non-grounded
    generation exactly as it does for an unconfirmed candidate.
    """
    url = known_url
    if not url.startswith('http'):
        url = f'https://{url}'

    html = _cached_page_html(db_con, ein, url)
    status_code = 200
    body_for_cache: Optional[bytes] = None

    if html is None:
        try:
            resp = requests.get(
                url, timeout=TIMEOUT, allow_redirects=True,
                headers={"User-Agent": UA, "Accept": "text/html,*/*"}
            )
        except requests.exceptions.RequestException:
            return None
        if resp.status_code != 200:
            return None
        html = resp.text
        status_code = resp.status_code
        body_for_cache = resp.content

    level, ratio = identity_match(org_name, html)
    # Deliberately no mismatch/unknown/weak gate here (unlike
    # validate_and_fetch_website): this URL is already a confirmed website
    # on file, not an LLM guess being screened for identity — a weak/partial
    # text match on the homepage shouldn't block donate/volunteer scanning
    # of a site we already trust.

    if body_for_cache is not None:
        _cache_page(db_con, ein, url, body_for_cache, status_code)

    content_text = extract_text_content(html)
    volunteer_url = find_volunteer_link(html, base_url=url)
    donate_url = find_donate_link(html, base_url=url)

    return {
        'url': url,
        'content_text': content_text[:2000],
        'identity_level': level,
        'identity_ratio': ratio,
        'volunteer_url': volunteer_url,
        'donate_url': donate_url,
    }


def validate_and_fetch_website(
    db_con: sqlite3.Connection,
    ein: str,
    org_name: str,
    candidate_url: str
) -> Optional[Dict]:
    """
    Fetch a candidate URL once, confirm it's really the named org's site via
    identity_match(), and if confirmed, extract content + look for a
    volunteer page. Returns None on any failure (network error, non-200,
    identity mismatch) — the caller falls back to non-grounded generation.

    Returns dict: {'url': str, 'content_text': str, 'identity_level': str,
                   'identity_ratio': float, 'volunteer_url': str|None,
                   'donate_url': str|None}
    """
    url = candidate_url
    if not url.startswith('http'):
        url = f'https://{url}'

    try:
        resp = requests.get(
            url, timeout=TIMEOUT, allow_redirects=True,
            headers={"User-Agent": UA, "Accept": "text/html,*/*"}
        )
    except requests.exceptions.RequestException:
        return None

    if resp.status_code != 200:
        return None

    html = resp.text
    level, ratio = identity_match(org_name, html)
    if level in ('mismatch', 'unknown', 'weak'):
        return None

    _cache_page(db_con, ein, url, resp.content, resp.status_code)

    content_text = extract_text_content(html)
    volunteer_url = find_volunteer_link(html, base_url=url)
    donate_url = find_donate_link(html, base_url=url)

    return {
        'url': url,
        'content_text': content_text[:2000],  # cap for prompt-size sanity
        'identity_level': level,
        'identity_ratio': ratio,
        'volunteer_url': volunteer_url,
        'donate_url': donate_url,
    }
