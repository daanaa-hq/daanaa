"""Volunteer hours — event-linked self-submission, impact aggregation, and export.

Builds on the existing volunteer_hours table (nonprofit-entry + claim-code flow,
already live with VolunteerApproval.tsx / nonprofit/<ein>/volunteer/pending et al).
This module adds the missing piece: a volunteer submitting their OWN hours
directly via an event's QR/short-link, no pre-existing nonprofit-entered record
required. Supports multi-nonprofit "coalition" events (one submission, hours
split across co-hosting orgs).

Stewardship alignment (see STEWARDSHIP.md, VOLUNTEER_HOURS_SYSTEM_SPEC.md):
  - Tier 2 data: volunteer name/email, visible only to the nonprofit(s) they
    helped. Never shared externally, never used for marketing.
  - Nonprofit-approved, not Daanaa-verified: we never certify accuracy. Every
    export says so explicitly.
  - 30-day edit window, then immutable (locked_at set once approved+30d old).
  - 7-year retention, then deleted by scripts/volunteer_hours_maintenance.py.
  - Approved hours bridge into impact_logs (anonymized: ein/hours/date only,
    no name/email) so they count toward the public community-impact totals
    the Wallet already powers.
"""

import csv
import io
import json
import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, Response, g, jsonify, request

# Rate limiter for public submission endpoint (DoS mitigation)
_submission_rate_limit = {}  # {ip: [(timestamp, count)]}

def _check_rate_limit(key: str, max_requests: int, window_seconds: int) -> bool:
    """Simple in-memory rate limiter. Returns True if request is allowed."""
    now = datetime.now()
    window_start = now - timedelta(seconds=window_seconds)

    if key not in _submission_rate_limit:
        _submission_rate_limit[key] = []

    # Clean expired entries
    _submission_rate_limit[key] = [
        (ts, cnt) for ts, cnt in _submission_rate_limit[key]
        if ts > window_start
    ]

    # Count requests in window
    total = sum(cnt for _, cnt in _submission_rate_limit[key])
    if total >= max_requests:
        return False

    # Record this request
    if _submission_rate_limit[key] and _submission_rate_limit[key][-1][0] == now:
        ts, cnt = _submission_rate_limit[key][-1]
        _submission_rate_limit[key][-1] = (ts, cnt + 1)
    else:
        _submission_rate_limit[key].append((now, 1))

    return True

volunteer_hours_events_bp = Blueprint('volunteer_hours_events', __name__)

DB_PATH = os.environ.get('DB_PATH', 'data/merit_registry.db')
VOLUNTEER_HOURLY_VALUE = 31.80  # Same BAL rate used in /api/impact/community-stats

_VALID_TASK_TYPES = {
    'volunteer', 'marshal', 'registration', 'setup', 'cleanup', 'hospitality',
    'tech_support', 'mentor', 'coordinator', 'other',
}


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _audit(db, hour_id: str, action: str, changed_by: str, details: dict | None = None):
    """Log a state change to volunteer_hours audit trail. Do NOT include IP addresses
    (PRIVACY-INVARIANT #3: IPs never persisted to disk, only used transiently)."""
    db.execute(
        '''INSERT INTO volunteer_hours_audit_log
           (hour_id, action, changed_by, change_details)
           VALUES (?, ?, ?, ?)''',
        (hour_id, action, changed_by, json.dumps(details) if details else None),
    )


def _bridge_to_impact_logs(db, ein: str, hours: float, service_date: str):
    """Feed an approved, anonymized hour entry into impact_logs so it counts
    toward the public community-impact totals (/api/impact/community-stats).
    No name/email here — that stays in volunteer_hours (Tier 2)."""
    log_id_note = f"volhours:{ein}:{service_date}:{secrets.token_hex(3)}"
    db.execute(
        '''INSERT INTO impact_logs (org_ein, impact_type, amount, ein, type, hours, log_date, source, verified)
           VALUES (?, 'volunteer', ?, ?, 'volunteer', ?, ?, 'volunteer_hours_event', 1)''',
        (ein, hours, ein, hours, service_date),
    )


# ── Public: event info for the submission page ──────────────────────────────

