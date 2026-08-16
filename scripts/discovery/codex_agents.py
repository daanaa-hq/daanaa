#!/usr/bin/env python3
"""
Codex: Novel Website Discovery Strategies for High-Revenue Nonprofits

Tests 3 novel discovery strategies on 100-200 high-revenue orgs without websites:
1. Enhanced Name Parsing + Domain Variants — Parse org name for keywords, try .org/.com/.net/.foundation
2. Google Site Search + Name Enrichment — "organization name" site:* to find any web mentions
3. Domain History Heuristic — Try common prefixes/suffixes + check Wayback Machine

Logs results to logs/codex_results.jsonl + logs/codex_agents.log
"""

import sqlite3
import json
import time
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/codex_agents.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
RESULTS_FILE = Path('logs/codex_results.jsonl')

# User agent
UA = "Mozilla/5.0 (compatible; CodexBot/1.0; +https://daanaa.org) nonprofit-discovery"


class DomainVariantStrategy:
    """Strategy 1: Parse org name for keywords, try domain variants."""

    NAME_KEYWORDS = {
        'foundation': 1.0,
        'fund': 0.9,
        'center': 0.85,
        'institute': 0.85,
        'council': 0.8,
        'association': 0.8,
        'society': 0.8,
        'coalition': 0.8,
        'alliance': 0.75,
        'group': 0.7,
        'network': 0.7,
        'initiative': 0.7,
        'program': 0.7,
        'project': 0.65,
        'house': 0.6,
        'camp': 0.6,
        'school': 0.6,
    }

    TLD_VARIANTS = ['.org', '.com', '.net', '.foundation', '.charity', '.info']

    def __init__(self, timeout=5):
        self.timeout = timeout
        self.headers = {'User-Agent': UA}
        self.found_count = 0
        self.tested_count = 0

    def extract_domain_candidates(self, org_name: str, ein: str) -> List[Tuple[str, float]]:
        """Extract potential domain names from org name and EIN."""
        candidates = []

        # Clean org name
        clean_name = org_name.strip().upper()

        # Strategy: Remove common keywords and use remainder as domain
        for keyword in self.NAME_KEYWORDS.keys():
            if keyword.upper() in clean_name:
                base = clean_name.replace(keyword.upper(), '').strip()
                if base and len(base) > 2:
                    # Use first word as primary
                    words = base.split()
                    for word in words[:3]:
                        clean_word = ''.join(c for c in word if c.isalnum()).lower()
                        if len(clean_word) > 2:
                            confidence = self.NAME_KEYWORDS[keyword]
                            candidates.append((clean_word, confidence))

        # Also try full first word
        first_word = ''.join(c for c in clean_name.split()[0] if c.isalnum()).lower()
        if first_word and len(first_word) > 2:
            candidates.append((first_word, 0.5))

        # Try acronym from first letters
        if len(clean_name.split()) >= 2:
            acronym = ''.join(w[0] for w in clean_name.split() if w).lower()
            if 3 <= len(acronym) <= 6:
                candidates.append((acronym, 0.4))

        # Remove duplicates, keep highest confidence
        seen = {}
        for domain, conf in candidates:
            if domain not in seen or conf > seen[domain]:
                seen[domain] = conf

        return list(seen.items())

    def test_domain(self, domain: str) -> Optional[str]:
        """Test if domain is reachable and returns 200."""
        for tld in self.TLD_VARIANTS:
            url = f"https://{domain}{tld}"
            try:
                response = requests.head(url, timeout=self.timeout, headers=self.headers, allow_redirects=True)
                if response.status_code == 200:
                    return url
                # Also test GET for sites that don't like HEAD
                if response.status_code in [403, 405]:
                    response = requests.get(url, timeout=self.timeout, headers=self.headers, allow_redirects=True)
                    if response.status_code == 200:
                        return url
            except Exception:
                pass
        return None

    def discover(self, ein: str, org_name: str) -> Optional[Dict]:
        """Try to find website using domain variants."""
        self.tested_count += 1

        candidates = self.extract_domain_candidates(org_name, ein)

        for domain_base, confidence in candidates[:5]:  # Try top 5
            found_url = self.test_domain(domain_base)
            if found_url:
                self.found_count += 1
                return {
                    'strategy': 'domain_variants',
                    'website': found_url,
                    'confidence': confidence,
                    'domain_base': domain_base
                }

        return None


