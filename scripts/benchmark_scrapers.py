#!/usr/bin/env python3
"""
benchmark_scrapers.py — Pluggable framework for comparing web scraper implementations.

Runs multiple fetcher configurations (current, aiohttp, future: Colly, etc.)
on the same org set, measures throughput/latency/errors, logs results.

Results saved to: data/scraper_benchmarks/{timestamp}.json
Dashboard: docs/SCRAPER_BENCHMARKS.md (auto-updated)

Usage:
    python3 scripts/benchmark_scrapers.py --limit 1000 --configs current aiohttp
    python3 scripts/benchmark_scrapers.py --all-configs  # Run all registered scrapers
"""

import json
import sqlite3
import time
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Callable, List, Tuple
import hashlib

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
BENCHMARK_DIR = Path.home() / "meritgiving/data/scraper_benchmarks"
RESULTS_FILE = Path.home() / "meritgiving/docs/SCRAPER_BENCHMARKS.md"

BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class BenchmarkResult:
    """Single benchmark run result."""
    config_name: str
    timestamp: str
    total_orgs: int
    successful: int
    failed: int
    skipped: int
    duration_sec: float
    throughput_per_sec: float
    errors_pct: float
    avg_latency_ms: float

    def __post_init__(self):
        self.throughput_per_sec = round(self.successful / self.duration_sec, 2) if self.duration_sec > 0 else 0
        self.errors_pct = round((self.failed / self.total_orgs * 100), 2) if self.total_orgs > 0 else 0


def get_test_orgs(limit: int = 100) -> List[Tuple[str, str]]:
    """Fetch org EINs and websites for benchmarking."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT EIN, website
        FROM registry_enriched
        WHERE website_status = 'ok'
        AND website IS NOT NULL
        AND website != ''
        ORDER BY merit_score DESC NULLS LAST
        LIMIT ?
    """

    rows = [(r["EIN"], r["website"]) for r in conn.execute(query, [limit])]
    conn.close()
    return rows


def create_scraper_config(name: str, fetch_func: Callable) -> dict:
    """Register a scraper configuration."""
    return {
        "name": name,
        "fetch_func": fetch_func,
        "description": fetch_func.__doc__ or "No description"
    }


def run_benchmark(
    config: dict,
    test_orgs: List[Tuple[str, str]],
    timeout_sec: float = 300
) -> BenchmarkResult:
    """
    Run a single benchmark configuration.

    Args:
        config: Dict with 'name' and 'fetch_func'
        test_orgs: List of (EIN, website) tuples
        timeout_sec: Max time to spend on this config

    Returns:
        BenchmarkResult with throughput/latency/error stats
    """
    config_name = config["name"]
    fetch_func = config["fetch_func"]

    print(f"\n📊 Benchmarking: {config_name}")
    print(f"   Orgs to fetch: {len(test_orgs)}")

    successful = 0
    failed = 0
    skipped = 0
    total_latencies = []
    start_time = time.time()

    for i, (ein, website) in enumerate(test_orgs):
        if time.time() - start_time > timeout_sec:
            skipped = len(test_orgs) - i
            print(f"   ⏱️  Timeout reached ({timeout_sec}s), skipping {skipped} remaining orgs")
            break

        try:
            fetch_start = time.time()
            status, html_bytes = fetch_func(website)
            fetch_latency = (time.time() - fetch_start) * 1000  # ms

            if status == 200 and html_bytes:
                successful += 1
                total_latencies.append(fetch_latency)
            else:
                failed += 1

            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"   [{i+1}/{len(test_orgs)}] ok={successful} fail={failed} {rate:.1f}/s")

        except Exception as e:
            failed += 1
            if i < 5:  # Log first few errors
                print(f"   Error on {ein}: {str(e)[:100]}")

    duration = time.time() - start_time
    avg_latency = sum(total_latencies) / len(total_latencies) if total_latencies else 0

    result = BenchmarkResult(
        config_name=config_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_orgs=len(test_orgs),
        successful=successful,
        failed=failed,
        skipped=skipped,
        duration_sec=round(duration, 2),
        throughput_per_sec=0,  # Set in __post_init__
        errors_pct=0,  # Set in __post_init__
        avg_latency_ms=round(avg_latency, 2)
    )

    print(f"   ✅ Done: {result.successful}/{len(test_orgs)} ok, {result.throughput_per_sec}/s, {result.avg_latency_ms}ms avg")

    return result


