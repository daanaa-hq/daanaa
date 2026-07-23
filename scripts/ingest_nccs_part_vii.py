#!/usr/bin/env python3
"""
Ingest NCCS Part VII (Compensation) data into registry_enriched.

Part VII contains executive compensation and Form 990 filing information.
Enriches transparency data for executive leadership visibility.
"""

import sqlite3
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")
NCCS_DATA_DIR = os.path.expanduser("~/meritgiving/data/nccs")
LOG_FILE = os.path.expanduser("~/meritgiving/logs/ingest_part_vii.log")

def log_msg(msg):
    """Log message with timestamp."""
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def find_part_vii_files():
    """Find all Part VII (Compensation) files."""
    pattern = "F7*COMPENSATION*"
    files = list(Path(NCCS_DATA_DIR).glob(pattern + ".CSV"))
    files.extend(Path(NCCS_DATA_DIR).glob(pattern + ".csv"))
    return sorted(files)

def ingest_part_vii(db, filepath):
    """Ingest single Part VII file (only last 5 years, active orgs only)."""
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

                # Extract compensation fields
                compensation = row.get('compensation') or row.get('COMP', '')

                # Convert to appropriate types
                try:
                    compensation = float(compensation) if compensation else None
                except ValueError:
                    skipped += 1
                    continue

                # Check if org is active
                org = db.execute("""
                    SELECT deductibility_status FROM registry_enriched WHERE ein = ?
                """, (ein,)).fetchone()

                if not org or org['deductibility_status'] != 'ACTIVE':
                    inactive_skipped += 1
                    continue

                # Update registry_enriched
                try:
                    cursor = db.execute("""
                        UPDATE registry_enriched
                        SET nccs_executive_compensation = ?,
                            nccs_form_990_filed = ?,
                            nccs_data_year = ?
                        WHERE ein = ?
                    """, (compensation, 1, tax_year, ein))

                    if cursor.rowcount > 0:
                        updated += 1
                    else:
                        skipped += 1
                except Exception as e:
                    log_msg(f"Error updating EIN {ein}: {e}")
                    skipped += 1

        db.commit()
        log_msg(f"Part VII {filepath.name}: updated={updated}, skipped={skipped}, inactive={inactive_skipped}, year_out_of_range={year_skipped}")
        return updated

    except Exception as e:
        log_msg(f"ERROR reading {filepath.name}: {e}")
        return 0

def main():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    log_msg("=== NCCS Part VII (Compensation) Ingestion ===")

    if not os.path.exists(DB_PATH):
        log_msg(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    files = find_part_vii_files()
    if not files:
        log_msg("WARNING: No Part VII files found. Expected F7*COMPENSATION*.CSV")
        sys.exit(1)

    log_msg(f"Found {len(files)} Part VII file(s)")

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    total_records = 0

    try:
        for filepath in files:
            count = ingest_part_vii(db, filepath)
            total_records += count
    finally:
        db.close()

    log_msg(f"Total records processed: {total_records}")
    log_msg("=== Part VII Ingestion Complete ===")

if __name__ == "__main__":
    main()
