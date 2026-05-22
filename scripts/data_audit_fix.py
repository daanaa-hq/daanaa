#!/usr/bin/env python3
"""
Data Audit & Fix — registry_enriched
Passes:
  1. Clear bad program_expense_pct (outside 0–100)
  2. Recompute months_of_reserve from net_assets / (total_expenses/12)
  3. Generate data/audit_report.json
  4. Flag contradictory scored rows

Usage:
  python3 scripts/data_audit_fix.py [--dry-run] [--verbose]
"""

import argparse, json, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH  = Path.home() / "meritgiving" / "data" / "merit_registry.db"
OUT_PATH = Path.home() / "meritgiving" / "data" / "audit_report.json"

RESERVE_CAP = 120   # months — anything beyond 10 years is clamped
PROGRESS_EVERY = 25_000


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def run(dry_run: bool, verbose: bool):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "passes": {}
    }

    # ── Pass 1: Clear bad program_expense_pct ──────────────────────────────
    print(f"[{ts()}] Pass 1 — clearing bad program_expense_pct...")
    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE program_expense_pct IS NOT NULL
          AND (program_expense_pct < 0 OR program_expense_pct > 100)
    """)
    bad_pct = cur.fetchone()[0]
    print(f"  Found {bad_pct:,} rows with program_expense_pct outside 0–100")

    if not dry_run:
        cur.execute("""
            UPDATE registry_enriched
            SET program_expense_pct = NULL
            WHERE program_expense_pct IS NOT NULL
              AND (program_expense_pct < 0 OR program_expense_pct > 100)
        """)
        conn.commit()
        print(f"  Nulled {cur.rowcount:,} rows")

    cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE program_expense_pct IS NOT NULL")
    remaining_pct = cur.fetchone()[0]
    cur.execute("""
        SELECT MIN(program_expense_pct), MAX(program_expense_pct), AVG(program_expense_pct)
        FROM registry_enriched WHERE program_expense_pct IS NOT NULL
    """)
    pmin, pmax, pavg = cur.fetchone()
    report["passes"]["program_expense_pct"] = {
        "bad_rows_cleared": bad_pct,
        "remaining_valid": remaining_pct,
        "range_after": {"min": pmin, "max": pmax, "avg": round(pavg or 0, 2)},
        "verdict": "CLEAN" if (pmin or 0) >= 0 and (pmax or 0) <= 100 else "STILL_DIRTY"
    }
    print(f"  After: {remaining_pct:,} valid rows, range [{pmin:.1f}, {pmax:.1f}]")

    # ── Pass 2: Recompute months_of_reserve ───────────────────────────────
    print(f"\n[{ts()}] Pass 2 — recomputing months_of_reserve from raw columns...")

    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE net_assets IS NOT NULL AND total_expenses > 0
    """)
    eligible = cur.fetchone()[0]
    print(f"  Eligible rows (have net_assets + total_expenses): {eligible:,}")

    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE (months_of_reserve IS NULL
               OR ABS(months_of_reserve) > ?)
          AND net_assets IS NOT NULL AND total_expenses > 0
    """, (RESERVE_CAP,))
    needs_fix = cur.fetchone()[0]
    print(f"  Rows to update (null or sentinel): {needs_fix:,}")

    updated = 0
    errors  = 0
    t0 = time.time()

    if not dry_run:
        # Batch fetch and update for speed
        cur2 = conn.cursor()
        cur.execute("""
            SELECT EIN, net_assets, total_expenses, months_of_reserve
            FROM registry_enriched
            WHERE (months_of_reserve IS NULL OR ABS(months_of_reserve) > ?)
              AND net_assets IS NOT NULL AND total_expenses > 0
        """, (RESERVE_CAP,))

        batch = []
        for row in cur:
            try:
                computed = row["net_assets"] / (row["total_expenses"] / 12.0)
                clamped  = max(-RESERVE_CAP, min(RESERVE_CAP, computed))
                batch.append((round(clamped, 2), row["EIN"]))
            except (ZeroDivisionError, TypeError):
                errors += 1
                continue

            if len(batch) >= 5000:
                cur2.executemany(
                    "UPDATE registry_enriched SET months_of_reserve = ? WHERE EIN = ?",
                    batch
                )
                conn.commit()
                updated += len(batch)
                if verbose:
                    elapsed = time.time() - t0
                    print(f"  {updated:,} updated ({elapsed:.0f}s)...")
                batch = []

        if batch:
            cur2.executemany(
                "UPDATE registry_enriched SET months_of_reserve = ? WHERE EIN = ?",
                batch
            )
            conn.commit()
            updated += len(batch)

        print(f"  Updated {updated:,} rows, {errors} errors, {time.time()-t0:.1f}s")

    # Stats after
    cur.execute("""
        SELECT MIN(months_of_reserve), MAX(months_of_reserve), AVG(months_of_reserve),
               COUNT(*) as total,
               SUM(CASE WHEN months_of_reserve < 0 THEN 1 ELSE 0 END) as negative,
               SUM(CASE WHEN ABS(months_of_reserve) > ? THEN 1 ELSE 0 END) as out_of_range
        FROM registry_enriched WHERE months_of_reserve IS NOT NULL
    """, (RESERVE_CAP,))
    rmin, rmax, ravg, rtotal, rneg, roor = cur.fetchone()
    report["passes"]["months_of_reserve"] = {
        "rows_updated": updated,
        "total_with_value": rtotal,
        "negative_count": rneg,
        "out_of_range_after": roor,
        "range_after": {"min": rmin, "max": rmax, "avg": round(ravg or 0, 1)},
        "verdict": "CLEAN" if roor == 0 else "STILL_HAS_OUTLIERS"
    }
    print(f"  After: {rtotal:,} rows, range [{rmin:.1f}, {rmax:.1f}], {roor} out-of-range remaining")

    # ── Pass 3: Full field coverage audit ────────────────────────────────
    print(f"\n[{ts()}] Pass 3 — generating audit report...")

    cur.execute("SELECT COUNT(*) FROM registry_enriched")
    total = cur.fetchone()[0]

    fields = [
        ("EIN",                "EIN IS NOT NULL"),
        ("organization_name",  "organization_name IS NOT NULL AND organization_name != ''"),
        ("STATE",              "STATE IS NOT NULL"),
        ("CITY",               "CITY IS NOT NULL"),
        ("NTEE1",              "NTEE1 IS NOT NULL"),
        ("ntee_description",   "ntee_description IS NOT NULL AND ntee_description != ''"),
        ("latest_tax_year",    "latest_tax_year IS NOT NULL"),
        ("total_revenue",      "total_revenue IS NOT NULL AND total_revenue > 0"),
        ("total_expenses",     "total_expenses IS NOT NULL AND total_expenses > 0"),
        ("total_assets",       "total_assets IS NOT NULL AND total_assets > 0"),
        ("net_assets",         "net_assets IS NOT NULL"),
        ("months_of_reserve",  "months_of_reserve IS NOT NULL"),
        ("merit_score",        "merit_score IS NOT NULL"),
        ("merit_band",         "merit_band IS NOT NULL"),
        ("merit_tier",         "merit_tier IS NOT NULL"),
        ("peer_percentile",    "peer_percentile IS NOT NULL"),
        ("score_tier",         "score_tier IS NOT NULL"),
        ("program_expense_pct","program_expense_pct IS NOT NULL"),
        ("mission",            "mission IS NOT NULL AND mission != ''"),
        ("website",            "website IS NOT NULL AND website != ''"),
        ("website_status",     "website_status IS NOT NULL"),
        ("donate_url",         "donate_url IS NOT NULL AND donate_url != ''"),
        ("cause_tags",         "cause_tags IS NOT NULL AND cause_tags != ''"),
        ("employee_count",     "employee_count IS NOT NULL AND employee_count > 0"),
    ]

    coverage = {}
    for field, condition in fields:
        cur.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {condition}")
        count = cur.fetchone()[0]
        pct   = round(count / total * 100, 1)
        coverage[field] = {"count": count, "pct": pct,
                           "status": "GOOD" if pct > 50 else "PARTIAL" if pct > 10 else "LOW"}

    report["coverage"] = coverage
    report["total_rows"] = total

    # ── Pass 4: Flag contradictions ───────────────────────────────────────
    print(f"[{ts()}] Pass 4 — checking for contradictions...")

    checks = {}

    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE score_tier = 'full' AND (total_revenue IS NULL OR total_revenue = 0)
    """)
    checks["full_score_no_revenue"] = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE merit_band IS NOT NULL AND merit_score IS NULL
    """)
    checks["band_without_score"] = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE ABS(months_of_reserve) > 120
    """)
    checks["months_reserve_sentinel_remaining"] = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE program_expense_pct IS NOT NULL
          AND (program_expense_pct < 0 OR program_expense_pct > 100)
    """)
    checks["bad_program_pct_remaining"] = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE website_status = 'ok'
          AND website IS NULL
    """)
    checks["status_ok_but_no_url"] = cur.fetchone()[0]

    report["contradictions"] = checks

    # ── Write report ──────────────────────────────────────────────────────
    with open(OUT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n[{ts()}] Audit report written to {OUT_PATH}")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for field, info in coverage.items():
        bar = "█" * int(info["pct"] / 5)
        print(f"  {field:<25} {info['pct']:5.1f}% {bar}")
    print("\nContradictions:")
    for k, v in checks.items():
        flag = "✓" if v == 0 else "⚠"
        print(f"  {flag} {k}: {v:,}")
    print(f"\n{'DRY RUN — no changes written' if dry_run else 'All changes committed.'}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",  action="store_true", help="Report only, no DB writes")
    p.add_argument("--verbose",  action="store_true", help="Show progress during updates")
    args = p.parse_args()
    run(dry_run=args.dry_run, verbose=args.verbose)
