#!/usr/bin/env python3
"""Daily maintenance for the volunteer hours system.

1. Locks approved submissions once their 30-day edit window has passed
   (belt-and-suspenders: locked_at is already set at approval time to
   approved_at + 30d, but this catches any that predate that change or
   were set incorrectly).
2. Deletes volunteer_hours + audit log rows older than 7 years
   (Stewardship P2: entrusted data has a retention limit, not indefinite
   storage). Nonprofit yearly impact cache aggregates survive deletion
   since they hold no PII.

Run daily via cron (see scripts/setup_cron_schedules.sh).
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'data', 'merit_registry.db'))
EDIT_WINDOW_DAYS = 30
RETENTION_YEARS = 7


def lock_expired_edit_windows(conn: sqlite3.Connection) -> int:
    cutoff = (datetime.now() - timedelta(days=EDIT_WINDOW_DAYS)).isoformat()
    rows = conn.execute(
        "SELECT id FROM volunteer_hours WHERE status='approved' AND locked_at IS NULL AND approved_at < ?",
        (cutoff,),
    ).fetchall()
    for (hour_id,) in rows:
        locked_at = datetime.now().isoformat()
        conn.execute("UPDATE volunteer_hours SET locked_at=? WHERE id=?", (locked_at, hour_id))
        conn.execute(
            "INSERT INTO volunteer_hours_audit_log (hour_id, action, changed_by, change_details) "
            "VALUES (?, 'locked', 'system', ?)",
            (hour_id, '{"reason": "30-day edit window elapsed"}'),
        )
    conn.commit()
    return len(rows)


def delete_expired_records(conn: sqlite3.Connection) -> int:
    cutoff_date = (datetime.now() - timedelta(days=RETENTION_YEARS * 365)).strftime('%Y-%m-%d')
    ids = [r[0] for r in conn.execute(
        "SELECT id FROM volunteer_hours WHERE service_date < ?", (cutoff_date,)
    ).fetchall()]
    if not ids:
        return 0
    placeholders = ','.join('?' * len(ids))
    conn.execute(f"DELETE FROM volunteer_hours_audit_log WHERE hour_id IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM volunteer_hours WHERE id IN ({placeholders})", ids)
    conn.commit()
    return len(ids)


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        locked = lock_expired_edit_windows(conn)
        deleted = delete_expired_records(conn)
        print(f"volunteer_hours_maintenance: locked={locked} deleted={deleted} (7yr retention cutoff)")
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
