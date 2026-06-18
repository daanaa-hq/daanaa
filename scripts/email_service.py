"""Email service for sending notifications."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional

@dataclass
class EmailTemplate:
    """Email template structure."""
    subject: str
    html: str
    plain_text: str

class EmailService:
    """Simple email service using SMTP."""

    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'localhost')
        self.smtp_port = int(os.getenv('SMTP_PORT', '1025'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@daanaa.org')
        self.enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'

    def send(self, to_email: str, subject: str, html: str, plain_text: str) -> bool:
        """Send an email."""
        if not self.enabled:
            print(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            return True

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            msg.attach(MIMEText(plain_text, 'plain'))
            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return False

def hours_verified_email(
    volunteer_email: str,
    nonprofit_name: str,
    hours: float,
    service_date: str,
    notes: Optional[str] = None,
) -> EmailTemplate:
    """Generate email for verified volunteer hours."""

    plain_text = f"""
Hello,

Good news! {nonprofit_name} has verified your volunteer hours.

Details:
- Date: {service_date}
- Hours: {hours}
{f"- Notes: {notes}" if notes else ""}

You can view this and other volunteer hours in your Daanaa Impact Wallet:
https://daanaa.org/wallet

Your volunteer record helps us understand community impact. Thank you for your service!

Best regards,
The Daanaa Team
https://daanaa.org
"""

    html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f5e6d3; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .content {{ background-color: #fff; padding: 20px; border: 1px solid #eee; border-radius: 8px; }}
        .details {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #d4af37; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #d4af37; color: #fff; text-decoration: none; border-radius: 6px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0; color: #1a2e3f;">Hours Verified!</h2>
        </div>

        <div class="content">
            <p>Hello,</p>
            <p>Good news! <strong>{nonprofit_name}</strong> has verified your volunteer hours.</p>

            <div class="details">
                <p><strong>Date:</strong> {service_date}</p>
                <p><strong>Hours:</strong> {hours}</p>
                {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
            </div>

            <p>You can view this and other volunteer hours in your Daanaa Impact Wallet:</p>
            <a href="https://daanaa.org/wallet" class="button">View Your Wallet</a>

            <p>Your volunteer record helps us understand community impact. Thank you for your service!</p>

            <div class="footer">
                <p>Best regards,<br>The Daanaa Team<br><a href="https://daanaa.org">daanaa.org</a></p>
            </div>
        </div>
    </div>
</body>
</html>
"""

    return EmailTemplate(
        subject=f"✓ Your volunteer hours with {nonprofit_name} have been verified",
        html=html,
        plain_text=plain_text
    )

def hours_rejected_email(
    volunteer_email: str,
    nonprofit_name: str,
    hours: float,
    service_date: str,
    rejection_reason: Optional[str] = None,
) -> EmailTemplate:
    """Generate email for rejected volunteer hours."""

    plain_text = f"""
Hello,

We wanted to let you know that {nonprofit_name} could not verify your volunteer hours.

Details:
- Date: {service_date}
- Hours: {hours}
{f"- Reason: {rejection_reason}" if rejection_reason else ""}

You can view this and contact the nonprofit through your Daanaa Impact Wallet:
https://daanaa.org/wallet

If you believe this was an error, please reach out to the nonprofit directly or contact us at daanaa.org.

Best regards,
The Daanaa Team
https://daanaa.org
"""

    html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #fef3c7; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .content {{ background-color: #fff; padding: 20px; border: 1px solid #eee; border-radius: 8px; }}
        .details {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #f59e0b; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #f59e0b; color: #fff; text-decoration: none; border-radius: 6px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0; color: #1a2e3f;">Hours Could Not Be Verified</h2>
        </div>

        <div class="content">
            <p>Hello,</p>
            <p>We wanted to let you know that <strong>{nonprofit_name}</strong> could not verify your volunteer hours.</p>

            <div class="details">
                <p><strong>Date:</strong> {service_date}</p>
                <p><strong>Hours:</strong> {hours}</p>
                {f'<p><strong>Reason:</strong> {rejection_reason}</p>' if rejection_reason else ''}
            </div>

            <p>You can view this and contact the nonprofit through your Daanaa Impact Wallet:</p>
            <a href="https://daanaa.org/wallet" class="button">View Your Wallet</a>

            <p>If you believe this was an error, please reach out to the nonprofit directly or contact us.</p>

            <div class="footer">
                <p>Best regards,<br>The Daanaa Team<br><a href="https://daanaa.org">daanaa.org</a></p>
            </div>
        </div>
    </div>
</body>
</html>
"""

    return EmailTemplate(
        subject=f"Your volunteer hours with {nonprofit_name} could not be verified",
        html=html,
        plain_text=plain_text
    )

# Global email service instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
