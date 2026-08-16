#!/usr/bin/env python3
"""
Aggregate vendor rating stats — run nightly as part of the pipeline.
Recalculates avg_rating, rating_count, total_savings for all vendors.
Zero-touch: no notifications, no queues, just updated stats in vendor_stats table.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'merit_registry.db'

def aggregate_all_vendors():
    """Recalculate stats for all vendors."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get all vendors
        vendors = cursor.execute("SELECT vendor_id FROM vendors").fetchall()

        for vendor_row in vendors:
            vendor_id = vendor_row['vendor_id']

            # Calculate aggregated stats
            stats = cursor.execute("""
                SELECT
                    ROUND(AVG(stars), 2) as avg_rating,
                    COUNT(*) as rating_count,
                    SUM(savings_amount) as total_savings,
                    COUNT(CASE WHEN savings_amount > 0 THEN 1 END) as nonprofits_contributed
                FROM vendor_ratings
                WHERE vendor_id = ?
            """, (vendor_id,)).fetchone()

            avg_rating, rating_count, total_savings, nonprofits_contributed = (
                stats['avg_rating'],
                stats['rating_count'] or 0,
                stats['total_savings'] or 0,
                stats['nonprofits_contributed'] or 0
            )

            # Upsert into vendor_stats
            cursor.execute("""
                INSERT INTO vendor_stats (
                    vendor_id, avg_rating, rating_count, total_savings,
                    nonprofits_contributed, last_aggregated_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(vendor_id) DO UPDATE SET
                    avg_rating = excluded.avg_rating,
                    rating_count = excluded.rating_count,
                    total_savings = excluded.total_savings,
                    nonprofits_contributed = excluded.nonprofits_contributed,
                    last_aggregated_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (vendor_id, avg_rating, rating_count, total_savings, nonprofits_contributed))

        conn.commit()

        # Summary
        total_vendors = len(vendors)
        active_vendors = cursor.execute(
            "SELECT COUNT(*) as cnt FROM vendors WHERE active = 1"
        ).fetchone()['cnt']

        print(f"✓ Aggregated stats for {total_vendors} vendors ({active_vendors} active)")

        # Show top vendors
        top_vendors = cursor.execute("""
            SELECT v.name, s.avg_rating, s.rating_count, s.total_savings
            FROM vendor_stats s
            JOIN vendors v ON s.vendor_id = v.vendor_id
            WHERE v.active = 1
            ORDER BY s.avg_rating DESC, s.rating_count DESC
            LIMIT 5
        """).fetchall()

        if top_vendors:
            print("\nTop-rated vendors:")
            for vendor in top_vendors:
                print(f"  {vendor['name']}: ⭐ {vendor['avg_rating']} ({vendor['rating_count']} ratings, ${vendor['total_savings']:,} saved)")

    finally:
        conn.close()


if __name__ == '__main__':
    try:
        aggregate_all_vendors()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
