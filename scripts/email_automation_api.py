#!/usr/bin/env python3
"""
Email Automation API — Governance interface for email triggers and approvals.

Endpoints:
- GET /api/email/pending — Get pending approval emails
- POST /api/email/{id}/approve — Approve an email
- POST /api/email/{id}/reject — Reject an email
- GET /api/email/stats — Email automation stats
- POST /api/email/send-high-confidence — Manually trigger sending of high-confidence emails
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging

email_automation_bp = Blueprint('email_automation', __name__, url_prefix='/api/email')

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
logger = logging.getLogger('email_automation_api')


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


@email_automation_bp.route('/pending', methods=['GET'])
def get_pending_emails():
    """Get emails pending founder approval."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            id,
            recipient_email,
            subject,
            confidence_score,
            status,
            created_at
        FROM email_queue
        WHERE status = 'pending_approval'
        ORDER BY confidence_score DESC
    """)

    emails = [dict(row) for row in cursor.fetchall()]
    db.close()

    # Categorize by confidence
    high_med = [e for e in emails if e['confidence_score'] >= 0.75]
    medium = [e for e in emails if 0.5 <= e['confidence_score'] < 0.75]
    low = [e for e in emails if e['confidence_score'] < 0.5]

    return jsonify({
        'all_pending': emails,
        'high_medium_confidence': high_med,
        'medium_confidence': medium,
        'low_confidence': low,
        'total_pending': len(emails),
        'ready_to_send': sum(1 for e in emails if e['confidence_score'] >= 0.9),
    })


@email_automation_bp.route('/<int:email_id>/approve', methods=['POST'])
def approve_email(email_id: int):
    """Founder approves an email for sending."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE email_queue SET status = 'ready_to_send' WHERE id = ?
    """, (email_id,))

    db.commit()
    db.close()

    logger.info(f"Email {email_id} approved by founder")

    return jsonify({'status': 'approved', 'email_id': email_id})


@email_automation_bp.route('/<int:email_id>/reject', methods=['POST'])
def reject_email(email_id: int):
    """Founder rejects an email."""
    data = request.get_json()
    reason = data.get('reason', 'rejected_by_founder')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE email_queue SET status = 'rejected' WHERE id = ?
    """, (email_id,))

    db.commit()
    db.close()

    logger.info(f"Email {email_id} rejected: {reason}")

    return jsonify({'status': 'rejected', 'email_id': email_id})


@email_automation_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get email automation statistics."""
    db = get_db()
    cursor = db.cursor()

    # Get stats from past 30 days
    cursor.execute("""
        SELECT
            COUNT(*) as total_triggers,
            COUNT(CASE WHEN decision = 'queued' THEN 1 END) as queued_count,
            COUNT(CASE WHEN decision = 'sent' THEN 1 END) as sent_count,
            COUNT(CASE WHEN decision = 'rejected' THEN 1 END) as rejected_count
        FROM email_triggers
        WHERE created_at > datetime('now', '-30 days')
    """)

    trigger_stats = dict(cursor.fetchone())

    # Get email delivery stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_sent,
            COUNT(CASE WHEN delivery_status = 'delivered' THEN 1 END) as delivered,
            COUNT(CASE WHEN delivery_status = 'bounced' THEN 1 END) as bounced
        FROM email_sent_log
        WHERE sent_at > datetime('now', '-30 days')
    """)

    delivery_stats = dict(cursor.fetchone())

    # Get pending count
    cursor.execute("""
        SELECT COUNT(*) as pending FROM email_queue WHERE status = 'pending_approval'
    """)

    pending_count = cursor.fetchone()['pending']

    db.close()

    return jsonify({
        'trigger_stats': {
            'total': trigger_stats['total_triggers'],
            'queued': trigger_stats['queued_count'],
            'sent': trigger_stats['sent_count'],
            'rejected': trigger_stats['rejected_count'],
        },
        'delivery_stats': {
            'total_sent': delivery_stats['total_sent'],
            'delivered': delivery_stats['delivered'],
            'bounced': delivery_stats['bounced'],
            'delivery_rate_pct': round((delivery_stats['delivered'] / (delivery_stats['total_sent'] or 1)) * 100, 1),
        },
        'pending_approvals': pending_count,
        'period': 'last_30_days',
        'generated_at': datetime.now().isoformat(),
    })


@email_automation_bp.route('/send-high-confidence', methods=['POST'])
def send_high_confidence():
    """Manually trigger sending of all high-confidence (90%+) emails."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id FROM email_queue
        WHERE status = 'ready_to_send'
        AND confidence_score >= 0.9
    """)

    emails = cursor.fetchall()
    sent_count = 0

    for email in emails:
        try:
            # Simulate sending (in real impl, would use SendGrid)
            cursor.execute("""
                UPDATE email_queue SET status = 'sent' WHERE id = ?
            """, (email['id'],))
            sent_count += 1
        except Exception as e:
            logger.error(f"Error sending email {email['id']}: {e}")

    db.commit()
    db.close()

    logger.info(f"Sent {sent_count} high-confidence emails")

    return jsonify({
        'sent_count': sent_count,
        'message': f'Sent {sent_count} high-confidence emails (90%+ confidence)'
    })


@email_automation_bp.route('/health', methods=['GET'])
def health():
    """Health check for email automation API."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM email_queue LIMIT 1")
        db.close()
        return jsonify({'status': 'healthy'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
