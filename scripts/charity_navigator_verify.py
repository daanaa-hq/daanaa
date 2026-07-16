#!/usr/bin/env python3
"""
Charity Navigator verification fallback.

When primary discovery finds nothing or has low confidence,
query Charity Navigator API for verified nonprofit data.

Only use when: no link found OR confidence < 90%
"""

import requests
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# CN API (free tier, no key required for basic search)
CN_API_BASE = "https://api.charitynavigator.org/v2"
CN_API_KEY = "YOUR_KEY_HERE"  # Set if rate limiting needed

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


class CharityNavigatorVerifier:
    """Verify and supplement discovered links via Charity Navigator."""

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()

    def search_by_ein(self, ein: str) -> dict | None:
        """Search CN for org by EIN. Returns CN data if found."""
        try:
            url = f"{CN_API_BASE}/organizations"
            params = {
                "ein": ein,
                "limit": 1,
            }
            if CN_API_KEY and CN_API_KEY != "YOUR_KEY_HERE":
                params["apiKey"] = CN_API_KEY

            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                return None

            data = resp.json()
            if not data or len(data) == 0:
                return None

            org = data[0]
            return {
                "name": org.get("charityName"),
                "website": org.get("websiteURL"),
                "donation_url": org.get("donateUrl"),  # CN provides direct donate link
                "ein": org.get("ein"),
                "source": "charity_navigator",
            }

        except Exception as e:
            logger.debug(f"CN lookup failed for EIN {ein}: {e}")
            return None

    def search_by_name(self, name: str, state: str = None) -> dict | None:
        """Search CN for org by name. Returns CN data if found."""
        try:
            url = f"{CN_API_BASE}/organizations"
            params = {
                "search": name,
                "limit": 1,
            }
            if state:
                params["state"] = state
            if CN_API_KEY and CN_API_KEY != "YOUR_KEY_HERE":
                params["apiKey"] = CN_API_KEY

            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                return None

            data = resp.json()
            if not data or len(data) == 0:
                return None

            org = data[0]
            return {
                "name": org.get("charityName"),
                "website": org.get("websiteURL"),
                "donation_url": org.get("donateUrl"),
                "ein": org.get("ein"),
                "source": "charity_navigator",
            }

        except Exception as e:
            logger.debug(f"CN search failed for '{name}': {e}")
            return None

    def verify_link(self, ein: str, org_name: str = None, state: str = None) -> dict | None:
        """
        Fallback verification: search CN for this org's verified donate link.

        Returns: {donate_url, source: 'charity_navigator'} if found
        """
        # Try EIN first (most reliable)
        result = self.search_by_ein(ein)
        if result and result.get("donation_url"):
            return result

        # Try name + state if available
        if org_name:
            result = self.search_by_name(org_name, state)
            if result and result.get("donation_url"):
                return result

        return None


def backfill_missing_links():
    """
    Find orgs with no donate link and try CN verification.
    Updates database with CN-verified links.
    """
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    # Orgs with website but no donate link
    cursor.execute("""
        SELECT EIN, organization_name, STATE
        FROM registry_enriched
        WHERE website IS NOT NULL AND website != ''
        AND donate_url IS NULL
        LIMIT 100
    """)

    orgs = cursor.fetchall()
    verifier = CharityNavigatorVerifier()

    updated = 0
    for ein, name, state in orgs:
        result = verifier.verify_link(ein, name, state)

        if result and result.get("donation_url"):
            cursor.execute(
                "UPDATE registry_enriched SET donate_url = ?, donate_url_status = 'charity_navigator' WHERE EIN = ?",
                (result["donation_url"], ein)
            )
            updated += 1
            logger.info(f"✓ {name} ({ein}): Found via Charity Navigator")

    db.commit()
    db.close()

    logger.info(f"Backfill complete: {updated} links added from Charity Navigator")
    return updated


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
    )

    logger.info("Running Charity Navigator verification backfill...")
    backfill_missing_links()
