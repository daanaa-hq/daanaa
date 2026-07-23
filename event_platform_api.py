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
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from functools import wraps
from flask import Blueprint, request, jsonify, current_app

event_bp = Blueprint('events', __name__, url_prefix='/api/events')

# ============================================================================
# Helper Functions
# ============================================================================

def get_db():
    """Get database connection."""
    db = sqlite3.connect(current_app.config['DATABASE'])
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
    """Get event details."""
    db = get_db()
    event = db.execute(
        'SELECT * FROM events WHERE id = ?', (event_id,)
    ).fetchone()
    db.close()

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    return jsonify(dict(event)), 200

@event_bp.route('/<event_id>', methods=['PUT'])
@require_auth
def update_event(event_id: str, user_id: str):
    """Update event details (organizer only)."""
    db = get_db()

    # Check ownership
    event = db.execute(
        'SELECT organizer_id FROM events WHERE id = ?', (event_id,)
    ).fetchone()

    if not event or event['organizer_id'] != user_id:
        db.close()
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    updates = []
    params = []

    for field in ['name', 'description', 'event_date', 'location', 'donation_url']:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])

    if updates:
        updates.append('updated_at = datetime("now")')
        params.append(event_id)

        db.execute(f'UPDATE events SET {", ".join(updates)} WHERE id = ?', params)
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

    # Check ownership
    event = db.execute(
        'SELECT organizer_id FROM events WHERE id = ?', (event_id,)
    ).fetchone()

    if not event or event['organizer_id'] != user_id:
        db.close()
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        db.execute('''
            UPDATE volunteer_hours
            SET status = 'approved', approved_by = ?, approved_at = datetime('now')
            WHERE id = ? AND event_id = ?
        ''', (user_id, hour_id, event_id))
        db.commit()
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
        'SELECT name, event_date, status FROM events WHERE id = ?', (event_id,)
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
        'SELECT name, event_date FROM events WHERE id = ?', (event_id,)
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
