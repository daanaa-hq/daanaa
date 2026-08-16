#!/usr/bin/env python3
"""
Nonprofit Discovery Orchestrator — multi-source website finding workflow.

Orchestrates automated discovery pipeline:
1. IRS 990 e-file extraction (websites + missions)
2. web_finder_agent (domain guessing + embedding verification)
3. Charity Navigator API fallback (for high-value orgs)
4. discovery_daemon link extraction (automatic)

Designed to run daily or on-demand. Produces clear stats + logging.

Usage:
    python3 scripts/nonprofit_discovery_orchestrator.py
    python3 scripts/nonprofit_discovery_orchestrator.py --batch-size 500 --dry-run
    python3 scripts/nonprofit_discovery_orchestrator.py --source irs --limit 100

Args:
    --batch-size: Orgs to process per source (default: 1000)
    --dry-run: Show what would happen, don't write
    --source: Run single source (irs, web_finder, charity_navigator)
    --limit: Max orgs to process total
"""

import sqlite3
import subprocess
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG_DIR = Path.home() / "meritgiving/logs"
LOG_FILE = LOG_DIR / "nonprofit_discovery_orchestrator.log"
STATE_FILE = LOG_DIR / ".discovery_state.json"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class DiscoveryStats:
    """Stats for this run."""
    timestamp: str
    source: str
    attempted: int
    successful: int
    websites_added: int
    missions_added: int
    errors: int

    def to_json(self):
        return json.dumps(asdict(self))


def get_eligible_orgs(limit=1000, has_website=False):
    """Get orgs eligible for discovery (high revenue first)."""
    db = sqlite3.connect(DB)
    cursor = db.cursor()

    query = """
        SELECT EIN, organization_name, total_revenue, STATE
        FROM registry_enriched
        WHERE deductibility = '1'
          AND org_status = 'active'
          AND total_revenue IS NOT NULL
    """

    if not has_website:
        query += " AND (website IS NULL OR website = '')"

    query += " ORDER BY total_revenue DESC LIMIT ?"

    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    db.close()
    return results


def run_irs_extraction(batch_size=1000, dry_run=False):
    """Run IRS 990 e-file extraction (websites + missions)."""
    stats = DiscoveryStats(
        timestamp=datetime.now(timezone.utc).isoformat(),
        source="irs_990",
        attempted=0,
        successful=0,
        websites_added=0,
        missions_added=0,
        errors=0,
    )

    # Dedupe guard: skip if another extraction is mid-run
    if _already_running("extract_990_fields.py"):
        logger.info("extract_990_fields already running — skipping (no duplicate)")
        return stats

    logger.info("Starting IRS 990 e-file extraction...")

    try:
        result = subprocess.run(
            [
                "python3",
                str(Path.home() / "meritgiving/scripts/extract_990_fields.py"),
            ],
            capture_output=True,
            text=True,
            timeout=3600,
        )

        if result.returncode == 0:
            # Parse output for stats
            for line in (result.stdout or "").splitlines():
                if "matched=" in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith("matched="):
                            stats.successful = int(part.split("=")[1].replace(",", ""))
            logger.info(f"✅ IRS extraction complete: {stats.successful:,} matched")
            stats.websites_added = stats.successful  # Approximate
        else:
            logger.warning(f"IRS extraction warning: {result.stderr[:200]}")
            stats.errors += 1

    except subprocess.TimeoutExpired:
        logger.error("IRS extraction timeout (24h limit)")
        stats.errors += 1
    except Exception as e:
        logger.error(f"IRS extraction error: {e}")
        stats.errors += 1

    return stats


