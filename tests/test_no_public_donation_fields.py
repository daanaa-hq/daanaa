"""Legal posture, updated 2026-07-10 (see DECISIONS.md 2026-07-10 and
project memory project_no_public_donation_ctas.md): the blanket 2026-06-10
"no donate fields anywhere" directive was reversed for the ORG DETAIL
endpoint only. A donate action may render publicly there, gated on
donate_url_status IN ('beta', 'claimed') -- never on donate_confidence,
which is NULL for ~99.7% of orgs with a URL. List/search/similar/summary
endpoints still must never expose donate fields; a donor never needs a
donate button on a card in a results grid, only on the org's own page.

If donate_url is exposed on org detail, donate_url_status MUST be exposed
alongside it -- a URL with no status is ungateable and the frontend would
have to either show it unconditionally (violates fail-closed) or hide it
always (defeats the point of exposing it). This is the actual invariant
this file now guards on org detail; the blanket ban still holds everywhere
else. docs/audit/donation_cta_removal_phase1.md (historical, pre-reversal).
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


def test_org_detail_donate_fields_are_gateable(client):
    """Org detail MAY expose donate_url (2026-07-10 reversal, org-detail only)
    -- but ONLY alongside donate_url_status, so a consumer can gate on it.
    A donate_url with no status would be ungateable and unsafe to render."""
    ein = _an_ein_with_donate_url(client)
    if not ein:
        pytest.skip("no org with internal donate_url in DB")
    resp = client.get(f"/api/organizations/{ein}")
    assert resp.status_code == 200, f"/api/organizations/<ein> returned {resp.status_code}"
    body = resp.get_json()
    if body.get("donate_url"):
        assert "donate_url_status" in body, (
            "donate_url is exposed without donate_url_status -- the frontend "
            "cannot gate it (must be status IN beta/claimed to render), so an "
            "ungated donate_url on org detail is a fail-closed violation."
        )


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
