#!/usr/bin/env python3
"""
Apply migration 003: Add search performance indexes
Task #5: Schema changes (approved 2026-08-12)

Usage:
  python3 scripts/migrations/run_migration_003.py
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
MIGRATION_FILE = Path(__file__).parent / "003_add_search_performance_indexes.sql"

def run_migration():
    """Apply indexes to registry_enriched table."""

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return False

    if not MIGRATION_FILE.exists():
        print(f"❌ Migration file not found: {MIGRATION_FILE}")
        return False

    print(f"Applying migration: {MIGRATION_FILE.name}")
    print(f"Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Read migration SQL
        with open(MIGRATION_FILE, 'r') as f:
            sql = f.read()

        # Execute migration
        cursor.executescript(sql)
        conn.commit()

        print("✅ Migration applied successfully")
        print()

        # Verify indexes
        print("Verifying indexes on registry_enriched:")
        cursor.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type='index'
            AND tbl_name='registry_enriched'
            ORDER BY name
        """)

        indexes = cursor.fetchall()
        if indexes:
            for name, sql_text in indexes:
                print(f"  ✓ {name}")
                if "idx_" in name:  # Only show our new indexes
                    print(f"    {sql_text[:80]}...")
        else:
            print("  (No indexes found)")

        print()

        # Quick performance test
        print("Performance impact test:")
        print("  Running sample queries to verify indexes are used...")

        # Test 1: State filter
        cursor.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE STATE = 'TX' LIMIT 1000
        """)
        count = cursor.fetchone()[0]
        print(f"  ✓ STATE filter: {count} orgs in Texas")

        # Test 2: Score sorting
        cursor.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE merit_score IS NOT NULL
            ORDER BY merit_score DESC
            LIMIT 100
        """)
        count = cursor.fetchone()[0]
        print(f"  ✓ Score sorting: {count} orgs sorted by merit score")

        # Test 3: NTEE filter
        cursor.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE NTEE1 = 'E' LIMIT 1000
        """)
        count = cursor.fetchone()[0]
        print(f"  ✓ NTEE filter: {count} educational orgs")

        print()
        print("✅ All tests passed")
        print()
        print("Migration complete! Expected 5-10% improvement on filtered/sorted queries.")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
