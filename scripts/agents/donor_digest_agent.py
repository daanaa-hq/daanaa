"""
Weekly donor digest agent.

Sends each signed-in donor a warm summary of their saved orgs once a week.
Idempotent — uses donor_digest_log to skip already-sent users this week.

Stewardship compliance:
  P1  — serves giving intent, not marketing
  P2  — aggregate counts only; no individual giving data exposed
  P8  — never mentions fund handling; donate link is a hand-off to the org
  P10 — no AI generation in this email; deterministic template

Cron: Sunday 18:00 (0 18 * * 0)
"""

import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.agents.base import BaseAgent
from scripts.admin.email_service import get_email_service, wallet_digest_email


class DonorDigestAgent(BaseAgent):
    name = "donor_digest"
    local_model = None  # no LLM needed — template-based

    def execute(self, **kwargs):
        svc = get_email_service()
        db = self.db()

        # Ensure required tables exist
        db.execute("""
            CREATE TABLE IF NOT EXISTS donor_users (
                firebase_uid  TEXT PRIMARY KEY,
                email         TEXT,
                display_name  TEXT,
                last_seen     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS org_wallet_saves (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                firebase_uid TEXT NOT NULL,
                ein          TEXT NOT NULL,
                saved_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(firebase_uid, ein)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS donor_digest_log (
                firebase_uid TEXT NOT NULL,
                sent_week    TEXT NOT NULL,
                sent_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (firebase_uid, sent_week)
            )
        """)
        db.commit()

        # Current ISO week label (e.g. "2026-W25")
        now = datetime.datetime.utcnow()
        week_label = now.strftime("%Y-W%W")

        # All users with at least 1 saved org and a known email
        users = db.execute("""
            SELECT DISTINCT u.firebase_uid, u.email, u.display_name
            FROM donor_users u
            JOIN org_wallet_saves s ON s.firebase_uid = u.firebase_uid
            WHERE u.email IS NOT NULL
              AND u.email != ''
              AND NOT EXISTS (
                SELECT 1 FROM donor_digest_log
                WHERE firebase_uid = u.firebase_uid AND sent_week = ?
              )
        """, (week_label,)).fetchall()

        self.log.info(f"Digest run {week_label}: {len(users)} users to notify")
        sent = skipped = errors = 0

        for user in users:
            uid = user["firebase_uid"]
            email = user["email"]
            display_name = user["display_name"] or ""

            try:
                # Fetch their saved EINs
                saves = db.execute(
                    "SELECT ein FROM org_wallet_saves WHERE firebase_uid=? ORDER BY saved_at DESC LIMIT 5",
                    (uid,),
                ).fetchall()
                if not saves:
                    skipped += 1
                    continue

                eins = [r["ein"] for r in saves]

                # Fetch org details for each EIN
                placeholders = ",".join("?" * len(eins))
                orgs_raw = db.execute(
                    f"SELECT EIN, organization_name, mission, donate_url "
                    f"FROM registry_enriched WHERE EIN IN ({placeholders})",
                    eins,
                ).fetchall()

                # Build org dicts indexed by EIN
                org_by_ein = {r["EIN"]: r for r in orgs_raw}
                orgs = []
                for ein in eins:
                    org = org_by_ein.get(ein)
                    if org:
                        orgs.append({
                            "ein": ein,
                            "name": org["organization_name"] or "Unknown Org",
                            "mission": org["mission"] or "",
                            "donate_url": org["donate_url"] or "",
                        })

                if not orgs:
                    skipped += 1
                    continue

                template = wallet_digest_email(display_name or None, orgs)
                if svc.send_template(email, template):
                    db.execute(
                        "INSERT OR IGNORE INTO donor_digest_log (firebase_uid, sent_week) VALUES (?, ?)",
                        (uid, week_label),
                    )
                    db.commit()
                    self.log_agent_decision(
                        "donor_digest",
                        {"firebase_uid": uid, "week": week_label, "org_count": len(orgs)},
                        f"digest sent to {email} with {len(orgs)} orgs",
                        evidence="user-saved org list from org_wallet_saves",
                    )
                    sent += 1
                else:
                    errors += 1

            except Exception as e:
                self.log.error(f"Digest error for {uid}: {e}")
                errors += 1

        self.log_job(
            processed=len(users),
            updated=sent,
            errors=errors,
            notes=f"week={week_label} sent={sent} skipped={skipped}",
        )
        return {"week": week_label, "sent": sent, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
    DonorDigestAgent().run()
