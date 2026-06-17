#!/usr/bin/env python3
"""Refresh impact_summary and impact_by_org tables daily."""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"

def refresh_impact_summary():
    """Aggregate all impact events into daily summary and org-level rollups."""
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    yesterday = (datetime.now() - timedelta(days=1)).date()

    # Aggregate all impact events from yesterday
    stats = c.execute("""
        SELECT
            COUNT(CASE WHEN impact_type='donation_attributed' THEN 1 END),
            SUM(CASE WHEN impact_type='donation_attributed' THEN amount ELSE 0 END),
            COUNT(CASE WHEN impact_type='volunteer_hours' THEN 1 END),
            SUM(CASE WHEN impact_type='volunteer_hours' THEN amount ELSE 0 END),
            COUNT(CASE WHEN impact_type='partnership_savings' THEN 1 END),
            SUM(CASE WHEN impact_type='partnership_savings' THEN amount ELSE 0 END),
            COUNT(DISTINCT org_ein),
            SUM(CASE WHEN verified=1 THEN 1 ELSE 0 END),
            COUNT(*)
        FROM impact_logs
        WHERE DATE(created_at) = ?
    """, (str(yesterday),)).fetchone()

    donation_count = stats[0] or 0
    donation_total = stats[1] or 0
    volunteer_count = stats[2] or 0
    volunteer_hours = stats[3] or 0
    savings_count = stats[4] or 0
    savings_total = stats[5] or 0
    unique_orgs = stats[6] or 0

    # Insert/update summary for yesterday
    c.execute("""
        INSERT OR REPLACE INTO impact_summary
        (summary_date, total_donation_attributed, count_donations_attributed,
         total_volunteer_hours, count_volunteer_reports, total_volunteer_value,
         total_partnership_savings, count_partner_transactions, unique_orgs_impacted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(yesterday),
        donation_total,
        donation_count,
        volunteer_hours,
        volunteer_count,
        volunteer_hours * 28.50,  # BLS average service rate
        savings_total,
        savings_count,
        unique_orgs,
    ))

    # Refresh org-level aggregates (all-time)
    c.execute("""
        INSERT OR REPLACE INTO impact_by_org (org_ein, donation_attributed, donation_count,
                                              volunteer_hours, volunteer_reports, volunteer_value,
                                              partnership_savings, last_updated)
        SELECT
            org_ein,
            SUM(CASE WHEN impact_type='donation_attributed' THEN amount ELSE 0 END),
            COUNT(CASE WHEN impact_type='donation_attributed' THEN 1 END),
            SUM(CASE WHEN impact_type='volunteer_hours' THEN amount ELSE 0 END),
            COUNT(CASE WHEN impact_type='volunteer_hours' THEN 1 END),
            SUM(CASE WHEN impact_type='volunteer_hours' THEN amount ELSE 0 END) * 28.50,
            SUM(CASE WHEN impact_type='partnership_savings' THEN amount ELSE 0 END),
            datetime('now')
        FROM impact_logs
        GROUP BY org_ein
    """)

    conn.commit()
    conn.close()
    print(f"✓ Impact summary refreshed for {yesterday}")

if __name__ == "__main__":
    refresh_impact_summary()