def save_results(results: List[BenchmarkResult]):
    """Save benchmark results to JSON."""
    timestamp = datetime.now(timezone.utc).isoformat()
    filename = BENCHMARK_DIR / f"benchmark_{timestamp.replace(':', '-')}.json"

    data = {
        "timestamp": timestamp,
        "results": [asdict(r) for r in results]
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n💾 Results saved: {filename}")
    return filename


def load_all_results() -> dict:
    """Load all benchmark results for dashboard generation."""
    all_results = {}

    for json_file in sorted(BENCHMARK_DIR.glob("benchmark_*.json")):
        try:
            with open(json_file) as f:
                data = json.load(f)
                timestamp = data["timestamp"]

                for result in data["results"]:
                    config_name = result["config_name"]
                    if config_name not in all_results:
                        all_results[config_name] = []

                    result["timestamp"] = timestamp
                    all_results[config_name].append(result)
        except Exception as e:
            print(f"Warning: couldn't load {json_file}: {e}")

    return all_results


def generate_dashboard(results: dict):
    """Generate Markdown dashboard of all benchmarks."""
    if not results:
        print("No results to display yet.")
        return

    md_lines = [
        "# Scraper Benchmark Results\n",
        "Nightly performance tracking of web scraper implementations.\n",
        "Auto-updated daily. Compare configurations to identify optimizations.\n",
        ""
    ]

    # Summary table
    md_lines.append("## Latest Run Summary\n")
    md_lines.append("| Config | Throughput (/s) | Avg Latency (ms) | Success Rate | Duration (s) |")
    md_lines.append("|--------|-----------------|------------------|--------------|--------------|")

    latest_by_config = {}
    for config_name, runs in results.items():
        if runs:
            latest = runs[-1]  # Most recent
            latest_by_config[config_name] = latest

            success_rate = f"{100 - latest['errors_pct']:.1f}%"
            md_lines.append(
                f"| {config_name} | {latest['throughput_per_sec']} | "
                f"{latest['avg_latency_ms']} | {success_rate} | {latest['duration_sec']} |"
            )

    md_lines.append("")

    # Trends
    md_lines.append("## Performance Trends\n")
    for config_name, runs in results.items():
        if len(runs) > 1:
            latest_throughput = runs[-1]["throughput_per_sec"]
            prev_throughput = runs[-2]["throughput_per_sec"]
            delta = latest_throughput - prev_throughput
            direction = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"

            md_lines.append(
                f"**{config_name}**: {latest_throughput}/s {direction} "
                f"({delta:+.2f}/s vs previous run)"
            )

    md_lines.append("")

    # Full history
    md_lines.append("## Full History\n")
    for config_name in sorted(results.keys()):
        runs = results[config_name]
        md_lines.append(f"\n### {config_name}\n")
        md_lines.append("| Timestamp | Throughput | Latency | Success | Duration |")
        md_lines.append("|-----------|-----------|---------|---------|----------|")

        for run in sorted(runs, key=lambda r: r["timestamp"], reverse=True)[:20]:  # Last 20
            ts = run["timestamp"][:10]  # Date only
            md_lines.append(
                f"| {ts} | {run['throughput_per_sec']}/s | "
                f"{run['avg_latency_ms']}ms | {100-run['errors_pct']:.1f}% | "
                f"{run['duration_sec']}s |"
            )

    md_lines.append("\n*Last updated: " + datetime.now(timezone.utc).isoformat() + "*\n")

    dashboard_content = "\n".join(md_lines)

    with open(RESULTS_FILE, "w") as f:
        f.write(dashboard_content)

    print(f"\n📊 Dashboard updated: {RESULTS_FILE}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100, help="Number of orgs to benchmark")
    parser.add_argument("--configs", nargs="+", default=["current"],
                       help="Configs to run: current, aiohttp, etc.")
    parser.add_argument("--all-configs", action="store_true", help="Run all registered scrapers")
    parser.add_argument("--dashboard-only", action="store_true", help="Just generate dashboard from existing results")
    parser.add_argument("--timeout", type=float, default=300, help="Max seconds per config")

    args = parser.parse_args()

    # If dashboard-only, skip benchmarking
    if args.dashboard_only:
        all_results = load_all_results()
        generate_dashboard(all_results)
        return

    # Load test orgs
    test_orgs = get_test_orgs(args.limit)
    if not test_orgs:
        print("No test orgs found. Check database.")
        sys.exit(1)

    print(f"✅ Loaded {len(test_orgs)} test orgs for benchmarking")

    # Import scraper implementations (will be created separately)
    from fetch_org_websites import fetch_url as current_fetch

    configs = {
        "current": create_scraper_config("current (requests + threads)", current_fetch),
    }

    # aiohttp variant will be added here when created
    try:
        from fetch_org_websites_async import fetch_url as async_fetch
        configs["aiohttp"] = create_scraper_config("aiohttp (async)", async_fetch)
    except ImportError:
        pass  # Not available yet

    # Filter configs
    if args.all_configs:
        requested_configs = list(configs.keys())
    else:
        requested_configs = args.configs

    to_run = {k: configs[k] for k in requested_configs if k in configs}

    if not to_run:
        print(f"❌ No valid configs. Available: {list(configs.keys())}")
        sys.exit(1)

    print(f"📊 Running {len(to_run)} configurations...\n")

    # Run benchmarks
    results = []
    for config_name, config in to_run.items():
        result = run_benchmark(config, test_orgs, timeout_sec=args.timeout)
        results.append(result)

    # Save and display results
    save_results(results)

    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    for result in results:
        print(f"\n{result.config_name}")
        print(f"  Throughput: {result.throughput_per_sec} req/sec")
        print(f"  Latency: {result.avg_latency_ms}ms avg")
        print(f"  Success: {100 - result.errors_pct:.1f}%")
        print(f"  Duration: {result.duration_sec}s")

    # Generate dashboard from all historical results
    all_results = load_all_results()
    generate_dashboard(all_results)

    print("\n✅ Benchmark complete. Review dashboard: docs/SCRAPER_BENCHMARKS.md")


if __name__ == "__main__":
    main()
