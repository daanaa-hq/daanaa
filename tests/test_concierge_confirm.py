"""Admin concierge confirm — /api/admin/concierge/confirm (eng review T2).

The operator takes a concierge call, reviews the AI-drafted Quick-Start
fields, and confirms them here. Two invariants this file exists to pin:

1. VERIFICATION BOUNDARY (stewardship P3): only a claim already
   'verified' or 'active' can be written. Pending, revoked, or missing
   claims get 403 and NOT ONE field changes. The concierge path must
   never become a verification bypass.
2. NO ORG CREDENTIALS: this path authenticates with the admin key only.
   It never accepts, verifies, or replays the org's verification token
   or PIN — a request carrying one is rejected outright.

Field-update semantics are the SAME as /api/claim/update (shared helper,
not forked logic): mission -> mission_source='claimed', website ->
website_status='claimed', donate confirm -> donate_url_status='claimed'.
"""

import os
import sqlite3

import pytest

import daanaa_api

KEY = "test-admin-key"
EIN_VERIFIED = "111000111"
EIN_PENDING = "222000222"
EIN_REVOKED = "333000333"
EIN_ACTIVE = "444000444"


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_registry.db")
    db = sqlite3.connect(db_path)
    db.execute("""
        CREATE TABLE registry_enriched (
            EIN TEXT PRIMARY KEY, organization_name TEXT,
            mission TEXT, mission_source TEXT,
            website TEXT, website_status TEXT,
            donate_url TEXT, donate_confidence REAL, donate_url_status TEXT,
            cause_tags TEXT
        )
    """)
    for ein, name in ((EIN_VERIFIED, "Verified Helpers"), (EIN_PENDING, "Pending Org"),
                      (EIN_REVOKED, "Revoked Org"), (EIN_ACTIVE, "Active Org")):
        db.execute(
            "INSERT INTO registry_enriched (EIN, organization_name, donate_url, donate_url_status, donate_confidence)"
            " VALUES (?, ?, 'https://old.example.org/give', 'ai_beta', 70)", (ein, name))
    db.commit()
    db.close()

    monkeypatch.setattr(daanaa_api, "DB_PATH", db_path)
    monkeypatch.setattr(daanaa_api, "LIVE_DB_PATH", db_path)
    monkeypatch.setattr(daanaa_api, "_ADMIN_KEY", KEY)
    daanaa_api._init_org_claims_table()
    daanaa_api._init_org_activity_table()
    # Apply migration 007 to add donate_url and cause_tags_json columns
    daanaa_api._run_migrations(db_path)

    with sqlite3.connect(db_path) as conn:
        for ein, status, revoked_at in (
            (EIN_VERIFIED, "verified", None),
            (EIN_PENDING, "pending", None),
            (EIN_REVOKED, "revoked", "2026-07-01"),
            (EIN_ACTIVE, "active", None),
        ):
            conn.execute(
                """INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at,
                                           claim_status, revoked_at, website_url)
                   VALUES (?, 'rep@example.org', 'x', '123456',
                           datetime('now', '+30 days'), ?, ?, NULL)""",
                (ein, status, revoked_at))

    daanaa_api.limiter.enabled = False
    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c
    daanaa_api.limiter.enabled = True


def _h():
    return {"X-Admin-Key": KEY}


def _payload(ein=EIN_VERIFIED, **over):
    p = {
        "ein": ein,
        "call_sid": "CAtest0001",
        "operator_note": "Spoke with the director, confirmed all five facts.",
        "mission": "Runs free after-school robotics clubs for middle schoolers in Portland.",
        "website": "riversideyouthrobotics.org",
        "donate_url": "https://riversideyouthrobotics.org/donate",
        "donate_confirmed": True,
        "contact_email": "info@riversideyouthrobotics.org",
        "contact_phone": "(503) 555-0142",
        "volunteer_note": "Seeking volunteer mentors.",
    }
    p.update(over)
    return p


def _registry(ein):
    # Lock-free design: org_claims holds nonprofit claims, registry_enriched holds IRS data.
    # For claimed fields, prefer org_claims; fall back to registry_enriched for IRS data.
    # Return order: mission, mission_source, website, website_status, donate_url, donate_url_status, donate_confidence
    row = sqlite3.connect(daanaa_api.DB_PATH).execute(
        "SELECT COALESCE(c.custom_mission, r.mission),"
        "       CASE WHEN c.custom_mission IS NOT NULL THEN 'claimed' ELSE r.mission_source END,"
        "       COALESCE(c.website_url, r.website),"
        "       CASE WHEN c.website_url IS NOT NULL THEN 'claimed' ELSE r.website_status END,"
        "       COALESCE(c.donate_url, r.donate_url), r.donate_url_status, r.donate_confidence"
        " FROM registry_enriched r"
        " LEFT JOIN org_claims c ON r.EIN = c.ein"
        " WHERE r.EIN=?", (ein,)).fetchone()
    return row


