"""Server-side URL validation at write time (T11 gap 2, EXECUTION_HANDOFF_2026_07_12.md).

The frontend already rejects javascript:/data: schemes via
frontend/src/utils/externalLink.ts (normalizeExternalUrl). This file proves
the server enforces the same rule at the write boundary -- any endpoint that
persists a URL a public or org-rep caller supplies must never store a
non-http(s) scheme, a schemeless garbage string, or a hostname with no dot.
Defense in depth: a UI bug or a direct API call must not be the only thing
standing between an attacker and a stored javascript: URI.
"""

import pytest

from daanaa_api import app, _normalize_public_url


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestNormalizePublicUrl:
    """Unit tests on the shared validator itself."""

    def test_rejects_javascript_scheme(self):
        assert _normalize_public_url("javascript:alert(1)") == ""

    def test_rejects_data_scheme(self):
        assert _normalize_public_url("data:text/html,<script>alert(1)</script>") == ""

    def test_rejects_bare_scheme_no_host(self):
        assert _normalize_public_url("https://") == ""

    def test_rejects_hostname_without_dot(self):
        assert _normalize_public_url("https://localhost") == ""

    def test_accepts_valid_https(self):
        assert _normalize_public_url("https://example.org") == "https://example.org"

    def test_accepts_bare_domain_by_adding_scheme(self):
        assert _normalize_public_url("example.org") == "https://example.org"

    def test_rejects_empty(self):
        assert _normalize_public_url("") == ""
        assert _normalize_public_url(None) == ""


class TestCommunityPartnerApplyRejectsMaliciousUrl:
    """/api/guild/community-partner is public and unauthenticated -- the
    highest-priority write path since anyone on the internet can post to it."""

    def _base_payload(self, website_url):
        return {
            "business_name": "Test Biz",
            "category": "retail",
            "offer": "10% off",
            "submitter_name": "Jane Doe",
            "submitter_email": "jane@example.org",
            "website_url": website_url,
        }

    def _fetch_website_url(self, cp_id):
        import os
        import sqlite3 as _sqlite3

        conn = _sqlite3.connect(os.environ["DB_PATH"])
        conn.row_factory = _sqlite3.Row
        row = conn.execute(
            "SELECT website_url FROM community_partners WHERE id=?", (cp_id,)
        ).fetchone()
        conn.close()
        return row["website_url"]

    def test_javascript_url_never_persisted(self, client):
        resp = client.post(
            "/api/guild/community-partner",
            json=self._base_payload("javascript:alert(document.cookie)"),
        )
        assert resp.status_code in (200, 201)
        cp_id = resp.get_json()["id"]
        assert self._fetch_website_url(cp_id) == ""

    def test_valid_url_persisted(self, client):
        resp = client.post(
            "/api/guild/community-partner",
            json=self._base_payload("https://example.org"),
        )
        assert resp.status_code in (200, 201)
        cp_id = resp.get_json()["id"]
        assert self._fetch_website_url(cp_id) == "https://example.org"
