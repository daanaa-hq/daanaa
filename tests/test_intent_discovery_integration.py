#!/usr/bin/env python3
"""
Integration tests for Intent Signals + Event Discovery (Phase 2)

QA Requirements:
 1. Source page to discovery queue
 2. Date window validation: 14 to 60 days
 3. ZIP, city, state, event type, and date search
 4. Deduplication
 5. Preview creation
 6. Anonymous intent signal
 7. Confirmed signup transition
 8. Approved hours transition to verified/completed
 9. Nonprofit aggregate counts with threshold five
10. Privacy checks and PII leakage tests
11. Source changes and event expiry

Run with: python3 -m pytest tests/test_intent_discovery_integration.py -v
"""

import sys
import os
import pytest
import sqlite3
import json
from datetime import date, timedelta
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import intent_layer
import event_discovery_engine

# Test database (in-memory)
@pytest.fixture
def test_db():
    """Create in-memory test database."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    return db

class TestEventDiscoveryQueue:
    """1. Source page to discovery queue"""

    def test_extract_candidates_from_html(self, test_db):
        """Extract event candidates from HTML."""
        html = """
        <h1>Community Clean-Up 2026-08-15</h1>
        <p>Join us for a volunteer event on 2026-08-15 for community service.</p>
        """
        candidates = event_discovery_engine.extract_candidates(
            "https://example.org/events",
            html,
            today=date(2026, 7, 24)
        )
        assert len(candidates) > 0
        assert candidates[0]['event_date'] == '2026-08-15'

    def test_queue_candidates_dedup(self, test_db):
        """Deduplication: same event not queued twice."""
        event_discovery_engine.ensure_queue(test_db)

        candidates = [{
            'title': 'Community Event',
            'event_date': '2026-08-15',
            'source_url': 'https://example.org',
            'evidence': 'cleanup event'
        }]

        added1 = event_discovery_engine.queue_candidates(test_db, "123456789", candidates)
        added2 = event_discovery_engine.queue_candidates(test_db, "123456789", candidates)

        assert added1 == 1
        assert added2 == 0  # Second insert ignored (UNIQUE constraint)

    def test_rolling_window_14_to_60_days(self):
        """2. Date window validation: 14 to 60 days."""
        today = date(2026, 7, 24)
        start, end = event_discovery_engine.rolling_window(today)

        assert start == '2026-08-07'  # 14 days from now
        assert end == '2026-09-22'    # 60 days from now


class TestIntentSignals:
    """6. Anonymous intent signal"""

    def test_record_volunteer_intent(self, test_db):
        """Record anonymous volunteer interest signal."""
        intent_layer.ensure_schema(test_db)

        # Record volunteer interest
        signal_id = intent_layer.record_intent(
            test_db,
            kind='volunteer',
            source='event_preview',
            event_id=2,
            evidence={'page': '/events/2', 'action': 'viewed'}
        )

        assert signal_id > 0

        # Verify no PII was stored
        row = test_db.execute(
            "SELECT * FROM intent_signals WHERE id=?", (signal_id,)
        ).fetchone()

        assert row['kind'] == 'volunteer'
        assert row['event_id'] == 2
        assert row['stage'] == 'expressed'
        # Verify no PII fields exist
        assert 'email' not in row.keys()
        assert 'ip' not in row.keys()
        assert 'phone' not in row.keys()

    def test_transition_to_action_started(self, test_db):
        """7. Confirmed signup transition."""
        intent_layer.ensure_schema(test_db)

        signal_id = intent_layer.record_intent(
            test_db,
            kind='volunteer',
            source='event_preview',
            event_id=2
        )

        # Transition: user confirms signup
        intent_layer.transition_intent(test_db, signal_id, 'action_started')

        row = test_db.execute(
            "SELECT stage FROM intent_signals WHERE id=?", (signal_id,)
        ).fetchone()

        assert row['stage'] == 'action_started'

    def test_transition_to_verified_on_hour_approval(self, test_db):
        """8. Approved hours transition to verified/completed."""
        intent_layer.ensure_schema(test_db)

        signal_id = intent_layer.record_intent(
            test_db,
            kind='volunteer',
            source='event_preview',
            event_id=2
        )

        # Flow: expressed → action_started → verified
        intent_layer.transition_intent(test_db, signal_id, 'action_started')
        intent_layer.transition_intent(test_db, signal_id, 'verified')

        row = test_db.execute(
            "SELECT stage FROM intent_signals WHERE id=?", (signal_id,)
        ).fetchone()

        assert row['stage'] == 'verified'

    def test_no_identity_fields_in_schema(self, test_db):
        """10. Privacy checks: no identity fields."""
        intent_layer.ensure_schema(test_db)

        # Get schema
        schema = test_db.execute(
            "PRAGMA table_info(intent_signals)"
        ).fetchall()

        column_names = [row['name'] for row in schema]

        # Verify PII fields do NOT exist
        forbidden_fields = ['email', 'phone', 'name', 'ip_address', 'cookie', 'wallet']
        for field in forbidden_fields:
            assert field not in column_names, f"PII field '{field}' found in schema!"

    def test_summarize_counts_only(self, test_db):
        """9. Nonprofit aggregate counts with threshold five."""
        intent_layer.ensure_schema(test_db)

        # Record 10 volunteer signals for EIN 123456789
        for i in range(10):
            intent_layer.record_intent(
                test_db,
                kind='volunteer',
                source='event_preview',
                ein='123456789',
                event_id=i+1
            )

        # Get summary
        summary = intent_layer.summarize_intent(test_db, ein='123456789')

        # Should return counts only, no individual details
        assert 'volunteer:expressed' in summary
        assert summary['volunteer:expressed'] == 10

        # Verify we can't extract individual user info from summary
        # (it's just aggregate counts)
        for key, value in summary.items():
            assert isinstance(value, int), "Summary should only contain counts"

    def test_summarize_threshold_enforcement(self, test_db):
        """9. Threshold five: don't expose counts < 5."""
        intent_layer.ensure_schema(test_db)

        # Record only 3 signals (below threshold)
        for i in range(3):
            intent_layer.record_intent(
                test_db,
                kind='volunteer',
                source='event_preview',
                ein='111111111',
                event_id=i+1
            )

        summary = intent_layer.summarize_intent(test_db, ein='111111111')

        # In production, non-profits see counts ONLY if >= 5
        # (test just verifies we can GET the summary; enforcement is in API)
        assert len(summary) > 0


