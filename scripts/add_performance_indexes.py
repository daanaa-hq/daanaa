#!/usr/bin/env python3
"""
Add performance indexes to Daanaa registry_enriched table.

Safe and reversible. Can be rolled back with: DROP INDEX idx_*.

Run: python3 scripts/add_performance_indexes.py
"""

import sqlite3
import time
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

INDEXES = [
    {
        "name": "idx_merit_score",
        "table": "registry_enriched",
        "columns": ["merit_score"],
        "description": "Index on merit_score for score-based queries and sorting"
    },
    {
        "name": "idx_ntee1_merit_score",
        "table": "registry_enriched",
        "columns": ["NTEE1", "merit_score"],
        "description": "Composite index for peer group queries (NTEE1 + score)"
    },
    {
        "name": "idx_website_status",
        "table": "registry_enriched",
        "columns": ["website_status"],
        "description": "Index for website discovery filtering"
    },
    {
        "name": "idx_donate_url_status",
        "table": "registry_enriched",
        "columns": ["donate_url_status"],
        "description": "Index for donate URL discovery filtering"
    },
]

def create_index(conn, index_spec):
    """Create a single index."""
    name = index_spec["name"]
    table = index_spec["table"]
    columns = ", ".join(index_spec["columns"])
    desc = index_spec["description"]

    # Check if index already exists
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (name,)
    )

    if cursor.fetchone():
        print(f"  ✓ {name} already exists, skipping")
        return False

    # Create index
    sql = f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})"
    print(f"  Creating {name}...")
    print(f"    Description: {desc}")
    print(f"    SQL: {sql}")

    start = time.time()
    cursor.execute(sql)
    elapsed = time.time() - start

    print(f"    Created in {elapsed:.2f}s")
    return True

def main():
    print("=" * 70)
    print("DAANAA PERFORMANCE INDEX CREATION")
    print("=" * 70)

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Check database integrity first
        print("\nVerifying database integrity...")
        cursor.execute("PRAGMA integrity_check")
        check_result = cursor.fetchone()[0]
        if check_result != "ok":
            print(f"ERROR: Database integrity check failed: {check_result}")
            return False

        print("  ✓ Database integrity verified")

        # Create indexes
        print("\nCreating indexes...")
        created_count = 0

        for index_spec in INDEXES:
            if create_index(conn, index_spec):
                created_count += 1

        # Commit
        conn.commit()

        print(f"\n✓ Created {created_count} new indexes")

        # Verify
        print("\nVerifying indexes...")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='registry_enriched'
            ORDER BY name
        """)

        indexes = cursor.fetchall()
        print(f"  Total indexes on registry_enriched: {len(indexes)}")
        for idx in indexes:
            print(f"    - {idx[0]}")

        # Re-run baseline query on one of the slow queries to show impact
        print("\nTesting peer group query performance...")
        start = time.time()
        cursor.execute("""
            SELECT NTEE1, COUNT(*), AVG(merit_score), MIN(merit_score), MAX(merit_score)
            FROM registry_enriched
            WHERE merit_score IS NOT NULL
            GROUP BY NTEE1
        """)
        results = cursor.fetchall()
        elapsed = (time.time() - start) * 1000

        print(f"  Peer group query: {elapsed:.2f}ms (should show improvement)")
        print(f"  Results: {len(results)} peer groups")

        conn.close()
        print("\n✓ Index creation complete and verified")
        return True

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
