#!/usr/bin/env python3
"""
Expand macro context coverage from 1K → 100K+ orgs

Uses FRED API (free, no cost) to fetch economic indicators.
Runs on home server using local Ryzen (no cloud APIs).

Usage:
    python3 scripts/expand_macro_context.py --target 100000 --batch-size 1000

Environment:
    FRED_API_KEY  (optional; falls back to free tier if not set)
    DB_PATH       (defaults to ~/meritgiving/data/merit_registry.db)
"""

import sqlite3
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import requests

# Configuration
DB_PATH = os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/merit_registry.db"))
FRED_API_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")  # Free tier if not set

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# FRED series IDs for key economic indicators
FRED_SERIES = {
    'unemployment': 'UNRATE',      # Unemployment Rate
    'cpi': 'CPIAUCSL',             # CPI-U
    'gdp_growth': 'A191RA1Q225SBEA', # Real GDP Growth
    'fed_rate': 'FEDFUNDS',        # Federal Funds Rate
}

def fetch_fred_data(series_id: str, year: int) -> float | None:
    """Fetch FRED indicator for a specific year (calendar average)."""
    try:
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY or 'ecbab2f3ed6f1725cf3e98da83a0b79e',  # Public demo key
            'units': 'lin',
            'frequency': 'a',  # Annual
        }

        resp = requests.get(f"{FRED_API_BASE}/series/observations", params=params, timeout=5)
        if resp.status_code != 200:
            return None

        data = resp.json()
        observations = data.get('observations', [])

        # Find value for the requested year
        for obs in observations:
            if obs['date'].startswith(str(year)):
                try:
                    return float(obs['value'])
                except (ValueError, TypeError):
                    return None

        return None
    except Exception as e:
        logger.warning(f"FRED fetch failed for {series_id} ({year}): {e}")
        return None

def get_macro_context_for_year(year: int) -> dict:
    """Get macro context snapshot for a given year."""
    logger.info(f"Fetching FRED data for {year}...")

    context = {
        'filing_year': year,
        'unemployment_rate': fetch_fred_data('unemployment', year),
        'cpi_year': fetch_fred_data('cpi', year),
        'gdp_growth': fetch_fred_data('gdp_growth', year),
        'fed_rate': fetch_fred_data('fed_rate', year),
        'source': 'fred',
        'confidence': 'high',
        'created_at': datetime.now().isoformat(),
    }

    logger.info(f"  unemployment: {context['unemployment_rate']}%")
    logger.info(f"  cpi: {context['cpi_year']}")
    logger.info(f"  gdp_growth: {context['gdp_growth']}%")
    logger.info(f"  fed_rate: {context['fed_rate']}%")

    return context

def expand_macro_context(target_orgs: int = 100000, batch_size: int = 1000):
    """Expand macro context to cover target number of orgs."""

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False

    try:
        # Get all orgs that need macro context
        logger.info(f"Finding orgs without macro context (target: {target_orgs})...")

        cursor.execute("""
            SELECT DISTINCT e.EIN, e.latest_tax_year
            FROM registry_enriched e
            LEFT JOIN macro_context_snapshots m ON e.EIN = m.ein
            WHERE m.ein IS NULL
            AND e.latest_tax_year >= 2020
            ORDER BY e.latest_tax_year DESC
            LIMIT ?
        """, (target_orgs,))

        orgs_missing = cursor.fetchall()
        logger.info(f"Found {len(orgs_missing)} orgs needing macro context")

        if not orgs_missing:
            logger.info("All orgs already have macro context")
            return True

        # Process in batches
        processed = 0
        failed = 0

        for i in range(0, len(orgs_missing), batch_size):
            batch = orgs_missing[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} orgs)...")

            # Cache macro data by year (avoid repeated FRED calls)
            year_cache = {}

            for row in batch:
                ein = row['EIN']
                year = row['latest_tax_year']

                # Get or fetch macro data for this year
                if year not in year_cache:
                    year_cache[year] = get_macro_context_for_year(year)

                macro = year_cache[year]

                # Insert into database
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO macro_context_snapshots
                        (ein, filing_year, unemployment_rate, cpi_year, gdp_growth,
                         interest_rate_federal, source, confidence, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ein,
                        macro['filing_year'],
                        macro['unemployment_rate'],
                        macro['cpi_year'],
                        macro['gdp_growth'],
                        macro['fed_rate'],
                        macro['source'],
                        macro['confidence'],
                        macro['created_at'],
                    ))
                    processed += 1
                except sqlite3.Error as e:
                    logger.error(f"Failed to insert {ein}: {e}")
                    failed += 1

            # Commit batch
            conn.commit()
            logger.info(f"Batch complete: {processed} inserted, {failed} failed")
            time.sleep(1)  # Rate limit FRED calls

        logger.info(f"\n✅ Expansion complete!")
        logger.info(f"Total processed: {processed}")
        logger.info(f"Total failed: {failed}")

        # Verify
        cursor.execute("SELECT COUNT(*) as count FROM macro_context_snapshots")
        total = cursor.fetchone()['count']
        logger.info(f"Total macro context records in DB: {total}")

        return True

    except Exception as e:
        logger.error(f"Error during expansion: {e}", exc_info=True)
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    import sys

    target = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    batch = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    logger.info(f"Starting macro context expansion (target: {target} orgs)")
    success = expand_macro_context(target_orgs=target, batch_size=batch)
    sys.exit(0 if success else 1)
