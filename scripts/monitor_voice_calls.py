#!/usr/bin/env python3
"""
Monitor voice support call volume and patterns.
Run daily (or on-demand) to see: call count, unique callers, response times.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = "/opt/daanaa/data/merit_registry.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def call_stats(days=7):
    """Get call statistics for the last N days."""
    db = get_db()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    # Total calls
    total = db.execute(
        "SELECT COUNT(*) as count FROM support_calls WHERE received_at > ?",
        (cutoff,)
    ).fetchone()["count"]

    # Unique callers
    unique = db.execute(
        "SELECT COUNT(DISTINCT from_phone) as count FROM support_calls WHERE received_at > ?",
        (cutoff,)
    ).fetchone()["count"]

    # Calls per day (trend)
    daily = db.execute(
        """SELECT DATE(received_at) as day, COUNT(*) as calls
           FROM support_calls WHERE received_at > ?
           GROUP BY day ORDER BY day DESC""",
        (cutoff,)
    ).fetchall()

    # Recent calls
    recent = db.execute(
        """SELECT from_phone, received_at, notes
           FROM support_calls WHERE received_at > ?
           ORDER BY received_at DESC LIMIT 10""",
        (cutoff,)
    ).fetchall()

    db.close()

    return {
        "total": total,
        "unique_callers": unique,
        "daily_breakdown": [(row["day"], row["calls"]) for row in daily],
        "recent_calls": [(row["from_phone"], row["received_at"], row["notes"]) for row in recent],
    }

if __name__ == "__main__":
    stats = call_stats(7)

    print("=" * 60)
    print(f"VOICE SUPPORT CALL VOLUME (last 7 days)")
    print("=" * 60)
    print(f"Total calls:       {stats['total']}")
    print(f"Unique callers:    {stats['unique_callers']}")
    print(f"Avg per day:       {stats['total'] / 7:.1f}")
    print()
    print("Daily breakdown:")
    for day, calls in stats['daily_breakdown']:
        print(f"  {day}: {calls} calls")
    print()
    print("Recent calls:")
    for phone, when, notes in stats['recent_calls']:
        print(f"  {phone} @ {when} | {notes or '(no notes)'}")
    print()
    print("PHASE TRANSITION RULE:")
    print("  If calls >= 10/week (1.4/day avg) → Move to Phase B")
    print("  Current: {:.1f} calls/week → {}".format(
        stats['total'] * 7 / 7,
        "Ready for Phase B" if stats['total'] >= 10 else "Stay Phase A (human only)"
    ))
    print("=" * 60)
