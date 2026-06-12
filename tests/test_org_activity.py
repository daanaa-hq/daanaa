"""Org activity timeline + admin Today queue.

The activity log is the ops backbone: every claim event, call, and admin
action lands in org_activity so decisions are explainable later (P9) and
future automation reads structured events. The Today queue is the worklist
the system derives from those states.
"""

import sqlite3

import pytest

import daanaa_api

KEY = "test-admin-key"


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_registry.db")
    db = sqlite3.connect(db_path)
    db.execute("""
        CREATE TABLE registry_enriched (
            EIN TEXT PRIMARY KEY, organization_name TEXT, street_address TEXT,
            CITY TEXT, STATE TEXT, zipcode TEXT, mission TEXT, donate_url TEXT
        )
    """)
    db.execute("INSERT INTO registry_enriched VALUES ('111000111', 'Test Helpers Inc', '12 Main St', 'Austin', 'TX', '78701', NULL, NULL)")
    db.commit()
    db.close()

    monkeypatch.setattr(daanaa_api, "DB_PATH", db_path)
    monkeypatch.setattr(daanaa_api, "LIVE_DB_PATH", db_path)
    monkeypatch.setattr(daanaa_api, "_ADMIN_KEY", KEY)
    daanaa_api._init_org_claims_table()
    daanaa_api._init_org_activity_table()

    daanaa_api.limiter.enabled = False
    monkeypatch.setattr(daanaa_api, "_send_daanaa_email", lambda *a, **k: None)
    monkeypatch.delenv("LOB_API_KEY", raising=False)
    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c
    daanaa_api.limiter.enabled = True


def _start_claim(client):
    return client.post("/api/claim/start", json={
        "ein": "111000111", "email": "director@testhelpers.org",
        "phone": "(512) 555-0142", "name": "Maria Alvarez",
        "title": "Executive Director",
        "attested_authority": True, "attested_legal": True,
    })


def _events(client):
    return [r[0] for r in sqlite3.connect(daanaa_api.DB_PATH).execute(
        "SELECT event_type FROM org_activity WHERE ein='111000111' ORDER BY id").fetchall()]


def test_claim_lifecycle_is_logged(client):
    assert _start_claim(client).status_code == 200
    assert _events(client) == ["claim_submitted"]

    pin = sqlite3.connect(daanaa_api.DB_PATH).execute(
        "SELECT pin FROM org_claims WHERE ein='111000111'").fetchone()[0]
    assert client.post("/api/claim/verify", json={"ein": "111000111", "pin": pin}).status_code == 200
    assert _events(client) == ["claim_submitted", "pin_verified"]


def test_admin_actions_are_logged_with_actor(client):
    _start_claim(client)
    client.patch("/api/admin/claims/111000111",
                 json={"action": "mark_called", "notes": "confirmed via website number"},
                 headers={"X-Admin-Key": KEY})
    client.patch("/api/admin/claims/111000111",
                 json={"action": "revoke", "reason": "test revoke"},
                 headers={"X-Admin-Key": KEY})
    rows = sqlite3.connect(daanaa_api.DB_PATH).execute(
        "SELECT event_type, actor FROM org_activity WHERE ein='111000111' ORDER BY id").fetchall()
    assert ("call_logged", "admin") in rows
    assert ("claim_revoked", "admin") in rows


def test_today_queue_buckets(client):
    _start_claim(client)
    res = client.get("/api/admin/today", headers={"X-Admin-Key": KEY})
    assert res.status_code == 200
    body = res.get_json()
    # Fresh claim, not yet called → in the call bucket
    assert body["counts"]["to_call"] == 1
    assert body["to_call"][0]["organization_name"] == "Test Helpers Inc"
    assert body["counts"]["pin_expiring"] == 0

    # After the call, with a PIN expiring inside 7 days → moves buckets
    client.patch("/api/admin/claims/111000111",
                 json={"action": "mark_called"}, headers={"X-Admin-Key": KEY})
    with sqlite3.connect(daanaa_api.DB_PATH) as conn:
        conn.execute("UPDATE org_claims SET pin_expires_at = datetime('now', '+3 days') WHERE ein='111000111'")
    body = client.get("/api/admin/today", headers={"X-Admin-Key": KEY}).get_json()
    assert body["counts"]["to_call"] == 0
    assert body["counts"]["pin_expiring"] == 1


def test_today_and_activity_require_admin_key(client):
    assert client.get("/api/admin/today").status_code == 401
    assert client.get("/api/admin/activity/111000111").status_code == 401


def test_activity_endpoint_returns_timeline(client):
    _start_claim(client)
    res = client.get("/api/admin/activity/111000111", headers={"X-Admin-Key": KEY})
    assert res.status_code == 200
    events = res.get_json()["activity"]
    assert events[0]["event_type"] == "claim_submitted"
    assert "Maria Alvarez" in events[0]["detail"]
