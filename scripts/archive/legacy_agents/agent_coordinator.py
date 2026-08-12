#!/usr/bin/env python3
"""
Multi-Agent Coordinator Framework
Runs Claude and Codex discovery agents in parallel.
Shared leaderboard + results aggregation.
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict

LOG_DIR = Path.home() / "meritgiving/logs"
LEADERBOARD_FILE = LOG_DIR / "agent_leaderboard.json"
RESULTS_DIR = LOG_DIR / "agent_results"

RESULTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] COORD: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "agent_coordinator.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

@dataclass
class AgentScore:
    """Agent performance metrics."""
    agent_name: str
    strategy: str
    websites_found: int
    orgs_tested: int
    success_rate: float
    time_seconds: float
    confidence_level: str
    timestamp: str
    status: str  # "active", "completed", "failed"

def update_leaderboard(agent_scores):
    """Update shared leaderboard."""
    # Sort by success rate descending
    sorted_scores = sorted(
        agent_scores,
        key=lambda x: x.success_rate,
        reverse=True
    )

    leaderboard = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents": [asdict(s) for s in sorted_scores],
        "total_websites_found": sum(s.websites_found for s in sorted_scores),
        "top_performer": sorted_scores[0].agent_name if sorted_scores else None,
    }

    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=2)

    logger.info(f"Leaderboard updated: {leaderboard['total_websites_found']} total websites")
    logger.info(f"Top performer: {leaderboard['top_performer']}")

    return leaderboard

def get_high_revenue_orgs(limit=300):
    """Get orgs for testing."""
    db = sqlite3.connect(Path.home() / "meritgiving/data/merit_registry.db")
    cursor = db.cursor()

    cursor.execute("""
        SELECT ein, organization_name, total_revenue
        FROM registry_enriched
        WHERE deductibility = '1'
          AND org_status = 'active'
          AND (website IS NULL OR website = '')
          AND total_revenue > 500000
        ORDER BY total_revenue DESC
        LIMIT ?
    """, (limit,))

    orgs = cursor.fetchall()
    db.close()
    return orgs

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("AGENT COORDINATOR - FRAMEWORK READY")
    logger.info("=" * 80)
    logger.info("Waiting for Claude and Codex agents to report results...")
    logger.info(f"Leaderboard: {LEADERBOARD_FILE}")
    logger.info(f"Results dir: {RESULTS_DIR}")
    logger.info("=" * 80)
