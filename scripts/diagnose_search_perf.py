#!/usr/bin/env python3
"""
Diagnostic script for search performance issues.
Tests the /api/search endpoint under various conditions.
"""

import sqlite3
import time
import sys
import os
from pathlib import Path

# Setup
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "merit_registry.db"

def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def diagnose_database():
    """Check database health and search table status."""
    log("🔍 DATABASE DIAGNOSTICS")

    if not DB_PATH.exists():
        log(f"ERROR: Database not found at {DB_PATH}")
        return False

    log(f"Database size: {DB_PATH.stat().st_size / (1024**2):.1f} MB")

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()

        # Check if org_fts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='org_fts'")
        if not cursor.fetchone():
            log("ERROR: org_fts FTS table not found — search will fail")
            return False
        log("✓ org_fts FTS table exists")

        # Count organizations
        cursor.execute("SELECT COUNT(*) FROM registry_enriched")
        org_count = cursor.fetchone()[0]
        log(f"✓ Total organizations: {org_count:,}")

        # Check FTS table row count
        cursor.execute("SELECT COUNT(*) FROM org_fts")
        fts_count = cursor.fetchone()[0]
        log(f"✓ FTS index entries: {fts_count:,}")

        if org_count != fts_count:
            log(f"WARN: FTS out of sync (registry: {org_count}, FTS: {fts_count})")

        # Check if PRAGMA integrity_check passes
        log("Running PRAGMA integrity_check (this may take a moment)...")
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        if result == "ok":
            log("✓ Database integrity: OK")
        else:
            log(f"ERROR: Database integrity check failed: {result}")
            return False

        conn.close()
        return True

    except Exception as e:
        log(f"ERROR: {e}")
        return False

def diagnose_fts_query():
    """Test FTS query performance."""
    log("\n🔍 FTS QUERY PERFORMANCE")

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()

        # Test simple FTS query
        test_queries = [
            ("health", "common word"),
            ("food bank", "multi-word"),
            ("xyz123notreal", "non-existent"),
        ]

        for query, description in test_queries:
            start = time.time()
            cursor.execute(
                """SELECT COUNT(*) FROM org_fts WHERE org_fts MATCH ?""",
                (query,)
            )
            count = cursor.fetchone()[0]
            duration = time.time() - start
            log(f"  '{query}' ({description}): {count:,} results in {duration:.3f}s")

            if duration > 1.0:
                log(f"  ⚠️  SLOW: {query} took {duration:.3f}s")

        conn.close()

    except Exception as e:
        log(f"ERROR: {e}")
        return False

def diagnose_full_search():
    """Test a full search endpoint simulation."""
    log("\n🔍 FULL SEARCH SIMULATION")

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()

        # Simulate the actual search endpoint query
        q = "health"
        per_page = 5

        start = time.time()
        cursor.execute("""
            SELECT
                re.ein, re.organization_name, re.city, re.state, re.website,
                re.mission, re.merit_score, re.merit_tier,
                re.merit_health_signal_v5, re.donate_url, re.donate_confidence
            FROM org_fts
            JOIN registry_enriched re ON org_fts.docid = re.rowid
            WHERE org_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (q, per_page))

        results = cursor.fetchall()
        duration = time.time() - start

        log(f"Query: '{q}' with per_page={per_page}")
        log(f"Results: {len(results)} rows in {duration:.3f}s")

        if duration > 1.0:
            log(f"⚠️  SLOW: Full search took {duration:.3f}s")
        elif duration > 0.5:
            log(f"⚠️  MODERATE: Full search took {duration:.3f}s")
        else:
            log(f"✓ Fast: Full search took {duration:.3f}s")

        conn.close()

    except Exception as e:
        log(f"ERROR: {e}")
        return False

def check_api_search():
    """Check if the actual API endpoint responds."""
    log("\n🔍 API SEARCH ENDPOINT")

    try:
        import requests

        start = time.time()
        resp = requests.get("http://127.0.0.1:5000/api/search?q=health&per_page=5", timeout=10)
        duration = time.time() - start

        log(f"GET /api/search?q=health: {resp.status_code} in {duration:.3f}s")

        if resp.status_code != 200:
            log(f"ERROR: Endpoint returned {resp.status_code}")
            log(f"Response: {resp.text[:200]}")
            return False

        if duration > 2.0:
            log(f"⚠️  SLOW: API endpoint took {duration:.3f}s")
        else:
            log(f"✓ Fast: API endpoint took {duration:.3f}s")

        return True

    except requests.exceptions.Timeout:
        log("ERROR: API request timed out (timeout=10s)")
        return False
    except requests.exceptions.ConnectionError:
        log("ERROR: Could not connect to API at 127.0.0.1:5000")
        log("Is the Flask API running? (python3 daanaa_api.py)")
        return False
    except Exception as e:
        log(f"ERROR: {e}")
        return False

def main():
    log("=" * 60)
    log("SEARCH PERFORMANCE DIAGNOSTICS")
    log("=" * 60)
    log(f"Database: {DB_PATH}")
    log("")

    checks = [
        ("Database Health", diagnose_database),
        ("FTS Query Performance", diagnose_fts_query),
        ("Full Search Simulation", diagnose_full_search),
        ("API Endpoint", check_api_search),
    ]

    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            log(f"FATAL ERROR in {name}: {e}")
            results[name] = False

    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    for name, passed in results.items():
        status = "✓" if passed else "✗"
        log(f"{status} {name}")

    all_passed = all(results.values())
    if all_passed:
        log("\n✓ All diagnostics passed")
        return 0
    else:
        log("\n✗ Some diagnostics failed — review above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
