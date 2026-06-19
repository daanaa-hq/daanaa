"""
Nonprofit onboarding drip agent.

Runs nightly. For every verified nonprofit rep, sends the right email at the
right time based on how long they've been verified and how complete their
profile is. Zero humans required.

Drip sequence:
  Day 0  — "Page verified" (sent by claim/verify endpoint, not this agent)
  Day 1  — "Complete your profile" — profile completion score + what's missing
  Day 3  — "Donors are searching for orgs like yours" — only if profile < 60%
  Day 7  — "How top orgs stand out on Daanaa" — tips + hidden gems context
  Day 30 — "Your first monthly report" — how many donor views, wallet adds

State is persisted in nonprofit_onboarding_log to stay idempotent.
Running twice on the same day is safe.
"""

import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.agents.base import BaseAgent
from scripts.email_service import get_email_service, EmailTemplate


# ── Profile completeness ──────────────────────────────────────────────────────

def _profile_score(row) -> tuple[int, list[str]]:
    """Return (0-100 score, list of missing field labels) for a claimed org."""
    score = 0
    missing = []

    checks = [
        (row.get("mission") or row.get("custom_mission"), 30, "mission statement"),
        (row.get("website"), 20, "website link"),
        (row.get("cause_tags") and row["cause_tags"] != "[]", 20, "cause tags"),
        (row.get("donate_url"), 20, "donation link"),
        (row.get("street_address"), 10, "address"),
    ]
    for value, pts, label in checks:
        if value:
            score += pts
        else:
            missing.append(label)

    return score, missing


# ── Email templates ───────────────────────────────────────────────────────────

_GOLD = "#d4af37"
_NAVY = "#1a2e3f"
_LOGO_URL = "https://daanaa.org/logo.png"


