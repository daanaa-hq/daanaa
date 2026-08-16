#!/usr/bin/env python3
"""
scripts/discovery/backfill_990_functional_expenses.py

Recovers trustworthy program/management/fundraising expense figures from
raw 990 XML Part IX (Statement of Functional Expenses), following the same
mechanics as scripts/discovery/expand_990_coverage.py (gt990 S3 index ->
download XML -> parse).

Writes to the new irs_990_functional_expense_filings table (migration 023)
ONLY -- never touches registry_enriched.program_expenses/management_expenses/
fundraising_expenses/program_expense_pct (confirmed unreliable at scale,
see DECISIONS.md 2026-08-16). Additive evidence table; those legacy columns
are not promoted from here without a separate, founder-reviewed migration.

Validated the XML path against a real filing before building this (EIN
521231983, FY2024): IRS990/TotalFunctionalExpensesGrp/{TotalAmt,
ProgramServicesAmt, ManagementAndGeneralAmt, FundraisingAmt}. Reconciled
exactly (Program $51,615,477 + Management $1,254,773 + Fundraising
$1,636,384 = Total $54,506,634).

Usage:
    python3 scripts/discovery/backfill_990_functional_expenses.py --limit 50 --workers 8
    python3 scripts/discovery/backfill_990_functional_expenses.py --min-revenue 10000000 --workers 12
"""
import argparse
import csv
import sqlite3
import threading
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from queue import Queue, Empty

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
GT990_LATEST = Path.home() / "meritgiving" / "data" / "cache" / "gt990_latest.csv"
NS = "http://www.irs.gov/efile"
PARSER_VERSION = "1.0-2026-08-16"
RECONCILE_TOLERANCE = 1.0  # dollars


def build_candidate_filings(min_revenue: float, limit: int | None) -> list[dict]:
    """Scan gt990_latest.csv, keep the newest Form 990 (not EZ/PF) per EIN,
    scoped to orgs in registry_enriched at/above min_revenue."""
    db = sqlite3.connect(DB_PATH)
    known = {
        r[0].zfill(9)
        for r in db.execute(
            "SELECT EIN FROM registry_enriched WHERE total_revenue >= ?", (min_revenue,)
        ).fetchall()
    }
    db.close()
    print(f"Candidate pool: {len(known):,} EINs (revenue >= ${min_revenue:,.0f})")

    best: dict[str, dict] = {}
    with open(GT990_LATEST, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ein = (row.get("EIN") or "").strip().zfill(9)
            if ein not in known:
                continue
            if (row.get("FormType") or "").strip() != "990":
                continue
            url = (row.get("URL") or "").strip()
            if not url:
                continue
            try:
                year = int((row.get("TaxYear") or "0").strip())
            except ValueError:
                year = 0
            prev = best.get(ein)
            if prev is None or year > prev["year"]:
                best[ein] = {
                    "ein": ein, "year": year, "url": url,
                    "object_id": (row.get("ObjectId") or "").strip(),
                    "sha256": (row.get("FileSha256") or "").strip(),
                }

    tasks = list(best.values())
    if limit:
        tasks.sort(key=lambda t: -1)  # stable order; caller controls scope via min_revenue
        tasks = tasks[:limit]
    print(f"Matched {len(tasks):,} newest-Form-990 filings")
    return tasks


def parse_functional_expenses(xml_path_or_bytes) -> dict | None:
    try:
        root = ET.fromstring(xml_path_or_bytes)
    except ET.ParseError:
        return None

    irs990 = root.find(f".//{{{NS}}}IRS990")
    if irs990 is None:
        return None
    grp = irs990.find(f".//{{{NS}}}TotalFunctionalExpensesGrp")
    if grp is None:
        return None

    def get_amt(tag):
        el = grp.find(f"{{{NS}}}{tag}")
        if el is None or not el.text:
            return None
        try:
            return float(el.text.strip())
        except ValueError:
            return None

    total = get_amt("TotalAmt")
    program = get_amt("ProgramServicesAmt")
    mgmt = get_amt("ManagementAndGeneralAmt")
    fundraising = get_amt("FundraisingAmt")

    return {
        "total_amt": total,
        "program_services_amt": program,
        "management_general_amt": mgmt,
        "fundraising_amt": fundraising,
    }


def fetch_and_parse(task: dict) -> dict | None:
    try:
        req = urllib.request.Request(task["url"], headers={"User-Agent": "Daanaa/1.0 data-pipeline"})
        with urllib.request.urlopen(req, timeout=30) as r:
            content = r.read()
    except Exception:
        return None

    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]

    parsed = parse_functional_expenses(content)
    if parsed is None:
        return None

    result = {**task, **parsed}
    return result


