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

def verify_website(url):
    """Verify website is accessible, return 200 + extract mission."""
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
            return url, 'ok', mission
        elif status in ('301', '302', '307', '308'):
            return url, 'redirect', None
        elif status == '403':
            return url, 'blocked', None
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
        verified_url, status, mission = verify_website(url)
        if verified_url:
            logger.info(f"{ein}: FOUND {verified_url} ({status}) + mission: {mission[:50] if mission else 'none'}")
            save_discovery(ein, verified_url, status, mission)
            return {'ein': ein, 'status': status, 'url': verified_url, 'mission': mission}
        else:
            logger.debug(f"{ein}: Not accessible ({status})")
            save_discovery(ein, url, status, None)
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
