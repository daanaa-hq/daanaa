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


# ── Provider: Resend ──────────────────────────────────────────────────────────

def _send_via_resend(
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    html: str,
    plain_text: str,
) -> bool:
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html,
                "text": plain_text,
            },
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
) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
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

    def send(self, to_email: str, subject: str, html: str, plain_text: str) -> bool:
        if not to_email:
            logger.warning(f"No recipient email for: {subject}")
            return False

        if not self.enabled:
            logger.info(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            return True

        if self.resend_api_key:
            return _send_via_resend(
                self.resend_api_key, self.from_email,
                to_email, subject, html, plain_text,
            )

        return _send_via_smtp(
            self.smtp_host, self.smtp_port,
            self.smtp_user, self.smtp_password,
            self.from_email, to_email, subject, html, plain_text,
        )

    def send_template(self, to_email: str, template: EmailTemplate) -> bool:
        return self.send(to_email, template.subject, template.html, template.plain_text)


# ── Templates ─────────────────────────────────────────────────────────────────

def _base_html(title: str, accent: str, header_bg: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{{font-family:Arial,sans-serif;color:#333;line-height:1.6;margin:0;padding:0;background:#f5f5f5}}
    .wrap{{max-width:600px;margin:0 auto;padding:20px}}
    .hdr{{background:{header_bg};padding:24px 20px;border-radius:8px 8px 0 0}}
    .hdr h2{{margin:0;color:#1a2e3f;font-size:20px}}
    .body{{background:#fff;padding:24px 20px;border:1px solid #eee;border-radius:0 0 8px 8px}}
    .details{{background:#f9f9f9;padding:14px 16px;border-left:4px solid {accent};margin:16px 0;border-radius:0 4px 4px 0}}
    .btn{{display:inline-block;padding:12px 24px;background:{accent};color:#fff;text-decoration:none;border-radius:6px;margin:12px 0;font-weight:bold}}
    .foot{{text-align:center;margin-top:20px;color:#888;font-size:12px}}
    p{{margin:8px 0}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hdr"><h2>{title}</h2></div>
    <div class="body">
      {body}
      <div class="foot">
        <p>Daanaa — nonprofit discovery for donors who care<br>
        <a href="https://daanaa.org" style="color:{accent}">daanaa.org</a> · support@daanaa.org</p>
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
  3. Once entered, your dashboard unlocks — add your mission, website, and team

Questions? Reply to this email or reach us at support@daanaa.org.

— The Daanaa Team
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

Great news — your claim for {org_name} (EIN {ein}) has been verified.

Your nonprofit dashboard is ready:
{dashboard_url}

From your dashboard you can:
  - Update your mission statement and website
  - Add cause tags so donors can find you
  - Review your financial context score
  - Verify volunteer hours your supporters log

This link is private to you. Bookmark it or save your login details.

— The Daanaa Team
https://daanaa.org
"""
    body = f"""<p>Hi {rep_name},</p>
<p>Your claim for <strong>{org_name}</strong> has been verified — your nonprofit dashboard is ready.</p>
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

— The Daanaa Team
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

— The Daanaa Team
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


# ── Singleton ─────────────────────────────────────────────────────────────────

_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
