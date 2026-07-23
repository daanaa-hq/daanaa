"""Event Claiming & Nonprofit Ownership API

Enables nonprofits to verify and manage AI-discovered events.
- POST /api/events/{event_id}/claim — Initiate claim (send verification email)
- GET /api/events/claim-verify/{token} — Verify claim via email link
- GET /api/nonprofit/dashboard — Nonprofit dashboard (claimed events, hours, volunteers)
- GET /api/nonprofit/events/{event_id} — Event detail for nonprofit organizer
"""

import sqlite3
import json
import secrets
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from flask import Blueprint, request, jsonify
from functools import wraps

claiming_bp = Blueprint('claiming', __name__, url_prefix='/api')

DB_PATH = os.environ.get("LIVE_DB_PATH", os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/daanaa_live.db")))

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def require_ein(f):
    """Decorator to require EIN header (nonprofit authentication)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        ein = request.headers.get('X-Nonprofit-EIN', '')
        if not ein or len(ein) != 9:
            return jsonify({'error': 'Missing or invalid X-Nonprofit-EIN header'}), 401
        kwargs['ein'] = ein
        return f(*args, **kwargs)
    return decorated

# ============================================================================
# Claim Initiation
# ============================================================================

@claiming_bp.route('/events/<event_id>/claim', methods=['POST'])
def initiate_claim(event_id: str):
    """Nonprofit director initiates event claim by providing email.

    Sends verification email with one-time token.
    """
    data = request.get_json()

    if not data or 'email' not in data:
        return jsonify({'error': 'Missing email'}), 400

    director_email = data['email']
    db = get_db()

    try:
        # Get event details
        event = db.execute(
            'SELECT id, short_id, title, ein FROM volunteer_events WHERE id = ? OR short_id = ?',
            (event_id, event_id)
        ).fetchone()

        if not event:
            db.close()
            return jsonify({'error': 'Event not found'}), 404

        # Prevent duplicate claims
        existing = db.execute(
            'SELECT id FROM event_claims WHERE event_id = ? AND status = ?',
            (event['id'], 'verified')
        ).fetchone()

        if existing:
            db.close()
            return jsonify({'error': 'This event has already been claimed'}), 409

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        claim_id = f"claim_{secrets.token_hex(8)}"

        # Create claim request
        db.execute('''
            INSERT INTO event_claims
            (id, event_id, ein, email, verification_token, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (claim_id, event['id'], event['ein'], director_email, verification_token))

        # Update event with pending claim
        db.execute('''
            UPDATE volunteer_events
            SET claim_verification_token = ?, claim_status = 'pending_verification'
            WHERE id = ?
        ''', (verification_token, event['id']))

        db.commit()

        # Send verification email
        try:
            from email_service_volunteer import send_email
            verification_url = f"https://daanaa.org/verify-event-claim/{verification_token}"

            email_body = f"""
            <h2>Verify Your Event on Daanaa</h2>
            <p>Hi there,</p>
            <p>We found <strong>{event['title']}</strong> on your organization's website and would like you to verify and manage it on Daanaa.</p>

            <p><strong>When you verify this event, you can:</strong></p>
            <ul>
              <li>Accept volunteer registrations through Daanaa</li>
              <li>Track and approve volunteer hours</li>
              <li>See impact metrics and volunteer participation</li>
              <li>Accept donations directly (we take no cut)</li>
            </ul>

            <p><strong><a href="{verification_url}" style="background: #d4af37; color: #1a472a; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Verify & Claim This Event</a></strong></p>

            <p>Or copy this link: {verification_url}</p>

            <p>This link expires in 48 hours. If you didn't request this, just ignore it.</p>
            <p>— Daanaa</p>
            """

            send_email(
                director_email,
                f"Verify: {event['title']} on Daanaa",
                email_body
            )
        except Exception as e:
            # Log error but don't fail — claim is created, resend can happen via dashboard
            pass

        db.close()
        return jsonify({
            'id': claim_id,
            'event_id': event['id'],
            'status': 'pending',
            'message': f'Verification email sent to {director_email}'
        }), 201

    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Claim Verification (Email Link)
# ============================================================================

@claiming_bp.route('/events/claim-verify/<token>', methods=['GET'])
def verify_claim(token: str):
    """Nonprofit director clicks email link to verify and claim event.

    This endpoint is called by the email link, typically from a browser.
    Sets claim_status = 'claimed', enables volunteer signup.
    """
    db = get_db()

    try:
        # Find the claim by token
        claim = db.execute(
            'SELECT id, event_id, ein, email FROM event_claims WHERE verification_token = ?',
            (token,)
        ).fetchone()

        if not claim:
            db.close()
            return jsonify({'error': 'Invalid or expired verification link'}), 404

        # Update claim status
        db.execute('''
            UPDATE event_claims
            SET status = 'verified', verified_at = datetime('now'), verification_ip = ?
            WHERE id = ?
        ''', (request.remote_addr, claim['id']))

        # Update event status
        db.execute('''
            UPDATE volunteer_events
            SET claim_status = 'claimed', claimed_by_ein = ?, claimed_by_email = ?, claimed_at = datetime('now')
            WHERE id = ?
        ''', (claim['ein'], claim['email'], claim['event_id']))

        # Log outreach conversion
        db.execute('''
            INSERT OR IGNORE INTO outreach_log
            (id, ein, event_id, email, outreach_type, converted_at)
            VALUES (?, ?, ?, ?, 'discovery', datetime('now'))
        ''', (f"log_{secrets.token_hex(8)}", claim['ein'], claim['event_id'], claim['email']))

        # Initialize nonprofit dashboard if needed
        db.execute('''
            INSERT OR IGNORE INTO event_nonprofit_dashboard (ein)
            VALUES (?)
        ''', (claim['ein'],))

        db.commit()
        db.close()

        # Return JSON response (can also do redirect to frontend dashboard)
        return jsonify({
            'status': 'verified',
            'event_id': claim['event_id'],
            'message': 'Event verified! You can now manage it on Daanaa.',
            'redirect': f'https://daanaa.org/nonprofit/dashboard'
        }), 200

    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Nonprofit Dashboard
# ============================================================================

@claiming_bp.route('/nonprofit/dashboard', methods=['GET'])
@require_ein
def nonprofit_dashboard(ein: str):
    """Get nonprofit dashboard: claimed events, volunteers, hours, impact."""
    db = get_db()

    try:
        # Get nonprofit info
        org = db.execute(
            'SELECT name, website, cause_tags FROM registry_enriched WHERE ein = ?',
            (ein,)
        ).fetchone()

        if not org:
            db.close()
            return jsonify({'error': 'Organization not found'}), 404

        # Get claimed events
        events = db.execute('''
            SELECT
                id, short_id, title, event_date, location_city, location_state,
                claim_status, claimed_at,
                (SELECT COUNT(*) FROM event_volunteers WHERE event_id = ve.id) as volunteer_count,
                (SELECT COALESCE(SUM(hours), 0) FROM volunteer_hours WHERE event_id = ve.id AND status = 'approved') as approved_hours,
                (SELECT COALESCE(SUM(hours), 0) FROM volunteer_hours WHERE event_id = ve.id AND status = 'pending') as pending_hours
            FROM volunteer_events ve
            WHERE claimed_by_ein = ? AND claim_status = 'claimed'
            ORDER BY event_date DESC
        ''', (ein,)).fetchall()

        # Get totals
        totals = db.execute('''
            SELECT
                COUNT(DISTINCT ve.id) as event_count,
                COUNT(DISTINCT ev.volunteer_id) as total_volunteers,
                COALESCE(SUM(CASE WHEN vh.status = 'approved' THEN vh.hours ELSE 0 END), 0) as total_approved_hours,
                COALESCE(SUM(CASE WHEN vh.status = 'pending' THEN vh.hours ELSE 0 END), 0) as total_pending_hours
            FROM volunteer_events ve
            LEFT JOIN event_volunteers ev ON ve.id = ev.event_id
            LEFT JOIN volunteer_hours vh ON ve.id = vh.event_id
            WHERE ve.claimed_by_ein = ? AND ve.claim_status = 'claimed'
        ''', (ein,)).fetchone()

        # Get pending hour approvals
        pending_hours = db.execute('''
            SELECT
                vh.id, vh.event_id, vh.hours, vh.service_date, vh.job_description,
                ev.volunteer_name, ev.volunteer_email,
                ve.title as event_title
            FROM volunteer_hours vh
            JOIN event_volunteers ev ON vh.volunteer_id = ev.volunteer_id
            JOIN volunteer_events ve ON vh.event_id = ve.event_id
            WHERE ve.claimed_by_ein = ? AND vh.status = 'pending'
            ORDER BY vh.service_date DESC
            LIMIT 20
        ''', (ein,)).fetchall()

        db.close()

        return jsonify({
            'organization': {
                'ein': ein,
                'name': org['name'],
                'website': org['website'],
                'causes': json.loads(org['cause_tags']) if org['cause_tags'] else []
            },
            'totals': {
                'event_count': totals['event_count'],
                'total_volunteers': totals['total_volunteers'],
                'total_approved_hours': totals['total_approved_hours'],
                'total_pending_hours': totals['total_pending_hours']
            },
            'events': [dict(e) for e in events],
            'pending_hour_approvals': [dict(h) for h in pending_hours]
        }), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Event Detail for Nonprofit Organizer
# ============================================================================

@claiming_bp.route('/nonprofit/events/<event_id>', methods=['GET'])
@require_ein
def nonprofit_event_detail(event_id: str, ein: str):
    """Get detailed view of an event managed by nonprofit (organizer view)."""
    db = get_db()

    try:
        # Verify ownership
        event = db.execute(
            'SELECT * FROM volunteer_events WHERE (id = ? OR short_id = ?) AND claimed_by_ein = ?',
            (event_id, event_id, ein)
        ).fetchone()

        if not event:
            db.close()
            return jsonify({'error': 'Event not found or not authorized'}), 404

        # Get volunteers
        volunteers = db.execute('''
            SELECT id, volunteer_name, volunteer_email, role, status, created_at
            FROM event_volunteers
            WHERE event_id = ?
            ORDER BY created_at DESC
        ''', (event['id'],)).fetchall()

        # Get hours by status
        hours = db.execute('''
            SELECT
                id, volunteer_id, hours, job_description, service_date, status,
                (SELECT volunteer_name FROM event_volunteers WHERE volunteer_id = vh.volunteer_id LIMIT 1) as volunteer_name
            FROM volunteer_hours
            WHERE event_id = ?
            ORDER BY service_date DESC
        ''', (event['id'],)).fetchall()

        db.close()

        return jsonify({
            'event': dict(event),
            'volunteers': [dict(v) for v in volunteers],
            'hours': [dict(h) for h in hours]
        }), 200

    except Exception as e:
        db.close()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Register blueprint
# ============================================================================

def init_claiming(app):
    """Initialize claiming routes."""
    app.register_blueprint(claiming_bp)
