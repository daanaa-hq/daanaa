"""Email compliance layer — the pre-listmonk guardrails (task #22 precondition).

Patterns learned from listmonk before any pilot email fires:
  - suppression list honored on every campaign send (unsubs + hard bounces)
  - campaign mail carries List-Unsubscribe + one-click POST headers (RFC 8058)
  - transactional mail (claim PINs) skips marketing headers but still sends
    to suppressed addresses (the user asked for that PIN)
  - unsubscribe endpoint: GET renders a confirm page (mail scanners must not
    unsubscribe people), POST executes; token is HMAC, no login needed.

Deliverability is a burn-once asset: @daanaa.org reputation never recovers
from a spam blocklist. These tests are the floor under every future send.
"""

import os
import sqlite3

import pytest

os.environ.setdefault("EMAIL_UNSUB_SECRET", "test-secret-for-hmac")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import email_service as es


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    p = str(tmp_path / "email_test.db")
    monkeypatch.setenv("DAANAA_DB_PATH", p)
    sqlite3.connect(p).close()
    return p


class TestUnsubscribeToken:
    def test_token_stable_and_case_insensitive(self):
        assert es.unsubscribe_token("A@x.org") == es.unsubscribe_token("a@x.org")
        assert len(es.unsubscribe_token("a@x.org")) == 32

    def test_token_verifies(self):
        t = es.unsubscribe_token("dir@org.org")
        assert es.verify_unsubscribe_token("dir@org.org", t)
        assert not es.verify_unsubscribe_token("dir@org.org", "0" * 32)
        assert not es.verify_unsubscribe_token("other@org.org", t)


class TestSuppression:
    def test_suppress_and_check(self, db_path):
        assert not es.is_suppressed("gone@x.org")
        es.suppress_email("gone@x.org", reason="unsubscribed")
        assert es.is_suppressed("GONE@x.org")  # case-insensitive

    def test_campaign_send_blocked_transactional_allowed(self, db_path, monkeypatch):
        es.suppress_email("optout@x.org", reason="unsubscribed")
        svc = es.EmailService()
        svc.enabled = False  # dry-run mode: send() returns True without SMTP
        # Campaign mail to a suppressed address must be refused
        assert svc.send("optout@x.org", "News", "<p>hi</p>", "hi",
                        kind="campaign") is False
        # Transactional mail (user-requested PIN) still goes through
        assert svc.send("optout@x.org", "Your PIN", "<p>123</p>", "123",
                        kind="transactional") is True


class TestHeaders:
    def test_campaign_smtp_message_has_unsubscribe_headers(self, db_path, monkeypatch):
        sent = {}

        class FakeSMTP:
            def __init__(self, host, port): pass
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def send_message(self, msg): sent["msg"] = msg
            def starttls(self): pass
            def login(self, u, p): pass

        monkeypatch.setattr(es.smtplib, "SMTP", FakeSMTP)
        svc = es.EmailService()
        svc.enabled = True
        svc.resend_api_key = ""
        assert svc.send("donor@x.org", "Digest", "<p>d</p>", "d", kind="campaign")
        msg = sent["msg"]
        assert "List-Unsubscribe" in msg
        assert "api/email/unsubscribe" in msg["List-Unsubscribe"]
        assert msg["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"

    def test_transactional_smtp_has_no_marketing_headers(self, db_path, monkeypatch):
        sent = {}

        class FakeSMTP:
            def __init__(self, host, port): pass
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def send_message(self, msg): sent["msg"] = msg

        monkeypatch.setattr(es.smtplib, "SMTP", FakeSMTP)
        svc = es.EmailService()
        svc.enabled = True
        svc.resend_api_key = ""
        assert svc.send("dir@x.org", "Your PIN", "<p>1</p>", "1",
                        kind="transactional")
        assert sent["msg"]["List-Unsubscribe"] is None


class TestUnsubscribeEndpoint:
    @pytest.fixture
    def client(self, db_path, monkeypatch):
        import daanaa_api
        monkeypatch.setattr(daanaa_api, "DB_PATH", db_path)
        monkeypatch.setattr(daanaa_api, "LIVE_DB_PATH", db_path)
        daanaa_api.limiter.enabled = False
        daanaa_api.app.config["TESTING"] = True
        with daanaa_api.app.test_client() as c:
            yield c
        daanaa_api.limiter.enabled = True

    def test_get_renders_confirm_not_unsub(self, client, db_path):
        t = es.unsubscribe_token("d@x.org")
        r = client.get(f"/api/email/unsubscribe?e=d@x.org&t={t}")
        assert r.status_code == 200
        assert not es.is_suppressed("d@x.org"), "GET must never unsubscribe"

    def test_post_unsubscribes_with_valid_token(self, client, db_path):
        t = es.unsubscribe_token("d2@x.org")
        r = client.post(f"/api/email/unsubscribe?e=d2@x.org&t={t}")
        assert r.status_code == 200
        assert es.is_suppressed("d2@x.org")

    def test_post_rejects_bad_token(self, client, db_path):
        r = client.post("/api/email/unsubscribe?e=d3@x.org&t=" + "0" * 32)
        assert r.status_code == 403
        assert not es.is_suppressed("d3@x.org")
