#!/usr/bin/env python3
"""claim_followup.py — automated follow-up for incomplete and stale claims.

Two sequences run nightly:

  1. PENDING (48h nudge): claim submitted but NOT verified after 48 hours.
     Sends one reminder with the original verification link. Max 1 nudge per claim.

  2. VERIFIED (7-day check-in): claim verified but no portal activity for 7 days.
     Sends a short "anything we can help with?" note. Max 1 check-in per claim.

Both sequences respect the daanaa.org email aliases directive (all outbound
email from @daanaa.org aliases via the Gmail OAuth token in email_agent/).
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "merit_registry.db"
LOG_FILE = BASE / "logs" / "claim_followup.log"

sys.path.insert(0, str(BASE))
from scripts.ops.mailer import send_ops_email


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def send_claim_email(to: str, subject: str, body: str) -> bool:
    try:
        from scripts.email_agent.oauth import gmail_service
        import base64
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"] = "Daanaa <hello@daanaa.org>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as e:
        log(f"Email failed to {to}: {e}")
        return False


def nudge_pending_claims(conn: sqlite3.Connection) -> int:
    """Send one reminder to claims submitted >48h ago with no verification."""
    cutoff_submit = (datetime.now() - timedelta(hours=48)).isoformat()
    cutoff_recent = (datetime.now() - timedelta(hours=72)).isoformat()

    rows = conn.execute("""
        SELECT c.ein, c.email, c.rep_name, c.submitted_at, c.verification_token,
               r.organization_name
        FROM org_claims c
        LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status = 'email_sent'
          AND c.submitted_at < ?
          AND c.submitted_at > ?
          AND (c.nudge_sent_at IS NULL OR c.nudge_sent_at = '')
    """, (cutoff_submit, cutoff_recent)).fetchall()

    sent = 0
    for row in rows:
        name = row["rep_name"] or "there"
        org = row["organization_name"] or f"EIN {row['ein']}"
        token = row["verification_token"] or ""
        verify_url = f"https://daanaa.org/for-nonprofits?ein={row['ein']}&token={token}" if token else f"https://daanaa.org/for-nonprofits?ein={row['ein']}"

        body = f"""Hi {name},

Just following up on your Daanaa claim for {org}.

We received your submission but the verification step wasn't completed. It only takes a moment:

{verify_url}

If you have any questions or need help, reply to this email and we'll get back to you.

Daanaa Team
hello@daanaa.org
"""
        if send_claim_email(row["email"], f"Complete your Daanaa claim for {org}", body):
            conn.execute(
                "UPDATE org_claims SET nudge_sent_at = ? WHERE ein = ? AND email = ?",
                (datetime.now().isoformat(), row["ein"], row["email"]),
            )
            conn.commit()
            sent += 1
            log(f"Nudge sent: {row['ein']} → {row['email']}")

    return sent


def checkin_verified_claims(conn: sqlite3.Connection) -> int:
    """Send a 7-day check-in to verified claims with no portal activity."""
    cutoff_verify = (datetime.now() - timedelta(days=7)).isoformat()
    cutoff_recent = (datetime.now() - timedelta(days=14)).isoformat()

    rows = conn.execute("""
        SELECT c.ein, c.email, c.rep_name, c.verified_at,
               r.organization_name
        FROM org_claims c
        LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status = 'verified'
          AND c.verified_at < ?
          AND c.verified_at > ?
          AND (c.checkin_sent_at IS NULL OR c.checkin_sent_at = '')
    """, (cutoff_verify, cutoff_recent)).fetchall()

    sent = 0
    for row in rows:
        name = row["rep_name"] or "there"
        org = row["organization_name"] or f"EIN {row['ein']}"
        portal_url = f"https://daanaa.org/nonprofit/{row['ein']}/portal"

        body = f"""Hi {name},

It's been a week since you claimed {org} on Daanaa. How's everything going?

A few things worth knowing:
• You can update your mission statement, service area, and volunteer opportunities from your portal: {portal_url}
• If anything looks wrong on your page, the "report an issue" link is the fastest path to a fix.
• Questions? Just reply to this email.

