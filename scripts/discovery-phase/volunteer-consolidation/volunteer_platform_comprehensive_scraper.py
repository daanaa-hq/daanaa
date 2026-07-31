#!/usr/bin/env python3
"""
Comprehensive nonprofit website extraction from volunteer platforms.

Strategies:
1. Query API endpoints where available (Idealist, VolunteerMatch, etc.)
2. Parse volunteer opportunity listings to extract organization websites
3. Access organization profile pages directly
4. Cross-reference with Daanaa registry
5. Deduplicate and output results
"""

import json
import sqlite3
import time
import random
import re
from typing import Set, Dict, List, Tuple
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

def load_registry_websites() -> Set[str]:
    """Load existing websites from Daanaa registry."""
    conn = sqlite3.connect(REGISTRY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT website FROM registry_enriched WHERE website IS NOT NULL AND website != ''")
    websites = {normalize_url(row[0]) for row in cursor.fetchall() if row[0]}
    conn.close()
    websites.discard("")
    print(f"[Registry] Loaded {len(websites)} existing websites from registry")
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
        if not parsed.netloc:
            return ""

        # Clean up domain
        domain = parsed.netloc.replace('www.', '')

        # Build normalized URL
        path = parsed.path.rstrip('/') if parsed.path else ''
        result = f"https://{domain}{path}"
        return result if len(result) > 10 else ""
    except (ValueError, Exception):
        return ""


def extract_urls_from_text(text: str) -> Set[str]:
    """Extract URLs from text."""
    if not text:
        return set()

    urls = set()
    # Pattern for http(s) URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]*[^\s<>"{}|\\^`\[\].,;:!?()]'
    matches = re.findall(url_pattern, text.lower())

    for match in matches:
        try:
            norm = normalize_url(match)
            if norm and 'idealist' not in norm and 'volunteermatch' not in norm and 'volunteerhub' not in norm:
                urls.add(norm)
        except:
            pass

    return urls


def safe_requests(url: str, headers: Dict = None, timeout: int = 15) -> requests.Response:
    """Safely make HTTP requests with retries."""
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt == 2:
                raise
            time.sleep(1 + random.random())
    return None


def scrape_idealist_orgs() -> Set[str]:
    """Scrape Idealist.org nonprofit organization websites."""
    print("\n[Idealist.org] Scraping nonprofit organization websites...")
    websites = set()

    try:
        # Try to access Idealist organizations directory
        urls_to_try = [
            "https://www.idealist.org/en/organizations",
            "https://www.idealist.org/browse/organizations",
            "https://idealist.org/organizations",
        ]

        for base_url in urls_to_try:
            try:
                response = safe_requests(base_url, timeout=15)
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract all organization links and their content
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if 'idealist.org' in href and ('/organizations/' in href or '/org/' in href):
                            # Extract text content from link context
                            parent = link.parent
                            if parent:
                                text = parent.get_text()
                                org_urls = extract_urls_from_text(text)
                                websites.update(org_urls)

                    # Extract from all text
                    text_content = soup.get_text()
                    org_urls = extract_urls_from_text(text_content)
                    websites.update(org_urls)

                    print(f"  Found {len(websites)} unique websites")
                    if websites:
                        break
                    time.sleep(1)
            except Exception as e:
                continue

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_volunteermatch_orgs() -> Set[str]:
    """Scrape VolunteerMatch nonprofit organization websites."""
    print("\n[VolunteerMatch] Scraping nonprofit organization websites...")
    websites = set()

    try:
        # VolunteerMatch frequently shows nonprofit profiles
        base_urls = [
            "https://www.volunteermatch.org/search/org",
            "https://www.volunteermatch.org/organizations",
        ]

        for base_url in base_urls:
            try:
                response = safe_requests(base_url, timeout=15)
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract organization website links
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')

                        # Look for links pointing to organization websites (not volunteermatch pages)
                        if href.startswith(('http://', 'https://')) and 'volunteermatch' not in href:
                            norm = normalize_url(href)
                            if norm and len(norm) > 15:
                                websites.add(norm)

                        # Extract from link text and surrounding context
                        text = link.get_text()
                        org_urls = extract_urls_from_text(text)
                        websites.update(org_urls)

                    # Extract from parent divs that likely contain org info
                    for div in soup.find_all('div', {'class': re.compile(r'.*org.*|.*non.*', re.I)}):
                        text = div.get_text()
                        org_urls = extract_urls_from_text(text)
                        websites.update(org_urls)

                    print(f"  Found {len(websites)} unique websites")
                    if websites:
                        break
                    time.sleep(1)

            except Exception as e:
                continue

    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_allfundraisers() -> Set[str]:
    """Scrape AllFundraisers nonprofit websites."""
    print("\n[AllFundraisers] Scraping nonprofit websites...")
    websites = set()

    try:
        response = safe_requests("https://allfundraisers.com/nonprofits/")
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract nonprofit links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')):
                    norm = normalize_url(href)
                    if norm and 'allfundraisers' not in norm:
                        websites.add(norm)

            text_content = soup.get_text()
            org_urls = extract_urls_from_text(text_content)
            websites.update(org_urls)

            print(f"  Found {len(websites)} unique websites")
            time.sleep(1)
    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_guidestar_profiles() -> Set[str]:
    """Scrape GuideStar nonprofit profiles."""
    print("\n[GuideStar] Scraping nonprofit websites...")
    websites = set()

    try:
        response = safe_requests("https://www.guidestar.org/nonprofit-directory")
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract organization links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')):
                    norm = normalize_url(href)
                    if norm and 'guidestar' not in norm:
                        websites.add(norm)

            text_content = soup.get_text()
            org_urls = extract_urls_from_text(text_content)
            websites.update(org_urls)

            print(f"  Found {len(websites)} unique websites")
            time.sleep(1)
    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_charity_navigator() -> Set[str]:
    """Scrape Charity Navigator nonprofit profiles."""
    print("\n[Charity Navigator] Scraping nonprofit websites...")
    websites = set()

    try:
        response = safe_requests("https://www.charitynavigator.org/")
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract organization links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')):
                    norm = normalize_url(href)
                    if norm and 'charitynavigator' not in norm:
                        websites.add(norm)

            text_content = soup.get_text()
            org_urls = extract_urls_from_text(text_content)
            websites.update(org_urls)

            print(f"  Found {len(websites)} unique websites")
            time.sleep(1)
    except Exception as e:
        print(f"  Error: {e}")

    return websites


def scrape_catchafire() -> Set[str]:
    """Scrape Catchafire nonprofit opportunities."""
    print("\n[Catchafire] Scraping nonprofit websites...")
    websites = set()

    try:
        response = safe_requests("https://www.catchafire.org/nonprofits/")
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')):
                    norm = normalize_url(href)
                    if norm and 'catchafire' not in norm:
                        websites.add(norm)

            text_content = soup.get_text()
            org_urls = extract_urls_from_text(text_content)
            websites.update(org_urls)

            print(f"  Found {len(websites)} unique websites")
            time.sleep(1)
    except Exception as e:
        print(f"  Error: {e}")

    return websites


def deduplicate_and_filter(all_websites: Set[str], registry_websites: Set[str]) -> Tuple[List[str], int]:
    """Deduplicate and filter new websites."""
    new_websites = []
    existing_count = 0

    for website in all_websites:
        if not website or len(website) < 15:
            continue

        if website in registry_websites:
            existing_count += 1
        else:
            new_websites.append(website)

    return sorted(set(new_websites)), existing_count


def main():
    """Main execution."""
    print("=" * 80)
    print("Volunteer Platform Comprehensive Website Extractor")
    print("=" * 80)

    # Load registry
    registry_websites = load_registry_websites()

    # Scrape all platforms
    all_websites = set()

    all_websites.update(scrape_volunteermatch_orgs())
    time.sleep(2)

    all_websites.update(scrape_idealist_orgs())
    time.sleep(2)

    all_websites.update(scrape_allfundraisers())
    time.sleep(2)

    all_websites.update(scrape_guidestar_profiles())
    time.sleep(2)

    all_websites.update(scrape_charity_navigator())
    time.sleep(2)

    all_websites.update(scrape_catchafire())

    # Deduplicate
    new_websites, existing_count = deduplicate_and_filter(all_websites, registry_websites)

    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        f.write("Volunteer Platform Comprehensive Website Extraction\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Extraction Date: 2026-07-30\n")
        f.write(f"Total Websites Collected: {len(all_websites)}\n")
        f.write(f"Already in Registry: {existing_count}\n")
        f.write(f"NEW Websites: {len(new_websites)}\n\n")

        if new_websites:
            f.write("=" * 80 + "\n")
            f.write("NEW Nonprofit Websites (not in Daanaa Registry):\n")
            f.write("=" * 80 + "\n\n")

            for idx, website in enumerate(new_websites, 1):
                f.write(f"{idx:4d}. {website}\n")

            f.write(f"\nTotal: {len(new_websites)} new websites\n")
        else:
            f.write("No new websites found.\n")

    print(f"\n[Output] Results written to {OUTPUT_FILE}")
    print(f"Total websites extracted: {len(all_websites)}")
    print(f"New websites found: {len(new_websites)}")
    print(f"Already in registry: {existing_count}")


if __name__ == "__main__":
    main()
