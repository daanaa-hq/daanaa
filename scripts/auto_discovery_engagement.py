#!/usr/bin/env python3
"""
Automatic Discovery Outreach System

When an org gets discovered by supporters, reach out with proof.
Non-pushy, evidence-based, optional.

Runs daily via cron.
"""
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

DB_PATH = Path(__file__).parent.parent / "data" / "merit_registry.db"
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
FROM_EMAIL = os.environ.get("FROM_EMAIL", "hello@daanaa.org")
MAX_OUTREACH_PER_DAY = 50  # Pace the outreach

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_org_email(db, ein):
    """Find the best email for an org (IRS, claimed, website)."""

    # 1. Check if org has claimed email
    claimed = db.execute(
        "SELECT email FROM org_claims WHERE ein=? AND claim_status='verified'",
        (ein,)
    ).fetchone()
    if claimed and claimed['email']:
        return claimed['email'], 'claimed'

    # 2. Check website contact form
    website_contact = db.execute(
        "SELECT volunteer_url FROM registry_enriched WHERE EIN=?",
        (ein,)
    ).fetchone()
    if website_contact and website_contact['volunteer_url']:
        # Extract email from volunteer URL if present
        url = website_contact['volunteer_url']
        if 'mailto:' in url:
            email = url.split('mailto:')[1].split('?')[0]
            return email, 'website'

    # 3. Return None if no email found
    return None, None

def should_reach_out(db, ein):
    """Check if we should reach out to this org."""

    # Check if already reached out this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = db.execute(
        """SELECT id FROM org_outreach_log
           WHERE ein=? AND sent_at > ? AND status IN ('sent', 'opened', 'clicked')""",
        (ein, week_ago.isoformat())
    ).fetchone()

    if recent:
        return False, "Already reached out this week"

    # Check if org has already claimed profile
    claimed = db.execute(
        "SELECT id FROM org_claims WHERE ein=? AND claim_status='verified'",
        (ein,)
    ).fetchone()

    if claimed:
        return False, "Already claimed profile"

    return True, "Ready for outreach"

def get_discovery_proof(db, ein):
    """Get proof of discovery (unique visitors this week)."""

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # This would track page views (added via frontend analytics)
    # For now, return a placeholder that would be populated by analytics
    metrics = db.execute(
        """SELECT unique_visitors_week FROM org_discovery_metrics
           WHERE ein=? AND updated_at > ?""",
        (ein, week_ago.isoformat())
    ).fetchone()

    if metrics:
        return metrics['unique_visitors_week']
    return 0

def send_outreach_email(org_ein, org_name, email, unique_visitors):
    """Send discovery outreach email."""

    if not email:
        return False, "No email address"

    try:
        # Get template
        db = get_db()
        template = db.execute(
            "SELECT body_template, subject_line FROM discovery_outreach_templates WHERE template_name='first_discovery' AND is_active=1"
        ).fetchone()
        db.close()

        if not template:
            return False, "No template found"

        # Populate template
        subject = template['subject_line']
        body = template['body_template'].format(
            org_name=org_name,
            unique_visitors=unique_visitors
        )

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = email
        msg.attach(MIMEText(body, 'plain'))

        # Send via SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, [email], msg.as_string())

        return True, "Sent successfully"

    except Exception as e:
        return False, f"Error: {str(e)}"

def log_outreach(db, ein, email, contact_method, success):
    """Log the outreach attempt."""

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    unique_visitors = get_discovery_proof(db, ein)

    db.execute(
        """INSERT INTO org_outreach_log
           (ein, outreach_type, contact_email, contact_method, message_template,
            unique_visitors_shown, sent_at, status)
           VALUES (?, 'discovery_proof', ?, ?, 'first_discovery', ?, ?, ?)""",
        (ein, email, contact_method, unique_visitors, now, 'sent' if success else 'pending')
    )
    db.commit()

def process_discoveries():
    """Main: find newly discovered orgs and send outreach."""

    db = get_db()

    # Get orgs with traffic this week (discovery_metrics tracks this)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    candidates = db.execute(
        """SELECT ein, organization_name, unique_visitors_week
           FROM org_discovery_metrics
           WHERE unique_visitors_week > 0
           AND updated_at > ?
           ORDER BY unique_visitors_week DESC
           LIMIT ?""",
        (week_ago.isoformat(), MAX_OUTREACH_PER_DAY)
    ).fetchall()

    outreach_count = 0

    for org in candidates:
        ein = org['ein']
        org_name = org['organization_name']
        visitors = org['unique_visitors_week']

        # Check if we should reach out
        should_reach, reason = should_reach_out(db, ein)
        if not should_reach:
            print(f"⏭️  {ein} - {reason}")
            continue

        # Get org email
        email, contact_method = get_org_email(db, ein)
        if not email:
            print(f"❌ {ein} - No email found")
            continue

        # Send outreach
        success, msg = send_outreach_email(ein, org_name, email, visitors)

        # Log it
        log_outreach(db, ein, email, contact_method, success)

        if success:
            print(f"✅ {ein} ({visitors} visitors) → {email}")
            outreach_count += 1
        else:
            print(f"⚠️  {ein} - {msg}")

    db.close()

    print(f"\n📊 Outreach complete: {outreach_count} emails sent")
    return outreach_count

if __name__ == '__main__':
    count = process_discoveries()
    sys.exit(0 if count >= 0 else 1)
