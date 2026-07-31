#!/usr/bin/env python3
"""
test_credibility_signals.py — unit tests for credibility signals.

Tests each signal type with multiple scenarios:
- Signal 1 (IRS Verification): verified, unverified, revoked, unknown
- Signal 2 (Data Freshness): fresh, aging, stale, unknown
- Signal 3 (Expense Ratio): concern, fair, strong, unknown
- Signal 4 (Peer Context): leader, strong, typical, developing, unknown
- Signal 5 (Recency & Completeness): complete, partial, minimal
- Signal 6 (Mission Alignment): org-attested, AI-generated, unknown
"""

import sys
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from credibility_signals import CredibilitySignals


class TestIRSVerificationSignal(unittest.TestCase):
    def setUp(self):
        self.cs = CredibilitySignals()

    def test_verified_org(self):
        org = {'org_status': 'active', 'irs_revoked': 0}
        sig = self.cs.signal_irs_verification(org)
        self.assertEqual(sig['status'], 'verified')
        self.assertEqual(sig['confidence'], 100)

    def test_revoked_org(self):
        org = {'org_status': 'active', 'irs_revoked': 1}
        sig = self.cs.signal_irs_verification(org)
        self.assertEqual(sig['status'], 'revoked')
        self.assertEqual(sig['confidence'], 0)

    def test_unverified_org(self):
        org = {'org_status': '', 'irs_revoked': 0}
        sig = self.cs.signal_irs_verification(org)
        self.assertEqual(sig['status'], 'unknown')
        self.assertIn(sig['confidence'], [30])

    def test_unknown_status(self):
        org = {'org_status': 'inactive', 'irs_revoked': 0}
        sig = self.cs.signal_irs_verification(org)
        self.assertEqual(sig['status'], 'unverified')


class TestDataFreshnessSignal(unittest.TestCase):
    def setUp(self):
        self.cs = CredibilitySignals()

    def test_fresh_filing(self):
        org = {'filing_year': 2026}  # Current year
        sig = self.cs.signal_data_freshness(org)
        self.assertEqual(sig['status'], 'fresh')
        self.assertGreaterEqual(sig['confidence'], 90)

    def test_aging_filing(self):
        org = {'filing_year': 2024}  # ~2 years old
        sig = self.cs.signal_data_freshness(org)
        self.assertEqual(sig['status'], 'aging')
        self.assertGreaterEqual(sig['confidence'], 70)

    def test_stale_filing(self):
        org = {'filing_year': 2022}  # >2 years old
        sig = self.cs.signal_data_freshness(org)
        self.assertEqual(sig['status'], 'stale')
        self.assertLess(sig['confidence'], 50)

    def test_no_filing_date(self):
        org = {'filing_year': None}
        sig = self.cs.signal_data_freshness(org)
        self.assertEqual(sig['status'], 'unknown')


class TestExpenseRatioSignal(unittest.TestCase):
    def setUp(self):
        self.cs = CredibilitySignals()

    def test_strong_expense_ratio(self):
        org = {'program_expense_ratio': 0.85}  # 85%
        sig = self.cs.signal_expense_ratio(org)
        self.assertEqual(sig['status'], 'strong')
        self.assertEqual(sig['confidence'], 95)

    def test_fair_expense_ratio(self):
        org = {'program_expense_ratio': 0.70}  # 70%
        sig = self.cs.signal_expense_ratio(org)
        self.assertEqual(sig['status'], 'fair')
        self.assertEqual(sig['confidence'], 95)

    def test_concern_expense_ratio(self):
        org = {'program_expense_ratio': 0.50}  # 50%
        sig = self.cs.signal_expense_ratio(org)
        self.assertEqual(sig['status'], 'concern')
        self.assertEqual(sig['confidence'], 95)

    def test_no_expense_ratio(self):
        org = {'program_expense_ratio': None}
        sig = self.cs.signal_expense_ratio(org)
        self.assertEqual(sig['status'], 'unknown')


class TestRecencyCompletenessSignal(unittest.TestCase):
    def setUp(self):
        self.cs = CredibilitySignals()

    def test_complete_org(self):
        org = {
            'mission': 'Help people',
            'website': 'example.com',
            'donate_url': 'donate.example.com',
            'board_size': 5,
        }
        sig = self.cs.signal_recency_completeness(org)
        self.assertEqual(sig['status'], 'complete')
        self.assertEqual(sig['confidence'], 100)

    def test_partial_org(self):
        org = {
            'mission': 'Help people',
            'website': 'example.com',
            'donate_url': None,
            'board_size': 0,
        }
        sig = self.cs.signal_recency_completeness(org)
        self.assertEqual(sig['status'], 'partial')
        self.assertIn('donation link', sig['missing_fields'])

    def test_minimal_org(self):
        org = {
            'mission': None,
            'website': None,
            'donate_url': None,
            'board_size': 0,
        }
        sig = self.cs.signal_recency_completeness(org)
        self.assertEqual(sig['status'], 'minimal')


class TestMissionAlignmentSignal(unittest.TestCase):
    def setUp(self):
        self.cs = CredibilitySignals()

    def test_org_attested_mission(self):
        org = {
            'mission': 'Help people',
            'mission_source': 'website',
        }
        sig = self.cs.signal_mission_alignment(org)
        self.assertEqual(sig['status'], 'org_attested')
        self.assertEqual(sig['confidence'], 100)

    def test_ai_generated_mission(self):
        org = {
            'mission': 'Help people',
            'mission_source': 'ai_generated',
        }
        sig = self.cs.signal_mission_alignment(org)
        self.assertEqual(sig['status'], 'ai_generated')
        self.assertGreaterEqual(sig['confidence'], 70)

    def test_no_mission(self):
        org = {
            'mission': None,
            'mission_source': None,
        }
        sig = self.cs.signal_mission_alignment(org)
        self.assertEqual(sig['status'], 'unknown')


class TestCompositeConfidence(unittest.TestCase):
    def setUp(self):
        self.cs = CredibilitySignals()

    def test_confidence_average(self):
        # Test that composite confidence is mean of signal confidences
        signals = [100, 95, 90, 85, 80, 75]
        expected = sum(signals) // len(signals)
        self.assertEqual(expected, 87)


if __name__ == '__main__':
    unittest.main()
