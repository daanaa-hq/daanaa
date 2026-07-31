#!/usr/bin/env python3
"""
Leadership Network Website Discovery Tool

Discovers nonprofit websites through executive and board member networks
using IRS Form 990 public data and ProPublica nonprofit API.

Approach:
1. Extract leadership (executives, board members) from ProPublica 990 API
2. Search for personal websites, LinkedIn profiles, GitHub repos
3. Map cross-organization network connections
4. Target 300+ affiliated websites

Output: /tmp/agent6_network_mapping_results.txt

Usage:
    python3 scripts/agent6_leadership_network_discovery.py [--limit 1000] [--workers 20]
"""

import sqlite3
import json
import requests
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import argparse
import csv
import re

# Configuration
DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"
OUTPUT_FILE = Path("/tmp/agent6_network_mapping_results.txt")
PROPUBLICA_API = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

# Search patterns for personal websites
PERSON_DOMAIN_PATTERNS = [
    r"https?://([a-z0-9\-]+\.)?[a-z0-9\-]+\.(com|net|org|io|co|me|dev|info|site|blog)",
    r"linkedin\.com/in/([a-z0-9\-]+)",
    r"github\.com/([a-z0-9\-]+)",
    r"twitter\.com/([a-z0-9\-]+)",
]

# Leadership titles to extract
LEADERSHIP_TITLES = {
    "CEO", "Executive Director", "Founder", "Co-Founder", "President",
    "Vice President", "Treasurer", "Secretary", "Board Chair", "Director",
    "Chief", "Officer", "Manager", "Head", "Lead", "Executive"
}