@volunteer_hours_events_bp.route('/api/events/<short_id>/log-hours-info', methods=['GET'])
def event_log_hours_info(short_id: str):
    """Public: minimal event + org info to render the hour-submission form."""
    if not re.match(r'^[A-Za-z0-9_-]{6,16}$', short_id):
        return jsonify({'error': 'Invalid event code'}), 400

    db = _get_db()
    row = db.execute(
        '''SELECT id, ein, title, event_date, location_city, location_state,
                  status, co_org_eins
           FROM volunteer_events WHERE short_id=?''',
        (short_id,),
    ).fetchone()
    if not row:
        return jsonify({'error': 'Event not found'}), 404
    if row['status'] in ('cancelled', 'expired'):
        return jsonify({'error': 'This event is no longer accepting hour submissions'}), 410

    eins = [row['ein']]
    co_eins = []
    if row['co_org_eins']:
        try:
            co_eins = [e for e in json.loads(row['co_org_eins']) if e]
        except (json.JSONDecodeError, TypeError):
            co_eins = []
    eins += [e for e in co_eins if e not in eins]

    orgs = []
    for ein in eins:
        org_row = db.execute(
            'SELECT EIN, organization_name FROM registry_enriched WHERE EIN=?', (ein,)
        ).fetchone()
        if org_row:
            orgs.append({'ein': org_row['EIN'], 'name': org_row['organization_name']})

    return jsonify({
        'event_id': row['id'],
        'title': row['title'],
        'event_date': row['event_date'],
        'location_city': row['location_city'],
        'location_state': row['location_state'],
        'orgs': orgs,
        'task_types': sorted(_VALID_TASK_TYPES),
    })


# ── Public: volunteer self-submits hours (single or multi-org) ──────────────

@volunteer_hours_events_bp.route('/api/events/<short_id>/log-hours', methods=['POST'])
def event_log_hours_submit(short_id: str):
    """Public: volunteer logs their own hours for this event, no account needed.

    DoS-protected with rate limiting (10 submissions per minute per IP).

    Body: {
      volunteer_name, volunteer_email,
      orgs: [{ein, hours, task_type?}],   -- one entry for a single-org event,
                                           -- multiple for a coalition event
      notes?
    }
    """
    # Rate limit: 10 requests per minute per IP (DoS mitigation)
    client_ip = (request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
                 or request.remote_addr or 'unknown')
    if not _check_rate_limit(client_ip, max_requests=10, window_seconds=60):
        return jsonify({'error': 'Too many submissions from this IP. Please try again in a moment.'}), 429

    if not re.match(r'^[A-Za-z0-9_-]{6,16}$', short_id):
        return jsonify({'error': 'Invalid event code'}), 400

    db = _get_db()
    event = db.execute(
        'SELECT id, ein, event_date, status, co_org_eins FROM volunteer_events WHERE short_id=?',
        (short_id,),
    ).fetchone()
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    if event['status'] in ('cancelled', 'expired'):
        return jsonify({'error': 'This event is no longer accepting hour submissions'}), 410

    valid_eins = {event['ein']}
    if event['co_org_eins']:
        try:
            valid_eins |= set(e for e in json.loads(event['co_org_eins']) if e)
        except (json.JSONDecodeError, TypeError):
            pass

    data = request.get_json(silent=True) or {}
    name = (data.get('volunteer_name') or '').strip()[:200]
    email = (data.get('volunteer_email') or '').strip()[:200]
    notes = (data.get('notes') or '').strip()[:2000]
    orgs = data.get('orgs')

    if not name or not email:
        return jsonify({'error': 'Name and email required'}), 400
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({'error': 'Valid email required'}), 400
    if not isinstance(orgs, list) or not orgs:
        return jsonify({'error': 'At least one organization + hours required'}), 400
    if len(orgs) > 10:
        return jsonify({'error': 'Too many organizations in one submission'}), 400

    validated = []
    for entry in orgs:
        if not isinstance(entry, dict):
            return jsonify({'error': 'Invalid orgs entry'}), 400
        ein = ''.join(c for c in (entry.get('ein') or '') if c.isdigit())[:10]
        try:
            hours = float(entry.get('hours') or 0)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid hours value'}), 400
        task_type = (entry.get('task_type') or 'volunteer').strip().lower()[:30]
        if task_type not in _VALID_TASK_TYPES:
            task_type = 'other'
        if ein not in valid_eins:
            return jsonify({'error': f'Organization {ein} is not part of this event'}), 400
        if not (0.25 <= hours <= 24):
            return jsonify({'error': 'Hours must be between 0.25 and 24 per organization'}), 400
        validated.append((ein, hours, task_type))

    created_ids = []
    now_iso = datetime.now().isoformat()
    ip = _client_ip()
    for ein, hours, task_type in validated:
        hour_id = f"EVT-{uuid.uuid4().hex[:16].upper()}"
        db.execute(
            '''INSERT INTO volunteer_hours (
                 id, nonprofit_ein, volunteer_name, volunteer_email, hours,
                 service_date, activity_description, status, submitted_at, created_at,
                 event_id, submitted_via, task_type, submitted_ip
               ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, 'self_qr', ?, ?)''',
            (hour_id, ein, name, email, hours, event['event_date'], notes or 'Event volunteer hours',
             now_iso, now_iso, event['id'], task_type, ip),
        )
        _audit(db, hour_id, 'submitted', 'volunteer', {'ein': ein, 'hours': hours, 'task_type': task_type})
        created_ids.append(hour_id)

    db.commit()
    return jsonify({
        'status': 'submitted',
        'submission_ids': created_ids,
        'message': 'Thanks! The organization(s) will review your hours.',
    }), 201


