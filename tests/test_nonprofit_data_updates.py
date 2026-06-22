#!/usr/bin/env python3
"""
Tests for nonprofit data update endpoint.
Tests the claiming flow data transparency + update submission.
"""
import json
import sqlite3
import unittest
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from daanaa_api import app, DB_PATH

class NonprofitDataUpdateTests(unittest.TestCase):
    """Test nonprofit data update endpoint."""

    def setUp(self):
        """Set up test client and database."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.db_path = DB_PATH

        # Create a test claim for EIN 12-3456789
        self.test_ein = '12-3456789'
        self.claim_token = 'test-token-xyz123'

        # Ensure test org exists in registry
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check if org exists
        c.execute('SELECT EIN FROM registry_enriched WHERE EIN = ?', (self.test_ein,))
        if not c.fetchone():
            # Insert minimal test org
            c.execute('''
                INSERT INTO registry_enriched (EIN, organization_name, total_revenue, total_expenses,
                                               program_expense_pct, months_of_reserve, latest_tax_year)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.test_ein, 'Test Nonprofit', 2900000, 2700000, 78, 2.5, 2024))

        # Create test claim
        c.execute('''
            INSERT OR REPLACE INTO org_claims
            (ein, email, irs_address, pin, pin_expires_at, claim_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.test_ein, 'test@example.com', '123 Test St', 'pin123',
              '2099-12-31 23:59:59', 'verified'))

        conn.commit()
        conn.close()

    def test_submit_nonprofit_update_success(self):
        """Test successful nonprofit data submission."""
        payload = {
            "claim_token": self.claim_token,
            "ein": self.test_ein,
            "updates": {
                "total_revenue": 3100000,
                "total_expenses": 2850000,
                "program_expense_pct": 81,
                "months_of_reserve": 3.2
            },
            "explanation": "2024 was a stronger year"
        }

        response = self.client.post('/api/nonprofit/update-data',
                                   data=json.dumps(payload),
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'received')
        self.assertIn('update_id', data)
        self.assertIsNotNone(data['update_id'])

    def test_submit_nonprofit_update_invalid_revenue(self):
        """Test rejection of negative revenue."""
        payload = {
            "claim_token": self.claim_token,
            "ein": self.test_ein,
            "updates": {
                "total_revenue": -1000000  # Invalid
            },
            "explanation": "Test"
        }

        response = self.client.post('/api/nonprofit/update-data',
                                   data=json.dumps(payload),
                                   content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('errors', data)

    def test_submit_nonprofit_update_invalid_program_pct(self):
        """Test rejection of invalid program expense percentage."""
        payload = {
            "claim_token": self.claim_token,
            "ein": self.test_ein,
            "updates": {
                "program_expense_pct": 150  # Invalid (> 100)
            },
            "explanation": "Test"
        }

        response = self.client.post('/api/nonprofit/update-data',
                                   data=json.dumps(payload),
                                   content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('errors', data)

    def test_submit_nonprofit_update_missing_claim_token(self):
        """Test rejection when claim_token is missing."""
        payload = {
            "ein": self.test_ein,
            "updates": {"total_revenue": 3100000},
            "explanation": "Test"
        }

        response = self.client.post('/api/nonprofit/update-data',
                                   data=json.dumps(payload),
                                   content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_get_nonprofit_update_status(self):
        """Test retrieving update status."""
        # First submit an update
        payload = {
            "claim_token": self.claim_token,
            "ein": self.test_ein,
            "updates": {"total_revenue": 3100000},
            "explanation": "Test"
        }

        response = self.client.post('/api/nonprofit/update-data',
                                   data=json.dumps(payload),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        update_id = json.loads(response.data)['update_id']

        # Now get status
        response = self.client.get(f'/api/nonprofit/update-status/{update_id}?claim_token={self.claim_token}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['update_id'], update_id)
        self.assertEqual(data['status'], 'pending_review')

    def test_nonprofit_update_stored_in_database(self):
        """Test that update is actually stored in database."""
        payload = {
            "claim_token": self.claim_token,
            "ein": self.test_ein,
            "updates": {
                "total_revenue": 3100000,
                "total_expenses": 2850000
            },
            "explanation": "Test explanation"
        }

        response = self.client.post('/api/nonprofit/update-data',
                                   data=json.dumps(payload),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        update_id = json.loads(response.data)['update_id']

        # Verify in database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT id, ein, status, submitted_total_revenue, submitted_total_expenses, submitted_explanation
            FROM org_nonprofit_updates
            WHERE id = ?
        ''', (update_id,))
        row = c.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], update_id)
        self.assertEqual(row[1], self.test_ein)
        self.assertEqual(row[2], 'pending_review')
        self.assertEqual(row[3], 3100000)
        self.assertEqual(row[4], 2850000)
        self.assertEqual(row[5], 'Test explanation')

    def test_sanity_check_flagging(self):
        """Test that large changes trigger sanity_check_failed flag."""
        payload = {
            "claim_token": self.claim_token,
            "ein": self.test_ein,
            "updates": {
                "total_revenue": 10000000  # ~244% increase from $2.9M
            },
            "explanation": "Major growth"
        }

        response = self.client.post('/api/nonprofit/update-data',
                                   data=json.dumps(payload),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        update_id = json.loads(response.data)['update_id']

        # Check sanity flag in database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT sanity_check_failed FROM org_nonprofit_updates WHERE id = ?', (update_id,))
        flagged = c.fetchone()[0]
        conn.close()

        self.assertEqual(flagged, 1)

    def tearDown(self):
        """Clean up test data."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM org_nonprofit_updates WHERE ein = ?', (self.test_ein,))
        c.execute('DELETE FROM org_claims WHERE ein = ?', (self.test_ein,))
        # Don't delete from registry_enriched to avoid breaking other tests
        conn.commit()
        conn.close()


if __name__ == '__main__':
    unittest.main()
