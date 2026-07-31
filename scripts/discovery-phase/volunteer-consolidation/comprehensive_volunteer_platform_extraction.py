#!/usr/bin/env python3
"""
Comprehensive nonprofit website extraction from volunteer and civic platforms.

Combines multiple extraction strategies to reach 300+ NEW nonprofit websites
from volunteer platforms like VolunteerMatch, Idealist.org, VolunteerHub, etc.
"""

import json
import sqlite3
import time
import random
import re
from typing import Set, Dict, List
from urllib.parse import urljoin, urlparse

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

# Vendor/platform domains to filter out
VENDOR_DOMAINS = {
    'bonterra', 'givegab', 'joindeed', 'apricot', 'socialsolutions',
    'cybergrants', 'everyaction', 'donordrive', 'mobilize', 'jumpstart',
    'networkforgood', 'idealist', 'volunteermatch', 'volunteerhub', 'causes',
    'catchafire', 'unitedway', 'sparkaction', 'pointservice', 'bonterratech',
    'classy', 'justgiving', 'fundly', 'givewp', 'donorbox',
}


def load_registry() -> Set[str]:
    """Load registry websites."""
    conn = sqlite3.connect(REGISTRY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT website FROM registry_enriched WHERE website IS NOT NULL")
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
        if not parsed.netloc:
            return ""
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.rstrip('/') if parsed.path else ''
        result = f"https://{domain}{path}"
        return result if len(result) > 12 else ""
    except:
        return ""


def is_nonprofit_domain(url: str) -> bool:
    """Check if URL appears to be a nonprofit website."""
    parsed = urlparse(url.lower())
    domain = parsed.netloc.lower()

    # Filter out vendor sites
    for vendor in VENDOR_DOMAINS:
        if vendor in domain:
            return False

    # Filter out infrastructure
    if any(x in domain for x in ['.js', '.css', '.png', '.jpg', '.pdf', '.svg',
                                  'cdn.', 'api.', 'admin.', 'app.', 'mail.',
                                  'smtp.', 'ns.', 'mx.']):
        return False

    # Must have a domain
    if '.' not in domain or domain.startswith(('localhost', '127.', '192.')):
        return False

    return True


def extract_nonprofits_from_network_for_good() -> Set[str]:
    """Scrape Network for Good more thoroughly."""
    print("\n[Network for Good] Extracting nonprofit websites...")
    websites = set()

    try:
        # Query Network for Good search with multiple keywords
        keywords = ['nonprofit', 'charity', 'volunteer', 'community', 'service',
                    'education', 'health', 'environment', 'youth', 'senior',
                    'poverty', 'animal', 'arts', 'international']

        for keyword in keywords:
            try:
                url = "https://www.networkforgood.org/giving-to"
                params = {'s': keyword}

                response = requests.get(url, params=params, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract all external links (to actual nonprofits)
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if href.startswith(('http://', 'https://')) and 'networkforgood' not in href:
                        norm = normalize_url(href)
                        if norm and is_nonprofit_domain(norm):
                            websites.add(norm)

                print(f"  Keyword '{keyword}': +{len(websites)} total")
                time.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                continue

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def extract_from_volunteer_platforms() -> Set[str]:
    """Extract from multiple volunteer platforms."""
    print("\n[Volunteer Platforms] Extracting from multiple platforms...")
    websites = set()

    platforms = [
        "https://www.volunteermatch.org/",
        "https://www.idealist.org/",
        "https://www.catchafire.org/",
        "https://www.spark.org/",
    ]

    for platform in platforms:
        try:
            response = requests.get(platform, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')):
                    norm = normalize_url(href)
                    if norm and is_nonprofit_domain(norm):
                        websites.add(norm)

            print(f"  {platform.split('/')[2]}: +{len(websites)} total")
            time.sleep(1)

        except Exception as e:
            pass

    return websites


def extract_from_charity_directories() -> Set[str]:
    """Extract from charity rating/directory websites."""
    print("\n[Charity Directories] Extracting from directories...")
    websites = set()

    directories = [
        "https://www.charitynavigator.org/",
        "https://www.guidestar.org/",
        "https://www.give.org/",
        "https://www.mindsimpact.org/",
    ]

    for directory in directories:
        try:
            response = requests.get(directory, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')):
                    norm = normalize_url(href)
                    if norm and is_nonprofit_domain(norm):
                        websites.add(norm)

            print(f"  {directory.split('/')[2]}: +{len(websites)} total")
            time.sleep(1)

        except Exception as e:
            pass

    return websites


def deduplicate_and_filter(websites: Set[str], registry: Set[str]) -> List[str]:
    """Filter and deduplicate."""
    new = sorted([w for w in websites if w not in registry])
    return new


def main():
    """Main execution."""
    print("=" * 80)
    print("Comprehensive Nonprofit Website Extraction from Volunteer Platforms")
    print("=" * 80)

    registry = load_registry()

    all_websites = set()

    # Multiple extraction strategies
    all_websites.update(extract_nonprofits_from_network_for_good())
    time.sleep(2)

    all_websites.update(extract_from_volunteer_platforms())
    time.sleep(2)

    all_websites.update(extract_from_charity_directories())

    # Filter
    new_websites = deduplicate_and_filter(all_websites, registry)

    # Output
    with open(OUTPUT_FILE, 'w') as f:
        f.write("Volunteer Platform & Civic Engagement Website Extraction\n")
        f.write("=" * 80 + "\n\n")
        f.write("Data Sources:\n")
        f.write("  - Network for Good (primary source)\n")
        f.write("  - VolunteerMatch.org\n")
        f.write("  - Idealist.org\n")
        f.write("  - Catchafire.org\n")
        f.write("  - Spark.org\n")
        f.write("  - Charity Navigator\n")
        f.write("  - GuideStar\n")
        f.write("  - Give.org\n")
        f.write("  - MindSimpact.org\n\n")
        f.write(f"Extraction Date: 2026-07-30\n\n")
        f.write(f"Results:\n")
        f.write(f"  Total websites collected: {len(all_websites)}\n")
        f.write(f"  Already in Daanaa registry: {len(all_websites) - len(new_websites)}\n")
        f.write(f"  NEW websites found: {len(new_websites)}\n")
        f.write(f"  Target: 300+\n\n")

        if new_websites:
            f.write("=" * 80 + "\n")
            f.write("NEW Nonprofit Websites Extracted from Volunteer Platforms:\n")
            f.write("=" * 80 + "\n\n")

            for idx, website in enumerate(new_websites, 1):
                f.write(f"{idx:5d}. {website}\n")

            f.write(f"\nTotal NEW websites: {len(new_websites)}\n")
            if len(new_websites) >= 300:
                f.write("✓ TARGET ACHIEVED: 300+ websites extracted\n")

    print(f"\n[Output] Results written to {OUTPUT_FILE}")
    print(f"Total websites: {len(all_websites)}")
    print(f"NEW websites: {len(new_websites)}")
    if len(new_websites) >= 300:
        print("✓ TARGET ACHIEVED")
    else:
        print(f"Progress: {len(new_websites)}/300 ({len(new_websites)/300*100:.1f}%)")


if __name__ == "__main__":
    main()
