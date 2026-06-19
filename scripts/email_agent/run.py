"""Main triage pipeline — read inbox, classify, auto-acknowledge, draft.

Idempotent via the `daanaa/triaged` label: messages already tagged are skipped.

Auto-acknowledge policy:
  tier=high   → auto-send ack immediately + create full draft for human review
  tier=medium → auto-ack only; draft queued for human
  tier=low    → label only; human writes from scratch
  reply       → draft queued, NO auto-ack (prevents infinite ack loops)
  internal/automated → silently archived, nothing sent

Usage:
    python3 -m scripts.email_agent.run [--dry-run] [--limit 25] [--query ...]
"""

from __future__ import annotations

import argparse
import base64
import re
from email.message import EmailMessage

from scripts.email_agent.oauth import gmail_service
from scripts.email_agent.routing import classify
from scripts.email_agent.labels import (
    ensure_labels, TRIAGED, NEEDS_HUMAN, AI_DRAFT, route_label,
)
from scripts.email_agent.drafter import create_draft
from scripts.email_agent.templates import extract_first_name

# ---------------------------------------------------------------------------
# Sender classification
# ---------------------------------------------------------------------------

_AUTOMATED_FROM_RE = re.compile(
    r"(no.?reply|noreply|postmaster|mailer.?daemon|do.not.reply|"
    r"notifications?|automated|bounce|alert|report\.system|"
    r"safebrowsing|google-no-reply)@",
    re.I,
)

_OWN_DOMAINS_RE = re.compile(r"@(daanaa\.org|ecomargins\.com)[\s>]?$", re.I)

FOUNDER_ALERT_ADDRESS = "akbar.khowaja@gmail.com"


def _is_internal(headers: dict[str, str]) -> bool:
    """Sender is one of our own domains — silently drop, never draft or ack.

    Google Groups rewrites From: when the original sender has DMARC p=reject
    (Google, Microsoft, Yahoo). It preserves Reply-To as the real sender.
    If Reply-To is external, treat as a real human email.
    """
    reply_to = headers.get("Reply-To", "")
    if reply_to and not _OWN_DOMAINS_RE.search(reply_to):
        return False
    return bool(_OWN_DOMAINS_RE.search(headers.get("From", "")))


def _is_automated(headers: dict[str, str]) -> bool:
    sender = headers.get("From", "")
    if _AUTOMATED_FROM_RE.search(sender):
        return True
    if headers.get("Auto-Submitted", "no").lower() not in ("no", ""):
        return True
    if headers.get("Precedence", "").lower() in ("bulk", "list", "junk"):
        return True
    subj = headers.get("Subject", "").lower()
    if "submitter: google.com" in subj or "report domain:" in subj:
        return True
    return False


def _is_reply(headers: dict[str, str]) -> bool:
    return bool(headers.get("In-Reply-To") or headers.get("References"))


# ---------------------------------------------------------------------------
# Message builders
# ---------------------------------------------------------------------------

_AUTO_ACK_FOOTER = (
    "\n\nDaanaa\n"
    "(This is an automatic acknowledgement. A real person will follow up "
    "with a full response, typically within 1 to 2 business days.)"
)

_TIER_SLA = {
    "high":   "1 business day",
    "medium": "2 business days",
    "low":    "2–3 business days",
}


def _build_auto_ack(route, sender: str, subject: str, message_id: str | None) -> dict:
    first_name = extract_first_name(sender)
    greet = f"Hi {first_name}," if first_name else "Hi,"
    sla = _TIER_SLA.get(route.tier, "2 business days")
    body = (
        f"{greet}\n\n"
        f"Thanks for writing to {route.address}. We got your message "
        f"and a real person will get back to you within {sla}.\n\n"
        "If this is urgent, reply and say so. We prioritize time-sensitive requests."
        + _AUTO_ACK_FOOTER
    )
    msg = EmailMessage()
    msg["To"] = sender
    msg["From"] = route.address
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if message_id:
        msg["In-Reply-To"] = message_id
        msg["References"] = message_id
    msg.set_content(body)
    return {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}