# ── Nonprofit: full list with status filter (all/pending/approved/rejected) ──

@volunteer_hours_events_bp.route('/api/nonprofit/<ein>/volunteer/list', methods=['GET'])
def nonprofit_volunteer_list(ein: str):
    """Firebase-auth: list volunteer hour submissions for the org's dashboard,
    filterable by status. Complements the older /volunteer/pending endpoint
    (which only returns confirmed+pending) with full history for the
    approval dashboard's All/Approved/Rejected tabs."""
    from daanaa_api import _require_firebase_user

    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = _get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid),
    ).fetchone()
    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    status = (request.args.get('status') or 'all').lower()
    valid_statuses = {'all', 'pending', 'confirmed', 'approved', 'rejected'}
    if status not in valid_statuses:
        status = 'all'

    if status == 'all':
        rows = db.execute(
            '''SELECT id, volunteer_name, volunteer_email, hours, service_date,
                      activity_description, task_type, status, submitted_at,
                      submitted_via, locked_at, edit_count
               FROM volunteer_hours WHERE nonprofit_ein=? ORDER BY submitted_at DESC LIMIT 500''',
            (ein,),
        ).fetchall()
    else:
        rows = db.execute(
            '''SELECT id, volunteer_name, volunteer_email, hours, service_date,
                      activity_description, task_type, status, submitted_at,
                      submitted_via, locked_at, edit_count
               FROM volunteer_hours WHERE nonprofit_ein=? AND status=? ORDER BY submitted_at DESC LIMIT 500''',
            (ein, status),
        ).fetchall()

    return jsonify({'records': [dict(r) for r in rows]})


# ── Nonprofit: edit within 30-day window ─────────────────────────────────────

@volunteer_hours_events_bp.route('/api/nonprofit/<ein>/volunteer/<hour_id>/edit', methods=['PATCH'])
def nonprofit_edit_hours(ein: str, hour_id: str):
    from daanaa_api import _require_firebase_user  # local import avoids circular import at module load

    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = _get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid),
    ).fetchone()
    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    row = db.execute(
        'SELECT id, locked_at, hours, task_type, activity_description FROM volunteer_hours WHERE id=? AND nonprofit_ein=?',
        (hour_id, ein),
    ).fetchone()
    if not row:
        return jsonify({'error': 'Submission not found'}), 404
    if row['locked_at']:
        return jsonify({'error': 'This submission is locked (30-day edit window has passed)'}), 409

    data = request.get_json(silent=True) or {}
    updates, vals, changes = [], [], {}
    if 'hours' in data:
        try:
            new_hours = float(data['hours'])
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid hours'}), 400
        if not (0.25 <= new_hours <= 24):
            return jsonify({'error': 'Hours must be between 0.25 and 24'}), 400
        updates.append('hours=?')
        vals.append(new_hours)
        changes['hours'] = {'old': row['hours'], 'new': new_hours}
    if 'task_type' in data:
        tt = (data['task_type'] or '').strip().lower()[:30]
        if tt not in _VALID_TASK_TYPES:
            tt = 'other'
        updates.append('task_type=?')
        vals.append(tt)
        changes['task_type'] = {'old': row['task_type'], 'new': tt}
    if 'notes' in data:
        notes = (data['notes'] or '').strip()[:2000]
        updates.append('activity_description=?')
        vals.append(notes)
        changes['notes'] = {'old': row['activity_description'], 'new': notes}

    if not updates:
        return jsonify({'error': 'No valid fields to edit'}), 400

    updates.append('edit_count=edit_count+1')
    db.execute(f"UPDATE volunteer_hours SET {', '.join(updates)} WHERE id=?", vals + [hour_id])
    _audit(db, hour_id, 'edited', uid, changes)
    db.commit()
    return jsonify({'status': 'edited'}), 200


