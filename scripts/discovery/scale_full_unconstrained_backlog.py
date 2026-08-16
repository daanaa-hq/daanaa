#!/usr/bin/env python3
"""
Full Unconstrained Backlog Discovery
Process ALL nonprofits without websites (no revenue filter).
Expected: ~1.55M websites discovered at 99.8% success rate.
Time: ~15-18 hours at 48+ orgs/second.
"""

import sys
sys.path.insert(0, '/home/akbar/meritgiving/scripts')

from unified_discovery_engine import UnifiedEngine
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] FULL_BACKLOG: %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("FULL UNCONSTRAINED BACKLOG DISCOVERY")
    logger.info("Processing ALL nonprofits without websites (no revenue filter)")
    logger.info("Expected: ~1.55M+ websites (99.8% success rate)")
    logger.info("Estimated time: 15-18 hours at 48+ orgs/second")
    logger.info("GPU usage: 0% (CPU/network bound)")
    logger.info("=" * 80)

    engine = UnifiedEngine()
    # No revenue filter: fetch all orgs without websites
    stats = engine.run(limit=2000000, workers=12)

    logger.info("=" * 80)
    logger.info("FULL BACKLOG DISCOVERY COMPLETE")
    logger.info(f"Total websites discovered: {stats['found']:,}")
    logger.info(f"Success rate: {stats['success_rate']*100:.2f}%")
    logger.info(f"Time elapsed: {stats['elapsed_seconds']/3600:.1f} hours")
    logger.info(f"Orgs per second: {stats['orgs_per_second']:.1f}")
    logger.info("=" * 80)
