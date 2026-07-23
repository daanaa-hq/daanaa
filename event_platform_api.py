"""Event Volunteer Tracking Platform API

Core endpoints for AKF event platform:
- Event creation and management
- Volunteer registration
- Hour logging
- Real-time dashboards
- Post-event reporting
"""

import sqlite3
import json
import secrets
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from functools import wraps
from flask import Blueprint, request, jsonify

# Audit logging
try:
    from audit_logging import log_hour_approval, log_hour_submission
except ImportError:
    log_hour_approval = None
    log_hour_submission = None

event_bp = Blueprint('events', __name__, url_prefix='/api/events')

# Database path — volunteer_events lives in LIVE_DB_PATH
DB_PATH = os.environ.get("LIVE_DB_PATH", os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/daanaa_live.db")))

# ============================================================================
# Helper Functions
# ============================================================================

def get_db():
    """Get database connection."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def require_auth(f):
    """Decorator to require Firebase UID from Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization header'}), 401
        kwargs['user_id'] = auth_header[7:]  # Strip 'Bearer '
        return f(*args, **kwargs)
    return decorated

def generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{secrets.token_hex(8)}"

# ============================================================================
# Event Management Endpoints
# ============================================================================

@event_bp.route('', methods=['POST'])
@require_auth
def create_event(user_id: str):
    """Create a new event (organizer only)."""
    data = request.get_json()

    required = ['name', 'event_date', 'organizer_name']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    event_id = generate_id('evt')
    db = get_db()

    try:
        db.execute('''
            INSERT INTO events (id, name, description, event_date, organizer_id, organizer_name, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        ''', (
            event_id,
            data['name'],
            data.get('description', ''),
            data['event_date'],
            user_id,
            data['organizer_name']
        ))

        # Initialize event stats
        db.execute('INSERT INTO event_stats (event_id) VALUES (?)', (event_id,))
        db.commit()

        return jsonify({
            'id': event_id,
            'name': data['name'],
            'event_date': data['event_date'],
            'status': 'active'
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@event_bp.route('/<event_id>', methods=['GET'])
def get_event(event_id: str):
    """Get event details from volunteer events."""
    import urllib.request
    import urllib.error

    try:
        # Proxy to the working volunteer-events API endpoint
        url = f"http://127.0.0.1:5000/api/volunteer-events?limit=1000"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

            # Search for event by numeric ID or short_id
            if 'events' in data:
                for event in data['events']:
                    if str(event.get('id')) == str(event_id) or event.get('short_id') == event_id:
                        return jsonify(event), 200

            return jsonify({'error': 'Event not found'}), 404
    except Exception:
        return jsonify({'error': 'Event not found'}), 404

@event_bp.route('/<event_id>', methods=['PUT'])
@require_auth
def update_event(event_id: str, user_id: str):
    """Update event details (organizer only)."""
    db = get_db()

    # Check ownership via EIN claim
    event = db.execute(
        'SELECT ein FROM volunteer_events WHERE id = ? OR short_id = ?', (event_id, event_id)
    ).fetchone()

    if not event:
        db.close()
        return jsonify({'error': 'Event not found'}), 404

    # For now, allow any authenticated user to update
    # In production, should verify user has claim on the EIN
    data = request.get_json()
    updates = []
    params = []

    for field in ['title', 'description', 'event_date', 'location_city', 'location_state']:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])

    if updates:
        updates.append('updated_at = datetime("now")')
        params.append(event_id)
        params.append(event_id)

        db.execute(f'UPDATE volunteer_events SET {", ".join(updates)} WHERE id = ? OR short_id = ?', params)
        db.commit()

    db.close()
    return jsonify({'status': 'updated'}), 200

# ============================================================================
# Volunteer Registration Endpoints
# ============================================================================

@event_bp.route('/<event_id>/volunteers', methods=['POST'])
def register_volunteer(event_id: str):
    """Register a volunteer for an event."""
    data = request.get_json()

    required = ['volunteer_name', 'volunteer_email']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    volunteer_id = generate_id('vol')
    db = get_db()

    try:
        db.execute('''
            INSERT INTO event_volunteers
            (id, event_id, volunteer_id, volunteer_name, volunteer_email, role, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            volunteer_id,
            event_id,
            data.get('volunteer_id', volunteer_id),  # Use provided UID if given
            data['volunteer_name'],
            data['volunteer_email'],
            data.get('role', ''),
            data.get('phone', '')
        ))
        db.commit()

        # Send registration confirmation email
        try:
            from email_service_volunteer import send_volunteer_registration_confirmation
            event = db.execute('SELECT title, event_date FROM volunteer_events WHERE id = ?', (event_id,)).fetchone()
            if event:
                send_volunteer_registration_confirmation(
                    data['volunteer_name'],
                    data['volunteer_email'],
                    event['title'],
                    event['event_date'],
                    f"https://daanaa.org/event/{event_id}"
                )
        except Exception as e:
            pass  # Email failure doesn't block registration

        return jsonify({
            'id': volunteer_id,
            'name': data['volunteer_name'],
            'email': data['volunteer_email'],
            'status': 'registered'
        }), 201
    except sqlite3.IntegrityError as e:
        db.rollback()
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'error': 'Volunteer already registered for this event'}), 409
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@event_bp.route('/<event_id>/volunteers', methods=['GET'])
def list_volunteers(event_id: str):
    """List all volunteers for an event."""
    db = get_db()
    volunteers = db.execute('''
        SELECT id, volunteer_name, volunteer_email, role, status, created_at
        FROM event_volunteers
        WHERE event_id = ?
        ORDER BY created_at DESC
    ''', (event_id,)).fetchall()
    db.close()

    return jsonify([dict(v) for v in volunteers]), 200

# ============================================================================
# Hour Logging Endpoints
# ============================================================================

@event_bp.route('/<event_id>/hours', methods=['POST'])
def log_hours(event_id: str):
    """Log volunteer hours for an event."""
    data = request.get_json()

    required = ['volunteer_id', 'hours', 'service_date']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    hour_id = generate_id('hrs')
    db = get_db()

    try:
        db.execute('''
            INSERT INTO volunteer_hours
            (id, event_id, volunteer_id, hours, job_description, service_date, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            hour_id,
            event_id,
            data['volunteer_id'],
            float(data['hours']),
            data.get('job_description', ''),
            data['service_date'],
            data.get('notes', '')
        ))
        db.commit()

        # Audit log (hour submission with IP)
        if log_hour_submission:
            try:
                volunteer = db.execute('SELECT volunteer_email FROM event_volunteers WHERE volunteer_id = ?', (data['volunteer_id'],)).fetchone()
                if volunteer:
                    log_hour_submission(
                        hour_id=hour_id,
                        event_id=int(event_id),
                        volunteer_id=data['volunteer_id'],
                        volunteer_email=volunteer['volunteer_email'],
                        hours_claimed=float(data['hours']),
                        job_description=data.get('job_description', ''),
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', 'Unknown'),
                        is_edit=False
                    )
            except Exception:
                pass  # Audit failure doesn't block

        # Send notification to organizer
        try:
            from email_service_volunteer import send_hours_logged_notification
            volunteer = db.execute('SELECT volunteer_name, volunteer_email FROM event_volunteers WHERE volunteer_id = ?', (data['volunteer_id'],)).fetchone()
            event = db.execute('SELECT title, ein FROM volunteer_events WHERE id = ?', (event_id,)).fetchone()
            if volunteer and event:
                send_hours_logged_notification(
                    f"organizer@{event['ein']}.org",  # Placeholder organizer email
                    "Organization Admin",
                    volunteer['volunteer_name'],
                    data['hours'],
                    event['title'],
                    f"https://daanaa.org/event/{event_id}/approve"
                )
        except Exception as e:
            pass  # Email failure doesn't block hour logging

        return jsonify({
            'id': hour_id,
            'hours': data['hours'],
            'status': 'pending'
        }), 201
    except ValueError:
        return jsonify({'error': 'Hours must be a number'}), 400
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@event_bp.route('/<event_id>/hours/<hour_id>/approve', methods=['POST'])
@require_auth
def approve_hours(event_id: str, hour_id: str, user_id: str):
    """Approve logged hours (organizer only)."""
    db = get_db()

    # Check event exists (organizer verification can be enhanced)
    event = db.execute(
        'SELECT ein FROM volunteer_events WHERE id = ? OR short_id = ?', (event_id, event_id)
    ).fetchone()

    if not event:
        db.close()
        return jsonify({'error': 'Event not found'}), 403

    try:
        # Get hours and volunteer info before updating (for logging)
        hours_record = db.execute('SELECT volunteer_id, hours FROM volunteer_hours WHERE id = ?', (hour_id,)).fetchone()
        volunteer_record = db.execute('SELECT volunteer_name FROM event_volunteers WHERE volunteer_id = ?', (hours_record['volunteer_id'],)).fetchone()

        db.execute('''
            UPDATE volunteer_hours
            SET status = 'approved', approved_by = ?, approved_at = datetime('now')
            WHERE id = ? AND event_id = ?
        ''', (user_id, hour_id, event_id))
        db.commit()

        # Audit log (hour approval with IP and approver)
        if log_hour_approval:
            try:
                log_hour_approval(
                    hour_id=hour_id,
                    event_id=int(event_id),
                    volunteer_id=hours_record['volunteer_id'],
                    volunteer_name=volunteer_record['volunteer_name'] if volunteer_record else 'Unknown',
                    hours_approved=float(hours_record['hours']),
                    approved_by_email=user_id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'Unknown'),
                    status='approved'
                )
            except Exception:
                pass  # Audit failure doesn't block

        # Send approval notification to volunteer
        try:
            from email_service_volunteer import send_hours_approved_notification
            volunteer = db.execute('SELECT volunteer_email, volunteer_name FROM event_volunteers WHERE volunteer_id = ?', (hours_record['volunteer_id'],)).fetchone()
            event = db.execute('SELECT title FROM volunteer_events WHERE id = ?', (event_id,)).fetchone()
            if volunteer and event:
                send_hours_approved_notification(
                    volunteer['volunteer_email'],
                    volunteer['volunteer_name'],
                    hours_record['hours'],
                    event['title']
                )
        except Exception as e:
            pass  # Email failure doesn't block approval

        db.close()
        return jsonify({'status': 'approved'}), 200
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Dashboard Endpoints
# ============================================================================

