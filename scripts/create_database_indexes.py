#!/usr/bin/env python3
"""
Database index creation and optimization for merit_registry.db
Adds strategic indexes for common query patterns and runs VACUUM.
Reports before/after query execution times.
"""
import sqlite3
import time
import sys
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'merit_registry.db')

# Test queries to benchmark
TEST_QUERIES = [
    ("nonprofit_ein lookup", "SELECT COUNT(*) FROM nonprofit_accounts WHERE ein = ?", ('01-0000001',)),
    ("org location search", "SELECT COUNT(*) FROM registry_enriched WHERE STATE = ? AND CITY = ?", ('CA', 'San Francisco')),
    ("org NTEE lookup", "SELECT COUNT(*) FROM registry_enriched WHERE NTEE1 = ?", ('A20',)),
]

def get_db_size(conn):
    """Return database file size in bytes"""
    return os.path.getsize(DB_PATH)

def execute_test_query(conn, description, query, params):
    """Execute a test query and return timing"""
    start = time.time()
    try:
        cursor = conn.execute(query, params)
        cursor.fetchall()
        elapsed = time.time() - start
        return elapsed, None
    except Exception as e:
        return None, str(e)

def create_indexes(conn):
    """Create strategic indexes"""
    indexes = [
        ("idx_nonprofit_ein", "nonprofit_accounts", "ein"),
        ("idx_nonprofit_email", "nonprofit_accounts", "email"),
        ("idx_org_state_city", "registry_enriched", "STATE, CITY"),
        ("idx_org_ntee1", "registry_enriched", "NTEE1"),
        ("idx_org_nteecc", "registry_enriched", "NTEECC"),
        ("idx_volunteer_nonprofit_status", "volunteer_hours", "nonprofit_ein, status"),
        ("idx_volunteer_submitted", "volunteer_hours", "submitted_at"),
        ("idx_org_claims_ein", "org_claims", "ein"),
        ("idx_org_claims_status", "org_claims", "claim_status"),
        ("idx_feedback_status", "feedback", "status"),
        ("idx_donate_handoffs_ein", "donate_handoffs", "ein"),
        ("idx_org_interest_ein", "org_interest", "ein"),
    ]

    created = []
    skipped = []

    for index_name, table_name, columns in indexes:
        try:
            # Check if index already exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                (index_name,)
            )
            if cursor.fetchone():
                skipped.append(index_name)
                continue

            # Create index
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})"
            conn.execute(sql)
            created.append(index_name)
        except sqlite3.OperationalError as e:
            if "no such table" not in str(e):
                raise
            skipped.append(f"{index_name} (table {table_name} missing)")

    return created, skipped

def run_vacuum(conn):
    """Run VACUUM to optimize database"""
    conn.execute("VACUUM")

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 70)
    print(f"Database Optimization Report — {datetime.now().isoformat()}")
    print("=" * 70)

    # Pre-optimization stats
    before_size = get_db_size(conn)
    print(f"\nBefore optimization:")
    print(f"  Database size: {before_size / 1024 / 1024:.2f} MB")

    # Count indexes before
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    before_indexes = cursor.fetchone()[0]
    print(f"  Existing indexes: {before_indexes}")

    # Run test queries before
    print(f"\nTest queries (before indexing):")
    before_times = {}
    for description, query, params in TEST_QUERIES:
        elapsed, error = execute_test_query(conn, description, query, params)
        if error:
            print(f"  {description}: ERROR - {error}")
        else:
            before_times[description] = elapsed
            print(f"  {description}: {elapsed*1000:.2f} ms")

    # Create indexes
    print(f"\nCreating indexes...")
    created, skipped = create_indexes(conn)
    conn.commit()

    if created:
        print(f"  Created {len(created)} new indexes:")
        for idx in created:
            print(f"    - {idx}")

    if skipped:
        print(f"  Skipped {len(skipped)} existing indexes:")
        for idx in skipped[:5]:  # Show first 5
            print(f"    - {idx}")
        if len(skipped) > 5:
            print(f"    ... and {len(skipped) - 5} more")

    # Run VACUUM
    print(f"\nRunning VACUUM...")
    run_vacuum(conn)
    print(f"  VACUUM complete")

    # Post-optimization stats
    after_size = get_db_size(conn)
    print(f"\nAfter optimization:")
    print(f"  Database size: {after_size / 1024 / 1024:.2f} MB")

    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    after_indexes = cursor.fetchone()[0]
    print(f"  Total indexes: {after_indexes}")

    # Run test queries after
    print(f"\nTest queries (after indexing):")
    after_times = {}
    speedups = {}
    for description, query, params in TEST_QUERIES:
        elapsed, error = execute_test_query(conn, description, query, params)
        if error:
            print(f"  {description}: ERROR - {error}")
        else:
            after_times[description] = elapsed
            if description in before_times:
                speedup = before_times[description] / elapsed if elapsed > 0 else 1.0
                speedups[description] = speedup
                symbol = "✓" if speedup > 1.1 else "—"
                print(f"  {description}: {elapsed*1000:.2f} ms [{symbol} {speedup:.1f}x]")
            else:
                print(f"  {description}: {elapsed*1000:.2f} ms")

    # Summary
    if speedups:
        avg_speedup = sum(speedups.values()) / len(speedups)
        print(f"\nPerformance improvement: average {avg_speedup:.1f}x speedup")

    print(f"\nSize change: {(after_size - before_size) / 1024 / 1024:+.2f} MB")
    print("=" * 70)

    conn.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
