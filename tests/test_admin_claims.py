"""Admin claims queue — /api/admin/claims.

The founder verifies every claim by phone. These endpoints are his worklist:
list claims with the PIN to read on the call, record that the call happened
(audit trail), and revoke bad claims with a written reason. Everything here
is PII and sits behind the admin key — a missing or wrong key must be a 401
before any data is touched.
"""

import os
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

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at,
                                       claim_status, phone, rep_title, attested_at)
               VALUES ('111000111', 'director@testhelpers.org', 'x', '123456',
                       datetime('now', '+30 days'), 'pending', '(512) 555-0142',
                       'Executive Director', datetime('now'))"""
        )

    daanaa_api.limiter.enabled = False
    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c
    daanaa_api.limiter.enabled = True


def _h():
    return {"X-Admin-Key": KEY}


def test_requires_admin_key(client):
    assert client.get("/api/admin/claims").status_code == 401
    assert client.patch("/api/admin/claims/111000111", json={"action": "mark_called"}).status_code == 401


def test_list_pending_claims_with_pin_and_org_name(client):
    res = client.get("/api/admin/claims?status=pending", headers=_h())
    assert res.status_code == 200
    claims = res.get_json()["claims"]
    assert len(claims) == 1
    c = claims[0]
    assert c["organization_name"] == "Test Helpers Inc"
    assert c["pin"] == "123456"
    assert c["phone"] == "(512) 555-0142"
    assert c["rep_title"] == "Executive Director"
    assert c["claim_status"] == "pending"


def test_mark_called_records_audit_trail(client):
    res = client.patch("/api/admin/claims/111000111",
                       json={"action": "mark_called", "notes": "Spoke with director, confirmed role"},
                       headers=_h())
    assert res.status_code == 200
    row = sqlite3.connect(daanaa_api.DB_PATH).execute(
        "SELECT called_at, call_notes FROM org_claims WHERE ein='111000111'").fetchone()
    assert row[0] is not None
    assert "confirmed role" in row[1]


def test_revoke_requires_reason(client):
    res = client.patch("/api/admin/claims/111000111",
                       json={"action": "revoke"}, headers=_h())
    assert res.status_code == 400


def test_revoke_sets_status_and_reason(client):
    res = client.patch("/api/admin/claims/111000111",
                       json={"action": "revoke", "reason": "could not verify identity"},
                       headers=_h())
    assert res.status_code == 200
    row = sqlite3.connect(daanaa_api.DB_PATH).execute(
        "SELECT claim_status, revoked_at, revoke_reason FROM org_claims WHERE ein='111000111'").fetchone()
    assert row[0] == "revoked"
    assert row[1] is not None
    assert row[2] == "could not verify identity"


def test_unknown_action_rejected(client):
    res = client.patch("/api/admin/claims/111000111",
                       json={"action": "delete_everything"}, headers=_h())
    assert res.status_code == 400