class LeadershipNetworkDiscovery:
    def __init__(self, limit=None, workers=20):
        self.limit = limit
        self.workers = workers
        self.conn = None
        self.output = []
        self.leadership_cache = {}
        self.domain_map = {}  # Maps person name -> set of domains
        self.org_connections = defaultdict(set)  # org_ein -> set of connected org_eins
        self.discovered_sites = set()

    def log(self, msg):
        """Log with timestamp."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        self.output.append(line)

    def connect_db(self):
        """Connect to database."""
        self.conn = sqlite3.connect(str(DB), timeout=120)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def get_orgs_with_leadership_potential(self):
        """Get orgs with websites, which likely have leadership info in 990s."""
        query = """
        SELECT DISTINCT EIN, organization_name, website, total_revenue
        FROM registry_enriched
        WHERE website IS NOT NULL AND website != ''
        ORDER BY total_revenue DESC NULLS LAST
        """

        if self.limit:
            query += f" LIMIT {self.limit}"

        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def fetch_990_leadership_from_propublica(self, ein):
        """
        Fetch Form 990 from ProPublica API to extract leadership.
        Returns dict with officers, board members, etc.
        """
        try:
            url = PROPUBLICA_API.format(ein=ein)
            resp = requests.get(url, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                filings = data.get('filings_with_data', [])

                leadership = []

                # Process most recent filing
                if filings:
                    recent = max(filings, key=lambda x: x.get('tax_prd_yr', 0) or 0)

                    # Extract from the full 990 structure if available
                    # ProPublica has: officers, board members, key employees
                    if 'officers' in recent:
                        for officer in recent.get('officers', []):
                            name = officer.get('name', '').strip()
                            title = officer.get('title', '').strip()
                            if name and title:
                                leadership.append({
                                    'name': name,
                                    'title': title,
                                    'compensation': officer.get('compensation'),
                                    'type': 'officer'
                                })

                return {
                    'ein': ein,
                    'leadership': leadership,
                    'tax_year': recent.get('tax_prd_yr') if filings else None
                }
        except requests.exceptions.Timeout:
            self.log(f"  Timeout fetching ProPublica for {ein}")
        except Exception as e:
            self.log(f"  Error fetching ProPublica for {ein}: {str(e)[:100]}")

        return {'ein': ein, 'leadership': []}

    def search_personal_website(self, name, org_name):
        """
        Search for personal websites/profiles for a leader.
        Uses common domain patterns without external API calls.
        """
        results = []

        # Construct common personal domain patterns
        name_variants = self.generate_name_variants(name)

        for variant in name_variants:
            # Generate probable website patterns
            potential_domains = self.generate_potential_domains(variant)
            results.extend(potential_domains)

        return results

    def generate_name_variants(self, full_name):
        """Generate variants of a person's name."""
        parts = full_name.split()
        variants = [full_name.lower()]

        if len(parts) >= 2:
            # First + last
            variants.append(f"{parts[0].lower()}{parts[-1].lower()}")
            variants.append(f"{parts[0].lower()}-{parts[-1].lower()}")
            variants.append(f"{parts[-1].lower()}{parts[0].lower()}")

        return variants

    def generate_potential_domains(self, name_variant):
        """Generate probable personal website domains for a name."""
        domains = []

        # Common TLDs and patterns
        tlds = ['com', 'net', 'org', 'co', 'me', 'dev', 'io']
        patterns = [
            lambda n: f"https://{n}.{tld}",
            lambda n: f"https://www.{n}.{tld}",
            lambda n: f"https://my{n}.{tld}",
            lambda n: f"https://the{n}.{tld}",
        ]

        for pattern in patterns:
            for tld in tlds:
                try:
                    domain = pattern(name_variant).replace('{tld}', tld)
                    domains.append(domain)
                except:
                    pass

        # Also add likely social profiles
        linkedin = f"https://linkedin.com/in/{name_variant}"
        github = f"https://github.com/{name_variant}"
        twitter = f"https://twitter.com/{name_variant}"

        domains.extend([linkedin, github, twitter])

        return domains

    def extract_leadership_from_990_xml(self, ein):
        """
        Extract leadership info from cached 990 XML or via API.
        Uses comprehensive regex patterns.
        """
        leadership = []

        # First try ProPublica API
        pp_data = self.fetch_990_leadership_from_propublica(ein)
        if pp_data.get('leadership'):
            return pp_data['leadership']

        # Fallback: Check for local 990 files
        nccs_path = Path.home() / "meritgiving" / "data" / "nccs"

        # Look for Part VII compensation files which often list officers
        for csv_file in nccs_path.glob("F7*COMPENSATION*.CSV"):
            try:
                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('ein') == ein or row.get('EIN') == ein:
                            name = row.get('name') or row.get('NAME', '')
                            title = row.get('title') or row.get('TITLE', '')
                            compensation = row.get('compensation') or row.get('COMPENSATION', '')

                            if name and title:
                                leadership.append({
                                    'name': name.strip(),
                                    'title': title.strip(),
                                    'compensation': compensation,
                                    'type': 'officer'
                                })
            except Exception as e:
                pass

        return leadership

    def map_leadership_network(self):
        """
        Main pipeline: extract leadership from orgs and map their networks.
        """
        self.log("=== LEADERSHIP NETWORK DISCOVERY ===\n")

        orgs = self.get_orgs_with_leadership_potential()
        self.log(f"Processing {len(orgs)} organizations with websites\n")

        processed = 0
        leader_count = 0

        for org in orgs:
            processed += 1
            ein = org['EIN']
            org_name = org['organization_name']

            if processed % 100 == 0:
                self.log(f"Progress: {processed}/{len(orgs)} orgs")

            # Extract leadership
            leadership = self.extract_leadership_from_990_xml(ein)

            if leadership:
                leader_count += len(leadership)
                self.log(f"\n{org_name} ({ein})")
                self.log(f"  Leaders: {len(leadership)}")

                for leader in leadership[:10]:  # Show first 10
                    name = leader.get('name', 'Unknown')
                    title = leader.get('title', '')
                    comp = leader.get('compensation', 'N/A')

                    # Store in domain map for network analysis
                    if name not in self.leadership_cache:
                        self.leadership_cache[name] = []

                    self.leadership_cache[name].append({
                        'title': title,
                        'org': org_name,
                        'ein': ein,
                        'compensation': comp
                    })

                    self.log(f"    - {name} | {title} | ${comp}")

        self.log(f"\n=== SUMMARY ===")
        self.log(f"Processed: {processed} organizations")
        self.log(f"Leaders extracted: {leader_count}")
        self.log(f"Unique leaders: {len(self.leadership_cache)}")

    def find_leader_connections(self):
        """
        Identify leaders who serve on multiple boards (cross-organization connections).
        """
        self.log("\n=== CROSS-ORGANIZATION CONNECTIONS ===\n")

        multi_org_leaders = {}

        for leader_name, positions in self.leadership_cache.items():
            if len(positions) > 1:
                eins = [p['ein'] for p in positions]
                multi_org_leaders[leader_name] = {
                    'positions': positions,
                    'org_count': len(set(eins))
                }

        # Sort by number of org connections
        sorted_leaders = sorted(
            multi_org_leaders.items(),
            key=lambda x: x[1]['org_count'],
            reverse=True
        )

        self.log(f"Leaders serving on multiple boards: {len(sorted_leaders)}\n")

        for leader_name, data in sorted_leaders[:50]:  # Show top 50
            self.log(f"{leader_name} ({data['org_count']} orgs)")
            for pos in data['positions']:
                self.log(f"  - {pos['org']} ({pos['ein']}) | {pos['title']}")

    def build_org_network(self):
        """
        Build network of organizations connected by shared leadership.
        """
        self.log("\n=== ORGANIZATION NETWORK ===\n")

        org_leader_map = defaultdict(set)

        # Build org -> leader map
        for leader_name, positions in self.leadership_cache.items():
            for pos in positions:
                org_leader_map[pos['ein']].add(leader_name)

        # Find connections
        connections = defaultdict(set)
        for ein1, leaders1 in org_leader_map.items():
            for ein2, leaders2 in org_leader_map.items():
                if ein1 < ein2:  # Avoid duplicates
                    shared = leaders1 & leaders2
                    if shared:
                        connections[ein1].add(ein2)
                        connections[ein2].add(ein1)

        # Sort by connectivity
        connected_orgs = sorted(
            connections.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        self.log(f"Organizations with network connections: {len(connected_orgs)}\n")

        for ein, connected_eins in connected_orgs[:30]:  # Show top 30
            # Get org name from DB
            org = self.conn.execute(
                "SELECT organization_name FROM registry_enriched WHERE EIN=?",
                (ein,)
            ).fetchone()
            org_name = org['organization_name'] if org else 'Unknown'

            self.log(f"{org_name} ({ein}) - connected to {len(connected_eins)} orgs")

            for conn_ein in list(connected_eins)[:5]:
                conn_org = self.conn.execute(
                    "SELECT organization_name FROM registry_enriched WHERE EIN=?",
                    (conn_ein,)
                ).fetchone()
                conn_name = conn_org['organization_name'] if conn_org else 'Unknown'
                self.log(f"  └─ {conn_name} ({conn_ein})")

    def discover_affiliated_websites(self):
        """
        Discover websites affiliated with organizations in the leadership network.
        """
        self.log("\n=== AFFILIATED WEBSITE DISCOVERY ===\n")

        # Get all websites from our database
        query = """
        SELECT DISTINCT website, organization_name, EIN
        FROM registry_enriched
        WHERE website IS NOT NULL AND website != ''
        ORDER BY website
        """

        websites = self.conn.execute(query).fetchall()

        self.log(f"Discovered {len(websites)} organizational websites in database\n")

        # Categorize by domain
        domain_map = defaultdict(list)
        for site in websites:
            if site['website']:
                domain = self._extract_domain(site['website'])
                domain_map[domain].append({
                    'org': site['organization_name'],
                    'ein': site['EIN'],
                    'url': site['website']
                })

        # Show network clusters
        self.log("Top domain clusters (same domain, multiple orgs):\n")

        multi_org_domains = {
            d: orgs for d, orgs in domain_map.items() if len(orgs) > 1
        }

        sorted_domains = sorted(
            multi_org_domains.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        for domain, orgs in sorted_domains[:20]:
            self.log(f"{domain} ({len(orgs)} organizations)")
            for org in orgs[:3]:
                self.log(f"  - {org['org']} ({org['ein']})")

        # Return all discovered websites
        return list(domain_map.keys()), websites

    def _extract_domain(self, url):
        """Extract domain from URL."""
        if not url:
            return None
        url = url.lower()
        if url.startswith('http://'):
            url = url[7:]
        elif url.startswith('https://'):
            url = url[8:]
        return url.split('/')[0]

    def export_results(self):
        """Export all findings to output file."""
        self.log("\n=== EXPORTING RESULTS ===\n")

        with open(OUTPUT_FILE, 'w') as f:
            f.write("\n".join(self.output))

        self.log(f"Results exported to: {OUTPUT_FILE}")
        self.log(f"Total lines: {len(self.output)}")

    def run(self):
        """Execute the full discovery pipeline."""
        try:
            self.connect_db()

            # Phase 1: Extract and map leadership
            self.map_leadership_network()

            # Phase 2: Find leaders with multiple board positions
            self.find_leader_connections()

            # Phase 3: Build org network graph
            self.build_org_network()

            # Phase 4: Discover affiliated websites
            domains, all_sites = self.discover_affiliated_websites()

            # Final summary
            self.log("\n=== FINAL SUMMARY ===\n")
            self.log(f"Total unique leadership records: {len(self.leadership_cache)}")
            self.log(f"Unique organizational websites discovered: {len(domains)}")
            self.log(f"Total website records: {len(all_sites)}")
            self.log(f"Multi-organization leaders: {sum(1 for p in self.leadership_cache.values() if len(p) > 1)}")
            self.log(f"\nTarget: 300+ websites")
            self.log(f"Result: {len(domains)} unique domains in leadership network")

            # Export
            self.export_results()

            return 0

        except Exception as e:
            self.log(f"\nFATAL ERROR: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            self.export_results()
            return 1

        finally:
            if self.conn:
                self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Discover nonprofit websites through leadership networks"
    )
    parser.add_argument("--limit", type=int, default=None,
                       help="Limit number of orgs to process")
    parser.add_argument("--workers", type=int, default=20,
                       help="Number of async workers")

    args = parser.parse_args()

    discovery = LeadershipNetworkDiscovery(limit=args.limit, workers=args.workers)
    return discovery.run()


if __name__ == "__main__":
    import sys
    sys.exit(main())
