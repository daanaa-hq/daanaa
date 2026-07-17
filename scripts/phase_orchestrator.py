#!/usr/bin/env python3
"""
Phase 1 → Phase 2 orchestrator.

Monitors discovery daemon progress. When Phase 1 shows saturation
(org batches < 50 for 5+ consecutive iterations), auto-activates
Phase 2 (Charity Navigator rate-limited scraper).

Runs continuously, checks every 30 minutes.
"""

import sqlite3
import subprocess
import time
import logging
import json
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/phase_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
STATE_FILE = Path.home() / 'meritgiving' / 'logs' / '.phase_state.json'
PHASE2_TRIGGER_LOG = Path.home() / 'meritgiving' / 'logs' / 'phase2_activation.log'

CHECK_INTERVAL = 1800  # 30 minutes
SATURATION_BATCH_THRESHOLD = 50
SATURATION_ITERATIONS = 5


def load_state():
    """Load phase state from disk."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        'phase': 1,
        'started': datetime.now().isoformat(),
        'low_batch_count': 0,
        'last_batch_size': 0,
        'phase2_activated': False
    }


def save_state(state):
    """Save phase state to disk."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_org_batch_size():
    """Get count of orgs awaiting discovery in this iteration."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM registry_enriched
        WHERE donate_url IS NULL AND EIN > 0
    """)
    count = cursor.fetchone()[0]
    db.close()
    return count


def get_link_queue_count():
    """Get pending links in queue."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE status='pending'")
    count = cursor.fetchone()[0]
    db.close()
    return count


def activate_phase2_parallel():
    """Activate Phase 2a (Advanced website discovery) + Phase 2b (Charity Navigator) in parallel.

    Phase 2a: Website discovery for orgs WITH financial data (stale/missing)
    Phase 2b: Charity Navigator fallback for orgs WITH NO financial data
    """
    logger.info("=" * 70)
    logger.info("🚀 ACTIVATING PHASE 2 (PARALLEL):")
    logger.info("  Phase 2a: Advanced website discovery (financial data orgs)")
    logger.info("  Phase 2b: Charity Navigator scraper (no-data orgs)")
    logger.info("=" * 70)

    success = True

    # Phase 2a: Advanced website discovery (steps 1-4)
    try:
        script_2a = Path.home() / 'meritgiving' / 'scripts' / 'website_discovery_advanced.py'
        if script_2a.exists():
            subprocess.Popen(
                ['python3', str(script_2a), '50', '0.3'],  # batch=50, sleep=0.3s
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            logger.info("✅ Phase 2a (Advanced discovery) started")
        else:
            logger.warning(f"⚠️  Phase 2a script not found: {script_2a}")
            success = False
    except Exception as e:
        logger.error(f"❌ Failed to start Phase 2a: {e}")
        success = False

    # Phase 2b: Charity Navigator scraper — PERMANENTLY DISABLED 2026-07-17.
    # CN's Terms of Use explicitly prohibit "data mining, robots, or similar
    # data gathering and extraction methods" and republishing without written
    # consent (verified 2026-07-17, board decision — see
    # docs/BOARD_SIMULATION_2026_07_17_EVENING.md). Never re-enable scraping.
    # The sanctioned path, if CN data is ever wanted, is their official API
    # program with written consent — a founder-gated decision.
    logger.info("Phase 2b (Charity Navigator scraper) skipped — disabled per ToS, "
                "board decision 2026-07-17")
            success = False
    except Exception as e:
        logger.error(f"❌ Failed to start Phase 2b: {e}")
        success = False

    if success:
        with open(PHASE2_TRIGGER_LOG, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] Phase 2 (2a+2b parallel) activated\n")

    return success


def main():
    logger.info("Phase Orchestrator started")

    while True:
        try:
            state = load_state()
            batch_size = get_org_batch_size()
            queue_count = get_link_queue_count()

            logger.info(
                f"Phase {state['phase']} | "
                f"Orgs needing discovery: {batch_size} | "
                f"Links queued: {queue_count}"
            )

            # Track saturation (Phase 1 → Phase 2 transition)
            if state['phase'] == 1:
                if batch_size < SATURATION_BATCH_THRESHOLD:
                    state['low_batch_count'] += 1
                    logger.info(
                        f"⚠️  Low batch detected ({batch_size} orgs), "
                        f"count: {state['low_batch_count']}/{SATURATION_ITERATIONS}"
                    )
                else:
                    state['low_batch_count'] = 0

                if state['low_batch_count'] >= SATURATION_ITERATIONS and not state['phase2_activated']:
                    logger.warning(
                        f"🔔 Phase 1 saturation detected: "
                        f"{SATURATION_ITERATIONS} consecutive batches < {SATURATION_BATCH_THRESHOLD} orgs"
                    )
                    if activate_phase2_parallel():
                        state['phase'] = 2
                        state['phase2_activated'] = True
                        logger.info("✅ Transitioned to Phase 2 (2a+2b running in parallel)")

            state['last_batch_size'] = batch_size
            save_state(state)

        except Exception as e:
            logger.error(f"Error in orchestrator: {e}", exc_info=True)

        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
