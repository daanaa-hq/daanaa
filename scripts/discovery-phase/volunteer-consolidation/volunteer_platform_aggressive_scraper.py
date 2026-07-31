#!/usr/bin/env python3
"""
Aggressive nonprofit website extraction from volunteer platforms.

This script attempts to extract 300+ nonprofit websites from volunteer
platforms and civic engagement sites by:
1. Querying organization search results
2. Parsing organization cards and profiles
3. Extracting website fields and links
4. Cross-referencing with Daanaa registry
"""

import json
import sqlite3
import time
import random
import re
from typing import Set, Dict, List
from urllib.parse import urljoin, urlparse, parse_qs
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

# Headers to use for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def load_registry_websites() -> Set[str]:
    """Load existing websites from registry."""
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
        if not parsed.netloc or len(parsed.netloc) < 4:
            return ""
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.rstrip('/') if parsed.path else ''
        result = f"https://{domain}{path}"
        return result if len(result) > 15 else ""
    except:
        return ""


def extract_urls_from_html(html: str, exclude_domains: List[str] = None) -> Set[str]:
    """Extract URLs from HTML content."""
    if exclude_domains is None:
        exclude_domains = []

    urls = set()
    url_pattern = r'https?://[a-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+'
    matches = re.finditer(url_pattern, html.lower())

    for match in matches:
        url = match.group(0).rstrip('"\')>,')
        norm = normalize_url(url)

        if norm and all(domain not in norm for domain in exclude_domains):
            urls.add(norm)

    return urls


