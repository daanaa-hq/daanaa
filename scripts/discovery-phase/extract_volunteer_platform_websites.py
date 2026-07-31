#!/usr/bin/env python3
"""
Extract nonprofit websites from volunteer platforms.

Sources:
  - Idealist.org API
  - VolunteerMatch API
  - LinkedIn volunteer opportunities
  - VolunteerHub search results

Cross-references with Daanaa registry and outputs deduplicated websites.
"""

import json
import sqlite3
import time
from typing import Set, Dict, List
from urllib.parse import urljoin, urlparse
import re
from collections import defaultdict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "requests", "beautifulsoup4"], check=True)
    import requests
    from bs4 import BeautifulSoup

# Registry database
REGISTRY_DB = "/home/akbar/meritgiving/data/merit_registry.db"
OUTPUT_FILE = "/tmp/agent15_volunteer_platforms_results.txt"

# Load registry for deduplication
def load_registry_websites() -> Set[str]:
    """Load existing websites from Daanaa registry."""
    conn = sqlite3.connect(REGISTRY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT website FROM registry_enriched WHERE website IS NOT NULL AND website != ''")
    websites = {row[0] for row in cursor.fetchall()}
    conn.close()
    print(f"[Registry] Loaded {len(websites)} existing websites from registry")
    return websites


def normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    # Handle invalid URLs
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return ""
        domain = parsed.netloc.replace('www.', '')
        return f"https://{domain}{parsed.path}".rstrip('/')
    except (ValueError, Exception):
        return ""


def extract_domains(url_str: str) -> Set[str]:
    """Extract domain from URL string."""
    if not url_str:
        return set()
    domains = set()
    # Try to extract URLs from text
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]*'
    matches = re.findall(url_pattern, url_str.lower())
    for match in matches:
        try:
            parsed = urlparse(match)
            if parsed.netloc:
                domains.add(normalize_url(match))
        except:
            pass
    return domains


def query_idealist_org() -> Dict[str, Set[str]]:
    """Query Idealist.org volunteer opportunities."""
    print("\n[Idealist.org] Querying volunteer opportunities...")
    results = defaultdict(set)

    try:
        # Idealist.org - search for nonprofits and get their profile pages
        base_url = "https://www.idealist.org/en/search"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        search_params = {
            'q': 'nonprofit',
            'type': 'organizations',
            'region': 'all',
            'sort': 'relevance'
        }

        try:
            response = requests.get(base_url, params=search_params, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract all links that reference organizations
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'organizations' in href or 'nonprofits' in href:
                    full_url = urljoin("https://www.idealist.org", href)
                    results['idealist_org_profiles'].add(full_url)

                # Check for website links in href
                if href.startswith(('http://', 'https://')):
                    domain_websites = extract_domains(href)
                    results['idealist_websites'].update(domain_websites)

            # Extract all visible text and search for URLs
            text_content = soup.get_text()
            websites = extract_domains(text_content)
            results['idealist_websites'].update(websites)

            print(f"  Found {len(results['idealist_org_profiles'])} organization profiles")
            print(f"  Found {len(results['idealist_websites'])} websites")
            time.sleep(2)
        except Exception as e:
            print(f"  Error querying: {e}")

    except Exception as e:
        print(f"[Idealist.org] Error: {e}")

    return results


def query_volunteer_match() -> Dict[str, Set[str]]:
    """Query VolunteerMatch opportunities."""
    print("\n[VolunteerMatch] Querying volunteer opportunities...")
    results = defaultdict(set)

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # VolunteerMatch search API
        base_url = "https://www.volunteermatch.org/search/org"
        params = {'k': 'nonprofit'}

        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract all organization links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'organizations' in href or 'nonprofits' in href or '/org/' in href:
                    full_url = urljoin("https://www.volunteermatch.org", href)
                    results['volunteermatch_profiles'].add(full_url)

                # Extract external website links
                if href.startswith(('http://', 'https://')) and 'volunteermatch' not in href:
                    domain_websites = extract_domains(href)
                    results['volunteermatch_websites'].update(domain_websites)

            # Extract URLs from page text
            text_content = soup.get_text()
            websites = extract_domains(text_content)
            results['volunteermatch_websites'].update(websites)

            print(f"  Found {len(results['volunteermatch_profiles'])} organization profiles")
            print(f"  Found {len(results['volunteermatch_websites'])} websites")
            time.sleep(2)

        except Exception as e:
            print(f"  Error querying: {e}")

    except Exception as e:
        print(f"[VolunteerMatch] Error: {e}")

    return results


def query_linkedin_volunteer() -> Dict[str, Set[str]]:
    """Query LinkedIn volunteer opportunities."""
    print("\n[LinkedIn] Querying volunteer opportunities...")
    results = defaultdict(set)

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; Daanaa Research Bot)'}

        # LinkedIn has volunteer opportunities indexed by nonprofit
        search_url = "https://www.linkedin.com/volunteer/opportunities"

        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract nonprofit links
            nonprofit_links = soup.find_all('a', href=re.compile(r'organizations|nonprofits'))
            for link in nonprofit_links:
                if link.get('href'):
                    results['linkedin_profiles'].add(urljoin("https://www.linkedin.com", link.get('href')))

            # Extract text content
            text_content = soup.get_text()
            websites = extract_domains(text_content)
            results['linkedin_websites'].update(websites)

            print(f"  Found {len(websites)} potential websites")
            time.sleep(1)
        except Exception as e:
            print(f"  Error querying LinkedIn: {e}")
    except Exception as e:
        print(f"[LinkedIn] Error: {e}")

    return results


