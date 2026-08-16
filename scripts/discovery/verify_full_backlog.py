#!/usr/bin/env python3
"""
Full Backlog Website Verification
Run semantic validation on all 1.37M discovered websites.
"""

import sys
sys.path.insert(0, '/home/akbar/meritgiving/scripts')

from website_verification_engine import WebsiteVerifier
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] FULL_VERIFY: %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("FULL BACKLOG WEBSITE VERIFICATION")
    logger.info("Processing all 1.37M discovered websites")
    logger.info("Expected: 50-60 hours GPU time")
    logger.info("Confidence scoring: HIGH (>0.65), SUSPICIOUS (0.45-0.65), ERROR (<0.45)")
    logger.info("=" * 80)

    verifier = WebsiteVerifier()
    # Run on ALL discovered websites (no limit)
    stats = verifier.run(limit=2000000, workers=4)

    logger.info("=" * 80)
    logger.info("FULL BACKLOG VERIFICATION COMPLETE")
    logger.info(f"Total websites verified: {stats['total_tested']:,}")
    logger.info(f"High confidence (>0.65): {stats['verified']:,}")
    logger.info(f"Needs review (0.45-0.65): {stats['suspicious']:,}")
    logger.info(f"Low/error (<0.45): {stats['errors']:,}")
    logger.info(f"Time elapsed: {stats['elapsed_seconds']/3600:.1f} hours")
    logger.info("=" * 80)
