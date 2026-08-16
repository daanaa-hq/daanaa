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


def create_scraper_config(name: str, fetch_func: Callable, batch_func: Callable = None) -> dict:
    """Register a scraper configuration.

    fetch_func: sync single-URL fetcher, used by the serial harness.
    batch_func: optional batch runner(test_orgs, deadline_sec) ->
        (successful, failed, skipped, latencies_ms). When present it is used
        instead of the serial loop — this is how concurrent scrapers
        (threads, asyncio) get measured at their real throughput. The
        2026-07-06 run rated "aiohttp" at 100% failure because the serial
        harness called the coroutine without awaiting it; and it rated the
        threaded scraper at serial speed because it never ran the threads.
    """
    return {
        "name": name,
        "fetch_func": fetch_func,
        "batch_func": batch_func,
        "description": (fetch_func or batch_func).__doc__ or "No description"
    }


def make_thread_batch(fetch_func: Callable, workers: int = 16) -> Callable:
    """Batch runner: the sync fetcher at its real ThreadPool concurrency."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def batch(test_orgs, deadline_sec):
        successful = failed = 0
        latencies = []
        start = time.time()

        def one(website):
            t0 = time.time()
            status, body = fetch_func(website)
            return status, body, (time.time() - t0) * 1000

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(one, w): ein for ein, w in test_orgs}
            done = 0
            for fut in as_completed(futs):
                done += 1
                try:
                    status, body, lat = fut.result()
                    if status == 200 and body:
                        successful += 1
                        latencies.append(lat)
                    else:
                        failed += 1
                except Exception:
                    failed += 1
                if done % 100 == 0:
                    rate = done / (time.time() - start)
                    print(f"   [{done}/{len(test_orgs)}] ok={successful} fail={failed} {rate:.1f}/s")
                if time.time() - start > deadline_sec:
                    for f in futs:
                        f.cancel()
                    break
        skipped = len(test_orgs) - successful - failed
        return successful, failed, max(skipped, 0), latencies

    batch.__doc__ = f"{fetch_func.__doc__ or ''} (ThreadPool x{workers})"
    return batch


def make_aiohttp_batch(concurrency: int = 32) -> Callable:
    """Batch runner: the async fetcher on a real event loop with a semaphore."""
    import asyncio
    import aiohttp
    from fetch_org_websites_async import fetch_url as async_fetch, UA, TIMEOUT

    def batch(test_orgs, deadline_sec):
        async def run():
            successful = failed = 0
            latencies = []
            start = time.time()
            sem = asyncio.Semaphore(concurrency)
            from fetch_org_websites_async import make_connector
            connector = make_connector(concurrency)
            done = 0

            async def one(website):
                async with sem:
                    t0 = time.time()
                    status, body = await async_fetch(website, session)
                    return status, body, (time.time() - t0) * 1000

            async with aiohttp.ClientSession(connector=connector) as session:
                tasks = [asyncio.create_task(one(w)) for _, w in test_orgs]
                for fut in asyncio.as_completed(tasks):
                    nonlocal_vars = None  # py<3.12 closure clarity
                    try:
                        status, body, lat = await fut
                        if status == 200 and body:
                            successful += 1
                            latencies.append(lat)
                        else:
                            failed += 1
                    except Exception:
                        failed += 1
                    done += 1
                    if done % 100 == 0:
                        rate = done / (time.time() - start)
                        print(f"   [{done}/{len(test_orgs)}] ok={successful} fail={failed} {rate:.1f}/s")
                    if time.time() - start > deadline_sec:
                        for t in tasks:
                            t.cancel()
                        break
            skipped = len(test_orgs) - successful - failed
            return successful, failed, max(skipped, 0), latencies

        return asyncio.run(run())

    batch.__doc__ = f"aiohttp async fetcher (semaphore x{concurrency})"
    return batch


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

    # Concurrent scrapers measure through their batch runner — the serial
    # loop below systematically under-reports them (see create_scraper_config).
    if config.get("batch_func"):
        start_time = time.time()
        successful, failed, skipped, total_latencies = config["batch_func"](test_orgs, timeout_sec)
        duration = time.time() - start_time
        avg_latency = sum(total_latencies) / len(total_latencies) if total_latencies else 0
        return BenchmarkResult(
            config_name=config_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_orgs=len(test_orgs),
            successful=successful,
            failed=failed,
            skipped=skipped,
            duration_sec=round(duration, 2),
            throughput_per_sec=0,
            errors_pct=0,
            avg_latency_ms=round(avg_latency, 2)
        )

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
        "current": create_scraper_config("current (requests, serial)", current_fetch),
        "threads16": create_scraper_config(
            "current + ThreadPool x16", current_fetch,
            batch_func=make_thread_batch(current_fetch, workers=16)),
        "threads32": create_scraper_config(
            "current + ThreadPool x32", current_fetch,
            batch_func=make_thread_batch(current_fetch, workers=32)),
    }

    try:
        import fetch_org_websites_async  # noqa: F401 — availability probe
        configs["aiohttp32"] = create_scraper_config(
            "aiohttp async x32", None, batch_func=make_aiohttp_batch(32))
        configs["aiohttp64"] = create_scraper_config(
            "aiohttp async x64", None, batch_func=make_aiohttp_batch(64))
    except ImportError:
        pass  # aiohttp not installed

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
