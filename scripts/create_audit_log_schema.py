#!/usr/bin/env python3
"""
Create audit_log table for compliance tracking.

Event types logged:
- volunteer_interest_submitted
- event_claimed
- hours_logged
- hours_approved
- profile_context_created
- member_invited
- member_joined
- email_sent
- admin_query

Privacy compliance:
- NO PII in any field
- NO donor data
- NO giving history
- EIN only (NO org name)
- Firebase UID (NO email/name)
- IP anonymized (last octet zeroed)
- User agent category only (NO full string)
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"


def create_audit_log_table():
    """Create audit_log table with privacy-first constraints."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check if table exists
    c.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='audit_log'
    """)
    if c.fetchone():
        print(f"✓ audit_log table already exists at {DB_PATH}")
        conn.close()
        return True

    # Create table
    c.execute("""
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Audit metadata
            event_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            -- User context (NO PII)
            user_auth TEXT,
            user_role TEXT,

            -- Organization context (EIN only, NO name/details)
            org_ein TEXT,

            -- Event context
            volunteer_event_id INTEGER,
            volunteer_context_id INTEGER,

            -- Data fields (SANITIZED, no sensitive info)
            hours_submitted REAL,
            hours_approved REAL,
            status TEXT,

            -- Compliance fields
            ip_address_anonymized TEXT,
            user_agent_category TEXT,

            -- Result
            success BOOLEAN,
            error_code TEXT,
            error_message TEXT
        )
    """)

    conn.commit()
    print(f"✓ Created audit_log table at {DB_PATH}")

    # Create helper indexes for common queries
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_org_date
        ON audit_log(org_ein, timestamp DESC)
    """)

    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_user_date
        ON audit_log(user_auth, timestamp DESC)
    """)

    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_event_date
        ON audit_log(event_type, timestamp DESC)
    """)

    conn.commit()
    print(f"✓ Created indexes for audit_log")

    conn.close()
    return True


if __name__ == "__main__":
    try:
        create_audit_log_table()
        print(f"\n✅ Audit log schema ready: {DB_PATH}")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
