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
                   'identity_ratio': float, 'volunteer_url': str|None}
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

    return {
        'url': url,
        'content_text': content_text[:2000],  # cap for prompt-size sanity
        'identity_level': level,
        'identity_ratio': ratio,
        'volunteer_url': volunteer_url,
    }
