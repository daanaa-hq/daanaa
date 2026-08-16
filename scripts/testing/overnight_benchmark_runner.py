#!/usr/bin/env python3
"""
overnight_benchmark_runner.py — Nightly scraper benchmark automation.

Runs every night (configured via cron) to:
1. Test current implementation (baseline)
2. Test aiohttp variant
3. Compare throughput/latency/errors
4. Log results to JSON
5. Update dashboard
6. Email/log winner

Add to crontab:
    0 21 * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 scripts/overnight_benchmark_runner.py

Results saved to:
    - data/scraper_benchmarks/{timestamp}.json (raw results)
    - docs/SCRAPER_BENCHMARKS.md (auto-updated dashboard)
"""

import subprocess
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

LOG_FILE = Path.home() / "meritgiving/logs/overnight_benchmark.log"
SCRIPTS_DIR = Path.home() / "meritgiving/scripts"

# Logging
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_benchmark():
    """Run nightly benchmark suite."""
    logger.info("=" * 60)
    logger.info("OVERNIGHT BENCHMARK STARTED")
    logger.info("=" * 60)

    try:
        # Run benchmark with 1000 orgs (balance between time and validity)
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "benchmark_scrapers.py"),
            "--limit", "1000",
            "--all-configs",  # Run all available scrapers
            "--timeout", "600"  # 10 min timeout per config
        ]

        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPTS_DIR.parent),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )

        logger.info("STDOUT:\n" + result.stdout)
        if result.stderr:
            logger.warning("STDERR:\n" + result.stderr)

        if result.returncode != 0:
            logger.error(f"Benchmark failed with return code {result.returncode}")
            return False

        logger.info("=" * 60)
        logger.info("OVERNIGHT BENCHMARK COMPLETED")
        logger.info("=" * 60)

        # Parse results and log winner
        parse_and_log_results()

        return True

    except subprocess.TimeoutExpired:
        logger.error("Benchmark timeout (1 hour exceeded)")
        return False
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return False


def parse_and_log_results():
    """Parse latest benchmark results and log summary."""
    try:
        benchmark_dir = Path.home() / "meritgiving/data/scraper_benchmarks"
        latest_file = max(benchmark_dir.glob("benchmark_*.json"), key=lambda p: p.stat().st_mtime)

        with open(latest_file) as f:
            data = json.load(f)

        results = data["results"]

        if not results:
            logger.warning("No results found in benchmark output")
            return

        # Find winner by throughput
        winner = max(results, key=lambda r: r["throughput_per_sec"])

        logger.info("\n" + "=" * 60)
        logger.info("BENCHMARK RESULTS")
        logger.info("=" * 60)

        for result in sorted(results, key=lambda r: r["throughput_per_sec"], reverse=True):
            config = result["config_name"]
            throughput = result["throughput_per_sec"]
            latency = result["avg_latency_ms"]
            success = 100 - result["errors_pct"]

            marker = "🏆 WINNER" if config == winner["config_name"] else "  "
            logger.info(
                f"{marker} {config:20} | "
                f"{throughput:6.1f} req/s | "
                f"{latency:7.1f}ms | "
                f"{success:5.1f}% success"
            )

        # Log speedup
        if len(results) > 1:
            current = next((r for r in results if "current" in r["config_name"]), None)
            if current and winner["config_name"] != current["config_name"]:
                speedup = winner["throughput_per_sec"] / current["throughput_per_sec"]
                logger.info(
                    f"\n🚀 Speedup: {winner['config_name']} is {speedup:.1f}x faster "
                    f"than {current['config_name']}"
                )

        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error parsing results: {e}")


def main():
    """Entry point."""
    success = run_benchmark()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
