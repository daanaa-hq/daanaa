#!/usr/bin/env python3
"""
Website discovery engine — finds nonprofit websites for 3.5M orgs without discovered sites.
Multi-strategy approach: search, DNS, registry lookup. Prioritizes by revenue.
"""

import sqlite3
import subprocess
import socket
import json
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
from urllib.parse import urlparse

try:
    import urllib.request
    import urllib.error
except ImportError:  # pragma: no cover
    urllib = None

EMBED_SERVER_URL = "http://127.0.0.1:11436/embedding"

# Parking/placeholder page markers — a domain that resolves and returns 200
# but is not the org's real site. Cheap lexical check, run before the
# (more expensive) semantic check.
PARKING_MARKERS = [
    'greengeeks', 'sedo', 'domain for sale', 'buy this domain',
    'this domain is for sale', 'godaddy', 'namecheap parking',
    'coming soon', 'under construction', 'ipubco', 'this domain may be for sale',
    'domain registered at', 'safenames', 'domain default page',
    'account has been suspended', 'parked domain', 'domain parking',
    'this web page is parked',
]

LOG_DIR = Path('/home/akbar/meritgiving/logs')
DB_PATH = Path('/home/akbar/meritgiving/data/merit_registry.db')
STATE_FILE = LOG_DIR / '.website_discovery_state.json'

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'website_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_orgs_to_discover(limit=10000):
    """Get orgs without websites, prioritized by revenue."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # High revenue first (likely to have websites)
    c.execute("""
        SELECT ein, organization_name, city, state, total_revenue
        FROM registry_enriched
        WHERE (website IS NULL OR website = '')
          AND (website_status IS NULL OR website_status = 'unknown')
          AND (total_revenue IS NOT NULL AND total_revenue > 100000)
        ORDER BY total_revenue DESC
        LIMIT ?
    """, (limit,))

    results = c.fetchall()
    conn.close()
    return results

def search_website(name, city, state):
    """Search for nonprofit website using multiple strategies."""

    # Strategy 1: Google search-like query (via common patterns)
    common_tlds = ['.org', '.com', '.net', '.edu']

    # Try common domain patterns
    for tld in common_tlds:
        # Direct org name + state
        domain_candidates = [
            f"{name.lower().replace(' ', '')}{tld}",
            f"{name.lower().replace(' ', '-')}{tld}",
            f"{name.lower().split()[0]}{tld}",  # First word only
            f"{city.lower().replace(' ', '')}{tld}",
        ]

        for domain in domain_candidates:
            if is_valid_domain(domain):
                return f"https://www.{domain}" if not domain.startswith('www.') else f"https://{domain}"

    # Strategy 2: Common nonprofit patterns
    name_slug = re.sub(r'[^\w]', '', name.lower())[:20]
    for tld in common_tlds:
        domain = f"{name_slug}{tld}"
        if is_valid_domain(domain):
            return f"https://www.{domain}"

    return None

def is_valid_domain(domain):
    """Check if domain resolves via DNS."""
    try:
        # Remove www. if present for DNS check
        check_domain = domain.replace('www.', '')
        socket.gethostbyname(check_domain)
        return True
    except (socket.gaierror, socket.error):
        return False

def extract_mission(html):
    """Extract mission statement from HTML."""
    if not html:
        return None

    import re
    from html import unescape

    html_lower = html.lower()

    # Strategy 1: Meta description
    meta_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html_lower)
    if meta_match:
        mission = unescape(meta_match.group(1)).strip()
        if 15 < len(mission) < 300:
            return mission

    # Strategy 2: Extract first <p> after <h1> or <title>
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        if 10 < len(title) < 100 and not title.lower().startswith('404'):
            return title

    # Strategy 3: First substantial paragraph
    p_match = re.search(r'<p[^>]*>([^<]{30,200})</p>', html, re.IGNORECASE)
    if p_match:
        text = unescape(re.sub(r'<[^>]+>', '', p_match.group(1))).strip()
        if len(text) > 20:
            return text[:200]

    return None

def _embed(text):
    """Call the local embedding server (mxbai-embed-large, port 11436).
    Returns None on any failure so callers can fail open to the lexical check."""
    if not text:
        return None
    try:
        payload = json.dumps({"content": text[:2000]}).encode('utf-8')
        req = urllib.request.Request(
            EMBED_SERVER_URL, data=payload,
            headers={"Content-Type": "application/json"}, method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            # llama.cpp embedding server returns [{"index":0,"embedding":[[...]]}]
            vec = data[0]['embedding']
            if isinstance(vec[0], list):
                vec = vec[0]
            return vec
    except Exception:
        return None

def _cosine_sim(a, b):
    if not a or not b or len(a) != len(b):
        return None
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return None
    return dot / (norm_a * norm_b)

def is_parking_or_placeholder(html):
    """Cheap lexical reject for parked/placeholder domains before the
    semantic check runs. Catches the obvious cases without a GPU round trip."""
    if not html:
        return False
    lowered = html.lower()
    return any(marker in lowered for marker in PARKING_MARKERS)

def is_relevant_match(org_name, page_text, threshold=0.45):
    """Semantic relevance gate: does the fetched page actually seem to be
    this org's site? Embeds org_name and the fetched title/mission text via
    the local GPU embedding server and checks cosine similarity.

    Fails OPEN (returns True / 'unknown') when the embed server is
    unreachable or either text is empty — a network hiccup should not block
    all discovery, but it means this check is a floor, not a guarantee.
    Returns (bool_or_None, similarity_or_None) so callers can log/store
    confidence rather than a bare pass/fail.
    """
    if not page_text:
        return None, None
    org_vec = _embed(org_name)
    page_vec = _embed(page_text)
    if org_vec is None or page_vec is None:
        return None, None
    sim = _cosine_sim(org_vec, page_vec)
    if sim is None:
        return None, None
    return sim >= threshold, sim

def verify_website(url, org_name=None):
    """Verify website is accessible, return 200 + extract mission.

    Adds two confidence gates before accepting a 200 as a real match:
    (1) cheap lexical parking-page reject, (2) semantic relevance check
    against the org name via the GPU embedding server. Both are logged
    even when they don't block, so match quality is auditable later.
    """
    if not url:
        return None, 'no_url', None

    try:
        # Fetch with curl to get response + body for mission extraction
        result = subprocess.run(
            ['curl', '-s', '-w', '\n%{http_code}', '-L', '--max-time', '8', url],
            capture_output=True,
            text=True,
            timeout=10
        )

        output_lines = result.stdout.rsplit('\n', 1)
        status = output_lines[-1].strip() if len(output_lines) > 1 else '000'
        html = output_lines[0] if len(output_lines) > 1 else ''

        if status == '200':
            mission = extract_mission(html) if html else None

            if is_parking_or_placeholder(html):
                return None, 'rejected_parking', None

            relevance_text = mission or ''
            relevant, similarity = is_relevant_match(org_name, relevance_text) if org_name else (None, None)
            if similarity is not None:
                logger.debug(f"relevance check: sim={similarity:.3f} url={url}")
            if relevant is False:
                return None, f'rejected_irrelevant_sim{similarity:.2f}', None

            return url, 'ok', mission
        elif status in ('301', '302', '307', '308'):
            return url, 'redirect', None
        elif status == '403':
            # Blocked means we could not actually verify content — this is
            # NOT a confirmed match. Previously returned `url` here, which
            # process_org() then saved as a "FOUND" website with no content
            # ever having been checked. Do not accept unverified blocks.
            return None, 'blocked', None
        elif status == '404':
            return None, 'dead', None
        elif status in ('500', '502', '503'):
            return None, 'error_server', None
        else:
            return None, f'error_{status}', None
    except subprocess.TimeoutExpired:
        return None, 'timeout', None
    except Exception as e:
        return None, f'error_{str(e)[:20]}', None

def save_discovery(ein, url, status, mission=None):
    """Save website discovery + mission to database."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    try:
        if mission:
            c.execute("""
                UPDATE registry_enriched
                SET website = ?, website_status = ?, mission = ?, mission_source = 'website_meta'
                WHERE ein = ?
            """, (url, status, mission, ein))
        else:
            c.execute("""
                UPDATE registry_enriched
                SET website = ?, website_status = ?
                WHERE ein = ?
            """, (url, status, ein))

        conn.commit()
        return True
    except Exception as e:
        logger.error(f"DB save error for {ein}: {e}")
        return False
    finally:
        conn.close()

