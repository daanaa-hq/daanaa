"""Claim flow (Phase 1: phone verification) — /api/claim/start guards.

These protect the legal posture of the claim flow: every claim must carry a
contact phone + role (we verify identity by phone before activating), a
revoked claim cannot be re-filed for 45 days, and orgs without a street
address on file can still claim (no letter required in Phase 1).
"""

import os
import sqlite3

import pytest

import daanaa_api


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
        "INSERT INTO registry_enriched VALUES ('111000111', 'Test Helpers Inc', '12 Main St', 'Austin', 'TX', '78701', NULL, NULL)"
    )
    # No street address on file — Phase 1 must still accept the claim
    db.execute(
        "INSERT INTO registry_enriched VALUES ('222000222', 'No Address Org', NULL, 'Boise', 'ID', '83701', NULL, NULL)"
    )
    db.commit()
    db.close()

    monkeypatch.setattr(daanaa_api, "DB_PATH", db_path)
    monkeypatch.setattr(daanaa_api, "LIVE_DB_PATH", db_path)
    daanaa_api._init_org_claims_table()

    # Endpoint has a 3/hour rate limit — disable for tests
    daanaa_api.limiter.enabled = False
    # Never send real email or letters from tests — patch the single choke
    # point every platform email goes through
    sent_emails = []
    monkeypatch.setattr(daanaa_api, "_send_daanaa_email",
                        lambda to, subject, body, **k: sent_emails.append((to, subject, body)))
    daanaa_api.app.config["_test_sent_emails"] = sent_emails
    monkeypatch.delenv("LOB_API_KEY", raising=False)

    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c
    daanaa_api.limiter.enabled = True


def _start(client, **overrides):
    payload = {
        "ein": "111000111",
        "email": "director@testhelpers.org",
        "phone": "(512) 555-0142",
        "title": "Executive Director",
        "attested_authority": True,
        "attested_legal": True,
    }
    payload.update(overrides)
    return client.post("/api/claim/start", json=payload)


def _claims_db(client):
    return sqlite3.connect(daanaa_api.DB_PATH)


# --- required fields ---

def test_missing_phone_rejected(client):
    res = _start(client, phone="")
    assert res.status_code == 400
    assert "phone" in res.get_json()["error"].lower()


def test_short_phone_rejected(client):
    res = _start(client, phone="555-0142")  # 7 digits — not a full US number
    assert res.status_code == 400


def test_missing_title_rejected(client):
    res = _start(client, title="")
    assert res.status_code == 400
    assert "title" in res.get_json()["error"].lower() or "role" in res.get_json()["error"].lower()


def test_missing_attestations_rejected(client):
    # The legal attestations are enforced server side, not just by the form UI
    assert _start(client, attested_authority=False).status_code == 400
    assert _start(client, attested_legal=False).status_code == 400


def test_attestation_version_recorded_for_audit(client):
    assert _start(client).status_code == 200
    row = _claims_db(client).execute(
        "SELECT attestation_version, attested_at FROM org_claims WHERE ein='111000111'"
    ).fetchone()
    assert row[0] == daanaa_api.CLAIM_ATTESTATION_VERSION
    assert row[1] is not None


# --- happy path: Phase 1 (no Lob key) leaves claim pending for the manual call ---

def test_claim_stores_phone_and_title_and_stays_pending(client):
    res = _start(client)
    assert res.status_code == 200
    assert res.get_json()["status"] == "pending"

    row = _claims_db(client).execute(
        "SELECT phone, rep_title, claim_status FROM org_claims WHERE ein='111000111'"
    ).fetchone()
    assert row == ("(512) 555-0142", "Executive Director", "pending")


def test_claim_sends_admin_notification_and_org_confirmation(client):
    assert _start(client).status_code == 200
    sent = daanaa_api.app.config["_test_sent_emails"]
    recipients = [to for to, _, _ in sent]
    assert "orgs@daanaa.org" in recipients            # admin notification
    assert "director@testhelpers.org" in recipients   # org confirmation
    org_body = next(b for to, _, b in sent if to == "director@testhelpers.org")
    assert "PIN" in org_body and "(512) 555-0142" in org_body
    # The PIN itself must never appear in the org email — it is given on the call
    pin = _claims_db(client).execute(
        "SELECT pin FROM org_claims WHERE ein='111000111'").fetchone()[0]
    assert pin not in org_body


def test_claim_without_street_address_succeeds(client):
    # Phase 1 verifies by phone — a missing IRS street address must not block
    res = _start(client, ein="222000222")
    assert res.status_code == 200
    assert res.get_json()["status"] == "pending"


# --- 45-day cooldown after revocation (legal review requirement) ---

def _insert_revoked(client, days_ago):
    db = _claims_db(client)
    db.execute(
        """INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at,
                                   claim_status, revoked_at, revoke_reason)
           VALUES ('111000111', 'old@testhelpers.org', 'x', '123456',
                   datetime('now', '+30 days'), 'revoked',
                   datetime('now', ?), 'disputed')""",
        (f"-{days_ago} days",),
    )
    db.commit()
    db.close()


def test_revoked_claim_blocked_within_45_days(client):
    _insert_revoked(client, days_ago=10)
    res = _start(client)
    assert res.status_code == 403
    assert "45" in res.get_json()["error"]


def test_revoked_claim_allowed_after_45_days(client):
    _insert_revoked(client, days_ago=50)
    res = _start(client)
    assert res.status_code == 200
    assert res.get_json()["status"] == "pending"


# --- existing claim states ---

def test_active_claim_blocked(client):
    db = _claims_db(client)
    db.execute(
        """INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at, claim_status)
           VALUES ('111000111', 'a@b.org', 'x', '123456', datetime('now', '+30 days'), 'active')"""
    )
    db.commit()
    db.close()
    assert _start(client).status_code == 409


def test_resubmission_updates_contact_info(client):
    # A pending claim re-submitted (typo fix) updates contact fields in place
    assert _start(client).status_code == 200
    res = _start(client, email="fixed@testhelpers.org", phone="512-555-9999")
    assert res.status_code == 200
    row = _claims_db(client).execute(
        "SELECT email, phone FROM org_claims WHERE ein='111000111'"
    ).fetchone()
    assert row == ("fixed@testhelpers.org", "512-555-9999")