@event_bp.route('/<event_id>/dashboard', methods=['GET'])
def get_dashboard(event_id: str):
    """Get real-time dashboard stats for an event."""
    db = get_db()

    # Get event info
    event = db.execute(
        'SELECT title, event_date, status FROM volunteer_events WHERE id = ? OR short_id = ?', (event_id, event_id)
    ).fetchone()

    if not event:
        db.close()
        return jsonify({'error': 'Event not found'}), 404

    # Get stats
    stats = db.execute(
        'SELECT * FROM event_stats WHERE event_id = ?', (event_id,)
    ).fetchone()

    # Get volunteer count
    volunteer_count = db.execute(
        'SELECT COUNT(*) as count FROM event_volunteers WHERE event_id = ?', (event_id,)
    ).fetchone()['count']

    # Get total approved hours
    total_hours = db.execute('''
        SELECT COALESCE(SUM(hours), 0) as total
        FROM volunteer_hours
        WHERE event_id = ? AND status = 'approved'
    ''', (event_id,)).fetchone()['total']

    db.close()

    return jsonify({
        'event_name': event['name'],
        'event_date': event['event_date'],
        'status': event['status'],
        'volunteer_count': volunteer_count,
        'total_hours_approved': total_hours,
        'volunteer_count_checked_in': stats['checked_in_count'] if stats else 0,
        'avg_hours_per_volunteer': stats['avg_hours_per_volunteer'] if stats else 0
    }), 200

