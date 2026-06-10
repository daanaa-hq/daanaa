#!/usr/bin/env python3
"""
Web Finder Agent — GPU-optimized semantic verification for discovering org websites

Strategy:
1. Query orgs with revenue data but missing websites (credibility proven, discoverable)
2. Use Google search to find likely website
3. Use GPU embeddings + semantic similarity to verify ownership
4. Cache verified websites

GPU: mxbai-embed-large on port 11436 (Vulkan) — batch 50 sites at a time
CPU: Google search, pattern matching, HTML parsing

Run:
    python3 scripts/web_finder_agent.py --limit 100 --dry-run
    python3 scripts/web_finder_agent.py --limit 1000
"""

import sqlite3
import requests
import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from html.parser import HTMLParser

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
LOG_PATH = Path.home() / "meritgiving/logs/web_finder_50k.log"
EMBED_URL = "http://127.0.0.1:11436/v1/embeddings"
EMBED_MODEL = "mxbai-embed-large"

# Google search via DuckDuckGo (no API key needed, respects robots.txt)
SEARCH_TIMEOUT = 10
FETCH_TIMEOUT = 8
MIN_CONFIDENCE = 0.5   # embedding floor; primary gate is the name-token check (≥70%)

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def embed_text(text: str) -> np.ndarray | None:
    """Get embedding via fast GPU 0 server."""
    try:
        resp = requests.post(
            EMBED_URL,
            json={"model": EMBED_MODEL, "input": text},
            timeout=30   # embed shares the GPU with mission gen; 5s timed out under load
        )
        if resp.status_code == 200:
            emb = resp.json()["data"][0]["embedding"]
            return np.array(emb, dtype=np.float32)
        log(f"  Embedding HTTP {resp.status_code}: {resp.text[:120]}")
    except Exception as e:
        log(f"  Embedding error: {e}")
    return None

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    if a is None or b is None:
        return 0.0
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))

def search_website(org_name: str, city: str, state: str) -> list[str]:
    """
    Search for org website candidates.
    Strategy: Try heuristic patterns first, then semantic search via existing websites.
    In production, can integrate SerpAPI or Google Custom Search.
    """
    candidates = set()

    # Pattern 1: Direct domain guesses (most orgs use org_name pattern)
    org_clean = org_name.lower().strip().replace(' ', '').replace('-', '').replace('.', '')
    candidates.add(f"{org_clean}.org")
    candidates.add(f"{org_clean}.com")

    # Pattern 2: First word + .org
    first_word = org_name.split()[0].lower().replace('-', '')
    if len(first_word) > 2:
        candidates.add(f"{first_word}.org")

    # Pattern 3: City + org pattern (e.g., "bostonchildrensmuseum.org")
    if city:
        city_clean = city.lower().replace(' ', '')
        candidates.add(f"{city_clean}{org_clean}.org")

    # Return top candidates to try
    return list(candidates)[:5]

def fetch_website_text(url: str) -> str | None:
    """Fetch website homepage and extract text."""
    try:
        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        resp = requests.get(url, timeout=FETCH_TIMEOUT, allow_redirects=True)
        if resp.status_code == 200:
            # Extract text from HTML (basic)
            text = resp.text.lower()
            # Drop script/style bodies — code noise, and it pushed token counts
            # past the embed server's 512-token batch limit (HTTP 500)
            text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Remove extra whitespace
            text = ' '.join(text.split())
            return text[:1200]  # ≤~450 tokens, safely under the embed batch limit
    except Exception as e:
        pass
    return None

def _name_token_ratio(org_name: str, page_text: str) -> float:
    """Share of meaningful org-name words that appear on the page.
    Deterministic and explainable: a real org homepage names the org."""
    stop = {'the', 'inc', 'incorporated', 'corp', 'corporation', 'foundation',
            'fund', 'assn', 'association', 'and', 'for', 'of'}
    tokens = [t for t in re.findall(r'[a-z]+', org_name.lower())
              if len(t) > 2 and t not in stop]
    if not tokens:
        return 0.0
    return sum(1 for t in tokens if t in page_text) / len(tokens)

