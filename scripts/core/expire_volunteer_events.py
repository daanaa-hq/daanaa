#!/usr/bin/env python3
"""Expire volunteer events whose event_date has passed. Runs nightly via overnight_pipeline.py."""
import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'merit_registry.db')


def run():
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("""
            UPDATE volunteer_events
            SET status = 'expired', updated_at = CURRENT_TIMESTAMP
            WHERE event_date < date('now')
              AND status = 'active'
        """)
        db.commit()
        n = cur.rowcount
    print(f"[expire_volunteer_events] expired {n} past event(s)")
    return n


if __name__ == '__main__':
    sys.exit(0 if run() >= 0 else 1)
