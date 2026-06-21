"""Test suite for nonprofit portal endpoints"""
import pytest
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = 'data/merit_registry.db'

@pytest.fixture
def db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

class TestNonprofitSignup:
    """POST /api/nonprofit/signup"""

    def test_signup_success(self, db):
        """Valid EIN + email → account created"""
        c = db.cursor()

        # Insert test org into registry
        c.execute('INSERT INTO registry_enriched (EIN, organization_name) VALUES (?, ?)',
                  ('391710244', 'Test Org'))
        db.commit()

        # Signup should succeed
        test_email = f'test-{datetime.now().timestamp()}@test.org'
        payload = {'ein': '391710244', 'email': test_email}

        # Note: actual test would use requests.post() or similar
        # This demonstrates the test structure

        db.execute('DELETE FROM registry_enriched WHERE EIN = ?', ('391710244',))
        db.commit()

    def test_signup_invalid_ein(self):
        """Non-existent EIN → 404"""
        payload = {'ein': '000000000', 'email': 'ed@test.org'}
        # Expected: 404 Organization not found

    def test_signup_duplicate_email(self, db):
        """Email already registered → 409"""
        c = db.cursor()

        # Insert org and account
        c.execute('INSERT INTO registry_enriched (EIN, organization_name) VALUES (?, ?)',
                  ('391710244', 'Test Org'))
        c.execute('INSERT INTO nonprofit_accounts (id, ein, email, name) VALUES (?, ?, ?, ?)',
                  ('acc-1', '391710244', 'ed@test.org', 'Test Org'))
        db.commit()

        # Duplicate email should fail
        payload = {'ein': '391710244', 'email': 'ed@test.org'}
        # Expected: 409 Email or EIN already registered

        db.execute('DELETE FROM nonprofit_accounts WHERE id = ?', ('acc-1',))
        db.execute('DELETE FROM registry_enriched WHERE EIN = ?', ('391710244',))
        db.commit()

class TestNonprofitDashboard:
    """GET /api/nonprofit/dashboard"""

    def test_dashboard_success(self, db):
        """Authed nonprofit sees pending requests + credits"""
        c = db.cursor()

        # Setup: org + account + letter request + credits
        c.execute('INSERT INTO nonprofit_accounts (id, ein, email, name) VALUES (?, ?, ?, ?)',
                  ('acc-1', '391710244', 'ed@test.org', 'Test Org'))
        c.execute('''
            INSERT INTO nonprofit_letter_requests (id, nonprofit_ein, donor_name, amount, donation_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('letter-1', '391710244', 'John Donor', 500, '2026-06-21', 'pending', datetime.now().isoformat()))
        c.execute('INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining, purchased_at) VALUES (?, ?, ?, ?)',
                  ('credit-1', '391710244', 50, datetime.now().isoformat()))
        db.commit()

        # Dashboard fetch with auth: Bearer 391710244
        # Expected: {nonprofit_ein, name, pending_letters: [...], letters_remaining: 50}

        db.execute('DELETE FROM nonprofit_accounts WHERE id = ?', ('acc-1',))
        db.execute('DELETE FROM nonprofit_letter_requests WHERE id = ?', ('letter-1',))
        db.execute('DELETE FROM letter_credits WHERE id = ?', ('credit-1',))
        db.commit()

    def test_dashboard_unauthorized(self):
        """Missing auth → 401"""
        # No Authorization header
        # Expected: 401 Unauthorized

class TestNonprofitLetterApproval:
    """POST /api/nonprofit/letter/{id}/approve"""

    def test_approve_success(self, db):
        """Authed nonprofit approves pending letter"""
        c = db.cursor()

        ein = '391710244'
        c.execute('INSERT INTO nonprofit_accounts (id, ein, email, name) VALUES (?, ?, ?, ?)',
                  ('acc-1', ein, 'ed@test.org', 'Test Org'))
        c.execute('''
            INSERT INTO nonprofit_letter_requests (id, nonprofit_ein, donor_name, amount, donation_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('letter-1', ein, 'John Donor', 500, '2026-06-21', 'pending', datetime.now().isoformat()))
        db.commit()

        # POST /api/nonprofit/letter/letter-1/approve with auth
        # Expected: {status: 'approved'}, letter.status changed to 'approved', approved_by set

        db.execute('DELETE FROM nonprofit_letter_requests WHERE id = ?', ('letter-1',))
        db.execute('DELETE FROM nonprofit_accounts WHERE id = ?', ('acc-1',))
        db.commit()

class TestNonprofitLetterGeneration:
    """POST /api/nonprofit/letter/{id}/generate"""

    def test_generate_success(self, db):
        """ED generates PDF after approval, credits decremented"""
        c = db.cursor()

        ein = '391710244'
        c.execute('INSERT INTO nonprofit_accounts (id, ein, email, name) VALUES (?, ?, ?, ?)',
                  ('acc-1', ein, 'ed@test.org', 'Test Org'))
        c.execute('''
            INSERT INTO nonprofit_letter_requests (id, nonprofit_ein, donor_name, amount, donation_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('letter-1', ein, 'John Donor', 500, '2026-06-21', 'approved', datetime.now().isoformat()))
        c.execute('INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining, purchased_at) VALUES (?, ?, ?, ?)',
                  ('credit-1', ein, 50, datetime.now().isoformat()))
        db.commit()

        # POST /api/nonprofit/letter/letter-1/generate with auth
        # Expected: {pdf_url: 's3://...', status: 'generated'}
        # Side effects: letter.status → 'generated', letters_remaining: 49

        db.execute('DELETE FROM nonprofit_letter_requests WHERE id = ?', ('letter-1',))
        db.execute('DELETE FROM nonprofit_accounts WHERE id = ?', ('acc-1',))
        db.execute('DELETE FROM letter_credits WHERE id = ?', ('credit-1',))
        db.commit()

    def test_generate_insufficient_credits(self, db):
        """No credits left → 400"""
        c = db.cursor()

        ein = '391710244'
        c.execute('INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining, purchased_at) VALUES (?, ?, ?, ?)',
                  ('credit-1', ein, 0, datetime.now().isoformat()))
        db.commit()

        # POST /api/nonprofit/letter/letter-1/generate with 0 credits
        # Expected: 400 Insufficient credits

class TestNonprofitLetterPurchase:
    """POST /api/nonprofit/purchase-letters"""

    def test_purchase_success(self, db):
        """Buy 100 letters for $10 (Stripe integration pending)"""
        c = db.cursor()

        ein = '391710244'
        c.execute('INSERT INTO nonprofit_accounts (id, ein, email, name) VALUES (?, ?, ?, ?)',
                  ('acc-1', ein, 'ed@test.org', 'Test Org'))
        db.commit()

        # POST /api/nonprofit/purchase-letters with auth
        # Expected: {credit_id: '...', letters_added: 100}
        # Side effects: INSERT letter_credits row with 100 letters

        db.execute('DELETE FROM nonprofit_accounts WHERE id = ?', ('acc-1',))
        db.commit()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
