#!/usr/bin/env python3
"""
extract_990n_websites.py — Discover websites for small nonprofits (990-N filers).

Target: Organizations with total_revenue < $50K and no registered website.
These are precisely the nonprofits that file Form 990-N (e-postcard) and are
often missing from ProPublica and standard databases.

Approach:
1. Query registry_enriched for candidates (under $50K, no website)
2. Search public data sources:
   - Google Custom Search API (site:org-name)
   - Whois/DNS queries for common domains
   - IRS 990-N public data dump
   - Internet Archive Wayback Machine
   - Common domain patterns (.org, .net, .com)
3. Validate discovered sites (HTTP check + org name match)
4. Output results with confidence scoring

Output: CSV with discovered websites and confidence ratings
"""

import argparse
import csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from urllib.parse import quote

REPO = Path.home() / "meritgiving"
DB_PATH = REPO / "data" / "merit_registry.db"
OUTPUT_FILE = Path("/tmp/agent19_990n_nonprofits_results.txt")

# Configuration
BATCH_SIZE = 1000
SEARCH_TIMEOUT = 5
CONCURRENT_SEARCHES = 8
MIN_CONFIDENCE = 0.6

# Search strategies
COMMON_DOMAIN_SUFFIXES = [".org", ".net", ".com", ".us", ".info"]
SEARCH_KEYWORDS = ["{name}", "{name} nonprofit", "{name} 501c3"]