class GoogleSearchStrategy:
    """Strategy 2: Search for org + city/state on Google to find web presence."""

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.headers = {'User-Agent': UA}
        self.found_count = 0
        self.tested_count = 0
        # Note: using DuckDuckGo as backup since Google blocks scrapers

    def discover(self, ein: str, org_name: str, city: Optional[str] = None, state: Optional[str] = None) -> Optional[Dict]:
        """Search for org website using name + location."""
        self.tested_count += 1

        # Build search query
        query_parts = [org_name]
        if city:
            query_parts.append(city)
        if state:
            query_parts.append(state)

        query = ' '.join(query_parts)

        # Try DuckDuckGo's direct result (they allow bots)
        try:
            url = f"https://www.duckduckgo.com/?q={requests.utils.quote(query)}&t=h_&ia=web"
            response = requests.get(url, timeout=self.timeout, headers=self.headers)

            if response.status_code == 200:
                # Look for .org/.com domains in response that match org name patterns
                domain_pattern = r'(https?://[a-z0-9\-]+\.(?:org|com|net))'
                matches = re.findall(domain_pattern, response.text)

                for match in matches:
                    # Simple heuristic: if domain contains org name words, likely a match
                    org_words = set(org_name.split()[:2])  # First 2 words
                    domain_text = match.lower()

                    for word in org_words:
                        clean_word = ''.join(c for c in word if c.isalnum()).lower()
                        if clean_word and len(clean_word) > 2 and clean_word in domain_text:
                            # Test if it's live
                            try:
                                test_resp = requests.head(match, timeout=5, headers=self.headers, allow_redirects=True)
                                if test_resp.status_code == 200:
                                    self.found_count += 1
                                    return {
                                        'strategy': 'google_search',
                                        'website': match,
                                        'confidence': 0.7,
                                        'search_query': query
                                    }
                            except Exception:
                                pass
        except Exception as e:
            logger.debug(f"Google search failed for {ein}: {e}")

        return None


