"""
Bluesky posting via atproto — the LinkedIn equivalent for Bluesky.

Setup (one-time, needs the user):
  1. Create a bsky.social account for Daanaa (or use an existing one).
  2. Settings -> App passwords -> create one (do NOT use the main account password).
  3. Write scripts/linkedin/.session/bluesky_creds.json:
     {"handle": "daanaa.bsky.social", "app_password": "xxxx-xxxx-xxxx-xxxx"}

Usage:
  python3 bluesky_poster.py --setup           # verify creds work, print profile
  python3 bluesky_poster.py --text "hello"    # post plain text (manual test)
"""
import argparse
import json
from pathlib import Path

from atproto import Client

BASE = Path(__file__).parent
CREDS_FILE = BASE / ".session" / "bluesky_creds.json"


def _load_creds() -> dict:
    if not CREDS_FILE.exists():
        raise SystemExit(
            f"No Bluesky credentials at {CREDS_FILE}.\n"
            'Create it with: {"handle": "daanaa.bsky.social", "app_password": "xxxx-xxxx-xxxx-xxxx"}\n'
            "Get an app password from Bluesky Settings -> App passwords (not your main password)."
        )
    return json.loads(CREDS_FILE.read_text())


def get_client() -> Client:
    creds = _load_creds()
    client = Client()
    client.login(creds["handle"], creds["app_password"])
    return client


def post_text(text: str) -> str:
    """Post plain text, return the post URI."""
    client = get_client()
    if len(text) > 300:
        text = text[:297] + "..."
    post = client.send_post(text=text)
    return post.uri


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", action="store_true", help="verify creds, print profile")
    ap.add_argument("--text", help="post this plain text (manual test)")
    args = ap.parse_args()

    if args.setup:
        client = get_client()
        profile = client.get_profile(client.me.did)
        print(f"Logged in as: {profile.display_name} (@{profile.handle})")
        print(f"Followers: {profile.followers_count}")
        return

    if args.text:
        uri = post_text(args.text)
        print(f"Posted: {uri}")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
