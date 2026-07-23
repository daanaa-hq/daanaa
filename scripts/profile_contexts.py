#!/usr/bin/env python3
"""Profile Contexts — Shared household & entity contexts with invitation flow.

Core requirements:
- One person = one private profile (Firebase UID)
- Optional shared contexts (household, DAF, business, other)
- Roles: Lead, Support, Member, Viewer
- Invitation flow (no silent member creation)
- UID masking in responses
- No PII collection (no display_name, description, tax docs, IDs, amounts, receipts)
- No profile merging on context join
"""

import sqlite3
import secrets
import json
from datetime import datetime, timezone, timedelta
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
MEMBER_STATUS = {"active", "removed"}
INVITATION_STATUS = {"pending", "accepted", "rejected", "expired"}

# Invitation expiry: 14 days
INVITATION_EXPIRY_DAYS = 14


def ensure_schema(db: sqlite3.Connection) -> None:
    """Create profile contexts tables if they don't exist."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS profile_contexts (
            context_id      TEXT PRIMARY KEY,
            context_type    TEXT NOT NULL CHECK(context_type IN ('household', 'daf', 'business', 'other')),
            created_by_uid  TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'archived', 'deleted')),
            created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS profile_context_members (
            context_id      TEXT NOT NULL,
            firebase_uid    TEXT NOT NULL,
            role            TEXT NOT NULL CHECK(role IN ('lead', 'support', 'member', 'viewer')),
            status          TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'removed')),
            joined_at       TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (context_id, firebase_uid),
            FOREIGN KEY (context_id) REFERENCES profile_contexts(context_id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS profile_context_invitations (
            invitation_id   TEXT PRIMARY KEY,
            context_id      TEXT NOT NULL,
            invited_uid     TEXT NOT NULL,
            invited_by_uid  TEXT NOT NULL,
            role            TEXT NOT NULL CHECK(role IN ('lead', 'support', 'member', 'viewer')),
            status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected', 'expired')),
            created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            responded_at    TEXT,
            expires_at      TEXT NOT NULL,
            FOREIGN KEY (context_id) REFERENCES profile_contexts(context_id),
            UNIQUE(context_id, invited_uid)
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

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_invitations_uid
        ON profile_context_invitations(invited_uid)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_invitations_status
        ON profile_context_invitations(context_id, status)
    """)

    db.commit()


def _mask_uid(uid: str) -> str:
    """Return masked UID for non-lead users (e.g., user_abc123...)."""
    if len(uid) < 8:
        return "user_***"
    return f"user_{uid[-6:]}"


def create_context(
    db: sqlite3.Connection,
    *,
    created_by_uid: str,
    context_type: str,
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
        (context_id, context_type, created_by_uid, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (context_id, context_type, created_by_uid, now, now),
    )

    # Add creator as lead (direct, no invitation needed)
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


def get_context_members(db: sqlite3.Connection, context_id: str, requesting_uid: str) -> List[Dict[str, Any]]:
    """Get active members of a context. Mask UIDs for non-lead users."""
    ensure_schema(db)

    # Check if requester is lead
    requester = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=? AND status='active'",
        (context_id, requesting_uid),
    ).fetchone()

    if not requester:
        raise PermissionError("not a member of this context")

    is_lead = requester["role"] == "lead"

    rows = db.execute(
        """
        SELECT
            firebase_uid,
            role,
            status,
            joined_at,
            created_at
        FROM profile_context_members
        WHERE context_id = ? AND status = 'active'
        ORDER BY joined_at ASC
        """,
        (context_id,),
    ).fetchall()

    members = []
    for r in rows:
        m = dict(r)
        # Mask UID if requester is not lead
        if not is_lead:
            m["firebase_uid"] = _mask_uid(m["firebase_uid"])
        members.append(m)

    return members


