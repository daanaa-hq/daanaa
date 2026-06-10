#!/usr/bin/env python3
"""
Donation Link Extractor — Find donate/give links on verified websites

Marks all extracted links as 'beta' (heuristic-discovered, not org-verified).
Includes clear disclosure: "This link was discovered automatically and has not
been verified by the organization. Always confirm on their official website."

Run:
    python3 scripts/donation_link_extractor.py --limit 500
    python3 scripts/donation_link_extractor.py --limit 100 --dry-run
"""

import sqlite3
import requests
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from html.parser import HTMLParser

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
LOG_PATH = Path.home() / "meritgiving/logs/donation_extractor.log"

_log_lock = threading.Lock()
_stats = {"processed": 0, "found": 0, "errors": 0}
_stats_lock = threading.Lock()

DONATION_PLATFORMS = {
    'donorbox': r'donorbox\.org',
    'paypal': r'paypal\.com',
    'stripe': r'stripe\.com',
    'classy': r'classy\.org',
    'mightycause': r'mightycause\.com',
    'networkforgood': r'networkforgood\.com',
    'givewp': r'givewp\.com',
    'givecloud': r'givecloud\.com',
    'kindful': r'kindful\.io',
    'zsuite': r'zsuite\.net',
}

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    with _log_lock:
        print(line)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")

def extract_links(website_url: str, html_content: str) -> list[dict]:
    """
    Extract donation links from HTML.
    Returns list of dicts: {url, platform, confidence}
    """
    links = []
    base_url = website_url if website_url.startswith('http') else f"https://{website_url}"

    # Pattern 1: href="/donate" or href="donate" or href="https://donate.org"
    donate_patterns = [
        r'href=["\']([^"\']*(?:donate|giving|gift|contribute|support|sponsor)[^"\']*)["\']',
        r'href=["\']([^"\']*give[^"\']*)["\']',
        r'href=["\']([^"\']*membership[^"\']*)["\']',
    ]

    for pattern in donate_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            if match.startswith('http'):
                url = match
            elif match.startswith('/'):
                url = base_url.rstrip('/') + match
            elif match.startswith('?'):
                url = base_url.rstrip('/') + '/' + match
            else:
                url = base_url.rstrip('/') + '/' + match

            # Detect platform
            platform = 'custom'
            for plat, regex in DONATION_PLATFORMS.items():
                if re.search(regex, url, re.IGNORECASE):
                    platform = plat
                    break

            links.append({
                'url': url[:2048],  # Truncate if insanely long
                'platform': platform,
                'confidence': 85,  # Heuristic, always mark as 'beta'
            })

    return list({d['url']: d for d in links}.values())[:5]  # Top 5 unique

def fetch_website(url: str) -> str | None:
    """Fetch website HTML."""
    try:
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        resp = requests.get(url, timeout=5, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=500)
    parser.add_argument('--workers', type=int, default=10)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    log("━" * 70)
    log("Donation Link Extractor — Heuristic-based discovery")
    log("⚠️  ALL LINKS MARKED 'beta' (heuristic-discovered, not org-verified)")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get orgs with verified websites (website_status = 'ok')
    query = """
        SELECT EIN, organization_name, website
        FROM registry_enriched
        WHERE website_status = 'ok'
          AND (donate_url IS NULL OR donate_url = '')
        LIMIT ?
    """

    rows = c.execute(query, (args.limit,)).fetchall()
    log(f"Found {len(rows)} orgs with verified websites but no donation link\n")

    if args.dry_run:
        log("DRY RUN — not saving results\n")

    def extract_org(row):
        ein, name, website = row
        html = fetch_website(website)
        if not html:
            with _stats_lock:
                _stats["errors"] += 1
            return None

        links = extract_links(website, html)
        if links:
            with _stats_lock:
                _stats["found"] += 1
            return (ein, links)

        return None

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(extract_org, row): row for row in rows}
        processed = 0

        for future in as_completed(futures):
            processed += 1
            with _stats_lock:
                _stats["processed"] += 1

            result = future.result()
            if result:
                ein, links = result
                for link_data in links:
                    log(f"✓ {ein}: {link_data['platform']} — {link_data['url'][:60]}...")

                    if not args.dry_run:
                        # Store with 'beta' tag — NOT verified by org
                        c.execute("""
                            UPDATE registry_enriched
                            SET donate_url = ?,
                                donate_platform = ?,
                                donate_url_status = 'beta',
                                donate_confidence = 85,
                                donate_checked_at = datetime('now')
                            WHERE EIN = ?
                        """, (
                            link_data['url'],
                            link_data['platform'],
                            ein
                        ))

            if processed % 50 == 0:
                log(f"  Progress: {processed}/{len(rows)}")

    if not args.dry_run:
        conn.commit()

    conn.close()

    log(f"\n━ Summary ━")
    log(f"Processed: {_stats['processed']}")
    log(f"Found links: {_stats['found']}")
    log(f"Errors: {_stats['errors']}")
    log(f"\n⚠️  All links marked 'beta' status")
    log(f"API disclosure: 'This link was auto-discovered and not verified by the organization.'")

if __name__ == "__main__":
    main()
