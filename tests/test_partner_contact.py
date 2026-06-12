"""Partner contact form — /api/partner/contact.

Vendors, processors, and foundations reach us through this form. It must
validate input, never accept garbage into our inbox pipeline, and route the
inquiry to partners@daanaa.org (founder directive: all platform mail stays
on @daanaa.org addresses).
"""

import pytest

import daanaa_api


@pytest.fixture
def client(monkeypatch):
    daanaa_api.limiter.enabled = False
    sent = []
    monkeypatch.setattr(daanaa_api, "_send_daanaa_email",
                        lambda to, subject, body, **k: sent.append((to, subject, body)))
    daanaa_api.app.config["_test_sent_emails"] = sent
    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c
    daanaa_api.limiter.enabled = True


def _submit(client, **overrides):
    payload = {
        "org_name": "Stax Payments",
        "name": "Jordan Lee",
        "email": "jordan@staxpayments.com",
        "partner_type": "Payment processing",
        "message": "We would like to discuss the zero fee tier for your referred nonprofits.",
    }
    payload.update(overrides)
    return client.post("/api/partner/contact", json=payload)


def test_valid_inquiry_emails_partners_alias(client):
    res = _submit(client)
    assert res.status_code == 200
    sent = daanaa_api.app.config["_test_sent_emails"]
    assert len(sent) == 1
    to, subject, body = sent[0]
    assert to == "partners@daanaa.org"
    assert "Stax Payments" in subject or "Stax Payments" in body
    # The sender's reply address must be in the body so we can answer them
    assert "jordan@staxpayments.com" in body
    assert "zero fee tier" in body


def test_missing_email_rejected(client):
    assert _submit(client, email="").status_code == 400
    assert _submit(client, email="not-an-email").status_code == 400
    assert not daanaa_api.app.config["_test_sent_emails"]


def test_missing_message_rejected(client):
    assert _submit(client, message="").status_code == 400
    assert not daanaa_api.app.config["_test_sent_emails"]


def test_missing_name_rejected(client):
    assert _submit(client, name="").status_code == 400


def test_oversized_message_rejected(client):
    assert _submit(client, message="x" * 6000).status_code == 400
    assert not daanaa_api.app.config["_test_sent_emails"]
