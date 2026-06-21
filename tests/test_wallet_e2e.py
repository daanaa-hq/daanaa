"""Tests for the E2E encrypted wallet endpoints.
These endpoints require no auth — security comes from the keyHash.
"""
import json
import pytest
import daanaa_api as api

KEY_HASH = 'a' * 64  # 64-char hex (256-bit HKDF id token)
CIPHERTEXT = 'dGVzdA=='  # base64 of "test"
IV = 'AAAAAAAAAAAAAAAA'  # base64 of 12 zero bytes
SALT = 'AAAAAAAAAAAAAAAAAAAAAA=='  # base64 of 16 zero bytes

@pytest.fixture
def client():
    api.app.config['TESTING'] = True
    with api.app.test_client() as c:
        yield c

class TestWalletInit:
    def test_init_returns_salt(self, client):
        r = client.post('/api/wallet/init')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'salt' in data
        assert isinstance(data['salt'], str)
        assert len(data['salt']) > 0

    def test_init_returns_different_salt_each_time(self, client):
        r1 = client.post('/api/wallet/init')
        r2 = client.post('/api/wallet/init')
        s1 = json.loads(r1.data)['salt']
        s2 = json.loads(r2.data)['salt']
        assert s1 != s2

class TestWalletSync:
    def test_get_missing_returns_404(self, client):
        r = client.get(f'/api/wallet/sync?keyHash={KEY_HASH}')
        assert r.status_code == 404
        data = json.loads(r.data)
        assert data['found'] is False

    def test_post_stores_and_get_retrieves(self, client):
        payload = {
            'keyHash': KEY_HASH,
            'ciphertext': CIPHERTEXT,
            'iv': IV,
            'salt': SALT,
        }
        r = client.post('/api/wallet/sync',
            data=json.dumps(payload), content_type='application/json')
        assert r.status_code == 200
        assert json.loads(r.data)['ok'] is True

        r2 = client.get(f'/api/wallet/sync?keyHash={KEY_HASH}')
        assert r2.status_code == 200
        data = json.loads(r2.data)
        assert data['found'] is True
        assert data['ciphertext'] == CIPHERTEXT
        assert data['iv'] == IV
        assert data['salt'] == SALT

    def test_post_overwrites_on_conflict(self, client):
        payload = {'keyHash': KEY_HASH, 'ciphertext': CIPHERTEXT, 'iv': IV, 'salt': SALT}
        client.post('/api/wallet/sync', data=json.dumps(payload), content_type='application/json')

        new_ct = 'bmV3Y2lwaGVydGV4dA=='
        new_iv = 'BBBBBBBBBBBBBBBB'
        payload2 = {'keyHash': KEY_HASH, 'ciphertext': new_ct, 'iv': new_iv, 'salt': SALT}
        client.post('/api/wallet/sync', data=json.dumps(payload2), content_type='application/json')

        r = client.get(f'/api/wallet/sync?keyHash={KEY_HASH}')
        data = json.loads(r.data)
        assert data['ciphertext'] == new_ct
        assert data['iv'] == new_iv

    def test_delete_removes_wallet(self, client):
        payload = {'keyHash': KEY_HASH, 'ciphertext': CIPHERTEXT, 'iv': IV, 'salt': SALT}
        client.post('/api/wallet/sync', data=json.dumps(payload), content_type='application/json')

        r = client.delete('/api/wallet/sync',
            data=json.dumps({'keyHash': KEY_HASH}), content_type='application/json')
        assert r.status_code == 200

        r2 = client.get(f'/api/wallet/sync?keyHash={KEY_HASH}')
        assert r2.status_code == 404

    def test_invalid_key_hash_rejected(self, client):
        payload = {'keyHash': 'tooshort', 'ciphertext': CIPHERTEXT, 'iv': IV, 'salt': SALT}
        r = client.post('/api/wallet/sync',
            data=json.dumps(payload), content_type='application/json')
        assert r.status_code == 400

    def test_oversized_payload_rejected(self, client):
        payload = {
            'keyHash': KEY_HASH,
            'ciphertext': 'x' * 65536,  # >64KB
            'iv': IV,
            'salt': SALT,
        }
        r = client.post('/api/wallet/sync',
            data=json.dumps(payload), content_type='application/json')
        # Flask's global MAX_CONTENT_LENGTH=64KB may return 413 before our handler
        # runs; our handler returns 400. Both correctly reject the oversized payload.
        assert r.status_code in (400, 413)