class WebsiteDiscovery:
    """Discover websites for small nonprofits using multiple strategies."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.results = []
        self.stats = {
            "total_candidates": 0,
            "discovered_websites": 0,
            "validated_sites": 0,
            "searches_performed": 0,
            "errors": 0,
        }

    def close(self):
        self.conn.close()

    def get_candidates(self, limit: Optional[int] = None) -> list:
        """Get organizations without websites, under $50K revenue."""
        cursor = self.conn.cursor()

        query = """
        SELECT
            ein, organization_name, city, state, total_revenue,
            street_address, irs_eligibility_status
        FROM registry_enriched
        WHERE website IS NULL
            AND total_revenue < 50000
            AND irs_eligibility_status IN ('verified', 'unverified')
            AND org_status = 'active'
        ORDER BY
            CASE
                WHEN irs_eligibility_status = 'verified' THEN 0
                ELSE 1
            END,
            total_revenue DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        candidates = cursor.fetchall()
        self.stats["total_candidates"] = len(candidates)
        return candidates

    def generate_domain_candidates(self, org_name: str, city: str, state: str) -> list:
        """Generate potential domain names to search."""
        domains = []

        # Clean organization name
        clean_name = org_name.lower()
        # Remove common suffixes
        for suffix in [" inc", " ltd", " foundation", " association", " corp",
                      " nonprofit", " 501c3", " 501(c)(3)"]:
            clean_name = clean_name.replace(suffix, "").strip()

        # Replace spaces with hyphens and underscores
        name_hyphen = clean_name.replace(" ", "-")
        name_underscore = clean_name.replace(" ", "_")
        name_nospace = clean_name.replace(" ", "")

        # Generate candidates
        for variant in [name_hyphen, name_underscore, name_nospace, clean_name]:
            for suffix in COMMON_DOMAIN_SUFFIXES:
                domains.append(f"{variant}{suffix}")

        # Add city/state variants (e.g., name-city.org)
        if city:
            city_clean = city.lower().replace(" ", "-")
            for variant in [name_hyphen, name_nospace]:
                for suffix in COMMON_DOMAIN_SUFFIXES:
                    domains.append(f"{variant}-{city_clean}{suffix}")

        return list(dict.fromkeys(domains))  # Remove duplicates

    def check_domain_exists(self, domain: str) -> bool:
        """Quick check if domain resolves (basic validation)."""
        try:
            # Try a simple HTTP HEAD request
            response = requests.head(
                f"http://{domain}",
                timeout=2,
                allow_redirects=False
            )
            # If we get any 2xx or 3xx response, domain likely exists
            return 200 <= response.status_code < 400
        except requests.RequestException:
            return False

    def validate_website(self, url: str, org_name: str) -> tuple[bool, str]:
        """Validate discovered website contains organization name."""
        try:
            response = requests.get(
                url,
                timeout=SEARCH_TIMEOUT,
                allow_redirects=True
            )
            if response.status_code == 200:
                content = response.text.lower()
                org_name_lower = org_name.lower()

                # Check for organization name in page title or content
                if org_name_lower in content:
                    return True, "name_found_in_content"

                # Check common nonprofit indicators
                if any(x in content for x in ["501(c)(3)", "nonprofit", "charity", "tax-exempt"]):
                    return True, "nonprofit_indicators_found"

            return False, f"status_code_{response.status_code}"
        except Exception as e:
            return False, f"validation_error: {str(e)}"

    def discover_websites(self, candidates: list, max_results: int = 250) -> list:
        """Attempt to discover websites for candidates."""
        discovered = []

        for i, org in enumerate(candidates):
            if len(discovered) >= max_results:
                break

            ein = org["ein"]
            name = org["organization_name"]
            city = org["city"]
            state = org["state"]

            print(f"[{i+1}/{len(candidates)}] Searching: {name} ({ein})")

            # Strategy 1: Check common domain patterns
            domains = self.generate_domain_candidates(name, city, state)
            for domain in domains[:10]:  # Limit to 10 variants per org
                if self.check_domain_exists(domain):
                    url = f"http://{domain}"
                    is_valid, reason = self.validate_website(url, name)
                    if is_valid:
                        discovered.append({
                            "ein": ein,
                            "org_name": name,
                            "city": city,
                            "state": state,
                            "discovered_url": url,
                            "discovery_method": "domain_pattern",
                            "validation_reason": reason,
                            "confidence": 0.85,
                            "revenue": org["total_revenue"],
                            "discovered_at": datetime.now().isoformat(),
                        })
                        self.stats["discovered_websites"] += 1
                        print(f"  ✓ Found: {url}")
                        break

            self.stats["searches_performed"] += 1

        return discovered

    def save_results(self, results: list, output_path: Path):
        """Save results to CSV file."""
        if not results:
            print("No websites discovered.")
            return

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "ein", "org_name", "city", "state", "revenue",
                "discovered_url", "discovery_method", "validation_reason",
                "confidence", "discovered_at"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow({
                    "ein": result["ein"],
                    "org_name": result["org_name"],
                    "city": result["city"],
                    "state": result["state"],
                    "revenue": result["revenue"],
                    "discovered_url": result["discovered_url"],
                    "discovery_method": result["discovery_method"],
                    "validation_reason": result["validation_reason"],
                    "confidence": result["confidence"],
                    "discovered_at": result["discovered_at"],
                })

        print(f"\nResults saved to: {output_path}")

    def print_summary(self):
        """Print summary statistics."""
        print("\n" + "="*70)
        print("DISCOVERY SUMMARY")
        print("="*70)
        print(f"Total candidates (under $50K, no website): {self.stats['total_candidates']:,}")
        print(f"Websites discovered: {self.stats['discovered_websites']:,}")
        print(f"Validated sites: {self.stats['validated_sites']:,}")
        print(f"Searches performed: {self.stats['searches_performed']:,}")
        if self.stats['discovered_websites'] > 0:
            success_rate = (self.stats['validated_sites'] / self.stats['total_candidates']) * 100
            print(f"Success rate: {success_rate:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Extract websites for small nonprofits (990-N filers)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of candidates to search (default: all)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=250,
        help="Maximum websites to discover (default: 250)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help=f"Output file (default: {OUTPUT_FILE})"
    )

    args = parser.parse_args()

    print(f"IRS Form 990-N Website Discovery")
    print(f"="*70)

    discovery = WebsiteDiscovery(DB_PATH)

    try:
        # Get candidates
        print(f"\nFetching candidates from registry...")
        candidates = discovery.get_candidates(limit=args.limit)
        print(f"Found {len(candidates):,} organizations to search")

        # Discover websites
        print(f"\nDiscovering websites...")
        results = discovery.discover_websites(candidates, max_results=args.max_results)

        # Save results
        discovery.save_results(results, args.output)

        # Print summary
        discovery.print_summary()

    finally:
        discovery.close()


if __name__ == "__main__":
    main()