def _base(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{{font-family:Georgia,'Times New Roman',serif;color:#1a2e3f;line-height:1.7;margin:0;padding:0;background:#f5f0e8}}
    .wrap{{max-width:600px;margin:0 auto;padding:24px 16px}}
    .brand{{background:#1a2e3f;padding:28px 20px 20px;border-radius:12px 12px 0 0;text-align:center}}
    .brand img{{width:64px;height:64px;display:block;margin:0 auto 10px}}
    .brand span{{display:block;font-family:Arial,sans-serif;font-size:22px;font-weight:700;letter-spacing:0.05em;color:#d4af37}}
    .title-bar{{background:#fef3c7;padding:14px 24px;border-left:4px solid {_GOLD}}}
    .title-bar h2{{margin:0;color:#1a2e3f;font-size:17px;font-weight:600;font-family:Arial,sans-serif}}
    .body{{background:#fff;padding:28px 24px;border:1px solid #e8e0d4;border-top:none;border-radius:0 0 12px 12px}}
    .box{{background:#f9f6f0;padding:14px 16px;border-left:4px solid {_GOLD};margin:16px 0;border-radius:0 6px 6px 0}}
    .box p{{margin:4px 0;font-size:14px}}
    .btn{{display:inline-block;padding:13px 28px;background:{_GOLD};color:#fff;text-decoration:none;border-radius:8px;margin:14px 0;font-weight:700;font-family:Arial,sans-serif;font-size:15px}}
    .bar{{height:12px;background:#eee;border-radius:6px;overflow:hidden;margin:8px 0}}
    .fill{{height:12px;background:{_GOLD};border-radius:6px}}
    .foot{{text-align:center;margin-top:28px;padding-top:16px;border-top:1px solid #ede8df;color:#888;font-size:12px;font-family:Arial,sans-serif}}
    p{{margin:10px 0}} ul,ol{{margin:8px 0 8px 20px}} li{{margin:5px 0}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <img src="{_LOGO_URL}" alt="Daanaa" width="64" height="64">
      <span>daanaa</span>
    </div>
    <div class="title-bar"><h2>{title}</h2></div>
    <div class="body">
      {body_html}
      <div class="foot">
        <p><a href="https://daanaa.org" style="color:#d4af37;text-decoration:none">daanaa.org</a>
        &nbsp;&middot;&nbsp; <a href="mailto:orgs@daanaa.org" style="color:#d4af37;text-decoration:none">orgs@daanaa.org</a></p>
        <p style="margin-top:8px">Nonprofit discovery for people who want to give thoughtfully.</p>
      </div>
    </div>
  </div>
</body>
</html>"""


def day1_profile_email(
    rep_name: str,
    org_name: str,
    ein: str,
    score: int,
    missing: list[str],
    dashboard_url: str,
) -> EmailTemplate:
    """Day 1: Complete your profile."""
    pct = min(score, 100)
    missing_html = "".join(f"<li>{m}</li>" for m in missing) if missing else "<li>Profile is complete!</li>"
    body = f"""<p>Hi {rep_name},</p>
<p>Your Daanaa page for <strong>{org_name}</strong> is live. Donors search for orgs like yours every day. A complete profile means they find you.</p>
<p><strong>Your profile is {pct}% complete.</strong></p>
<div class="bar"><div class="fill" style="width:{pct}%"></div></div>
{"<p>What's still missing:</p><ul>" + missing_html + "</ul>" if missing else ""}
<p>It takes about 5 minutes to fill in the rest from your dashboard:</p>
<a href="{dashboard_url}" class="btn">Complete Your Profile</a>
<div class="box">
  <p><strong>Why it matters:</strong> Donors use cause tags, mission text, and donation links to decide which orgs to support.
  Orgs with complete profiles appear in 3× more searches.</p>
</div>
<p>Questions? Reply to this email. Our nonprofit team at orgs@daanaa.org reads every message.</p>"""
    return EmailTemplate(
        subject=f"Your Daanaa profile is {pct}% complete. Here's what you can add.",
        html=_base(f"{org_name}: Profile {pct}% complete", body),
        plain_text=f"""Hi {rep_name},

Your Daanaa page for {org_name} is live and {pct}% complete.

{"Missing: " + ", ".join(missing) + "." if missing else "Profile is complete!"}

Complete it at: {dashboard_url}

Orgs with complete profiles appear in 3x more searches. It takes about 5 minutes.

Questions? Reply or email orgs@daanaa.org.

The Daanaa Team
""",
    )


def day3_nudge_email(
    rep_name: str,
    org_name: str,
    ein: str,
    score: int,
    dashboard_url: str,
) -> EmailTemplate:
    """Day 3: donors are searching for orgs like yours."""
    body = f"""<p>Hi {rep_name},</p>
<p>Donors searched for nonprofits in your category on Daanaa this week. Your profile for <strong>{org_name}</strong> is {score}% complete. A little more information could make the difference.</p>
<div class="box">
  <p><strong>The three things donors look for most:</strong></p>
  <ul>
    <li>A clear mission statement (what you do, who you serve)</li>
    <li>Cause tags (so you show up in the right searches)</li>
    <li>A donation link (so donors can give directly)</li>
  </ul>
</div>
<p>Each one takes under a minute to add:</p>
<a href="{dashboard_url}" class="btn">Update My Profile</a>
<p style="font-size:13px;color:#888">If you need help or have questions about your listing, reply to this email and our nonprofit team will help.</p>"""
    return EmailTemplate(
        subject=f"Donors are searching for orgs like {org_name}",
        html=_base("Donors are searching for orgs like yours", body),
        plain_text=f"""Hi {rep_name},

Donors searched for nonprofits in your category on Daanaa this week. Your profile for {org_name} is {score}% complete.

The three things donors look for most:
  - A clear mission statement
  - Cause tags
  - A donation link

Update your profile: {dashboard_url}

The Daanaa Team
""",
    )


def day7_tips_email(
    rep_name: str,
    org_name: str,
    ein: str,
    is_hidden_gem: bool,
    dashboard_url: str,
) -> EmailTemplate:
    """Day 7: how top orgs stand out."""
    gem_note = (
        "<div class=\"box\"><p><strong>You're a Hidden Gem.</strong> Daanaa has flagged "
        f"{org_name} as a high-performing, lesser-known org. Donors who filter for "
        "hidden gems specifically want to find orgs like you. Make sure your profile "
        "is complete so they can connect with you.</p></div>"
    ) if is_hidden_gem else ""
    body = f"""<p>Hi {rep_name},</p>
<p>It's been a week since {org_name} joined Daanaa. Here's what the orgs that donors engage with most have in common:</p>
<ul>
  <li><strong>Specific mission text:</strong> "We feed 1,200 families in South Dallas every week" lands better than "We serve the community"</li>
  <li><strong>Accurate cause tags:</strong> donors filter by cause, and your tags determine which searches you appear in</li>
  <li><strong>A live donation link:</strong> donors who are ready to give need a clear path forward</li>
  <li><strong>Financial health signal:</strong> your Daanaa score comes from IRS data and we show donors context, not a grade</li>
</ul>
{gem_note}
<p>You can update everything from your dashboard:</p>
<a href="{dashboard_url}" class="btn">Open My Dashboard</a>
<p>If you have questions about your score, your data, or anything on your page, reply here. We read every email from nonprofits.</p>"""
    return EmailTemplate(
        subject=f"Tips for standing out on Daanaa: {org_name}",
        html=_base("How the best-performing orgs stand out", body),
        plain_text=f"""Hi {rep_name},

It's been a week since {org_name} joined Daanaa. Here's what works:

- Specific mission text ("We feed 1,200 families in South Dallas every week")
- Accurate cause tags. Donors filter by cause.
- A live donation link. Donors who are ready to give need a clear path.
- Your financial health score comes from IRS data. Donors see context, not a grade.

{"You're flagged as a Hidden Gem. Donors who want lesser-known, high-performing orgs will find you." if is_hidden_gem else ""}

Open your dashboard: {dashboard_url}

The Daanaa Team
""",
    )


def day30_report_email(
    rep_name: str,
    org_name: str,
    ein: str,
    wallet_adds: int,
    volunteer_hours: int,
    profile_score: int,
    dashboard_url: str,
) -> EmailTemplate:
    """Day 30: first monthly impact report."""
    body = f"""<p>Hi {rep_name},</p>
<p>Here's your first monthly snapshot for <strong>{org_name}</strong> on Daanaa:</p>
<div class="box">
  <p><strong>Donors who saved your page:</strong> {wallet_adds} people added your org to their Daanaa Wallet</p>
  <p><strong>Volunteer hours logged:</strong> {volunteer_hours} hours by your community</p>
  <p><strong>Profile completeness:</strong> {profile_score}%</p>
</div>
{"<p>Your profile is complete. You're showing up in all the right searches.</p>" if profile_score >= 90 else f"<p>Your profile is {profile_score}% complete. A complete profile means more donors find you. <a href=\"{dashboard_url}\">Finish it here</a>.</p>"}
<p>Every month, Daanaa is seen by thousands of donors who want to give thoughtfully. Your page makes it possible for them to find you.</p>
<a href="{dashboard_url}" class="btn">View My Dashboard</a>
<p style="font-size:13px;color:#888">These numbers are from your page's activity since you joined. We don't share individual user data with nonprofits, only aggregate counts.</p>"""
    return EmailTemplate(
        subject=f"Your Daanaa monthly report: {org_name}",
        html=_base(f"{org_name}: Your First Month on Daanaa", body),
        plain_text=f"""Hi {rep_name},

Your first month on Daanaa:

  Donors who saved your page: {wallet_adds}
  Volunteer hours logged: {volunteer_hours}
  Profile completeness: {profile_score}%

{"Profile is complete. You're showing up in all the right searches." if profile_score >= 90 else f"Profile is {profile_score}% complete. Finish it here: {dashboard_url}"}

The Daanaa Team
""",
    )


# ── Agent ─────────────────────────────────────────────────────────────────────

class OnboardingAgent(BaseAgent):
    """
    Nightly nonprofit onboarding drip agent.
    Idempotent — safe to run multiple times per day.
    """

    name = "onboarding"
    local_model = "qwen2.5:7b"

    def _ensure_onboarding_log(self):
        self.db().execute("""
            CREATE TABLE IF NOT EXISTS nonprofit_onboarding_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ein        TEXT NOT NULL,
                step       TEXT NOT NULL,   -- day1 | day3 | day7 | day30
                sent_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ein, step)
            )
        """)
        self.db().commit()

    def _already_sent(self, ein: str, step: str) -> bool:
        row = self.db().execute(
            "SELECT 1 FROM nonprofit_onboarding_log WHERE ein=? AND step=?",
            (ein, step),
        ).fetchone()
        return row is not None

    def _mark_sent(self, ein: str, step: str):
        self.db().execute(
            "INSERT OR IGNORE INTO nonprofit_onboarding_log (ein, step) VALUES (?, ?)",
            (ein, step),
        )
        self.db().commit()

    def _get_org_data(self, ein: str) -> dict:
        row = self.db().execute("""
            SELECT r.organization_name, r.mission, r.website, r.cause_tags,
                   r.donate_url, r.street_address, r.is_hidden_gem,
                   c.rep_name, c.email, c.verified_at, c.custom_mission
            FROM org_claims c
            JOIN registry_enriched r ON c.ein = r.EIN
            WHERE c.ein = ?
              AND c.claim_status IN ('verified', 'active')
              AND c.revoked_at IS NULL
        """, (ein,)).fetchone()
        return dict(row) if row else {}

    def _get_wallet_adds(self, ein: str) -> int:
        """Count how many donors have this org in their wallet (aggregate only, P2)."""
        try:
            row = self.db().execute(
                "SELECT COUNT(*) AS n FROM org_wallet_saves WHERE ein=?", (ein,)
            ).fetchone()
            return int(row["n"]) if row else 0
        except Exception:
            return 0

    def _get_volunteer_hours(self, ein: str) -> int:
        row = self.db().execute(
            "SELECT COALESCE(SUM(hours), 0) AS total FROM volunteer_hours WHERE ein=? AND status='verified'",
            (ein,),
        ).fetchone()
        return int(row["total"]) if row else 0

    def execute(self, **kwargs):
        self._ensure_onboarding_log()
        svc = get_email_service()
        now = datetime.datetime.utcnow()

        # Fetch all verified nonprofit claims with their verified_at timestamp
        claims = self.db().execute("""
            SELECT c.ein, c.email, c.rep_name, c.verified_at
            FROM org_claims c
            WHERE c.claim_status IN ('verified', 'active')
              AND c.revoked_at IS NULL
              AND c.email IS NOT NULL
              AND c.email != ''
              AND c.verified_at IS NOT NULL
            ORDER BY c.verified_at DESC
        """).fetchall()

        self.log.info(f"Processing {len(claims)} verified claims for onboarding drip")
        sent = 0
        errors = 0

        for claim in claims:
            ein = claim["ein"]
            rep_email = claim["email"]
            rep_name = claim["rep_name"] or "there"
            verified_at_str = claim["verified_at"]

            try:
                verified_at = datetime.datetime.fromisoformat(verified_at_str.replace("Z", ""))
            except Exception:
                continue

            days_verified = (now - verified_at).days
            dashboard_url = f"https://daanaa.org/nonprofit/dashboard/{ein}"

            org = self._get_org_data(ein)
            if not org:
                continue

            org_name = org.get("organization_name", "your organization")
            score, missing = _profile_score(org)

            try:
                # Day 1: complete your profile
                if days_verified >= 1 and not self._already_sent(ein, "day1"):
                    template = day1_profile_email(rep_name, org_name, ein, score, missing, dashboard_url)
                    if svc.send_template(rep_email, template):
                        self._mark_sent(ein, "day1")
                        self.log_agent_decision(
                            "onboarding_email",
                            {"ein": ein, "step": "day1"},
                            f"day1 sent to {rep_email}",
                            evidence="verified nonprofit claim",
                        )
                        sent += 1
                    continue  # Only one email per run per org

                # Day 3: donors are searching (only if profile still incomplete)
                if days_verified >= 3 and score < 60 and not self._already_sent(ein, "day3"):
                    template = day3_nudge_email(rep_name, org_name, ein, score, dashboard_url)
                    if svc.send_template(rep_email, template):
                        self._mark_sent(ein, "day3")
                        self.log_agent_decision(
                            "onboarding_email",
                            {"ein": ein, "step": "day3", "score": score},
                            f"day3 nudge sent to {rep_email}",
                            evidence="profile incomplete after 3 days",
                        )
                        sent += 1
                    continue

                # Day 7: tips for standing out
                if days_verified >= 7 and not self._already_sent(ein, "day7"):
                    is_hidden_gem = bool(org.get("is_hidden_gem"))
                    template = day7_tips_email(rep_name, org_name, ein, is_hidden_gem, dashboard_url)
                    if svc.send_template(rep_email, template):
                        self._mark_sent(ein, "day7")
                        self.log_agent_decision(
                            "onboarding_email",
                            {"ein": ein, "step": "day7"},
                            f"day7 tips sent to {rep_email}",
                            evidence="verified claim, 7 days post-verification",
                        )
                        sent += 1
                    continue

                # Day 30: first monthly report
                if days_verified >= 30 and not self._already_sent(ein, "day30"):
                    wallet_adds = self._get_wallet_adds(ein)
                    vol_hours = self._get_volunteer_hours(ein)
                    template = day30_report_email(
                        rep_name, org_name, ein,
                        wallet_adds, vol_hours, score, dashboard_url,
                    )
                    if svc.send_template(rep_email, template):
                        self._mark_sent(ein, "day30")
                        self.log_agent_decision(
                            "onboarding_email",
                            {"ein": ein, "step": "day30", "wallet_adds": wallet_adds},
                            f"day30 report sent to {rep_email}",
                            evidence="30 days post-verification aggregate stats",
                        )
                        sent += 1

            except Exception as e:
                self.log.error(f"Onboarding error for {ein}: {e}")
                errors += 1

        self.log_job(processed=len(claims), updated=sent, errors=errors,
                     notes=f"drip: {sent} emails sent")
        return {"processed": len(claims), "sent": sent, "errors": errors}


if __name__ == "__main__":
    OnboardingAgent().run()
