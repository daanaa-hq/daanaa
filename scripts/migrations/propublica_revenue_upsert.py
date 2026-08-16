#!/usr/bin/env python3
"""
Upsert ProPublica revenue data into registry_enriched.

Reads latest revenue per EIN from financials_annual.csv (most recent tax_year
first), and UPSERTs into registry_enriched.total_revenue where currently NULL.
Logs coverage before/after.

Usage:
    python3 scripts/propublica_revenue_upsert.py
"""

import sqlite3
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
DB = REPO_ROOT / "data" / "merit_registry.db"
FINANCIALS_CSV = REPO_ROOT / "data" / "csv" / "financials_annual.csv"

def load_latest_revenues():
    """Load latest revenue per EIN from ProPublica CSV."""
    revenues = {}  # ein -> (total_revenue, tax_year)

    if not FINANCIALS_CSV.exists():
        print(f"✗ CSV not found: {FINANCIALS_CSV}")
        return revenues

    with open(FINANCIALS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ein = row.get('ein', '').strip()
            if not ein or not ein.isdigit():
                continue

            tax_year = row.get('tax_year', '').strip()
            total_revenue_cents = row.get('total_revenue_cents', '').strip()

            if not tax_year or not total_revenue_cents:
                continue

            # Convert cents to dollars
            try:
                tax_year_int = int(tax_year)
                revenue_dollars = int(total_revenue_cents) / 100
            except (ValueError, TypeError):
                continue

            # Keep only the latest tax year per EIN
            if ein not in revenues or tax_year_int > int(revenues[ein][1]):
                revenues[ein] = (revenue_dollars, tax_year)

    print(f"✓ Loaded {len(revenues):,} EINs with revenue data from ProPublica")
    return revenues

def audit_coverage(db):
    """Count orgs with and without revenue data."""
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE total_revenue IS NOT NULL")
    with_revenue = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE total_revenue IS NULL")
    without_revenue = cursor.fetchone()[0]

    total = with_revenue + without_revenue
    pct = (with_revenue / total * 100) if total > 0 else 0

    return {"with": with_revenue, "without": without_revenue, "total": total, "pct": pct}

def upsert_revenues(db, revenues):
    """Upsert ProPublica revenues into registry_enriched."""
    cursor = db.cursor()

    updated = 0
    for ein, (revenue, tax_year) in revenues.items():
        cursor.execute(
            """UPDATE registry_enriched
               SET total_revenue = ?
               WHERE EIN = ? AND total_revenue IS NULL""",
            (revenue, ein)
        )
        updated += cursor.rowcount

    db.commit()
    print(f"✓ Upserted {updated:,} revenue values")
    return updated

def main():
    print("=" * 70)
    print("ProPublica Revenue Upsert")
    print("=" * 70)

    # Load ProPublica data
    revenues = load_latest_revenues()
    if not revenues:
        print("✗ No revenue data loaded")
        return

    # Connect to DB
    db = sqlite3.connect(str(DB))

    # Before audit
    before = audit_coverage(db)
    print(f"Before: {before['with']:,} with revenue, {before['without']:,} without ({before['pct']:.1f}%)")

    # Upsert
    updated = upsert_revenues(db, revenues)

    # After audit
    after = audit_coverage(db)
    print(f"After: {after['with']:,} with revenue, {after['without']:,} without ({after['pct']:.1f}%)")

    # Summary
    improvement = after['with'] - before['with']
    print(f"\nImprovement: +{improvement:,} orgs ({improvement/before['total']*100:.2f}% coverage gain)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    db.close()

if __name__ == '__main__':
    main()
