"""Email notifications for volunteer hours system."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@daanaa.org")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")
SENDER_NAME = "Daanaa Volunteer Hours"

ENABLE_EMAIL = os.environ.get("ENABLE_EMAIL", "true").lower() == "true"


def send_email(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
    """
    Send an email notification.
    Returns True if sent successfully, False otherwise.
    """
    if not ENABLE_EMAIL:
        logger.info(f"Email disabled. Would send: {subject} to {to_email}")
        return True

    if not SENDER_PASSWORD:
        logger.warning("SENDER_PASSWORD not configured, skipping email")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = to_email

        # Attach plain text version
        text_part = MIMEText(text_body or subject, "plain")
        msg.attach(text_part)

        # Attach HTML version
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_volunteer_registration_confirmation(
    volunteer_name: str,
    volunteer_email: str,
    event_name: str,
    event_date: str,
    event_url: str
) -> bool:
    """Send confirmation when volunteer registers for event."""

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1a472a;">Thank you for volunteering, {volunteer_name}!</h2>

                <p>You're registered for:</p>
                <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #d4af37;">
                    <p><strong>{event_name}</strong></p>
                    <p>📅 {event_date}</p>
                </div>

                <p style="margin-top: 20px;">On the day of the event, you can log your volunteer hours by:</p>
                <ol>
                    <li>Scanning the QR code at the event, OR</li>
                    <li>Visiting: <a href="{event_url}" style="color: #d4af37;">{event_url}</a></li>
                </ol>

                <p style="margin-top: 20px; color: #666; font-size: 12px;">
                    The organizer will review and approve your hours. You'll receive an email confirmation when approved.
                </p>

                <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 11px;">
                    Daanaa Volunteer Hours System<br>
                    https://daanaa.org
                </p>
            </div>
        </body>
    </html>
    """

    subject = f"Registration Confirmed: {event_name}"
    return send_email(volunteer_email, subject, html_body)


def send_hours_logged_notification(
    organizer_email: str,
    organizer_name: str,
    volunteer_name: str,
    hours: float,
    event_name: str,
    event_url: str
) -> bool:
    """Notify organizer when volunteer logs hours."""

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1a472a;">New Hours Submission - {event_name}</h2>

                <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #d4af37;">
                    <p><strong>{volunteer_name}</strong> logged <strong>{hours} hours</strong></p>
                </div>

                <p style="margin-top: 20px;">
                    <a href="{event_url}" style="background: #d4af37; color: #1a472a; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Review & Approve Hours
                    </a>
                </p>

                <p style="margin-top: 20px; color: #666; font-size: 12px;">
                    This submission is pending your approval.
                </p>

                <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 11px;">
                    Daanaa Volunteer Hours System<br>
                    https://daanaa.org
                </p>
            </div>
        </body>
    </html>
    """

    subject = f"New Hours Submission: {volunteer_name} ({hours} hours)"
    return send_email(organizer_email, subject, html_body)


def send_hours_approved_notification(
    volunteer_email: str,
    volunteer_name: str,
    hours: float,
    event_name: str
) -> bool:
    """Notify volunteer when hours are approved."""

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1a472a;">✅ Your Hours Have Been Approved!</h2>

                <div style="background: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50;">
                    <p><strong>{hours} hours</strong> approved for <strong>{event_name}</strong></p>
                </div>

                <p style="margin-top: 20px;">
                    Thank you for your service! Your contribution has been recorded.
                </p>

                <p style="margin-top: 20px;">
                    <a href="https://daanaa.org/volunteer/search" style="background: #d4af37; color: #1a472a; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Explore More Events
                    </a>
                </p>

                <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 11px;">
                    Daanaa Volunteer Hours System<br>
                    https://daanaa.org
                </p>
            </div>
        </body>
    </html>
    """

    subject = f"✅ Hours Approved: {hours} hours for {event_name}"
    return send_email(volunteer_email, subject, html_body)


def send_bulk_import_confirmation(
    organizer_email: str,
    event_name: str,
    volunteer_count: int,
    event_url: str
) -> bool:
    """Notify organizer after bulk volunteer import."""

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1a472a;">✅ Volunteers Imported Successfully</h2>

                <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #d4af37;">
                    <p><strong>{volunteer_count} volunteers</strong> imported for <strong>{event_name}</strong></p>
                </div>

                <p style="margin-top: 20px;">
                    They can now:
                </p>
                <ul>
                    <li>Register online</li>
                    <li>Scan QR code to log hours</li>
                    <li>Submit hours for your approval</li>
                </ul>

                <p style="margin-top: 20px;">
                    <a href="{event_url}" style="background: #d4af37; color: #1a472a; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        View Event Dashboard
                    </a>
                </p>

                <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 11px;">
                    Daanaa Volunteer Hours System<br>
                    https://daanaa.org
                </p>
            </div>
        </body>
    </html>
    """

    subject = f"✅ {volunteer_count} Volunteers Imported for {event_name}"
    return send_email(organizer_email, subject, html_body)
