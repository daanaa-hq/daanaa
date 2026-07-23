#!/usr/bin/env python3
"""Nonprofit Event Outreach Campaign

Discovers unclaimed AI-generated events and sends outreach emails to nonprofits
to invite them to claim and manage the events on Daanaa.

Usage:
  python3 nonprofit_outreach_campaign.py --dry-run     # Preview emails, don't send
  python3 nonprofit_outreach_campaign.py --tier 1      # Send only to Tier 1 nonprofits
  python3 nonprofit_outreach_campaign.py --limit 50    # Send max 50 emails
"""

import sqlite3
import json
import secrets
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional

DB_PATH = os.path.expanduser("~/meritgiving/data/daanaa_live.db")
REGISTRY_DB = os.path.expanduser("~/meritgiving/data/merit_registry.db")

def get_db(path=DB_PATH):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db

def get_unclaimed_events(tier: int = 1) -> List[Dict]:
    """Get unclaimed AI-discovered events eligible for outreach.

    Tier 1: Verified contact info in registry
    Tier 2: EINs in IRS database but unverified contact
    """
    db = get_db()

    # Get unclaimed events with organizer info
    query = """
        SELECT
            ve.id,
            ve.short_id,
            ve.ein,
            ve.title,
            ve.event_date,
            ve.location_city,
            ve.location_state,
            ve.description,
            ve.source_url,
            ve.ai_generated,
            r.name as org_name,
            r.website as org_website,
            r.cause_tags
        FROM volunteer_events ve
        JOIN registry_enriched r ON ve.ein = r.ein
        WHERE ve.claim_status = 'unconfirmed'
        AND ve.ai_generated = 1
        AND ve.event_date > date('now', '-7 days')  -- Recent events
        AND NOT EXISTS (
            SELECT 1 FROM outreach_log ol
            WHERE ol.event_id = ve.id AND ol.sent_at > datetime('now', '-30 days')
        )
    """

    if tier == 1:
        query += """
        AND r.website IS NOT NULL  -- Has verified website
        ORDER BY ve.event_date ASC
        """
    else:
        query += " ORDER BY ve.event_date ASC"

    events = db.execute(query).fetchall()
    db.close()

    return [dict(e) for e in events]

def get_nonprofit_contact_email(ein: str) -> Optional[str]:
    """Get the best contact email for a nonprofit."""
    db = get_db()

    # Try org_contacts first (if populated)
    contact = db.execute(
        "SELECT volunteer_email, general_email, events_email FROM org_contacts WHERE ein = ?",
        (ein,)
    ).fetchone()

    if contact:
        # Prefer volunteer coordinator
        email = contact['volunteer_email'] or contact['events_email'] or contact['general_email']
        if email:
            db.close()
            return email

    # Fallback: look for website contact form or general email
    registry_db = get_db(REGISTRY_DB)
    org = registry_db.execute(
        "SELECT website FROM registry_enriched WHERE ein = ?",
        (ein,)
    ).fetchone()

    registry_db.close()
    db.close()

    return None

def send_outreach_email(
    nonprofit_name: str,
    email: str,
    event_title: str,
    event_date: str,
    event_url: str,
    claim_url: str
) -> bool:
    """Send outreach email to nonprofit director.

    Returns True if sent successfully, False otherwise.
    """
    try:
        from email_service_volunteer import send_email

        body = f"""
        <h2>We found your event on Daanaa 🎯</h2>

        <p>Hi {nonprofit_name} team,</p>

        <p>We discovered <strong>{event_title}</strong> on your website and think you could use Daanaa to make volunteering easier.</p>

        <h3>When you claim this event, you can:</h3>
        <ul>
          <li>✅ Accept volunteer registrations directly</li>
          <li>✅ Track and verify volunteer hours (no spreadsheets)</li>
          <li>✅ See impact metrics for your board/funders</li>
          <li>✅ Accept donations (you keep 100%, no fees)</li>
        </ul>

        <p><strong><a href="{claim_url}" style="background: #d4af37; color: #1a472a; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: 600;">Claim & Manage This Event</a></strong></p>

        <p style="margin-top: 20px; font-size: 14px; color: #666;">
          <strong>Event date:</strong> {event_date}<br>
          <strong>Original page:</strong> <a href="{event_url}">{event_url}</a><br>
          <strong>Claim link expires:</strong> 48 hours
        </p>

        <p style="margin-top: 30px; font-size: 13px; color: #999;">
          Not interested? Just ignore this email — no pressure. <a href="mailto:hello@daanaa.org?subject=Not+interested">Tell us why</a> and we won't reach out again.
        </p>

        <p style="margin-top: 20px; font-size: 12px;">
          Daanaa connects volunteers to nonprofits. We don't take a cut on donations and are self-funded.
          <a href="https://daanaa.org">Learn more</a>
        </p>
        """

        send_email(email, f"Manage {event_title} on Daanaa", body)
        return True
    except Exception as e:
        print(f"❌ Error sending email to {email}: {e}", file=sys.stderr)
        return False