def query_volunteerhub() -> Dict[str, Set[str]]:
    """Query VolunteerHub volunteer opportunities."""
    print("\n[VolunteerHub] Querying volunteer opportunities...")
    results = defaultdict(set)

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # VolunteerHub search
        search_url = "https://www.volunteerhub.com/search"
        params = {'q': 'nonprofit', 'type': 'opportunity'}

        try:
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract all links that might lead to organizations
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'organizations' in href or 'nonprofits' in href or '/org/' in href:
                    full_url = urljoin("https://www.volunteerhub.com", href)
                    results['volunteerhub_profiles'].add(full_url)

                # Extract external links
                if href.startswith(('http://', 'https://')) and 'volunteerhub' not in href:
                    domain_websites = extract_domains(href)
                    results['volunteerhub_websites'].update(domain_websites)

            # Extract URLs from text
            text_content = soup.get_text()
            websites = extract_domains(text_content)
            results['volunteerhub_websites'].update(websites)

            print(f"  Found {len(results['volunteerhub_profiles'])} organization profiles")
            print(f"  Found {len(results['volunteerhub_websites'])} websites")
            time.sleep(2)

        except Exception as e:
            print(f"  Error querying: {e}")

    except Exception as e:
        print(f"[VolunteerHub] Error: {e}")

    return results


def deduplicate_and_filter(all_websites: Set[str], registry_websites: Set[str]) -> List[tuple]:
    """Deduplicate websites and identify new ones not in registry."""
    normalized_registry = {normalize_url(w) for w in registry_websites if w}
    normalized_registry.discard("")  # Remove empty strings

    results = []
    new_count = 0
    existing_count = 0

    for website in all_websites:
        if not website or len(website) < 8:
            continue

        norm = normalize_url(website)
        if not norm:  # Skip invalid URLs
            continue
        if norm in normalized_registry:
            existing_count += 1
        else:
            new_count += 1
            results.append((norm, "new"))

    print(f"\n[Deduplication] Total collected: {len(all_websites)}")
    print(f"  Already in registry: {existing_count}")
    print(f"  New websites: {new_count}")

    return sorted(results, key=lambda x: x[0])


def main():
    """Main execution."""
    print("=" * 80)
    print("Volunteer Platform Website Extractor")
    print("=" * 80)

    # Load existing registry
    registry_websites = load_registry_websites()

    # Query all platforms
    all_results = {}

    all_results['idealist'] = query_idealist_org()
    time.sleep(2)

    all_results['volunteermatch'] = query_volunteer_match()
    time.sleep(2)

    all_results['linkedin'] = query_linkedin_volunteer()
    time.sleep(2)

    all_results['volunteerhub'] = query_volunteerhub()

    # Aggregate all websites
    all_websites = set()
    for platform_results in all_results.values():
        for key, websites in platform_results.items():
            if 'website' in key or 'url' in key:
                all_websites.update(websites)

    # Deduplicate
    deduped = deduplicate_and_filter(all_websites, registry_websites)

    # Write results
    with open(OUTPUT_FILE, 'w') as f:
        f.write("Volunteer Platform Website Extraction Results\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Extraction Date: 2026-07-30\n")
        f.write(f"Total Websites Collected: {len(all_websites)}\n")
        f.write(f"Websites Already in Registry: {len([x for x in deduped if x[1] == 'existing'])}\n")
        f.write(f"NEW Websites (not in registry): {len([x for x in deduped if x[1] == 'new'])}\n\n")

        f.write("Source Breakdown:\n")
        f.write("-" * 80 + "\n")
        for platform, results in all_results.items():
            website_count = sum(len(v) for k, v in results.items() if 'website' in k)
            f.write(f"{platform.upper()}: {website_count} websites\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("NEW Websites to Add to Registry:\n")
        f.write("=" * 80 + "\n\n")

        new_websites = [x[0] for x in deduped if x[1] == 'new']
        for idx, website in enumerate(new_websites, 1):
            f.write(f"{idx:4d}. {website}\n")

        f.write(f"\nTotal New Websites: {len(new_websites)}\n")

    print(f"\n[Output] Results written to {OUTPUT_FILE}")
    print(f"New websites found: {len([x for x in deduped if x[1] == 'new'])}")


if __name__ == "__main__":
    main()
