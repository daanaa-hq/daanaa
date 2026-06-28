#!/usr/bin/env python3
"""events_automation.py — daily event lifecycle automation.

Tasks run in order:
  1. Auto-fill: mark events 'filled' when confirmed signups hit capacity
  2. Pre-event reminder: email confirmed signups 24h before the event
  3. Post-event nudge: email the org the day after to verify volunteer hours
  4. Reminder guard: mark pre_reminder_sent / post_nudge_sent to fire exactly once

Cron: 0 8 * * *  (8am daily, after overnight expiry at 2:30am)
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailer import send_ops_email

DB = Path.home() / "meritgiving/data/merit_registry.db"
DAANAA_BASE_URL = "https://daanaa.org"


def _db():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_columns(db):
    """Add automation guard columns if not present (idempotent)."""
    for col in ("pre_reminder_sent_at", "post_nudge_sent_at"):
        try:
            db.execute(f"ALTER TABLE volunteer_events ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    db.commit()


# ── Task 1: Auto-fill ──────────────────────────────────────────────────────

def auto_fill_events(db) -> int:
    """Mark active events 'filled' when confirmed signups reach or exceed capacity."""
    events = db.execute(
        "SELECT id, capacity FROM volunteer_events "
        "WHERE status='active' AND capacity IS NOT NULL AND event_date >= date('now')"
    ).fetchall()
    filled = 0
    for ev in events:
        count = db.execute(
            "SELECT COALESCE(SUM(total_count),0) FROM org_signups "
            "WHERE event_id=? AND status='confirmed'",
            (ev["id"],),
        ).fetchone()[0]
        if count >= ev["capacity"]:
            db.execute(
                "UPDATE volunteer_events SET status='filled', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (ev["id"],),
            )
            filled += 1
    db.commit()
    if filled:
        print(f"[auto_fill] marked {filled} event(s) as filled")
    return filled


# ── Task 2: Pre-event reminders ────────────────────────────────────────────

def send_pre_event_reminders(db) -> int:
    """Email confirmed signups for events happening tomorrow. Fires once per event."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    events = db.execute(
        "SELECT ve.*, r.organization_name AS org_name "
        "FROM volunteer_events ve "
        "LEFT JOIN registry_enriched r ON ve.ein=r.EIN "
        "WHERE ve.event_date=? AND ve.status IN ('active','filled') "
        "AND (ve.pre_reminder_sent_at IS NULL)",
        (tomorrow,),
    ).fetchall()

    sent_total = 0
    for ev in events:
        signups = db.execute(
            "SELECT contact_name, contact_email, attendees, total_count "
            "FROM org_signups WHERE event_id=? AND status='confirmed'",
            (ev["id"],),
        ).fetchall()
        if not signups:
            db.execute(
                "UPDATE volunteer_events SET pre_reminder_sent_at=CURRENT_TIMESTAMP WHERE id=?",
                (ev["id"],),
            )
            continue

        event_url = f"{DAANAA_BASE_URL}/events/{ev['id']}"
        location = "Virtual" if ev["is_virtual"] else ", ".join(
            filter(None, [ev["location_city"], ev["location_state"]])
        ) or "See event page"

        org_display = ev["org_name"] or "the organizer"
        time_str = ""
        if ev["start_time"]:
            h, m = map(int, ev["start_time"].split(":"))
            ampm = "pm" if h >= 12 else "am"
            time_str = f" at {h % 12 or 12}:{m:02d} {ampm}"

        # Build optional prep details (new fields, graceful fallback for older rows)
        what_to_bring = getattr(ev, 'what_to_bring', None) or (ev["what_to_bring"] if "what_to_bring" in ev.keys() else None)
        parking_info  = getattr(ev, 'parking_info',  None) or (ev["parking_info"]  if "parking_info"  in ev.keys() else None)
        waiver_url    = getattr(ev, 'waiver_url',    None) or (ev["waiver_url"]    if "waiver_url"    in ev.keys() else None)

        for s in signups:
            try:
                attendees = json.loads(s["attendees"] or "[]")
            except (json.JSONDecodeError, TypeError):
                attendees = []
            party = (", ".join(a["name"] for a in attendees if a.get("name"))
                     or s["contact_name"])

            prep_lines = ""
            if what_to_bring:
                prep_lines += f"What to bring: {what_to_bring}\n"
            if parking_info:
                prep_lines += f"Parking / transit: {parking_info}\n"
            if waiver_url:
                prep_lines += f"Waiver required: {waiver_url}\n"

            body = (
                f"Hi {s['contact_name']},\n\n"
                f"This is a reminder that {ev['title']} is tomorrow"
                f"{time_str}.\n\n"
                f"Location: {location}\n"
                f"Organizer: {org_display}\n"
                f"Attending: {party}\n"
                + (f"\n{prep_lines}" if prep_lines else "")
                + f"\nEvent page: {event_url}\n\n"
                f"Need to cancel? Visit:\n"
                f"{event_url}?cancel=<your booking token is in your confirmation email>\n\n"
                f"Your contact info was shared with the organizer only. "
                f"Daanaa does not retain your information after the event.\n\n"
                f"— Daanaa team"
            )
            send_ops_email(
                s["contact_email"],
                f"Tomorrow: {ev['title']}",
                body,
                from_addr="Daanaa Events <events@daanaa.org>",
            )
            sent_total += 1

        db.execute(
            "UPDATE volunteer_events SET pre_reminder_sent_at=CURRENT_TIMESTAMP WHERE id=?",
            (ev["id"],),
        )

    db.commit()
    if sent_total:
        print(f"[pre_reminder] sent {sent_total} reminder(s) for {len(events)} event(s) tomorrow")
    return sent_total


