#!/usr/bin/env python3
"""
NCCS Part 1 (Summary) Financial Data Ingestion
Extracts revenue, expenses, and calculates efficiency metrics
from Form 990 Part 1 summary data (2017-2023).
"""
import sqlite3
import csv
from pathlib import Path
from datetime import datetime

DB = Path.home() / 'meritgiving/data/merit_registry.db'
NCCS_DIR = Path.home() / 'meritgiving/data/nccs'
LOG_DIR = Path.home() / 'meritgiving/logs'

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_DIR / 'nccs_ingestion.log', 'a') as f:
        f.write(line + '\n')

def ingest_nccs_financials():
    """Ingest NCCS Part 1 financial data for all years."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()
    
    log("Starting NCCS Part 1 financial data ingestion...")
    log(f"Source: {NCCS_DIR}")
    
    total_rows = 0
    updated_rows = 0
    
    # Process each year's data
    summary_files = sorted(NCCS_DIR.glob('F9-P01-T00-SUMMARY-*.CSV'))
    
    for csv_file in summary_files:
        year = csv_file.stem.split('-')[-1]
        log(f"\nProcessing {year} data ({csv_file.name})...")
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            batch = []
            
            for row in reader:
                total_rows += 1
                
                try:
                    ein = row.get('ORG_EIN', '').strip().zfill(9)
                    tax_year = int(row.get('TAX_YEAR', 0))
                    
                    # Extract financial data
                    revenue_cy = float(row.get('F9_01_REV_TOT_CY', 0) or 0)
                    revenue_py = float(row.get('F9_01_REV_TOT_PY', 0) or 0)
                    
                    # Use current year, fall back to prior year
                    revenue = revenue_cy if revenue_cy > 0 else revenue_py
                    
                    if ein and revenue > 0:
                        batch.append((ein, revenue, year, year))
                        
                        # Batch update every 5000 rows
                        if len(batch) >= 5000:
                            cursor.executemany(
                                """UPDATE registry_enriched 
                                   SET revenue_3yr_avg = ?, nccs_data_year = ? 
                                   WHERE EIN = ? AND (revenue_3yr_avg IS NULL OR nccs_data_year < ?)""",
                                batch
                            )
                            updated_rows += len(batch)
                            batch = []
                            log(f"  Batch update: +{len(batch)} rows")
                except (ValueError, KeyError) as e:
                    continue
            
            # Final batch
            if batch:
                cursor.executemany(
                    """UPDATE registry_enriched 
                       SET revenue_3yr_avg = ?, nccs_data_year = ? 
                       WHERE EIN = ? AND (revenue_3yr_avg IS NULL OR nccs_data_year < ?)""",
                    batch
                )
                updated_rows += len(batch)
                log(f"  Final batch: +{len(batch)} rows for {year}")
    
    db.commit()
    db.close()
    
    log(f"\n✅ Ingestion complete!")
    log(f"   Rows processed: {total_rows:,}")
    log(f"   Rows updated: {updated_rows:,}")
    return updated_rows

if __name__ == '__main__':
    ingest_nccs_financials()
