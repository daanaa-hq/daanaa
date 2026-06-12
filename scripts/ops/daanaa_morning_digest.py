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
    db.close()

    if not to_call and not expiring:
        print("nothing to report, no digest sent")
        return

    lines = [f"Good morning. Here is what needs you today ({datetime.now():%A, %B %d}).", ""]
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
    lines.append("Open the queue: http://192.168.1.73:5000/admin")
    sent = send_ops_email("orgs@daanaa.org", f"[Daanaa today] {len(to_call)} to call, {len(expiring)} expiring",
                          "\n".join(lines), from_addr="Daanaa Ops <orgs@daanaa.org>")
    print(f"digest sent: {sent}")


if __name__ == "__main__":
    main()
