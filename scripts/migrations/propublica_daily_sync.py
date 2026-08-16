#!/usr/bin/env python3
"""
ProPublica 990 continuous sync — check for new filings daily.

ProPublica publishes new 990s as they're filed. This script:
1. Queries the ProPublica API for recently filed 990s
2. Identifies new EINs in our index
3. Updates filing data in registry_enriched
"""

import sqlite3
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG = Path.home() / 'meritgiving' / 'logs' / 'propublica_sync.log'

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROPUBLICA_API = "https://projects.propublica.org/api/nonprofits"

def sync_propublica():
    """Fetch recent 990s from ProPublica API."""
    db = sqlite3.connect(str(DB))
    c = db.cursor()
    
    logger.info("Starting ProPublica daily sync...")
    
    try:
        # Get last 100 filings (safe API limit)
        url = f"{PROPUBLICA_API}/search.json?query=*"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        filings = data.get('filings', [])
        
        updated = 0
        new_eins = []
        
        for filing in filings[:100]:  # Rate limit: 100 per day
            ein = filing.get('ein')
            org_name = filing.get('name')
            tax_year = filing.get('tax_prd_yr')
            
            if not ein or not tax_year:
                continue
            
            # Check if org is in our registry
            c.execute("SELECT EIN FROM registry_enriched WHERE EIN = ?", (ein,))
            if c.fetchone():
                # Update filing year
                c.execute("""
                    UPDATE registry_enriched 
                    SET latest_tax_year = ?, data_source = 'propublica', updated_at = CURRENT_TIMESTAMP
                    WHERE EIN = ? AND (latest_tax_year IS NULL OR latest_tax_year < ?)
                """, (tax_year, ein, tax_year))
                if c.rowcount > 0:
                    updated += 1
                    new_eins.append(ein)
        
        db.commit()
        logger.info(f"ProPublica sync: {updated} orgs updated with new 990 filings")
        
        if new_eins:
            logger.info(f"New 990s found for EINs: {new_eins[:10]}")  # Log first 10
        
    except requests.Timeout:
        logger.error("ProPublica API timeout")
    except Exception as e:
        logger.error(f"Sync failed: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    sync_propublica()