def worker_thread(task_q: Queue, result_q: Queue, stop: threading.Event):
    while not stop.is_set():
        try:
            task = task_q.get(timeout=1)
        except Empty:
            continue
        result = fetch_and_parse(task)
        result_q.put(result if result else {"ein": task["ein"], "failed": True})
        task_q.task_done()
        time.sleep(0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-revenue", type=float, default=10_000_000,
                     help="Only consider orgs at/above this revenue (default $10M -- highest-visibility orgs first)")
    ap.add_argument("--limit", type=int, default=None, help="Cap number of filings processed")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    tasks = build_candidate_filings(args.min_revenue, args.limit)
    if not tasks:
        print("No candidates.")
        return

    task_q: Queue = Queue()
    result_q: Queue = Queue()
    stop = threading.Event()
    for t in tasks:
        task_q.put(t)

    threads = [threading.Thread(target=worker_thread, args=(task_q, result_q, stop), daemon=True)
               for _ in range(args.workers)]
    for t in threads:
        t.start()

    db = sqlite3.connect(DB_PATH, timeout=60)
    now = datetime.now(timezone.utc).isoformat()
    processed = 0
    fetched_ok = 0
    reconciled = 0
    t0 = time.time()

    while processed < len(tasks):
        try:
            r = result_q.get(timeout=60)
        except Empty:
            print("Result queue timeout -- workers may be stalled")
            continue
        processed += 1

        if r.get("failed") or r.get("total_amt") is None:
            continue
        fetched_ok += 1

        total = r["total_amt"]
        program = r.get("program_services_amt") or 0
        mgmt = r.get("management_general_amt") or 0
        fundraising = r.get("fundraising_amt") or 0
        parts_sum = program + mgmt + fundraising
        reconciles = 1 if (total and abs(parts_sum - total) <= RECONCILE_TOLERANCE) else 0
        if reconciles:
            reconciled += 1
        status = "accepted" if reconciles else "rejected"
        reason = None if reconciles else f"parts_sum={parts_sum:.2f} vs total={total:.2f}"

        db.execute(
            "INSERT OR REPLACE INTO irs_990_functional_expense_filings "
            "(EIN, tax_year, object_id, source_url, file_sha256, total_amt, "
            "program_services_amt, management_general_amt, fundraising_amt, "
            "reconciles, validation_status, rejection_reason, parser_version, extracted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (r["ein"], r["year"], r["object_id"], r["url"], r["sha256"],
             total, program, mgmt, fundraising, reconciles, status, reason,
             PARSER_VERSION, now)
        )
        if processed % 200 == 0:
            db.commit()
            elapsed = time.time() - t0
            rate = processed / elapsed * 60
            print(f"[{processed:,}/{len(tasks):,}] fetched={fetched_ok:,} reconciled={reconciled:,} "
                  f"({rate:.0f}/min)")

    db.commit()
    stop.set()

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s.")
    print(f"  Processed:  {processed:,}")
    print(f"  Fetched OK: {fetched_ok:,}")
    print(f"  Reconciled: {reconciled:,} ({100*reconciled/max(fetched_ok,1):.1f}% of fetched)")
    db.close()


if __name__ == "__main__":
    main()
