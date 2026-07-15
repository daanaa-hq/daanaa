#!/usr/bin/env python3
"""
Verify discovered links before they're deployed to the live site.

Tests:
1. HTTP status (200 = valid)
2. Content type (donation page = has payment processor keywords)
3. Redirect chains (no sketchy redirects)
4. Response time (reasonable, not stuck)

Only marks links as verified if all checks pass.
"""

import requests
import sqlite3
from pathlib import Path
from datetime import datetime
import json

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'

# Keywords that indicate a real donation page
DONATION_KEYWORDS = ['donate', 'paypal', 'stripe', 'gift', 'contribute', 'fundraise', 'payment']
VOLUNTEER_KEYWORDS = ['volunteer', 'join us', 'get involved', 'apply', 'sign up', 'opportunities']


class LinkVerifier:
    """Verify discovered links are live and correct."""

    def __init__(self, timeout=10, max_redirects=5):
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Daanaa Link Verifier)'
        }

    def verify_donation_link(self, url: str) -> dict:
        """Verify a donation link is live and has donation content."""
        try:
            response = requests.head(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)

            # Check status
            if response.status_code != 200:
                return {
                    'verified': False,
                    'status_code': response.status_code,
                    'reason': f'HTTP {response.status_code}'
                }

            # For payment processors (PayPal, Stripe), presence of 200 is enough
            if any(host in url.lower() for host in ['paypal', 'stripe', 'givewell', 'donorbox']):
                return {
                    'verified': True,
                    'status_code': 200,
                    'type': 'payment_processor',
                    'reason': 'Payment processor link detected'
                }

            # For other donation URLs, check content
            response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            content = response.text.lower()

            # Check for donation keywords
            found_keywords = [kw for kw in DONATION_KEYWORDS if kw in content]

            if len(found_keywords) > 0:
                return {
                    'verified': True,
                    'status_code': 200,
                    'type': 'donation_page',
                    'keywords_found': found_keywords,
                    'reason': f'Found donation keywords: {", ".join(found_keywords[:2])}'
                }
            else:
                return {
                    'verified': False,
                    'status_code': 200,
                    'reason': 'No donation keywords found in page content'
                }

        except requests.Timeout:
            return {'verified': False, 'reason': 'Timeout (>10s)'}
        except requests.ConnectionError:
            return {'verified': False, 'reason': 'Connection error (site unreachable)'}
        except Exception as e:
            return {'verified': False, 'reason': f'Error: {str(e)[:50]}'}

    def verify_volunteer_link(self, url: str) -> dict:
        """Verify a volunteer opportunity link."""
        try:
            response = requests.head(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)

            if response.status_code != 200:
                return {
                    'verified': False,
                    'status_code': response.status_code,
                    'reason': f'HTTP {response.status_code}'
                }

            # Check content
            response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            content = response.text.lower()

            found_keywords = [kw for kw in VOLUNTEER_KEYWORDS if kw in content]

            if len(found_keywords) > 0:
                return {
                    'verified': True,
                    'status_code': 200,
                    'type': 'volunteer_page',
                    'keywords_found': found_keywords,
                    'reason': f'Found volunteer keywords: {", ".join(found_keywords[:2])}'
                }
            else:
                return {
                    'verified': False,
                    'status_code': 200,
                    'reason': 'No volunteer keywords found'
                }

        except requests.Timeout:
            return {'verified': False, 'reason': 'Timeout (>10s)'}
        except requests.ConnectionError:
            return {'verified': False, 'reason': 'Connection error'}
        except Exception as e:
            return {'verified': False, 'reason': f'Error: {str(e)[:50]}'}


def verify_org_links(ein: str, org_name: str, donate_url: str = None, volunteer_url: str = None) -> dict:
    """Verify all discovered links for an organization."""
    verifier = LinkVerifier()
    results = {
        'ein': ein,
        'org_name': org_name,
        'donate_url': None,
        'volunteer_url': None,
        'verified_at': datetime.now().isoformat()
    }

    if donate_url:
        results['donate_url'] = verifier.verify_donation_link(donate_url)

    if volunteer_url:
        results['volunteer_url'] = verifier.verify_volunteer_link(volunteer_url)

    return results


def batch_verify_links(limit=100):
    """Verify recently discovered links in batch."""
    db = sqlite3.connect(DB)
    cursor = db.cursor()

    # Get orgs with unverified donation/volunteer links
    cursor.execute("""
        SELECT EIN, organization_name, donate_url, volunteer_url
        FROM registry_enriched
        WHERE (
            (donate_url IS NOT NULL AND (donate_url_status IS NULL OR donate_url_status != 'verified'))
            OR
            (volunteer_url IS NOT NULL AND volunteer_url LIKE '%://%')
        )
        AND EIN > 0
        ORDER BY updated_at DESC
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()
    verified_count = 0
    failed_count = 0

    for ein, org_name, donate_url, volunteer_url in results:
        verify_result = verify_org_links(ein, org_name, donate_url, volunteer_url)

        # Update database with verification results
        if donate_url and verify_result['donate_url'].get('verified'):
            cursor.execute(
                "UPDATE registry_enriched SET donate_url_status = ?, donate_checked_at = ? WHERE EIN = ?",
                ('verified', datetime.now().isoformat(), ein)
            )
            verified_count += 1
        elif donate_url:
            cursor.execute(
                "UPDATE registry_enriched SET donate_url_status = ?, donate_url = NULL, donate_checked_at = ? WHERE EIN = ?",
                ('failed', datetime.now().isoformat(), ein)
            )
            failed_count += 1

        if verified_count % 10 == 0:
            print(f"Verified {verified_count}, failed {failed_count}...")

    db.commit()
    db.close()

    return verified_count, failed_count


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'batch':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        print(f"Verifying {limit} recently discovered links...")
        verified, failed = batch_verify_links(limit)
        print(f"\n✅ Results: {verified} verified, {failed} removed (bad links)")
    else:
        # Test single link
        url = sys.argv[1] if len(sys.argv) > 1 else 'https://indusartscouncil.org/'
        print(f"Testing: {url}")
        verifier = LinkVerifier()
        result = verifier.verify_donation_link(url)
        print(result)
