"""Main triage pipeline — read inbox, classify, label, draft.

Idempotent via the `daanaa/triaged` label: messages already tagged are skipped.

Usage:
    python3 -m scripts.email_agent.run [--dry-run] [--limit 25] [--query ...]
"""

from __future__ import annotations

import argparse

from scripts.email_agent.oauth import gmail_service
from scripts.email_agent.routing import classify
from scripts.email_agent.labels import (
    ensure_labels, TRIAGED, NEEDS_HUMAN, AI_DRAFT, route_label,
)
from scripts.email_agent.drafter import create_draft


def _headers(payload: dict) -> dict[str, str]:
    return {h["name"]: h["value"] for h in payload.get("headers", [])}


def fetch_inbox(svc, query: str, limit: int):
    resp = svc.users().messages().list(userId="me", q=query, maxResults=limit).execute()
    for stub in resp.get("messages", []):
        yield svc.users().messages().get(userId="me", id=stub["id"], format="full").execute()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="No drafts created, no labels applied")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--query", default="newer_than:30d -label:daanaa/triaged")
    args = ap.parse_args()

    svc = gmail_service()
    labels = ensure_labels(svc)
    profile = svc.users().getProfile(userId="me").execute()
    print(f"Inbox: {profile['emailAddress']}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print(f"Query: {args.query}\n")

    stats = {"matched": 0, "drafted": 0, "needs_human": 0, "skipped": 0, "errors": 0}

    for msg in fetch_inbox(svc, args.query, args.limit):
        headers = _headers(msg["payload"])
        route = classify(headers)
        targeted = headers.get("Delivered-To") or headers.get("To", "?")
        subject = headers.get("Subject", "(no subject)")[:55]

        if route is None:
            stats["skipped"] += 1
            continue

        stats["matched"] += 1

        # tier=high|medium → create a draft for human review
        # tier=low → label only, no draft (human-authored is the rule)
        should_draft = route.tier in ("high", "medium")
        will_need_human = route.tier in ("low", "medium")

        add_labels = [labels[TRIAGED], labels[route_label(route.address.split("@")[0])]]
        if will_need_human:
            add_labels.append(labels[NEEDS_HUMAN])

        print(f"  [{route.tier:6}] {targeted} | {subject}")

        if args.dry_run:
            if should_draft:
                stats["drafted"] += 1
                print(f"           → would draft reply from {route.address}")
            if will_need_human:
                stats["needs_human"] += 1
                print(f"           → would flag needs-human")
            continue

        try:
            if should_draft:
                draft_id = create_draft(svc, route, msg)
                add_labels.append(labels[AI_DRAFT])
                stats["drafted"] += 1
                print(f"           ✓ draft created ({draft_id})")
            if will_need_human:
                stats["needs_human"] += 1
                print(f"           ✓ flagged needs-human")
            svc.users().messages().modify(
                userId="me", id=msg["id"], body={"addLabelIds": add_labels}
            ).execute()
        except Exception as e:
            stats["errors"] += 1
            print(f"           ✗ error: {e}")

    print(f"\n{stats}")


if __name__ == "__main__":
    main()
