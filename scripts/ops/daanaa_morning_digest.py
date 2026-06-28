#!/usr/bin/env python3
"""Morning digest — cron 07:25 daily, lands before the founder's coffee.

Reads the same buckets as the admin Today queue straight from the DB and
emails orgs@daanaa.org the worklist. Silent when there's nothing to do —
an empty digest trains people to ignore digests.
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailer import send_ops_email

DB = Path.home() / "meritgiving/data/merit_registry.db"


def _events_summary(db):
    """Return (today_events, need_verification, upcoming_week) — empty lists if table missing."""
    try:
        today = db.execute("""
            SELECT ve.id, ve.title, ve.start_time, ve.is_virtual,
                   ve.location_city, ve.location_state,
                   r.organization_name,
                   COALESCE(SUM(s.total_count), 0) AS signups
            FROM volunteer_events ve
            LEFT JOIN registry_enriched r ON r.EIN = ve.ein
            LEFT JOIN org_signups s ON s.event_id = ve.id AND s.status = 'confirmed'
            WHERE ve.event_date = date('now') AND ve.status IN ('active', 'filled')
            GROUP BY ve.id
            ORDER BY ve.start_time""").fetchall()

        need_verification = db.execute("""
            SELECT ve.id, ve.title, ve.event_date, r.organization_name,
                   COUNT(s.id) AS unverified
            FROM volunteer_events ve
            LEFT JOIN registry_enriched r ON r.EIN = ve.ein
            LEFT JOIN org_signups s ON s.event_id = ve.id AND s.status = 'confirmed'
            WHERE ve.event_date BETWEEN date('now', '-14 days') AND date('now', '-1 day')
              AND ve.post_nudge_sent_at IS NOT NULL
            GROUP BY ve.id
            HAVING unverified > 0
            ORDER BY ve.event_date DESC""").fetchall()

        upcoming = db.execute("""
            SELECT ve.id, ve.title, ve.event_date, r.organization_name,
                   COALESCE(SUM(s.total_count), 0) AS signups,
                   ve.capacity
            FROM volunteer_events ve
            LEFT JOIN registry_enriched r ON r.EIN = ve.ein
            LEFT JOIN org_signups s ON s.event_id = ve.id AND s.status = 'confirmed'
            WHERE ve.event_date > date('now')
              AND ve.event_date <= date('now', '+7 days')
              AND ve.status IN ('active', 'filled')
            GROUP BY ve.id
            ORDER BY ve.event_date, ve.start_time""").fetchall()

        return today, need_verification, upcoming
    except sqlite3.OperationalError:
        return [], [], []


def main():
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    to_call = db.execute("""
        SELECT c.ein, c.rep_name, c.rep_title, c.phone, r.organization_name,
               CAST(julianday('now') - julianday(c.created_at) AS INTEGER) AS days
        FROM org_claims c LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status='pending' AND c.called_at IS NULL
        ORDER BY c.created_at""").fetchall()
    expiring = db.execute("""
        SELECT c.ein, c.email, r.organization_name,
               CAST(julianday(c.pin_expires_at) - julianday('now') AS INTEGER) AS days_left
        FROM org_claims c LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status='pending' AND c.called_at IS NOT NULL
          AND datetime(c.pin_expires_at) < datetime('now', '+7 days')
        ORDER BY c.pin_expires_at""").fetchall()
    new_claims = db.execute("""
        SELECT c.ein, c.rep_name, r.organization_name
        FROM org_claims c LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.created_at > datetime('now', '-1 day')
        ORDER BY c.created_at DESC""").fetchall()
    new_verified = db.execute("""
        SELECT c.ein, c.rep_name, r.organization_name
        FROM org_claims c LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status = 'verified'
          AND c.verified_at > datetime('now', '-1 day')
        ORDER BY c.verified_at DESC""").fetchall()
    pending_partners = db.execute("""
        SELECT id, business_name, category, submitter_name, created_at
        FROM community_partners WHERE is_active=0
        ORDER BY created_at DESC LIMIT 20""").fetchall()
    today_events, need_verification, upcoming_events = _events_summary(db)
    db.close()

    all_empty = (not to_call and not expiring and not new_claims and not new_verified
                 and not pending_partners and not today_events and not need_verification
                 and not upcoming_events)
    if all_empty:
        print("nothing to report, no digest sent")
        return

    lines = [f"Good morning. Here is what needs you today ({datetime.now():%A, %B %d}).", ""]

    if today_events:
        lines.append(f"Events happening today ({len(today_events)}):")
        for ev in today_events:
            where = "Virtual" if ev["is_virtual"] else ", ".join(
                filter(None, [ev["location_city"], ev["location_state"]])) or "TBD"
            time_s = ""
            if ev["start_time"]:
                h, m = map(int, ev["start_time"].split(":"))
                time_s = f" at {h % 12 or 12}:{m:02d} {'pm' if h >= 12 else 'am'}"
            lines.append(f"  ▸ {ev['title']} — {ev['organization_name'] or 'unclaimed'}"
                         f"{time_s} ({where}, {ev['signups']} signed up)"
                         f" https://daanaa.org/events/{ev['id']}")
        lines.append("")

    if need_verification:
        lines.append(f"Past events with unverified volunteer hours ({len(need_verification)}):")
        for ev in need_verification:
            lines.append(f"  ! {ev['title']} — {ev['organization_name'] or 'unclaimed'}"
                         f" ({ev['event_date']}, {ev['unverified']} unverified)"
                         f" https://daanaa.org/nonprofit/dashboard/{ev['id']}")
        lines.append("")

    if upcoming_events:
        lines.append(f"Events this week ({len(upcoming_events)}):")
        for ev in upcoming_events:
            cap = f"/{ev['capacity']}" if ev["capacity"] else ""
            lines.append(f"  · {ev['event_date']} {ev['title']} — {ev['organization_name'] or 'unclaimed'}"
                         f" ({ev['signups']}{cap} signed up)")
        lines.append("")

    if to_call:
        lines.append(f"Verification calls to make ({len(to_call)}):")
        for r in to_call:
            lines.append(f"  - {r['rep_name'] or 'Contact'} ({r['rep_title'] or 'role unknown'}), "
                         f"{r['organization_name'] or r['ein']}, {r['phone'] or 'no phone'}"
                         f" — waiting {r['days']}d")
        lines.append("")
    if expiring:
        lines.append(f"PINs expiring within 7 days, still unused ({len(expiring)}):")
        for r in expiring:
            lines.append(f"  - {r['organization_name'] or r['ein']} ({r['email']}) — {r['days_left']}d left")
        lines.append("")
    if new_claims:
        lines.append(f"New claims in the last 24h ({len(new_claims)}):")
        for r in new_claims:
            lines.append(f"  + {r['organization_name'] or r['ein']} ({r['rep_name'] or 'unknown rep'})")
        lines.append("")
    if new_verified:
        lines.append(f"Newly verified in the last 24h ({len(new_verified)}):")
        for r in new_verified:
            lines.append(f"  ✓ {r['organization_name'] or r['ein']} ({r['rep_name'] or 'unknown rep'})")
        lines.append("")
    if pending_partners:
        lines.append(f"Partner applications awaiting review ({len(pending_partners)}):")
        for r in pending_partners:
            lines.append(f"  ? {r['business_name']} ({r['category']}) — {r['submitter_name']}")
        lines.append("")
    lines.append("Open the queue: http://192.168.1.73:5000/admin")
    subject = (f"[Daanaa today] {len(to_call)} to call, {len(expiring)} expiring"
               + (f", {len(today_events)} events today" if today_events else "")
               + (f", {len(need_verification)} need verification" if need_verification else "")
               + (f", {len(new_claims)} new claims" if new_claims else "")
               + (f", {len(new_verified)} verified" if new_verified else "")
               + (f", {len(pending_partners)} partner apps" if pending_partners else ""))
    sent = send_ops_email("orgs@daanaa.org", subject,
                          "\n".join(lines), from_addr="Daanaa Ops <orgs@daanaa.org>")
    print(f"digest sent: {sent}")


if __name__ == "__main__":
    main()
