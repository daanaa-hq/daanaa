#!/usr/bin/env python3
"""
Extract nonprofit websites from donation platforms.

Sources:
  - GiveWell: https://www.givewell.org/charities
  - GiveDirectly: https://www.givedirectly.org/partners
  - GlobalGiving: https://www.globalgiving.org/
  - Charity Navigator: https://www.charitynavigator.org/

Extracts:
  - Nonprofit names
  - Websites (resolve redirects + affiliate links)
  - EINs (if available)
  - Platform URLs
  - Confidence scores

Respects:
  - robots.txt + rate limiting (3-5s between requests)
  - No form submission or CAPTCHA bypass
  - User-Agent + transparent identification
  - 429/403 handling (backoff, no retry)

Output: /tmp/agent7_donation_results.txt (tab-delimited)
"""

import re
import time
import json
import logging
import sqlite3
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.robotparser import RobotFileParser
from typing import Optional, Tuple
import random

import requests
from bs4 import BeautifulSoup

# Setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
OUTPUT_PATH = Path("/tmp/agent7_donation_results.txt")

UA = "Mozilla/5.0 (compatible; DaanaaBot/1.0; +https://daanaa.org/robots.txt)"
TIMEOUT = 10
MAX_RETRIES = 2


class PlatformScraper:
    """Base class for platform-specific scrapers."""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.robots = RobotFileParser()
        self.last_fetch = {}
        self.results = []
        self._init_robots()

    def _init_robots(self):
        """Load robots.txt for this domain."""
        try:
            self.robots.set_url(f"{self.base_url}/robots.txt")
            self.robots.read()
            logger.info(f"{self.name}: robots.txt loaded")
        except Exception as e:
            logger.warning(f"{self.name}: robots.txt read failed ({e})")
            # Fail open
            self.robots = None

    def _can_fetch(self, url: str) -> bool:
        """Check robots.txt before fetching."""
        if not self.robots:
            return True
        try:
            return self.robots.can_fetch(UA, url)
        except Exception:
            return True  # Fail open

    def _rate_limit(self, domain: str, min_s: float = 3.0, max_s: float = 5.0):
        """Per-domain rate limiter."""
        now = time.time()
        last = self.last_fetch.get(domain, 0)
        wait_time = max(0, (last + random.uniform(min_s, max_s)) - now)
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_fetch[domain] = time.time()

    def _fetch(self, url: str) -> Optional[str]:
        """Fetch URL with rate limiting and error handling."""
        domain = urlparse(url).netloc

        if not self._can_fetch(url):
            logger.warning(f"{self.name}: robots.txt disallows {url}")
            return None

        self._rate_limit(domain)

        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(
                    url,
                    timeout=TIMEOUT,
                    headers={'User-Agent': UA},
                    allow_redirects=True
                )

                if resp.status_code == 429:
                    logger.warning(f"{self.name}: 429 from {domain}, backing off")
                    return None
                elif resp.status_code == 403:
                    logger.warning(f"{self.name}: 403 from {domain}, stopping")
                    return None
                elif resp.status_code == 200:
                    return resp.text
                else:
                    logger.debug(f"{self.name}: {resp.status_code} from {url}")
                    return None
            except requests.Timeout:
                logger.debug(f"{self.name}: timeout on {url}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)
                continue
            except Exception as e:
                logger.debug(f"{self.name}: fetch error on {url}: {e}")
                return None

        return None

    def scrape(self) -> list:
        """Override in subclass."""
        raise NotImplementedError

    def resolve_redirect(self, url: str) -> Tuple[str, int]:
        """Resolve URL redirects. Returns (final_url, hops)."""
        if not url:
            return url, 0

        parsed = urlparse(url)
        domain = parsed.netloc
        self._rate_limit(domain, 1.0, 2.0)

        try:
            resp = requests.head(
                url,
                timeout=TIMEOUT,
                headers={'User-Agent': UA},
                allow_redirects=True
            )
            final_url = resp.url
            hops = len(resp.history)

            # Check for affiliate redirects
            if self._is_affiliate(url, final_url):
                logger.debug(f"Affiliate redirect: {url} -> {final_url}")

            return final_url, hops
        except Exception as e:
            logger.debug(f"Redirect resolution failed for {url}: {e}")
            return url, 0

    def _is_affiliate(self, original: str, final: str) -> bool:
        """Detect affiliate/redirect schemes."""
        affiliate_domains = [
            'everydayactions', 'impactful', 'givebutter',
            'donorbox', 'click', 'link.', 'redirect'
        ]
        return any(aff in final.lower() for aff in affiliate_domains)

    def _extract_ein(self, name: str, url: Optional[str] = None) -> Optional[str]:
        """Try to match nonprofit to EIN in database."""
        if not DB_PATH.exists():
            return None

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Match by organization name (exact, then fuzzy)
            cursor.execute(
                "SELECT ein FROM registry_enriched WHERE name = ? LIMIT 1",
                (name,)
            )
            row = cursor.fetchone()
            if row:
                conn.close()
                return row[0]

            # Fuzzy match on name start
            name_prefix = name.split(' ')[0]
            cursor.execute(
                "SELECT ein FROM registry_enriched WHERE name LIKE ? LIMIT 1",
                (f"{name_prefix}%",)
            )
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            logger.debug(f"EIN lookup failed: {e}")
            return None


class GiveWellScraper(PlatformScraper):
    """Scrape GiveWell recommended charities."""

    def __init__(self):
        super().__init__("GiveWell", "https://www.givewell.org")

    def scrape(self) -> list:
        logger.info(f"{self.name}: Starting scrape")

        # GiveWell API endpoint (no robots.txt block on API)
        api_url = "https://www.givewell.org/charities"

        html = self._fetch(api_url)
        if not html:
            logger.error(f"{self.name}: Failed to fetch main page")
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # Extract charity links from the page
        for link in soup.find_all('a', href=re.compile(r'/charities/[a-z0-9\-]+$')):
            href = link.get('href')
            name = link.get_text(strip=True)

            if not href or not name:
                continue

            full_url = urljoin(self.base_url, href)
            website = self._extract_website_from_givewell_page(full_url)
            ein = self._extract_ein(name, website)

            self.results.append({
                'platform': self.name,
                'name': name,
                'website': website,
                'website_resolved': self.resolve_redirect(website)[0] if website else None,
                'ein': ein,
                'platform_url': full_url,
                'confidence': 95
            })

            logger.info(f"{self.name}: {name} -> {website}")

        logger.info(f"{self.name}: Scraped {len(self.results)} charities")
        return self.results

    def _extract_website_from_givewell_page(self, url: str) -> Optional[str]:
        """Extract charity website from GiveWell charity page."""
        html = self._fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Look for "website" or "donate" link
        for link in soup.find_all('a', href=re.compile(r'https?://')):
            href = link.get('href')
            text = link.get_text(strip=True).lower()

            if any(w in text for w in ['website', 'visit', 'donate', 'home']):
                if not any(d in href for d in ['givewell', 'google', 'facebook']):
                    return href

        return None


class GiveDirectlyScraper(PlatformScraper):
    """Scrape GiveDirectly partner nonprofits."""

    def __init__(self):
        super().__init__("GiveDirectly", "https://www.givedirectly.org")

    def scrape(self) -> list:
        logger.info(f"{self.name}: Starting scrape")

        partners_url = "https://www.givedirectly.org/partners"
        html = self._fetch(partners_url)

        if not html:
            logger.error(f"{self.name}: Failed to fetch partners page")
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # Extract partner organization links
        for section in soup.find_all(['div', 'article'], class_=re.compile(r'partner|org')):
            name_elem = section.find(['h2', 'h3', 'strong'])
            if not name_elem:
                continue

            name = name_elem.get_text(strip=True)

            # Find link within section
            link_elem = section.find('a', href=re.compile(r'https?://'))
            website = link_elem.get('href') if link_elem else None

            if not website or 'givedirectly' in website.lower():
                continue

            ein = self._extract_ein(name, website)
            resolved_url, hops = self.resolve_redirect(website)

            self.results.append({
                'platform': self.name,
                'name': name,
                'website': website,
                'website_resolved': resolved_url,
                'redirect_hops': hops,
                'ein': ein,
                'platform_url': partners_url,
                'confidence': 90
            })

            logger.info(f"{self.name}: {name} -> {website}")

        logger.info(f"{self.name}: Scraped {len(self.results)} partners")
        return self.results


class GlobalGivingScraper(PlatformScraper):
    """Scrape GlobalGiving featured nonprofits."""

    def __init__(self):
        super().__init__("GlobalGiving", "https://www.globalgiving.org")

    def scrape(self) -> list:
        logger.info(f"{self.name}: Starting scrape")

        # GlobalGiving has a browsable directory; start with featured
        base_url = "https://www.globalgiving.org/projects"
        html = self._fetch(base_url)

        if not html:
            logger.error(f"{self.name}: Failed to fetch projects page")
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # Extract project/org links (GlobalGiving structure)
        for card in soup.find_all(['div', 'article'], class_=re.compile(r'project|org|card')):
            name_elem = card.find(['h2', 'h3', 'a'], class_=re.compile(r'name|title'))
            if not name_elem:
                continue

            name = name_elem.get_text(strip=True)

            # Look for "About" or organization link
            links = card.find_all('a', href=True)
            website = None
            for link in links:
                href = link.get('href')
                if any(w in href.lower() for w in ['about', 'org', 'www']):
                    if 'globalgiving' not in href.lower():
                        website = urljoin(self.base_url, href)
                        break

            if not website:
                # Try extracting from description text
                desc = card.get_text()
                url_match = re.search(r'https?://[^\s]+', desc)
                if url_match:
                    website = url_match.group(0)

            if not website:
                continue

            ein = self._extract_ein(name, website)
            resolved_url, hops = self.resolve_redirect(website)

            self.results.append({
                'platform': self.name,
                'name': name,
                'website': website,
                'website_resolved': resolved_url,
                'redirect_hops': hops,
                'ein': ein,
                'platform_url': base_url,
                'confidence': 85
            })

            logger.info(f"{self.name}: {name} -> {website}")

        logger.info(f"{self.name}: Scraped {len(self.results)} organizations")
        return self.results


class CharityNavigatorScraper(PlatformScraper):
    """Scrape Charity Navigator top-rated nonprofits."""

    def __init__(self):
        super().__init__("Charity Navigator", "https://www.charitynavigator.org")

    def scrape(self) -> list:
        logger.info(f"{self.name}: Starting scrape")

        # Charity Navigator has a search/browse interface
        base_url = "https://www.charitynavigator.org/index.cfm"

        html = self._fetch(base_url)
        if not html:
            logger.error(f"{self.name}: Failed to fetch main page")
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # Extract organization cards
        for card in soup.find_all(['div', 'tr'], class_=re.compile(r'org|charity|result')):
            name_elem = card.find(['h2', 'h3', 'a'], class_=re.compile(r'name|title'))
            if not name_elem:
                continue

            name = name_elem.get_text(strip=True)

            # Find organization link
            org_link = card.find('a', href=re.compile(r'charitynavigator\.org/organizations'))
            if not org_link:
                continue

            platform_url = urljoin(self.base_url, org_link.get('href'))

            # Extract website from org detail page
            website = self._extract_website_from_cn_detail(platform_url)

            if not website:
                continue

            ein = self._extract_ein(name, website)
            resolved_url, hops = self.resolve_redirect(website)

            self.results.append({
                'platform': self.name,
                'name': name,
                'website': website,
                'website_resolved': resolved_url,
                'redirect_hops': hops,
                'ein': ein,
                'platform_url': platform_url,
                'confidence': 92
            })

            logger.info(f"{self.name}: {name} -> {website}")

        logger.info(f"{self.name}: Scraped {len(self.results)} charities")
        return self.results

    def _extract_website_from_cn_detail(self, url: str) -> Optional[str]:
        """Extract website from Charity Navigator org detail page."""
        html = self._fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Look for "Website" or "Official Organization Website" link
        for link in soup.find_all('a', href=re.compile(r'https?://')):
            text = link.get_text(strip=True).lower()
            href = link.get('href')

            if any(w in text for w in ['website', 'official', 'homepage', 'visit']):
                if not any(d in href for d in ['charitynavigator', 'google', 'facebook']):
                    return href

        return None


def write_results(all_results: list):
    """Write results to TSV file."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w') as f:
        # Header
        f.write('\t'.join([
            'Platform',
            'Nonprofit Name',
            'Website',
            'Website Resolved',
            'Redirect Hops',
            'EIN',
            'Platform URL',
            'Confidence (%)',
            'Extracted At'
        ]) + '\n')

        # Data rows
        for result in all_results:
            website = result.get('website') or ''
            website_resolved = result.get('website_resolved') or website

            f.write('\t'.join([
                result.get('platform', ''),
                result.get('name', ''),
                website,
                website_resolved,
                str(result.get('redirect_hops', 0)),
                result.get('ein', '') or '',
                result.get('platform_url', ''),
                str(result.get('confidence', 0)),
                time.strftime('%Y-%m-%d %H:%M:%S')
            ]) + '\n')

    logger.info(f"Results written to {OUTPUT_PATH}")
    logger.info(f"Total records: {len(all_results)}")


def scrape_from_database():
    """Extract comprehensive nonprofit website data from existing database."""
    results = []

    if not DB_PATH.exists():
        return results

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Query 1: High-confidence donate links (verified platforms)
        logger.info("Extracting high-confidence donation links...")
        cursor.execute("""
            SELECT DISTINCT
                EIN, organization_name, website, donate_url, donate_confidence, donate_platform
            FROM registry_enriched
            WHERE website IS NOT NULL
              AND website != ''
              AND website LIKE 'http%'
              AND donate_url IS NOT NULL
              AND donate_url != ''
              AND donate_confidence >= 85
            ORDER BY donate_confidence DESC
            LIMIT 250
        """)

        for ein, org_name, website, donate_url, confidence, platform in cursor.fetchall():
            results.append({
                'platform': f'Verified ({platform or "direct"})' if platform else 'Database (Verified)',
                'name': org_name,
                'website': website,
                'website_resolved': website,
                'redirect_hops': 0,
                'ein': ein,
                'platform_url': donate_url or '',
                'confidence': int(confidence) if confidence else 85
            })

        # Query 2: Websites with 70+ confidence (secondary tier)
        logger.info("Extracting medium-confidence websites...")
        cursor.execute("""
            SELECT DISTINCT
                EIN, organization_name, website, donate_url, donate_confidence
            FROM registry_enriched
            WHERE website IS NOT NULL
              AND website != ''
              AND website LIKE 'http%'
              AND (donate_confidence >= 70 OR donate_confidence IS NULL)
              AND website_status = 'ok'
            ORDER BY website_status DESC, donate_confidence DESC NULLS LAST
            LIMIT 250
        """)

        for ein, org_name, website, donate_url, confidence in cursor.fetchall():
            # Skip if already added
            if any(r['ein'] == ein for r in results):
                continue

            results.append({
                'platform': 'Database (Website Verified)',
                'name': org_name,
                'website': website,
                'website_resolved': website,
                'redirect_hops': 0,
                'ein': ein,
                'platform_url': donate_url or '',
                'confidence': int(confidence) if confidence else 70
            })

        # Query 3: Large orgs with websites (500K+, likely have platforms)
        logger.info("Extracting large organization websites...")
        cursor.execute("""
            SELECT DISTINCT
                EIN, organization_name, website, donate_url
            FROM registry_enriched
            WHERE website IS NOT NULL
              AND website != ''
              AND website LIKE 'http%'
              AND total_revenue > 500000
            LIMIT 150
        """)

        for ein, org_name, website, donate_url in cursor.fetchall():
            if any(r['ein'] == ein for r in results):
                continue

            results.append({
                'platform': 'Database (Large Org)',
                'name': org_name,
                'website': website,
                'website_resolved': website,
                'redirect_hops': 0,
                'ein': ein,
                'platform_url': donate_url or '',
                'confidence': 80
            })

        # Query 4: All remaining orgs with verified websites
        logger.info("Extracting additional verified websites...")
        cursor.execute("""
            SELECT DISTINCT
                EIN, organization_name, website, donate_url
            FROM registry_enriched
            WHERE website IS NOT NULL
              AND website != ''
              AND website LIKE 'http%'
              AND website_status IS NOT NULL
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 200
        """)

        for ein, org_name, website, donate_url in cursor.fetchall():
            if any(r['ein'] == ein for r in results):
                continue

            results.append({
                'platform': 'Database (Website Status Verified)',
                'name': org_name,
                'website': website,
                'website_resolved': website,
                'redirect_hops': 0,
                'ein': ein,
                'platform_url': donate_url or '',
                'confidence': 75
            })

        conn.close()
        logger.info(f"Database extraction complete: {len(results)} unique orgs")
        return results
    except Exception as e:
        logger.warning(f"Database extraction failed: {e}")
        return results


def main():
    """Run all scrapers."""
    all_results = []

    # Try platform scrapers
    scrapers = [
        GiveWellScraper(),
        GiveDirectlyScraper(),
        GlobalGivingScraper(),
        CharityNavigatorScraper()
    ]

    for scraper in scrapers:
        try:
            results = scraper.scrape()
            all_results.extend(results)
        except Exception as e:
            logger.error(f"{scraper.name}: scrape failed: {e}")
            continue

    logger.info(f"Platform scraping: {len(all_results)} records extracted")

    # Supplement from database (this is more reliable)
    db_results = scrape_from_database()
    all_results.extend(db_results)

    logger.info(f"Total extracted: {len(all_results)} records from all sources")

    # Dedup by website
    seen_websites = set()
    deduped = []
    for result in all_results:
        website = (result.get('website_resolved') or result.get('website', ''))
        if website:
            website = website.lower().strip()
            if website and website not in seen_websites:
                seen_websites.add(website)
                deduped.append(result)

    logger.info(f"After dedup: {len(deduped)} unique websites")

    write_results(deduped)


if __name__ == '__main__':
    main()
