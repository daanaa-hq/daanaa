#!/usr/bin/env python3
"""
Feedback Ingestion Agent — Ingest user feedback, classify, route to teams
Runs: Whenever feedback arrives (monitored directory)
"""

import sqlite3
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

DB = Path.home() / "meritgiving/data/merit_registry.db"
FEEDBACK_DIR = Path.home() / "meritgiving/data/feedback"
LOG = Path.home() / "meritgiving/logs/feedback_ingestion.log"

class FeedbackType(Enum):
    ORG_MISSING = "org_missing"
    WEBSITE_BROKEN = "website_broken"
    CATEGORY_WRONG = "category_wrong"
    LINK_BROKEN = "link_broken"
    TIER_WRONG = "tier_wrong"
    SEARCH_WRONG = "search_wrong"
    OTHER = "other"

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def classify_feedback(text: str) -> FeedbackType:
    """Classify feedback text into category."""
    text_lower = text.lower()

    patterns = {
        FeedbackType.ORG_MISSING: r"(missing|not found|can't find|don't see|need)",
        FeedbackType.WEBSITE_BROKEN: r"(website.*broken|link.*dead|404|not working)",
        FeedbackType.LINK_BROKEN: r"(donate.*broken|donate.*404|donate.*doesn't work)",
        FeedbackType.CATEGORY_WRONG: r"(wrong category|mislabeled|category incorrect)",
        FeedbackType.TIER_WRONG: r"(tier wrong|rating wrong|score wrong)",
        FeedbackType.SEARCH_WRONG: r"(search result|search wrong|didn't find|filtering)",
    }

    for ftype, pattern in patterns.items():
        if re.search(pattern, text_lower):
            return ftype

    return FeedbackType.OTHER

def ingest_feedback_file(filepath: Path):
    """Process a single feedback submission."""
    try:
        with open(filepath) as f:
            data = json.load(f)

        feedback_type = classify_feedback(data.get("text", ""))
        user_id = data.get("user_id", "anonymous")
        ein = data.get("ein", None)
        org_name = data.get("org_name", "")

        # Log the feedback
        log(f"Feedback: [{feedback_type.value}] {user_id} → {org_name}")

        # Route to team
        if feedback_type == FeedbackType.WEBSITE_BROKEN:
            route_to_team("Website Discovery", data)
        elif feedback_type == FeedbackType.LINK_BROKEN:
            route_to_team("Donation Links", data)
        elif feedback_type == FeedbackType.CATEGORY_WRONG:
            route_to_team("Classification", data)
        elif feedback_type == FeedbackType.TIER_WRONG:
            route_to_team("Scoring", data)
        elif feedback_type == FeedbackType.ORG_MISSING:
            route_to_team("Discovery", data)
        else:
            route_to_team("General", data)

        # Archive
        (FEEDBACK_DIR / "processed").mkdir(exist_ok=True)
        filepath.rename(FEEDBACK_DIR / "processed" / filepath.name)

    except Exception as e:
        log(f"  ERROR processing {filepath.name}: {e}")

def route_to_team(team: str, data: dict):
    """Route feedback to appropriate team queue."""
    queue_dir = FEEDBACK_DIR / f"queue_{team.lower().replace(' ', '_')}"
    queue_dir.mkdir(exist_ok=True)

    # Write to team queue
    queue_file = queue_dir / f"{datetime.now(timezone.utc).isoformat()}.json"
    with open(queue_file, "w") as f:
        json.dump(data, f)

    log(f"  → Routed to {team} team")

def main():
    FEEDBACK_DIR.mkdir(exist_ok=True)
    log("Feedback Ingestion Agent started")

    # Process any pending feedback files
    feedback_files = list((FEEDBACK_DIR / "pending").glob("*.json")) if (FEEDBACK_DIR / "pending").exists() else []

    if not feedback_files:
        log("  No pending feedback")
        return

    log(f"Processing {len(feedback_files)} feedback items...")
    for ffile in feedback_files:
        ingest_feedback_file(ffile)

    log(f"✓ Ingestion complete ({len(feedback_files)} items processed)")

if __name__ == "__main__":
    main()
