#!/usr/bin/env python3
"""
Ingest NCCS Part X (Balance Sheet) data into registry_enriched.

Reads F9-P10-T00-BALANCE-SHEET-YYYY.CSV files and extracts:
- Total assets (end of year)
- Total liabilities (end of year)
- Net assets for benefit of members (end of year)

Filters: Last 5 years (2019-2024) + ACTIVE deductibility_status only.
"""

import sqlite3
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuration
DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")
NCCS_DATA_DIR = os.path.expanduser("~/meritgiving/data/nccs")
LOG_FILE = os.path.expanduser("~/meritgiving/logs/ingest_part_x.log")

def log_msg(msg):
    """Log message with timestamp."""
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def find_part_x_files():
    """Find all Part X (Balance Sheet) files: F9-P10-T00-BALANCE-SHEET-YYYY.CSV"""
    pattern = "F9-P10*BALANCE*"
    files = list(Path(NCCS_DATA_DIR).glob(pattern + ".CSV"))
    files.extend(Path(NCCS_DATA_DIR).glob(pattern + ".csv"))
    return sorted(files)

def ingest_part_x(db, filepath):
    """Ingest single Part X balance sheet file (2019-2024, active orgs only)."""
    log_msg(f"Reading {filepath.name}...")

    updated = 0
    skipped = 0
    inactive_skipped = 0
    year_skipped = 0

    try:
        with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                # Extract EIN (use ORG_EIN as primary)
                ein = (row.get('ORG_EIN') or row.get('EIN', '')).strip()
                if not ein or len(ein) != 9:
                    skipped += 1
                    continue

                # Extract tax year
                tax_year_str = row.get('TAX_YEAR', '').strip()
                try:
                    tax_year = int(tax_year_str) if tax_year_str else None
                except ValueError:
                    skipped += 1
                    continue

                # Keep all years (previous filter: tax_year >= 2019, but keeping all for completeness)
                if not tax_year or tax_year < 2017:
                    year_skipped += 1
                    continue

                # Extract balance sheet fields (end of year values)
                total_assets_str = row.get('F9_10_ASSET_TOT_EOY', '').strip()
                total_liabilities_str = row.get('F9_10_LIAB_TOT_EOY', '').strip()
                net_assets_str = row.get('F9_10_NAFB_TOT_EOY', '').strip()

                # Convert to float, handle empty/invalid
                try:
                    total_assets = float(total_assets_str) if total_assets_str else None
                    total_liabilities = float(total_liabilities_str) if total_liabilities_str else None
                    net_assets = float(net_assets_str) if net_assets_str else None
                except ValueError:
                    skipped += 1
                    continue

                # Check if org is active in registry_enriched
                org = db.execute("""
                    SELECT org_status FROM registry_enriched WHERE ein = ?
                """, (ein,)).fetchone()

                if not org or org['org_status'] != 'active':
                    inactive_skipped += 1
                    continue

                # Update registry_enriched with Part X data
                try:
                    cursor = db.execute("""
                        UPDATE registry_enriched
                        SET nccs_net_assets = ?,
                            nccs_liabilities = ?,
                            nccs_part_x_loaded = 1,
                            nccs_data_year = ?
                        WHERE ein = ?
                    """, (net_assets, total_liabilities, tax_year, ein))

                    if cursor.rowcount > 0:
                        updated += 1
                    else:
                        skipped += 1
                except Exception as e:
                    log_msg(f"Error updating EIN {ein}: {e}")
                    skipped += 1

        db.commit()
        log_msg(f"Part X {filepath.name}: updated={updated}, skipped={skipped}, inactive={inactive_skipped}, year_out_of_range={year_skipped}")
        return updated

    except Exception as e:
        log_msg(f"ERROR reading {filepath.name}: {e}")
        return 0

def main():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    log_msg("=== NCCS Part X (Balance Sheet) Ingestion ===")

    if not os.path.exists(DB_PATH):
        log_msg(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    if not os.path.exists(NCCS_DATA_DIR):
        log_msg(f"ERROR: NCCS data directory not found at {NCCS_DATA_DIR}")
        sys.exit(1)

    # Find Part X files
    files = find_part_x_files()
    if not files:
        log_msg("WARNING: No Part X files found. Expected F9-P10-T00-BALANCE-SHEET-YYYY.CSV")
        sys.exit(1)

    log_msg(f"Found {len(files)} Part X file(s)")

    # Connect and ingest
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    total_records = 0

    try:
        for filepath in files:
            count = ingest_part_x(db, filepath)
            total_records += count
    finally:
        db.close()

    log_msg(f"Total records processed: {total_records}")
    log_msg("=== Part X Ingestion Complete ===")

if __name__ == "__main__":
    main()