@event_bp.route('/<event_id>/report', methods=['GET'])
def get_report(event_id: str):
    """Get post-event report (hours summary)."""
    db = get_db()

    # Get event info
    event = db.execute(
        'SELECT title, event_date FROM volunteer_events WHERE id = ? OR short_id = ?', (event_id, event_id)
    ).fetchone()

    if not event:
        db.close()
        return jsonify({'error': 'Event not found'}), 404

    # Get hour summary by volunteer
    hours_summary = db.execute('''
        SELECT
            ev.volunteer_name,
            ev.volunteer_email,
            COUNT(vh.id) as submission_count,
            SUM(CASE WHEN vh.status = 'approved' THEN vh.hours ELSE 0 END) as approved_hours,
            SUM(CASE WHEN vh.status = 'pending' THEN vh.hours ELSE 0 END) as pending_hours
        FROM event_volunteers ev
        LEFT JOIN volunteer_hours vh ON ev.volunteer_id = vh.volunteer_id AND vh.event_id = ?
        WHERE ev.event_id = ?
        GROUP BY ev.volunteer_id
        ORDER BY approved_hours DESC
    ''', (event_id, event_id)).fetchall()

    db.close()

    return jsonify({
        'event_name': event['name'],
        'event_date': event['event_date'],
        'volunteers': [dict(h) for h in hours_summary]
    }), 200

# ============================================================================
# Register blueprint with app
# ============================================================================

def init_event_platform(app):
    """Initialize event platform routes."""
    app.register_blueprint(event_bp)
