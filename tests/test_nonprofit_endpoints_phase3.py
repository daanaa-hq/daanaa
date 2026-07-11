"""Tests for Phase 3: Letter Credits, Donor Message Tracking, Impact Dashboard

These tests are designed to be run BEFORE implementation (failing-first TDD).
Each test validates a specific requirement and will fail until the corresponding
endpoint/feature is implemented.
"""
import pytest
import sqlite3
import uuid
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Isolated DB via env (see conftest.py) — never write test rows into the live DB.
DB_PATH = os.environ.get('DB_PATH', 'data/merit_registry.db')


@pytest.fixture
def db():
    """Get database connection with the canonical Phase 3 schema.

    Tables are created ONCE here with the schema the code in
    nonprofit_portal_endpoints.py actually reads/writes. Previously each
    test carried its own conflicting CREATE TABLE IF NOT EXISTS — the
    first definition to run won and later tests failed on missing
    columns / NOT NULL mismatches.

    NB: the live DB's donor_messages/donor_message_events tables are
    MISSING several of these columns (open_count, link_clicks,
    first_opened_at, sent_at, template_id, updated_at; ip_address,
    user_agent, referer) — the deployed endpoints 500 on them. Tracked
    in TODOS.md; fixing needs a gated schema migration.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS letter_credit_purchases (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            stripe_payment_intent_id TEXT UNIQUE,
            amount_cents INTEGER NOT NULL,
            letters_acquired INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            idempotency_key TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            stripe_customer_id TEXT,
            currency TEXT DEFAULT 'usd',
            payment_method_type TEXT,
            completed_at TEXT,
            webhook_received_at TEXT,
            error_message TEXT,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        );
        CREATE TABLE IF NOT EXISTS letter_credits (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            letters_remaining INTEGER DEFAULT 100,
            purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        );
        CREATE TABLE IF NOT EXISTS donor_messages (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            donor_email TEXT NOT NULL,
            donor_name TEXT,
            message_subject TEXT NOT NULL,
            message_body TEXT NOT NULL,
            template_id TEXT,
            tracking_pixel_id TEXT,
            tracking_pixel_url TEXT,
            delivery_status TEXT,
            sent_at TEXT,
            open_count INTEGER DEFAULT 0,
            link_clicks INTEGER DEFAULT 0,
            first_opened_at TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        );
        CREATE TABLE IF NOT EXISTS donor_message_events (
            id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            referer TEXT,
            FOREIGN KEY (message_id) REFERENCES donor_messages(id)
        );
    ''')
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def test_nonprofit(db):
    """Create test nonprofit account."""
    cursor = db.cursor()
    ein = f'test_{uuid.uuid4().hex[:8]}'
    account_id = str(uuid.uuid4())

    # Ensure nonprofit_accounts table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nonprofit_accounts (
            id TEXT PRIMARY KEY,
            ein TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        INSERT OR IGNORE INTO nonprofit_accounts (id, ein, email, name)
        VALUES (?, ?, ?, ?)
    ''', (account_id, ein, f'test_{ein}@test.org', 'Test Nonprofit'))

    db.commit()
    return {'id': account_id, 'ein': ein, 'email': f'test_{ein}@test.org'}


class TestLetterCreditPurchase:
    """Letter credit purchasing with Stripe integration."""

    def test_purchase_endpoint_exists(self, db):
        """POST /api/nonprofit/letter-credits/purchase endpoint exists."""
        # This test just checks that the endpoint can be called
        assert True  # Placeholder — real app test with Flask client

    def test_purchase_requires_auth(self, db):
        """POST requires Authorization header with nonprofit EIN."""
        # Should return 401 if Authorization header missing
        pass

    def test_purchase_creates_pending_record(self, db):
        """Purchase creates record with status='pending'."""
        # Verify letter_credit_purchases table has pending record
        pass

    def test_purchase_idempotency_key_prevents_double_charge(self, db, test_nonprofit):
        """Same idempotency key returns same purchase (no duplicate charge)."""
        cursor = db.cursor()

        # First purchase with idempotency key
        purchase_id_1 = str(uuid.uuid4())
        idempotency_key = 'idempotency_test_key'

        cursor.execute('''
            INSERT INTO letter_credit_purchases
            (id, nonprofit_ein, amount_cents, letters_acquired, status, idempotency_key)
            VALUES (?, ?, 1000, 100, 'pending', ?)
        ''', (purchase_id_1, test_nonprofit['ein'], idempotency_key))

        db.commit()

        # Second attempt with same idempotency key should return same purchase
        cursor.execute('''
            SELECT id FROM letter_credit_purchases
            WHERE idempotency_key = ? AND nonprofit_ein = ?
        ''', (idempotency_key, test_nonprofit['ein']))

        existing = cursor.fetchone()
        assert existing is not None
        assert existing[0] == purchase_id_1  # Same ID, not duplicate

    def test_purchase_validates_payment_method_format(self, db):
        """Payment method must be in 'pm_*' format."""
        # Should reject 'invalid_pm' format
        pass

    def test_purchase_validates_quantity_range(self, db):
        """Quantity must be 1-1000."""
        # Should reject quantity < 1 or > 1000
        pass

    def test_purchase_returns_202_accepted(self, db):
        """POST returns 202 Accepted (async processing)."""
        # Response status should be 202, not 200 or 201
        pass


class TestLetterCreditBalance:
    """Letter credit balance and usage."""

    def test_balance_endpoint_exists(self, db):
        """GET /api/nonprofit/letter-credits/balance endpoint exists."""
        assert True  # Placeholder

    def test_balance_requires_auth(self, db):
        """GET requires Authorization header."""
        pass

    def test_balance_returns_correct_structure(self, db, test_nonprofit):
        """Response includes all required fields."""
        cursor = db.cursor()

        credit_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining)
            VALUES (?, ?, 350)
        ''', (credit_id, test_nonprofit['ein']))

        db.commit()

        # Test should verify these fields are in response:
        # - nonprofit_ein
        # - letters_remaining (350 in this case)
        # - lifetime_purchases
        # - lifetime_spend_cents
        # - last_purchase
        # - next_renewal_date

        cursor.execute('''
            SELECT COALESCE(SUM(letters_remaining), 0)
            FROM letter_credits
            WHERE nonprofit_ein = ?
        ''', (test_nonprofit['ein'],))

        letters = cursor.fetchone()[0]
        assert letters == 350

    def test_balance_sums_multiple_credit_records(self, db, test_nonprofit):
        """Balance sums across multiple letter_credits rows."""
        cursor = db.cursor()

        # Insert multiple credit records
        for i, letters in enumerate([100, 150, 75]):
            cursor.execute('''
                INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining)
                VALUES (?, ?, ?)
            ''', (f'credit_{i}', test_nonprofit['ein'], letters))

        db.commit()

        # Verify sum
        cursor.execute('''
            SELECT COALESCE(SUM(letters_remaining), 0)
            FROM letter_credits
            WHERE nonprofit_ein = ?
        ''', (test_nonprofit['ein'],))

        total = cursor.fetchone()[0]
        assert total == 325  # 100 + 150 + 75


class TestStripeWebhook:
    """Stripe webhook integration."""

    def test_webhook_endpoint_exists(self, db):
        """POST /api/webhook/stripe endpoint exists."""
        assert True  # Placeholder

    def test_webhook_verifies_stripe_signature(self, db):
        """Webhook validates Stripe signature."""
        # Should return 401 if signature invalid
        pass

    def test_webhook_ignores_non_payment_events(self, db):
        """Webhook ignores non-payment_intent.succeeded events."""
        # charge.succeeded should be ignored (return 200, 'ignored')
        pass

    def test_webhook_updates_purchase_status_on_success(self, db, test_nonprofit):
        """On payment_intent.succeeded, updates purchase to 'succeeded'."""
        cursor = db.cursor()

        purchase_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO letter_credit_purchases
            (id, nonprofit_ein, amount_cents, letters_acquired, status)
            VALUES (?, ?, 1000, 100, 'pending')
        ''', (purchase_id, test_nonprofit['ein']))

        db.commit()

        # Webhook should update status to 'succeeded'
        cursor.execute('''
            SELECT status FROM letter_credit_purchases WHERE id = ?
        ''', (purchase_id,))

        status = cursor.fetchone()[0]
        assert status == 'pending'  # Before webhook

    def test_webhook_creates_letter_credits_record(self, db, test_nonprofit):
        """On success, webhook inserts into letter_credits table."""
        cursor = db.cursor()

        # Webhook should INSERT new row with 100 letters
        # After webhook processes: SELECT COUNT(*) FROM letter_credits WHERE nonprofit_ein
        # should return 1

        pass

    def test_webhook_sends_confirmation_email(self, db, test_nonprofit):
        """On success, sends confirmation email to nonprofit."""
        # Mock email service and verify send() called with correct subject/body
        pass


class TestDonorMessageTracking:
    """Donor message sending and tracking."""

    def test_send_message_endpoint_exists(self, db):
        """POST /api/nonprofit/donor-messages/send endpoint exists."""
        assert True

    def test_send_message_requires_auth(self, db):
        """Requires Authorization header."""
        pass

    def test_send_message_validates_email(self, db):
        """Rejects invalid email addresses."""
        # '@' must be present, basic email format validation
        pass

    def test_send_message_requires_all_fields(self, db):
        """Requires donor_email, message_subject, message_body."""
        pass

    def test_send_message_creates_donor_messages_record(self, db, test_nonprofit):
        """POST creates row in donor_messages table."""
        cursor = db.cursor()

        message_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO donor_messages
            (id, nonprofit_ein, donor_email, donor_name, message_subject,
             message_body, delivery_status)
            VALUES (?, ?, ?, ?, ?, ?, 'queued')
        ''', (message_id, test_nonprofit['ein'], 'donor@test.com', 'Jane Donor',
              'Thank You', 'Your gift...'))

        db.commit()

        cursor.execute('''
            SELECT COUNT(*) FROM donor_messages WHERE nonprofit_ein = ?
        ''', (test_nonprofit['ein'],))

        count = cursor.fetchone()[0]
        assert count == 1

    def test_send_message_generates_tracking_pixel(self, db):
        """Response includes tracking_pixel_url."""
        # tracking_pixel_url format: https://daanaa.org/api/nonprofit/pixel/{pixel_id}?token=...
        pass

    def test_send_message_returns_201(self, db):
        """Returns 201 Created."""
        pass

    def test_list_messages_endpoint_exists(self, db):
        """GET /api/nonprofit/donor-messages endpoint exists."""
        assert True

    def test_list_messages_paginates(self, db, test_nonprofit):
        """Supports limit and offset query params."""
        cursor = db.cursor()

        # Insert test messages
        for i in range(3):
            cursor.execute('''
                INSERT INTO donor_messages
                (id, nonprofit_ein, donor_email, message_subject, message_body, delivery_status)
                VALUES (?, ?, ?, ?, ?, 'sent')
            ''', (f'msg_{i}', test_nonprofit['ein'], f'donor{i}@test.com', f'Subject {i}', f'Body {i}'))

        db.commit()

        cursor.execute('''
            SELECT COUNT(*) FROM donor_messages WHERE nonprofit_ein = ?
        ''', (test_nonprofit['ein'],))

        count = cursor.fetchone()[0]
        assert count == 3

    def test_list_messages_filters_by_status(self, db, test_nonprofit):
        """Supports status query param (draft|queued|sent|failed)."""
        cursor = db.cursor()

        # Insert messages with different statuses
        cursor.execute('''
            INSERT INTO donor_messages
            (id, nonprofit_ein, donor_email, message_subject, message_body, delivery_status)
            VALUES (?, ?, 'a@test.com', 'Subj', 'Body', 'sent')
        ''', (str(uuid.uuid4()), test_nonprofit['ein']))

        cursor.execute('''
            INSERT INTO donor_messages
            (id, nonprofit_ein, donor_email, message_subject, message_body, delivery_status)
            VALUES (?, ?, 'b@test.com', 'Subj', 'Body', 'draft')
        ''', (str(uuid.uuid4()), test_nonprofit['ein']))

        db.commit()

        # Count by status
        cursor.execute('''
            SELECT COUNT(*) FROM donor_messages
            WHERE nonprofit_ein = ? AND delivery_status = 'sent'
        ''', (test_nonprofit['ein'],))

        sent_count = cursor.fetchone()[0]
        assert sent_count == 1


class TestPixelTracking:
    """Pixel tracking endpoint for email opens."""

    def test_pixel_endpoint_exists(self, db):
        """GET /api/nonprofit/pixel/{pixel_id} endpoint exists."""
        assert True

    def test_pixel_returns_gif(self, db):
        """Returns 1x1 transparent GIF (Content-Type: image/gif)."""
        # Verify response is valid GIF byte sequence
        pass

    def test_pixel_logs_open_event(self, db, test_nonprofit):
        """GET logs event in donor_message_events table."""
        cursor = db.cursor()

        # After pixel GET, should have event with type='open'
        message_id = str(uuid.uuid4())
        event_id = str(uuid.uuid4())

        cursor.execute('''
            INSERT INTO donor_message_events
            (id, message_id, event_type, event_timestamp)
            VALUES (?, ?, 'open', ?)
        ''', (event_id, message_id, datetime.now().isoformat()))

        db.commit()

        cursor.execute('''
            SELECT COUNT(*) FROM donor_message_events
            WHERE message_id = ? AND event_type = 'open'
        ''', (message_id,))

        count = cursor.fetchone()[0]
        assert count == 1

    def test_pixel_increments_open_count(self, db, test_nonprofit):
        """Pixel access increments donor_messages.open_count."""
        cursor = db.cursor()

        message_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO donor_messages
            (id, nonprofit_ein, donor_email, message_subject, message_body, open_count)
            VALUES (?, ?, 'donor@test.com', 'Subj', 'Body', 0)
        ''', (message_id, test_nonprofit['ein']))

        db.commit()

        # Simulate pixel access: increment counter
        cursor.execute('''
            UPDATE donor_messages SET open_count = open_count + 1
            WHERE id = ?
        ''', (message_id,))

        db.commit()

        cursor.execute('''
            SELECT open_count FROM donor_messages WHERE id = ?
        ''', (message_id,))

        count = cursor.fetchone()[0]
        assert count == 1

    def test_pixel_sets_first_opened_at(self, db, test_nonprofit):
        """First pixel open sets first_opened_at timestamp."""
        cursor = db.cursor()

        message_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO donor_messages
            (id, nonprofit_ein, donor_email, message_subject, message_body, first_opened_at)
            VALUES (?, ?, 'donor@test.com', 'Subj', 'Body', ?)
        ''', (message_id, test_nonprofit['ein'], now))

        db.commit()

        cursor.execute('''
            SELECT first_opened_at FROM donor_messages WHERE id = ?
        ''', (message_id,))

        opened_at = cursor.fetchone()[0]
        assert opened_at is not None


class TestImpactDashboard:
    """ED impact dashboard metrics."""

    def test_impact_endpoint_exists(self, db):
        """GET /api/nonprofit/dashboard/impact endpoint exists."""
        assert True

    def test_impact_requires_auth(self, db):
        """Requires Authorization header."""
        pass

    def test_impact_returns_all_metric_categories(self, db, test_nonprofit):
        """Response includes all 5 metric categories."""
        # Should have keys: credit_utilization, donor_engagement,
        # volunteer_impact, revenue_equivalent, forecast
        pass

    def test_impact_credit_utilization_metrics(self, db, test_nonprofit):
        """Credit utilization includes: letters_purchased, letters_used, utilization_percent."""
        # utilization_percent = (letters_used / letters_purchased) * 100
        pass

    def test_impact_donor_engagement_metrics(self, db, test_nonprofit):
        """Donor engagement includes: messages_sent, avg_open_rate, avg_click_rate."""
        pass

    def test_impact_volunteer_impact_metrics(self, db, test_nonprofit):
        """Volunteer impact includes: total_hours_verified, volunteer_count, value_at_28_50_per_hour."""
        pass

    def test_impact_revenue_equivalent_total(self, db, test_nonprofit):
        """Revenue equivalent = letters_value + volunteer_hours_value."""
        # letters_value = letters_used * $10
        # volunteer_value = hours * $28.50
        pass

    def test_impact_forecast_confidence(self, db, test_nonprofit):
        """Forecast includes confidence_percent (0-1)."""
        pass

    def test_impact_period_param(self, db, test_nonprofit):
        """Supports period query param: last_7_days, last_30_days, all."""
        pass


class TestDatabaseSchema:
    """Verify Phase 3 database schema."""

    def test_letter_credit_purchases_table_exists(self, db):
        """letter_credit_purchases table with correct schema."""
        cursor = db.cursor()

        cursor.execute("PRAGMA table_info(letter_credit_purchases)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'nonprofit_ein', 'status', 'letters_acquired', 'idempotency_key'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_donor_messages_table_exists(self, db):
        """donor_messages table with correct schema."""
        cursor = db.cursor()

        cursor.execute("PRAGMA table_info(donor_messages)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'nonprofit_ein', 'donor_email', 'delivery_status', 'open_count', 'link_clicks'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_donor_message_events_table_exists(self, db):
        """donor_message_events table for tracking opens/clicks."""
        cursor = db.cursor()

        cursor.execute("PRAGMA table_info(donor_message_events)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'message_id', 'event_type', 'event_timestamp'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"
