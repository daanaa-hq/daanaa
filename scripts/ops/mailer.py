"""Shared ops mailer — sends via the email_agent Gmail token, daanaa.org
aliases on both ends (founder directive). Used by watchdog, digest, nudge.

PHONE DELIVERY (added 2026-08-08)
--------------------------------
On 2026-08-08 daanaa.org was down ~14h without anyone noticing. The watchdog was
not at fault: it detected the outage, re-alerted on schedule, and the mail send
succeeded. The alerts went to security@daanaa.org — an inbox nobody watches while
away from a desk. Detection worked; delivery reached the wrong place.

So every ops alert now ALSO pushes to a phone when NTFY_TOPIC is configured.
Email remains the record; push is what actually wakes someone up.

Enable (free, no account):
  1. Install the "ntfy" app (iOS/App Store, Android/Play or F-Droid)
  2. Subscribe to a private, unguessable topic, e.g. daanaa-ops-<random>
  3. Add to .env:  NTFY_TOPIC=daanaa-ops-<random>
                   NTFY_SERVER=https://ntfy.sh      (optional, this is the default)

The topic name IS the credential on ntfy.sh — anyone who knows it can read your
alerts. Use something random, never the bare word "daanaa". Alert bodies carry
service names and status only; never donor, claimant, or user data (Stewardship
P2). Do not widen what gets sent here without re-reading that.

Self-hosting ntfy on the droplet removes the third-party entirely and is the
better long-term answer if alert content ever gets richer.
"""
import base64
import json
import os
import sys
import urllib.request
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_ENV = Path(__file__).resolve().parents[2] / ".env"


def _env(key: str, default: str = "") -> str:
    """Read from the process env, falling back to .env (cron has a bare env)."""
    if os.environ.get(key):
        return os.environ[key]
    try:
        for line in _ENV.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return default


def send_push(title: str, body: str, priority: str = "high") -> bool:
    """Push to phone via ntfy. No-op (returns False) when NTFY_TOPIC is unset.

    Deliberately never raises: a push failure must not prevent the email, and an
    alerting path that can crash its caller is worse than no alerting path.
    """
    topic = _env("NTFY_TOPIC")
    if not topic:
        return False
    server = _env("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    try:
        req = urllib.request.Request(
            f"{server}/{topic}",
            data=body.encode("utf-8")[:3800],
            headers={
                "Title": title[:200],
                "Priority": priority,
                "Tags": "rotating_light",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=15).read()
        return True
    except Exception as e:
        print(f"ops push failed: {e}", file=sys.stderr)
        return False


def send_ops_email(to_addr: str, subject: str, body: str,
                   from_addr: str = "Daanaa Ops <security@daanaa.org>") -> bool:
    """Send the alert. Email is the durable record; push is the one that reaches
    a human. Returns True if EITHER channel delivered — an alert that reached the
    phone but not the inbox is still a delivered alert."""
    pushed = send_push(subject, body)
    mailed = False
    try:
        from scripts.email_agent.oauth import gmail_service
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()
        mailed = True
    except Exception as e:
        print(f"ops mail failed: {e}", file=sys.stderr)
    return mailed or pushed
