"""
Email service for Daanaa transactional notifications.

Provider priority:
  1. Resend  — set RESEND_API_KEY env var; reliable delivery via daanaa.org domain
  2. SMTP    — fallback for local dev or if Resend key is absent
  3. Dry-run — EMAIL_ENABLED=false (default) logs intent without sending

Templates:
  - claim_received_email      — nonprofit just submitted a claim
  - claim_verified_email      — claim is approved, portal open
  - hours_verified_email      — volunteer hours confirmed by nonprofit
  - hours_rejected_email      — volunteer hours could not be confirmed
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class EmailTemplate:
    subject: str
    html: str
    plain_text: str


# ── Compliance layer (patterns learned from listmonk, task #22) ───────────────
# Deliverability is a burn-once asset: @daanaa.org never recovers from a spam
# blocklist. Every campaign send checks the suppression list and carries
# RFC 8058 one-click unsubscribe headers. Transactional mail (user-requested
# PINs/verification) skips marketing headers and ignores suppression.

import hashlib
import hmac as _hmac
import sqlite3 as _sqlite3
from pathlib import Path as _Path


def _db_path() -> str:
    return os.getenv("DAANAA_DB_PATH",
                     str(_Path.home() / "meritgiving/data/merit_registry.db"))


def _compliance_db():
    db = _sqlite3.connect(_db_path(), timeout=30)
    db.execute("""CREATE TABLE IF NOT EXISTS email_suppression (
        email TEXT PRIMARY KEY,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    return db


def unsubscribe_token(email: str) -> str:
    """HMAC token so one-click unsubscribe needs no login. Secret from env
    only (EMAIL_UNSUB_SECRET); empty secret disables token generation."""
    secret = os.getenv("EMAIL_UNSUB_SECRET", "")
    if not secret:
        return ""
    return _hmac.new(secret.encode(), email.lower().strip().encode(),
                     hashlib.sha256).hexdigest()[:32]


def verify_unsubscribe_token(email: str, token: str) -> bool:
    expected = unsubscribe_token(email)
    return bool(expected) and _hmac.compare_digest(expected, token or "")


def is_suppressed(email: str) -> bool:
    db = _compliance_db()
    try:
        return db.execute("SELECT 1 FROM email_suppression WHERE email = ?",
                          (email.lower().strip(),)).fetchone() is not None
    finally:
        db.close()


def suppress_email(email: str, reason: str = "unsubscribed") -> None:
    db = _compliance_db()
    try:
        db.execute("INSERT OR REPLACE INTO email_suppression (email, reason) "
                   "VALUES (?, ?)", (email.lower().strip(), reason))
        db.commit()
    finally:
        db.close()


def _unsubscribe_headers(to_email: str) -> dict:
    token = unsubscribe_token(to_email)
    if not token:
        return {}
    url = (f"https://daanaa.org/api/email/unsubscribe"
           f"?e={to_email.lower().strip()}&t={token}")
    return {
        "List-Unsubscribe": f"<{url}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


# ── Provider: Resend ──────────────────────────────────────────────────────────

def _send_via_resend(
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    html: str,
    plain_text: str,
    extra_headers: dict | None = None,
) -> bool:
    try:
        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html,
            "text": plain_text,
        }
        if extra_headers:
            payload["headers"] = extra_headers
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        if resp.status_code in (200, 201):
            logger.info(f"[Resend] sent to {to_email}: {subject}")
            return True
        logger.error(f"[Resend] HTTP {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"[Resend] request failed: {e}")
        return False


# ── Provider: SMTP ────────────────────────────────────────────────────────────

def _send_via_smtp(
    host: str,
    port: int,
    user: str,
    password: str,
    from_email: str,
    to_email: str,
    subject: str,
    html: str,
    plain_text: str,
    extra_headers: dict | None = None,
) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        for k, v in (extra_headers or {}).items():
            msg[k] = v
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(host, port) as server:
            if user and password:
                server.starttls()
                server.login(user, password)
            server.send_message(msg)
        logger.info(f"[SMTP] sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"[SMTP] failed sending to {to_email}: {e}")
        return False


# ── EmailService ──────────────────────────────────────────────────────────────

class EmailService:
    def __init__(self):
        self.resend_api_key = os.getenv("RESEND_API_KEY", "")
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "Daanaa <noreply@daanaa.org>")
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.firestore_base_url = os.getenv(
            "FIRESTORE_BASE_URL",
            "https://firestore.googleapis.com/v1/projects/daanaa-af9c2/databases/(default)/documents",
        )
        self.firestore_api_key = os.getenv("FIRESTORE_API_KEY", "")

    def _fetch_user_email(self, user_id: str) -> Optional[str]:
        if not self.firestore_api_key:
            return None
        try:
            url = f"{self.firestore_base_url}/{user_id}/profile/info?key={self.firestore_api_key}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                fields = response.json().get("fields", {})
                return fields.get("email", {}).get("stringValue", "")
            return None
        except Exception as e:
            logger.warning(f"Error fetching email for user {user_id}: {e}")
            return None

    def send(self, to_email: str, subject: str, html: str, plain_text: str,
             kind: str = "transactional") -> bool:
        """kind='campaign' → suppression list honored + RFC 8058 unsubscribe
        headers attached. kind='transactional' (default) → user-requested
        mail (PINs, verification): no marketing headers, suppression ignored
        because the recipient asked for this specific message."""
        if not to_email:
            logger.warning(f"No recipient email for: {subject}")
            return False

        extra_headers: dict = {}
        if kind == "campaign":
            if is_suppressed(to_email):
                logger.info(f"[SUPPRESSED] not sending campaign to {to_email}")
                return False
            extra_headers = _unsubscribe_headers(to_email)

        if not self.enabled:
            logger.info(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            return True

        if self.resend_api_key:
            return _send_via_resend(
                self.resend_api_key, self.from_email,
                to_email, subject, html, plain_text,
                extra_headers=extra_headers,
            )

        return _send_via_smtp(
            self.smtp_host, self.smtp_port,
            self.smtp_user, self.smtp_password,
            self.from_email, to_email, subject, html, plain_text,
            extra_headers=extra_headers,
        )

    def send_template(self, to_email: str, template: EmailTemplate) -> bool:
        return self.send(to_email, template.subject, template.html, template.plain_text)


# ── Templates ─────────────────────────────────────────────────────────────────

_LOGO_URL = "https://daanaa.org/logo.png"


def _base_html(title: str, accent: str, header_bg: str, body: str) -> str:
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
    .title-bar{{background:{header_bg};padding:14px 24px;border-left:4px solid {accent}}}
    .title-bar h2{{margin:0;color:#1a2e3f;font-size:17px;font-weight:600;font-family:Arial,sans-serif}}
    .body{{background:#fff;padding:28px 24px;border:1px solid #e8e0d4;border-top:none;border-radius:0 0 12px 12px}}
    .details{{background:#f9f6f0;padding:14px 16px;border-left:4px solid {accent};margin:16px 0;border-radius:0 6px 6px 0}}
    .details p{{margin:4px 0;font-size:14px}}
    .btn{{display:inline-block;padding:13px 28px;background:{accent};color:#fff;text-decoration:none;border-radius:8px;margin:14px 0;font-weight:700;font-family:Arial,sans-serif;font-size:15px}}
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
      {body}
      <div class="foot">
        <p><a href="https://daanaa.org" style="color:#d4af37;text-decoration:none">daanaa.org</a>
        &nbsp;&middot;&nbsp; support@daanaa.org</p>
        <p style="margin-top:8px">Nonprofit discovery for people who want to give thoughtfully.</p>
      </div>
    </div>
  </div>
</body>
</html>"""


def claim_received_email(
    org_name: str,
    rep_name: str,
    ein: str,
) -> EmailTemplate:
    """Sent immediately when a nonprofit submits a claim request."""
    subject = f"We received your claim for {org_name}"
    plain = f"""Hi {rep_name},

We received your request to claim the page for {org_name} (EIN {ein}) on Daanaa.

What happens next:
  1. We verify your connection to the organization (usually within 2 business days)
  2. You'll receive a verification letter with a one-time access code
  3. Once entered, your dashboard unlocks. Add your mission, website, and team

Questions? Reply to this email or reach us at support@daanaa.org.

The Daanaa Team
https://daanaa.org
"""
    body = f"""<p>Hi {rep_name},</p>
<p>We received your request to claim the page for <strong>{org_name}</strong> on Daanaa.</p>
<div class="details">
  <p><strong>EIN:</strong> {ein}</p>
  <p><strong>Status:</strong> Under review</p>
</div>
<p><strong>What happens next:</strong></p>
<ol>
  <li>We verify your connection to the organization (usually within 2 business days)</li>
  <li>You'll receive a verification letter with a one-time access code</li>
  <li>Once entered, your nonprofit dashboard unlocks</li>
</ol>
<p>Questions? Reply to this email or reach us at <a href="mailto:support@daanaa.org">support@daanaa.org</a>.</p>"""
    return EmailTemplate(
        subject=subject,
        html=_base_html("Claim received", "#f59e0b", "#fef3c7", body),
        plain_text=plain,
    )


def claim_verified_email(
    org_name: str,
    rep_name: str,
    ein: str,
    dashboard_url: str,
) -> EmailTemplate:
    """Sent when a claim is approved and the nonprofit dashboard is open."""
    subject = f"Your Daanaa page for {org_name} is verified"
    plain = f"""Hi {rep_name},

Your claim for {org_name} (EIN {ein}) has been verified. Your nonprofit dashboard is ready:
{dashboard_url}

From your dashboard you can:
  - Update your mission statement and website
  - Add cause tags so donors can find you
  - Review your financial context score
  - Verify volunteer hours your supporters log

This link is private to you. Bookmark it or save your login details.

The Daanaa Team
https://daanaa.org
"""
    body = f"""<p>Hi {rep_name},</p>
<p>Your claim for <strong>{org_name}</strong> has been verified. Your nonprofit dashboard is ready.</p>
<div class="details">
  <p><strong>EIN:</strong> {ein}</p>
  <p><strong>Status:</strong> Verified ✓</p>
</div>
<p>From your dashboard you can:</p>
<ul>
  <li>Update your mission statement and website</li>
  <li>Add cause tags so donors can find you</li>
  <li>Review your financial context score</li>
  <li>Verify volunteer hours your supporters log</li>
</ul>
<a href="{dashboard_url}" class="btn">Open Your Dashboard</a>
<p style="font-size:13px;color:#888">This link is private to you. Bookmark it or save your login details.</p>"""
    return EmailTemplate(
        subject=subject,
        html=_base_html("Page verified", "#22c55e", "#dcfce7", body),
        plain_text=plain,
    )


def hours_verified_email(
    volunteer_email: str,
    nonprofit_name: str,
    hours: float,
    service_date: str,
    notes: Optional[str] = None,
) -> EmailTemplate:
    subject = f"Your volunteer hours with {nonprofit_name} have been verified"
    plain = f"""Hello,

Good news! {nonprofit_name} verified your volunteer hours.

  Date: {service_date}
  Hours: {hours}
{f'  Notes: {notes}' if notes else ''}

View your full volunteer record at https://daanaa.org/wallet

Thank you for your service!

The Daanaa Team
"""
    body = f"""<p>Hello,</p>
<p>Good news! <strong>{nonprofit_name}</strong> verified your volunteer hours.</p>
<div class="details">
  <p><strong>Date:</strong> {service_date}</p>
  <p><strong>Hours:</strong> {hours}</p>
  {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
</div>
<p>View your full volunteer record in your Daanaa Wallet:</p>
<a href="https://daanaa.org/wallet" class="btn">View Your Wallet</a>
<p>Thank you for your service!</p>"""
    return EmailTemplate(
        subject=subject,
        html=_base_html("Hours verified", "#d4af37", "#f5e6d3", body),
        plain_text=plain,
    )


def hours_rejected_email(
    volunteer_email: str,
    nonprofit_name: str,
    hours: float,
    service_date: str,
    rejection_reason: Optional[str] = None,
) -> EmailTemplate:
    subject = f"Your volunteer hours with {nonprofit_name} could not be verified"
    plain = f"""Hello,

{nonprofit_name} was unable to verify your volunteer hours.

  Date: {service_date}
  Hours: {hours}
{f'  Reason: {rejection_reason}' if rejection_reason else ''}

If you believe this is an error, contact the nonprofit directly or email support@daanaa.org.

View your wallet at https://daanaa.org/wallet

The Daanaa Team
"""
    body = f"""<p>Hello,</p>
<p><strong>{nonprofit_name}</strong> was unable to verify your volunteer hours.</p>
<div class="details">
  <p><strong>Date:</strong> {service_date}</p>
  <p><strong>Hours:</strong> {hours}</p>
  {f'<p><strong>Reason:</strong> {rejection_reason}</p>' if rejection_reason else ''}
</div>
<p>If you believe this is an error, contact the nonprofit or email
<a href="mailto:support@daanaa.org">support@daanaa.org</a>.</p>
<a href="https://daanaa.org/wallet" class="btn">View Your Wallet</a>"""
    return EmailTemplate(
        subject=subject,
        html=_base_html("Hours could not be verified", "#f59e0b", "#fef3c7", body),
        plain_text=plain,
    )


def wallet_digest_email(
    display_name: Optional[str],
    orgs: list[dict],
) -> EmailTemplate:
    """Weekly digest for donors: a warm summary of their saved orgs.

    Each org dict should have: name, ein, mission (optional), donate_url (optional).
    Max 5 orgs shown. Stewardship: never used for marketing, always serves giving intent.
    """
    first = display_name.split()[0] if display_name else None
    greet = f"Hi {first}," if first else "Hi,"
    n = len(orgs)
    count_line = f"You have {n} {'organization' if n == 1 else 'organizations'} in your Daanaa wallet."

    org_cards_html = ""
    org_lines_plain = ""
    for org in orgs[:5]:
        name = org.get("name", "Unknown Organization")
        ein = org.get("ein", "")
        mission = org.get("mission") or ""
        donate_url = org.get("donate_url") or ""
        org_url = f"https://daanaa.org/org/{ein}"
        donate_html = (
            f'<p style="margin:6px 0"><a href="{donate_url}" style="color:#d4af37;font-weight:700">Give now</a>'
            f' &nbsp;&middot;&nbsp; <a href="{org_url}" style="color:#888">View page</a></p>'
            if donate_url else
            f'<p style="margin:6px 0"><a href="{org_url}" style="color:#d4af37">View page</a></p>'
        )
        org_cards_html += f"""
<div style="padding:14px 16px;border-left:4px solid #d4af37;background:#f9f6f0;margin:14px 0;border-radius:0 6px 6px 0">
  <p style="margin:0 0 4px;font-weight:700;font-size:15px">{name}</p>
  {f'<p style="margin:4px 0;font-size:13px;color:#555">{mission[:160]}{"..." if len(mission) > 160 else ""}</p>' if mission else ''}
  {donate_html}
</div>"""
        org_lines_plain += f"\n  {name}"
        if donate_url:
            org_lines_plain += f"\n  Give: {donate_url}"
        org_lines_plain += f"\n  Page: {org_url}\n"

    body = f"""<p>{greet}</p>
<p>{count_line} Here's a quick look at each one so you can act when you're ready.</p>
{org_cards_html}
<p style="margin-top:20px"><a href="https://daanaa.org/wallet" style="color:#d4af37;font-weight:700">Open your full wallet</a></p>
<p style="font-size:12px;color:#888;margin-top:16px">You're getting this because you saved these orgs to your Daanaa wallet.
<a href="https://daanaa.org/wallet" style="color:#888">Manage your wallet</a> to add or remove orgs at any time.</p>"""

    plain = f"""{greet}

{count_line} Here's a quick look:
{org_lines_plain}
Open your wallet: https://daanaa.org/wallet

The Daanaa Team
"""
    return EmailTemplate(
        subject=f"Your Daanaa wallet: {n} {'org' if n == 1 else 'orgs'} you've saved",
        html=_base_html("Your giving wallet", "#d4af37", "#f5e6d3", body),
        plain_text=plain,
    )


def grant_opportunity_email(
    rep_name: Optional[str],
    org_name: str,
    grants: list[dict],
) -> EmailTemplate:
    """Weekly grant alert for verified nonprofit reps.

    Each grant dict should have: title, agency, close_date, url (optional), cfda (optional).
    Max 5 grants shown. Stewardship: P1 (giving intent), P3 (public data only),
    P10 (no LLM inference on this email, deterministic template).
    """
    first = rep_name.split()[0] if rep_name else None
    greet = f"Hi {first}," if first else "Hi,"
    n = len(grants)
    count_line = (
        f"We found {n} federal grant {'opportunity' if n == 1 else 'opportunities'} "
        f"that may be a fit for {org_name}."
    )

    grant_cards_html = ""
    grant_lines_plain = ""
    for g in grants[:5]:
        title = g.get("title", "Untitled Grant")
        agency = g.get("agency", "")
        close_date = g.get("close_date", "")
        url = g.get("url") or ""
        cfda = g.get("cfda", "")
        deadline_html = (
            f'<span style="color:#c0392b;font-weight:700">Closes {close_date}</span>'
            if close_date else ""
        )
        cfda_html = (
            f'<span style="font-size:11px;color:#888;margin-left:8px">CFDA {cfda}</span>'
            if cfda else ""
        )
        link_html = (
            f'<p style="margin:6px 0"><a href="{url}" style="color:#d4af37;font-weight:700">'
            f'View on Grants.gov</a></p>'
            if url else
            '<p style="margin:6px 0;font-size:12px;color:#888">Search Grants.gov for details</p>'
        )
        grant_cards_html += f"""
<div style="padding:14px 16px;border-left:4px solid #4a90d9;background:#f0f5fb;margin:14px 0;border-radius:0 6px 6px 0">
  <p style="margin:0 0 4px;font-weight:700;font-size:15px">{title}</p>
  <p style="margin:4px 0;font-size:13px;color:#555">{agency}{cfda_html}</p>
  {f'<p style="margin:4px 0;font-size:13px">{deadline_html}</p>' if deadline_html else ''}
  {link_html}
</div>"""
        grant_lines_plain += f"\n  {title}"
        if agency:
            grant_lines_plain += f"\n  {agency}"
        if close_date:
            grant_lines_plain += f"\n  Closes: {close_date}"
        if url:
            grant_lines_plain += f"\n  {url}"
        grant_lines_plain += "\n"

    body = f"""<p>{greet}</p>
<p>{count_line} These come from Grants.gov, the official federal grants database. Each one lists nonprofits as eligible recipients.</p>
{grant_cards_html}
<p style="margin-top:20px;font-size:13px;color:#555">Grant opportunities change quickly. Review each one and confirm your organization meets the eligibility requirements before applying.</p>
<p style="margin-top:16px"><a href="https://grants.gov/search-grants?eligibilities=25&oppStatuses=posted" style="color:#d4af37;font-weight:700">Browse all open grants on Grants.gov</a></p>
<p style="font-size:12px;color:#888;margin-top:16px">You're receiving this because {org_name} has a verified profile on Daanaa.
<a href="https://daanaa.org/nonprofit/dashboard" style="color:#888">Manage your profile</a> at any time.</p>"""

    plain = f"""{greet}

{count_line}

These come from Grants.gov, the official federal grants database.
{grant_lines_plain}
Browse all open grants: https://grants.gov/search-grants?eligibilities=25&oppStatuses=posted

Review each opportunity carefully and confirm your organization meets eligibility requirements before applying.

The Daanaa Team
"""
    return EmailTemplate(
        subject=f"Grant alert: {n} {'opportunity' if n == 1 else 'opportunities'} for {org_name}",
        html=_base_html("Grant opportunities", "#4a90d9", "#eef4fb", body),
        plain_text=plain,
    )


def nonprofit_signup_email(
    nonprofit_name: str,
    nonprofit_email: str,
    magic_link: str,
) -> EmailTemplate:
    """Nonprofit ED signup confirmation with magic link."""
    body = f"""
<p>Thank you for registering <strong>{nonprofit_name}</strong> with Daanaa.</p>

<p>To verify your email and unlock your dashboard, click the link below:</p>

<p style="text-align: center; margin: 20px 0;">
  <a href="{magic_link}" style="background-color: #4a90d9; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
    Verify Email & Access Dashboard
  </a>
</p>

<p style="font-size: 0.9em; color: #666;">
  Or copy this link: <code>{magic_link}</code>
</p>

<p>This link expires in 24 hours.</p>

<p>From your dashboard, you can:<br>
• Approve donation letters for your donors<br>
• Generate tax-compliant receipt PDFs<br>
• Manage your letter generation credits</p>

<p>Questions? Reply to this email or contact us at support@daanaa.org</p>

<p>The Daanaa Team</p>
"""
    plain = f"""Thank you for registering {nonprofit_name} with Daanaa.

To verify your email and unlock your dashboard, visit:
{magic_link}

This link expires in 24 hours.

From your dashboard, you can:
• Approve donation letters for your donors
• Generate tax-compliant receipt PDFs
• Manage your letter generation credits

Questions? Contact us at support@daanaa.org

The Daanaa Team"""

    return EmailTemplate(
        subject=f"Verify your {nonprofit_name} Daanaa account",
        html=_base_html("Verify your account", "#4a90d9", "#eef4fb", body),
        plain_text=plain,
    )


# ── Singleton ─────────────────────────────────────────────────────────────────

_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
