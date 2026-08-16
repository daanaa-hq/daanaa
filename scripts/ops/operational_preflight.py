#!/usr/bin/env python3
"""Read-only operational preflight for the local Daanaa environment.

No migration, restart, deployment, backup pruning, or file mutation occurs.
The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sqlite3
import time
from pathlib import Path
from shutil import disk_usage
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def http_json(url: str, timeout: float = 5.0) -> tuple[int, object, float]:
    started = time.perf_counter()
    request = Request(url, headers={"User-Agent": "daanaa-operational-preflight/1"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        elapsed = (time.perf_counter() - started) * 1000
        return response.status, json.loads(body.decode("utf-8")), elapsed


def check_database(db_path: Path, full_integrity: bool) -> dict:
    result = {"path": str(db_path), "ok": False}
    if not db_path.is_file():
        result["error"] = "database file not found"
        return result
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
        integrity_sql = "PRAGMA integrity_check" if full_integrity else "PRAGMA quick_check"
        integrity = conn.execute(integrity_sql).fetchone()[0]
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"registry_enriched", "org_fts"}
        registry_rows = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0] if "registry_enriched" in tables else None
        fts_rows = conn.execute("SELECT COUNT(*) FROM org_fts").fetchone()[0] if "org_fts" in tables else None
        indexes = [row[1] for row in conn.execute("PRAGMA index_list('registry_enriched')")]
        conn.close()
        result.update({
            "ok": integrity == "ok" and required <= tables,
            "integrity_check": integrity,
            "integrity_mode": "full" if full_integrity else "quick",
            "required_tables_present": sorted(required & tables),
            "missing_tables": sorted(required - tables),
            "registry_rows": registry_rows,
            "fts_rows": fts_rows,
            "registry_indexes": indexes,
        })
    except Exception as exc:
        result["error"] = str(exc)
    return result


def benchmark_search(api_url: str, queries: list[str], iterations: int) -> dict:
    measurements = []
    failures = []
    for query in queries:
        samples = []
        for _ in range(iterations):
            url = f"{api_url.rstrip('/')}/api/search?{urlencode({'q': query, 'per_page': 5})}"
            try:
                status, payload, elapsed = http_json(url)
                if status != 200:
                    failures.append({"query": query, "status": status})
                else:
                    samples.append(elapsed)
                    if not isinstance(payload, (dict, list)):
                        failures.append({"query": query, "error": "unexpected JSON shape"})
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                failures.append({"query": query, "error": str(exc)})
        if samples:
            ordered = sorted(samples)
            p95_index = min(len(ordered) - 1, max(0, int(len(ordered) * 0.95) - 1))
            measurements.append({
                "query": query,
                "iterations": len(samples),
                "min_ms": round(min(samples), 2),
                "p50_ms": round(statistics.median(samples), 2),
                "p95_ms": round(ordered[p95_index], 2),
                "max_ms": round(max(samples), 2),
            })
    all_samples = [item["p50_ms"] for item in measurements]
    return {
        "ok": bool(measurements) and not failures,
        "api_url": api_url,
        "queries": measurements,
        "failures": failures,
        "overall_p50_ms": round(statistics.median(all_samples), 2) if all_samples else None,
        "overall_p95_ms": round(sorted(all_samples)[min(len(all_samples) - 1, max(0, int(len(all_samples) * 0.95) - 1))], 2) if all_samples else None,
    }


def run(args: argparse.Namespace) -> dict:
    usage = disk_usage(args.root)
    free_gib = usage.free / (1024 ** 3)
    database = check_database(args.db, args.full_integrity)
    api = {"ok": False}
    try:
        status, payload, elapsed = http_json(f"{args.api_url.rstrip('/')}/health")
        api = {"ok": status == 200, "status": status, "elapsed_ms": round(elapsed, 2), "response": payload}
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        api = {"ok": False, "error": str(exc)}
    search = benchmark_search(args.api_url, args.queries, args.iterations) if args.search else {"ok": True, "skipped": True}
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "database": database,
        "disk": {"root": str(args.root), "free_gib": round(free_gib, 2), "free_percent": round(usage.free / usage.total * 100, 2), "minimum_free_gib": args.min_free_gib, "ok": free_gib >= args.min_free_gib},
        "api": api,
        "search": search,
        "ok": database["ok"] and api["ok"] and search["ok"] and free_gib >= args.min_free_gib,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Daanaa operational preflight")
    parser.add_argument("--db", type=Path, default=Path("data/merit_registry.db"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--api-url", default="http://127.0.0.1:5000")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--min-free-gib", type=float, default=10.0)
    parser.add_argument("--full-integrity", action="store_true")
    parser.add_argument("--no-search", action="store_false", dest="search")
    parser.set_defaults(search=True)
    parser.add_argument("--queries", nargs="+", default=["health", "food bank", "xyz123notreal"])
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run(args)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
        print("PREFLIGHT: PASS" if report["ok"] else "PREFLIGHT: REVIEW REQUIRED")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