def _build_founder_alert(route, sender: str, subject: str, is_reply: bool) -> dict:
    kind = "Reply" if is_reply else "New message"
    body = (
        f"{kind} via {route.address}\n\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n\n"
        f"Draft queued in hello@ecomargins.com — review and send when ready.\n\n"
        f"Daanaa email agent"
    )
    msg = EmailMessage()
    msg["To"] = FOUNDER_ALERT_ADDRESS
    msg["From"] = "hello@daanaa.org"
    msg["Subject"] = f"[Daanaa] {kind}: {subject[:60]}"
    msg.set_content(body)
    return {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def _headers(payload: dict) -> dict[str, str]:
    return {h["name"]: h["value"] for h in payload.get("headers", [])}


def fetch_inbox(svc, query: str, limit: int):
    resp = svc.users().messages().list(userId="me", q=query, maxResults=limit).execute()
    for stub in resp.get("messages", []):
        yield svc.users().messages().get(userId="me", id=stub["id"], format="full").execute()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--query", default="newer_than:30d -label:daanaa/triaged")
    ap.add_argument("--no-auto-ack", action="store_true")
    ap.add_argument("--no-alerts", action="store_true", help="Skip founder alert emails")
    args = ap.parse_args()

    svc = gmail_service()
    labels = ensure_labels(svc)
    profile = svc.users().getProfile(userId="me").execute()
    print(f"Inbox: {profile['emailAddress']}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print(f"Query: {args.query}\n")

    stats = {
        "matched": 0, "auto_acked": 0, "drafted": 0,
        "needs_human": 0, "alerts_sent": 0,
        "skipped": 0, "automated": 0, "errors": 0,
    }

    for msg in fetch_inbox(svc, args.query, args.limit):
        headers = _headers(msg["payload"])
        route = classify(headers)
        targeted = headers.get("Delivered-To") or headers.get("To", "?")
        subject = headers.get("Subject", "(no subject)")[:55]
        sender = headers.get("From", "")
        message_id = headers.get("Message-ID") or headers.get("Message-Id")

        if route is None:
            stats["skipped"] += 1
            continue

        # Internal — silently archive
        if _is_internal(headers):
            stats["automated"] += 1
            print(f"  [intern] ⊘ {targeted} | {subject}")
            if not args.dry_run:
                try:
                    svc.users().messages().modify(
                        userId="me", id=msg["id"],
                        body={"addLabelIds": [labels[TRIAGED]]},
                    ).execute()
                except Exception as e:
                    stats["errors"] += 1
                    print(f"           ✗ {e}")
            continue

        # Automated — silently archive
        if _is_automated(headers):
            stats["automated"] += 1
            print(f"  [auto  ] ⊘ {targeted} | {subject}")
            if not args.dry_run:
                try:
                    svc.users().messages().modify(
                        userId="me", id=msg["id"],
                        body={"addLabelIds": [labels[TRIAGED]]},
                    ).execute()
                except Exception as e:
                    stats["errors"] += 1
                    print(f"           ✗ {e}")
            continue

        # Real human email
        stats["matched"] += 1
        is_reply = _is_reply(headers)

        should_auto_ack = route.tier in ("high", "medium") and not args.no_auto_ack and not is_reply
        should_draft    = route.tier in ("high", "medium")
        will_need_human = route.tier in ("low", "medium") or is_reply
        should_alert    = not args.no_alerts

        add_labels = [labels[TRIAGED], labels[route_label(route.address.split("@")[0])]]
        if will_need_human:
            add_labels.append(labels[NEEDS_HUMAN])

        tier_mark = {"high": "✦", "medium": "○", "low": "·"}.get(route.tier, " ")
        reply_tag = " [reply]" if is_reply else ""
        print(f"  [{route.tier:6}] {tier_mark} {targeted} | {subject}{reply_tag}")

        if args.dry_run:
            if should_auto_ack:
                print(f"           → would auto-ack from {route.address}")
            elif is_reply:
                print(f"           → reply: no auto-ack, draft queued for human")
            if should_draft:
                stats["drafted"] += 1
                print(f"           → would create full draft")
            if will_need_human:
                stats["needs_human"] += 1
            if should_alert:
                print(f"           → would alert {FOUNDER_ALERT_ADDRESS}")
            continue

        try:
            if should_auto_ack:
                ack_body = _build_auto_ack(route, sender, subject, message_id)
                svc.users().messages().send(
                    userId="me",
                    body={**ack_body, "threadId": msg["threadId"]},
                ).execute()
                stats["auto_acked"] += 1
                add_labels.append(labels.get("daanaa/auto-acked", labels[TRIAGED]))
                print(f"           ✓ auto-ack sent")

            if should_draft:
                draft_id = create_draft(svc, route, msg)
                add_labels.append(labels[AI_DRAFT])
                stats["drafted"] += 1
                print(f"           ✓ draft queued ({draft_id})")

            if will_need_human:
                stats["needs_human"] += 1

            if should_alert:
                alert_body = _build_founder_alert(route, sender, subject, is_reply)
                svc.users().messages().send(userId="me", body=alert_body).execute()
                stats["alerts_sent"] += 1
                print(f"           ✓ founder alert → {FOUNDER_ALERT_ADDRESS}")

            svc.users().messages().modify(
                userId="me", id=msg["id"], body={"addLabelIds": add_labels}
            ).execute()

        except Exception as e:
            stats["errors"] += 1
            print(f"           ✗ error: {e}")

    print(f"\n{stats}")
    print(
        f"\nSummary: {stats['automated']} automated silenced, "
        f"{stats['auto_acked']} acks sent, "
        f"{stats['drafted']} drafts queued, "
        f"{stats['alerts_sent']} founder alerts sent."
    )


if __name__ == "__main__":
    main()
