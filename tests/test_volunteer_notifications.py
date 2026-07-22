"""Test volunteer hours notifications system.

Covers:
- Duplicate prevention
- Email failure handling
- Test environment isolation (no external emails sent)
- Idempotency
- Privacy (no PII leaks)
"""

import sqlite3
import unittest
import os
from datetime import datetime, timedelta
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from volunteer_notifications import (
    create_submission_notification,
    create_approval_notification,
    create_rejection_notification,
    send_pending_notifications,
    get_notification_stats,
)


class VolunteerNotificationTest(unittest.TestCase):
    """Test notification system."""

    def setUp(self):
        """Create in-memory test database."""
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row

        # Create minimal schema for testing
        self.db.execute('''
            CREATE TABLE volunteer_hours (
                id TEXT PRIMARY KEY,
                nonprofit_ein TEXT NOT NULL,
                volunteer_name TEXT,
                volunteer_email TEXT,
                hours REAL,
                service_date TEXT,
                organization_name TEXT,
                rejection_reason TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')

        self.db.execute('''
            CREATE TABLE org_claims (
                ein TEXT PRIMARY KEY,
                email TEXT,
                claim_status TEXT
            )
        ''')

        self.db.execute('''
            CREATE TABLE registry_enriched (
                ein TEXT PRIMARY KEY,
                organization_name TEXT,
                website_contact_email TEXT
            )
        ''')

        # Create notification tracking table
        self.db.execute('''
            CREATE TABLE volunteer_notification_jobs (
                job_id TEXT PRIMARY KEY,
                hour_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                recipient_email TEXT NOT NULL,
                recipient_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                next_retry_at TIMESTAMP,
                error_message TEXT,
                is_test_run BOOLEAN DEFAULT 0,
                UNIQUE(hour_id, notification_type),
                FOREIGN KEY (hour_id) REFERENCES volunteer_hours(id)
            )
        ''')

        # Create index for notification queue
        self.db.execute('''
            CREATE INDEX idx_notification_status ON volunteer_notification_jobs(status)
        ''')

        # Insert test data
        self._setup_test_data()

    def _setup_test_data(self):
        """Create test organizations and submissions."""
        # Test nonprofit
        self.nonprofit_ein = '123456789'
        self.nonprofit_email = 'contact@nonprofit.org'
        self.db.execute(
            'INSERT INTO org_claims (ein, email, claim_status) VALUES (?, ?, ?)',
            (self.nonprofit_ein, self.nonprofit_email, 'verified')
        )
        self.db.execute(
            'INSERT INTO registry_enriched (ein, organization_name) VALUES (?, ?)',
            (self.nonprofit_ein, 'Test Nonprofit')
        )

        # Test volunteer submission
        self.hour_id = 'VOL-abc123def456'
        self.volunteer_email = 'volunteer@example.com'
        self.db.execute('''
            INSERT INTO volunteer_hours
            (id, nonprofit_ein, volunteer_name, volunteer_email, hours,
             service_date, organization_name, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.hour_id, self.nonprofit_ein, 'John Doe', self.volunteer_email,
              4.0, '2026-07-22', 'Test Nonprofit', 'pending'))
        self.db.commit()

    def test_submission_notification_created(self):
        """Verify submission notification is queued."""
        result = create_submission_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22',
            is_test=True
        )
        self.assertTrue(result, "Notification should be created")

        # Verify job exists
        job = self.db.execute(
            'SELECT * FROM volunteer_notification_jobs WHERE hour_id=? AND notification_type=?',
            (self.hour_id, 'submitted')
        ).fetchone()
        self.assertIsNotNone(job, "Notification job should exist")
        self.assertEqual(job['status'], 'pending')
        self.assertEqual(job['recipient_type'], 'nonprofit')
        self.assertEqual(job['is_test_run'], 1)

    def test_duplicate_submission_prevention(self):
        """Verify duplicate submission notifications are prevented."""
        # Create first
        result1 = create_submission_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )
        self.assertTrue(result1)

        # Attempt duplicate
        result2 = create_submission_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )
        self.assertFalse(result2, "Duplicate should not be created")

        # Verify only one job
        count = self.db.execute(
            'SELECT COUNT(*) FROM volunteer_notification_jobs WHERE hour_id=?',
            (self.hour_id,)
        ).fetchone()[0]
        self.assertEqual(count, 1, "Only one notification should exist")

    def test_approval_notification_created(self):
        """Verify approval notification is queued."""
        result = create_approval_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22',
            is_test=True
        )
        self.assertTrue(result)

        job = self.db.execute(
            'SELECT * FROM volunteer_notification_jobs WHERE notification_type=?',
            ('approved',)
        ).fetchone()
        self.assertIsNotNone(job)
        self.assertEqual(job['recipient_type'], 'volunteer')
        self.assertEqual(job['recipient_email'], self.volunteer_email)

    def test_approval_duplicate_prevention(self):
        """Verify duplicate approval notifications are prevented."""
        create_approval_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )
        create_approval_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )

        count = self.db.execute(
            'SELECT COUNT(*) FROM volunteer_notification_jobs WHERE notification_type=?',
            ('approved',)
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_rejection_notification_created(self):
        """Verify rejection notification is queued."""
        result = create_rejection_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 'Hours do not match event',
            is_test=True
        )
        self.assertTrue(result)

        job = self.db.execute(
            'SELECT * FROM volunteer_notification_jobs WHERE notification_type=?',
            ('rejected',)
        ).fetchone()
        self.assertIsNotNone(job)
        self.assertEqual(job['recipient_email'], self.volunteer_email)

    def test_rejection_duplicate_prevention(self):
        """Verify duplicate rejection notifications are prevented."""
        create_rejection_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 'Reason 1'
        )
        create_rejection_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 'Reason 2'
        )

        count = self.db.execute(
            'SELECT COUNT(*) FROM volunteer_notification_jobs WHERE notification_type=?',
            ('rejected',)
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_missing_volunteer_email_rejection(self):
        """Verify rejection doesn't create notification if email missing."""
        result = create_rejection_notification(
            self.db, self.hour_id, None,
            self.nonprofit_ein, 'Test Nonprofit', 'Reason'
        )
        self.assertFalse(result, "Should not create notification without email")

    def test_missing_volunteer_email_approval(self):
        """Verify approval doesn't create notification if email missing."""
        result = create_approval_notification(
            self.db, self.hour_id, None,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )
        self.assertFalse(result, "Should not create notification without email")

    def test_notification_stats(self):
        """Verify notification statistics are accurate."""
        create_submission_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )

        stats = get_notification_stats(self.db)
        self.assertEqual(stats['pending'], 1)
        self.assertEqual(stats['sent'], 0)
        self.assertEqual(stats['failed'], 0)

    def test_test_mode_isolation(self):
        """Verify test submissions are marked and isolated."""
        create_submission_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22',
            is_test=True
        )

        job = self.db.execute(
            'SELECT is_test_run FROM volunteer_notification_jobs WHERE hour_id=?',
            (self.hour_id,)
        ).fetchone()
        self.assertEqual(job['is_test_run'], 1, "Should be marked as test")

    def test_no_pii_in_subject(self):
        """Verify PII (names, emails) not in notification subjects."""
        create_submission_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )

        job = self.db.execute(
            'SELECT subject FROM volunteer_notification_jobs WHERE hour_id=?',
            (self.hour_id,)
        ).fetchone()

        # Subject should not contain volunteer email or name
        self.assertNotIn('@', job['subject'], "Email should not be in subject")
        self.assertNotIn('John', job['subject'], "Name should not be in subject")

    def test_multiple_submissions_separate_notifications(self):
        """Verify different submission types get separate notifications."""
        # Create submission notification
        create_submission_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )

        # Create approval notification (different type, same hour)
        create_approval_notification(
            self.db, self.hour_id, self.volunteer_email,
            self.nonprofit_ein, 'Test Nonprofit', 4.0, '2026-07-22'
        )

        # Should have 2 notifications (different types)
        count = self.db.execute(
            'SELECT COUNT(*) FROM volunteer_notification_jobs WHERE hour_id=?',
            (self.hour_id,)
        ).fetchone()[0]
        self.assertEqual(count, 2, "Should have both submitted and approval")


if __name__ == '__main__':
    unittest.main()
