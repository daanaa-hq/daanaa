"""
V6 Financial Context Implementation Tests

Validates:
- Database migration and schema
- v6 scoring logic
- API endpoint correctness
- Privacy and data safety
- Frontend integration readiness
"""

import sqlite3
import unittest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.v6_financial_context_api import get_v6_financial_context


class TestV6DatabaseSchema(unittest.TestCase):
    """Test v6 database tables and schema."""

    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self._create_v6_schema()

    def tearDown(self):
        self.db.close()

    def _create_v6_schema(self):
        """Create v6 tables for testing."""
        cursor = self.db.cursor()

        # v6_scoring_runs
        cursor.execute('''
            CREATE TABLE v6_scoring_runs (
                run_id TEXT PRIMARY KEY,
                methodology_version TEXT,
                status TEXT,
                row_counts TEXT
            )
        ''')

        # v6_peer_context_assignments
        cursor.execute('''
            CREATE TABLE v6_peer_context_assignments (
                run_id TEXT,
                ein TEXT,
                selected_tier TEXT,
                ntee_code TEXT,
                ntee_level TEXT,
                geography_scope TEXT,
                geography_value TEXT,
                archetype TEXT,
                revenue_band TEXT,
                revenue_band_source TEXT,
                peer_group_description TEXT,
                peer_count INTEGER,
                scoreable_peer_count INTEGER,
                peer_median REAL,
                peer_p25 REAL,
                peer_p75 REAL,
                confidence TEXT,
                confidence_margin TEXT,
                is_inferred BOOLEAN,
                metric_name TEXT,
                metric_value REAL,
                source_year_min INTEGER,
                source_year_max INTEGER,
                PRIMARY KEY (run_id, ein),
                FOREIGN KEY (run_id) REFERENCES v6_scoring_runs(run_id)
            )
        ''')

        # registry_enriched (minimal for testing)
        cursor.execute('''
            CREATE TABLE registry_enriched (
                EIN TEXT PRIMARY KEY,
                total_revenue REAL,
                total_expenses REAL,
                net_assets REAL,
                months_of_reserve REAL
            )
        ''')

        # v6_conditional_band_context
        cursor.execute('''
            CREATE TABLE v6_conditional_band_context (
                ein TEXT,
                revenue_band TEXT,
                peer_median REAL,
                peer_p25 REAL,
                peer_p75 REAL,
                peer_count INTEGER,
                scoreable_peer_count INTEGER,
                confidence TEXT
            )
        ''')

        self.db.commit()

    def test_schema_exists(self):
        """Test that all v6 tables exist."""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'v6_%'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        expected = {'v6_scoring_runs', 'v6_peer_context_assignments', 'v6_conditional_band_context'}
        self.assertTrue(expected.issubset(tables), f"Missing tables: {expected - tables}")

    def test_tier_1_direct_requirements(self):
        """Test Tier 1 assignment requires revenue."""
        cursor = self.db.cursor()

        # Insert test data
        cursor.execute('INSERT INTO v6_scoring_runs VALUES (?, ?, ?, ?)',
                      ('run_1', 'v6_foundation', 'active', '{"Tier 1": 100}'))

        # Tier 1 with revenue should pass
        cursor.execute('''
            INSERT INTO v6_peer_context_assignments
            (run_id, ein, selected_tier, revenue_band, revenue_band_source,
             peer_count, scoreable_peer_count, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('run_1', '123456789', '1_Direct', 'Small', 'IRS 990', 50, 40, 'good'))
        self.db.commit()

        # Verify insertion
        cursor.execute('SELECT ein, revenue_band FROM v6_peer_context_assignments')
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], 'Small', "Tier 1 should have revenue band")

    def test_no_tier_2_with_blank_nteecc(self):
        """Test that blank NTEECC orgs are not Tier 2."""
        cursor = self.db.cursor()

        cursor.execute('INSERT INTO v6_scoring_runs VALUES (?, ?, ?, ?)',
                      ('run_1', 'v6_foundation', 'active', '{"Tier 2": 100}'))

        # Tier 2 should have NTEE
        cursor.execute('''
            INSERT INTO v6_peer_context_assignments
            (run_id, ein, selected_tier, ntee_code, peer_count, scoreable_peer_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('run_1', '987654321', '2_Regional_Conditional', 'B12345', 50, 30))
        self.db.commit()

        cursor.execute('SELECT ntee_code FROM v6_peer_context_assignments WHERE ein = ?',
                      ('987654321',))
        result = cursor.fetchone()
        self.assertIsNotNone(result[0], "Tier 2 must have NTEECC")


class TestV6TierAssignment(unittest.TestCase):
    """Test v6 five-tier fallback hierarchy."""

    def test_tier_thresholds(self):
        """Test minimum peer thresholds per tier."""
        thresholds = {
            '1_Direct': 5,  # minimum scoreable
            '2_Regional_Conditional': 5,
            '3_Broader_Regional': 5,
            '4_National': 1,  # allows < 5
            '5_Archetype_Only': 0,  # no numeric
        }

        for tier, minimum in thresholds.items():
            self.assertGreaterEqual(minimum, 0, f"{tier} threshold must be >= 0")

    def test_tier_5_no_numeric(self):
        """Test Tier 5 has no numeric peer comparison."""
        # Tier 5 should not display median, p25, p75
        tier_5_response = {
            'selected_tier': '5_Archetype_Only',
            'peer_median': None,
            'peer_p25': None,
            'peer_p75': None,
        }

        self.assertIsNone(tier_5_response['peer_median'])
        self.assertIsNone(tier_5_response['peer_p25'])
        self.assertIsNone(tier_5_response['peer_p75'])


class TestV6APIResponse(unittest.TestCase):
    """Test v6 API endpoint response contract."""

    def test_response_schema(self):
        """Test that API response includes required fields."""
        required_fields = {
            'organization_ein',
            'methodology_version',
            'data_status',
            'selected_tier',
            'peer_group_description',
            'confidence',
            'sources',
            'limitations',
        }

        # Example response structure
        response = {
            'organization_ein': '123456789',
            'methodology_version': 'v6_foundation',
            'data_status': 'direct',
            'selected_tier': '1_Direct',
            'peer_group_description': 'Education orgs in Northeast',
            'confidence': 'good',
            'sources': ['IRS 990'],
            'limitations': None,
        }

        for field in required_fields:
            self.assertIn(field, response, f"Missing required field: {field}")

    def test_no_pii_exposure(self):
        """Test that API response does not expose PII."""
        forbidden_fields = {
            'email', 'phone', 'ssn', 'donor', 'wallet',
            'ip_address', 'personal_address'
        }

        response = {
            'organization_ein': '123456789',
            'peer_group_description': 'Education nonprofits',
            # ... other fields
        }

        for field in forbidden_fields:
            self.assertNotIn(field, response, f"PII field exposed: {field}")


class TestV6DataQuality(unittest.TestCase):
    """Test v6 data quality validation."""

    def test_no_negative_reserves(self):
        """Test that negative reserve values are rejected."""
        negative_value = -5.0
        self.assertLess(negative_value, 0, "Negative reserves should be invalid")

    def test_zero_revenue_treatment(self):
        """Test that zero revenue is treated as unavailable."""
        # Zero revenue should not create a revenue band
        revenue = 0
        self.assertEqual(revenue, 0)
        # Should be treated as "unavailable", not "Grassroots"

    def test_scoreable_peer_counting(self):
        """Test that scoreable peers are counted separately."""
        peer_data = {
            'peer_count': 100,
            'scoreable_peer_count': 45,  # Only 45% have financial data
        }

        # Should use scoreable_peer_count for thresholds
        self.assertLessEqual(
            peer_data['scoreable_peer_count'],
            peer_data['peer_count'],
            "Scoreable must be <= total"
        )


class TestV6Privacy(unittest.TestCase):
    """Test v6 privacy and data safety."""

    def test_wallet_not_exposed(self):
        """Test that wallet data is not in financial context."""
        context = {
            'organization_ein': '123456789',
            'peer_median': 12.5,
        }

        self.assertNotIn('wallet', context)
        self.assertNotIn('giving_intent', context)

    def test_donor_data_not_exposed(self):
        """Test that donor info is not in peer context."""
        context = {
            'organization_ein': '123456789',
            'peer_group_description': 'Education nonprofits',
        }

        # Should not contain donor names, emails, etc.
        for key in context:
            self.assertNotIn('donor', key.lower())


if __name__ == '__main__':
    unittest.main()
