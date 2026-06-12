"""Claim re-entry magic links — POST /api/claim/login.

A verified claimant who lost their edit link asks for a fresh one. Security
properties under test: the link only ever goes to the email on file (never
the address the requester typed), unverified claims get nothing, and the
response is byte-identical whether or not a claim exists so the endpoint
cannot be used to probe which orgs are claimed.
"""

import sqlite3

import pytest

import daanaa_api


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
    daanaa_api._init_org_claims_table()
    daanaa_api._init_org_activity_table()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at, claim_status, rep_name)
               VALUES ('111000111', 'director@testhelpers.org', 'x', '123456',
                       datetime('now', '+30 days'), 'verified', 'Maria Alvarez')"""
        )

    daanaa_api.limiter.enabled = False
    sent = []
    monkeypatch.setattr(daanaa_api, "_send_daanaa_email",
                        lambda to, subject, body, **k: sent.append((to, subject, body)))
    daanaa_api.app.config["_test_sent_emails"] = sent
    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c
    daanaa_api.limiter.enabled = True


def _login(client, value):
    return client.post("/api/claim/login", json={"ein_or_email": value})


def test_edit_link_goes_to_email_on_file_only(client):
    res = _login(client, "111000111")
    assert res.status_code == 200
    sent = daanaa_api.app.config["_test_sent_emails"]
    assert len(sent) == 1
    to, _, body = sent[0]
    assert to == "director@testhelpers.org"
    expected_token = daanaa_api._make_verify_token("111000111", "123456")
    assert f"/claim/edit?ein=111000111&token={expected_token}" in body


def test_lookup_by_email_works(client):
    res = _login(client, "director@testhelpers.org")
    assert res.status_code == 200
    assert len(daanaa_api.app.config["_test_sent_emails"]) == 1


def test_unknown_org_gets_identical_response_and_no_email(client):
    known = _login(client, "111000111").get_json()
    daanaa_api.app.config["_test_sent_emails"].clear()
    unknown = _login(client, "999888777").get_json()
    assert known == unknown  # anti-enumeration: byte-identical body
    assert not daanaa_api.app.config["_test_sent_emails"]


def test_pending_claim_gets_no_link(client):
    # Not yet verified by phone — there is nothing to re-enter
    with sqlite3.connect(daanaa_api.DB_PATH) as conn:
        conn.execute("UPDATE org_claims SET claim_status='pending' WHERE ein='111000111'")
    res = _login(client, "111000111")
    assert res.status_code == 200
    assert not daanaa_api.app.config["_test_sent_emails"]


def test_request_is_logged(client):
    _login(client, "111000111")
    events = sqlite3.connect(daanaa_api.DB_PATH).execute(
        "SELECT event_type FROM org_activity WHERE ein='111000111'").fetchall()
    assert ("login_link_sent",) in events
