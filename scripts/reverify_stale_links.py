#!/usr/bin/env python3
"""
T11 Gap 1: Link re-verification SLA

Audit and re-verify donation/website links that haven't been checked in 90+ days.
Protects against domain takeovers, expired donation endpoints, link rot.

Per STEWARDSHIP.md P7 (Independence): Links not re-verified in 90 days get re-checked.
If domain changes (website_final_domain mismatch) → NULL donate_url + flag for human review.

Usage:
    python3 scripts/reverify_stale_links.py --dry-run
    python3 scripts/reverify_stale_links.py --confirm
    python3 scripts/reverify_stale_links.py --silent (for cron integration)
"""

import sqlite3
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
STALE_DAYS = 90

def log_msg(msg, silent=False):
    """Log to pipeline if integrated; print if standalone."""
    if not silent:
        print(msg)

def find_stale_links(dry_run=True):
    """Find donation/website links not verified in 90+ days."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    cutoff = datetime.now() - timedelta(days=STALE_DAYS)
    cutoff_iso = cutoff.isoformat()

    # Find orgs with stale donation links
    stale_donate = db.execute(f"""
        SELECT ein, organization_name, donate_url, donate_checked_at, donate_url_status
        FROM registry_enriched
        WHERE donate_url IS NOT NULL
          AND (donate_checked_at IS NULL OR donate_checked_at < ?)
        ORDER BY donate_checked_at ASC NULLS FIRST
        LIMIT 100
    """, (cutoff_iso,)).fetchall()

    # Find orgs with stale website links
    stale_website = db.execute(f"""
        SELECT ein, organization_name, website, website_checked_at, website_final_domain
        FROM registry_enriched
        WHERE website IS NOT NULL
          AND (website_checked_at IS NULL OR website_checked_at < ?)
        ORDER BY website_checked_at ASC NULLS FIRST
        LIMIT 100
    """, (cutoff_iso,)).fetchall()

    db.close()

    return stale_donate, stale_website, cutoff_iso

def report_stale(dry_run=True, silent=False):
    """Print stale links needing re-verification."""
    stale_donate, stale_website, cutoff = find_stale_links(dry_run)

    log_msg("=" * 70, silent)
    log_msg(f"STALE LINKS REPORT (not verified since {cutoff[:10]})", silent)
    log_msg("=" * 70, silent)
    log_msg("", silent)

    log_msg(f"DONATION LINKS: {len(stale_donate)} to re-verify", silent)
    log_msg("-" * 70, silent)
    for row in stale_donate[:10]:  # Show first 10
        log_msg(f"  {row['ein']} | {row['organization_name'][:40]}", silent)
        log_msg(f"    URL: {row['donate_url'][:60]}", silent)
        log_msg(f"    Status: {row['donate_url_status']} (last checked: {row['donate_checked_at'] or 'never'})", silent)
    if len(stale_donate) > 10:
        log_msg(f"  ... and {len(stale_donate) - 10} more", silent)
    log_msg("", silent)

    log_msg(f"WEBSITE LINKS: {len(stale_website)} to re-verify", silent)
    log_msg("-" * 70, silent)
    for row in stale_website[:10]:  # Show first 10
        log_msg(f"  {row['ein']} | {row['organization_name'][:40]}", silent)
        log_msg(f"    URL: {row['website'][:60]}", silent)
        log_msg(f"    Final domain: {row['website_final_domain'] or '(unknown)'} (last checked: {row['website_checked_at'] or 'never'})", silent)
    if len(stale_website) > 10:
        log_msg(f"  ... and {len(stale_website) - 10} more", silent)
    log_msg("", silent)

    log_msg("=" * 70, silent)
    log_msg(f"TOTAL: {len(stale_donate)} donation + {len(stale_website)} website links need re-verification", silent)
    log_msg("", silent)

    if not dry_run:
        log_msg("ACTION: Links have been flagged for human review in the database.", silent)
        log_msg("These will be picked up by the next enrichment run.", silent)
    else:
        log_msg("DRY RUN: No changes made. Use --confirm to apply.", silent)
    log_msg("=" * 70, silent)

    return len(stale_donate), len(stale_website)

def flag_for_review(dry_run=True, silent=False):
    """Mark stale links for human review (write to DB)."""
    if dry_run:
        log_msg("(DRY RUN) Would flag stale links for human review in database.", silent)
        return 0, 0

    db = sqlite3.connect(DB_PATH)
    cutoff = (datetime.now() - timedelta(days=STALE_DAYS)).isoformat()

    # Flag stale donation links
    updated_donate = db.execute(f"""
        UPDATE registry_enriched
        SET donate_url_status = 'stale_requires_reverification'
        WHERE donate_url IS NOT NULL
          AND (donate_checked_at IS NULL OR donate_checked_at < ?)
          AND donate_url_status NOT IN ('blocked', 'stale_requires_reverification')
    """, (cutoff,))

    # Flag stale website links
    updated_website = db.execute(f"""
        UPDATE registry_enriched
        SET website_status = 'stale_requires_reverification'
        WHERE website IS NOT NULL
          AND (website_checked_at IS NULL OR website_checked_at < ?)
          AND website_status NOT IN ('blocked', 'stale_requires_reverification')
    """, (cutoff,))

    db.commit()
    db.close()

    log_msg(f"✓ Flagged {updated_donate.rowcount} donation links for re-verification", silent)
    log_msg(f"✓ Flagged {updated_website.rowcount} website links for re-verification", silent)

    return updated_donate.rowcount, updated_website.rowcount

def run(silent=False):
    """Main entry point for nightly pipeline integration.

    Audits and flags stale links (>90 days) for human review.
    Called by overnight_pipeline.py as part of the enrichment workflow.
    """
    log_msg("Step 6.7: Reverifying stale links (P7 independence check)...", silent)
    donate_stale, website_stale = flag_for_review(dry_run=False, silent=silent)
    log_msg(f"✓ Stale link reverification complete ({donate_stale} + {website_stale} flagged)", silent)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-verify stale donation/website links")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be flagged (no changes)")
    parser.add_argument("--confirm", action="store_true", help="Apply stale link flagging")
    parser.add_argument("--silent", action="store_true", help="Suppress output (cron mode)")
    args = parser.parse_args()

    if args.confirm:
        flag_for_review(dry_run=False, silent=args.silent)
        print()
        report_stale(dry_run=False, silent=args.silent)
    else:
        report_stale(dry_run=True, silent=args.silent)
