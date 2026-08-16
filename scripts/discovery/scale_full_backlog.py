#!/usr/bin/env python3
"""
Full Backlog Discovery Run
Process all 1.6M+ nonprofits without websites.
Expected: ~1.55M websites discovered (99.8% success rate).
Time: ~19 hours at 23 orgs/second.
"""

import sys
sys.path.insert(0, '/home/akbar/meritgiving/scripts')

from unified_discovery_engine import UnifiedEngine
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] BACKLOG: %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("FULL BACKLOG DISCOVERY INITIATED")
    logger.info("Processing 1.6M+ nonprofits without websites")
    logger.info("Expected: ~1.55M websites (99.8% success)")
    logger.info("Estimated time: 19 hours")
    logger.info("=" * 80)

    engine = UnifiedEngine()
    stats = engine.run(limit=1600000, workers=12)

    logger.info("=" * 80)
    logger.info("BACKLOG DISCOVERY COMPLETE")
    logger.info(f"Total websites discovered: {stats['found']:,}")
    logger.info(f"Success rate: {stats['success_rate']*100:.2f}%")
    logger.info(f"Time elapsed: {stats['elapsed_seconds']/3600:.1f} hours")
    logger.info("=" * 80)
