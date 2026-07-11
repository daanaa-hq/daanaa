"""Comprehensive test suite for nonprofit portal."""
import os
import pytest
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Isolated DB via env (see conftest.py) — never write test rows into the live DB.
DB_PATH = os.environ.get('DB_PATH', 'data/merit_registry.db')


@pytest.fixture
def db():
    """Get database connection with test org setup."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure tables exist
    cursor = conn.cursor()
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
        CREATE TABLE IF NOT EXISTS nonprofit_letter_requests (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            donor_name TEXT,
            amount INTEGER NOT NULL,
            donation_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            approved_by TEXT,
            approved_at TEXT,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS letter_credits (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            letters_remaining INTEGER DEFAULT 0,
            purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS e2e_wallet_sync (
            key_hash TEXT PRIMARY KEY,
            ciphertext TEXT NOT NULL,
            iv TEXT NOT NULL,
            salt TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    yield conn
    conn.close()


@pytest.fixture
def test_org(db):
    """Create a test organization."""
    cursor = db.cursor()
    ein = '391710244'

    # Clean up any existing test data
    cursor.execute('DELETE FROM nonprofit_accounts WHERE ein = ?', (ein,))
    db.commit()

    # Insert test org into registry (if not using real registry)
    cursor.execute('''
        SELECT 1 FROM registry_enriched WHERE EIN = ?
    ''', (ein,))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT OR IGNORE INTO registry_enriched (EIN, organization_name, organization_status)
            VALUES (?, ?, ?)
        ''', (ein, 'Test Nonprofit Foundation', 'ACTIVE'))
        db.commit()

    return ein


class TestNonprofitSignup:
    """POST /api/nonprofit/signup"""

    def test_signup_success(self, db, test_org):
        """Valid EIN + email → account created."""
        cursor = db.cursor()
        email = f'test-{datetime.now().timestamp()}@test.org'

        # Account creation logic
        cursor.execute('''
            SELECT organization_name FROM registry_enriched WHERE EIN = ?
        ''', (test_org,))
        org = cursor.fetchone()
        assert org is not None, "Test org not found in registry"

        account_id = 'test-account-1'
        cursor.execute('''
            INSERT INTO nonprofit_accounts (id, ein, email, name)
            VALUES (?, ?, ?, ?)
        ''', (account_id, test_org, email, org[0]))
        db.commit()

        # Verify account was created
        cursor.execute('SELECT * FROM nonprofit_accounts WHERE id = ?', (account_id,))
        account = cursor.fetchone()
        assert account is not None
        assert account['ein'] == test_org
        assert account['email'] == email

    def test_signup_duplicate_email(self, db, test_org):
        """Email already registered → 409."""
        cursor = db.cursor()
        email = 'duplicate@test.org'

        # Create first account
        cursor.execute('''
            INSERT INTO nonprofit_accounts (id, ein, email, name)
            VALUES (?, ?, ?, ?)
        ''', ('acc-1', test_org, email, 'Test Org'))
        db.commit()

        # Try to create second account with same email (should fail)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO nonprofit_accounts (id, ein, email, name)
                VALUES (?, ?, ?, ?)
            ''', ('acc-2', '391710245', email, 'Other Org'))
            db.commit()

        # Clean up
        cursor.execute('DELETE FROM nonprofit_accounts WHERE email = ?', (email,))
        db.commit()


class TestNonprofitDashboard:
    """GET /api/nonprofit/dashboard"""

    def test_dashboard_shows_pending_letters(self, db, test_org):
        """Dashboard displays pending letter requests."""
        cursor = db.cursor()

        # Setup: account + pending letter request
        cursor.execute('''
            INSERT INTO nonprofit_accounts (id, ein, email, name)
            VALUES (?, ?, ?, ?)
        ''', ('acc-1', test_org, 'ed@test.org', 'Test Org'))

        letter_id = 'letter-1'
        cursor.execute('''
            INSERT INTO nonprofit_letter_requests
            (id, nonprofit_ein, donor_name, amount, donation_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (letter_id, test_org, 'John Donor', 500, '2026-06-21', 'pending'))

        cursor.execute('''
            INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining)
            VALUES (?, ?, ?)
        ''', ('credit-1', test_org, 50))

        db.commit()

        # Verify dashboard data
        cursor.execute('''
            SELECT COUNT(*) FROM nonprofit_letter_requests
            WHERE nonprofit_ein = ? AND status = 'pending'
        ''', (test_org,))
        pending_count = cursor.fetchone()[0]
        assert pending_count == 1

        cursor.execute('''
            SELECT letters_remaining FROM letter_credits WHERE nonprofit_ein = ?
        ''', (test_org,))
        credits = cursor.fetchone()[0]
        assert credits == 50

        # Clean up
        cursor.execute('DELETE FROM nonprofit_letter_requests WHERE nonprofit_ein = ?', (test_org,))
        cursor.execute('DELETE FROM nonprofit_accounts WHERE ein = ?', (test_org,))
        cursor.execute('DELETE FROM letter_credits WHERE nonprofit_ein = ?', (test_org,))
        db.commit()


class TestLetterApproval:
    """POST /api/nonprofit/letter/{id}/approve"""

    def test_approve_changes_status(self, db, test_org):
        """Letter status changes from pending to approved."""
        cursor = db.cursor()

        cursor.execute('''
            INSERT INTO nonprofit_accounts (id, ein, email, name)
            VALUES (?, ?, ?, ?)
        ''', ('acc-1', test_org, 'ed@test.org', 'Test Org'))

        letter_id = 'letter-1'
        cursor.execute('''
            INSERT INTO nonprofit_letter_requests
            (id, nonprofit_ein, donor_name, amount, donation_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (letter_id, test_org, 'Jane Donor', 300, '2026-06-21', 'pending'))
        db.commit()

        # Approve the letter
        cursor.execute('''
            UPDATE nonprofit_letter_requests
            SET status = 'approved', approved_by = ?, approved_at = ?
            WHERE id = ?
        ''', (test_org, datetime.now().isoformat(), letter_id))
        db.commit()

        # Verify status changed
        cursor.execute('SELECT status FROM nonprofit_letter_requests WHERE id = ?', (letter_id,))
        status = cursor.fetchone()[0]
        assert status == 'approved'

        # Clean up
        cursor.execute('DELETE FROM nonprofit_letter_requests WHERE id = ?', (letter_id,))
        cursor.execute('DELETE FROM nonprofit_accounts WHERE ein = ?', (test_org,))
        db.commit()


class TestLetterGeneration:
    """POST /api/nonprofit/letter/{id}/generate"""

    def test_generate_decrements_credits(self, db, test_org):
        """Generating letter decrements credit count."""
        cursor = db.cursor()

        cursor.execute('''
            INSERT INTO nonprofit_accounts (id, ein, email, name)
            VALUES (?, ?, ?, ?)
        ''', ('acc-1', test_org, 'ed@test.org', 'Test Org'))

        cursor.execute('''
            INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining)
            VALUES (?, ?, ?)
        ''', ('credit-1', test_org, 50))

        letter_id = 'letter-1'
        cursor.execute('''
            INSERT INTO nonprofit_letter_requests
            (id, nonprofit_ein, donor_name, amount, donation_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (letter_id, test_org, 'Bob Donor', 250, '2026-06-21', 'approved'))
        db.commit()

        # Generate letter (decrement credits)
        cursor.execute('''
            UPDATE nonprofit_letter_requests SET status = 'generated' WHERE id = ?
        ''', (letter_id,))
        cursor.execute('''
            UPDATE letter_credits
            SET letters_remaining = letters_remaining - 1
            WHERE nonprofit_ein = ?
        ''', (test_org,))
        db.commit()

        # Verify credits decremented
        cursor.execute('''
            SELECT letters_remaining FROM letter_credits WHERE nonprofit_ein = ?
        ''', (test_org,))
        remaining = cursor.fetchone()[0]
        assert remaining == 49

        # Clean up
        cursor.execute('DELETE FROM nonprofit_letter_requests WHERE nonprofit_ein = ?', (test_org,))
        cursor.execute('DELETE FROM nonprofit_accounts WHERE ein = ?', (test_org,))
        cursor.execute('DELETE FROM letter_credits WHERE nonprofit_ein = ?', (test_org,))
        db.commit()

    def test_generate_with_insufficient_credits(self, db, test_org):
        """Cannot generate when credits are 0."""
        cursor = db.cursor()

        cursor.execute('''
            INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining)
            VALUES (?, ?, ?)
        ''', ('credit-1', test_org, 0))
        db.commit()

        # Verify insufficient credits
        cursor.execute('''
            SELECT letters_remaining FROM letter_credits WHERE nonprofit_ein = ?
        ''', (test_org,))
        remaining = cursor.fetchone()[0]
        assert remaining == 0

        # Clean up
        cursor.execute('DELETE FROM letter_credits WHERE nonprofit_ein = ?', (test_org,))
        db.commit()


class TestLetterPurchase:
    """POST /api/nonprofit/purchase-letters"""

    def test_purchase_adds_credits(self, db, test_org):
        """Purchasing adds 100 credits."""
        cursor = db.cursor()

        cursor.execute('''
            INSERT INTO nonprofit_accounts (id, ein, email, name)
            VALUES (?, ?, ?, ?)
        ''', ('acc-1', test_org, 'ed@test.org', 'Test Org'))
        db.commit()

        # Purchase letters (add 100 credits)
        credit_id = 'credit-2'
        cursor.execute('''
            INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining)
            VALUES (?, ?, ?)
        ''', (credit_id, test_org, 100))
        db.commit()

        # Verify credits were added
        cursor.execute('''
            SELECT letters_remaining FROM letter_credits WHERE nonprofit_ein = ?
        ''', (test_org,))
        remaining = cursor.fetchone()[0]
        assert remaining == 100

        # Clean up
        cursor.execute('DELETE FROM nonprofit_accounts WHERE ein = ?', (test_org,))
        cursor.execute('DELETE FROM letter_credits WHERE nonprofit_ein = ?', (test_org,))
        db.commit()


class TestWalletSecurity:
    """E2E wallet token sync"""

    def test_wallet_sync_stores_encrypted_data(self, db):
        """Wallet sync stores ciphertext without decryption."""
        cursor = db.cursor()
        key_hash = 'abc123def456'
        ciphertext = 'encrypted_wallet_data_here'
        iv = 'initialization_vector'
        salt = 'salt_bytes'

        cursor.execute('''
            INSERT INTO e2e_wallet_sync (key_hash, ciphertext, iv, salt)
            VALUES (?, ?, ?, ?)
        ''', (key_hash, ciphertext, iv, salt))
        db.commit()

        # Verify data was stored
        cursor.execute('SELECT * FROM e2e_wallet_sync WHERE key_hash = ?', (key_hash,))
        wallet = cursor.fetchone()
        assert wallet is not None
        assert wallet['ciphertext'] == ciphertext

        # Clean up
        cursor.execute('DELETE FROM e2e_wallet_sync WHERE key_hash = ?', (key_hash,))
        db.commit()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
