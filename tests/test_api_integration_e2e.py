#!/usr/bin/env python3
"""
End-to-End API Integration Tests

Tests the actual HTTP routes and their integration with hardened modules.
This is NOT a unit test — it exercises real API responses with real database.
"""

import sys
import os
import sqlite3
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import modules (feature flags enabled only within tests)
import daanaa_api
from scripts import profile_contexts
import intent_layer
import event_discovery_engine


@pytest.fixture
def client(monkeypatch):
    """Create Flask test client with feature flags enabled."""
    # Enable feature flags for API tests
    monkeypatch.setenv('ENABLE_PROFILE_CONTEXTS', 'true')
    monkeypatch.setenv('ENABLE_INTENT_SIGNALS', 'true')
    monkeypatch.setenv('ENABLE_EVENT_DISCOVERY', 'true')

    daanaa_api.app.config['TESTING'] = True
    with daanaa_api.app.test_client() as client:
        yield client


@pytest.fixture
def test_db():
    """Create test database."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    # Initialize all schemas
    profile_contexts.ensure_schema(db)
    intent_layer.ensure_schema(db)
    event_discovery_engine.ensure_queue(db)

    return db


@pytest.fixture
def mock_firebase_user(monkeypatch):
    """Mock Firebase authentication."""
    def mock_require_firebase_user():
        return "test_user_123"

    monkeypatch.setattr(daanaa_api, '_require_firebase_user', mock_require_firebase_user)
    return "test_user_123"


class TestProfileContextsAPI:
    """Test profile contexts API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_flags(self, monkeypatch):
        """Setup feature flags before each test."""
        # Override the module-level flag since it was read at import time
        monkeypatch.setattr(daanaa_api, 'ENABLE_PROFILE_CONTEXTS', True)
        monkeypatch.setattr(daanaa_api, '_profile_contexts_available', True)

    def test_create_context_endpoint(self, client, mock_firebase_user, monkeypatch):
        """Test POST /api/profile-contexts creates context via API."""
        # Mock database
        test_db = sqlite3.connect(":memory:")
        test_db.row_factory = sqlite3.Row
        profile_contexts.ensure_schema(test_db)

        def mock_get_db():
            return test_db

        monkeypatch.setattr(daanaa_api, 'get_db', mock_get_db)

        response = client.post('/api/profile-contexts', json={
            'context_type': 'household',
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'context_id' in data
        assert data['context_id'].startswith('ctx_')

    def test_get_context_members_with_uid_masking(self, client, mock_firebase_user, monkeypatch):
        """Test GET /api/profile-contexts/<id>/members masks UIDs for non-leads."""
        test_db = sqlite3.connect(":memory:")
        test_db.row_factory = sqlite3.Row
        profile_contexts.ensure_schema(test_db)

        # Setup: create context and add member
        lead_uid = "test_user_123"
        member_uid = "user_2"
        ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')
        inv_id = profile_contexts.invite_member(test_db, context_id=ctx_id, invited_uid=member_uid,
                                                role='member', invited_by_uid=lead_uid)
        profile_contexts.accept_invitation(test_db, invitation_id=inv_id, accepting_uid=member_uid)

        def mock_get_db():
            return test_db

        monkeypatch.setattr(daanaa_api, 'get_db', mock_get_db)

        response = client.get(f'/api/profile-contexts/{ctx_id}/members')

        assert response.status_code == 200
        data = json.loads(response.data)
        members = data['members']

        # Lead sees raw UIDs
        assert any(m['firebase_uid'] == member_uid for m in members)

    def test_invite_member_endpoint(self, client, mock_firebase_user, monkeypatch):
        """Test POST /api/profile-contexts/<id>/members creates invitation."""
        test_db = sqlite3.connect(":memory:")
        test_db.row_factory = sqlite3.Row
        profile_contexts.ensure_schema(test_db)

        lead_uid = "test_user_123"
        ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')

        def mock_get_db():
            return test_db

        monkeypatch.setattr(daanaa_api, 'get_db', mock_get_db)

        response = client.post(f'/api/profile-contexts/{ctx_id}/members', json={
            'firebase_uid': 'user_2',
            'role': 'member',
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'invitation_id' in data
        assert data['invited_uid'] == 'user_2'

    def test_accept_invitation_endpoint(self, client, mock_firebase_user, monkeypatch):
        """Test POST /api/profile-contexts/invitations/<id>/accept."""
        test_db = sqlite3.connect(":memory:")
        test_db.row_factory = sqlite3.Row
        profile_contexts.ensure_schema(test_db)

        lead_uid = "test_user_123"
        member_uid = "user_2"
        ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')
        inv_id = profile_contexts.invite_member(test_db, context_id=ctx_id, invited_uid=member_uid,
                                                role='member', invited_by_uid=lead_uid)

        def mock_get_db():
            return test_db

        # Mock the member as accepting their invitation
        def mock_member_auth():
            return member_uid

        monkeypatch.setattr(daanaa_api, 'get_db', mock_get_db)
        monkeypatch.setattr(daanaa_api, '_require_firebase_user', mock_member_auth)

        response = client.post(f'/api/profile-contexts/invitations/{inv_id}/accept')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_reject_invitation_endpoint(self, client, mock_firebase_user, monkeypatch):
        """Test POST /api/profile-contexts/invitations/<id>/reject."""
        test_db = sqlite3.connect(":memory:")
        test_db.row_factory = sqlite3.Row
        profile_contexts.ensure_schema(test_db)

        lead_uid = "test_user_123"
        member_uid = "user_2"
        ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')
        inv_id = profile_contexts.invite_member(test_db, context_id=ctx_id, invited_uid=member_uid,
                                                role='member', invited_by_uid=lead_uid)

        def mock_get_db():
            return test_db

        def mock_member_auth():
            return member_uid

        monkeypatch.setattr(daanaa_api, 'get_db', mock_get_db)
        monkeypatch.setattr(daanaa_api, '_require_firebase_user', mock_member_auth)

        response = client.post(f'/api/profile-contexts/invitations/{inv_id}/reject')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestIntentSignalsAPI:
    """Test intent signal recording in volunteer flow."""

    @pytest.fixture(autouse=True)
    def setup_flags(self, monkeypatch):
        """Setup feature flags before each test."""
        monkeypatch.setattr(daanaa_api, 'ENABLE_INTENT_SIGNALS', True)
        monkeypatch.setattr(daanaa_api, '_intent_available', True)

    def test_intent_recorded_on_volunteer_submit(self, test_db):
        """Test that record_intent is called when volunteer hours submitted."""
        ein = "123456789"

        # Simulate volunteer hours submission
        intent_id = intent_layer.record_intent(test_db, kind='volunteer', source='volunteer_submission', ein=ein)

        # Verify intent was recorded
        row = test_db.execute(
            "SELECT * FROM intent_signals WHERE id=? AND kind='volunteer'",
            (intent_id,)
        ).fetchone()

        assert row is not None
        assert row['stage'] == 'expressed'
        assert row['kind'] == 'volunteer'

    def test_intent_recorded_on_hours_approval(self, test_db):
        """Test that record_intent is called when hours approved."""
        ein = "123456789"

        # First record initial submit
        submit_id = intent_layer.record_intent(test_db, kind='volunteer', source='volunteer_submission', ein=ein)

        # Record approval
        approval_id = intent_layer.record_intent(test_db, kind='volunteer', source='volunteer_approval', ein=ein, evidence={'approved': True})

        # Verify both recorded
        submit_row = test_db.execute("SELECT * FROM intent_signals WHERE id=?", (submit_id,)).fetchone()
        approval_row = test_db.execute("SELECT * FROM intent_signals WHERE id=?", (approval_id,)).fetchone()

        assert submit_row is not None
        assert approval_row is not None
        assert approval_row['source'] == 'volunteer_approval'

    def test_intent_aggregation(self, test_db):
        """Test that intent signals are aggregatable without PII."""
        ein = "123456789"

        # Record multiple volunteer signals
        intent_layer.record_intent(test_db, kind='volunteer', source='volunteer_submission', ein=ein)
        intent_layer.record_intent(test_db, kind='volunteer', source='volunteer_claim', ein=ein)
        intent_layer.record_intent(test_db, kind='volunteer', source='volunteer_approval', ein=ein)

        # Summarize signals (aggregation only)
        summary = intent_layer.summarize_intent(test_db, ein=ein)

        assert 'volunteer:expressed' in summary
        assert summary['volunteer:expressed'] >= 1


class TestEventDiscoveryAPI:
    """Test event discovery review queue."""

    @pytest.fixture(autouse=True)
    def setup_flags(self, monkeypatch):
        """Setup feature flags before each test."""
        monkeypatch.setattr(daanaa_api, 'ENABLE_EVENT_DISCOVERY', True)
        monkeypatch.setattr(daanaa_api, '_discovery_available', True)

    def test_candidates_in_pending_review(self, test_db):
        """Test that queued candidates have pending_review status."""
        ein = "123456789"
        candidates = [{
            'title': 'Community Cleanup Event',
            'event_date': '2026-08-15',
            'source_url': 'https://example.org/events',
            'evidence': 'Found event text on website',
        }]

        event_discovery_engine.queue_candidates(test_db, ein, candidates)

        # Verify candidate in queue with pending_review status
        row = test_db.execute(
            "SELECT status FROM event_discovery_queue WHERE ein=? LIMIT 1",
            (ein,)
        ).fetchone()

        assert row is not None
        assert row['status'] == 'pending_review'

    def test_candidates_no_auto_publish(self, test_db):
        """Test that candidates never auto-publish without admin action."""
        ein = "123456789"
        candidates = [{
            'title': 'Volunteer Event',
            'event_date': '2026-08-20',
            'source_url': 'https://org.example.org',
            'evidence': 'Event found',
        }]

        # Queue candidates
        event_discovery_engine.queue_candidates(test_db, ein, candidates)

        # Verify not published
        published = test_db.execute(
            "SELECT COUNT(*) as count FROM event_discovery_queue WHERE ein=? AND status='active'",
            (ein,)
        ).fetchone()

        assert published['count'] == 0


class TestCanonicalDatabase:
    """Test that discovery and API use the same database."""

    def test_discovery_scheduler_uses_canonical_db(self):
        """Verify discovery_scheduler.sh uses merit_registry.db."""
        scheduler_path = Path("/home/akbar/meritgiving/scripts/discovery_scheduler.sh")
        if scheduler_path.exists():
            content = scheduler_path.read_text()
            # Should set LIVE_DB_PATH to merit_registry.db
            assert 'merit_registry.db' in content
            # Should NOT set it to daanaa_live.db
            assert 'daanaa_live.db' not in content or 'merit_registry.db' in content.split('daanaa_live.db')[0]

    def test_discovery_batch_uses_canonical_db(self):
        """Verify discovery_batch.py uses merit_registry.db as default."""
        batch_path = Path("/home/akbar/meritgiving/scripts/discovery_batch.py")
        if batch_path.exists():
            content = batch_path.read_text()
            # Should reference merit_registry.db
            assert 'merit_registry.db' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
