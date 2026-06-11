"""Legal posture (2026-06-10): Daanaa is a discovery platform, not a fundraising
platform. Public API responses must contain NO donation URL fields — donate data
stays internal (claim flow + admin only). docs/audit/donation_cta_removal_phase1.md
"""

import pytest

from daanaa_api import app

DONATE_KEY_FRAGMENTS = ("donate", "donation", "payment_url", "giving_url", "give_url")


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _donate_keys(obj, path="$"):
    """Recursively collect JSON keys that look donation-related."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(frag in k.lower() for frag in DONATE_KEY_FRAGMENTS):
                hits.append(f"{path}.{k}")
            hits.extend(_donate_keys(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_donate_keys(v, f"{path}[{i}]"))
    return hits


def _assert_clean(resp, route):
    assert resp.status_code == 200, f"{route} returned {resp.status_code}"
    hits = _donate_keys(resp.get_json())
    assert not hits, f"{route} exposes donation fields: {hits[:10]}"


def _an_ein_with_donate_url(client):
    """Find a real org that has internal donate data — the interesting case."""
    import sqlite3
    from daanaa_api import DB_PATH
    db = sqlite3.connect(DB_PATH)
    row = db.execute(
        "SELECT EIN FROM registry_enriched "
        "WHERE donate_url IS NOT NULL AND donate_url != '' "
        "AND subsection = '3' AND deductibility IN ('1','0','4') LIMIT 1"
    ).fetchone()
    db.close()
    return row[0] if row else None


def test_org_list_has_no_donation_fields(client):
    _assert_clean(client.get("/api/organizations?per_page=10"), "/api/organizations")


def test_org_detail_has_no_donation_fields(client):
    ein = _an_ein_with_donate_url(client)
    if not ein:
        pytest.skip("no org with internal donate_url in DB")
    _assert_clean(client.get(f"/api/organizations/{ein}"), "/api/organizations/<ein>")


def test_search_has_no_donation_fields(client):
    _assert_clean(client.get("/api/search?q=food+bank"), "/api/search")


def test_similar_has_no_donation_fields(client):
    ein = _an_ein_with_donate_url(client)
    if not ein:
        pytest.skip("no org with internal donate_url in DB")
    _assert_clean(client.get(f"/api/organizations/{ein}/similar"), "/api/organizations/<ein>/similar")


def test_research_lamp_tiers_has_no_donation_fields(client):
    _assert_clean(client.get("/api/research/summary/lamp-tiers"), "/api/research/summary/lamp-tiers")


def test_direct_link_filter_is_gone(client):
    """The public 'direct donate link' filter must no longer narrow results."""
    base = client.get("/api/organizations?per_page=1&state=WY").get_json()
    filtered = client.get("/api/organizations?per_page=1&state=WY&direct_link=1").get_json()
    assert filtered["total"] == base["total"], (
        "direct_link param still filters on donate_url — public donate affordance remains"
    )
