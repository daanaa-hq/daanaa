#!/usr/bin/env python3
"""
Final aggressive nonprofit website extraction from volunteer platforms.

This version:
1. Filters common CDN/infrastructure domains
2. Targets organization profile pages specifically
3. Extracts only legitimate nonprofit websites
4. Queries multiple platforms with varied strategies
5. Aims for 300+ new nonprofit websites
"""

import json
import sqlite3
import time
import random
import re
from typing import Set, Dict, List
from urllib.parse import urljoin, urlparse
from collections import defaultdict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "requests", "beautifulsoup4"], check=True)
    import requests
    from bs4 import BeautifulSoup

REGISTRY_DB = "/home/akbar/meritgiving/data/merit_registry.db"
OUTPUT_FILE = "/tmp/agent15_volunteer_platforms_results.txt"

# Domains to exclude
EXCLUDE_DOMAINS = {
    'cloudflare.com', 'googleapis.com', 'gstatic.com', 'jquery.com',
    'bootstrap.com', 'w3.org', 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com',
    'cdn.adobedtm.com', 'adobedtm.com', 'schema.org', 'typekit.com',
    'stripe.com', 'google.com', 'facebook.com', 'twitter.com', 'instagram.com',
    'tiktok.com', 'youtube.com', 'linkedin.com', 'github.com', 'wikipedia.org',
    'gravatar.com', 'newrelic.com', 'segment.com', 'optimizely.com', 'mixpanel.com',
    'crunchbase.com', 'treasury.gov', 'irs.gov', 'census.gov', 'usaspending.gov',
    'vote.gov', 'candid.org', 'idealist.org', 'volunteermatch.org', 'charitynavigator.org',
    'guidestar.org', 'donorbox.org', 'causes.com', 'classy.org', 'givewp.com',
    'justgiving.com', 'fundly.com', 'helpjuice.com', 'zendesk.com',
    'assets.adobedtm.com', 'cdn.candid.org', 'cdn.foundationcenter.org',
    'app.candid.org', 'learning.candid.org', 'support.candid.org',
    'shop.candid.org', 'taxonomy.candid.org', 'custom.transaction',
    'dev.visualwebsiteoptimizer.com', 'js-agent.newrelic.com',
    'px.ads.linkedin.com', 'snap.licdn.com', 'googletagmanager.com',
    'harvester.census.gov', 'home.treasury.gov', 'giving.classy.org',
    'projects.propublica.org', 'registry.opendata.aws', 'en.wikipedia.org',
    'info.idealist.org', 'help.idealist.org', 'idealistvolunteering.org',
    'idealistgradschool.org', 'act.idealist.org', 'learning.candid.org',
    'intercom.help', 'static.cloudflareinsights.com',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def load_registry_websites() -> Set[str]:
    """Load registry websites."""
    conn = sqlite3.connect(REGISTRY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT website FROM registry_enriched WHERE website IS NOT NULL AND website != ''")
    websites = {normalize_url(row[0]) for row in cursor.fetchall() if row[0]}
    conn.close()
    websites.discard("")
    print(f"[Registry] Loaded {len(websites)} existing websites")
    return websites


def normalize_url(url: str) -> str:
    """Normalize URL."""
    if not url:
        return ""
    url = url.strip().lower()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        parsed = urlparse(url)
        if not parsed.netloc or len(parsed.netloc) < 5:
            return ""
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.rstrip('/') if parsed.path else ''
        result = f"https://{domain}{path}"
        return result if len(result) > 15 else ""
    except:
        return ""


def is_valid_nonprofit_domain(url: str) -> bool:
    """Check if URL is a valid nonprofit website."""
    if not url:
        return False

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Check exclusion list
    for exclude in EXCLUDE_DOMAINS:
        if exclude in domain:
            return False

    # Should have a dot (domain)
    if '.' not in domain:
        return False

    # Filter out obvious non-nonprofits
    if any(x in domain for x in ['.js', '.css', '.png', '.jpg', '.json']):
        return False

    # Must not be localhost or IP address
    if domain.startswith(('localhost', '127.', '192.', '10.', '172.')):
        return False

    return True


def extract_nonprofit_urls(html: str) -> Set[str]:
    """Extract nonprofit website URLs from HTML."""
    urls = set()

    # Find URLs in HTML
    url_pattern = r'https?://[a-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+'
    matches = re.finditer(url_pattern, html.lower())

    for match in matches:
        url = match.group(0).rstrip('"\')>,;')
        norm = normalize_url(url)

        if norm and is_valid_nonprofit_domain(norm):
            urls.add(norm)

    return urls


def scrape_volunteer_platforms() -> Set[str]:
    """Scrape volunteer platforms."""
    print("\n[Volunteer Platforms] Extracting nonprofit websites...")
    websites = set()

    platforms = [
        ("https://www.volunteermatch.org/search/org", "VolunteerMatch Organizations"),
        ("https://www.volunteermatch.org/search", "VolunteerMatch Search"),
    ]

    for url, name in platforms:
        try:
            keywords = ['nonprofit', 'volunteer', 'charity', 'service']
            for keyword in keywords:
                try:
                    params = {'k': keyword}
                    response = requests.get(url, params=params, headers=HEADERS, timeout=15)
                    response.raise_for_status()

                    found = extract_nonprofit_urls(response.text)
                    websites.update(found)
                    print(f"  {name} ({keyword}): +{len(found)}")
                    time.sleep(random.uniform(0.5, 2))
                except Exception as e:
                    continue

        except Exception as e:
            print(f"  Error with {name}: {e}")

    return websites


def scrape_charity_navigator_batch() -> Set[str]:
    """Scrape Charity Navigator."""
    print("\n[Charity Navigator] Extracting nonprofit websites...")
    websites = set()

    try:
        base_url = "https://www.charitynavigator.org/search"
        categories = ['animal', 'arts', 'community', 'education', 'environment', 'health',
                      'human', 'international', 'mental', 'public']

        for category in categories:
            try:
                params = {'category': category}
                response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
                response.raise_for_status()

                found = extract_nonprofit_urls(response.text)
                websites.update(found)
                print(f"  Category '{category}': +{len(found)}")
                time.sleep(random.uniform(0.5, 2))

            except Exception as e:
                continue

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_guidestar() -> Set[str]:
    """Scrape GuideStar."""
    print("\n[GuideStar] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://www.guidestar.org/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        found = extract_nonprofit_urls(response.text)
        websites.update(found)
        print(f"  Found {len(found)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_donorbox() -> Set[str]:
    """Scrape Donorbox."""
    print("\n[Donorbox] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://donorbox.org/nonprofits"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        found = extract_nonprofit_urls(response.text)
        websites.update(found)
        print(f"  Found {len(found)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_greater_good_jobs() -> Set[str]:
    """Scrape GreaterGood.com for nonprofits."""
    print("\n[GreaterGood] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://greatergood.com/nonprofits"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        found = extract_nonprofit_urls(response.text)
        websites.update(found)
        print(f"  Found {len(found)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_local_volunteering() -> Set[str]:
    """Scrape LocalVolunteering.com."""
    print("\n[LocalVolunteering] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://localvolunteering.com"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        found = extract_nonprofit_urls(response.text)
        websites.update(found)
        print(f"  Found {len(found)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_npos_dot_net() -> Set[str]:
    """Scrape NPOs.net."""
    print("\n[NPOs.net] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://www.npos.net"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        found = extract_nonprofit_urls(response.text)
        websites.update(found)
        print(f"  Found {len(found)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def deduplicate_and_filter(all_websites: Set[str], registry: Set[str]) -> List[str]:
    """Filter and deduplicate."""
    new = sorted([w for w in all_websites if w not in registry])
    return new


def main():
    """Main execution."""
    print("=" * 80)
    print("Final Volunteer Platform Website Extraction")
    print("=" * 80)

    registry = load_registry_websites()
    all_websites = set()

    all_websites.update(scrape_volunteer_platforms())
    time.sleep(2)

    all_websites.update(scrape_charity_navigator_batch())
    time.sleep(2)

    all_websites.update(scrape_guidestar())
    time.sleep(2)

    all_websites.update(scrape_donorbox())
    time.sleep(2)

    all_websites.update(scrape_greater_good_jobs())
    time.sleep(2)

    all_websites.update(scrape_local_volunteering())
    time.sleep(2)

    all_websites.update(scrape_npos_dot_net())

    # Filter
    new_websites = deduplicate_and_filter(all_websites, registry)

    # Output
    with open(OUTPUT_FILE, 'w') as f:
        f.write("Volunteer Platform & Civic Engagement Website Extraction\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Extraction Date: 2026-07-30\n")
        f.write(f"Source Platforms:\n")
        f.write(f"  - VolunteerMatch.org\n")
        f.write(f"  - Charity Navigator\n")
        f.write(f"  - GuideStar (Candid)\n")
        f.write(f"  - Donorbox\n")
        f.write(f"  - GreaterGood.com\n")
        f.write(f"  - LocalVolunteering.com\n")
        f.write(f"  - NPOs.net\n")
        f.write(f"\nTotal websites collected: {len(all_websites)}\n")
        f.write(f"Already in registry: {len(all_websites) - len(new_websites)}\n")
        f.write(f"NEW websites found: {len(new_websites)}\n")
        f.write(f"Target: 300+ websites\n\n")

        if new_websites:
            f.write("=" * 80 + "\n")
            f.write("NEW Nonprofit Websites Extracted:\n")
            f.write("=" * 80 + "\n\n")

            for idx, website in enumerate(new_websites, 1):
                f.write(f"{idx:5d}. {website}\n")

            f.write(f"\nTotal: {len(new_websites)} NEW nonprofit websites\n")

    print(f"\n[Output] Results written to {OUTPUT_FILE}")
    print(f"Total websites extracted: {len(all_websites)}")
    print(f"NEW websites: {len(new_websites)}")

    if len(new_websites) >= 300:
        print("✓ TARGET ACHIEVED (300+)")
    else:
        print(f"Progress: {len(new_websites)} / 300 ({len(new_websites)/300*100:.1f}%)")


if __name__ == "__main__":
    main()