def invite_member(
    db: sqlite3.Connection,
    *,
    context_id: str,
    invited_uid: str,
    role: str = "member",
    invited_by_uid: str,
) -> str:
    """
    Create an invitation for someone to join a context.
    Inviter must be lead or support.
    Returns invitation_id.
    """
    if role not in ROLES:
        raise ValueError("invalid role")
    if not invited_uid or not invited_by_uid:
        raise ValueError("invited_uid and invited_by_uid are required")

    ensure_schema(db)

    # Check if context exists
    ctx = db.execute(
        "SELECT status FROM profile_contexts WHERE context_id = ?", (context_id,)
    ).fetchone()
    if not ctx or ctx["status"] != "active":
        raise ValueError("context not found or archived")

    # Check if inviter is lead or support
    inviter = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=? AND status='active'",
        (context_id, invited_by_uid),
    ).fetchone()
    if not inviter or ROLE_HIERARCHY.get(inviter["role"], 0) < ROLE_HIERARCHY.get("support", 0):
        raise PermissionError("only lead or support can invite members")

    # Check if already a member
    existing_member = db.execute(
        "SELECT status FROM profile_context_members WHERE context_id=? AND firebase_uid=?",
        (context_id, invited_uid),
    ).fetchone()
    if existing_member and existing_member["status"] == "active":
        raise ValueError("already a member of this context")

    # Check if invitation already pending
    existing_invite = db.execute(
        "SELECT status FROM profile_context_invitations WHERE context_id=? AND invited_uid=? AND status='pending'",
        (context_id, invited_uid),
    ).fetchone()
    if existing_invite:
        raise ValueError("invitation already pending")

    invitation_id = f"inv_{secrets.token_hex(12)}"
    now = datetime.now(timezone.utc).isoformat()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=INVITATION_EXPIRY_DAYS)).isoformat()

    db.execute(
        """
        INSERT INTO profile_context_invitations
        (invitation_id, context_id, invited_uid, invited_by_uid, role, status, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (invitation_id, context_id, invited_uid, invited_by_uid, role, "pending", now, expires_at),
    )

    db.commit()
    return invitation_id


def accept_invitation(
    db: sqlite3.Connection,
    *,
    invitation_id: str,
    accepting_uid: str,
) -> None:
    """Accept an invitation and become a member of the context."""
    ensure_schema(db)

    # Get invitation
    invite = db.execute(
        "SELECT context_id, invited_uid, role, expires_at, status FROM profile_context_invitations WHERE invitation_id=?",
        (invitation_id,),
    ).fetchone()

    if not invite:
        raise ValueError("invitation not found")

    if invite["invited_uid"] != accepting_uid:
        raise PermissionError("this invitation is not for you")

    if invite["status"] != "pending":
        raise ValueError(f"invitation already {invite['status']}")

    # Check expiry
    expires_at = datetime.fromisoformat(invite["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        db.execute(
            "UPDATE profile_context_invitations SET status=? WHERE invitation_id=?",
            ("expired", invitation_id),
        )
        db.commit()
        raise ValueError("invitation has expired")

    now = datetime.now(timezone.utc).isoformat()

    # Add as member
    db.execute(
        """
        INSERT INTO profile_context_members
        (context_id, firebase_uid, role, status, joined_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (invite["context_id"], accepting_uid, invite["role"], "active", now, now),
    )

    # Mark invitation accepted
    db.execute(
        "UPDATE profile_context_invitations SET status=?, responded_at=? WHERE invitation_id=?",
        ("accepted", now, invitation_id),
    )

    db.commit()


def reject_invitation(
    db: sqlite3.Connection,
    *,
    invitation_id: str,
    rejecting_uid: str,
) -> None:
    """Reject an invitation."""
    ensure_schema(db)

    invite = db.execute(
        "SELECT invited_uid, status FROM profile_context_invitations WHERE invitation_id=?",
        (invitation_id,),
    ).fetchone()

    if not invite:
        raise ValueError("invitation not found")

    if invite["invited_uid"] != rejecting_uid:
        raise PermissionError("this invitation is not for you")

    if invite["status"] != "pending":
        raise ValueError(f"invitation already {invite['status']}")

    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        "UPDATE profile_context_invitations SET status=?, responded_at=? WHERE invitation_id=?",
        ("rejected", now, invitation_id),
    )

    db.commit()


def get_user_invitations(db: sqlite3.Connection, firebase_uid: str) -> List[Dict[str, Any]]:
    """Get pending invitations for a user."""
    ensure_schema(db)

    rows = db.execute(
        """
        SELECT
            pci.invitation_id,
            pci.context_id,
            pci.role,
            pci.created_at,
            pci.expires_at,
            pc.context_type,
            pci.invited_by_uid
        FROM profile_context_invitations pci
        JOIN profile_contexts pc ON pci.context_id = pc.context_id
        WHERE pci.invited_uid = ? AND pci.status = 'pending' AND pci.expires_at > datetime('now')
        ORDER BY pci.created_at DESC
        """,
        (firebase_uid,),
    ).fetchall()

    return [dict(r) for r in rows]


def update_member_role(
    db: sqlite3.Connection,
    *,
    context_id: str,
    firebase_uid: str,
    new_role: str,
    changed_by_uid: str,
) -> None:
    """Update a member's role (lead only)."""
    if new_role not in ROLES:
        raise ValueError("invalid role")

    ensure_schema(db)

    # Check if changer is lead
    changer = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=? AND status='active'",
        (context_id, changed_by_uid),
    ).fetchone()
    if not changer or changer["role"] != "lead":
        raise PermissionError("only lead can change roles")

    # Prevent self-demotion
    if firebase_uid == changed_by_uid and new_role != "lead":
        raise ValueError("lead cannot demote themselves")

    # Verify member exists
    member = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=? AND status='active'",
        (context_id, firebase_uid),
    ).fetchone()
    if not member:
        raise ValueError("member not found")

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
    """Remove a member from a context (lead or support)."""
    ensure_schema(db)

    # Check if remover is lead or support
    remover = db.execute(
        "SELECT role FROM profile_context_members WHERE context_id=? AND firebase_uid=? AND status='active'",
        (context_id, removed_by_uid),
    ).fetchone()
    if not remover or ROLE_HIERARCHY.get(remover["role"], 0) < ROLE_HIERARCHY.get("support", 0):
        raise PermissionError("only lead or support can remove members")

    # Prevent self-removal
    if firebase_uid == removed_by_uid:
        raise ValueError("cannot remove yourself")

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
    """Archive a context (lead only)."""
    ensure_schema(db)

    # Check if archiver is lead
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
    """Get context details (basic public info, no sensitive data)."""
    ensure_schema(db)

    row = db.execute(
        "SELECT context_id, context_type, status, created_by_uid, created_at FROM profile_contexts WHERE context_id=?",
        (context_id,),
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
