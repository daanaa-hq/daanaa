"""
Daanaa Email Automation System

Sends personalized email sequences to nonprofits, donors, and partners.
Tracks opens, clicks, and conversions for learning + optimization.

Three sequence types:
1. Nonprofit nurture: Encourage profile claim + completion (5 emails over 60 days)
2. Donor nurture: Drive donation intent + action (5 emails over 60 days)
3. Partner nurture: Build relationships for co-marketing (3 emails over 30 days)

Core strategy: Data-driven, not pushy. Every email has a clear purpose and measures impact.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class SequenceType(Enum):
    """Types of email sequences."""
    NONPROFIT_NURTURE = "nonprofit_nurture"
    DONOR_NURTURE = "donor_nurture"
    PARTNER_NURTURE = "partner_nurture"


@dataclass
class EmailTemplate:
    """Email template with personalization fields."""
    sequence_type: SequenceType
    step_number: int
    subject_line: str
    body: str
    cta_text: str
    cta_url: str
    personalization_fields: List[Dict]


class EmailAutomation:
    """
    Manages email sequences for relationship nurturing.
    """

    def __init__(self, db_path: str = "/home/akbar/meritgiving/data/merit_registry.db"):
        self.db_path = db_path
        self.db = None
        self.init_db()
        self.load_templates()

    def init_db(self):
        """Initialize email tracking tables."""
        self.db = sqlite3.connect(self.db_path)
        cursor = self.db.cursor()

        # Email sequences: tracks which email is sent to whom
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_sequences (
                id TEXT PRIMARY KEY,
                sequence_type TEXT,
                target_id TEXT,
                target_type TEXT,  -- 'nonprofit', 'donor', 'partner'
                sequence_step INTEGER,
                email_template_id TEXT,
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                cta_action TEXT,
                notes TEXT
            )
        """)

        # Email templates: pre-built templates with personalization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id TEXT PRIMARY KEY,
                sequence_type TEXT,
                step_number INTEGER,
                subject_line TEXT,
                body TEXT,
                cta_text TEXT,
                cta_url TEXT,
                personalization_fields TEXT,  -- JSON
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        self.db.commit()

    def load_templates(self):
        """Load default email templates."""
        cursor = self.db.cursor()

        # Clear existing
        cursor.execute("DELETE FROM email_templates")

        templates = self._get_default_templates()

        for template in templates:
            template_id = f"template_{template['sequence_type']}_{template['step']}"
            cursor.execute("""
                INSERT INTO email_templates
                (id, sequence_type, step_number, subject_line, body, cta_text, cta_url,
                 personalization_fields, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template_id,
                template['sequence_type'],
                template['step'],
                template['subject_line'],
                template['body'],
                template['cta_text'],
                template['cta_url'],
                json.dumps(template['personalization_fields']),
                datetime.now(),
                datetime.now()
            ))

        self.db.commit()

    def _get_default_templates(self) -> List[Dict]:
        """Default email templates for all sequence types."""
        return [
            # NONPROFIT NURTURE SEQUENCE (5 emails over 60 days)
            {
                "sequence_type": "nonprofit_nurture",
                "step": 1,
                "subject_line": "Your nonprofit's financial health, explained",
                "body": """Hi {{nonprofit_name}},

We discovered your organization in our research and thought you'd want to know: {{mission_statement}}

That's why we built Daanaa — a free directory that shows how nonprofits like yours actually fund their work, based on IRS data.

When you claim your profile, you can:
- Share your story directly with potential donors
- See how your funding model compares to peer organizations
- Connect with other nonprofit leaders

It takes about 10 minutes.

{{org_name}} team
Daanaa""",
                "cta_text": "Claim your profile",
                "cta_url": "https://daanaa.org/claim",
                "personalization_fields": [
                    {"field": "nonprofit_name", "source": "nonprofit_registry"},
                    {"field": "mission_statement", "source": "nonprofit_registry"},
                    {"field": "org_name", "source": "nonprofit_registry"},
                ]
            },
            {
                "sequence_type": "nonprofit_nurture",
                "step": 2,
                "subject_line": "{{nonprofit_name}} — nearly done with your profile",
                "body": """Hi {{contact_person}},

We noticed you started claiming your profile on Daanaa but haven't finished yet.

The last few questions just take a few minutes, and they help donors understand:
- What you fund
- Where you're based
- How to donate directly

{{org_name}} team
Daanaa""",
                "cta_text": "Finish claiming",
                "cta_url": "https://daanaa.org/claim/{{nonprofit_id}}",
                "personalization_fields": [
                    {"field": "nonprofit_name", "source": "nonprofit_registry"},
                    {"field": "contact_person", "source": "claim_data"},
                    {"field": "nonprofit_id", "source": "nonprofit_registry"},
                    {"field": "org_name", "source": "nonprofit_registry"},
                ]
            },
            {
                "sequence_type": "nonprofit_nurture",
                "step": 3,
                "subject_line": "How other nonprofits use Daanaa",
                "body": """Hi {{nonprofit_name}},

After claiming their profiles, nonprofit leaders tell us Daanaa helps with:
- Attracting new donors (people search directly from our directory)
- Connecting with peer organizations
- Showing financial transparency without shame

Some use it to train their board on funding models. Others link to it from their annual report.

It's free. No fees, no ads, no ranking.

{{org_name}} team
Daanaa""",
                "cta_text": "See how it works",
                "cta_url": "https://daanaa.org/how-it-works",
                "personalization_fields": []
            },
            {
                "sequence_type": "nonprofit_nurture",
                "step": 4,
                "subject_line": "Questions about Daanaa?",
                "body": """Hi {{nonprofit_name}},

We're here to help. Reach out with questions about:
- Claiming your profile
- How your data is displayed
- How Daanaa works

Reply directly to this email or contact us at hello@daanaa.org

{{org_name}} team
Daanaa""",
                "cta_text": "Contact us",
                "cta_url": "mailto:hello@daanaa.org",
                "personalization_fields": [
                    {"field": "nonprofit_name", "source": "nonprofit_registry"},
                    {"field": "org_name", "source": "nonprofit_registry"},
                ]
            },
            {
                "sequence_type": "nonprofit_nurture",
                "step": 5,
                "subject_line": "{{nonprofit_name}}, last update from Daanaa",
                "body": """Hi {{nonprofit_name}},

We built Daanaa to help nonprofits like yours get discovered by aligned donors and partners.

Claiming your profile is free and takes 10 minutes. If you decide it's not for you, that's okay — no hard feelings.

But if you have questions, we're always here.

{{org_name}} team
Daanaa""",
                "cta_text": "Claim your profile",
                "cta_url": "https://daanaa.org/claim",
                "personalization_fields": [
                    {"field": "nonprofit_name", "source": "nonprofit_registry"},
                    {"field": "org_name", "source": "nonprofit_registry"},
                ]
            },

            # DONOR NURTURE SEQUENCE (5 emails over 60 days)
            {
                "sequence_type": "donor_nurture",
                "step": 1,
                "subject_line": "We found nonprofits doing {{cause_interest}}",
                "body": """Hi {{donor_name}},

On Daanaa, you searched for organizations working in {{cause_interest}}.

We pulled {{org_count}} vetted nonprofits that match your interests. Most you've probably never heard of.

All their funding models are transparent. No rankings, no judgment — just data.

Browse them when you're ready.

Daanaa team""",
                "cta_text": "Explore nonprofits",
                "cta_url": "https://daanaa.org/directory?cause={{cause_id}}",
                "personalization_fields": [
                    {"field": "donor_name", "source": "wallet_data"},
                    {"field": "cause_interest", "source": "wallet_data"},
                    {"field": "org_count", "source": "calculated"},
                    {"field": "cause_id", "source": "wallet_data"},
                ]
            },
            {
                "sequence_type": "donor_nurture",
                "step": 2,
                "subject_line": "{{nonprofit_name}} might be who you're looking for",
                "body": """Hi {{donor_name}},

Based on your search for {{cause_interest}}, we thought {{nonprofit_name}} might interest you.

{{mission_statement}}

They fund their work through {{funding_model}}. No paid staff positions, lean operations.

The data is all public. We just made it readable.

{{org_name}} team
Daanaa""",
                "cta_text": "View full profile",
                "cta_url": "https://daanaa.org/orgs/{{nonprofit_id}}",
                "personalization_fields": [
                    {"field": "donor_name", "source": "wallet_data"},
                    {"field": "nonprofit_name", "source": "nonprofit_registry"},
                    {"field": "cause_interest", "source": "wallet_data"},
                    {"field": "mission_statement", "source": "nonprofit_registry"},
                    {"field": "funding_model", "source": "nonprofit_registry"},
                    {"field": "nonprofit_id", "source": "nonprofit_registry"},
                    {"field": "org_name", "source": "nonprofit_registry"},
                ]
            },
            {
                "sequence_type": "donor_nurture",
                "step": 3,
                "subject_line": "How to support {{nonprofit_name}}",
                "body": """Hi {{donor_name}},

{{nonprofit_name}} has a direct donate link on their profile.

No middleman. No fees. Straight to their bank account.

If you want to support them, that's the fastest way.

{{org_name}} team
Daanaa""",
                "cta_text": "Donate to {{nonprofit_name}}",
                "cta_url": "https://{{nonprofit_donate_url}}",
                "personalization_fields": [
                    {"field": "donor_name", "source": "wallet_data"},
                    {"field": "nonprofit_name", "source": "nonprofit_registry"},
                    {"field": "nonprofit_donate_url", "source": "nonprofit_registry"},
                    {"field": "org_name", "source": "nonprofit_registry"},
                ]
            },
            {
                "sequence_type": "donor_nurture",
                "step": 4,
                "subject_line": "More {{cause_interest}} nonprofits you might not know about",
                "body": """Hi {{donor_name}},

We found {{new_org_count}} more {{cause_interest}} nonprofits you haven't discovered yet.

All data-backed. All vetted. All doing real work.

Browse whenever you're ready to explore.

{{org_name}} team
Daanaa""",
                "cta_text": "Explore more",
                "cta_url": "https://daanaa.org/directory?cause={{cause_id}}",
                "personalization_fields": [
                    {"field": "donor_name", "source": "wallet_data"},
                    {"field": "cause_interest", "source": "wallet_data"},
                    {"field": "new_org_count", "source": "calculated"},
                    {"field": "cause_id", "source": "wallet_data"},
                    {"field": "org_name", "source": "nonprofit_registry"},
                ]
            },
            {
                "sequence_type": "donor_nurture",
                "step": 5,
                "subject_line": "{{donor_name}}, we're here if you need help",
                "body": """Hi {{donor_name}},

Finding the right nonprofit to support is personal. If you have questions about any organization or cause on Daanaa, we're here.

reply@daanaa.org

{{org_name}} team
Daanaa""",
                "cta_text": "Contact us",
                "cta_url": "mailto:hello@daanaa.org",
                "personalization_fields": [
                    {"field": "donor_name", "source": "wallet_data"},
                    {"field": "org_name", "source": "nonprofit_registry"},
                ]
            },

            # PARTNER NURTURE SEQUENCE (3 emails over 30 days)
            {
                "sequence_type": "partner_nurture",
                "step": 1,
                "subject_line": "Idea: partnering on nonprofit discovery",
                "body": """Hi {{partner_contact}},

I noticed your {{partner_type}} works in {{partnership_area}}. We do something similar at Daanaa.

We help nonprofits get discovered by aligned donors and partners. You help organizations thrive. That overlap made me think we might work well together.

Nothing formal — just an idea.

{{founder_name}}
Daanaa""",
                "cta_text": "Let's chat",
                "cta_url": "https://daanaa.org/contact",
                "personalization_fields": [
                    {"field": "partner_contact", "source": "partner_data"},
                    {"field": "partner_type", "source": "partner_data"},
                    {"field": "partnership_area", "source": "partner_data"},
                    {"field": "founder_name", "source": "config"},
                ]
            },
            {
                "sequence_type": "partner_nurture",
                "step": 2,
                "subject_line": "What we're building at Daanaa",
                "body": """Hi {{partner_contact}},

Daanaa is a free directory of nonprofits indexed by their funding model and financial health.

No rankings. No algorithms trying to push certain orgs. Just data, made readable.

Nonprofits claim their profiles. Donors and partners discover them. Everyone learns something true.

Your {{partner_type}} could help us expand this in {{partnership_area}}. Would be stronger together.

Interested?

{{founder_name}}
Daanaa""",
                "cta_text": "Learn more",
                "cta_url": "https://daanaa.org/about",
                "personalization_fields": [
                    {"field": "partner_contact", "source": "partner_data"},
                    {"field": "partner_type", "source": "partner_data"},
                    {"field": "partnership_area", "source": "partner_data"},
                    {"field": "founder_name", "source": "config"},
                ]
            },
            {
                "sequence_type": "partner_nurture",
                "step": 3,
                "subject_line": "Last message: Daanaa + {{partner_name}}",
                "body": """Hi {{partner_contact}},

If you want to explore working together on nonprofit discovery, I'm here. If not, no pressure.

Either way, thanks for considering it.

{{founder_name}}
Daanaa""",
                "cta_text": "Schedule a call",
                "cta_url": "https://calendly.com/akbar",
                "personalization_fields": [
                    {"field": "partner_contact", "source": "partner_data"},
                    {"field": "partner_name", "source": "partner_data"},
                    {"field": "founder_name", "source": "config"},
                ]
            }
        ]

    def enroll_nonprofit(self, nonprofit_id: str, nonprofit_name: str,
                        mission_statement: str, contact_email: str,
                        contact_person: Optional[str] = None) -> str:
        """Enroll a nonprofit in the nurture sequence."""
        sequence_id = f"sequence_nonprofit_{nonprofit_id}_{int(datetime.now().timestamp())}"

        cursor = self.db.cursor()

        # Get first template
        cursor.execute("""
            SELECT id FROM email_templates
            WHERE sequence_type = ? AND step_number = 1
            LIMIT 1
        """, ("nonprofit_nurture",))

        template_id = cursor.fetchone()[0]

        # Create sequence record
        cursor.execute("""
            INSERT INTO email_sequences
            (id, sequence_type, target_id, target_type, sequence_step, email_template_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            sequence_id,
            "nonprofit_nurture",
            nonprofit_id,
            "nonprofit",
            1,
            template_id
        ))

        self.db.commit()

        return sequence_id

    def enroll_donor(self, donor_id: str, donor_name: str, email: str,
                    cause_interest: str) -> str:
        """Enroll a donor in the nurture sequence."""
        sequence_id = f"sequence_donor_{donor_id}_{int(datetime.now().timestamp())}"

        cursor = self.db.cursor()

        # Get first template
        cursor.execute("""
            SELECT id FROM email_templates
            WHERE sequence_type = ? AND step_number = 1
            LIMIT 1
        """, ("donor_nurture",))

        template_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO email_sequences
            (id, sequence_type, target_id, target_type, sequence_step, email_template_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            sequence_id,
            "donor_nurture",
            donor_id,
            "donor",
            1,
            template_id
        ))

        self.db.commit()
        return sequence_id

    def enroll_partner(self, partner_id: str, partner_name: str,
                      partner_contact: str, email: str) -> str:
        """Enroll a partner in the nurture sequence."""
        sequence_id = f"sequence_partner_{partner_id}_{int(datetime.now().timestamp())}"

        cursor = self.db.cursor()

        cursor.execute("""
            SELECT id FROM email_templates
            WHERE sequence_type = ? AND step_number = 1
            LIMIT 1
        """, ("partner_nurture",))

        template_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO email_sequences
            (id, sequence_type, target_id, target_type, sequence_step, email_template_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            sequence_id,
            "partner_nurture",
            partner_id,
            "partner",
            1,
            template_id
        ))

        self.db.commit()
        return sequence_id

    def log_email_sent(self, sequence_id: str, email_address: str):
        """Log that an email was sent."""
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE email_sequences
            SET sent_at = ?
            WHERE id = ?
        """, (datetime.now(), sequence_id))
        self.db.commit()

    def log_email_opened(self, sequence_id: str):
        """Log that an email was opened."""
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE email_sequences
            SET opened_at = ?
            WHERE id = ?
        """, (datetime.now(), sequence_id))
        self.db.commit()

    def log_email_clicked(self, sequence_id: str, cta_action: str):
        """Log that email CTA was clicked."""
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE email_sequences
            SET clicked_at = ?, cta_action = ?
            WHERE id = ?
        """, (datetime.now(), cta_action, sequence_id))
        self.db.commit()

    def advance_sequence(self, sequence_id: str) -> bool:
        """Move a sequence to the next step."""
        cursor = self.db.cursor()

        # Get current sequence
        cursor.execute("""
            SELECT sequence_type, sequence_step
            FROM email_sequences
            WHERE id = ?
        """, (sequence_id,))

        result = cursor.fetchone()
        if not result:
            return False

        sequence_type, current_step = result

        # Get max steps for this sequence
        cursor.execute("""
            SELECT MAX(step_number)
            FROM email_templates
            WHERE sequence_type = ?
        """, (sequence_type,))

        max_step = cursor.fetchone()[0]

        if current_step >= max_step:
            return False  # Sequence complete

        # Get next template
        cursor.execute("""
            SELECT id FROM email_templates
            WHERE sequence_type = ? AND step_number = ?
        """, (sequence_type, current_step + 1))

        next_template = cursor.fetchone()
        if not next_template:
            return False

        # Update sequence
        cursor.execute("""
            UPDATE email_sequences
            SET sequence_step = ?, email_template_id = ?, sent_at = NULL
            WHERE id = ?
        """, (current_step + 1, next_template[0], sequence_id))

        self.db.commit()
        return True

    def weekly_email_summary(self) -> Dict:
        """Generate weekly email performance summary."""
        week_ago = datetime.now() - timedelta(days=7)

        cursor = self.db.cursor()

        # Total emails sent
        cursor.execute("""
            SELECT COUNT(*) FROM email_sequences
            WHERE sent_at > ?
        """, (week_ago,))
        emails_sent = cursor.fetchone()[0]

        # Opens
        cursor.execute("""
            SELECT COUNT(*) FROM email_sequences
            WHERE opened_at > ? AND sent_at > ?
        """, (week_ago, week_ago))
        emails_opened = cursor.fetchone()[0]

        # Clicks
        cursor.execute("""
            SELECT COUNT(*) FROM email_sequences
            WHERE clicked_at > ? AND sent_at > ?
        """, (week_ago, week_ago))
        emails_clicked = cursor.fetchone()[0]

        # Conversions (for nonprofits: claim_complete, for donors: give intent)
        cursor.execute("""
            SELECT COUNT(*) FROM email_sequences
            WHERE cta_action IN ('claimed', 'donated', 'replied') AND sent_at > ?
        """, (week_ago,))
        conversions = cursor.fetchone()[0]

        open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
        click_rate = (emails_clicked / emails_sent * 100) if emails_sent > 0 else 0
        conversion_rate = (conversions / emails_sent * 100) if emails_sent > 0 else 0

        return {
            "period": "last_7_days",
            "emails_sent": emails_sent,
            "emails_opened": emails_opened,
            "open_rate_pct": round(open_rate, 1),
            "emails_clicked": emails_clicked,
            "click_rate_pct": round(click_rate, 1),
            "conversions": conversions,
            "conversion_rate_pct": round(conversion_rate, 1),
        }

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    # Test email automation
    ea = EmailAutomation()

    # Enroll a nonprofit
    nonprofit_seq = ea.enroll_nonprofit(
        "nonprofit_12345",
        "Hope Soup Kitchen",
        "Providing free meals and community support",
        "director@hopesoup.org",
        "Sarah Williams"
    )
    print(f"Enrolled nonprofit: {nonprofit_seq}")

    # Enroll a donor
    donor_seq = ea.enroll_donor(
        "donor_67890",
        "John Donor",
        "john@example.com",
        "food security"
    )
    print(f"Enrolled donor: {donor_seq}")

    # Get summary
    summary = ea.weekly_email_summary()
    print(f"\nWeekly email summary: {summary}")

    ea.close()
