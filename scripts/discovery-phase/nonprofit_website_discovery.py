#!/usr/bin/env python3
"""
Advanced nonprofit website discovery from volunteer and civic engagement platforms.

Strategies:
1. Query nonprofit directories that expose APIs
2. Parse structured data (JSON-LD, microdata) from organization pages
3. Extract organization URLs from canonical sources
4. Match against Daanaa registry for enrichment
"""

import json
import sqlite3
import time
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


def load_registry_websites() -> Dict[str, str]:
    """Load website to name mapping from Daanaa registry."""
    conn = sqlite3.connect(REGISTRY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT website, organization_name, EIN
        FROM registry_enriched
        WHERE website IS NOT NULL AND website != ''
    """)
    websites = {normalize_url(row[0]): (row[1], row[2]) for row in cursor.fetchall() if row[0]}
    conn.close()
    websites.pop("", None)
    print(f"[Registry] Loaded {len(websites)} existing website mappings")
    return websites


def normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    if not url:
        return ""
    url = url.strip().lower()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        parsed = urlparse(url)
        if not parsed.netloc or len(parsed.netloc) < 4:
            return ""

        # Clean domain
        domain = parsed.netloc.replace('www.', '').replace('www2.', '')
        path = parsed.path.rstrip('/') if parsed.path else ''
        result = f"https://{domain}{path}"

        # Sanity check
        return result if len(result) > 15 and '.' in domain else ""
    except:
        return ""


def extract_organization_urls_from_json_ld(html: str) -> Set[str]:
    """Extract organization URLs from JSON-LD structured data."""
    urls = set()

    # Find all JSON-LD blocks
    json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.finditer(json_ld_pattern, html, re.DOTALL | re.IGNORECASE)

    for match in matches:
        try:
            data = json.loads(match.group(1))

            # Recursively search for URL fields in JSON-LD
            def extract_urls_from_dict(obj):
                url_set = set()
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['url', 'sameAs', 'website']:
                            if isinstance(value, str):
                                url_set.add(value)
                            elif isinstance(value, list):
                                url_set.update([v for v in value if isinstance(v, str)])
                        elif isinstance(value, (dict, list)):
                            url_set.update(extract_urls_from_dict(value))
                elif isinstance(obj, list):
                    for item in obj:
                        url_set.update(extract_urls_from_dict(item))
                return url_set

            found = extract_urls_from_dict(data)
            for url in found:
                norm = normalize_url(url)
                if norm:
                    urls.add(norm)
        except json.JSONDecodeError:
            pass

    return urls


def extract_nonprofit_websites_from_dir() -> Set[str]:
    """Extract nonprofit websites from directory sources."""
    print("\n[Nonprofit Directories] Extracting from indexed sources...")
    websites = set()

    # These are public nonprofit directories with structured data
    sources = [
        ("https://projects.propublica.org/nonprofits/organizations", "ProPublica Nonprofit Explorer"),
        ("https://www.irs.gov/charities-non-profits", "IRS Nonprofit Directory"),
    ]

    for url, name in sources:
        print(f"  Querying {name}...")
        try:
            response = requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; Daanaa Research)'},
                timeout=15
            )
            response.raise_for_status()

            # Extract URLs from JSON-LD
            json_ld_urls = extract_organization_urls_from_json_ld(response.text)
            websites.update(json_ld_urls)

            # Parse HTML for links
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')):
                    norm = normalize_url(href)
                    # Filter out directory links
                    if norm and all(x not in norm for x in ['propublica', 'irs.gov', '.pdf']):
                        websites.add(norm)

            print(f"    Found {len(websites)} websites so far")
            time.sleep(1)
        except Exception as e:
            print(f"    Error: {e}")

    return websites


def extract_from_501c3_explorer() -> Set[str]:
    """Extract from 501(c)(3) nonprofit explorer sources."""
    print("\n[501c3 Explorer] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://projects.propublica.org/nonprofits/"
        response = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Daanaa Research)'},
            timeout=15
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract JSON-LD data
        json_ld_urls = extract_organization_urls_from_json_ld(response.text)
        websites.update(json_ld_urls)

        # Extract from links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith(('http://', 'https://')) and 'propublica' not in href:
                norm = normalize_url(href)
                if norm:
                    websites.add(norm)

        print(f"  Found {len(websites)} websites")
        time.sleep(1)
    except Exception as e:
        print(f"  Error: {e}")

    return websites


def extract_from_guidestar_json() -> Set[str]:
    """Extract from GuideStar nonprofit database."""
    print("\n[GuideStar Database] Extracting nonprofit websites...")
    websites = set()

    try:
        # GuideStar exposes some data in JSON format
        url = "https://www.guidestar.org/"
        response = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Daanaa Research)'},
            timeout=15
        )
        response.raise_for_status()

        # Extract JSON-LD
        json_ld_urls = extract_organization_urls_from_json_ld(response.text)
        websites.update(json_ld_urls)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith(('http://', 'https://')) and 'guidestar' not in href:
                norm = normalize_url(href)
                if norm and '.edu' not in norm and '.gov' not in norm:  # Filter out non-nonprofit
                    websites.add(norm)

        print(f"  Found {len(websites)} websites")
        time.sleep(1)
    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_volunteer_opportunities() -> Set[str]:
    """Scrape volunteer opportunity platforms for org websites."""
    print("\n[Volunteer Opportunities] Extracting nonprofit websites...")
    websites = set()

    platforms = [
        "https://www.volunteermatch.org/",
        "https://www.idealist.org/",
    ]

    for platform in platforms:
        try:
            response = requests.get(
                platform,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; Daanaa Research)'},
                timeout=15
            )
            response.raise_for_status()

            # Extract JSON-LD
            json_ld_urls = extract_organization_urls_from_json_ld(response.text)
            websites.update(json_ld_urls)

            # Parse for links
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')) and platform.split('/')[2] not in href:
                    norm = normalize_url(href)
                    if norm:
                        websites.add(norm)

            print(f"  {platform.split('/')[2]}: Found {len(websites)} websites so far")
            time.sleep(1)
        except Exception as e:
            print(f"  Error with {platform}: {e}")

    return websites


def filter_results(all_websites: Set[str], registry_websites: Dict[str, tuple]) -> List[str]:
    """Filter out websites already in registry."""
    registry_set = set(registry_websites.keys())

    new_websites = []
    for website in all_websites:
        if website not in registry_set:
            new_websites.append(website)

    return sorted(new_websites)


def main():
    """Main execution."""
    print("=" * 80)
    print("Advanced Nonprofit Website Discovery")
    print("=" * 80)

    registry = load_registry_websites()

    all_websites = set()

    all_websites.update(extract_nonprofit_websites_from_dir())
    time.sleep(1)

    all_websites.update(extract_from_501c3_explorer())
    time.sleep(1)

    all_websites.update(extract_from_guidestar_json())
    time.sleep(1)

    all_websites.update(scrape_volunteer_opportunities())

    # Filter
    new_websites = filter_results(all_websites, registry)

    # Output
    with open(OUTPUT_FILE, 'w') as f:
        f.write("Advanced Nonprofit Website Discovery Results\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total websites collected: {len(all_websites)}\n")
        f.write(f"NEW websites (not in Daanaa registry): {len(new_websites)}\n\n")

        if new_websites:
            f.write("=" * 80 + "\n")
            f.write("NEW Nonprofit Websites:\n")
            f.write("=" * 80 + "\n\n")

            for idx, website in enumerate(new_websites, 1):
                f.write(f"{idx:4d}. {website}\n")

    print(f"\n[Output] Results written to {OUTPUT_FILE}")
    print(f"Total websites collected: {len(all_websites)}")
    print(f"NEW websites found: {len(new_websites)}")


if __name__ == "__main__":
    main()
