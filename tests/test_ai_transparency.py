"""AI-extraction transparency — claimants see what AI derived and how to override.

Stewardship P9/P10 and Library Document 005 (provenance class 5): every
AI-generated fact shown about an organization must be visible to that
organization, labeled with its source, and overridable by them. This
endpoint powers the "What we derived about you" dashboard panel.
"""

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
            CITY TEXT, STATE TEXT,
            mission TEXT, mission_source TEXT,
            cause_tags TEXT,
            website TEXT, website_status TEXT,
            donate_url TEXT, donate_confidence REAL, donate_url_status TEXT
        )
    """)
    db.execute(
        "INSERT INTO registry_enriched VALUES "
        "('111000111', 'Test Helpers Inc', 'Austin', 'TX', "
        " 'Provides meals to homebound seniors in Travis County.', 'ai_generated', "
        " '[\"seniors\", \"food security\"]', "
        " 'https://testhelpers.org', 'ok', "
        " 'https://testhelpers.org/donate', 92.0, 'verified')"
    )
    db.commit()
    db.close()

    monkeypatch.setattr(daanaa_api, "DB_PATH", db_path)
    monkeypatch.setattr(daanaa_api, "LIVE_DB_PATH", db_path)
    daanaa_api._init_org_claims_table()

    db = sqlite3.connect(db_path)
    db.execute("""
        INSERT INTO org_claims
            (ein, email, irs_address, pin, pin_expires_at, claim_status, verified_at,
             custom_mission)
        VALUES (?, 'director@testhelpers.org', 'x', ?, datetime('now','+1 day'),
                'verified', datetime('now'), NULL)
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


def test_requires_auth(client):
    assert client.post("/api/claim/ai-derived", json={"ein": EIN}).status_code == 400
    r = client.post("/api/claim/ai-derived",
                    json={"ein": EIN, "verification_token": "wrong"})
    assert r.status_code == 403


def test_shows_ai_derived_fields_with_provenance(client):
    r = client.post("/api/claim/ai-derived",
                    json={"ein": EIN, "verification_token": _token()})
    assert r.status_code == 200
    body = r.get_json()
    derived = {d["field"]: d for d in body["derived"]}

    # Mission: AI-generated, labeled as such, with the actual value shown
    assert derived["mission"]["value"] == "Provides meals to homebound seniors in Travis County."
    assert derived["mission"]["source"] == "ai_generated"
    assert derived["mission"]["is_ai"] is True

    # Cause tags and donate link carry provenance too
    assert derived["cause_tags"]["is_ai"] is True
    assert derived["donate_url"]["value"] == "https://testhelpers.org/donate"


def test_every_derived_field_explains_override_path(client):
    r = client.post("/api/claim/ai-derived",
                    json={"ein": EIN, "verification_token": _token()})
    for d in r.get_json()["derived"]:
        assert d.get("how_to_override"), f"{d['field']} lacks an override explanation"


def test_shows_claimed_override_when_present(client):
    db = sqlite3.connect(daanaa_api.DB_PATH)
    db.execute("UPDATE org_claims SET custom_mission='We feed our neighbors.' WHERE ein=?", (EIN,))
    db.commit()
    db.close()

    r = client.post("/api/claim/ai-derived",
                    json={"ein": EIN, "verification_token": _token()})
    derived = {d["field"]: d for d in r.get_json()["derived"]}
    assert derived["mission"]["your_override"] == "We feed our neighbors."
    # The AI value is still shown so they can compare — transparency, not replacement
    assert derived["mission"]["value"].startswith("Provides meals")


def test_scraped_mission_is_not_flagged_ai(client):
    db = sqlite3.connect(daanaa_api.DB_PATH)
    db.execute("UPDATE registry_enriched SET mission_source='scraped' WHERE EIN=?", (EIN,))
    db.commit()
    db.close()

    r = client.post("/api/claim/ai-derived",
                    json={"ein": EIN, "verification_token": _token()})
    derived = {d["field"]: d for d in r.get_json()["derived"]}
    assert derived["mission"]["is_ai"] is False
