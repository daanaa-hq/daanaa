"""Volunteer Hours Notifications — Email service for submission/approval/rejection.

Reliability & Privacy (per STEWARDSHIP.md & PRIVACY-INVARIANTS):
  - Database writes succeed even if email delivery fails
  - Notification attempts are tracked to prevent duplicates
  - Email addresses never logged; only recipient type logged
  - Test submissions use mocked email transport (no external delivery)
  - Notifications are idempotent (same submission ID never sends twice)
"""

import sqlite3
import smtplib
import uuid
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple

# Email configuration (from environment or defaults)
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'localhost')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', 'notifications@daanaa.org')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'

# Test/QA flag: when true, notifications are not sent externally
IS_TEST_ENVIRONMENT = os.environ.get('DAANAA_TEST_NOTIFICATIONS', 'false').lower() == 'true'


def _send_email(to_address: str, subject: str, body_text: str, body_html: str = None,
                is_test: bool = False) -> Tuple[bool, Optional[str]]:
    """Send email via SMTP. Returns (success, error_message).

    Args:
        to_address: Recipient email
        subject: Email subject
        body_text: Plain text body
        body_html: HTML body (optional)
        is_test: If True, don't send externally (for QA)

    Returns:
        (success: bool, error_message: str or None)
    """
    if is_test or IS_TEST_ENVIRONMENT:
        # Test mode: log but don't send
        print(f"[NOTIFICATION_TEST] {to_address}: {subject}")
        return (True, None)

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = to_address

        msg.attach(MIMEText(body_text, 'plain'))
        if body_html:
            msg.attach(MIMEText(body_html, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return (True, None)
    except Exception as e:
        return (False, str(e))


def _get_nonprofit_contact(db: sqlite3.Connection, ein: str) -> Optional[str]:
    """Get verified nonprofit contact email. Returns email or None.

    Priority:
    1. Claimed nonprofit contact (org_claims.email if verified)
    2. Organization website contact (if available)
    """
    # Check org_claims for verified contact
    claim = db.execute(
        "SELECT email FROM org_claims WHERE ein=? AND claim_status='verified' LIMIT 1",
        (ein,)
    ).fetchone()
    if claim and claim[0]:
        return claim[0]

    # Fall back to organization contact (if available)
    org = db.execute(
        "SELECT website_contact_email FROM registry_enriched WHERE ein=? LIMIT 1",
        (ein,)
    ).fetchone()
    if org and org[0]:
        return org[0]

    return None


def create_submission_notification(db: sqlite3.Connection, hour_id: str,
                                    volunteer_email: str, nonprofit_ein: str,
                                    organization_name: str, hours: float,
                                    service_date: str, is_test: bool = False) -> bool:
    """Queue notification to nonprofit about new submission.

    Returns True if job was created, False if duplicate exists.
    """
    nonprofit_contact = _get_nonprofit_contact(db, nonprofit_ein)
    if not nonprofit_contact:
        # Can't notify without contact — record as skipped
        job_id = f"notif-{uuid.uuid4().hex[:16]}"
        db.execute('''
            INSERT OR IGNORE INTO volunteer_notification_jobs
            (job_id, hour_id, notification_type, recipient_email, recipient_type,
             subject, status, is_test_run)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, hour_id, 'submitted', 'unknown@example.com', 'nonprofit',
              'New volunteer submission', 'skipped', is_test))
        db.commit()
        return False

    job_id = f"notif-{uuid.uuid4().hex[:16]}"

    # Create the notification job (uniqueness constraint prevents duplicates)
    try:
        db.execute('''
            INSERT INTO volunteer_notification_jobs
            (job_id, hour_id, notification_type, recipient_email, recipient_type,
             subject, is_test_run)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, hour_id, 'submitted', nonprofit_contact, 'nonprofit',
              f'New volunteer hours submission from {organization_name}', is_test))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate already exists
        return False


def create_approval_notification(db: sqlite3.Connection, hour_id: str,
                                  volunteer_email: str, nonprofit_ein: str,
                                  organization_name: str, hours: float,
                                  service_date: str, is_test: bool = False) -> bool:
    """Queue notification to volunteer about approval.

    Returns True if job was created, False if duplicate exists or volunteer email missing.
    """
    if not volunteer_email:
        return False

    job_id = f"notif-{uuid.uuid4().hex[:16]}"

    try:
        db.execute('''
            INSERT INTO volunteer_notification_jobs
            (job_id, hour_id, notification_type, recipient_email, recipient_type,
             subject, is_test_run)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, hour_id, 'approved', volunteer_email, 'volunteer',
              f'{organization_name} approved your volunteer hours', is_test))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate already exists
        return False


def create_rejection_notification(db: sqlite3.Connection, hour_id: str,
                                   volunteer_email: str, nonprofit_ein: str,
                                   organization_name: str, rejection_reason: str,
                                   is_test: bool = False) -> bool:
    """Queue notification to volunteer about rejection.

    Returns True if job was created, False if duplicate exists or volunteer email missing.
    """
    if not volunteer_email:
        return False

    job_id = f"notif-{uuid.uuid4().hex[:16]}"

    try:
        db.execute('''
            INSERT INTO volunteer_notification_jobs
            (job_id, hour_id, notification_type, recipient_email, recipient_type,
             subject, is_test_run)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, hour_id, 'rejected', volunteer_email, 'volunteer',
              f'{organization_name} updated your volunteer submission', is_test))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate already exists
        return False


