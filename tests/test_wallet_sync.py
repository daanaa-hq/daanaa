import json
import pytest
from unittest.mock import patch, MagicMock

# Patch firebase_admin before daanaa_api imports it
import sys
sys.modules.setdefault('firebase_admin', MagicMock())
sys.modules.setdefault('firebase_admin.auth', MagicMock())
sys.modules.setdefault('firebase_admin.credentials', MagicMock())

import daanaa_api as api

@pytest.fixture
def client():
    api.app.config['TESTING'] = True
    with api.app.test_client() as c:
        yield c

FAKE_UID = 'test-uid-abc123'
FAKE_TOKEN = 'fake-firebase-id-token'

def _mock_verify(token, check_revoked=False):
    if token == FAKE_TOKEN:
        return {'uid': FAKE_UID}
    raise Exception('Invalid token')

def test_wallet_get_empty(client):
    with patch('daanaa_api.fb_auth.verify_id_token', side_effect=_mock_verify):
        r = client.get('/api/wallet', headers={'Authorization': f'Bearer {FAKE_TOKEN}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['donations'] == []
        assert data['volunteerHours'] == []

def test_wallet_put_and_get(client):
    payload = {
        'donations': [{'id': '1', 'ein': '12-3456789', 'orgName': 'Test Org', 'amount': 100,
                       'date': '2026-01-01', 'status': 'self_documented',
                       'loggedAt': '2026-01-01T00:00:00Z', 'letterRequested': False}],
        'volunteerHours': []
    }
    with patch('daanaa_api.fb_auth.verify_id_token', side_effect=_mock_verify):
        r = client.put('/api/wallet',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {FAKE_TOKEN}'}
        )
        assert r.status_code == 200

        r2 = client.get('/api/wallet', headers={'Authorization': f'Bearer {FAKE_TOKEN}'})
        assert r2.status_code == 200
        data = json.loads(r2.data)
        assert len(data['donations']) == 1
        assert data['donations'][0]['orgName'] == 'Test Org'

def test_wallet_requires_auth(client):
    r = client.get('/api/wallet')
    assert r.status_code == 401

def test_wallet_delete(client):
    payload = {
        'donations': [{'id': '1', 'ein': '12-3456789', 'orgName': 'X', 'amount': 50,
                       'date': '2026-01-01', 'status': 'self_documented',
                       'loggedAt': '2026-01-01T00:00:00Z', 'letterRequested': False}],
        'volunteerHours': []
    }
    with patch('daanaa_api.fb_auth.verify_id_token', side_effect=_mock_verify):
        client.put('/api/wallet',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {FAKE_TOKEN}'}
        )
        r = client.delete('/api/wallet', headers={'Authorization': f'Bearer {FAKE_TOKEN}'})
        assert r.status_code == 200
        r2 = client.get('/api/wallet', headers={'Authorization': f'Bearer {FAKE_TOKEN}'})
        data = json.loads(r2.data)
        assert data['donations'] == []
