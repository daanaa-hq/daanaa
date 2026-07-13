"""Privacy controls — export and delete of entrusted (Tier 2) claim data.

Charter promise 9 ("We will never lock you in") and Library Document 011:
a claimant can export everything they entrusted to Daanaa and delete it
entirely. The public IRS record is not theirs to delete and must remain.

Both endpoints authenticate exactly like /api/claim/update: EIN + a
verification token (raw PIN or HMAC token). Secret material (pin,
pin_expires_at) must never appear in an export.
"""

import json
import sqlite3

import pytest

import daanaa_api


EIN = "111000111"
PIN = "482913"


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_registry.db")
    db = sqlite3.connect(db_path)
    db.execute("""
        CREATE TABLE registry_enriched (
            EIN TEXT PRIMARY KEY,
            organization_name TEXT,
            street_address TEXT,
            CITY TEXT,
            STATE TEXT,
            zipcode TEXT,
            mission TEXT,
            donate_url TEXT
        )
    """)
    db.execute(
        "INSERT INTO registry_enriched VALUES "
        "('111000111', 'Test Helpers Inc', '12 Main St', 'Austin', 'TX', '78701', NULL, NULL)"
    )
    db.commit()
    db.close()

    monkeypatch.setattr(daanaa_api, "DB_PATH", db_path)
    monkeypatch.setattr(daanaa_api, "LIVE_DB_PATH", db_path)
    daanaa_api._init_org_claims_table()
    daanaa_api._init_org_activity_table()

    # Seed a verified claim carrying every kind of entrusted field
    db = sqlite3.connect(db_path)
    db.execute("""
        INSERT INTO org_claims
            (ein, email, irs_address, pin, pin_expires_at, claim_status,
             verified_at, custom_mission, custom_description, phone,
             rep_name, rep_title, volunteer_contact_name,
             volunteer_contact_email, donor_contact_email, call_notes)
        VALUES (?, 'director@testhelpers.org', '12 Main St', ?,
                datetime('now', '+1 day'), 'verified', datetime('now'),
                'We help people.', 'A longer description.', '(512) 555-0142',
                'Maria Alvarez', 'Executive Director', 'Sam Lee',
                'volunteers@testhelpers.org', 'giving@testhelpers.org',
                'spoke 7/1, warm call')
    """, (EIN, PIN))
    db.commit()
    db.close()

    daanaa_api.limiter.enabled = False
    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c
    daanaa_api.limiter.enabled = True


def _token():
    return daanaa_api._make_verify_token(EIN, PIN)


# ── Export ────────────────────────────────────────────────────────────────

def test_export_requires_ein_and_token(client):
    assert client.post("/api/claim/my-data", json={}).status_code == 400
    assert client.post("/api/claim/my-data", json={"ein": EIN}).status_code == 400


def test_export_rejects_bad_token(client):
    r = client.post("/api/claim/my-data",
                    json={"ein": EIN, "verification_token": "wrong"})
    assert r.status_code == 403


def test_export_returns_all_entrusted_fields(client):
    r = client.post("/api/claim/my-data",
                    json={"ein": EIN, "verification_token": _token()})
    assert r.status_code == 200
    data = r.get_json()["entrusted_data"]
    assert data["email"] == "director@testhelpers.org"
    assert data["custom_mission"] == "We help people."
    assert data["rep_name"] == "Maria Alvarez"
    assert data["volunteer_contact_email"] == "volunteers@testhelpers.org"
    assert data["call_notes"] == "spoke 7/1, warm call"


def test_export_never_leaks_secret_material(client):
    r = client.post("/api/claim/my-data",
                    json={"ein": EIN, "verification_token": _token()})
    body = json.dumps(r.get_json())
    assert PIN not in body
    data = r.get_json()["entrusted_data"]
    assert "pin" not in data
    assert "pin_expires_at" not in data


def test_export_accepts_raw_pin_like_claim_update(client):
    r = client.post("/api/claim/my-data",
                    json={"ein": EIN, "verification_token": PIN})
    assert r.status_code == 200


# ── Delete ────────────────────────────────────────────────────────────────

def test_delete_rejects_bad_token(client):
    r = client.post("/api/claim/my-data/delete",
                    json={"ein": EIN, "verification_token": "wrong"})
    assert r.status_code == 403
    # Row must survive a rejected delete
    db = sqlite3.connect(daanaa_api.DB_PATH)
    assert db.execute("SELECT COUNT(*) FROM org_claims WHERE ein=?", (EIN,)).fetchone()[0] == 1


def test_delete_removes_entrusted_data_keeps_public_record(client):
    r = client.post("/api/claim/my-data/delete",
                    json={"ein": EIN, "verification_token": _token()})
    assert r.status_code == 200
    assert r.get_json()["success"] is True

    db = sqlite3.connect(daanaa_api.DB_PATH)
    # Entrusted row is gone entirely
    assert db.execute("SELECT COUNT(*) FROM org_claims WHERE ein=?", (EIN,)).fetchone()[0] == 0
    # The public IRS record was never theirs to delete — it remains
    assert db.execute("SELECT COUNT(*) FROM registry_enriched WHERE EIN=?", (EIN,)).fetchone()[0] == 1


def test_delete_then_export_is_404(client):
    client.post("/api/claim/my-data/delete",
                json={"ein": EIN, "verification_token": _token()})
    r = client.post("/api/claim/my-data",
                    json={"ein": EIN, "verification_token": _token()})
    assert r.status_code == 404


def test_delete_logs_event_without_pii(client):
    client.post("/api/claim/my-data/delete",
                json={"ein": EIN, "verification_token": _token()})
    db = sqlite3.connect(daanaa_api.DB_PATH)
    try:
        rows = db.execute(
            "SELECT detail FROM org_activity WHERE ein=? AND event_type='claim_data_deleted'",
            (EIN,)).fetchall()
    except sqlite3.OperationalError:
        rows = []
    # An audit event exists, and it carries no personal data
    assert len(rows) == 1
    assert "director@testhelpers.org" not in rows[0][0]
    assert "Maria" not in rows[0][0]
