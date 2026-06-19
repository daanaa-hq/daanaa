"""Main triage pipeline — read inbox, classify, auto-acknowledge, draft.

Idempotent via the `daanaa/triaged` label: messages already tagged are skipped.

Auto-acknowledge policy (no human needed for these):
  tier=high   → auto-send acknowledgment immediately, PLUS create full draft
                for human to review and personalize before final send.
  tier=medium → create draft for human review; auto-ack only (no full reply)
  tier=low    → label only; human writes from scratch

The auto-ack is a brief "we got your email, expect a reply within X days"
with the AI footer. The full drafted reply is queued in Drafts for a human
to review, edit, and send. This separates the instant response from the
considered response — donors, nonprofits, and vendors hear from us immediately
even if a full answer takes a day or two.

Usage:
    python3 -m scripts.email_agent.run [--dry-run] [--limit 25] [--query ...]
"""

from __future__ import annotations

import argparse
import base64
from email.message import EmailMessage

from scripts.email_agent.oauth import gmail_service
from scripts.email_agent.routing import classify
from scripts.email_agent.labels import (
    ensure_labels, TRIAGED, NEEDS_HUMAN, AI_DRAFT, route_label,
)
from scripts.email_agent.drafter import create_draft, build_draft_body
from scripts.email_agent.templates import reply_template, extract_first_name


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
    """Build a short acknowledgement to auto-send immediately."""
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


def _headers(payload: dict) -> dict[str, str]:
    return {h["name"]: h["value"] for h in payload.get("headers", [])}


def fetch_inbox(svc, query: str, limit: int):
    resp = svc.users().messages().list(userId="me", q=query, maxResults=limit).execute()
    for stub in resp.get("messages", []):
        yield svc.users().messages().get(userId="me", id=stub["id"], format="full").execute()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="No sends, no drafts, no labels")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--query", default="newer_than:30d -label:daanaa/triaged")
    ap.add_argument("--no-auto-ack", action="store_true", help="Skip auto-acknowledgements")
    args = ap.parse_args()

    svc = gmail_service()
    labels = ensure_labels(svc)
    profile = svc.users().getProfile(userId="me").execute()
    print(f"Inbox: {profile['emailAddress']}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print(f"Auto-ack: {'OFF' if args.no_auto_ack else 'ON (high/medium tier)'}")
    print(f"Query: {args.query}\n")

    stats = {
        "matched": 0, "auto_acked": 0,
        "drafted": 0, "needs_human": 0,
        "skipped": 0, "errors": 0,
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

        stats["matched"] += 1

        # Decide actions for this tier
        should_auto_ack = route.tier in ("high", "medium") and not args.no_auto_ack
        should_draft    = route.tier in ("high", "medium")
        will_need_human = route.tier in ("low", "medium")

        add_labels = [labels[TRIAGED], labels[route_label(route.address.split("@")[0])]]
        if will_need_human:
            add_labels.append(labels[NEEDS_HUMAN])

        tier_mark = {"high": "✦", "medium": "○", "low": "·"}.get(route.tier, " ")
        print(f"  [{route.tier:6}] {tier_mark} {targeted} | {subject}")

        if args.dry_run:
            if should_auto_ack:
                print(f"           → would auto-ack from {route.address} (instant)")
            if should_draft:
                stats["drafted"] += 1
                print(f"           → would create full draft from {route.address}")
            if will_need_human:
                stats["needs_human"] += 1
                print(f"           → would flag needs-human")
            continue

        try:
            # 1. Auto-send instant acknowledgement (no human needed)
            if should_auto_ack:
                ack_body = _build_auto_ack(route, sender, subject, message_id)
                svc.users().messages().send(
                    userId="me",
                    body={**ack_body, "threadId": msg["threadId"]},
                ).execute()
                stats["auto_acked"] += 1
                add_labels.append(labels.get("daanaa/auto-acked", labels[TRIAGED]))
                print(f"           ✓ auto-ack sent")

            # 2. Create full draft for human to review and personalize
            if should_draft:
                draft_id = create_draft(svc, route, msg)
                add_labels.append(labels[AI_DRAFT])
                stats["drafted"] += 1
                print(f"           ✓ full draft queued ({draft_id})")

            if will_need_human:
                stats["needs_human"] += 1

            svc.users().messages().modify(
                userId="me", id=msg["id"], body={"addLabelIds": add_labels}
            ).execute()

        except Exception as e:
            stats["errors"] += 1
            print(f"           ✗ error: {e}")

    print(f"\n{stats}")
    acked = stats['auto_acked']
    drafted = stats['drafted']
    print(
        f"\nSummary: {acked} instant acks sent, "
        f"{drafted} full drafts queued for human review."
    )


if __name__ == "__main__":
    main()
