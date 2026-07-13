"""Nonprofit self-discovery dashboard — the pilot's core surface.

A verified claimant sees: their financial context in plain language, peer
context (public Tier 1 data), donor interest aggregates, and profile
completeness. Board condition (Maria): the narrative encourages and never
wounds — no ranking-shame language, ever, regardless of the numbers.
"""

import sqlite3

import pytest

import daanaa_api


EIN = "111000111"
PIN = "482913"

SHAME_WORDS = ["bottom", "worst", "failing", "behind", "underperform",
               "poor", "weak", "lagging", "below average"]


def _seed_org(db, ein, name, revenue, score, signal, gem=0):
    db.execute("""
        INSERT INTO registry_enriched
            (EIN, organization_name, CITY, STATE, NTEE1, total_revenue,
             mission, mission_source, website, website_status,
             donate_url, donate_url_status, is_hidden_gem,
             merit_score_v5, merit_archetype_v5, merit_archetype_v5_label,
             merit_band_v5, merit_band_v5_label, merit_health_signal_v5,
             merit_peer_group_v5, merit_peer_count_v5)
        VALUES (?, ?, 'Austin', 'TX', 'K', ?, 'Feeds people.', 'scraped',
                'https://example.org', 'ok', 'https://example.org/donate',
                'verified', ?, ?, 'DON', 'Donation-Funded', 'MICRO',
                'Micro (<$150K)', ?, 'DON|MICRO|K', 40)
    """, (ein, name, revenue, gem, score, signal))


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_registry.db")
    db = sqlite3.connect(db_path)
    db.execute("""
        CREATE TABLE registry_enriched (
            EIN TEXT PRIMARY KEY, organization_name TEXT, CITY TEXT, STATE TEXT,
            NTEE1 TEXT, total_revenue REAL, mission TEXT, mission_source TEXT,
            website TEXT, website_status TEXT, donate_url TEXT,
            donate_url_status TEXT, is_hidden_gem INTEGER DEFAULT 0,
            merit_score_v5 REAL, merit_archetype_v5 TEXT,
            merit_archetype_v5_label TEXT, merit_band_v5 TEXT,
            merit_band_v5_label TEXT, merit_health_signal_v5 TEXT,
            merit_peer_group_v5 TEXT, merit_peer_count_v5 INTEGER
        )
    """)
    _seed_org(db, EIN, "Test Helpers Inc", 120000, 76.0, "HEALTHY", gem=1)
    # Peer cell: same archetype/band/NTEE
    for i, (score, sig) in enumerate([(88, "HEALTHY"), (61, "STABLE"),
                                      (44, "STABLE"), (30, "CAUTION")]):
        _seed_org(db, f"22200022{i}", f"Peer Org {i}", 100000 + i * 10000, score, sig)
    db.commit()
    db.close()

    monkeypatch.setattr(daanaa_api, "DB_PATH", db_path)
    monkeypatch.setattr(daanaa_api, "LIVE_DB_PATH", db_path)
    daanaa_api._init_org_claims_table()

    db = sqlite3.connect(db_path)
    db.execute("""
        INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at,
                                claim_status, verified_at)
        VALUES (?, 'director@testhelpers.org', 'x', ?, datetime('now','+1 day'),
                'verified', datetime('now'))
    """, (EIN, PIN))
    db.commit()
    db.close()

    daanaa_api.limiter.enabled = False
    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c
    daanaa_api.limiter.enabled = True


def _dash(client, ein=EIN, token=None):
    token = token or daanaa_api._make_verify_token(EIN, PIN)
    return client.post("/api/nonprofit/dashboard",
                       json={"ein": ein, "verification_token": token})


def test_requires_auth(client):
    r = client.post("/api/nonprofit/dashboard", json={"ein": EIN})
    assert r.status_code == 400
    assert _dash(client, token="wrong").status_code == 403


def test_financial_context_present_and_plain(client):
    body = _dash(client).get_json()
    fc = body["financial_context"]
    assert fc["health_signal"] == "HEALTHY"
    assert fc["archetype"] == "Donation-Funded"
    assert fc["band"] == "Micro (<$150K)"
    assert fc["peer_count"] == 40
    assert isinstance(fc["narrative"], str) and len(fc["narrative"]) > 40


def test_narrative_never_wounds_even_at_low_score(client):
    # Drop the org to the lowest score in its cell with a CAUTION signal
    db = sqlite3.connect(daanaa_api.DB_PATH)
    db.execute("UPDATE registry_enriched SET merit_score_v5=8, "
               "merit_health_signal_v5='CAUTION' WHERE EIN=?", (EIN,))
    db.commit()
    db.close()

    body = _dash(client).get_json()
    text = (body["financial_context"]["narrative"] + " "
            + body["profile"]["narrative"]).lower()
    for word in SHAME_WORDS:
        assert word not in text, f"shame word '{word}' in narrative"
    # Honest data is still there — framing changes, facts don't
    assert body["financial_context"]["health_signal"] == "CAUTION"


def test_peer_context_uses_public_data_only(client):
    body = _dash(client).get_json()
    peers = body["peer_context"]["peers"]
    assert 1 <= len(peers) <= 5
    for p in peers:
        # Only Tier 0/1 fields — never claim/contact data
        assert set(p.keys()) <= {"name", "city", "state", "revenue",
                                 "health_signal", "website"}
    assert EIN not in [p.get("ein") for p in peers]  # self excluded


def test_donor_interest_graceful_without_analytics_table(client):
    body = _dash(client).get_json()
    di = body["donor_interest"]
    assert di["bookmarks_this_month"] == 0
    assert "note" in di


def test_profile_completeness_actionable(client):
    body = _dash(client).get_json()
    profile = body["profile"]
    assert profile["checks"]["mission"] is True
    assert profile["checks"]["website_verified"] is True
    assert profile["checks"]["donate_link_verified"] is True


def test_unclaimed_org_cannot_view(client):
    r = client.post("/api/nonprofit/dashboard",
                    json={"ein": "222000220",
                          "verification_token": daanaa_api._make_verify_token("222000220", PIN)})
    assert r.status_code == 404


def test_legacy_get_route_still_says_gone(client):
    # The old base64-token GET route must not silently come back to life
    r = client.get("/api/nonprofit/dashboard/sometoken")
    assert r.status_code in (404, 410, 501)