# ── Task 3: Post-event org nudge ───────────────────────────────────────────

def send_post_event_nudges(db) -> int:
    """Email the org's events coordinator the day after an event to verify hours.

    Only fires if there are confirmed signups that still need verification.
    Uses org_contacts.events_email → falls back to org_claims.email.
    """
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    events = db.execute(
        "SELECT ve.*, r.organization_name AS org_name "
        "FROM volunteer_events ve "
        "LEFT JOIN registry_enriched r ON ve.ein=r.EIN "
        "WHERE ve.event_date=? AND ve.status IN ('active','filled','expired') "
        "AND (ve.post_nudge_sent_at IS NULL)",
        (yesterday,),
    ).fetchall()

    nudged = 0
    for ev in events:
        # Only nudge if there are unverified confirmed signups
        unverified = db.execute(
            "SELECT COUNT(*) FROM org_signups "
            "WHERE event_id=? AND status='confirmed'",
            (ev["id"],),
        ).fetchone()[0]

        if not unverified:
            db.execute(
                "UPDATE volunteer_events SET post_nudge_sent_at=CURRENT_TIMESTAMP WHERE id=?",
                (ev["id"],),
            )
            db.commit()
            continue

        # Find best contact email: events_email → claim email
        contact_row = db.execute(
            "SELECT events_email, events_name FROM org_contacts WHERE ein=?",
            (ev["ein"],),
        ).fetchone()
        claim_row = db.execute(
            "SELECT email, rep_name FROM org_claims WHERE ein=? "
            "AND claim_status IN ('verified','active') AND revoked_at IS NULL "
            "ORDER BY verified_at DESC LIMIT 1",
            (ev["ein"],),
        ).fetchone()

        to_email = (contact_row and contact_row["events_email"]) or (claim_row and claim_row["email"])
        to_name  = (contact_row and contact_row["events_name"])  or (claim_row and claim_row["rep_name"]) or "Hi"

        if not to_email:
            db.execute(
                "UPDATE volunteer_events SET post_nudge_sent_at=CURRENT_TIMESTAMP WHERE id=?",
                (ev["id"],),
            )
            db.commit()
            continue

        org_display   = ev["org_name"] or "your organization"
        attendees_url = f"{DAANAA_BASE_URL}/nonprofit/dashboard/{ev['ein']}"

        body = (
            f"Hi {to_name},\n\n"
            f"Thank you for hosting {ev['title']} yesterday on behalf of {org_display}.\n\n"
            f"{unverified} volunteer(s) signed up and may be waiting for their hours to be verified "
            f"for their Giving Wallet.\n\n"
            f"To verify hours, visit your event dashboard:\n"
            f"{attendees_url}\n\n"
            f"Verifying hours takes less than a minute and helps volunteers track their impact.\n\n"
            f"— Daanaa team\n\n"
            f"Questions? Reply to events@daanaa.org"
        )
        send_ops_email(
            to_email,
            f"Verify volunteer hours — {ev['title']}",
            body,
            from_addr="Daanaa Events <events@daanaa.org>",
        )
        db.execute(
            "UPDATE volunteer_events SET post_nudge_sent_at=CURRENT_TIMESTAMP WHERE id=?",
            (ev["id"],),
        )
        db.commit()
        nudged += 1

    if nudged:
        print(f"[post_nudge] sent {nudged} hour-verification nudge(s)")
    return nudged


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    db = _db()
    _ensure_columns(db)
    filled    = auto_fill_events(db)
    reminders = send_pre_event_reminders(db)
    nudges    = send_post_event_nudges(db)
    db.close()
    print(f"[events_automation] done — filled={filled}, reminders={reminders}, nudges={nudges}")


if __name__ == "__main__":
    main()
