#!/usr/bin/env python3
"""Daily prompt improvement cron job (Task 8).

Runs at 7 AM to autonomously improve prompts based on quality trends.
If quality metrics indicate accuracy is below target, generates a new prompt version.

The improvement mechanism:
  1. Check if today's quality metrics show accuracy < target (0.75)
  2. If yes, fetch recent metrics trend (7 days)
  3. Generate an improved prompt version with enhanced context/examples
  4. Save new version to prompt_versions.json
  5. Log the reasoning and date

Usage:
  python3 improve_prompts_cron.py  (uses production DB and config)
  python3 improve_prompts_cron.py --db /path/to/test.db  (uses test DB)
"""
import sys
import sqlite3
import json
import argparse
from datetime import date
from pathlib import Path

# Make the repo root importable
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.prompt_improvement import PromptImprovement

BASE = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "merit_registry.db"
CONFIG_PATH = BASE / "scripts" / "enrich_batch_config.json"


def load_config():
    """Load enrichment batch configuration from JSON file.

    Returns:
        Dict with batch config, server settings, thresholds, and prompt templates
    """
    with open(CONFIG_PATH) as f:
        return json.load(f)


def main(db_path=None, config_path=None, prompt_versions_file=None):
    """Autonomously improve prompts based on quality metrics.

    Args:
        db_path: Path to SQLite database. If None, uses production DB
        config_path: Path to config JSON. If None, uses production config
        prompt_versions_file: Path to prompt_versions.json. If None, uses default

    Returns:
        New prompt version string (e.g., 'v1.2') if improvement was triggered,
        or None if quality was good and no improvement needed
    """
    db_path = db_path or str(DB_PATH)
    config_path = config_path or str(CONFIG_PATH)

    # Load config
    with open(config_path) as f:
        config = json.load(f)

    # Create DB connection
    con = sqlite3.connect(str(db_path), timeout=180)

    try:
        improver = PromptImprovement(
            db_con=con,
            config=config,
            prompt_versions_file=prompt_versions_file
        )

        if improver.should_improve_prompts():
            new_version = improver.generate_improved_prompt()
            print(f"[{date.today()}] New prompt version created: {new_version}")
            print(improver.get_improvement_reasoning())
            return new_version
        else:
            print(f"[{date.today()}] Quality metrics good; no improvement needed")
            return None

    finally:
        con.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Autonomously improve enrichment prompts based on quality metrics'
    )
    parser.add_argument('--db', dest='db_path', help='Path to SQLite database')
    parser.add_argument('--config', dest='config_path', help='Path to config JSON')
    parser.add_argument('--prompts-file', dest='prompt_versions_file',
                        help='Path to prompt_versions.json')
    args = parser.parse_args()

    result = main(
        db_path=args.db_path,
        config_path=args.config_path,
        prompt_versions_file=args.prompt_versions_file
    )
    sys.exit(0)
