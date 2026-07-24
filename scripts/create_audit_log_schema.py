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
            user_auth TEXT,  -- Firebase UID (hash or token) or 'anonymous'
            user_role TEXT,  -- 'lead', 'support', 'member', 'viewer', 'admin', NULL

            -- Organization context (EIN only, NO name/details)
            org_ein TEXT,

            -- Event context
            volunteer_event_id INTEGER,
            volunteer_context_id INTEGER,

            -- Data fields (SANITIZED, no sensitive info)
            hours_submitted DECIMAL(5,2),
            hours_approved DECIMAL(5,2),
            status TEXT,  -- 'pending', 'approved', 'rejected'

            -- Compliance fields
            ip_address_anonymized TEXT,  -- Last octet zeroed (e.g., "192.168.1.0")
            user_agent_category TEXT,  -- 'browser', 'mobile', 'unknown'

            -- Result
            success BOOLEAN,
            error_code TEXT,
            error_message TEXT,

            -- Indexes for efficient queries
            UNIQUE(id),
            INDEX event_type_timestamp (event_type, timestamp),
            INDEX org_ein_timestamp (org_ein, timestamp),
            INDEX user_auth_timestamp (user_auth, timestamp),
            INDEX volunteer_event_id (volunteer_event_id),
            CONSTRAINT valid_event_type CHECK (event_type IN (
                'volunteer_interest_submitted',
                'volunteer_interest_batch',
                'event_claimed',
                'event_claim_rejected',
                'hours_logged',
                'hours_approved',
                'hours_rejected',
                'profile_context_created',
                'profile_context_updated',
                'member_invited',
                'member_joined',
                'member_removed',
                'member_role_changed',
                'email_sent',
                'email_failed',
                'admin_query_executed',
                'discovery_queue_processed',
                'org_claimed',
                'claim_verified'
            ))
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
