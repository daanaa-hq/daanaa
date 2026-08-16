#!/usr/bin/env python3
"""
Email Automation Engine — Intelligent email triggers with safe governance.

Philosophy:
- Safe defaults: auto-execute only if confidence >= 90%
- Transparency: all emails logged with confidence + reason
- Auditability: every trigger decision recorded and reviewable
- Stewardship: respect nonprofit time and attention (weekly max, no spam patterns)

Trigger Types:
1. Nonprofit Engagement Trigger — "Nonprofit interacted with carousel → nurture sequence"
2. Donor Interest Trigger — "Donor bookmarked org → org profile updated notification"
3. Action Recommendation Trigger — "New high-confidence recommendation posted → notify founder"
4. Weekly Digest Trigger — "Summary of weekly discovery activity"

Confidence Scoring:
- HIGH (90-100%): Auto-execute without asking
- MEDIUM (70-90%): Ask founder for approval before sending
- LOW (<70%): Log only, don't send (wait for feedback)
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger('email_automation')
logger.setLevel(logging.INFO)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
HELLO_DAANAA_EMAIL = 'hello@daanaa.org'


class ConfidenceLevel(Enum):
    HIGH = 0.9  # >= 90%: auto-execute
    MEDIUM = 0.7  # 70-90%: ask first
    LOW = 0.4  # < 70%: log only


class TriggerType(Enum):
    NONPROFIT_ENGAGEMENT = 'nonprofit_engagement'
    DONOR_INTEREST = 'donor_interest'
    ACTION_RECOMMENDATION = 'action_recommendation'
    WEEKLY_DIGEST = 'weekly_digest'


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


def init_email_tables():
    """Create tables for email automation tracking."""
    db = get_db()
    cursor = db.cursor()

    # Email trigger decisions (what we decided to send and why)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_type TEXT NOT NULL,
            recipient_type TEXT,
            recipient_id TEXT,
            recipient_email TEXT,
            confidence_score REAL,
            decision TEXT,
            reason TEXT,
            context TEXT,
            approved_by TEXT,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Email queue (pending approval)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_id INTEGER NOT NULL,
            recipient_email TEXT NOT NULL,
            subject TEXT,
            body TEXT,
            html_body TEXT,
            confidence_score REAL,
            status TEXT DEFAULT 'pending_approval',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trigger_id) REFERENCES email_triggers(id)
        )
    """)

    # Email sent log (for analytics)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_sent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_id INTEGER NOT NULL,
            recipient_email TEXT,
            subject TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivery_status TEXT,
            bounce_reason TEXT,
            FOREIGN KEY (trigger_id) REFERENCES email_triggers(id)
        )
    """)

    db.commit()
    db.close()


def evaluate_nonprofit_engagement(nonprofit_id: str, nonprofit_name: str, nonprofit_email: str, carousel_title: str) -> dict:
    """
    Evaluate whether to send nonprofit a "thanks for engaging" nurture email.

    High confidence if:
    - Organization engaged with carousel (real signal)
    - First engagement (warm welcome)
    - Org has valid email
    """
    db = get_db()
    cursor = db.cursor()

    # Check if we've emailed them recently (avoid spam)
    cursor.execute("""
        SELECT COUNT(*) FROM email_sent_log
        WHERE recipient_email = ?
        AND sent_at > datetime('now', '-7 days')
    """, (nonprofit_email,))

    recent_emails = cursor.fetchone()[0]

    confidence = 0.85  # Base confidence for engagement

    # Boost if first engagement
    cursor.execute("""
        SELECT COUNT(*) FROM email_triggers
        WHERE recipient_email = ? AND trigger_type = 'nonprofit_engagement'
    """, (nonprofit_email,))

    if cursor.fetchone()[0] == 0:
        confidence = 0.95  # First engagement: highest confidence

    # Reduce if we've already emailed them this week
    if recent_emails >= 2:
        confidence = 0.50  # Too many emails: risky

    db.close()

    return {
        'type': TriggerType.NONPROFIT_ENGAGEMENT.value,
        'confidence': confidence,
        'recipient': nonprofit_email,
        'reason': f"Organization engaged with '{carousel_title}' carousel",
        'template': 'nonprofit_nurture',
        'context': {
            'nonprofit_name': nonprofit_name,
            'nonprofit_id': nonprofit_id,
            'carousel_title': carousel_title,
        }
    }


def evaluate_action_recommendation(recommendation_topic: str, confidence_score: float) -> dict:
    """
    Evaluate whether to notify founder of a new high-confidence recommendation.

    High confidence if:
    - Recommendation confidence >= 85%
    - Hasn't been notified about this topic recently
    """
    db = get_db()
    cursor = db.cursor()

    # Check if we've already notified about this
    cursor.execute("""
        SELECT COUNT(*) FROM email_triggers
        WHERE recipient_type = 'founder'
        AND trigger_type = 'action_recommendation'
        AND context LIKE ?
        AND created_at > datetime('now', '-7 days')
    """, (f'%{recommendation_topic}%',))

    recent_notifications = cursor.fetchone()[0]

    confidence = confidence_score * 0.95  # Slight boost from recommendation confidence

    if recent_notifications > 0:
        confidence = confidence * 0.5  # Already notified recently

    db.close()

    return {
        'type': TriggerType.ACTION_RECOMMENDATION.value,
        'confidence': confidence,
        'recipient': 'founder',
        'recipient_email': HELLO_DAANAA_EMAIL,
        'reason': f"New {confidence_score:.0%} confidence recommendation: {recommendation_topic}",
        'template': 'recommendation_approval',
        'context': {
            'topic': recommendation_topic,
            'confidence_score': confidence_score,
        }
    }


def evaluate_weekly_digest() -> dict:
    """
    Evaluate whether to send weekly summary digest.

    High confidence if:
    - We have activity to report (discovery, recommendations, engagement)
    - It's been 7 days since last digest
    """
    db = get_db()
    cursor = db.cursor()

    # Check activity from past week
    cursor.execute("""
        SELECT
            COUNT(*) as total_events,
            (SELECT COUNT(*) FROM recommendations WHERE created_at > datetime('now', '-7 days') AND status = 'pending') as pending_recs,
            (SELECT COUNT(*) FROM carousel_metrics WHERE posted_at > datetime('now', '-7 days')) as new_carousels
        FROM email_triggers
        WHERE created_at > datetime('now', '-7 days')
    """)

    stats = dict(cursor.fetchone())

    # Check when last digest was sent
    cursor.execute("""
        SELECT sent_at FROM email_sent_log
        WHERE subject LIKE '%Weekly Summary%'
        ORDER BY sent_at DESC
        LIMIT 1
    """)

    last_digest = cursor.fetchone()
    days_since = 7  # Default if none
    if last_digest:
        last_sent = datetime.fromisoformat(last_digest['sent_at'])
        days_since = (datetime.now() - last_sent).days

    # High confidence if: 7+ days passed AND have content
    confidence = 0.95 if (days_since >= 7 and stats['total_events'] > 0) else 0.3

    db.close()

    return {
        'type': TriggerType.WEEKLY_DIGEST.value,
        'confidence': confidence,
        'recipient': 'founder',
        'recipient_email': HELLO_DAANAA_EMAIL,
        'reason': f"{stats['total_events']} events, {stats['pending_recs']} pending recommendations, {stats['new_carousels']} new carousels",
        'template': 'weekly_digest',
        'context': stats,
    }


def log_trigger_decision(trigger_eval: dict, decision: str, approved_by: str = 'system'):
    """Log a trigger evaluation and the decision made."""
    db = get_db()
    cursor = db.cursor()

    context = json.dumps(trigger_eval.get('context', {}))

    cursor.execute("""
        INSERT INTO email_triggers
        (trigger_type, recipient_type, recipient_email, confidence_score, decision, reason, context, approved_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trigger_eval['type'],
        trigger_eval.get('recipient_type', 'nonprofit'),
        trigger_eval.get('recipient_email', 'unknown'),
        trigger_eval.get('confidence', 0),
        decision,
        trigger_eval.get('reason', ''),
        context,
        approved_by,
    ))

    db.commit()
    db.close()


