#!/usr/bin/env python3
"""Profile Contexts API — shared contexts for households, DAFs, businesses, etc.

Core requirements:
- One person = one private profile (Firebase UID as identity)
- Optional shared contexts (household, DAF, business, other)
- Permission roles: Lead, Support, Member, Viewer
- Wallets remain private unless explicitly shared
- No profile merging when joining a context
- No PII collection (tax docs, IDs, donation amounts, household income)

Schema:
  profile_contexts:
    context_id, context_type, created_by_uid, status, created_at

  profile_context_members:
    context_id, firebase_uid, role, status, joined_at

Endpoints:
  GET    /api/profile-contexts
  POST   /api/profile-contexts
  POST   /api/profile-contexts/<context_id>/members
  PATCH  /api/profile-contexts/<context_id>/members/<firebase_uid>
  DELETE /api/profile-contexts/<context_id>/members/<firebase_uid>
"""

import sqlite3
import secrets
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Valid context types
CONTEXT_TYPES = {"household", "daf", "business", "other"}

# Valid roles
ROLES = {"lead", "support", "member", "viewer"}

# Role hierarchy (for permission checks)
ROLE_HIERARCHY = {
    "lead": 4,
    "support": 3,
    "member": 2,
    "viewer": 1,
}

# Valid statuses
CONTEXT_STATUS = {"active", "archived", "deleted"}
MEMBER_STATUS = {"active", "invited", "removed", "declined"}


def ensure_schema(db: sqlite3.Connection) -> None:
    """Create profile contexts tables if they don't exist."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS profile_contexts (
            context_id      TEXT PRIMARY KEY,
            context_type    TEXT NOT NULL CHECK(context_type IN ('household', 'daf', 'business', 'other')),
            created_by_uid  TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived', 'deleted')),
            display_name    TEXT,
            description     TEXT,
            created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS profile_context_members (
            context_id      TEXT NOT NULL,
            firebase_uid    TEXT NOT NULL,
            role            TEXT NOT NULL CHECK(role IN ('lead', 'support', 'member', 'viewer')),
            status          TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'invited', 'removed', 'declined')),
            invited_by_uid  TEXT,
            joined_at       TEXT,
            created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (context_id, firebase_uid),
            FOREIGN KEY (context_id) REFERENCES profile_contexts(context_id)
        )
    """)

    # Indexes for common queries
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_profile_contexts_created_by
        ON profile_contexts(created_by_uid)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_profile_context_members_uid
        ON profile_context_members(firebase_uid)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_profile_context_members_status
        ON profile_context_members(context_id, status)
    """)

    db.commit()


def create_context(
    db: sqlite3.Connection,
    *,
    created_by_uid: str,
    context_type: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Create a new shared context (household, DAF, business, etc).
    Creator is automatically added as 'lead'.
    Returns context_id.
    """
    if context_type not in CONTEXT_TYPES:
        raise ValueError("invalid context_type")
    if not created_by_uid:
        raise ValueError("created_by_uid is required")

    ensure_schema(db)

    context_id = f"ctx_{secrets.token_hex(12)}"
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO profile_contexts
        (context_id, context_type, created_by_uid, display_name, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (context_id, context_type, created_by_uid, display_name, description, now, now),
    )

    # Add creator as lead
    db.execute(
        """
        INSERT INTO profile_context_members
        (context_id, firebase_uid, role, status, joined_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (context_id, created_by_uid, "lead", "active", now, now),
    )

    db.commit()
    return context_id


def get_user_contexts(db: sqlite3.Connection, firebase_uid: str) -> List[Dict[str, Any]]:
    """Get all active contexts for a user, with their role."""
    ensure_schema(db)

    rows = db.execute(
        """
        SELECT
            pc.context_id,
            pc.context_type,
            pc.display_name,
            pc.description,
            pc.status,
            pc.created_by_uid,
            pc.created_at,
            pcm.role,
            pcm.status as member_status,
            pcm.joined_at,
            (SELECT COUNT(*) FROM profile_context_members WHERE context_id=pc.context_id AND status='active') as member_count
        FROM profile_contexts pc
        JOIN profile_context_members pcm ON pc.context_id = pcm.context_id
        WHERE pcm.firebase_uid = ? AND pcm.status = 'active' AND pc.status = 'active'
        ORDER BY pc.created_at DESC
        """,
        (firebase_uid,),
    ).fetchall()

    return [dict(r) for r in rows]


def get_context_members(db: sqlite3.Connection, context_id: str) -> List[Dict[str, Any]]:
    """Get all active members of a context (with their roles)."""
    ensure_schema(db)

    rows = db.execute(
        """
        SELECT
            firebase_uid,
            role,
            status,
            joined_at,
            created_at
        FROM profile_context_members
        WHERE context_id = ? AND status IN ('active', 'invited')
        ORDER BY joined_at ASC
        """,
        (context_id,),
    ).fetchall()

    return [dict(r) for r in rows]


def add_member(
    db: sqlite3.Connection,
    *,
    context_id: str,
    firebase_uid: str,
    role: str = "member",
    invited_by_uid: str,
) -> None:
    """
    Add a member to a context (or update existing).
    Can invite (status=invited) or direct add (status=active).
    """
    if role not in ROLES:
        raise ValueError("invalid role")
    if not firebase_uid or not invited_by_uid:
        raise ValueError("firebase_uid and invited_by_uid are required")

    ensure_schema(db)

    now = datetime.now(timezone.utc).isoformat()

    # Check if context exists
    ctx = db.execute(
        "SELECT status FROM profile_contexts WHERE context_id = ?", (context_id,)
    ).fetchone()
    if not ctx:
        raise ValueError("context not found")

    # Check if inviter is a lead or support
    inviter = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=?",
        (context_id, invited_by_uid),
    ).fetchone()
    if not inviter or ROLE_HIERARCHY.get(inviter["role"], 0) < ROLE_HIERARCHY.get("support", 0):
        raise PermissionError("only lead or support can add members")

    # Insert or update
    existing = db.execute(
        "SELECT status FROM profile_context_members WHERE context_id=? AND firebase_uid=?",
        (context_id, firebase_uid),
    ).fetchone()

    if existing:
        # Reactivate if previously removed
        if existing["status"] == "removed":
            db.execute(
                "UPDATE profile_context_members SET status=?, role=?, joined_at=? WHERE context_id=? AND firebase_uid=?",
                ("active", role, now, context_id, firebase_uid),
            )
        else:
            # Update role if already active/invited
            db.execute(
                "UPDATE profile_context_members SET role=? WHERE context_id=? AND firebase_uid=?",
                (role, context_id, firebase_uid),
            )
    else:
        db.execute(
            """
            INSERT INTO profile_context_members
            (context_id, firebase_uid, role, status, invited_by_uid, joined_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (context_id, firebase_uid, role, "active", invited_by_uid, now, now),
        )

    db.commit()


def update_member_role(
    db: sqlite3.Connection,
    *,
    context_id: str,
    firebase_uid: str,
    new_role: str,
    changed_by_uid: str,
) -> None:
    """Update a member's role in a context."""
    if new_role not in ROLES:
        raise ValueError("invalid role")

    ensure_schema(db)

    # Check if changer is a lead
    changer = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=?",
        (context_id, changed_by_uid),
    ).fetchone()
    if not changer or changer["role"] != "lead":
        raise PermissionError("only lead can change roles")

    # Prevent self-demotion (lead must remain)
    if firebase_uid == changed_by_uid and new_role != "lead":
        raise ValueError("lead cannot demote themselves (transfer lead role first)")

    # Verify member exists
    member = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=?",
        (context_id, firebase_uid),
    ).fetchone()
    if not member or member["role"] == "removed":
        raise ValueError("member not found or removed")

    db.execute(
        "UPDATE profile_context_members SET role=? WHERE context_id=? AND firebase_uid=?",
        (new_role, context_id, firebase_uid),
    )
    db.commit()


