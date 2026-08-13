#!/usr/bin/env python3
"""
Migration: Add v6 percentile columns to registry_enriched

Idempotent: safe to run multiple times (checks for column existence first)
Timestamp: 2026-08-13
Status: Ready for Phase 1 deployment
"""

import sqlite3
import sys

DB_PATH = "data/merit_registry.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("[Migration 001] Adding v6 percentile columns to registry_enriched...")

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(registry_enriched)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    columns_to_add = [
        ("merit_percentile_v6", "INTEGER DEFAULT NULL"),
        ("merit_percentile_confidence_v6", "TEXT DEFAULT NULL"),
        ("merit_peer_count_v6_scoreable", "INTEGER DEFAULT NULL"),
    ]

    for col_name, col_def in columns_to_add:
        if col_name in existing_cols:
            print(f"  ✓ Column '{col_name}' already exists, skipping")
        else:
            sql = f"ALTER TABLE registry_enriched ADD COLUMN {col_name} {col_def}"
            cursor.execute(sql)
            print(f"  ✓ Added column '{col_name}'")

    conn.commit()
    conn.close()

    print("[Migration 001] Complete. All v6 percentile columns ready.")
    return 0

if __name__ == "__main__":
    sys.exit(migrate())
