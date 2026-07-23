#!/usr/bin/env python3
"""
Ingest NCCS Part X (Balance Sheet) data into registry_enriched.

Part X contains net assets, liabilities, and financial health indicators.
This data can unlock ~106K additional orgs for scoring.
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
    """Find all Part X (Balance Sheet) files in NCCS data directory."""
    pattern = "F10*BALANCE*"
    files = list(Path(NCCS_DATA_DIR).glob(pattern + ".CSV"))
    files.extend(Path(NCCS_DATA_DIR).glob(pattern + ".csv"))
    return sorted(files)

def ingest_part_x(db, filepath):
    """Ingest single Part X file (only last 5 years, active orgs only)."""
    log_msg(f"Reading {filepath.name}...")

    added = 0
    updated = 0
    skipped = 0
    inactive_skipped = 0
    year_skipped = 0

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                ein = row.get('ein') or row.get('EIN', '').strip()
                if not ein or len(ein) != 9:
                    skipped += 1
                    continue

                # Extract tax year
                tax_year = row.get('tax_year') or row.get('TAX_YEAR', '')
                try:
                    tax_year = int(tax_year) if tax_year else None
                except ValueError:
                    skipped += 1
                    continue

                # Only keep last 5 years (2019-2024)
                if not tax_year or tax_year < 2019:
                    year_skipped += 1
                    continue

                # Extract key balance sheet fields
                net_assets = row.get('net_assets') or row.get('TOT_ASSET', '')
                liabilities = row.get('liabilities') or row.get('TOT_LIAB', '')
                revenue = row.get('revenue') or row.get('TOT_REV', '')
                expenses = row.get('expenses') or row.get('TOT_EXP', '')

                # Convert to float, handle errors
                try:
                    net_assets = float(net_assets) if net_assets else None
                    liabilities = float(liabilities) if liabilities else None
                    revenue = float(revenue) if revenue else None
                    expenses = float(expenses) if expenses else None
                except ValueError:
                    skipped += 1
                    continue

                # Check if org is active (deductibility_status ACTIVE or similar)
                org = db.execute("""
                    SELECT deductibility_status FROM registry_enriched WHERE ein = ?
                """, (ein,)).fetchone()

                if not org or org['deductibility_status'] != 'ACTIVE':
                    inactive_skipped += 1
                    continue

                # Update registry_enriched with Part X data
                try:
                    cursor = db.execute("""
                        UPDATE registry_enriched
                        SET nccs_net_assets = ?,
                            nccs_liabilities = ?,
                            nccs_revenue_part_x = ?,
                            nccs_expenses_part_x = ?,
                            nccs_part_x_loaded = 1,
                            nccs_data_year = ?
                        WHERE ein = ?
                    """, (net_assets, liabilities, revenue, expenses, tax_year, ein))

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
        log_msg("WARNING: No Part X files found. Expected F10*BALANCE*.CSV")
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
