"""Nonprofit "what changed" activity feed — the dashboard's return-visit hook.

Founder-approved (Benevity pattern, task #15): one consolidated feed of what
happened to the org's presence — link verifications, donor interest, data
refreshes, volunteer activity — in encouraging plain language (P5: no shame
framing, ever). Auth matches the self-dashboard: EIN + verification token.
"""

import sqlite3

import pytest

import daanaa_api

EIN = "111000111"
PIN = "482913"

SHAME_WORDS = ["bottom", "worst", "failing", "behind", "underperform",
               "poor", "weak", "lagging", "below average"]


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
            merit_peer_group_v5 TEXT, merit_peer_count_v5 INTEGER,
            donate_checked_at TEXT, website_checked_at TEXT, updated_at TEXT
        )
    """)
    db.execute("""
        INSERT INTO registry_enriched
            (EIN, organization_name, CITY, STATE, NTEE1, total_revenue,
             mission, mission_source, website, website_status, donate_url,
             donate_url_status, donate_checked_at, website_checked_at,
             updated_at)
        VALUES (?, 'Test Helpers Inc', 'Austin', 'TX', 'K', 120000,
                'Feeds people.', 'scraped', 'https://example.org', 'ok',
                'https://example.org/donate', 'beta',
                datetime('now', '-2 days'), datetime('now', '-3 days'),
                datetime('now', '-1 day'))
    """, (EIN,))
    db.execute("""
        CREATE TABLE wallet_analytics (
            ein TEXT, cause_tag TEXT, location_state TEXT, location_city TEXT,
            bookmark_count INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute(
        "INSERT INTO wallet_analytics (ein, bookmark_count) VALUES (?, 7)",
        (EIN,))
    db.execute("""
        CREATE TABLE volunteer_hours (
            id TEXT PRIMARY KEY, nonprofit_ein TEXT, volunteer_name TEXT,
            volunteer_email TEXT, hours REAL, service_date TEXT,
            activity_description TEXT, status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        INSERT INTO volunteer_hours (id, nonprofit_ein, volunteer_name,
            volunteer_email, hours, service_date, activity_description, status)
        VALUES ('vh1', ?, 'Sam', 's@x.org', 4.0, '2026-07-15', 'Food sort',
                'pending')
    """, (EIN,))
    db.execute("""
        CREATE TABLE org_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ein TEXT NOT NULL,
            event_type TEXT NOT NULL, detail TEXT,
            actor TEXT NOT NULL DEFAULT 'system',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute(
        "INSERT INTO org_activity (ein, event_type, detail) "
        "VALUES (?, 'profile_updated', 'Mission statement updated')", (EIN,))
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


def _feed(client, ein=EIN, token=None):
    token = token or daanaa_api._make_verify_token(EIN, PIN)
    return client.post("/api/nonprofit/activity-feed",
                       json={"ein": ein, "verification_token": token})


def test_requires_auth(client):
    assert client.post("/api/nonprofit/activity-feed",
                       json={"ein": EIN}).status_code == 400
    assert _feed(client, token="wrong").status_code == 403


def test_feed_covers_the_interconnection_surfaces(client):
    body = _feed(client).get_json()
    events = body["events"]
    assert events, "feed must not be empty when activity exists"
    types = {e["type"] for e in events}
    # Link verification, donor interest, data refresh, volunteer activity,
    # and the org_activity log must all surface.
    assert "donate_link" in types
    assert "donor_interest" in types
    assert "data_refresh" in types
    assert "volunteer" in types
    assert "profile_updated" in types


def test_events_sorted_newest_first_with_messages(client):
    events = _feed(client).get_json()["events"]
    stamps = [e["ts"] for e in events if e.get("ts")]
    assert stamps == sorted(stamps, reverse=True)
    for e in events:
        assert isinstance(e["message"], str) and len(e["message"]) > 10


def test_no_shame_language(client):
    text = " ".join(e["message"].lower()
                    for e in _feed(client).get_json()["events"])
    for w in SHAME_WORDS:
        assert w not in text, f"shame word {w!r} in feed"


def test_volunteer_pending_prompts_action(client):
    events = _feed(client).get_json()["events"]
    vol = [e for e in events if e["type"] == "volunteer"]
    assert vol and "1" in vol[0]["message"]  # one pending submission
