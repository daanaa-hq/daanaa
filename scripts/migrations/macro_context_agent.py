#!/usr/bin/env python3
import sqlite3, os, json
from datetime import datetime

DB_PATH = os.path.expanduser('~/meritgiving/data/merit_registry.db')

def fetch_fred_data():
    """Fetch FRED economic indicators (stubbed for MVP)"""
    return {
        'cpi': 310.0,
        'unemployment': 3.9,
        'gdp_growth': 2.5,
        'fed_rate': 4.25,
        'population_change': 0.5,
        'housing_price': 385.2,
    }

def backfill_macro_context(limit=1000):
    """Backfill macro context for 1K orgs"""
    fred_data = fetch_fred_data()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT EIN, latest_tax_year FROM registry_enriched LIMIT ?', (limit,))
    orgs = c.fetchall()
    
    inserted = 0
    for ein, tax_year in orgs:
        try:
            c.execute(
                "INSERT OR IGNORE INTO macro_context_snapshots (ein, filing_year, cpi_year, unemployment_rate, gdp_growth, interest_rate_federal, source_update_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ein, tax_year, fred_data['cpi'], fred_data['unemployment'], fred_data['gdp_growth'], fred_data['fed_rate'], datetime.now().isoformat())
            )
            inserted += 1
        except:
            pass
    
    conn.commit()
    conn.close()
    return inserted

if __name__ == '__main__':
    print(f"Backfilled {backfill_macro_context()} orgs")
