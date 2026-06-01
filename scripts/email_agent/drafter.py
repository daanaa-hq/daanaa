"""Create Gmail drafts for triaged messages."""

from __future__ import annotations

import base64
from email.message import EmailMessage

from scripts.email_agent.routing import Route
from scripts.email_agent.templates import reply_template, extract_first_name


def build_draft_body(route: Route, original_headers: dict[str, str]) -> dict:
    """Return a Gmail API draft body for the given inbound message."""
    sender = original_headers.get("From", "")
    subject = original_headers.get("Subject", "")
    message_id = original_headers.get("Message-ID") or original_headers.get("Message-Id")

    first_name = extract_first_name(sender)
    _, body = reply_template(route, first_name)

    msg = EmailMessage()
    msg["To"] = sender
    msg["From"] = route.address  # requires send-as alias configured to send
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if message_id:
        msg["In-Reply-To"] = message_id
        msg["References"] = message_id
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"message": {"raw": raw}}


def create_draft(svc, route: Route, original_msg: dict) -> str:
    """Create a Gmail draft replying to original_msg. Returns the draft id."""
    headers = {h["name"]: h["value"] for h in original_msg["payload"].get("headers", [])}
    body = build_draft_body(route, headers)
    body["message"]["threadId"] = original_msg["threadId"]
    draft = svc.users().drafts().create(userId="me", body=body).execute()
    return draft["id"]