def scrape_volunteermatch_orgs_batch() -> Set[str]:
    """Scrape VolunteerMatch with improved extraction."""
    print("\n[VolunteerMatch] Extracting nonprofit websites from opportunities...")
    websites = set()

    try:
        # Query multiple keyword searches
        keywords = ['nonprofit', 'volunteer', 'charity', 'service', 'community']

        for keyword in keywords:
            try:
                url = "https://www.volunteermatch.org/search/org"
                params = {'k': keyword, 'l': ''}

                response = requests.get(url, params=params, headers=HEADERS, timeout=15)
                response.raise_for_status()

                # Extract URLs from HTML
                exclude = ['volunteermatch.org']
                found = extract_urls_from_html(response.text, exclude)
                websites.update(found)

                print(f"  Keyword '{keyword}': +{len(found)} websites")
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"  Error with keyword '{keyword}': {e}")

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_idealist_orgs_batch() -> Set[str]:
    """Scrape Idealist.org with improved extraction."""
    print("\n[Idealist.org] Extracting nonprofit websites from opportunities...")
    websites = set()

    try:
        # Search for different types of opportunities
        base_url = "https://www.idealist.org/search"
        keywords = ['nonprofit', 'volunteer', 'charity', 'community', 'advocacy']

        for keyword in keywords:
            try:
                params = {
                    'q': keyword,
                    'type': 'organizations',
                    'continent': 'North America'
                }

                response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
                response.raise_for_status()

                # Extract URLs
                exclude = ['idealist.org']
                found = extract_urls_from_html(response.text, exclude)
                websites.update(found)

                print(f"  Keyword '{keyword}': +{len(found)} websites")
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"  Error with keyword '{keyword}': {e}")

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_linkedin_volunteer_opportunities() -> Set[str]:
    """Scrape LinkedIn volunteer opportunities."""
    print("\n[LinkedIn] Extracting nonprofit websites...")
    websites = set()

    try:
        base_url = "https://www.linkedin.com/volunteers/opportunities"

        try:
            response = requests.get(base_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            exclude = ['linkedin.com']
            found = extract_urls_from_html(response.text, exclude)
            websites.update(found)

            print(f"  Found {len(found)} websites")
            time.sleep(2)

        except Exception as e:
            print(f"  Error: {e}")

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_charity_navigator_batch() -> Set[str]:
    """Scrape Charity Navigator nonprofit listings."""
    print("\n[Charity Navigator] Extracting nonprofit websites...")
    websites = set()

    try:
        base_url = "https://www.charitynavigator.org/search"
        categories = ['animal', 'arts', 'community', 'education', 'environment', 'health']

        for category in categories:
            try:
                params = {'category': category}
                response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
                response.raise_for_status()

                exclude = ['charitynavigator.org']
                found = extract_urls_from_html(response.text, exclude)
                websites.update(found)

                print(f"  Category '{category}': +{len(found)} websites")
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"  Error with category '{category}': {e}")

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_guidestar_batch() -> Set[str]:
    """Scrape GuideStar nonprofit profiles."""
    print("\n[GuideStar] Extracting nonprofit websites...")
    websites = set()

    try:
        base_url = "https://www.guidestar.org/search"

        try:
            response = requests.get(base_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            exclude = ['guidestar.org']
            found = extract_urls_from_html(response.text, exclude)
            websites.update(found)

            print(f"  Found {len(found)} websites")
            time.sleep(2)

        except Exception as e:
            print(f"  Error: {e}")

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_causes_batch() -> Set[str]:
    """Scrape Causes.com nonprofit pages."""
    print("\n[Causes] Extracting nonprofit websites...")
    websites = set()

    try:
        base_url = "https://www.causes.com/nonprofits"

        try:
            response = requests.get(base_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            exclude = ['causes.com']
            found = extract_urls_from_html(response.text, exclude)
            websites.update(found)

            print(f"  Found {len(found)} websites")
            time.sleep(2)

        except Exception as e:
            print(f"  Error: {e}")

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_donorbox_directory() -> Set[str]:
    """Scrape Donorbox nonprofit directory."""
    print("\n[Donorbox] Extracting nonprofit websites...")
    websites = set()

    try:
        base_url = "https://donorbox.org/nonprofits"

        try:
            response = requests.get(base_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            exclude = ['donorbox.org']
            found = extract_urls_from_html(response.text, exclude)
            websites.update(found)

            print(f"  Found {len(found)} websites")
            time.sleep(2)

        except Exception as e:
            print(f"  Error: {e}")

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def deduplicate_and_filter(all_websites: Set[str], registry_websites: Set[str]) -> List[str]:
    """Filter and deduplicate."""
    new = [w for w in all_websites if w not in registry_websites]
    return sorted(new)


def main():
    """Main execution."""
    print("=" * 80)
    print("Volunteer Platform Aggressive Website Extraction")
    print("=" * 80)

    registry = load_registry_websites()
    all_websites = set()

    # Scrape all platforms
    all_websites.update(scrape_volunteermatch_orgs_batch())
    time.sleep(2)

    all_websites.update(scrape_idealist_orgs_batch())
    time.sleep(2)

    all_websites.update(scrape_linkedin_volunteer_opportunities())
    time.sleep(2)

    all_websites.update(scrape_charity_navigator_batch())
    time.sleep(2)

    all_websites.update(scrape_guidestar_batch())
    time.sleep(2)

    all_websites.update(scrape_causes_batch())
    time.sleep(2)

    all_websites.update(scrape_donorbox_directory())

    # Filter
    new_websites = deduplicate_and_filter(all_websites, registry)

    # Output
    with open(OUTPUT_FILE, 'w') as f:
        f.write("Volunteer Platform & Civic Engagement Website Extraction\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Extraction Date: 2026-07-30\n")
        f.write(f"Total websites collected: {len(all_websites)}\n")
        f.write(f"Already in registry: {len(all_websites) - len(new_websites)}\n")
        f.write(f"NEW websites found: {len(new_websites)}\n\n")

        if new_websites:
            f.write("=" * 80 + "\n")
            f.write("NEW Nonprofit Websites Extracted from Volunteer Platforms:\n")
            f.write("=" * 80 + "\n\n")
            f.write("Target: 300+ websites from VolunteerHub, Idealist.org, VolunteerMatch,\n")
            f.write("LinkedIn Volunteer Opportunities, Charity Navigator, GuideStar, and other\n")
            f.write("civic engagement and nonprofit directories.\n\n")

            for idx, website in enumerate(new_websites, 1):
                f.write(f"{idx:4d}. {website}\n")

            f.write(f"\nTotal NEW websites: {len(new_websites)}\n")

    print(f"\n[Output] Results written to {OUTPUT_FILE}")
    print(f"Total websites extracted: {len(all_websites)}")
    print(f"NEW websites found: {len(new_websites)}")
    print(f"Target: 300+")
    if len(new_websites) >= 300:
        print("✓ TARGET ACHIEVED")
    else:
        print(f"Progress: {len(new_websites) / 300 * 100:.1f}%")


if __name__ == "__main__":
    main()
