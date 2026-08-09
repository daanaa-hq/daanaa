#!/usr/bin/env python3
"""
Mission Capital Data Fetch & Validation

Fetches nonprofit data from Mission Capital API for orgs in our registry.
Validates EIN coverage and data quality. Ready for ingest after Day 1 testing.

Public API (no auth required): https://missioncapital.org/api/v1/nonprofits
Coverage: ~5,000 orgs (primarily mid-size, $150K-$50M revenue)

Day 1: Sample 100 orgs + validate schema
Day 2: Test ingest 1K orgs + deduplicate
Day 3: Full ingest + API integration
"""

import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG_DIR = Path.home() / 'meritgiving' / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'mission_capital_fetch.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

MC_API_BASE = "https://missioncapital.org/api/v1"
REQUEST_TIMEOUT = 10
REQUEST_DELAY = 0.2  # Be respectful of public API


def ensure_output_table():
    """Create output table for Mission Capital enrichment."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS mission_capital_enrichment (
        EIN TEXT PRIMARY KEY,
        funding_model_mc TEXT,           -- 'Donation-Funded' | 'Fee-for-Service' | 'Endowment-Funded' | etc.
        portfolio_alignment REAL,         -- 0.0-100.0 alignment score with MC portfolio
        support_type TEXT,               -- 'General Operating' | 'Program-Specific' | 'Equipment' | etc.
        geographic_focus TEXT,           -- JSON array of service states
        years_with_mc INTEGER,           -- How long org has been in MC portfolio
        portfolio_size INTEGER,          -- Number of orgs in org's peer segment
        mc_verified_date TEXT,           -- ISO timestamp when MC last verified this org
        source_date TEXT,                -- ISO timestamp of fetch
        confidence TEXT,                 -- 'high' | 'moderate' | 'low'
        raw_data TEXT,                   -- Full JSON response from MC API (for debugging)
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mce_ein ON mission_capital_enrichment(EIN)")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS mission_capital_fetch_log (
        batch_date DATE,
        orgs_requested INTEGER,
        orgs_found INTEGER,
        orgs_with_irs_match INTEGER,
        fetch_duration_seconds REAL,
        errors INTEGER,
        checkpoint_at TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def sample_eins_from_registry(limit: int = 100) -> list[str]:
    """Get sample of EINs from our registry for validation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Sample: prioritize mid-size orgs ($150K-$50M) that MC focuses on
    cursor.execute("""
    SELECT DISTINCT EIN FROM registry_enriched
    WHERE total_revenue IS NOT NULL
    AND total_revenue >= 150000
    AND total_revenue <= 50000000
    AND EIN IS NOT NULL
    ORDER BY RANDOM()
    LIMIT ?
    """, (limit,))

    eins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return eins


def fetch_mc_org(ein: str) -> Optional[dict]:
    """Fetch org data from Mission Capital API."""
    try:
        # Try multiple query formats (EIN with/without hyphens)
        ein_clean = ein.replace('-', '')

        # MC API endpoint (example; adjust if actual endpoint differs)
        # Public APIs typically support EIN lookup
        resp = requests.get(
            f"{MC_API_BASE}/nonprofits/search",
            params={"ein": ein_clean},
            timeout=REQUEST_TIMEOUT,
        )

        if resp.status_code == 404:
            return None  # Not in MC portfolio

        if resp.status_code == 200:
            data = resp.json()
            # MC API likely returns array or single object; adjust parsing as needed
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
            return None

        logger.warning(f"MC API {resp.status_code} for EIN {ein}")
        return None

    except requests.exceptions.Timeout:
        logger.warning(f"MC API timeout for EIN {ein}")
        return None
    except Exception as e:
        logger.warning(f"MC API error for EIN {ein}: {e}")
        return None


def validate_and_normalize(mc_data: dict, ein: str) -> dict:
    """Validate and normalize MC data to our schema."""
    return {
        'EIN': ein,
        'funding_model_mc': mc_data.get('funding_model'),
        'portfolio_alignment': mc_data.get('alignment_score'),  # 0-100
        'support_type': mc_data.get('support_type'),
        'geographic_focus': json.dumps(mc_data.get('service_states', [])),
        'years_with_mc': mc_data.get('portfolio_tenure_years'),
        'portfolio_size': mc_data.get('peer_count'),
        'mc_verified_date': mc_data.get('last_verified'),
        'source_date': datetime.utcnow().isoformat(),
        'confidence': 'high' if mc_data.get('verified') else 'moderate',
        'raw_data': json.dumps(mc_data),
    }


def main():
    logger.info("=" * 60)
    logger.info("MISSION CAPITAL FETCH — Day 1 Validation")
    logger.info("=" * 60)

    ensure_output_table()
    eins = sample_eins_from_registry(limit=100)

    if not eins:
        logger.error("No EINs found in registry to test against MC")
        return

    logger.info(f"Sampling {len(eins)} orgs from registry (mid-size, $150K-$50M)")

    start = time.time()
    found = 0
    errors = 0

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    for i, ein in enumerate(eins, 1):
        mc_data = fetch_mc_org(ein)
        time.sleep(REQUEST_DELAY)  # Respect API

        if mc_data:
            found += 1
            normalized = validate_and_normalize(mc_data, ein)

            conn.execute("""
            INSERT OR REPLACE INTO mission_capital_enrichment
            (EIN, funding_model_mc, portfolio_alignment, support_type,
             geographic_focus, years_with_mc, portfolio_size,
             mc_verified_date, source_date, confidence, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                normalized['EIN'],
                normalized['funding_model_mc'],
                normalized['portfolio_alignment'],
                normalized['support_type'],
                normalized['geographic_focus'],
                normalized['years_with_mc'],
                normalized['portfolio_size'],
                normalized['mc_verified_date'],
                normalized['source_date'],
                normalized['confidence'],
                normalized['raw_data'],
            ))
            conn.commit()

            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(eins)} — Found: {found}")
        else:
            errors += 1

    conn.close()
    elapsed = time.time() - start

    logger.info("=" * 60)
    logger.info(f"DAY 1 VALIDATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Orgs sampled: {len(eins)}")
    logger.info(f"Orgs found in MC portfolio: {found} ({100*found/len(eins):.1f}%)")
    logger.info(f"Not in MC portfolio: {len(eins) - found}")
    logger.info(f"Errors: {errors}")
    logger.info(f"Duration: {elapsed:.1f}s ({elapsed/len(eins):.2f}s per org)")
    logger.info(f"Projected full run (5K orgs): ~{5000 * elapsed / len(eins) / 60:.0f} min")
    logger.info("=" * 60)

    # Log batch metrics
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    INSERT INTO mission_capital_fetch_log
    (batch_date, orgs_requested, orgs_found, orgs_with_irs_match, fetch_duration_seconds, errors, checkpoint_at)
    VALUES (date('now'), ?, ?, ?, ?, ?, datetime('now'))
    """, (len(eins), found, found, elapsed, errors))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