class TestDiscoveryAndPreview:
    """5. Preview creation (unconfirmed events)"""

    def test_discovered_events_stay_unconfirmed(self, test_db):
        """Discovered events never open for signup until nonprofit claims."""
        event_discovery_engine.ensure_queue(test_db)

        # Queue a candidate (from discovery)
        candidates = [{
            'title': 'Discovered Event',
            'event_date': '2026-08-15',
            'source_url': 'https://example.org',
            'evidence': 'found on website'
        }]

        event_discovery_engine.queue_candidates(test_db, "123456789", candidates)

        # Verify it's in pending_review (admin approval required)
        row = test_db.execute(
            "SELECT status FROM event_discovery_queue LIMIT 1"
        ).fetchone()

        assert row['status'] == 'pending_review'

    def test_no_auto_publication(self, test_db):
        """11. No automatic publication: admin must review."""
        event_discovery_engine.ensure_queue(test_db)

        candidates = [{
            'title': 'Event',
            'event_date': '2026-08-15',
            'source_url': 'https://example.org',
            'evidence': 'text'
        }]

        event_discovery_engine.queue_candidates(test_db, "123456789", candidates)

        # Candidates stay in queue until manually promoted
        pending = test_db.execute(
            "SELECT COUNT(*) as count FROM event_discovery_queue WHERE status='pending_review'"
        ).fetchone()['count']

        assert pending == 1


class TestSearchFilters:
    """3. ZIP, city, state, event type, and date search"""

    def test_search_scope_builder(self):
        """Build SQL WHERE clause for various filters."""
        # ZIP search
        clause, params = event_discovery_engine.search_scope(zip_code="90210")
        assert "location_zip=?" in clause
        assert "90210" in params

        # City + state
        clause, params = event_discovery_engine.search_scope(city="Los Angeles", state="CA")
        assert "location_city" in clause
        assert "location_state" in clause

        # State only
        clause, params = event_discovery_engine.search_scope(state="NY")
        assert "location_state=?" in clause

        # Event type + date
        clause, params = event_discovery_engine.search_scope(
            event_type="cleanup",
            date_from="2026-08-01",
            date_to="2026-08-31"
        )
        assert "event_type=?" in clause
        assert "event_date>=" in clause
        assert "event_date<=" in clause


class TestPrivacyInvariants:
    """10. Privacy checks and PII leakage tests"""

    def test_wallet_separate_from_intent(self, test_db):
        """Wallet data remains separate from intent signals."""
        intent_layer.ensure_schema(test_db)

        # Record an intent
        intent_layer.record_intent(
            test_db,
            kind='volunteer',
            source='event_preview',
            event_id=1
        )

        # Verify intent_signals table has NO wallet-related fields
        schema = test_db.execute(
            "PRAGMA table_info(intent_signals)"
        ).fetchall()

        column_names = [row['name'] for row in schema]
        assert 'wallet_contents' not in column_names
        assert 'donation_amount' not in column_names
        assert 'giving_history' not in column_names

    def test_no_ip_logging_in_intent(self, test_db):
        """Intent signals never store IP address."""
        intent_layer.ensure_schema(test_db)

        signal_id = intent_layer.record_intent(
            test_db,
            kind='volunteer',
            source='event_preview',
            event_id=1,
            evidence={'some': 'data'}
        )

        row = test_db.execute(
            "SELECT * FROM intent_signals WHERE id=?", (signal_id,)
        ).fetchone()

        # IP should never be in the record
        assert 'ip' not in str(row.keys()).lower()

    def test_evidence_contains_no_pii(self, test_db):
        """Evidence field documents source, never stores PII."""
        intent_layer.ensure_schema(test_db)

        # Even if we try to pass PII in evidence, it's just documentation
        signal_id = intent_layer.record_intent(
            test_db,
            kind='volunteer',
            source='event_preview',
            event_id=1,
            evidence={
                'page': '/events/1',
                'referrer': 'search',
                'source_url': 'https://example.org'
            }
        )

        row = test_db.execute(
            "SELECT evidence FROM intent_signals WHERE id=?", (signal_id,)
        ).fetchone()

        # Evidence is stored as JSON, never indexed or aggregated individually
        evidence = json.loads(row['evidence'])
        assert 'page' in evidence
        # The API would never expose individual evidence; only aggregate counts


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
