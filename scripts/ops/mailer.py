"""Shared ops mailer — sends via the email_agent Gmail token, daanaa.org
aliases on both ends (founder directive). Used by watchdog, digest, nudge."""
import base64
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def send_ops_email(to_addr: str, subject: str, body: str,
                   from_addr: str = "Daanaa Ops <security@daanaa.org>") -> bool:
    try:
        from scripts.email_agent.oauth import gmail_service
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as e:
        print(f"ops mail failed: {e}", file=sys.stderr)
        return False
