#!/usr/bin/env python3
"""
Intelligent nonprofit website extraction using volunteer platforms
and civic engagement directories.

Strategy: Query real volunteer opportunities to extract nonprofit organizations,
then cross-reference with registry to find new organizations and their websites.
"""

import json
import sqlite3
import time
import random
import re
from typing import Set, Dict, List, Tuple
from urllib.parse import urljoin, urlparse, quote

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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def load_registry() -> Dict[str, Tuple]:
    """Load registry website and org name mappings."""
    conn = sqlite3.connect(REGISTRY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT website, organization_name, EIN
        FROM registry_enriched
        WHERE website IS NOT NULL AND website != ''
    """)
    websites = {}
    for row in cursor.fetchall():
        if row[0]:
            normalized = normalize_url(row[0])
            if normalized:
                websites[normalized] = (row[1], row[2])
    conn.close()
    print(f"[Registry] Loaded {len(websites)} websites")
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


def query_nonprofit_data_sources() -> Set[str]:
    """Query nonprofit data sources directly."""
    print("\n[Nonprofit Data Sources] Querying APIs and public data...")
    websites = set()

    # Data sources with nonprofit information
    sources = [
        {
            'name': 'ProPublica Nonprofit Explorer',
            'url': 'https://projects.propublica.org/nonprofits/organizations.json',
            'type': 'api'
        }
    ]

    for source in sources:
        print(f"  Querying {source['name']}...")
        try:
            if source.get('type') == 'api':
                response = requests.get(source['url'], headers=HEADERS, timeout=15)
                response.raise_for_status()

                try:
                    data = response.json()
                    # ProPublica returns array of orgs
                    if isinstance(data, list):
                        for org in data[:100]:  # Get first 100
                            if isinstance(org, dict) and 'homepage_url' in org:
                                norm = normalize_url(org['homepage_url'])
                                if norm:
                                    websites.add(norm)
                except json.JSONDecodeError:
                    pass

            print(f"    Found {len(websites)} websites so far")
            time.sleep(1)
        except Exception as e:
            print(f"    Error: {e}")

    return websites


def scrape_volunteermatch_org_profiles() -> Set[str]:
    """Extract from VolunteerMatch organization profiles."""
    print("\n[VolunteerMatch Profiles] Extracting organization websites...")
    websites = set()

    try:
        # Query VolunteerMatch for various opportunity types
        keywords = ['nonprofit', 'charity', 'volunteer', 'community', 'service',
                    'education', 'health', 'environment', 'animals', 'poverty']

        for keyword in keywords:
            try:
                url = "https://www.volunteermatch.org/search"
                params = {'k': keyword, 'l': ''}

                response = requests.get(url, params=params, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Parse organization names and links from results
                for div in soup.find_all('div', class_=re.compile(r'opportunity|card|org')):
                    text = div.get_text()

                    # Look for website patterns in text
                    # Nonprofits often list their site in opportunity descriptions
                    website_patterns = re.findall(
                        r'(?:website|web|http)[:\s]*([a-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+)',
                        text, re.IGNORECASE
                    )

                    for pattern in website_patterns:
                        if pattern.startswith(('http://', 'https://')):
                            norm = normalize_url(pattern)
                            if norm:
                                websites.add(norm)

                print(f"  Keyword '{keyword}': +{len([w for w in websites])} websites")
                time.sleep(random.uniform(1, 2))

            except Exception as e:
                continue

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_causes_nonprofits() -> Set[str]:
    """Scrape Causes.com nonprofit directory."""
    print("\n[Causes Directory] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://www.causes.com"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for nonprofit organization links
        for a in soup.find_all('a', href=re.compile(r'causes.com/nonprofits')):
            href = a.get('href', '')
            if '/nonprofits/' in href:
                # Try to access the nonprofit page
                full_url = urljoin('https://www.causes.com', href)
                try:
                    resp = requests.get(full_url, headers=HEADERS, timeout=10)
                    sub_soup = BeautifulSoup(resp.content, 'html.parser')

                    # Look for website links on nonprofit page
                    for link in sub_soup.find_all('a', href=re.compile(r'https?://')):
                        org_url = link.get('href', '')
                        if 'causes.com' not in org_url:
                            norm = normalize_url(org_url)
                            if norm:
                                websites.add(norm)

                    time.sleep(random.uniform(0.5, 1))
                except:
                    pass

        print(f"  Found {len(websites)} websites")

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_catchafire_nonprofits() -> Set[str]:
    """Scrape Catchafire nonprofit projects."""
    print("\n[Catchafire] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://www.catchafire.org"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract organization URLs from links
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href.startswith(('http://', 'https://')) and 'catchafire' not in href:
                norm = normalize_url(href)
                if norm and '.' in norm:
                    websites.add(norm)

        print(f"  Found {len(websites)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_unitedway_directory() -> Set[str]:
    """Scrape United Way directory for nonprofit information."""
    print("\n[United Way] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://www.unitedway.org/search"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract links that might be to nonprofits
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href.startswith(('http://', 'https://')) and 'unitedway' not in href:
                norm = normalize_url(href)
                if norm:
                    websites.add(norm)

        print(f"  Found {len(websites)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_network_for_good() -> Set[str]:
    """Scrape Network for Good directory."""
    print("\n[Network for Good] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://www.networkforgood.org"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href.startswith(('http://', 'https://')) and 'networkforgood' not in href:
                norm = normalize_url(href)
                if norm:
                    websites.add(norm)

        print(f"  Found {len(websites)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_spark_action() -> Set[str]:
    """Scrape Spark Action volunteer platform."""
    print("\n[Spark Action] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://www.sparkaction.org"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href.startswith(('http://', 'https://')) and 'sparkaction' not in href:
                norm = normalize_url(href)
                if norm:
                    websites.add(norm)

        print(f"  Found {len(websites)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_pointservice() -> Set[str]:
    """Scrape PointService volunteer platform."""
    print("\n[PointService] Extracting nonprofit websites...")
    websites = set()

    try:
        url = "https://www.pointservice.org"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href.startswith(('http://', 'https://')) and 'pointservice' not in href:
                norm = normalize_url(href)
                if norm:
                    websites.add(norm)

        print(f"  Found {len(websites)} websites")
        time.sleep(1)

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def filter_results(websites: Set[str], registry: Dict) -> List[str]:
    """Filter out websites already in registry."""
    registry_keys = set(registry.keys())
    new = [w for w in websites if w not in registry_keys]
    return sorted(new)


def main():
    """Main execution."""
    print("=" * 80)
    print("Intelligent Nonprofit Website Extraction from Volunteer Platforms")
    print("=" * 80)

    registry = load_registry()

    all_websites = set()

    # Query data sources
    all_websites.update(query_nonprofit_data_sources())
    time.sleep(1)

    # Scrape platforms
    all_websites.update(scrape_volunteermatch_org_profiles())
    time.sleep(1)

    all_websites.update(scrape_causes_nonprofits())
    time.sleep(1)

    all_websites.update(scrape_catchafire_nonprofits())
    time.sleep(1)

    all_websites.update(scrape_unitedway_directory())
    time.sleep(1)

    all_websites.update(scrape_network_for_good())
    time.sleep(1)

    all_websites.update(scrape_spark_action())
    time.sleep(1)

    all_websites.update(scrape_pointservice())

    # Filter
    new_websites = filter_results(all_websites, registry)

    # Output
    with open(OUTPUT_FILE, 'w') as f:
        f.write("Volunteer Platform & Civic Engagement Website Extraction Report\n")
        f.write("=" * 80 + "\n\n")
        f.write("Data Extraction Strategy:\n")
        f.write("  - Query ProPublica Nonprofit Explorer API\n")
        f.write("  - Scrape VolunteerMatch.org organization profiles\n")
        f.write("  - Scrape Causes.com nonprofit directory\n")
        f.write("  - Scrape Catchafire.org\n")
        f.write("  - Scrape United Way search results\n")
        f.write("  - Scrape Network for Good\n")
        f.write("  - Scrape Spark Action\n")
        f.write("  - Scrape PointService\n\n")
        f.write(f"Extraction Date: 2026-07-30\n\n")
        f.write(f"Statistics:\n")
        f.write(f"  Total websites collected: {len(all_websites)}\n")
        f.write(f"  Already in Daanaa registry: {len(all_websites) - len(new_websites)}\n")
        f.write(f"  NEW websites (target 300+): {len(new_websites)}\n\n")

        if new_websites:
            f.write("=" * 80 + "\n")
            f.write("NEW Nonprofit Websites Extracted from Volunteer Platforms:\n")
            f.write("=" * 80 + "\n\n")

            for idx, website in enumerate(new_websites, 1):
                f.write(f"{idx:5d}. {website}\n")

            f.write(f"\nTotal NEW websites: {len(new_websites)}\n")
            if len(new_websites) >= 300:
                f.write("✓ TARGET ACHIEVED: 300+ websites extracted\n")
            else:
                f.write(f"Progress: {len(new_websites)}/300 ({len(new_websites)/300*100:.1f}%)\n")

    print(f"\n[Output] Results written to {OUTPUT_FILE}")
    print(f"Total websites: {len(all_websites)}")
    print(f"NEW websites: {len(new_websites)}")
    if len(new_websites) >= 300:
        print("✓ TARGET ACHIEVED")
    else:
        print(f"Progress: {len(new_websites)}/300 ({len(new_websites)/300*100:.1f}%)")


if __name__ == "__main__":
    main()
