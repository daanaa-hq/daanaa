"""
Student Service API Routes — Core endpoints for student volunteer discovery and service tracking
Extends: daanaa_api.py
Integrates: Firebase auth (students), existing nonprofit auth, volunteer_hours table
"""

import json
import secrets
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, List, Tuple, Optional

from flask import Blueprint, jsonify, request, abort
from flask import current_app as app
import sqlite3

# Blueprint for student service routes
student_bp = Blueprint('student_service', __name__, url_prefix='/api/student')

# ============================================================================
# UTILITIES & HELPERS
# ============================================================================

def get_db():
    """Get database connection."""
    db = sqlite3.connect('data/merit_registry.db')
    db.row_factory = sqlite3.Row
    return db

def _require_student_auth() -> str:
    """Verify Firebase student token. Returns student_id or aborts 401."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        abort(401, {'error': 'Missing or invalid Authorization header'})

    token = auth_header[7:]
    # TODO: Verify Firebase token against public certs (same as nonprofit auth)
    # For now, extract student_id from token claims
    # In production: Use Firebase Admin SDK or public key verification

    try:
        # Placeholder: In real code, decode Firebase ID token
        # import firebase_admin.auth as fb_auth
        # decoded = fb_auth.verify_id_token(token)
        # return decoded['uid']

        # For MVP: Accept any token and extract from header (will be replaced)
        firebase_uid = request.headers.get('X-Firebase-UID', '')
        if not firebase_uid:
            abort(401, {'error': 'Invalid Firebase token'})
        return firebase_uid
    except Exception as e:
        abort(401, {'error': f'Token verification failed: {str(e)}'})

def _log_audit(student_id: str, action: str, resource_type: str, resource_id: str = None,
               old_value: str = None, new_value: str = None):
    """Log action to audit trail (privacy-first: no PII, hashed IP)."""
    db = get_db()
    cursor = db.cursor()

    # Hash IP (never store full IP)
    import hashlib
    ip_address = request.remote_addr or 'unknown'
    ip_hash = 'ip_' + hashlib.sha256(ip_address.encode()).hexdigest()[:16]

    audit_id = 'aud_' + secrets.token_hex(8)

    cursor.execute('''
        INSERT INTO student_audit_log
        (audit_id, student_id, action, resource_type, resource_id, actor_type, old_value, new_value, ip_address_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (audit_id, student_id, action, resource_type, resource_id, 'student', old_value, new_value, ip_hash))

    db.commit()
    db.close()

def _generate_certificate_number() -> str:
    """Generate unique certificate validation number."""
    return 'DAANAA-' + datetime.now(timezone.utc).strftime('%Y-%m-%d') + '-' + secrets.token_hex(4).upper()

# ============================================================================
# 1. STUDENT OPPORTUNITIES — Discovery
# ============================================================================

@student_bp.route('/opportunities', methods=['GET'])
def get_opportunities():
    """
    GET /api/student/opportunities

    Student discovers volunteer opportunities.

    Query params:
    - cause (optional): Filter by cause area (e.g., 'education', 'health')
    - location_type (optional): 'in-person', 'hybrid', 'remote'
    - nonprofit_ein (optional): Find opportunities at specific nonprofit
    - sort (optional): 'recent', 'popular', 'commitment_hours'
    - page (optional): Pagination (default 1)
    - limit (optional): Per page (default 20, max 100)

    Returns: List of opportunities with enrollment status
    """
    db = get_db()
    cursor = db.cursor()

    # Get query params
    cause = request.args.get('cause', '').strip()
    location_type = request.args.get('location_type', '').strip()
    nonprofit_ein = request.args.get('nonprofit_ein', '').strip()
    sort = request.args.get('sort', 'recent')
    page = max(1, int(request.args.get('page', 1)))
    limit = min(100, int(request.args.get('limit', 20)))
    offset = (page - 1) * limit

    # Build query
    query = 'SELECT * FROM student_opportunities WHERE is_active = 1'
    params = []

    if nonprofit_ein:
        query += ' AND nonprofit_ein = ?'
        params.append(nonprofit_ein)

    if cause:
        query += ' AND cause_area LIKE ?'
        params.append(f'%{cause}%')

    if location_type:
        query += ' AND location_type = ?'
        params.append(location_type)

    # Sort
    if sort == 'commitment_hours':
        query += ' ORDER BY commitment_hours DESC'
    elif sort == 'popular':
        query += ' ORDER BY (SELECT COUNT(*) FROM student_opportunity_enrollments WHERE opportunity_id = student_opportunities.opportunity_id) DESC'
    else:  # recent
        query += ' ORDER BY created_at DESC'

    # Count total
    count_query = query.replace('SELECT *', 'SELECT COUNT(*) as count')
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']

    # Paginate
    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    cursor.execute(query, params)
    opportunities = cursor.fetchall()

    # Get student's enrollment status (if authenticated)
    student_id = None
    try:
        student_id = _require_student_auth()
    except:
        pass  # OK to view opportunities without auth

    result = []
    for opp in opportunities:
        opp_dict = dict(opp)

        # Add nonprofit name
        cursor.execute('SELECT organization_name FROM registry_enriched WHERE ein = ?', (opp['nonprofit_ein'],))
        org = cursor.fetchone()
        opp_dict['nonprofit_name'] = org['organization_name'] if org else 'Unknown Organization'

        # Add student's enrollment status if authenticated
        if student_id:
            cursor.execute(
                'SELECT status FROM student_opportunity_enrollments WHERE student_id = ? AND opportunity_id = ?',
                (student_id, opp['opportunity_id'])
            )
            enrollment = cursor.fetchone()
            opp_dict['student_enrollment_status'] = enrollment['status'] if enrollment else None
        else:
            opp_dict['student_enrollment_status'] = None

        result.append(opp_dict)

    db.close()

    return jsonify({
        'data': result,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit,
        'limit': limit
    }), 200

# ============================================================================
# 2. STUDENT SERVICE LOG — Submit/View Hours
# ============================================================================

@student_bp.route('/service-log/submit', methods=['POST'])
def submit_service_log():
    """
    POST /api/student/service-log/submit

    Student logs volunteer hours.

    Body:
    {
        "nonprofit_ein": "123456789",
        "service_date": "2026-08-15",
        "hours_claimed": 4.5,
        "activity_description": "Taught health education class",
        "supervisor_name": "Jane Smith"
    }

    Returns: Created service log with submission_status = 'submitted'
    """
    student_id = _require_student_auth()

    data = request.get_json() or {}

    # Validate required fields
    nonprofit_ein = data.get('nonprofit_ein', '').strip()
    service_date = data.get('service_date', '').strip()
    hours_claimed = data.get('hours_claimed')
    activity_description = data.get('activity_description', '').strip()
    supervisor_name = data.get('supervisor_name', '').strip()

    if not nonprofit_ein or not service_date or not hours_claimed or not activity_description:
        return jsonify({'error': 'Missing required fields: nonprofit_ein, service_date, hours_claimed, activity_description'}), 400

    # Validate hours
    try:
        hours_claimed = float(hours_claimed)
        if hours_claimed <= 0 or hours_claimed > 24:
            return jsonify({'error': 'Hours must be between 0.5 and 24'}), 422
    except (ValueError, TypeError):
        return jsonify({'error': 'hours_claimed must be a number'}), 400

    # Validate date format (YYYY-MM-DD)
    try:
        datetime.strptime(service_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'service_date must be in YYYY-MM-DD format'}), 400

    # Validate nonprofit exists
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT ein FROM registry_enriched WHERE ein = ?', (nonprofit_ein,))
    if not cursor.fetchone():
        db.close()
        return jsonify({'error': 'Nonprofit not found'}), 404

    # Check for duplicates (same student + org + date)
    cursor.execute(
        'SELECT service_log_id FROM student_service_logs WHERE student_id = ? AND nonprofit_ein = ? AND service_date = ? AND submission_status IN ("submitted", "approved")',
        (student_id, nonprofit_ein, service_date)
    )
    if cursor.fetchone():
        db.close()
        return jsonify({'error': 'Duplicate hour submission detected (same date/org)'}), 409

    # Create service log
    service_log_id = 'sl_' + secrets.token_hex(8)

    cursor.execute('''
        INSERT INTO student_service_logs
        (service_log_id, student_id, nonprofit_ein, service_date, hours_claimed,
         activity_description, supervisor_name, submission_status, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'submitted', datetime('now'))
    ''', (service_log_id, student_id, nonprofit_ein, service_date, hours_claimed,
          activity_description, supervisor_name or None))

    db.commit()

    # Log audit
    _log_audit(student_id, 'service_log_submitted', 'service_log', service_log_id,
               new_value=f'{hours_claimed} hours at {nonprofit_ein}')

    db.close()

    return jsonify({
        'service_log_id': service_log_id,
        'submission_status': 'submitted',
        'message': 'Hours logged! Waiting for supervisor approval.',
        'expected_approval_time': '1-2 business days',
        'submitted_at': datetime.now(timezone.utc).isoformat()
    }), 201

@student_bp.route('/service-log', methods=['GET'])
def get_service_log():
    """
    GET /api/student/service-log

    Student views submitted service hours.

    Query params:
    - status (optional): Filter by submission_status
    - nonprofit_ein (optional): Filter by organization

    Returns: List of service logs with summary
    """
    student_id = _require_student_auth()

    db = get_db()
    cursor = db.cursor()

    # Get query params
    status = request.args.get('status', '').strip()
    nonprofit_ein = request.args.get('nonprofit_ein', '').strip()

    # Build query
    query = 'SELECT * FROM student_service_logs WHERE student_id = ?'
    params = [student_id]

    if status:
        query += ' AND submission_status = ?'
        params.append(status)

    if nonprofit_ein:
        query += ' AND nonprofit_ein = ?'
        params.append(nonprofit_ein)

    query += ' ORDER BY submitted_at DESC'

    cursor.execute(query, params)
    logs = cursor.fetchall()

    # Enrich with nonprofit names
    result = []
    total_submitted = 0
    total_approved = 0
    pending = 0

    for log in logs:
        log_dict = dict(log)

        # Add nonprofit name
        cursor.execute('SELECT organization_name FROM registry_enriched WHERE ein = ?', (log['nonprofit_ein'],))
        org = cursor.fetchone()
        log_dict['nonprofit_name'] = org['organization_name'] if org else 'Unknown'

        # Count totals
        if log['submission_status'] == 'approved':
            total_approved += log['hours_claimed']
        else:
            pending += 1
        total_submitted += log['hours_claimed']

        result.append(log_dict)

    db.close()

    return jsonify({
        'data': result,
        'summary': {
            'total_hours_submitted': total_submitted,
            'total_hours_approved': total_approved,
            'pending_approval': pending,
            'rejected': len([l for l in result if l['submission_status'] == 'rejected'])
        }
    }), 200

@student_bp.route('/service-log/<service_log_id>', methods=['DELETE'])
def delete_service_log(service_log_id: str):
    """
    DELETE /api/student/service-log/{service_log_id}

    Student deletes unapproved service log (right to deletion).
    Only works if submission_status = 'submitted'.
    """
    student_id = _require_student_auth()

    db = get_db()
    cursor = db.cursor()

    # Verify ownership and status
    cursor.execute(
        'SELECT submission_status FROM student_service_logs WHERE service_log_id = ? AND student_id = ?',
        (service_log_id, student_id)
    )
    log = cursor.fetchone()

    if not log:
        db.close()
        return jsonify({'error': 'Service log not found'}), 404

    if log['submission_status'] != 'submitted':
        db.close()
        return jsonify({'error': 'Can only delete unapproved logs (status=submitted)'}), 403

    # Delete
    cursor.execute('DELETE FROM student_service_logs WHERE service_log_id = ?', (service_log_id,))
    db.commit()

    # Log audit
    _log_audit(student_id, 'service_log_deleted', 'service_log', service_log_id)

    db.close()

    return '', 204

# ============================================================================
# 3. STUDENT PROFILE
# ============================================================================

@student_bp.route('/profile', methods=['GET'])
def get_student_profile():
    """
    GET /api/student/profile

    Student views their profile and enrollment status.
    """
    student_id = _require_student_auth()

    db = get_db()
    cursor = db.cursor()

    # Get student account
    cursor.execute('SELECT * FROM student_accounts WHERE student_id = ?', (student_id,))
    student = cursor.fetchone()

    if not student:
        db.close()
        return jsonify({'error': 'Student profile not found'}), 404

    # Get school name
    cursor.execute('SELECT organization_name FROM registry_enriched WHERE ein = ?', (student['school_ein'],))
    school = cursor.fetchone()
    school_name = school['organization_name'] if school else 'Unknown'

    # Get service hours stats
    cursor.execute('''
        SELECT
            COUNT(CASE WHEN submission_status IN ('submitted', 'flagged') THEN 1 END) as pending,
            SUM(CASE WHEN submission_status = 'approved' THEN hours_claimed ELSE 0 END) as total_approved,
            SUM(hours_claimed) as total_submitted
        FROM student_service_logs WHERE student_id = ?
    ''', (student_id,))
    stats = cursor.fetchone()

    # Get opportunity enrollments
    cursor.execute(
        'SELECT COUNT(*) as count FROM student_opportunity_enrollments WHERE student_id = ? AND status = "committed"',
        (student_id,)
    )
    opportunities_enrolled = cursor.fetchone()['count']

    # Get certificates
    cursor.execute(
        'SELECT COUNT(*) as count FROM student_certificates WHERE student_id = ? AND certificate_status = "active"',
        (student_id,)
    )
    certificates_earned = cursor.fetchone()['count']

    db.close()

    return jsonify({
        'student_id': student['student_id'],
        'first_name': student['first_name'],
        'last_name': student['last_name'],
        'email': student['email'],
        'school_name': school_name,
        'enrollment_status': student['enrollment_status'],
        'age_group': student['age_group'],
        'enrolled_at': student['enrolled_at'],
        'service_hours': {
            'total_submitted': stats['total_submitted'] or 0,
            'total_approved': stats['total_approved'] or 0,
            'pending': stats['pending'] or 0
        },
        'opportunities_enrolled': opportunities_enrolled,
        'certificates_earned': certificates_earned
    }), 200

# ============================================================================
# 4. STUDENT CERTIFICATE
# ============================================================================

@student_bp.route('/certificate', methods=['GET'])
def get_student_certificate():
    """
    GET /api/student/certificate

    Student views their verified service certificate.
    """
    student_id = _require_student_auth()

    db = get_db()
    cursor = db.cursor()

    # Get most recent active certificate
    cursor.execute(
        'SELECT * FROM student_certificates WHERE student_id = ? AND certificate_status = "active" ORDER BY issued_at DESC LIMIT 1',
        (student_id,)
    )
    cert = cursor.fetchone()

    if not cert:
        db.close()
        return jsonify({'message': 'No certificate yet. Log more hours to earn your verified service record.'}), 404

    # Get organizations served
    cursor.execute('''
        SELECT nonprofit_ein, nonprofit_name, hours_verified
        FROM (
            SELECT
                nonprofit_ein,
                (SELECT organization_name FROM registry_enriched WHERE ein = nonprofit_ein) as nonprofit_name,
                SUM(CASE WHEN submission_status = 'approved' THEN hours_claimed ELSE 0 END) as hours_verified
            FROM student_service_logs
            WHERE student_id = ?
            GROUP BY nonprofit_ein
        )
        WHERE hours_verified > 0
    ''', (student_id,))
    orgs = [dict(o) for o in cursor.fetchall()]

    db.close()

    return jsonify({
        'certificate_id': cert['certificate_id'],
        'certificate_number': cert['certificate_number'],
        'total_hours_verified': cert['total_hours_verified'],
        'service_period_start': cert['service_period_start'],
        'service_period_end': cert['service_period_end'],
        'issued_at': cert['issued_at'],
        'certificate_status': cert['certificate_status'],
        'organizations_served': orgs,
        'message': 'Download your verified service certificate below.',
        'download_url': '/api/student/certificate/download',
        'verification_url': f'https://daanaa.org/verify/{cert["certificate_number"]}'
    }), 200

# ============================================================================
# 5. PUBLIC VERIFICATION — No Auth Required
# ============================================================================

@student_bp.route('/verify/<certificate_number>', methods=['GET'])
def verify_certificate(certificate_number: str):
    """
    GET /api/student/verify/{certificate_number}

    Public endpoint to verify certificate authenticity.
    Student name is redacted (privacy-first).
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT * FROM student_certificates WHERE certificate_number = ?', (certificate_number,))
    cert = cursor.fetchone()

    if not cert:
        db.close()
        return jsonify({'valid': False, 'message': 'Certificate not found'}), 404

    db.close()

    # Return public info only (no student name)
    return jsonify({
        'valid': True,
        'certificate_number': cert['certificate_number'],
        'student_name': 'Redacted (privacy)',
        'total_hours': cert['total_hours_verified'],
        'issued_by': 'Daanaa Student Service Program',
        'issued_at': cert['issued_at'],
        'status': cert['certificate_status'],
        'message': 'This certificate is authentic and verified.'
    }), 200