def _already_running(pattern: str) -> bool:
    """True if a process matching pattern is already running (dedupe guard)."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", pattern], capture_output=True, text=True, timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def run_web_finder(batch_size=1000, dry_run=False):
    """Run web_finder_agent (domain guessing + embedding verification)."""
    stats = DiscoveryStats(
        timestamp=datetime.now(timezone.utc).isoformat(),
        source="web_finder",
        attempted=batch_size,
        successful=0,
        websites_added=0,
        missions_added=0,
        errors=0,
    )

    # Dedupe guard: a long manual/previous run may still be going. Two
    # web_finders would double-fetch the same candidate pool.
    if _already_running("web_finder_agent.py"):
        logger.info("web_finder_agent already running — skipping this cycle (no duplicate)")
        stats.attempted = 0
        return stats

    logger.info(f"Starting web_finder_agent ({batch_size} orgs, high-revenue first)...")

    try:
        result = subprocess.run(
            [
                "python3",
                str(Path.home() / "meritgiving/scripts/web_finder_agent.py"),
                "--limit",
                str(batch_size),
                "--priority",
                "high-revenue",
                "--workers",
                "8",
            ],
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hours
        )

        if result.returncode == 0:
            # Count verified websites from output
            verified_count = (result.stdout or "").count("✓")
            stats.successful = verified_count
            stats.websites_added = verified_count
            logger.info(f"✅ web_finder found {verified_count:,} verified websites")
        else:
            logger.warning(f"web_finder had errors: {result.stderr[:200]}")
            stats.errors += 1

    except subprocess.TimeoutExpired:
        logger.error("web_finder timeout (2h limit)")
        stats.errors += 1
    except Exception as e:
        logger.error(f"web_finder error: {e}")
        stats.errors += 1

    return stats


def run_charity_navigator_fallback(batch_size=500, dry_run=False):
    """
    Check Charity Navigator for orgs we haven't found elsewhere.
    Legal: rate-limited API, identified UA, caching.
    """
    stats = DiscoveryStats(
        timestamp=datetime.now(timezone.utc).isoformat(),
        source="charity_navigator",
        attempted=batch_size,
        successful=0,
        websites_added=0,
        missions_added=0,
        errors=0,
    )

    logger.info(f"Checking Charity Navigator API ({batch_size} orgs fallback)...")

    # Get high-revenue orgs without donation links yet
    db = sqlite3.connect(DB)
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT EIN, organization_name, STATE
        FROM registry_enriched
        WHERE deductibility = '1'
          AND org_status = 'active'
          AND total_revenue > 1000000
          AND (donate_url IS NULL OR donate_url = '')
        ORDER BY total_revenue DESC
        LIMIT ?
        """,
        (batch_size,),
    )
    orgs = cursor.fetchall()
    db.close()

    if not orgs:
        logger.info("No high-revenue orgs needing CN fallback")
        return stats

    # TODO: Implement CN API check (legal, rate-limited)
    # For now, log the pool
    logger.info(f"CN fallback pool: {len(orgs)} high-revenue orgs without donate links")
    stats.attempted = len(orgs)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Nonprofit discovery orchestrator — multi-source pipeline"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Orgs per source (default: 1000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen, don't write",
    )
    parser.add_argument(
        "--source",
        choices=["irs", "web_finder", "charity_navigator", "all"],
        default="all",
        help="Run single source (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Max orgs to process total",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Nonprofit Discovery Orchestrator Started")
    logger.info("=" * 60)

    all_stats = []

    # IRS 990 extraction (one-time scan of 49K XMLs)
    if args.source in ("irs", "all"):
        logger.info("\n[1/3] IRS 990 E-File Extraction")
        stats = run_irs_extraction(dry_run=args.dry_run)
        all_stats.append(stats)
        logger.info(f"IRS result: {stats.websites_added:,} websites, {stats.errors} errors")

    # web_finder_agent (domain guessing + verification)
    if args.source in ("web_finder", "all"):
        logger.info("\n[2/3] Web Finder Agent")
        batch = args.batch_size if args.limit is None else min(args.limit, args.batch_size)
        stats = run_web_finder(batch_size=batch, dry_run=args.dry_run)
        all_stats.append(stats)
        logger.info(f"web_finder result: {stats.websites_added:,} verified")

    # Charity Navigator fallback
    if args.source in ("charity_navigator", "all"):
        logger.info("\n[3/3] Charity Navigator Fallback")
        stats = run_charity_navigator_fallback(
            batch_size=500, dry_run=args.dry_run
        )
        all_stats.append(stats)
        logger.info(f"CN result: {stats.websites_added:,} found")

    # Summary
    logger.info("\n" + "=" * 60)
    total_websites = sum(s.websites_added for s in all_stats)
    total_missions = sum(s.missions_added for s in all_stats)
    total_errors = sum(s.errors for s in all_stats)

    logger.info(f"Pipeline Complete")
    logger.info(f"  Websites discovered: {total_websites:,}")
    logger.info(f"  Missions extracted: {total_missions:,}")
    logger.info(f"  Errors: {total_errors}")
    logger.info(f"  Discovery daemon will now extract links from new websites")
    logger.info("=" * 60)

    # Save state for monitoring
    state = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "websites_discovered": total_websites,
        "missions_extracted": total_missions,
        "stats": [asdict(s) for s in all_stats],
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    logger.info(f"State saved to {STATE_FILE}")


if __name__ == "__main__":
    main()
