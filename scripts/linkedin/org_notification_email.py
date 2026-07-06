"""
Org notification email — the day-of "we featured you" email.

Identified 2026-07-02 as the highest-leverage piece of the marketing pipeline
and never built. When Daanaa features an org (LinkedIn/Bluesky gem post,
carousel, etc.), the org itself is the best distribution multiplier: if they
see it and reshare, their own audience discovers Daanaa. This script closes
that loop by drafting a same-day notification email.

Also reusable for cold "claim your profile" outreach — same specific-gap-hook
pattern, just without the "we posted about you today" framing.

Never sends anything. Drafts only, saved for manual review and send.

Usage:
  python3 org_notification_email.py --ein 202910382                 # featured-today framing
  python3 org_notification_email.py --ein 202910382 --claim-only     # claim-your-profile framing, no "featured today" line
  python3 org_notification_email.py --today                         # most recent entry in .featured_gems.json
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = BASE.parent.parent / "data" / "merit_registry.db"
FEATURED_LOG = BASE / ".featured_gems.json"
OUT_DIR = BASE.parent.parent / "docs" / "outreach" / "notifications"

sys.path.insert(0, str(BASE))
import llm_client as _llm


def get_org(ein: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """SELECT EIN, organization_name, CITY, STATE, mission, mission_source,
                  website, donate_url, donate_url_status, cause_tags
           FROM registry_enriched WHERE EIN=?""",
        (ein,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise SystemExit(f"EIN {ein} not found in registry_enriched")
    return dict(row)


def most_recent_featured_ein() -> str:
    if not FEATURED_LOG.exists():
        raise SystemExit("No .featured_gems.json yet — pass --ein explicitly")
    eins = json.loads(FEATURED_LOG.read_text())
    if not eins:
        raise SystemExit(".featured_gems.json is empty — pass --ein explicitly")
    return eins[-1]


def build_prompt(org: dict, featured_today: bool) -> str:
    gap_notes = []
    if org["mission_source"] and org["mission_source"] != "org_submitted":
        gap_notes.append("the mission on their page was written by Daanaa from public filings, not by the org")
    if not org["donate_url"]:
        gap_notes.append("there is no donation link on their page yet")
    gap_line = "; ".join(gap_notes) if gap_notes else "their profile is otherwise complete"

    context = (
        f"Org name: {org['organization_name']}\n"
        f"City/state: {org['CITY']}, {org['STATE']}\n"
        f"Mission on file: {org['mission']}\n"
        f"Profile gap: {gap_line}\n"
        f"Claim link: https://daanaa.org/org/{org['EIN']}\n"
    )

    if featured_today:
        ask = (
            "We featured this org today in a Daanaa social post (LinkedIn/Bluesky). "
            "Write a short email letting them know, inviting them to see the post and "
            "reshare it if they'd like, and mentioning they can claim their free profile "
            "(fixing the gap noted above) in about 5 minutes."
        )
    else:
        ask = (
            "Write a short cold outreach email inviting them to claim their free Daanaa "
            "profile, using the specific profile gap noted above as the reason to act — "
            "not a generic 'you're listed' pitch."
        )

    return f"""You are drafting a short outreach email for Daanaa, a free nonprofit
directory built from public IRS data. No pay-for-placement, ever.

Voice rules — follow exactly:
- Kitchen-table test: a real person would say this out loud
- No hyphenated jargon (no "mission-driven", "impact-focused", "data-driven")
- No em dashes
- Specific, not generic — name the actual gap, not a vague benefit
- Under 150 words total including subject line
- Sign off as "Akbar, daanaa.org"
- No urgency/scarcity language, no claims of endorsement

{context}
{ask}

Output format:
Subject: <subject line>

<email body>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ein")
    ap.add_argument("--today", action="store_true", help="use most recent .featured_gems.json entry")
    ap.add_argument("--claim-only", action="store_true", help="cold claim-outreach framing instead of featured-today")
    args = ap.parse_args()

    ein = args.ein or (most_recent_featured_ein() if args.today else None)
    if not ein:
        raise SystemExit("Pass --ein <EIN> or --today")

    org = get_org(ein)
    prompt = build_prompt(org, featured_today=not args.claim_only)
    draft = _llm.generate(prompt, max_tokens=400, temperature=0.7)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_name = org["organization_name"].lower().replace(" ", "-")[:40]
    out_path = OUT_DIR / f"{date_str}-{ein}-{safe_name}.md"
    out_path.write_text(
        f"# {org['organization_name']} ({org['CITY']}, {org['STATE']}) — EIN {ein}\n\n"
        f"Generated {date_str}. Draft only, not sent.\n\n"
        f"{draft}\n"
    )
    print(f"Draft written: {out_path}")
    print()
    print(draft)


if __name__ == "__main__":
    main()