# ============================================================================
# 7. STUDENT PROFILE — Update & manage
# ============================================================================

@student_bp.route('/profile', methods=['POST'])
def update_student_profile():
    """
    POST /api/student/profile

    Update student profile (name, contact, preferences).

    Body:
    {
      first_name?: string,
      last_name?: string,
      email?: string,
      phone?: string,
      preferred_causes?: string[],
      preferred_location_types?: string[],
      availability_hours_per_week?: number
    }
    """
    student_id = _require_student_auth()
    db = get_db()

    data = request.get_json(silent=True) or {}

    # Validate input
    first_name = (data.get('first_name') or '').strip()[:100]
    last_name = (data.get('last_name') or '').strip()[:100]
    phone = (data.get('phone') or '').strip()[:20]
    preferred_causes = data.get('preferred_causes') or []
    preferred_location_types = data.get('preferred_location_types') or []
    availability = data.get('availability_hours_per_week') or 0

    if not isinstance(preferred_causes, list) or not isinstance(preferred_location_types, list):
        return jsonify({'error': 'Invalid preferences format'}), 400

    try:
        db.execute('''
            UPDATE student_accounts
            SET first_name=?, last_name=?, phone=?,
                preferred_causes=?, preferred_location_types=?,
                availability_hours_per_week=?,
                updated_at=datetime('now')
            WHERE student_id=?
        ''', (first_name, last_name, phone,
              json.dumps(preferred_causes), json.dumps(preferred_location_types),
              availability, student_id))

        _log_audit(student_id, 'profile_update', 'student_account', student_id)
        db.commit()

        return jsonify({'status': 'updated', 'message': 'Profile updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500
    finally:
        db.close()


# ============================================================================
# 8. OPPORTUNITY ENROLLMENT — Explicit enrollment
# ============================================================================

@student_bp.route('/opportunity/<opportunity_id>/enroll', methods=['POST'])
def enroll_in_opportunity(opportunity_id: str):
    """
    POST /api/student/opportunity/{opportunity_id}/enroll

    Explicitly enroll in an opportunity (creates enrollment record).

    Body: {} (empty or optional notes)
    """
    student_id = _require_student_auth()
    db = get_db()

    data = request.get_json(silent=True) or {}
    notes = (data.get('notes') or '').strip()[:500]

    try:
        # Check opportunity exists
        opp = db.execute(
            'SELECT id, nonprofit_ein FROM student_opportunities WHERE opportunity_id=?',
            (opportunity_id,)
        ).fetchone()

        if not opp:
            return jsonify({'error': 'Opportunity not found'}), 404

        # Check not already enrolled
        existing = db.execute(
            'SELECT id FROM student_opportunity_enrollments WHERE student_id=? AND opportunity_id=?',
            (student_id, opportunity_id)
        ).fetchone()

        if existing:
            return jsonify({'status': 'already_enrolled', 'enrollment_id': existing['id']}), 200

        # Create enrollment
        enrollment_id = 'enr_' + secrets.token_hex(8)
        db.execute('''
            INSERT INTO student_opportunity_enrollments
            (enrollment_id, student_id, opportunity_id, status, notes, enrolled_at)
            VALUES (?, ?, ?, 'active', ?, datetime('now'))
        ''', (enrollment_id, student_id, opportunity_id, notes))

        _log_audit(student_id, 'enroll', 'opportunity', opportunity_id)
        db.commit()

        return jsonify({
            'status': 'enrolled',
            'enrollment_id': enrollment_id,
            'message': 'Successfully enrolled in opportunity'
        }), 201
    except Exception as e:
        return jsonify({'error': f'Enrollment failed: {str(e)}'}), 500
    finally:
        db.close()


# ============================================================================
# 9. DISPUTES — File and resolve
# ============================================================================

@student_bp.route('/dispute', methods=['POST'])
def file_dispute():
    """
    POST /api/student/dispute

    File a dispute against a submission decision.

    Body:
    {
      service_log_id: string,
      reason: string,
      evidence?: string,
      requested_resolution?: 'review' | 'approval' | 'reversal'
    }
    """
    student_id = _require_student_auth()
    db = get_db()

    data = request.get_json(silent=True) or {}
    service_log_id = (data.get('service_log_id') or '').strip()
    reason = (data.get('reason') or '').strip()
    evidence = (data.get('evidence') or '').strip()[:2000]
    requested = (data.get('requested_resolution') or 'review').strip().lower()

    if not service_log_id or not reason:
        return jsonify({'error': 'service_log_id and reason required'}), 400

    if requested not in ['review', 'approval', 'reversal']:
        requested = 'review'

    try:
        # Verify log exists and belongs to student
        log = db.execute(
            'SELECT id, service_date, nonprofit_ein FROM student_service_logs WHERE service_log_id=? AND student_id=?',
            (service_log_id, student_id)
        ).fetchone()

        if not log:
            return jsonify({'error': 'Service log not found'}), 404

        # Check not already disputed
        existing = db.execute(
            'SELECT id FROM student_disputes WHERE service_log_id=? AND dispute_status != "resolved"',
            (service_log_id,)
        ).fetchone()

        if existing:
            return jsonify({'error': 'Dispute already pending for this submission'}), 409

        # Create dispute
        dispute_id = 'dis_' + secrets.token_hex(8)
        db.execute('''
            INSERT INTO student_disputes
            (dispute_id, student_id, service_log_id, reason, evidence, requested_resolution,
             dispute_status, filed_at)
            VALUES (?, ?, ?, ?, ?, ?, 'filed', datetime('now'))
        ''', (dispute_id, student_id, service_log_id, reason, evidence, requested))

        _log_audit(student_id, 'file_dispute', 'service_log', service_log_id)
        db.commit()

        return jsonify({
            'status': 'filed',
            'dispute_id': dispute_id,
            'message': 'Dispute filed successfully. We will review and respond within 5 business days.'
        }), 201
    except Exception as e:
        return jsonify({'error': f'Dispute filing failed: {str(e)}'}), 500
    finally:
        db.close()


@student_bp.route('/disputes', methods=['GET'])
def get_disputes():
    """
    GET /api/student/disputes

    List all disputes filed by student.

    Returns: List of disputes with status and timeline
    """
    student_id = _require_student_auth()
    db = get_db()

    try:
        disputes = db.execute('''
            SELECT
                dispute_id, service_log_id, reason, dispute_status,
                filed_at, reviewed_at, resolved_at, resolution_notes
            FROM student_disputes
            WHERE student_id=?
            ORDER BY filed_at DESC
        ''', (student_id,)).fetchall()

        return jsonify({
            'data': [{
                'dispute_id': d['dispute_id'],
                'service_log_id': d['service_log_id'],
                'reason': d['reason'],
                'status': d['dispute_status'],
                'filed_at': d['filed_at'],
                'reviewed_at': d['reviewed_at'],
                'resolved_at': d['resolved_at'],
                'resolution_notes': d['resolution_notes']
            } for d in disputes]
        }), 200
    except Exception as e:
        return jsonify({'error': f'Fetch failed: {str(e)}'}), 500
    finally:
        db.close()

# ============================================================================
# Register blueprint with Flask app
# ============================================================================
# In daanaa_api.py main(), add:
# app.register_blueprint(student_bp)