def _claim(ein):
    conn = sqlite3.connect(daanaa_api.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn.execute("SELECT * FROM org_claims WHERE ein=?", (ein,)).fetchone()


# ── Auth boundary ────────────────────────────────────────────────────────────

def test_requires_admin_key(client):
    assert client.post("/api/admin/concierge/confirm", json=_payload()).status_code == 401
    assert client.post("/api/admin/concierge/confirm", json=_payload(),
                       headers={"X-Admin-Key": "wrong"}).status_code == 401


# ── Verification boundary: the invariant this endpoint exists to protect ────

def test_pending_claim_gets_403_and_writes_nothing(client):
    res = client.post("/api/admin/concierge/confirm", json=_payload(ein=EIN_PENDING), headers=_h())
    assert res.status_code == 403
    row = _registry(EIN_PENDING)
    assert row[0] is None                      # mission untouched
    assert row[5] == "ai_beta"                 # donate_url_status untouched
    assert _claim(EIN_PENDING)["call_notes"] is None


def test_revoked_claim_gets_403(client):
    res = client.post("/api/admin/concierge/confirm", json=_payload(ein=EIN_REVOKED), headers=_h())
    assert res.status_code == 403
    assert _registry(EIN_REVOKED)[0] is None


def test_missing_claim_gets_403(client):
    res = client.post("/api/admin/concierge/confirm",
                      json=_payload(ein="999000999"), headers=_h())
    assert res.status_code == 403


def test_active_claim_is_allowed_and_not_downgraded(client):
    res = client.post("/api/admin/concierge/confirm", json=_payload(ein=EIN_ACTIVE), headers=_h())
    assert res.status_code == 200
    assert _claim(EIN_ACTIVE)["claim_status"] == "active"


# ── No org credentials on this path, ever ────────────────────────────────────

def test_org_verification_token_is_rejected_not_used(client):
    for key in ("verification_token", "token", "pin"):
        res = client.post("/api/admin/concierge/confirm",
                          json=_payload(**{key: "123456"}), headers=_h())
        assert res.status_code == 400, key


def test_response_never_leaks_a_verification_token(client):
    res = client.post("/api/admin/concierge/confirm", json=_payload(), headers=_h())
    assert res.status_code == 200
    assert "token" not in res.get_data(as_text=True).lower()


# ── Field-update semantics (same as the claim editor) ────────────────────────

def test_confirm_writes_quickstart_fields_with_claimed_source(client):
    res = client.post("/api/admin/concierge/confirm", json=_payload(), headers=_h())
    assert res.status_code == 200
    mission, mission_source, website, website_status, donate_url, donate_status, conf = \
        _registry(EIN_VERIFIED)
    assert mission.startswith("Runs free")
    assert mission_source == "claimed"
    assert website == "https://riversideyouthrobotics.org"   # bare domain normalized
    assert website_status == "claimed"
    assert donate_url == "https://riversideyouthrobotics.org/donate"
    assert donate_status == "claimed"
    assert conf == 95


def test_donate_url_not_flipped_without_explicit_confirm(client):
    res = client.post("/api/admin/concierge/confirm",
                      json=_payload(donate_confirmed=False), headers=_h())
    assert res.status_code == 200
    row = _registry(EIN_VERIFIED)
    assert row[4] == "https://old.example.org/give"   # donate_url untouched
    assert row[5] == "ai_beta"                        # status untouched


def test_javascript_donate_url_is_dropped(client):
    res = client.post("/api/admin/concierge/confirm",
                      json=_payload(donate_url="javascript:alert(1)"), headers=_h())
    assert res.status_code == 200
    row = _registry(EIN_VERIFIED)
    assert row[4] == "https://old.example.org/give"
    assert row[5] == "ai_beta"


def test_contacts_written_unified(client):
    client.post("/api/admin/concierge/confirm", json=_payload(), headers=_h())
    claim = _claim(EIN_VERIFIED)
    assert claim["contact_preference"] == "unified"
    assert claim["volunteer_contact_email"] == "info@riversideyouthrobotics.org"
    assert claim["donor_contact_email"] == "info@riversideyouthrobotics.org"
    assert claim["volunteer_contact_phone"] == "(503) 555-0142"


# ── Provenance: source, call linkage, attestation metadata ───────────────────

def test_provenance_recorded_on_org_claims(client):
    client.post("/api/admin/concierge/confirm", json=_payload(), headers=_h())
    claim = _claim(EIN_VERIFIED)
    notes = claim["call_notes"] or ""
    assert "concierge_call" in notes
    assert "CAtest0001" in notes
    assert daanaa_api.CLAIM_ATTESTATION_VERSION in notes
    assert "confirmed all five facts" in notes
    assert "volunteer mentors" in notes.lower()
    assert claim["called_at"] is not None


def test_org_activity_timeline_entry(client):
    client.post("/api/admin/concierge/confirm", json=_payload(), headers=_h())
    row = sqlite3.connect(daanaa_api.DB_PATH).execute(
        "SELECT event_type, actor FROM org_activity WHERE ein=? ORDER BY id DESC LIMIT 1",
        (EIN_VERIFIED,)).fetchone()
    assert row is not None
    assert row[0] == "concierge_draft_confirmed"
    assert row[1] == "admin"


# ── Input hygiene ────────────────────────────────────────────────────────────

def test_ein_and_call_sid_required(client):
    assert client.post("/api/admin/concierge/confirm",
                       json=_payload(ein=""), headers=_h()).status_code == 400
    assert client.post("/api/admin/concierge/confirm",
                       json=_payload(call_sid=""), headers=_h()).status_code == 400