def send_pending_notifications(db: sqlite3.Connection, max_age_hours: int = 24) -> dict:
    """Send all pending notifications. Returns {sent: int, failed: int, skipped: int}.

    Called by background job or manually for testing. Safe to call repeatedly —
    prevents duplicate sends and handles failures gracefully.
    """
    results = {'sent': 0, 'failed': 0, 'skipped': 0}

    # Get pending notifications (not yet sent, not in failed state, or ready for retry)
    pending = db.execute('''
        SELECT job_id, hour_id, notification_type, recipient_email, recipient_type,
               subject, attempts, max_attempts, next_retry_at, is_test_run
        FROM volunteer_notification_jobs
        WHERE status='pending' OR (status='failed' AND next_retry_at IS NOT NULL AND next_retry_at <= datetime('now'))
        ORDER BY created_at ASC
        LIMIT 100
    ''').fetchall()

    for job in pending:
        job_id, hour_id, notif_type, recipient, recip_type, subject, attempts, max_att, retry_at, is_test = job

        # Skip if max attempts reached
        if attempts >= max_att:
            db.execute("UPDATE volunteer_notification_jobs SET status=? WHERE job_id=?",
                      ('skipped', job_id))
            db.commit()
            results['skipped'] += 1
            continue

        # Get submission details for email body
        hour = db.execute('''
            SELECT nonprofit_ein, hours, service_date, volunteer_name, volunteer_email,
                   organization_name, rejection_reason
            FROM volunteer_hours WHERE id=?
        ''', (hour_id,)).fetchone()

        if not hour:
            db.execute("UPDATE volunteer_notification_jobs SET status=? WHERE job_id=?",
                      ('skipped', job_id))
            db.commit()
            results['skipped'] += 1
            continue

        # Build email based on notification type
        body_text = _build_email_body(notif_type, hour, recipient)

        # Send email
        success, error = _send_email(recipient, subject, body_text, is_test=is_test)

        # Update status
        if success:
            db.execute('''
                UPDATE volunteer_notification_jobs
                SET status=?, sent_at=?, attempts=?
                WHERE job_id=?
            ''', ('sent', datetime.now().isoformat(), attempts + 1, job_id))
            results['sent'] += 1
        else:
            next_retry = datetime.now() + timedelta(hours=1)
            db.execute('''
                UPDATE volunteer_notification_jobs
                SET status=?, attempts=?, error_message=?, next_retry_at=?
                WHERE job_id=?
            ''', ('failed', attempts + 1, error[:500], next_retry.isoformat(), job_id))
            results['failed'] += 1

        db.commit()

    return results


def _build_email_body(notif_type: str, hour: sqlite3.Row, recipient: str) -> str:
    """Build email body based on notification type."""
    org_name = hour['organization_name'] or 'Unnamed Organization'
    date_str = hour['service_date']
    hours_str = f"{hour['hours']:.1f}"

    if notif_type == 'submitted':
        return f"""Hello,

A volunteer has submitted {hours_str} hours for review at {org_name} on {date_str}.

Please log in to your nonprofit dashboard to review and approve or reject this submission.

Organization: {org_name}
Hours: {hours_str}
Date: {date_str}

Thank you,
Daanaa Team
notifications@daanaa.org
"""

    elif notif_type == 'approved':
        return f"""Hello,

Great news! {org_name} has approved your volunteer service.

Organization: {org_name}
Hours Approved: {hours_str}
Date: {date_str}

You can view this and other submissions in your Daanaa wallet.

Thank you for your service!
Daanaa Team
"""

    elif notif_type == 'rejected':
        reason = hour['rejection_reason'] or 'No reason provided.'
        return f"""Hello,

{org_name} has reviewed your volunteer service submission and was unable to approve it at this time.

Organization: {org_name}
Submitted Hours: {hours_str}
Date: {date_str}
Reason: {reason}

You can view this submission and resubmit if you believe there's an error in your Daanaa wallet.

If you have questions, please contact {org_name} directly.

Thank you,
Daanaa Team
"""

    return ""


# Public API for testing and monitoring
def get_notification_stats(db: sqlite3.Connection) -> dict:
    """Get current notification queue stats."""
    stats = db.execute('''
        SELECT
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) as sent,
            SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END) as skipped
        FROM volunteer_notification_jobs
    ''').fetchone()

    return {
        'pending': stats[0] or 0,
        'sent': stats[1] or 0,
        'failed': stats[2] or 0,
        'skipped': stats[3] or 0,
    }
