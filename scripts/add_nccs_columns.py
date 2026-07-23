#!/usr/bin/env python3
"""
Add NCCS data columns to registry_enriched table.

Adds columns for Part VII (compensation), Part X (balance sheet), Part XI (overhead).
Safe: uses IF NOT EXISTS to avoid errors on re-runs.
"""

import sqlite3
import os
import sys

DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")

# Columns to add (if not exists)
COLUMNS = [
    # Part VII - Compensation
    ("nccs_executive_compensation", "REAL"),
    ("nccs_form_990_filed", "INTEGER"),  # year filed

    # Part X - Balance Sheet
    ("nccs_net_assets", "REAL"),
    ("nccs_liabilities", "REAL"),
    ("nccs_revenue_part_x", "REAL"),
    ("nccs_expenses_part_x", "REAL"),
    ("nccs_part_x_loaded", "INTEGER DEFAULT 0"),

    # Part XI - Overhead Ratios
    ("nccs_overhead_ratio", "REAL"),
    ("nccs_program_ratio", "REAL"),
    ("nccs_efficiency_score", "REAL"),

    # Tracking
    ("nccs_full_load_date", "TEXT"),
    ("nccs_data_year", "INTEGER"),
]

def add_columns():
    """Add columns to registry_enriched if they don't exist."""
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    added = 0
    for col_name, col_type in COLUMNS:
        try:
            cursor.execute(f"""
                ALTER TABLE registry_enriched
                ADD COLUMN {col_name} {col_type}
            """)
            print(f"✓ Added column: {col_name}")
            added += 1
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print(f"~ Column exists: {col_name}")
            else:
                print(f"✗ Error adding {col_name}: {e}")

    db.commit()
    db.close()

    print(f"\nTotal columns added: {added}")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    add_columns()