class WaybackMachineStrategy:
    """Strategy 3: Check Wayback Machine for historical domain evidence."""

    def __init__(self, timeout=8):
        self.timeout = timeout
        self.headers = {'User-Agent': UA}
        self.found_count = 0
        self.tested_count = 0

    def generate_domain_guesses(self, org_name: str, ein: str) -> List[str]:
        """Generate common domain name patterns to test."""
        guesses = []

        # First word only
        first_word = org_name.split()[0].lower()
        clean_first = ''.join(c for c in first_word if c.isalnum())
        if clean_first:
            guesses.append(f"{clean_first}.org")
            guesses.append(f"{clean_first}.com")

        # First two words
        if len(org_name.split()) >= 2:
            two_words = org_name.split()[:2]
            combined = ''.join(c for c in ''.join(two_words) if c.isalnum()).lower()
            if combined and len(combined) < 25:
                guesses.append(f"{combined}.org")
                guesses.append(f"{combined}.com")

        # Acronym
        acronym = ''.join(w[0].lower() for w in org_name.split() if w)
        if 3 <= len(acronym) <= 6:
            guesses.append(f"{acronym}.org")
            guesses.append(f"{acronym}.com")

        # EIN as fallback
        if ein:
            guesses.append(f"{ein}.org")

        return guesses[:8]

    def check_wayback(self, domain: str) -> Optional[str]:
        """Check if domain appears in Wayback Machine."""
        try:
            # Wayback API to check if snapshot exists
            api_url = f"https://archive.org/wayback/available?url={domain}&output=json"
            response = requests.get(api_url, timeout=self.timeout, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                if data.get('archived_snapshots') and data['archived_snapshots'].get('closest'):
                    snapshot = data['archived_snapshots']['closest']
                    # If there's a snapshot AND status is 200, domain likely exists
                    if snapshot.get('status') == '200':
                        # Construct the live domain URL
                        parsed = urlparse(domain)
                        if parsed.scheme:
                            return domain
                        else:
                            return f"https://{domain}"
        except Exception as e:
            logger.debug(f"Wayback check failed for {domain}: {e}")

        return None

    def discover(self, ein: str, org_name: str) -> Optional[Dict]:
        """Try to find website using Wayback Machine evidence."""
        self.tested_count += 1

        guesses = self.generate_domain_guesses(org_name, ein)

        for guess in guesses:
            found_url = self.check_wayback(guess)
            if found_url:
                # Verify it's actually live now
                try:
                    resp = requests.head(found_url, timeout=5, headers=self.headers, allow_redirects=True)
                    if resp.status_code == 200:
                        self.found_count += 1
                        return {
                            'strategy': 'wayback_machine',
                            'website': found_url,
                            'confidence': 0.75,
                            'wayback_evidence': guess
                        }
                except Exception:
                    pass

        return None


class CodexDiscoveryEngine:
    """Main engine: run all strategies on a batch of orgs."""

    def __init__(self):
        self.domain_strategy = DomainVariantStrategy()
        self.google_strategy = GoogleSearchStrategy()
        self.wayback_strategy = WaybackMachineStrategy()
        self.results = []
        self.start_time = None

    def get_high_revenue_orgs_without_websites(self, offset: int = 300, limit: int = 150) -> List[Dict]:
        """Fetch high-revenue orgs without websites, starting at offset."""
        db = sqlite3.connect(str(DB_PATH))
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("""
            SELECT EIN, organization_name, total_revenue, CITY, STATE
            FROM registry_enriched
            WHERE total_revenue > 500000
            AND (website IS NULL OR website = '' OR website = 'unknown')
            AND org_status = 'active'
            ORDER BY total_revenue DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        orgs = [dict(row) for row in cursor.fetchall()]
        db.close()

        return orgs

    def run_discovery(self, ein: str, org_name: str, city: Optional[str] = None, state: Optional[str] = None) -> Optional[Dict]:
        """Run all strategies on one org, return first success."""

        # Strategy 1: Domain Variants
        result = self.domain_strategy.discover(ein, org_name)
        if result:
            return result

        time.sleep(0.5)  # Rate limiting

        # Strategy 2: Google Search
        result = self.google_strategy.discover(ein, org_name, city, state)
        if result:
            return result

        time.sleep(0.5)

        # Strategy 3: Wayback Machine
        result = self.wayback_strategy.discover(ein, org_name)
        if result:
            return result

        return None

    def execute(self, offset: int = 300, limit: int = 150, max_workers: int = 5):
        """Execute discovery on batch of orgs."""
        self.start_time = time.time()

        logger.info(f"Starting Codex discovery: offset={offset}, limit={limit}")

        orgs = self.get_high_revenue_orgs_without_websites(offset, limit)
        logger.info(f"Loaded {len(orgs)} orgs for testing")

        # Run in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for org in orgs:
                future = executor.submit(
                    self.run_discovery,
                    org['EIN'],
                    org['organization_name'],
                    org.get('CITY'),
                    org.get('STATE')
                )
                futures[future] = org

            for future in as_completed(futures):
                org = futures[future]
                try:
                    result = future.result()
                    self.record_result(org, result)
                except Exception as e:
                    logger.error(f"Error processing {org['EIN']}: {e}")
                    self.record_result(org, None, error=str(e))

        elapsed = time.time() - self.start_time
        self.print_summary(elapsed)

    def record_result(self, org: Dict, discovery_result: Optional[Dict], error: Optional[str] = None):
        """Record a result to JSON."""
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'ein': org['EIN'],
            'org_name': org['organization_name'],
            'revenue': org['total_revenue'],
            'state': org.get('STATE'),
            'discovered_website': discovery_result['website'] if discovery_result else None,
            'strategy': discovery_result['strategy'] if discovery_result else None,
            'confidence': discovery_result['confidence'] if discovery_result else None,
            'error': error
        }

        self.results.append(record)

        # Write to JSONL immediately
        with open(RESULTS_FILE, 'a') as f:
            f.write(json.dumps(record) + '\n')

        if discovery_result:
            logger.info(f"✓ {org['EIN']} - {discovery_result['strategy']}: {discovery_result['website']}")
        else:
            logger.debug(f"✗ {org['EIN']} - No discovery")

    def print_summary(self, elapsed_seconds: float):
        """Print summary statistics."""
        total_orgs = len(self.results)
        websites_found = sum(1 for r in self.results if r['discovered_website'])

        strategies_count = {}
        for result in self.results:
            if result['strategy']:
                strategies_count[result['strategy']] = strategies_count.get(result['strategy'], 0) + 1

        success_rate = (websites_found / total_orgs * 100) if total_orgs > 0 else 0

        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_orgs_tested': total_orgs,
            'websites_found': websites_found,
            'success_rate_percent': success_rate,
            'time_seconds': elapsed_seconds,
            'strategies_breakdown': strategies_count,
            'strategy_success_rates': {
                'domain_variants': sum(1 for r in self.results if r['strategy'] == 'domain_variants') / total_orgs * 100 if total_orgs > 0 else 0,
                'google_search': sum(1 for r in self.results if r['strategy'] == 'google_search') / total_orgs * 100 if total_orgs > 0 else 0,
                'wayback_machine': sum(1 for r in self.results if r['strategy'] == 'wayback_machine') / total_orgs * 100 if total_orgs > 0 else 0,
            }
        }

        logger.info("\n" + "="*60)
        logger.info("CODEX DISCOVERY SUMMARY")
        logger.info("="*60)
        logger.info(f"Total orgs tested: {total_orgs}")
        logger.info(f"Websites found: {websites_found}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Time elapsed: {elapsed_seconds:.1f}s ({elapsed_seconds/60:.1f}m)")
        logger.info(f"\nStrategy breakdown:")
        for strategy, count in strategies_count.items():
            pct = count / total_orgs * 100 if total_orgs > 0 else 0
            logger.info(f"  {strategy}: {count} ({pct:.1f}%)")
        logger.info("="*60 + "\n")

        # Write summary to file
        with open('logs/codex_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        return summary


if __name__ == '__main__':
    import sys

    # Parse arguments
    offset = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 150

    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)

    # Run discovery
    engine = CodexDiscoveryEngine()
    engine.execute(offset=offset, limit=limit, max_workers=5)
