#!/usr/bin/env python3
"""
Database health check — runs after rebuild to validate data quality.
Detects corruption, missing data, and structural issues that would break the API.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "merit_registry.db"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def validate():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    issues = []
    warnings = []

    # 1. Count orgs
    total = cur.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    log(f"Total orgs: {total:,}")

    # 2. Check for NULLs in required columns
    log("\n=== REQUIRED FIELDS ===")
    for col in ['EIN', 'organization_name', 'STATE', 'subsection', 'deductibility', 'updated_at']:
        nulls = cur.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {col} IS NULL").fetchone()[0]
        if nulls > 0:
            issues.append(f"❌ {col}: {nulls:,} NULLs (should be 0)")
            log(f"  ❌ {col}: {nulls:,} NULLs")
        else:
            log(f"  ✓ {col}: {total:,} complete")

    # 3. Check for invalid values
    log("\n=== DATA VALIDITY ===")

    # Deductibility must be 0 or 1
    bad_deduct = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE deductibility NOT IN (0, 1)").fetchone()[0]
    if bad_deduct > 0:
        issues.append(f"❌ deductibility: {bad_deduct:,} invalid values (must be 0 or 1)")
        log(f"  ❌ deductibility: {bad_deduct:,} invalid values")
    else:
        log(f"  ✓ deductibility: all valid (0 or 1)")

    # STATE must be 2 characters
    bad_state = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE LENGTH(STATE) != 2").fetchone()[0]
    if bad_state > 0:
        issues.append(f"❌ STATE: {bad_state:,} invalid values (must be 2 chars)")
        log(f"  ❌ STATE: {bad_state:,} invalid values")
        # Show examples
        examples = cur.execute("SELECT DISTINCT STATE FROM registry_enriched WHERE LENGTH(STATE) != 2 LIMIT 10").fetchall()
        for ex in examples:
            log(f"      Example: '{ex[0]}'")
    else:
        log(f"  ✓ STATE: all 2 chars")

    # 4. Financial data quality
    log("\n=== FINANCIAL DATA ===")
    with_revenue = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE total_revenue IS NOT NULL AND total_revenue > 0").fetchone()[0]
    log(f"  Orgs with revenue data: {with_revenue:,} ({100*with_revenue/total:.1f}%)")

    negative_rev = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE total_revenue < 0").fetchone()[0]
    if negative_rev > 0:
        issues.append(f"❌ Negative revenue: {negative_rev:,} orgs (impossible)")
        log(f"  ❌ Negative revenue: {negative_rev:,} orgs")
        examples = cur.execute("SELECT EIN, organization_name, total_revenue FROM registry_enriched WHERE total_revenue < 0 LIMIT 5").fetchall()
        for ex in examples:
            log(f"      {ex[0]}: {ex[1]} = ${ex[2]:,.0f}")

    negative_exp = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE total_expenses < 0").fetchone()[0]
    if negative_exp > 0:
        issues.append(f"❌ Negative expenses: {negative_exp:,} orgs (impossible)")
        log(f"  ❌ Negative expenses: {negative_exp:,} orgs")

    bad_pct = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE program_expense_pct > 100 OR program_expense_pct < 0").fetchone()[0]
    if bad_pct > 0:
        issues.append(f"❌ Bad program_expense_pct: {bad_pct:,} orgs (outside 0-100%)")
        log(f"  ❌ Bad program_expense_pct: {bad_pct:,} orgs")

    # 5. NTEE coverage
    log("\n=== NTEE CLASSIFICATION ===")
    with_ntee1 = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE NTEE1 IS NOT NULL").fetchone()[0]
    log(f"  With NTEE1: {with_ntee1:,} ({100*with_ntee1/total:.1f}%)")
    if with_ntee1 < 0.7 * total:
        warnings.append(f"⚠ NTEE1 coverage < 70% ({100*with_ntee1/total:.1f}%)")

    unique_ntee1 = cur.execute("SELECT COUNT(DISTINCT NTEE1) FROM registry_enriched WHERE NTEE1 IS NOT NULL").fetchone()[0]
    log(f"  Unique NTEE1 values: {unique_ntee1}")
    if unique_ntee1 < 26:
        warnings.append(f"⚠ Only {unique_ntee1} NTEE1 values (expected 26 A-Z)")

    # 6. Scoring coverage
    log("\n=== SCORING ===")
    v4_scored = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL").fetchone()[0]
    log(f"  v4 scored: {v4_scored:,} ({100*v4_scored/total:.1f}%)")

    v5_scored = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE merit_score_v5 IS NOT NULL").fetchone()[0]
    log(f"  v5 scored: {v5_scored:,} ({100*v5_scored/total:.1f}%)")

    # 7. Data sources
    log("\n=== DATA SOURCES ===")
    by_source = cur.execute("SELECT source, COUNT(*) as cnt FROM registry_enriched GROUP BY source ORDER BY cnt DESC").fetchall()
    for row in by_source:
        log(f"  {row[0]}: {row[1]:,}")

    # 8. Visibility
    log("\n=== VISIBILITY STATUS ===")
    with_visibility = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE visibility_tier IS NOT NULL").fetchone()[0]
    log(f"  With visibility_tier: {with_visibility:,}")

    hidden_gems = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem = 1").fetchone()[0]
    log(f"  Marked as hidden gems: {hidden_gems:,}")

    # Summary
    log("\n" + "="*60)
    if issues:
        log("CRITICAL ISSUES FOUND:")
        for issue in issues:
            log(f"  {issue}")
    else:
        log("✓ NO CRITICAL ISSUES")

    if warnings:
        log("\nWARNINGS:")
        for warning in warnings:
            log(f"  {warning}")

    if not issues:
        log("\n✓ Database is healthy and ready for production use")
        return True
    else:
        log("\n❌ Database has critical issues — do not deploy")
        return False

    conn.close()

if __name__ == "__main__":
    success = validate()
    exit(0 if success else 1)