def verify_website_ownership(org_record: dict, website_url: str) -> tuple[bool, float]:
    """
    Verify the website belongs to the org. Two signals, both required:
    1. Name-token check: ≥70% of meaningful org-name words appear on the page
       (a domain-pattern guess can land on an unrelated squatter/company site).
    2. Embedding similarity ≥ 0.5 between org identity and page text — a sanity
       floor only. (Name-vs-HTML cosine peaks ~0.7, so the old 0.85 bar could
       never pass: 0 verified in 1,800 attempts on 2026-06-10.)
    Returns (is_verified, confidence_score)
    """
    org_name = org_record['organization_name']

    # Fetch page first — cheapest signal
    website_text = fetch_website_text(website_url)
    if website_text is None:
        return False, 0.0

    name_ratio = _name_token_ratio(org_name, website_text)
    if name_ratio < 0.7:
        log(f"    Verified: False (name tokens on page: {name_ratio:.0%})")
        return False, 0.0

    org_address = f"{org_name} {org_record.get('CITY', '')} {org_record.get('STATE', '')}"
    org_emb = embed_text(org_address)
    website_emb = embed_text(website_text)
    similarity = cosine_similarity(org_emb, website_emb)

    is_verified = similarity >= MIN_CONFIDENCE
    log(f"    Verified: {is_verified} (name tokens: {name_ratio:.0%}, similarity: {similarity:.3f})")
    return is_verified, similarity

def find_donation_links(website_text: str) -> list[str]:
    """Extract donation links from website text."""
    patterns = [
        r'href=["\']([^"\']*(?:donate|giving|gift|contribute|sponsor|support)[^"\']*)["\']',
        r'href=["\']([^"\']*(?:donorbox|paypal|stripe|classy)[^"\']*)["\']',
    ]
    links = []
    for pattern in patterns:
        links.extend(re.findall(pattern, website_text, re.IGNORECASE))
    return list(set(links))[:3]  # Return top 3 unique

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--priority', choices=['high-revenue', 'all'], default='high-revenue')
    args = parser.parse_args()

    log("━" * 70)
    log(f"Web Finder Agent — Priority: {args.priority}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Query orgs: have revenue, missing website, ordered by revenue DESC.
    # Skip orgs attempted in the last 90 days so nightly loops advance through
    # the queue instead of re-trying the same top-revenue failures forever.
    if args.priority == 'high-revenue':
        query = """
            SELECT EIN, organization_name, CITY, STATE, total_revenue
            FROM registry_enriched
            WHERE deductibility = '1'
              AND total_revenue > 100000
              AND (website IS NULL OR website = '')
              AND (website_checked_at IS NULL
                   OR website_checked_at < datetime('now', '-90 days'))
            ORDER BY total_revenue DESC
            LIMIT ?
        """
    else:
        query = """
            SELECT EIN, organization_name, CITY, STATE, total_revenue
            FROM registry_enriched
            WHERE deductibility = '1'
              AND (website IS NULL OR website = '')
              AND (website_checked_at IS NULL
                   OR website_checked_at < datetime('now', '-90 days'))
            ORDER BY total_revenue DESC
            LIMIT ?
        """

    orgs = c.execute(query, (args.limit,)).fetchall()
    log(f"Found {len(orgs)} orgs to process")

    if args.dry_run:
        log("DRY RUN — not saving results")

    processed = 0
    verified = 0

    for row in orgs:
        ein, name, city, state, revenue = row
        log(f"\n[{processed+1}/{len(orgs)}] {name} (${revenue:,.0f})")

        # Get website candidates via heuristic patterns
        candidates = search_website(name, city or '', state or '')

        found = False
        for candidate in candidates:
            # Try to fetch and verify
            website_text = fetch_website_text(candidate)
            if website_text is None:
                continue

            # Verify ownership via GPU semantic similarity
            is_verified, confidence = verify_website_ownership(
                {'EIN': ein, 'organization_name': name, 'CITY': city, 'STATE': state},
                candidate
            )

            if is_verified:
                # 'beta' per disclosure policy: heuristically discovered, not human-reviewed
                log(f"  ✓ Verified! {candidate} (confidence: {confidence:.3f})")
                if not args.dry_run:
                    c.execute("""
                        UPDATE registry_enriched
                        SET website = ?, website_status = 'beta', website_checked_at = datetime('now')
                        WHERE EIN = ?
                    """, (candidate, ein))
                    verified += 1
                found = True
                break

        if not found:
            log(f"  ✗ No verified website found among candidates")
            if not args.dry_run:
                # Mark the attempt so nightly loops move on (re-eligible after 90 days)
                c.execute("""
                    UPDATE registry_enriched
                    SET website_status = 'no_website_found', website_checked_at = datetime('now')
                    WHERE EIN = ?
                """, (ein,))

        processed += 1
        if processed % 50 == 0 and not args.dry_run:
            conn.commit()  # checkpoint so an interrupted night keeps its progress

    if not args.dry_run:
        conn.commit()
    conn.close()

    log(f"\n━ Summary ━")
    log(f"Processed: {processed}")
    log(f"Verified: {verified}")
    log(f"Coverage gain: +{verified} websites")

if __name__ == "__main__":
    main()
