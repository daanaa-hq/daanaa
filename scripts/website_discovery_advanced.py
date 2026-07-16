#!/usr/bin/env python3
"""
Advanced website discovery for Phase 2 (runs after Phase 1 basic discovery).

Implements steps 1-4 for higher coverage on orgs with financial data:
1. DuckDuckGo search fallback (org name + "nonprofit")
2. Domain guessing (name slugification + .org/.ngo/.nonprofit variants)
3. Staleness check (rediscover orgs not found in 90+ days)
4. Playwright browser automation (JS-heavy modern sites)

Complements Phase 1 (direct website probe) and runs parallel to Phase 3
(Charity Navigator for no-data orgs). Only targets orgs WITH financial data.
"""

import sqlite3
import logging
import re
import time
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: missing requests/beautifulsoup4 — pip install requests beautifulsoup4")
    exit(1)

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("WARNING: duckduckgo-search not installed — pip install duckduckgo-search")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("WARNING: httpx not installed — pip install httpx[http2]")

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("INFO: playwright not installed — skipping JS sites (pip install playwright)")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/website_discovery_advanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


def slugify_org_name(name: str) -> str:
    """Convert org name to domain slug: 'The Food Bank Inc' → 'foodbank'."""
    if not name:
        return ""
    slug = re.sub(r'[^a-z0-9]+', '', name.lower())
    return slug[:63]  # Max 63 chars for domain labels


def guess_domains(org_name: str, city: str = "", state: str = "") -> list:
    """Generate plausible domain variants for an org.

    Examples:
      - name only: foodbank.org, foodbank.ngo
      - name + city: foodbank-denver.org, foodbankdenver.org
    """
    variants = []
    slug = slugify_org_name(org_name)
    if not slug:
        return []

    # Tier 1: name only, common nonprofits TLDs
    for tld in ['.org', '.ngo', '.nonprofit']:
        variants.append(f"http://{slug}{tld}")
        variants.append(f"https://{slug}{tld}")

    # Tier 2: name + city (if provided)
    if city:
        city_slug = slugify_org_name(city)
        if city_slug and city_slug != slug:
            for tld in ['.org', '.ngo']:
                combined = f"{slug}-{city_slug}"
                variants.append(f"https://{combined}{tld}")
                # Also try without hyphen
                combined_no_hyphen = slug + city_slug
                if len(combined_no_hyphen) < 63:
                    variants.append(f"https://{combined_no_hyphen}{tld}")

    return variants


