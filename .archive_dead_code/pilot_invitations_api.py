"""Pilot invitations API — 25-org pilot signup infrastructure.

Manages invitation generation, tracking, and verification for the Daanaa nonprofit-leader pilot.
All pilot invitations are invitation-only (not open signup).
"""

import sqlite3
import secrets
import os
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from typing import Optional, Dict, List

DB_PATH = os.environ.get('DB_PATH', 'data/merit_registry.db')

pilot_invitations_bp = Blueprint('pilot_invitations', __name__)


def _get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables():
    """Create pilot invitation tables if they don't exist."""
    conn = _get_db()
    cursor = conn.cursor()

    # Pilot invitations: one per organization, tracks invite code and status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pilot_invitations (
            id TEXT PRIMARY KEY,
            ein TEXT UNIQUE NOT NULL,
            organization_name TEXT NOT NULL,
            invite_code TEXT UNIQUE NOT NULL,
            invite_link TEXT,
            email_sent_to TEXT,
            email_sent_at TEXT,
            email_opened BOOLEAN DEFAULT 0,
            email_opened_at TEXT,
            signup_started BOOLEAN DEFAULT 0,
            signup_started_at TEXT,
            signup_completed BOOLEAN DEFAULT 0,
            signup_completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # Pilot invite tokens: used for one-click signup links
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pilot_invite_tokens (
            id TEXT PRIMARY KEY,
            pilot_invitation_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT,
            used BOOLEAN DEFAULT 0,
            used_at TEXT,
            used_by_account_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pilot_invitation_id) REFERENCES pilot_invitations(id)
        )
    ''')

    conn.commit()
    conn.close()


def create_pilot_invitation(ein: str, org_name: str, email: Optional[str] = None) -> Dict:
    """
    Create a new pilot invitation for an organization.

    Args:
        ein: Organization EIN (9 digits)
        org_name: Organization name (for reference)
        email: Optional email to send invite to (not yet implemented)

    Returns:
        Dict with invitation details (id, invite_code, invite_link)
    """
    _ensure_tables()

    conn = _get_db()
    cursor = conn.cursor()

    try:
        # Check if org exists in registry
        cursor.execute('SELECT organization_name FROM registry_enriched WHERE EIN = ?', (ein,))
        org = cursor.fetchone()
        if not org:
            conn.close()
            return {'error': 'Organization not found in registry'}, 404

        # Check if already invited
        cursor.execute('SELECT id FROM pilot_invitations WHERE ein = ?', (ein,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute('SELECT invite_code, invite_link, status FROM pilot_invitations WHERE ein = ?', (ein,))
            row = cursor.fetchone()
            conn.close()
            return {
                'id': existing['id'],
                'ein': ein,
                'invite_code': row['invite_code'],
                'invite_link': row['invite_link'],
                'status': row['status'],
                'message': 'Invitation already exists',
            }

        # Create invitation
        invitation_id = str(uuid.uuid4())
        invite_code = secrets.token_urlsafe(24)  # ~180-bit entropy
        base_url = os.environ.get('DAANAA_FRONTEND_URL', 'https://daanaa.org')
        invite_link = f"{base_url}/nonprofit/pilot-signup?code={invite_code}"

        cursor.execute('''
            INSERT INTO pilot_invitations
            (id, ein, organization_name, invite_code, invite_link, email_sent_to, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (invitation_id, ein, org_name or org[0], invite_code, invite_link, email, 'pending'))

        conn.commit()
        conn.close()

        return {
            'id': invitation_id,
            'ein': ein,
            'organization_name': org_name or org[0],
            'invite_code': invite_code,
            'invite_link': invite_link,
            'status': 'pending',
        }

    except sqlite3.IntegrityError as e:
        conn.close()
        return {'error': f'Database error: {str(e)}'}, 500
    except Exception as e:
        conn.close()
        return {'error': str(e)}, 500


def get_invitation_by_code(invite_code: str) -> Optional[Dict]:
    """
    Retrieve invitation details by invite code.

    Args:
        invite_code: The invite code from the signup link

    Returns:
        Dict with invitation details or None if not found
    """
    _ensure_tables()

    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, ein, organization_name, status, created_at
        FROM pilot_invitations
        WHERE invite_code = ?
    ''', (invite_code,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        'id': row['id'],
        'ein': row['ein'],
        'organization_name': row['organization_name'],
        'status': row['status'],
        'created_at': row['created_at'],
    }


def mark_invitation_opened(invitation_id: str):
    """Mark an invitation as opened (email opened or link clicked)."""
    _ensure_tables()

    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE pilot_invitations
        SET email_opened = 1, email_opened_at = ?
        WHERE id = ? AND email_opened = 0
    ''', (datetime.utcnow().isoformat(), invitation_id))

    conn.commit()
    conn.close()