# ── Nonprofit: yearly impact aggregation ─────────────────────────────────────

@volunteer_hours_events_bp.route('/api/nonprofit/<ein>/volunteer/impact/<int:year>', methods=['GET'])
def nonprofit_volunteer_impact(ein: str, year: int):
    from daanaa_api import _require_firebase_user

    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = _get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid),
    ).fetchone()
    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    rows = db.execute(
        '''SELECT hours, task_type, service_date, volunteer_email
           FROM volunteer_hours
           WHERE nonprofit_ein=? AND status='approved'
             AND substr(service_date, 1, 4) = ?''',
        (ein, str(year)),
    ).fetchall()

    total_hours = sum(r['hours'] for r in rows)
    volunteers = {r['volunteer_email'].lower() for r in rows if r['volunteer_email']}
    by_task: dict[str, float] = {}
    by_month: dict[str, float] = {}
    for r in rows:
        t = r['task_type'] or 'other'
        by_task[t] = round(by_task.get(t, 0) + r['hours'], 2)
        month = (r['service_date'] or '')[5:7] or '??'
        by_month[month] = round(by_month.get(month, 0) + r['hours'], 2)

    event_count = db.execute(
        '''SELECT COUNT(DISTINCT event_id) as c FROM volunteer_hours
           WHERE nonprofit_ein=? AND status='approved' AND event_id IS NOT NULL
             AND substr(service_date, 1, 4) = ?''',
        (ein, str(year)),
    ).fetchone()['c']

    cache_row = db.execute(
        'SELECT is_public FROM nonprofit_yearly_impact_cache WHERE nonprofit_ein=? AND year=?',
        (ein, year),
    ).fetchone()
    is_public = bool(cache_row['is_public']) if cache_row else False

    db.execute(
        '''INSERT INTO nonprofit_yearly_impact_cache
             (nonprofit_ein, year, total_hours_approved, volunteer_count, event_count,
              hours_by_task_type, hours_by_month, is_public, last_updated)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(nonprofit_ein, year) DO UPDATE SET
             total_hours_approved=excluded.total_hours_approved,
             volunteer_count=excluded.volunteer_count,
             event_count=excluded.event_count,
             hours_by_task_type=excluded.hours_by_task_type,
             hours_by_month=excluded.hours_by_month,
             last_updated=CURRENT_TIMESTAMP''',
        (ein, year, total_hours, len(volunteers), event_count,
         json.dumps(by_task), json.dumps(by_month), int(is_public)),
    )
    db.commit()

    return jsonify({
        'ein': ein,
        'year': year,
        'total_hours_approved': round(total_hours, 2),
        'volunteer_count': len(volunteers),
        'event_count': event_count,
        'labor_value_estimate': round(total_hours * VOLUNTEER_HOURLY_VALUE, 2),
        'hours_by_task_type': by_task,
        'hours_by_month': by_month,
        'is_public': is_public,
    })


@volunteer_hours_events_bp.route('/api/nonprofit/<ein>/volunteer/impact/<int:year>/visibility', methods=['POST'])
def nonprofit_set_impact_visibility(ein: str, year: int):
    """Opt in/out of showing this year's total hours on the public org profile."""
    from daanaa_api import _require_firebase_user

    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = _get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid),
    ).fetchone()
    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    data = request.get_json(silent=True) or {}
    is_public = bool(data.get('is_public', False))
    db.execute(
        '''INSERT INTO nonprofit_yearly_impact_cache (nonprofit_ein, year, is_public)
           VALUES (?, ?, ?)
           ON CONFLICT(nonprofit_ein, year) DO UPDATE SET is_public=excluded.is_public''',
        (ein, year, int(is_public)),
    )
    db.commit()
    return jsonify({'status': 'updated', 'is_public': is_public})


@volunteer_hours_events_bp.route('/api/public/nonprofit/<ein>/volunteer-impact', methods=['GET'])
def public_volunteer_impact(ein: str):
    """Public: nonprofit's opted-in yearly volunteer impact (aggregate only, no PII)."""
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]
    year = request.args.get('year', type=int) or datetime.now().year

    db = _get_db()
    row = db.execute(
        '''SELECT total_hours_approved, volunteer_count, event_count, is_public
           FROM nonprofit_yearly_impact_cache WHERE nonprofit_ein=? AND year=?''',
        (ein, year),
    ).fetchone()
    if not row or not row['is_public']:
        return jsonify({'error': 'Not available'}), 404

    return jsonify({
        'ein': ein,
        'year': year,
        'total_hours_approved': row['total_hours_approved'],
        'volunteer_count': row['volunteer_count'],
        'event_count': row['event_count'],
        'labor_value_estimate': round((row['total_hours_approved'] or 0) * VOLUNTEER_HOURLY_VALUE, 2),
    })