def process_org(org_data):
    """Discover website + mission for a single org."""
    ein, name, city, state, revenue = org_data

    # Search for website
    url = search_website(name, city, state)

    if url:
        # Verify website is live + extract mission
        verified_url, status, mission = verify_website(url, org_name=name)
        if verified_url:
            logger.info(f"{ein}: FOUND {verified_url} ({status}) + mission: {mission[:50] if mission else 'none'}")
            save_discovery(ein, verified_url, status, mission)
            return {'ein': ein, 'status': status, 'url': verified_url, 'mission': mission}
        else:
            # Not a confirmed match (rejected/dead/blocked/error). Do NOT
            # write the unverified candidate url into the website column —
            # only the status, for skip-tracking. Previously this saved
            # `url` here regardless of why verification failed, which is how
            # parked/irrelevant domains and unconfirmed 403s ended up stored
            # as an org's website. See LESSONS.md 2026-08-17.
            logger.debug(f"{ein}: Not accessible ({status})")
            save_discovery(ein, None, status, None)
            return {'ein': ein, 'status': status, 'url': None, 'mission': None}
    else:
        logger.debug(f"{ein}: No URL found for {name}")
        save_discovery(ein, None, 'no_website_found', None)
        return {'ein': ein, 'status': 'no_website_found', 'url': None, 'mission': None}

def main():
    """Run website discovery engine."""
    logger.info("Starting website discovery for 3.5M backlog nonprofits")

    # Get batch of orgs to discover
    batch_size = 1000
    orgs = get_orgs_to_discover(batch_size)

    if not orgs:
        logger.warning("No orgs to discover")
        return

    logger.info(f"Processing {len(orgs)} orgs (high-revenue first)")

    found_count = 0
    not_found_count = 0

    # Process in parallel (8 workers max)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_org, org): org for org in orgs}

        for future in as_completed(futures):
            try:
                result = future.result()
                if result['url']:
                    found_count += 1
                else:
                    not_found_count += 1
            except Exception as e:
                logger.error(f"Error processing org: {e}")
                not_found_count += 1

    # Report
    logger.info(f"Batch complete: {found_count} found, {not_found_count} not found")
    logger.info(f"Discovery rate: {100*found_count/(found_count+not_found_count):.1f}%")

    # Save state
    state = {
        'timestamp': datetime.now().isoformat(),
        'batch_size': batch_size,
        'found': found_count,
        'not_found': not_found_count,
    }
    STATE_FILE.write_text(json.dumps(state))

if __name__ == '__main__':
    main()
