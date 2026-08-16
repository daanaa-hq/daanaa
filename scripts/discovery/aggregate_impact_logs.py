#!/usr/bin/env python3
"""Daily aggregation of impact logs for monthly reporting.

Runs daily at 1 AM UTC (after midnight cutoff) to compute yesterdays stats.
Updates impact_aggregates table with rolled-up metrics.
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/merit_registry.db')

def aggregate_daily():
    """Aggregate yesterday's impact logs into daily snapshot."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # Aggregate metrics for yesterday
    cursor.execute('''
        SELECT
          COALESCE(SUM(amount), 0) as total_dollars,
          COALESCE(SUM(hours), 0) as total_hours,
          COUNT(CASE WHEN type='giving' THEN 1 END) as donation_count,
          COUNT(CASE WHEN type='volunteer' THEN 1 END) as volunteer_count,
          COUNT(DISTINCT ein) as org_count,
          COUNT(DISTINCT CASE WHEN type='volunteer' THEN ein END) as active_volunteers
        FROM impact_logs
        WHERE log_date = ?
    ''', (yesterday,))

    row = cursor.fetchone()
    if row:
        total_dollars, total_hours, donation_count, volunteer_count, org_count, active_volunteers = row

        # Upsert into impact_aggregates
        cursor.execute('''
            INSERT OR REPLACE INTO impact_aggregates
            (aggregate_date, total_dollars, total_hours, donation_count, volunteer_count, org_count, active_volunteers)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (yesterday, total_dollars or 0, total_hours or 0, donation_count or 0,
              volunteer_count or 0, org_count or 0, active_volunteers or 0))

        conn.commit()
        print(f"✓ Aggregated impact for {yesterday}: ${total_dollars} + {total_hours}h volunteer")
    else:
        print(f"No impact logs for {yesterday}")

    conn.close()

if __name__ == '__main__':
    aggregate_daily()