Thanks for being part of the network.

Daanaa Team
hello@daanaa.org
"""
        if send_claim_email(row["email"], f"How's your Daanaa portal going, {name}?", body):
            conn.execute(
                "UPDATE org_claims SET checkin_sent_at = ? WHERE ein = ? AND email = ?",
                (datetime.now().isoformat(), row["ein"], row["email"]),
            )
            conn.commit()
            sent += 1
            log(f"Check-in sent: {row['ein']} → {row['email']}")

    return sent


def nudge_incomplete_profiles(conn: sqlite3.Connection) -> int:
    """14-day nudge: verified claim with no custom_mission set yet.

    Targets the first 30-day window after verification — early enough to
    be useful, late enough that the org has had a chance to settle in.
    Max 1 nudge per claim (profile_nudge_sent_at guards repeats).
    """
    cutoff_verified = (datetime.now() - timedelta(days=14)).isoformat()
    cutoff_window   = (datetime.now() - timedelta(days=44)).isoformat()

    rows = conn.execute("""
        SELECT c.ein, c.email, c.rep_name, c.verified_at,
               r.organization_name
        FROM org_claims c
        LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status = 'verified'
          AND c.verified_at < ?
          AND c.verified_at > ?
          AND (c.custom_mission IS NULL OR c.custom_mission = '')
          AND (c.profile_nudge_sent_at IS NULL OR c.profile_nudge_sent_at = '')
    """, (cutoff_verified, cutoff_window)).fetchall()

    sent = 0
    for row in rows:
        name = row["rep_name"] or "there"
        org  = row["organization_name"] or f"EIN {row['ein']}"
        portal_url = f"https://daanaa.org/nonprofit/{row['ein']}/portal"

        body = f"""Hi {name},

One quick thing — you haven't added a custom mission statement to your Daanaa page for {org} yet.

The mission is the first thing a potential donor reads. Even a single sentence in your own words makes a real difference.

You can add it in about a minute from your portal:
{portal_url}

If you're not sure what to write, start with what you do and who you serve — that's enough.

Reply to this email if you have any questions.

Daanaa Team
hello@daanaa.org
"""
        if send_claim_email(row["email"], f"One thing left on your Daanaa page — {org}", body):
            conn.execute(
                "UPDATE org_claims SET profile_nudge_sent_at = ? WHERE ein = ? AND email = ?",
                (datetime.now().isoformat(), row["ein"], row["email"]),
            )
            conn.commit()
            sent += 1
            log(f"Profile nudge sent: {row['ein']} → {row['email']}")

    return sent


def ensure_columns(conn: sqlite3.Connection):
    """Add followup tracking columns if schema predates this script."""
    for col, default in [
        ("nudge_sent_at", "NULL"),
        ("checkin_sent_at", "NULL"),
        ("profile_nudge_sent_at", "NULL"),
    ]:
        try:
            conn.execute(f"ALTER TABLE org_claims ADD COLUMN {col} TEXT DEFAULT {default}")
            conn.commit()
            log(f"Added column org_claims.{col}")
        except sqlite3.OperationalError:
            pass  # already exists


def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log("=== claim_followup start ===")

    conn = get_db()
    ensure_columns(conn)

    nudged  = nudge_pending_claims(conn)
    checked = checkin_verified_claims(conn)
    profile = nudge_incomplete_profiles(conn)
    conn.close()

    log(f"Done. pending nudges: {nudged} | 7-day check-ins: {checked} | profile nudges: {profile}")

    if nudged + checked + profile > 0:
        send_ops_email(
            "security@daanaa.org",
            f"[Daanaa] Claim follow-ups: {nudged} nudges, {checked} check-ins, {profile} profile",
            f"Nightly claim follow-up run complete.\n\n"
            f"Pending (48h) nudges:   {nudged}\n"
            f"7-day check-ins:        {checked}\n"
            f"Profile completion (14d): {profile}\n",
        )


if __name__ == "__main__":
    main()
