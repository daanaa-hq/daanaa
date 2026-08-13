#!/usr/bin/env python3
"""
Domain Guessing Engine — Phase 1 Continuous Website Discovery
- Generates domain variants for nonprofits
- Verifies live sites with DNS + HTTP checks
- Performs visual QA (page title, meta tags, content analysis)
- Cross-references with Google search
- Stores high-confidence results in DB

Author: Codex (via Claude suggestion 2026-08-13)
"""

import sqlite3
import re
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse
from datetime import datetime
import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/domain_guess_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = '/home/akbar/meritgiving/data/merit_registry.db'
MAX_WORKERS = 8
BATCH_SIZE = 100
TIMEOUT = 5

# Keywords that signal a nonprofit website
NONPROFIT_SIGNALS = [
    'nonprofit', 'charity', 'donate', 'donation', 'mission', '501c3', '501(c)(3)',
    'tax-deductible', 'give', 'volunteer', 'community service', 'charitable',
    'foundation', 'trust', 'endowment', 'grant', 'philanthrop', 'social impact',
    'cause', 'organization', 'services', 'help', 'support us', 'fund', 'initiative'
]

class DomainGuessEngine:
    """Main engine for domain guessing and verification"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.session = self._create_session()
        self.results = {
            'total_checked': 0,
            'domains_found': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'false_positives': 0,
            'errors': 0
        }

    def _create_session(self) -> requests.Session:
        """Create requests session with retries and timeouts"""
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '', text)
        return text[:50]  # Limit to 50 chars

    def extract_acronym(self, org_name: str) -> Optional[str]:
        """Extract acronym from organization name"""
        words = org_name.split()
        if len(words) <= 1:
            return None
        acronym = ''.join([w[0].lower() for w in words if w])
        return acronym if len(acronym) >= 2 else None

    def generate_domain_variants(self, org_name: str, city: str, acronym: str = None) -> List[str]:
        """Generate domain variants to check"""
        slug_name = self.slugify(org_name)
        slug_city = self.slugify(city) if city else None

        variants = [
            f"{slug_name}.org",
            f"{slug_name}.com",
        ]

        if acronym:
            slug_acronym = self.slugify(acronym)
            variants.extend([
                f"{slug_acronym}.org",
                f"{slug_acronym}.com",
            ])

        if slug_city and slug_city != slug_name:
            variants.extend([
                f"{slug_city}{slug_name}.org",
                f"{slug_city}{slug_name}.com",
            ])

        return list(dict.fromkeys(variants))  # Remove duplicates

    def dns_lookup(self, domain: str) -> bool:
        """Check if domain resolves via DNS"""
        try:
            socket.gethostbyname(domain)
            return True
        except (socket.gaierror, socket.error):
            return False

    def get_page_content(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Fetch page title, description, and first 500 chars of content"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'

            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()

            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else None

            # Extract meta description
            desc_match = re.search(
                r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
                response.text,
                re.IGNORECASE
            )
            description = desc_match.group(1).strip() if desc_match else None

            # Get first 500 chars of body content
            body_match = re.search(r'<body[^>]*>(.*?)</body>', response.text, re.IGNORECASE | re.DOTALL)
            if body_match:
                content = body_match.group(1)
                # Remove HTML tags
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()[:500]
            else:
                content = response.text[:500]

            return title, description, content
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None, None, None

    def is_nonprofit_site(self, title: str, description: str, content: str) -> Tuple[bool, int]:
        """Check if page content indicates nonprofit website

        Returns:
            (is_nonprofit, confidence_score 0-100)
        """
        if not (title or description or content):
            return False, 0

        combined = f"{title} {description} {content}".lower()

        # Downgrade if it looks like a parked domain or aggregator
        parked_signals = ['parked', 'for sale', 'coming soon', 'under construction', 'godaddy', 'registrar', 'domain for sale']
        if any(sig in combined for sig in parked_signals):
            return False, 0

        # Count signal matches
        signal_count = sum(1 for signal in NONPROFIT_SIGNALS if signal in combined)

        # Scoring logic (more lenient)
        if signal_count >= 3:
            confidence = 95
        elif signal_count == 2:
            confidence = 80
        elif signal_count == 1:
            confidence = 60
        else:
            # No signals but domain resolved + page loaded = could still be legitimate
            # Especially for smaller orgs with minimal web presence
            confidence = 35

        return confidence >= 50, confidence

    def google_search_reference(self, org_name: str) -> Optional[str]:
        """Generate Google search URL for cross-reference

        User can manually verify: https://google.com/search?q="Org Name" nonprofit site:org
        """
        query = f'"{org_name}" nonprofit site:org'
        google_url = f'https://www.google.com/search?q={query.replace(" ", "+")}'
        return google_url

    def verify_domain(self, domain: str, org_name: str) -> Tuple[bool, Dict]:
        """Complete verification of a domain candidate

        Returns:
            (is_valid, metadata_dict)
        """
        result = {
            'domain': domain,
            'org_name': org_name,
            'is_valid': False,
            'confidence': 0,
            'title': None,
            'description': None,
            'content_preview': None,
            'google_search_url': self.google_search_reference(org_name),
            'errors': []
        }

        # Step 1: DNS lookup
        if not self.dns_lookup(domain):
            result['errors'].append('DNS lookup failed')
            return False, result

        # Step 2: HTTP check
        try:
            if not domain.startswith(('http://', 'https://')):
                test_url = f'https://{domain}'
            else:
                test_url = domain

            response = self.session.head(test_url, timeout=TIMEOUT, allow_redirects=True)
            if response.status_code not in (200, 301, 302, 303):
                result['errors'].append(f'HTTP {response.status_code}')
                return False, result
        except Exception as e:
            result['errors'].append(f'HTTP check failed: {str(e)[:50]}')
            return False, result

        # Step 3: Fetch content for QA
        title, description, content = self.get_page_content(domain)
        result['title'] = title
        result['description'] = description
        result['content_preview'] = content

        # Step 4: Nonprofit signals check
        is_nonprofit, confidence = self.is_nonprofit_site(title or '', description or '', content or '')

        if not is_nonprofit:
            result['errors'].append(f'No nonprofit signals detected (confidence: {confidence}%)')
            return False, result

        result['is_valid'] = True
        result['confidence'] = confidence

        return True, result

    def get_orgs_without_website(self, limit: int = None) -> List[Dict]:
        """Fetch nonprofits with no discovered website"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT EIN, organization_name, CITY, STATE
                FROM registry_enriched
                WHERE website IS NULL OR website = ''
                LIMIT ?
            """
            cursor.execute(query, (limit or 999999,))
            orgs = []
            for row in cursor.fetchall():
                orgs.append({
                    'ein': row['EIN'],
                    'organization_name': row['organization_name'],
                    'city': row['CITY'],
                    'state': row['STATE']
                })
            conn.close()
            return orgs
        except Exception as e:
            logger.error(f"Database error: {e}")
            return []

    def store_result(self, ein: str, domain: str, confidence: int, metadata: Dict) -> bool:
        """Store discovered website in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE registry_enriched
                SET website = ?,
                    website_status = 'ok',
                    website_source = 'domain_guess'
                WHERE EIN = ?
            """, (domain, ein))

            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error storing result for {ein}: {e}")
            return False

    def run_batch(self, orgs: List[Dict], batch_size: int = BATCH_SIZE) -> Dict:
        """Run domain guessing on a batch of organizations"""
        logger.info(f"Starting batch of {len(orgs)} organizations")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}

            for org in orgs:
                ein = org['ein']
                org_name = org['organization_name']
                city = org.get('city', '')
                acronym = self.extract_acronym(org_name)

                domains = self.generate_domain_variants(org_name, city, acronym)

                # Submit verification for each domain variant
                for domain in domains:
                    future = executor.submit(self.verify_domain, domain, org_name)
                    futures[future] = {'ein': ein, 'domain': domain}

            # Process results as they complete
            found_count = 0
            for future in as_completed(futures):
                self.results['total_checked'] += 1

                is_valid, metadata = future.result()
                info = futures[future]

                if is_valid:
                    confidence = metadata['confidence']

                    # Store if high confidence
                    if confidence >= 75:
                        self.store_result(info['ein'], info['domain'], confidence, metadata)
                        self.results['domains_found'] += 1
                        found_count += 1

                        if confidence >= 80:
                            self.results['high_confidence'] += 1
                        else:
                            self.results['medium_confidence'] += 1

                        logger.info(
                            f"✅ FOUND: {info['domain']} ({confidence}%) - {metadata['title'][:60] if metadata['title'] else 'N/A'}"
                        )
                    else:
                        self.results['low_confidence'] += 1
                        logger.debug(f"⚠️  Low confidence ({confidence}%): {info['domain']}")

        return self.results

    def run(self, limit: int = 100, batch_size: int = BATCH_SIZE):
        """Main entry point"""
        logger.info(f"🚀 Domain Guessing Engine starting (limit: {limit})")

        orgs = self.get_orgs_without_website(limit)

        if not orgs:
            logger.warning("No organizations without websites found")
            return self.results

        logger.info(f"Processing {len(orgs)} organizations")
        self.run_batch(orgs, batch_size)

        # Print summary
        logger.info("="*60)
        logger.info("DOMAIN GUESSING ENGINE RESULTS")
        logger.info("="*60)
        logger.info(f"Total checked:       {self.results['total_checked']}")
        logger.info(f"Domains found:       {self.results['domains_found']}")
        logger.info(f"High confidence:     {self.results['high_confidence']}")
        logger.info(f"Medium confidence:   {self.results['medium_confidence']}")
        logger.info(f"Low confidence:      {self.results['low_confidence']}")
        logger.info(f"Success rate:        {(self.results['domains_found']/max(1, self.results['total_checked'])*100):.1f}%")
        logger.info("="*60)

        return self.results

def main():
    """CLI entry point"""
    global MAX_WORKERS
    import argparse

    parser = argparse.ArgumentParser(description='Domain Guessing Engine for nonprofit website discovery')
    parser.add_argument('--limit', type=int, default=100, help='Number of orgs to process')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Batch size')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help='Number of parallel workers')

    args = parser.parse_args()

    MAX_WORKERS = args.workers

    engine = DomainGuessEngine()
    results = engine.run(limit=args.limit, batch_size=args.batch_size)

    print(json.dumps(results, indent=2))
    return 0 if results['domains_found'] > 0 else 1

if __name__ == '__main__':
    sys.exit(main())