def queue_email(trigger_eval: dict):
    """Queue an email for sending (either now or after approval)."""
    db = get_db()
    cursor = db.cursor()

    confidence = trigger_eval.get('confidence', 0)

    # Generate email content
    subject = _generate_subject(trigger_eval['template'], trigger_eval.get('context', {}))
    body, html_body = _generate_email_body(trigger_eval['template'], trigger_eval.get('context', {}))

    # Log the trigger decision
    log_trigger_decision(trigger_eval, 'queued')

    # Get the trigger ID we just created
    cursor.execute("SELECT last_insert_rowid()")
    trigger_id = cursor.fetchone()[0]

    # Queue the email
    status = 'ready_to_send' if confidence >= ConfidenceLevel.HIGH.value else 'pending_approval'

    cursor.execute("""
        INSERT INTO email_queue
        (trigger_id, recipient_email, subject, body, html_body, confidence_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        trigger_id,
        trigger_eval.get('recipient_email'),
        subject,
        body,
        html_body,
        confidence,
        status,
    ))

    db.commit()
    db.close()

    logger.info(f"Queued email: {subject} ({confidence:.0%} confidence)")


def send_queued_emails_high_confidence():
    """Send all queued emails with >= 90% confidence (no approval needed)."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, trigger_id, recipient_email, subject, html_body, confidence_score
        FROM email_queue
        WHERE status = 'ready_to_send'
    """)

    emails = cursor.fetchall()

    sent_count = 0
    for email in emails:
        try:
            # Send email (will be mocked in dev)
            success = _send_email(email['recipient_email'], email['subject'], email['html_body'])

            if success:
                cursor.execute("""
                    UPDATE email_queue SET status = 'sent' WHERE id = ?
                """, (email['id'],))

                cursor.execute("""
                    INSERT INTO email_sent_log (trigger_id, recipient_email, subject, delivery_status)
                    VALUES (?, ?, ?, 'delivered')
                """, (email['trigger_id'], email['recipient_email'], email['subject']))

                logger.info(f"Sent: {email['subject']} to {email['recipient_email']}")
                sent_count += 1
            else:
                cursor.execute("""
                    UPDATE email_queue SET status = 'failed' WHERE id = ?
                """, (email['id'],))

        except Exception as e:
            logger.error(f"Error sending email {email['id']}: {e}")
            cursor.execute("""
                UPDATE email_queue SET status = 'error' WHERE id = ?
            """, (email['id'],))

    db.commit()
    db.close()

    logger.info(f"Sent {sent_count} high-confidence emails")
    return sent_count


def get_pending_approvals():
    """Get list of emails pending founder approval."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, recipient_email, subject, confidence_score, created_at
        FROM email_queue
        WHERE status = 'pending_approval'
        ORDER BY confidence_score DESC
    """)

    approvals = [dict(row) for row in cursor.fetchall()]
    db.close()

    return approvals


def approve_email(email_id: int):
    """Founder approves an email for sending."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE email_queue SET status = 'ready_to_send' WHERE id = ?
    """, (email_id,))

    db.commit()
    db.close()

    logger.info(f"Email {email_id} approved for sending")


def reject_email(email_id: int, reason: str = 'rejected_by_founder'):
    """Founder rejects an email."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE email_queue SET status = 'rejected' WHERE id = ?
    """, (email_id,))

    db.commit()
    db.close()

    logger.info(f"Email {email_id} rejected: {reason}")


def _generate_subject(template: str, context: dict) -> str:
    """Generate email subject based on template type."""
    if template == 'nonprofit_nurture':
        return f"Thanks for exploring {context.get('carousel_title', 'Daanaa')}"
    elif template == 'recommendation_approval':
        return f"New carousel recommendation: {context.get('topic', 'Daanaa')}"
    elif template == 'weekly_digest':
        return f"Daanaa Weekly Summary — {datetime.now().strftime('%b %d')}"
    else:
        return "Message from Daanaa"


def _generate_email_body(template: str, context: dict) -> tuple:
    """Generate email body (plain text + HTML). Returns (text, html)."""
    if template == 'nonprofit_nurture':
        text = f"""Hi {context.get('nonprofit_name', 'there')},

Thanks for checking out Daanaa and exploring the {context.get('carousel_title', 'latest')} carousel.

If you have questions about your financial profile or want to keep exploring the directory, just let us know.

Cheers,
Daanaa"""

        html = f"""
<p>Hi {context.get('nonprofit_name', 'there')},</p>
<p>Thanks for checking out Daanaa and exploring the <strong>{context.get('carousel_title', 'latest')}</strong> carousel.</p>
<p>If you have questions about your financial profile or want to keep exploring the directory, just let us know.</p>
<p>Cheers,<br>Daanaa</p>
"""

    elif template == 'recommendation_approval':
        text = f"""New carousel recommendation pending approval:

Topic: {context.get('topic', 'Untitled')}
Confidence: {context.get('confidence_score', 0):.0%}

Visit the dashboard to approve or modify: /dashboards

— Daanaa Learning Engine"""

        html = f"""
<p><strong>New Carousel Recommendation:</strong></p>
<p><strong>Topic:</strong> {context.get('topic', 'Untitled')}<br>
<strong>Confidence:</strong> {context.get('confidence_score', 0):.0%}</p>
<p><a href="/dashboards">Review in Dashboard</a></p>
<p>— Daanaa Learning Engine</p>
"""

    else:
        text = "Message from Daanaa"
        html = "<p>Message from Daanaa</p>"

    return text, html


def _send_email(recipient: str, subject: str, html_body: str) -> bool:
    """Send email (mocked in dev, real send in prod)."""
    # TODO: Integrate with SendGrid or similar
    # For now, just log that we would send
    logger.info(f"[MOCK] Would send to {recipient}: {subject}")
    return True


# Initialize tables on import
init_email_tables()
