"""Droplet claim proxy — /api/claim/* must forward to the home server.

The droplet API is read-only (precompute files); the claim flow needs the
writable registry DB and mail sender on the home box. The droplet forwards
/api/claim/* through a reverse SSH tunnel (127.0.0.1:5001). These tests pin
the forwarding contract: method/body/visitor-IP pass through, upstream
errors pass through as-is, and a dead tunnel degrades to a 503 without
touching the rest of the site.
"""

import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import droplet_api


@pytest.fixture
def client():
    droplet_api.app.config["TESTING"] = True
    with droplet_api.app.test_client() as c:
        yield c


class _FakeResponse(io.BytesIO):
    def __init__(self, payload: dict, status: int = 200):
        super().__init__(json.dumps(payload).encode())
        self.status = status
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_claim_post_forwarded_with_body_and_visitor_ip(client, monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout=0):
        seen["url"] = req.full_url
        seen["method"] = req.get_method()
        seen["body"] = json.loads(req.data)
        seen["cf_ip"] = req.headers.get("Cf-connecting-ip")
        return _FakeResponse({"status": "pending"})

    monkeypatch.setattr(droplet_api.urllib.request, "urlopen", fake_urlopen)
    res = client.post("/api/claim/start", json={"ein": "111000111"},
                      headers={"CF-Connecting-IP": "203.0.113.9"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "pending"
    assert seen["url"].endswith("/api/claim/start")
    assert seen["method"] == "POST"
    assert seen["body"] == {"ein": "111000111"}
    # Rate limiting on the home API buckets per visitor, not per droplet
    assert seen["cf_ip"] == "203.0.113.9"


def test_upstream_error_passes_through(client, monkeypatch):
    def fake_urlopen(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 403, "Forbidden",
            {"Content-Type": "application/json"},
            io.BytesIO(b'{"error": "45-day cooldown"}'),
        )

    monkeypatch.setattr(droplet_api.urllib.request, "urlopen", fake_urlopen)
    res = client.post("/api/claim/start", json={"ein": "111000111"})
    assert res.status_code == 403
    assert "45-day" in res.get_json()["error"]


def test_dead_tunnel_returns_503(client, monkeypatch):
    def fake_urlopen(req, timeout=0):
        raise ConnectionRefusedError()

    monkeypatch.setattr(droplet_api.urllib.request, "urlopen", fake_urlopen)
    res = client.post("/api/claim/verify", json={"ein": "1", "pin": "000000"})
    assert res.status_code == 503
    assert "error" in res.get_json()


def test_partner_contact_forwarded(client, monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout=0):
        seen["url"] = req.full_url
        return _FakeResponse({"status": "received"})

    monkeypatch.setattr(droplet_api.urllib.request, "urlopen", fake_urlopen)
    res = client.post("/api/partner/contact", json={"name": "Jordan"})
    assert res.status_code == 200
    assert seen["url"].endswith("/api/partner/contact")


def test_oversized_body_rejected(client, monkeypatch):
    called = []
    monkeypatch.setattr(droplet_api.urllib.request, "urlopen",
                        lambda *a, **k: called.append(1))
    res = client.post("/api/claim/start", data="x" * 100_000,
                      content_type="application/json")
    assert res.status_code == 413
    assert not called  # never reached the tunnel