def http_probe_with_redirect(url: str, timeout: float = 5.0) -> Optional[str]:
    """Probe URL with redirect following using httpx (if available) or requests."""
    try:
        if HTTPX_AVAILABLE:
            with httpx.Client(follow_redirects=True, timeout=timeout) as client:
                resp = client.get(url, headers={'User-Agent': 'Mozilla/5.0 (Nonprofit Discovery)'})
                if resp.status_code == 200:
                    return resp.url  # Returns final URL after redirects
        else:
            resp = requests.get(url, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200:
                return resp.url
    except Exception as e:
        pass
    return None


def duckduckgo_search_nonprofit(org_name: str, city: str = "", state: str = "") -> Optional[str]:
    """Search DuckDuckGo for org website: 'Org Name nonprofit'."""
    if not DDGS_AVAILABLE:
        return None

    try:
        query = f'"{org_name}" nonprofit'
        if city:
            query += f' {city}'
        if state:
            query += f' {state}'
        query += ' website'

        ddgs = DDGS(timeout=10)
        results = ddgs.text(query, max_results=3)

        if results:
            # Results are dicts with 'href' key
            for result in results:
                url = result.get('href')
                if url and 'nonprofit.org' not in url:  # Skip aggregator sites
                    # Verify the URL is live
                    verified = http_probe_with_redirect(url, timeout=3.0)
                    if verified:
                        return str(verified)
    except Exception as e:
        logger.debug(f"DuckDuckGo search failed for {org_name}: {e}")

    return None


def playwright_fetch(url: str, timeout: float = 15.0) -> Optional[str]:
    """Fetch JS-heavy page using Playwright, return final URL."""
    if not PLAYWRIGHT_AVAILABLE:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(timeout=timeout)
            page.goto(url, wait_until='domcontentloaded')
            final_url = page.url
            browser.close()
            return final_url if final_url else url
    except Exception as e:
        logger.debug(f"Playwright fetch failed for {url}: {e}")

    return None


def discover_website_advanced(ein: int, org_name: str, city: str = "", state: str = "",
                              existing_website: Optional[str] = None) -> Optional[str]:
    """Attempt discovery using steps 1-4, in order."""

    # Step 2: Domain guessing (fast, no network)
    domain_variants = guess_domains(org_name, city, state)
    for variant in domain_variants:
        verified = http_probe_with_redirect(variant, timeout=3.0)
        if verified:
            logger.info(f"✅ {ein} ({org_name}): domain guess found {verified}")
            return str(verified)

    # Step 1: DuckDuckGo search fallback (medium speed)
    if DDGS_AVAILABLE:
        ddg_result = duckduckgo_search_nonprofit(org_name, city, state)
        if ddg_result:
            logger.info(f"✅ {ein} ({org_name}): DuckDuckGo found {ddg_result}")
            return ddg_result

    # Step 4: Playwright for known-stale domains (slow, browser-based)
    if PLAYWRIGHT_AVAILABLE and existing_website:
        # Only use Playwright on sites we know are stale (JS modern framework)
        try:
            verified = playwright_fetch(existing_website, timeout=8.0)
            if verified and verified != existing_website:
                logger.info(f"✅ {ein} ({org_name}): Playwright updated {existing_website} → {verified}")
                return verified
        except Exception:
            pass

    return None


def get_stale_discovery_candidates(batch_size: int = 100) -> list:
    """Get orgs with financial data but no website, or website not checked in 90+ days."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    cursor.execute("""
        SELECT EIN, organization_name, CITY, STATE, website
        FROM registry_enriched
        WHERE org_status = 'active'
        AND EIN > 0
        AND (total_revenue IS NOT NULL OR total_revenue > 0)  -- Has financial data
        AND (
            website IS NULL
            OR website = ''
            OR website_checked_at IS NULL
            OR website_checked_at < datetime('now', '-90 days')
        )
        ORDER BY
            CASE WHEN website IS NOT NULL THEN 0 ELSE 1 END,  -- Existing sites first
            total_revenue DESC NULLS LAST
        LIMIT ?
    """, (batch_size,))

    results = cursor.fetchall()
    db.close()
    return results


def update_website(ein: int, website_url: str) -> bool:
    """Update org's website in the database."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    try:
        cursor.execute("""
            UPDATE registry_enriched
            SET website = ?, website_status = 'beta', website_checked_at = CURRENT_TIMESTAMP
            WHERE EIN = ?
        """, (website_url, ein))
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to update {ein}: {e}")
        return False
    finally:
        db.close()


def run_discovery_phase2(batch_size: int = 50, sleep_between_orgs: float = 0.5):
    """Run Phase 2 advanced discovery continuously."""
    logger.info("=" * 70)
    logger.info("🚀 PHASE 2: ADVANCED WEBSITE DISCOVERY (parallel with Phase 1 + Phase 3)")
    logger.info(f"   Target: orgs WITH financial data, no/stale website")
    logger.info(f"   Methods: domain guessing, DuckDuckGo, Playwright")
    logger.info(f"   Batch: {batch_size} | Sleep: {sleep_between_orgs}s/org")
    logger.info("=" * 70)

    iteration = 0
    total_discovered = 0

    while True:
        iteration += 1
        try:
            logger.info(f"[Iteration {iteration}] Fetching {batch_size} stale/missing candidates...")
            orgs = get_stale_discovery_candidates(batch_size)

            if not orgs:
                logger.info("No stale/missing candidates. Waiting 60s...")
                time.sleep(60)
                continue

            discovered_this_batch = 0
            for ein, name, city, state, existing_website in orgs:
                result = discover_website_advanced(ein, name, city or "", state or "", existing_website)
                if result:
                    update_website(ein, result)
                    total_discovered += 1
                    discovered_this_batch += 1

                time.sleep(sleep_between_orgs)

            logger.info(f"[Iteration {iteration}] Batch complete: {discovered_this_batch}/{len(orgs)} discovered, total: {total_discovered}")
            time.sleep(5)  # Brief pause before next batch

        except KeyboardInterrupt:
            logger.info("⏹️  Phase 2 stopped by user")
            break
        except Exception as e:
            logger.error(f"Fatal error in Phase 2: {e}")
            time.sleep(60)


if __name__ == '__main__':
    import sys
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    sleep_between_orgs = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

    logger.info(f"Available: DuckDuckGo={DDGS_AVAILABLE}, httpx={HTTPX_AVAILABLE}, Playwright={PLAYWRIGHT_AVAILABLE}")
    run_discovery_phase2(batch_size=batch_size, sleep_between_orgs=sleep_between_orgs)
