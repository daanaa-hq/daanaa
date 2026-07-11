#!/usr/bin/env python3
"""Sample-check canonical Daanaa org URLs without changing the site."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "visibility" / "public" / "data" / "orgs.csv"
DEFAULT_REPORT = ROOT / "visibility" / "reports" / "production-url-audit.json"


def iter_urls(csv_path: Path, limit: int):
    with csv_path.open(newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if i >= limit:
                break
            yield row["ein"], row["profile_url"]


def check_url(url: str, timeout: float) -> dict[str, object]:
    req = Request(url, headers={"User-Agent": "DaanaaVisibilityAudit/1.0"})
    started = time.time()
    try:
        with urlopen(req, timeout=timeout) as resp:
            return {
                "status": resp.status,
                "ok": 200 <= resp.status < 400,
                "elapsed_ms": round((time.time() - started) * 1000),
                "final_url": resp.geturl(),
            }
    except HTTPError as e:
        return {
            "status": e.code,
            "ok": False,
            "elapsed_ms": round((time.time() - started) * 1000),
            "error": str(e),
        }
    except URLError as e:
        return {
            "status": None,
            "ok": False,
            "elapsed_ms": round((time.time() - started) * 1000),
            "error": str(e.reason),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample-check Daanaa org profile URLs.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--sleep", type=float, default=0.1)
    args = parser.parse_args()

    results = []
    for ein, url in iter_urls(args.csv, args.limit):
        result = {"ein": ein, "url": url}
        result.update(check_url(url, args.timeout))
        results.append(result)
        print(f"{ein} {result['status']} {url}")
        if args.sleep:
            time.sleep(args.sleep)

    ok = sum(1 for r in results if r["ok"])
    report = {
        "csv": str(args.csv),
        "checked": len(results),
        "ok": ok,
        "failed": len(results) - ok,
        "results": results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.report}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