def mark_signup_started(invitation_id: str):
    """Mark that the organization has started signup via this invitation."""
    _ensure_tables()

    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE pilot_invitations
        SET signup_started = 1, signup_started_at = ?
        WHERE id = ?
    ''', (datetime.utcnow().isoformat(), invitation_id))

    conn.commit()
    conn.close()


def mark_signup_completed(invitation_id: str, account_id: str):
    """Mark that the organization has completed signup."""
    _ensure_tables()

    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE pilot_invitations
        SET signup_completed = 1, signup_completed_at = ?, status = 'completed'
        WHERE id = ?
    ''', (datetime.utcnow().isoformat(), invitation_id))

    conn.commit()
    conn.close()


@pilot_invitations_bp.route('/api/admin/pilot/invitations', methods=['GET'])
def list_pilot_invitations():
    """List all pilot invitations (admin only)."""
    _ensure_tables()

    # Check admin key
    expected_key = os.environ.get('DAANAA_ADMIN_KEY', '')
    if expected_key:
        auth = request.headers.get('Authorization', '')
        admin_key = auth.split(' ')[-1] if auth else ''
        if admin_key != expected_key:
            return jsonify({'error': 'Unauthorized'}), 401

    conn = _get_db()
    cursor = conn.cursor()

    # Get summary stats
    cursor.execute('SELECT COUNT(*) as total FROM pilot_invitations')
    total = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as count FROM pilot_invitations WHERE email_opened = 1')
    opened = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM pilot_invitations WHERE signup_started = 1')
    started = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM pilot_invitations WHERE signup_completed = 1')
    completed = cursor.fetchone()['count']

    # Get list of invitations
    cursor.execute('''
        SELECT id, ein, organization_name, invite_code, status,
               email_opened, signup_started, signup_completed, created_at
        FROM pilot_invitations
        ORDER BY created_at DESC
    ''')

    invitations = []
    for row in cursor.fetchall():
        invitations.append({
            'id': row['id'],
            'ein': row['ein'],
            'organization_name': row['organization_name'],
            'invite_code': row['invite_code'],
            'status': row['status'],
            'email_opened': bool(row['email_opened']),
            'signup_started': bool(row['signup_started']),
            'signup_completed': bool(row['signup_completed']),
            'created_at': row['created_at'],
        })

    conn.close()

    return jsonify({
        'stats': {
            'total': total,
            'email_opened': opened,
            'signup_started': started,
            'signup_completed': completed,
        },
        'invitations': invitations,
    })


@pilot_invitations_bp.route('/api/admin/pilot/create', methods=['POST'])
def admin_create_invitation():
    """Create a pilot invitation (admin only)."""
    _ensure_tables()

    # Check admin key
    expected_key = os.environ.get('DAANAA_ADMIN_KEY', '')
    if expected_key:
        auth = request.headers.get('Authorization', '')
        admin_key = auth.split(' ')[-1] if auth else ''
        if admin_key != expected_key:
            return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    ein = (data.get('ein') or '').strip()
    org_name = (data.get('organization_name') or '').strip()
    email = (data.get('email') or '').strip()

    if not ein:
        return jsonify({'error': 'EIN required'}), 400

    result = create_pilot_invitation(ein, org_name, email)

    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]

    return jsonify(result), 201


@pilot_invitations_bp.route('/api/pilot/verify-invite', methods=['POST'])
def verify_pilot_invite():
    """Verify an invite code during signup."""
    data = request.get_json() or {}
    invite_code = (data.get('code') or '').strip()

    if not invite_code:
        return jsonify({'error': 'Invite code required'}), 400

    invitation = get_invitation_by_code(invite_code)
    if not invitation:
        return jsonify({'error': 'Invalid or expired invite code'}), 404

    # Mark as opened
    mark_invitation_opened(invitation['id'])

    return jsonify({
        'valid': True,
        'ein': invitation['ein'],
        'organization_name': invitation['organization_name'],
        'invitation_id': invitation['id'],
    })


@pilot_invitations_bp.route('/api/pilot/signup-status/<invitation_id>', methods=['GET'])
def get_pilot_signup_status(invitation_id: str):
    """Get signup status for a pilot invitation."""
    _ensure_tables()

    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, ein, organization_name, status,
               email_opened, signup_started, signup_completed, created_at
        FROM pilot_invitations
        WHERE id = ?
    ''', (invitation_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Invitation not found'}), 404

    return jsonify({
        'invitation_id': row['id'],
        'ein': row['ein'],
        'organization_name': row['organization_name'],
        'status': row['status'],
        'email_opened': bool(row['email_opened']),
        'signup_started': bool(row['signup_started']),
        'signup_completed': bool(row['signup_completed']),
        'created_at': row['created_at'],
    })
