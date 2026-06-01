"""Gmail labels used by the triage agent.

Labels act as state — a message with `daanaa/triaged` is never re-processed.
Per-route labels (e.g. `daanaa/orgs`) give you a one-click view of each channel
in Gmail.
"""

from __future__ import annotations

from scripts.email_agent.routing import ROUTES

ROOT = "daanaa"
TRIAGED = f"{ROOT}/triaged"
NEEDS_HUMAN = f"{ROOT}/needs-human"
AI_DRAFT = f"{ROOT}/ai-drafted"
ERROR = f"{ROOT}/error"


def required_labels() -> list[str]:
    per_route = [f"{ROOT}/{key}" for key in ROUTES]
    return [ROOT, TRIAGED, NEEDS_HUMAN, AI_DRAFT, ERROR, *per_route]


def ensure_labels(svc) -> dict[str, str]:
    """Create any missing labels; return {label_name: label_id}."""
    existing = {
        lab["name"]: lab["id"]
        for lab in svc.users().labels().list(userId="me").execute().get("labels", [])
    }
    for name in required_labels():
        if name in existing:
            continue
        created = svc.users().labels().create(
            userId="me",
            body={
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()
        existing[name] = created["id"]
    return existing


def route_label(route_key: str) -> str:
    return f"{ROOT}/{route_key}"
