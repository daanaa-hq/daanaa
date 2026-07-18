#!/usr/bin/env python3
"""
Comprehensive website discovery system.

Extracts from nonprofit websites:
1. Donation links + button text + button location
2. Volunteer opportunity links
3. GitHub repositories
4. skills.sh profiles
5. Contact information

This is an active discovery system that searches websites, not just
cached ProPublica data.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import re
import json
import threading
import time
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crawler etiquette (2026-07-18 best-practices pass, matching
# donation_link_pipeline.py's existing standard):
#   - Honest, identified User-Agent with a contact URL — never impersonate a
#     browser. Site owners can see who we are and reach us.
#   - robots.txt respected per-host (cached; fails open on fetch errors so a
#     broken robots.txt doesn't silo an org out of discovery).
#   - Per-domain minimum request spacing so no single nonprofit's site gets
#     hammered even when many of its pages are crawled in one batch.
UA = ("Mozilla/5.0 (compatible; DaanaaBot/1.0; "
      "+https://daanaa.org/about) nonprofit-directory-discovery")

_robots_cache: dict = {}
_robots_lock = threading.Lock()
_domain_last: dict = {}
_domain_lock = threading.Lock()
_DOMAIN_MIN_SPACING_S = 2.0


def _can_fetch(url: str) -> bool:
    """False if robots.txt disallows this URL for our UA. Fails open."""
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        with _robots_lock:
            if base not in _robots_cache:
                rp = RobotFileParser()
                rp.set_url(base + "/robots.txt")
                try:
                    rp.read()
                except Exception:
                    pass
                _robots_cache[base] = rp
        return _robots_cache[base].can_fetch(UA, url)
    except Exception:
        return True


def _domain_pause(url: str) -> None:
    """Sleep just enough to keep >=2s between requests to the same host."""
    try:
        host = urlparse(url).netloc
    except Exception:
        return
    with _domain_lock:
        last = _domain_last.get(host, 0.0)
        now = time.time()
        wait = _DOMAIN_MIN_SPACING_S - (now - last)
        _domain_last[host] = max(now, last + _DOMAIN_MIN_SPACING_S)
    if wait > 0:
        time.sleep(wait)


class WebsiteDiscovery:
    """Discover nonprofit website features and links."""

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.headers = {'User-Agent': UA}

    def fetch_website(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse website (robots-respecting, domain-rate-limited)."""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            if not _can_fetch(url):
                logger.info(f"robots.txt disallows {url} — skipping")
                return None
            _domain_pause(url)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def find_donate_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Find all donation-related links and buttons."""
        donate_patterns = [
            r'donate', r'give', r'support', r'sponsor', r'contribution',
            r'fund', r'help\s+us', r'support\s+us', r'make\s+a\s+gift'
        ]

        donate_links = []
        pattern = '|'.join(donate_patterns)
        regex = re.compile(pattern, re.IGNORECASE)

        # Find all links
        for link in soup.find_all('a', href=True):
            text = link.get_text().strip()
            href = link.get('href', '')

            # Check if link text or href matches donate patterns
            if regex.search(text) or regex.search(href):
                full_url = urljoin(base_url, href)

                donate_links.append({
                    'url': full_url,
                    'text': text,
                    'location': 'unknown',  # Can be enhanced to detect header/footer
                    'button_style': link.get('class', []),
                    'confidence': 0.95 if text else 0.7
                })

        # Find PayPal/Stripe buttons
        for script in soup.find_all('script'):
            if script.string and ('paypal' in script.string.lower() or 'stripe' in script.string.lower()):
                donate_links.append({
                    'url': 'payment_processor_detected',
                    'text': 'Payment processor embedded',
                    'type': 'embedded_button',
                    'confidence': 0.85
                })

        return donate_links

    def find_volunteer_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Find volunteer/get-involved opportunities."""
        volunteer_patterns = [
            r'volunteer', r'get\s+involved', r'join\s+us', r'become\s+a\s+volunteer',
            r'help\s+us', r'serve', r'intern', r'opportunities'
        ]

        volunteer_links = []
        pattern = '|'.join(volunteer_patterns)
        regex = re.compile(pattern, re.IGNORECASE)

        for link in soup.find_all('a', href=True):
            text = link.get_text().strip()
            href = link.get('href', '')

            if regex.search(text) or regex.search(href):
                full_url = urljoin(base_url, href)
                volunteer_links.append({
                    'url': full_url,
                    'text': text,
                    'confidence': 0.9 if text else 0.6
                })

        return volunteer_links

    def find_github_repos(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Find GitHub repository links."""
        github_links = []

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'github.com' in href:
                github_links.append({
                    'url': href,
                    'text': link.get_text().strip(),
                    'confidence': 1.0
                })

        return github_links

    def find_skills_profiles(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Find skills.sh or volunteer platform profiles."""
        skills_patterns = [
            'skills.sh',
            'idealist.org',
            'volunteermatch.org',
            'catchafire.org',
            'handson.org'
        ]

        skills_links = []

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            for platform in skills_patterns:
                if platform in href:
                    skills_links.append({
                        'platform': platform,
                        'url': href,
                        'text': link.get_text().strip()
                    })

        return skills_links

    def discover_all(self, website_url: str) -> Dict:
        """Comprehensive discovery: donation, volunteer, GitHub, skills."""
        base_url = website_url if website_url.startswith(('http://', 'https://')) else f'https://{website_url}'

        soup = self.fetch_website(base_url)
        if not soup:
            return {'error': 'Failed to fetch website'}

        return {
            'website_url': base_url,
            'donation_links': self.find_donate_links(soup, base_url),
            'volunteer_links': self.find_volunteer_links(soup, base_url),
            'github_repos': self.find_github_repos(soup, base_url),
            'skills_profiles': self.find_skills_profiles(soup, base_url),
            'discovered_at': str(__import__('datetime').datetime.now())
        }


def test_discovery():
    """Test discovery on known organizations."""
    discovery = WebsiteDiscovery()

    # Test on Indus Arts Council
    print("Testing Indus Arts Council...")
    print("=" * 60)

    result = discovery.discover_all('https://indusartscouncil.org/')

    print(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    test_discovery()