def remove_member(
    db: sqlite3.Connection,
    *,
    context_id: str,
    firebase_uid: str,
    removed_by_uid: str,
) -> None:
    """Remove a member from a context (mark as removed, don't delete)."""
    ensure_schema(db)

    # Check if remover is a lead or support
    remover = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=?",
        (context_id, removed_by_uid),
    ).fetchone()
    if not remover or ROLE_HIERARCHY.get(remover["role"], 0) < ROLE_HIERARCHY.get("support", 0):
        raise PermissionError("only lead or support can remove members")

    # Prevent self-removal (lead must transfer lead role first)
    if firebase_uid == removed_by_uid:
        raise ValueError("cannot remove yourself (transfer lead role to another member first)")

    # Mark as removed
    db.execute(
        "UPDATE profile_context_members SET status=? WHERE context_id=? AND firebase_uid=?",
        ("removed", context_id, firebase_uid),
    )
    db.commit()


def archive_context(
    db: sqlite3.Connection,
    *,
    context_id: str,
    archived_by_uid: str,
) -> None:
    """Archive a context (only lead can do this)."""
    ensure_schema(db)

    # Check if archiver is the lead
    archiver = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=?",
        (context_id, archived_by_uid),
    ).fetchone()
    if not archiver or archiver["role"] != "lead":
        raise PermissionError("only lead can archive context")

    db.execute(
        "UPDATE profile_contexts SET status=? WHERE context_id=?",
        ("archived", context_id),
    )
    db.commit()


def get_context_detail(db: sqlite3.Connection, context_id: str) -> Dict[str, Any]:
    """Get full context details (if user is a member)."""
    ensure_schema(db)

    row = db.execute(
        "SELECT * FROM profile_contexts WHERE context_id=?", (context_id,)
    ).fetchone()

    if not row:
        raise ValueError("context not found")

    return dict(row)


def can_access_context(
    db: sqlite3.Connection, context_id: str, firebase_uid: str, min_role: str = "member"
) -> bool:
    """Check if a user has access to a context with at least min_role."""
    ensure_schema(db)

    member = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=? AND status='active'",
        (context_id, firebase_uid),
    ).fetchone()

    if not member:
        return False

    return ROLE_HIERARCHY.get(member["role"], 0) >= ROLE_HIERARCHY.get(min_role, 0)