def log_outreach(event_id: int, ein: str, email: str):
    """Log the outreach attempt."""
    db = get_db()
    outreach_id = f"outreach_{secrets.token_hex(8)}"

    db.execute("""
        INSERT INTO outreach_log (id, ein, event_id, email, outreach_type, sent_at)
        VALUES (?, ?, ?, ?, 'discovery', datetime('now'))
    """, (outreach_id, ein, event_id, email))

    db.commit()
    db.close()

def run_campaign(tier: int = 1, limit: int = None, dry_run: bool = False) -> Dict:
    """Run the outreach campaign.

    Returns a summary dict with sent, failed, skipped counts.
    """
    events = get_unclaimed_events(tier=tier)

    if limit:
        events = events[:limit]

    summary = {
        'total': len(events),
        'sent': 0,
        'failed': 0,
        'skipped': 0,
        'emails': []
    }

    if not events:
        print(f"No unclaimed events found for Tier {tier}")
        return summary

    print(f"Found {len(events)} unclaimed events. Starting outreach...")
    print()

    for event in events:
        ein = event['ein']
        event_id = event['id']
        event_title = event['title']
        event_date = event['event_date']
        org_name = event['org_name']
        org_website = event['org_website']
        source_url = event['source_url']

        # Get nonprofit contact
        email = get_nonprofit_contact_email(ein)
        if not email:
            print(f"⏭️  SKIP: {org_name} ({ein}) — no verified contact email")
            summary['skipped'] += 1
            continue

        # Generate claim link
        verification_token = secrets.token_urlsafe(32)
        claim_url = f"https://daanaa.org/verify-event-claim/{verification_token}"

        print(f"📧 {org_name}")
        print(f"   Event: {event_title} ({event_date})")
        print(f"   Email: {email}")

        if dry_run:
            print(f"   [DRY RUN] Would send email")
            summary['emails'].append({
                'ein': ein,
                'org': org_name,
                'email': email,
                'event': event_title,
                'status': 'dry_run'
            })
        else:
            # Send email
            if send_outreach_email(org_name, email, event_title, event_date, source_url, claim_url):
                # Log outreach
                log_outreach(event_id, ein, email)
                summary['sent'] += 1
                summary['emails'].append({
                    'ein': ein,
                    'org': org_name,
                    'email': email,
                    'event': event_title,
                    'status': 'sent'
                })
                print(f"   ✅ Sent")
            else:
                summary['failed'] += 1
                summary['emails'].append({
                    'ein': ein,
                    'org': org_name,
                    'email': email,
                    'event': event_title,
                    'status': 'failed'
                })
                print(f"   ❌ Failed")

        print()

    # Print summary
    print("=" * 60)
    print(f"Campaign Summary:")
    print(f"  Total events: {summary['total']}")
    print(f"  Sent: {summary['sent']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Skipped: {summary['skipped']}")
    print("=" * 60)

    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Nonprofit Event Outreach Campaign')
    parser.add_argument('--tier', type=int, default=1, help='Nonprofit tier (1=verified contact, 2=all)')
    parser.add_argument('--limit', type=int, help='Max emails to send')
    parser.add_argument('--dry-run', action='store_true', help='Preview emails without sending')

    args = parser.parse_args()

    run_campaign(tier=args.tier, limit=args.limit, dry_run=args.dry_run)
