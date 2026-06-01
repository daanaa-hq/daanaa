"""Dry-run inbox triage.

Reads recent messages from hello@ecomargins.com, classifies each by the
@daanaa.org alias it was sent to, and prints what the agent WOULD do —
without sending, drafting, or modifying anything.

Usage:
    python3 -m scripts.email_agent.triage [--limit 20] [--query "newer_than:7d"]
"""

from __future__ import annotations

import argparse
from typing import Iterable

from scripts.email_agent.oauth import gmail_service
from scripts.email_agent.routing import classify, ROUTES


def _headers_dict(payload: dict) -> dict[str, str]:
    return {h["name"]: h["value"] for h in payload.get("headers", [])}


def list_recent(svc, query: str, limit: int) -> Iterable[dict]:
    resp = svc.users().messages().list(userId="me", q=query, maxResults=limit).execute()
    for stub in resp.get("messages", []):
        yield svc.users().messages().get(
            userId="me", id=stub["id"], format="metadata",
            metadataHeaders=["Delivered-To", "To", "Cc", "From", "Subject", "Date"],
        ).execute()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--query", default="newer_than:30d")
    args = ap.parse_args()

    svc = gmail_service()
    profile = svc.users().getProfile(userId="me").execute()
    print(f"Inbox: {profile['emailAddress']}")
    print(f"Routing table: {len(ROUTES)} aliases (see email-agent-routing.md)")
    print(f"Scanning: q='{args.query}' limit={args.limit}\n")

    matched, unmatched = 0, 0
    by_tier: dict[str, int] = {}

    for msg in list_recent(svc, args.query, args.limit):
        headers = _headers_dict(msg["payload"])
        route = classify(headers)
        sender = headers.get("From", "?")
        subject = headers.get("Subject", "(no subject)")[:60]
        targeted = headers.get("Delivered-To") or headers.get("To", "?")

        if route is None:
            unmatched += 1
            print(f"  [skip] {targeted!r:40} | {sender[:30]} | {subject}")
            continue

        matched += 1
        by_tier[route.tier] = by_tier.get(route.tier, 0) + 1
        action = {
            "high":   "draft + auto-send (with AI-disclosed footer)",
            "medium": "auto-acknowledge + log; human approves any data change",
            "low":    "draft for human review; AI never sends",
        }[route.tier]
        print(f"  [{route.tier:6}] {route.address:24} → {route.department}")
        print(f"           from: {sender[:50]}")
        print(f"           subj: {subject}")
        print(f"           plan: {action}\n")

    print(f"Matched: {matched}  Unmatched: {unmatched}")
    print(f"By tier: {by_tier}")
    print("\nDry-run only — no replies sent, no labels applied.")


if __name__ == "__main__":
    main()
