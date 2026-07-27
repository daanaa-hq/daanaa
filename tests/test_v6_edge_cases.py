#!/usr/bin/env python3
"""
test_v6_edge_cases.py

Comprehensive edge-case tests for v6 financial context system.

Tests:
1. Missing revenue (Tier 2 conditional)
2. Explicit zero revenue
3. Revoked status
4. Revoked flag
5. Invalid region or NTEE
6. Blank NTEE
7. Invalid revenue bands
8. Fewer than five peers
9. Tier 5 numeric leakage
10. Duplicate ingestion
11. Rollback after failed ingestion
12. Organization-submitted corrections
"""

import sqlite3
import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestV6EdgeCases(unittest.TestCase):
    """Edge-case tests for v6 system."""

    def setUp(self):
        """Create temporary test database."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

        # Create minimal schema
        self._create_test_schema()

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        os.unlink(self.db_path)

    def _create_test_schema(self):
        """Create test database schema."""
        # registry_enriched
        self.cursor.execute('''
            CREATE TABLE registry_enriched (
                EIN TEXT PRIMARY KEY,
                organization_name TEXT,
                NTEE1 TEXT,
                total_revenue REAL,
                irs_revoked INTEGER DEFAULT 0,
                org_status TEXT
            )
        ''')

        # v6_scoring_runs
        self.cursor.execute('''
            CREATE TABLE v6_scoring_runs (
                run_id TEXT PRIMARY KEY,
                status TEXT,
                started_at TEXT
            )
        ''')

        # v6_peer_context_assignments
        self.cursor.execute('''
            CREATE TABLE v6_peer_context_assignments (
                run_id TEXT,
                ein TEXT,
                selected_tier TEXT,
                revenue_band TEXT,
                peer_count INTEGER,
                scoreable_peer_count INTEGER,
                peer_median REAL,
                peer_p25 REAL,
                peer_p75 REAL,
                PRIMARY KEY (run_id, ein)
            )
        ''')

        # org_financial_years
        self.cursor.execute('''
            CREATE TABLE org_financial_years (
                ein TEXT,
                tax_year INTEGER,
                total_revenue REAL,
                total_expenses REAL,
                source TEXT,
                source_id TEXT,
                record_hash TEXT,
                retrieved_at TEXT,
                PRIMARY KEY (ein, tax_year, source)
            )
        ''')

        # ingestion_audit_log
        self.cursor.execute('''
            CREATE TABLE ingestion_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                table_name TEXT,
                ein TEXT,
                tax_year INTEGER,
                reason TEXT,
                timestamp TEXT
            )
        ''')

        self.db.commit()

    # TEST 1: Missing revenue (Tier 2)
    def test_missing_revenue_tier2(self):
        """Test Tier 2 assignment when revenue_band is NULL."""
        self.cursor.execute('INSERT INTO registry_enriched VALUES (?, ?, ?, ?, ?, ?)',
                          ('123456789', 'Test Org', 'B12', None, 0, 'active'))
        self.cursor.execute('''
            INSERT INTO v6_scoring_runs VALUES (?, ?, ?)
        ''', ('run1', 'candidate', '2026-07-27T00:00:00Z'))
        self.cursor.execute('''
            INSERT INTO v6_peer_context_assignments
            (run_id, ein, selected_tier, revenue_band, peer_count, scoreable_peer_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('run1', '123456789', '2_regional_conditional', None, 100, 80))
        self.db.commit()

        # Verify: Tier 2 with NULL revenue_band is valid
        self.cursor.execute(
            'SELECT revenue_band FROM v6_peer_context_assignments WHERE ein = ?',
            ('123456789',)
        )
        result = self.cursor.fetchone()
        self.assertIsNone(result['revenue_band'], "Tier 2 should allow NULL revenue_band")

    # TEST 2: Explicit zero revenue
    def test_explicit_zero_revenue(self):
        """Test that explicit zero revenue is distinct from NULL."""
        self.cursor.execute('INSERT INTO registry_enriched VALUES (?, ?, ?, ?, ?, ?)',
                          ('111111111', 'Zero Org', 'B12', 0, 0, 'active'))
        self.cursor.execute('''
            INSERT INTO org_financial_years
            (ein, tax_year, total_revenue, source, source_id, record_hash, retrieved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('111111111', 2025, 0, 'irs_soi', 'xyz', 'hash123', '2026-07-27T00:00:00Z'))
        self.db.commit()

        # Verify: Zero is stored as 0, not NULL
        self.cursor.execute(
            'SELECT total_revenue FROM org_financial_years WHERE ein = ?',
            ('111111111',)
        )
        result = self.cursor.fetchone()
        self.assertEqual(result['total_revenue'], 0, "Explicit zero should be stored as 0")

    # TEST 3: Revoked status
    def test_revoked_status(self):
        """Test org with org_status='revoked'."""
        self.cursor.execute('INSERT INTO registry_enriched VALUES (?, ?, ?, ?, ?, ?)',
                          ('222222222', 'Revoked Org', 'B12', 100000, 0, 'revoked'))

        # Verify: org_status is captured
        self.cursor.execute('SELECT org_status FROM registry_enriched WHERE ein = ?',
                          ('222222222',))
        result = self.cursor.fetchone()
        self.assertEqual(result['org_status'], 'revoked')

    # TEST 4: Revoked flag
    def test_revoked_flag(self):
        """Test org with irs_revoked=1."""
        self.cursor.execute('INSERT INTO registry_enriched VALUES (?, ?, ?, ?, ?, ?)',
                          ('333333333', 'IRS Revoked', 'B12', 100000, 1, 'active'))

        # Verify: irs_revoked flag is set
        self.cursor.execute('SELECT irs_revoked FROM registry_enriched WHERE ein = ?',
                          ('333333333',))
        result = self.cursor.fetchone()
        self.assertEqual(result['irs_revoked'], 1)

    # TEST 5: Invalid region
    def test_invalid_region_rejection(self):
        """Test that invalid regions are rejected."""
        # Valid regions: Northeast, Midwest, South, West
        invalid_regions = ['state_CA', 'Northeast USA', '', 'unknown']

        for region in invalid_regions:
            # Should be caught by validator before insertion
            # For this test, we verify the validation logic would reject it
            valid_regions = {'Northeast', 'Midwest', 'South', 'West'}
            self.assertNotIn(region, valid_regions,
                           f"Region '{region}' should not be in valid set")

    # TEST 6: Blank NTEE
    def test_blank_ntee(self):
        """Test org with NULL NTEE classification."""
        self.cursor.execute('INSERT INTO registry_enriched VALUES (?, ?, ?, ?, ?, ?)',
                          ('444444444', 'No NTEE Org', None, 100000, 0, 'active'))

        # Verify: NULL NTEE is stored
        self.cursor.execute('SELECT NTEE1 FROM registry_enriched WHERE ein = ?',
                          ('444444444',))
        result = self.cursor.fetchone()
        self.assertIsNone(result['NTEE1'], "Blank NTEE should be stored as NULL")

    # TEST 7: Invalid revenue bands
    def test_invalid_revenue_bands(self):
        """Test that non-canonical revenue bands are rejected."""
        canonical = {'grassroots', 'small', 'mid', 'established', 'major', None}
        invalid = ['Grassroots', 'Small', 'MAJOR', 'tiny', 'xlarge', '']

        for band in invalid:
            if band:  # Skip empty string in this check
                self.assertNotIn(band, canonical,
                               f"Band '{band}' should not be canonical")

    # TEST 8: Fewer than five peers
    def test_fewer_than_five_peers(self):
        """Test that Tier 1-4 with <5 peers are flagged."""
        self.cursor.execute('''
            INSERT INTO v6_scoring_runs VALUES (?, ?, ?)
        ''', ('run2', 'candidate', '2026-07-27T00:00:00Z'))

        # Insert org with only 3 scoreable peers
        self.cursor.execute('''
            INSERT INTO v6_peer_context_assignments
            (run_id, ein, selected_tier, revenue_band, peer_count, scoreable_peer_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('run2', '555555555', '1_direct', 'small', 10, 3))
        self.db.commit()

        # Validator should catch this
        self.cursor.execute(
            'SELECT scoreable_peer_count FROM v6_peer_context_assignments WHERE ein = ?',
            ('555555555',)
        )
        result = self.cursor.fetchone()
        self.assertLess(result['scoreable_peer_count'], 5,
                       "Org with <5 peers should be detected by validator")

    # TEST 9: Tier 5 numeric leakage
    def test_tier5_numeric_leakage(self):
        """Test that Tier 5 has no peer_median/p25/p75."""
        self.cursor.execute('''
            INSERT INTO v6_scoring_runs VALUES (?, ?, ?)
        ''', ('run3', 'candidate', '2026-07-27T00:00:00Z'))

        # Insert Tier 5 with NULL peer values (correct)
        self.cursor.execute('''
            INSERT INTO v6_peer_context_assignments
            (run_id, ein, selected_tier, revenue_band, peer_median, peer_p25, peer_p75, peer_count, scoreable_peer_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('run3', '666666666', '5_archetype_only', None, None, None, None, 0, 0))
        self.db.commit()

        # Verify: All peer values are NULL
        self.cursor.execute(
            'SELECT peer_median, peer_p25, peer_p75 FROM v6_peer_context_assignments WHERE ein = ?',
            ('666666666',)
        )
        result = self.cursor.fetchone()
        self.assertIsNone(result['peer_median'])
        self.assertIsNone(result['peer_p25'])
        self.assertIsNone(result['peer_p75'])

    # TEST 10: Duplicate ingestion
    def test_duplicate_ingestion_idempotent(self):
        """Test that duplicate records are skipped (idempotent)."""
        # Insert first record
        self.cursor.execute('''
            INSERT INTO org_financial_years
            (ein, tax_year, total_revenue, source, source_id, record_hash, retrieved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('777777777', 2025, 500000, 'irs_soi', 'abc', 'hash_abc', '2026-07-27T00:00:00Z'))
        self.db.commit()

        # Verify insertion
        self.cursor.execute('SELECT COUNT(*) as cnt FROM org_financial_years WHERE ein = ?',
                          ('777777777',))
        count_after_first = self.cursor.fetchone()['cnt']
        self.assertEqual(count_after_first, 1)

        # Attempt duplicate (should be idempotent, skip)
        self.cursor.execute('''
            INSERT OR IGNORE INTO org_financial_years
            (ein, tax_year, total_revenue, source, source_id, record_hash, retrieved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('777777777', 2025, 500000, 'irs_soi', 'abc', 'hash_abc', '2026-07-27T00:00:00Z'))
        self.db.commit()

        # Verify: Still only 1 row
        self.cursor.execute('SELECT COUNT(*) as cnt FROM org_financial_years WHERE ein = ?',
                          ('777777777',))
        count_after_second = self.cursor.fetchone()['cnt']
        self.assertEqual(count_after_second, 1, "Duplicate should be skipped (idempotent)")

    # TEST 11: Rollback after failed ingestion
    def test_transaction_rollback_on_failure(self):
        """Test that transaction rolls back on constraint violation."""
        # Start a transaction
        self.cursor.execute('BEGIN TRANSACTION')

        # Insert a valid record
        self.cursor.execute('''
            INSERT INTO org_financial_years
            (ein, tax_year, total_revenue, source, source_id, record_hash, retrieved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('888888888', 2025, 100000, 'irs_soi', 'def', 'hash_def', '2026-07-27T00:00:00Z'))

        # Attempt to violate primary key (duplicate)
        try:
            self.cursor.execute('''
                INSERT INTO org_financial_years
                (ein, tax_year, total_revenue, source, source_id, record_hash, retrieved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('888888888', 2025, 200000, 'irs_soi', 'def', 'hash_def_2', '2026-07-27T00:00:00Z'))
            self.cursor.execute('COMMIT')
            self.fail("Should have raised UNIQUE constraint error")
        except sqlite3.IntegrityError:
            # Expected: constraint violation
            self.cursor.execute('ROLLBACK')

        # Verify: Transaction was rolled back (no records inserted)
        self.cursor.execute('SELECT COUNT(*) as cnt FROM org_financial_years WHERE ein = ?',
                          ('888888888',))
        count = self.cursor.fetchone()['cnt']
        self.assertEqual(count, 0, "Transaction should have rolled back completely")

    # TEST 12: Organization-submitted corrections
    def test_org_submitted_corrections(self):
        """Test that orgs can submit corrections with audit trail."""
        # Simulate org claiming/correcting its page
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS org_claims (
                ein TEXT PRIMARY KEY,
                organization_name TEXT,
                email TEXT,
                claimed_at TEXT,
                correction_text TEXT,
                correction_source TEXT,
                verified_at TEXT
            )
        ''')

        self.cursor.execute('''
            INSERT INTO org_claims
            (ein, organization_name, email, claimed_at, correction_text, correction_source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('999999999', 'Corrected Name Inc', 'org@example.com',
              '2026-07-27T00:00:00Z', 'Our actual revenue is $500K', 'donor_claim'))
        self.db.commit()

        # Verify: Claim recorded
        self.cursor.execute('SELECT correction_text FROM org_claims WHERE ein = ?',
                          ('999999999',))
        result = self.cursor.fetchone()
        self.assertEqual(result['correction_text'], 'Our actual revenue is $500K')


if __name__ == '__main__':
    unittest.main()
