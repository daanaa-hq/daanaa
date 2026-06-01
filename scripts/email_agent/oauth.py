"""OAuth bootstrap + token loading for the Daanaa email agent.

Holds the refresh token for hello@ecomargins.com (the receiving inbox into which
all 9 @daanaa.org aliases forward). Run this module directly the first time to
authorize; subsequent runs reuse the saved token silently.

Per email-agent-routing.md, this is the SINGLE credential the agent uses. The
account-of-record (accounts@daanaa.org) is intentionally NOT wired here.
"""

from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CONFIG_DIR = Path(os.path.expanduser("~/.config/daanaa"))
CREDENTIALS_PATH = CONFIG_DIR / "gmail_credentials.json"
TOKEN_PATH = CONFIG_DIR / "gmail_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]


def load_credentials() -> Credentials:
    """Return valid Credentials, running the browser flow once if needed."""
    creds: Credentials | None = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Missing OAuth credential at {CREDENTIALS_PATH}. "
                "Download from console.cloud.google.com → APIs & Services → Credentials."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=False)

    TOKEN_PATH.write_text(creds.to_json())
    os.chmod(TOKEN_PATH, 0o600)
    return creds


def gmail_service():
    return build("gmail", "v1", credentials=load_credentials())


if __name__ == "__main__":
    svc = gmail_service()
    profile = svc.users().getProfile(userId="me").execute()
    print(f"Authorized as: {profile['emailAddress']}")
    print(f"Total messages: {profile['messagesTotal']}")
    print(f"Token saved to: {TOKEN_PATH}")
