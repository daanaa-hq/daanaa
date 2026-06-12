#!/usr/bin/env python3
"""PIN expiry nudge — cron 10:00 daily.

An org that took the verification call but hasn't used its PIN gets ONE
friendly transactional reminder when 7 days remain. Service, not marketing:
sent once ever (tracked as a reminder_sent event in org_activity), only to
orgs we already spoke with, from verify@daanaa.org.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailer import send_ops_email

DB = Path.home() / "meritgiving/data/merit_registry.db"


def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    rows = db.execute("""
        SELECT c.ein, c.email, c.rep_name, r.organization_name,
               CAST(julianday(c.pin_expires_at) - julianday('now') AS INTEGER) AS days_left
        FROM org_claims c LEFT JOIN registry_enriched r ON r.EIN = c.ein
        WHERE c.claim_status = 'pending'
          AND c.called_at IS NOT NULL
          AND datetime(c.pin_expires_at) BETWEEN datetime('now') AND datetime('now', '+7 days')
          AND NOT EXISTS (SELECT 1 FROM org_activity a
                          WHERE a.ein = c.ein AND a.event_type = 'reminder_sent')
    """).fetchall()

    for r in rows:
        first = (r["rep_name"] or "").split(" ")[0]
        org = r["organization_name"] or "your organization"
        body = (
            f"Hello{' ' + first if first else ''},\n\n"
            f"A quick reminder from Daanaa. The PIN we gave you on our call for "
            f"{org} is still waiting, and it stays good for about {r['days_left']} more days.\n\n"
            f"Enter it here to open your page for editing:\n"
            f"https://daanaa.org/claim/verify?ein={r['ein']}\n\n"
            f"If the PIN slips past its date, no harm done. Reply to this email "
            f"and we will set you up with a fresh one.\n\n"
            f"Warmly,\nThe Daanaa team\nverify@daanaa.org · daanaa.org\n"
        )
        if send_ops_email(r["email"], f"Your Daanaa PIN for {org} is still waiting",
                          body, from_addr="Daanaa <verify@daanaa.org>"):
            db.execute(
                "INSERT INTO org_activity (ein, event_type, detail, actor) "
                "VALUES (?, 'reminder_sent', ?, 'system')",
                (r["ein"], f"PIN expiry nudge to {r['email']}, {r['days_left']}d left"))
            db.commit()
            print(f"nudged {r['ein']} ({r['email']})")
    if not rows:
        print("no nudges due")
    db.close()


if __name__ == "__main__":
    main()