# ── Nonprofit: export (labeled "nonprofit-approved", not "Daanaa-verified") ──

@volunteer_hours_events_bp.route('/api/nonprofit/<ein>/volunteer/export', methods=['GET'])
def nonprofit_volunteer_export(ein: str):
    from daanaa_api import _require_firebase_user

    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = _get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid),
    ).fetchone()
    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    org_row = db.execute('SELECT organization_name FROM registry_enriched WHERE EIN=?', (ein,)).fetchone()
    org_name = org_row['organization_name'] if org_row else ein

    year = request.args.get('year', type=int) or datetime.now().year
    fmt = (request.args.get('format') or 'csv').lower()

    rows = db.execute(
        '''SELECT id, volunteer_name, volunteer_email, hours, service_date,
                  activity_description, task_type, status, approved_by, approved_at
           FROM volunteer_hours
           WHERE nonprofit_ein=? AND status='approved' AND substr(service_date, 1, 4)=?
           ORDER BY service_date ASC''',
        (ein, str(year)),
    ).fetchall()

    total_hours = sum(r['hours'] for r in rows)
    disclaimer = (
        "IMPORTANT: These hours were approved by nonprofit staff. "
        "Daanaa does not independently verify volunteer hours. "
        "This report is for your records only."
    )

    if fmt == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
        except ImportError:
            return jsonify({'error': 'PDF export unavailable on this server'}), 501

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph(f"Volunteer Hours Report — {org_name}", styles['Title']),
            Paragraph(f"Year: {year} | Total Approved Hours: {round(total_hours, 2)}", styles['Normal']),
            Spacer(1, 12),
            Paragraph(disclaimer, styles['Italic']),
            Spacer(1, 16),
        ]
        table_data = [['Date', 'Volunteer', 'Hours', 'Task', 'Approved By', 'Approved At']]
        for r in rows:
            table_data.append([
                r['service_date'], r['volunteer_name'], str(r['hours']),
                r['task_type'] or '', r['approved_by'] or '', (r['approved_at'] or '')[:10],
            ])
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2744')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        doc.build(elements)
        buf.seek(0)
        return Response(
            buf.read(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="volunteer_hours_{ein}_{year}.pdf"'},
        )

    # CSV (default)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([f'Volunteer Hours Report — {org_name}'])
    writer.writerow([f'Year: {year}', f'Total Approved Hours: {round(total_hours, 2)}'])
    writer.writerow([disclaimer])
    writer.writerow([])
    writer.writerow(['Date', 'Volunteer Name', 'Volunteer Email', 'Hours', 'Task', 'Notes', 'Approved By', 'Approved At'])
    for r in rows:
        writer.writerow([
            r['service_date'], r['volunteer_name'], r['volunteer_email'], r['hours'],
            r['task_type'] or '', r['activity_description'] or '', r['approved_by'] or '', r['approved_at'] or '',
        ])
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="volunteer_hours_{ein}_{year}.csv"'},
    )


# ── Nonprofit: one-time data-use acknowledgement ─────────────────────────────

@volunteer_hours_events_bp.route('/api/nonprofit/<ein>/data-agreement', methods=['GET', 'POST'])
def nonprofit_data_agreement(ein: str):
    from daanaa_api import _require_firebase_user

    uid = _require_firebase_user()
    ein = ''.join(c for c in (ein or '') if c.isdigit())[:10]
    if not ein:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = _get_db()
    claim = db.execute(
        'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
        (ein, uid),
    ).fetchone()
    if not claim:
        return jsonify({'error': 'You do not own this nonprofit'}), 403

    if request.method == 'GET':
        row = db.execute('SELECT agreed_at, agreement_version FROM nonprofit_data_agreements WHERE nonprofit_ein=?', (ein,)).fetchone()
        return jsonify({'agreed': bool(row), 'agreed_at': row['agreed_at'] if row else None})

    db.execute(
        '''INSERT INTO nonprofit_data_agreements (nonprofit_ein, agreed_by, agreement_version)
           VALUES (?, ?, 'v1')
           ON CONFLICT(nonprofit_ein) DO UPDATE SET agreed_by=excluded.agreed_by, agreed_at=CURRENT_TIMESTAMP''',
        (ein, uid),
    )
    db.commit()
    return jsonify({'status': 'agreed'}), 201
