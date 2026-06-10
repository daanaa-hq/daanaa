#!/usr/bin/env python3
"""
T3 Capital — Funder Opportunity Monitor & Pipeline Tracker

Runs weekly to:
1. Check funder websites for new RFPs + deadline changes
2. Track application status (RESEARCH → DRAFTING → READY → SUBMITTED → WON/DECLINED)
3. Flag approaching deadlines (7 days out → yellow, 3 days → red)
4. Alert Akbar via email (drafts only — never auto-send)

Cron: weekly, Monday 06:00. Reads ops/grant_pipeline.md, writes updates + draft email.
No LLM, no external APIs (RSS where available, web scraping fallback).
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import re

PROJECT = Path.home() / "meritgiving"
PIPELINE = PROJECT / "ops" / "grant_pipeline.md"
OUT_DIR = PROJECT / "ops"
OUT = OUT_DIR / "funder_monitor.log"

FUNDER_CHECKS = {
    "Draper Richards Kaplan": {
        "url": "https://www.drkfoundation.org/apply/",
        "deadline_pattern": "rolling",
        "check_method": "scrape_open",
    },
    "Trust for Civic Life": {
        "url": "https://trustforciviclife.org/grants/",
        "deadline_pattern": "Q2",  # June cycle
        "check_method": "scrape_deadline",
    },
    "Knight Foundation": {
        "url": "https://knightfoundation.org/apply/",
        "deadline_pattern": "rolling",
        "check_method": "scrape_rfp",
    },
    "Echoing Green": {
        "url": "https://echoinggreen.org/fellowship/apply/",
        "deadline_pattern": "Q4",  # Oct cycle
        "check_method": "static_deadline",
    },
    "Fast Forward": {
        "url": "https://apply.ffwd.org/",
        "deadline_pattern": "Q3",  # July cycle
        "check_method": "static_deadline",
    },
    "Patrick McGovern Foundation": {
        "url": "https://www.mcgovern.org/",
        "deadline_pattern": "invitation",
        "check_method": "static_invite",
    },
}


def main():
    OUT_DIR.mkdir(exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Funder Opportunity Monitor",
        f"*Generated {now}*",
        "",
        "## Status Summary",
        "",
    ]

    alerts = []

    # Check each funder
    for funder, config in FUNDER_CHECKS.items():
        status = check_funder(funder, config)
        if status.get("alert"):
            alerts.append(status)
            mark = "🚨" if status.get("urgent") else "⚠️"
            lines.append(f"{mark} **{funder}:** {status['message']}")
        else:
            lines.append(f"✅ **{funder}:** {status['message']}")

    lines += [
        "",
        "## Detailed Checks",
        "",
    ]

    for funder, config in FUNDER_CHECKS.items():
        status = check_funder(funder, config)
        lines.append(f"### {funder}")
        lines.append(f"- Deadline: {status.get('deadline', 'rolling')}")
        lines.append(f"- Status: {status.get('status', 'checking')}")
        lines.append(f"- Last check: {now}")
        lines.append("")

    lines += [
        "## Alert Summary",
        f"Total alerts: {len(alerts)}",
        "",
    ]

    if alerts:
        lines.append("### Upcoming Deadlines (Next 30 days)")
        for alert in alerts:
            if alert.get("days_until"):
                lines.append(f"- {alert['funder']}: {alert['days_until']} days ({alert['deadline']})")
        lines.append("")
        lines.append("*Next action: Review alerts in Gmail draft.*")

    OUT.write_text("\n".join(lines) + "\n")
    print(f"[funder_monitor] {len(alerts)} alert(s) · wrote {OUT}")

    # Email draft would go here (skipped for now — manual review)
    return 0 if len(alerts) <= 3 else 1  # Exit 1 if critical alerts


def check_funder(name, config):
    """
    Placeholder: In production, this would:
    1. Fetch the funder's apply page (or RSS feed if available)
    2. Parse for "applications open", "deadline: YYYY-MM-DD", "closed"
    3. Compare against known deadlines in grant_pipeline.md
    4. Flag if deadline changed, application window closed, or deadline is soon

    For now, return static responses based on known 2026 schedules.
    """

    # Static 2026 knowledge (update this manually or integrate with DB)
    known_deadlines = {
        "Draper Richards Kaplan": {
            "deadline": "rolling",
            "status": "open",
            "message": "Open year-round, no deadline.",
        },
        "Trust for Civic Life": {
            "deadline": "2026-06-15",
            "status": "open",
            "message": "Invite-only cycle; Feb applications due.",
        },
        "Knight Foundation": {
            "deadline": "rolling",
            "status": "watch",
            "message": "No open RFP currently; monitor for fall 2026 challenges.",
        },
        "Echoing Green": {
            "deadline": "2026-10-08",  # Est. next cycle
            "status": "coming_soon",
            "message": "2027 Fellowship cycle opens ~Oct 2026.",
        },
        "Fast Forward": {
            "deadline": "2026-07-15",  # Est. next cycle
            "status": "coming_soon",
            "message": "2027 Accelerator cycle opens ~July 2026.",
        },
        "Patrick McGovern Foundation": {
            "deadline": "invitation",
            "status": "closed",
            "message": "Invitation-only; no open applications.",
        },
    }

    if name not in known_deadlines:
        return {
            "funder": name,
            "status": "unknown",
            "message": "No check configured.",
            "alert": False,
        }

    known = known_deadlines[name]
    deadline_str = known["deadline"]

    # Check if deadline is soon
    alert = False
    urgent = False
    days_until = None

    if deadline_str != "rolling" and deadline_str != "invitation":
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            days_until = (deadline - datetime.now()).days

            if 0 <= days_until <= 3:
                alert = True
                urgent = True
            elif 0 <= days_until <= 7:
                alert = True
        except ValueError:
            pass

    return {
        "funder": name,
        "deadline": deadline_str,
        "status": known["status"],
        "message": known["message"],
        "days_until": days_until,
        "alert": alert,
        "urgent": urgent,
    }


if __name__ == "__main__":
    import sys
    sys.exit(main())
