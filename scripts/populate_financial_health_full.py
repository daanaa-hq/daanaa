#!/usr/bin/env python3
"""
Full-scale financial health population (Phase 11)

Scores every org with financial data, computes per-org peer benchmarks
within (NTEE1 x size band) peer groups.

Designed for the overnight window on the home server. Batched writes,
progress logging, resumable (INSERT OR REPLACE keyed on ein).
"""
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "merit_registry.db"
BATCH_SIZE = 5000
LOG_EVERY = 25000


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def classify_fallback(reserves_months, operating_margin):
    """Fallback heuristic for orgs without a v5 signal.

    Never assigns CRISIS: per Charter Article 7 and Stewardship P5, a
    single-year operating-margin proxy is not enough evidence to put a
    crisis label on an organization. CAUTION is the floor, and it means
    "look closer," not "they failed."
    """
    if reserves_months >= 6 and operating_margin > 0.05:
        return "HEALTHY", 0.70
    if reserves_months >= 3 or operating_margin >= 0.02:
        return "STABLE", 0.60
    return "CAUTION", 0.55


def score_all_orgs(db):
    """Score every org that has both revenue and expenses on file.

    Source of truth for health_signal is merit_health_signal_v5 (the
    validated v5 scorer). The local heuristic only fills in where v5 has
    no signal, at reduced confidence.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    total = db.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE total_revenue > 0 AND total_expenses > 0"
    ).fetchone()[0]
    log(f"Scoring financial health for {total:,} orgs")

    cur = db.execute(
        """SELECT EIN, total_revenue, total_expenses, merit_health_signal_v5
           FROM registry_enriched
           WHERE total_revenue > 0 AND total_expenses > 0"""
    )

    processed = 0
    batch = []
    while True:
        rows = cur.fetchmany(BATCH_SIZE)
        if not rows:
            break
        for ein, revenue, expenses, v5_signal in rows:
            operating_margin = (revenue - expenses) / revenue
            reserves_months = (revenue - expenses) * 12 / expenses
            if v5_signal in ("HEALTHY", "STABLE", "CAUTION"):
                signal, confidence = v5_signal, 0.85
            else:
                signal, confidence = classify_fallback(reserves_months, operating_margin)
            batch.append((ein, now, reserves_months, signal, confidence))
        db.executemany(
            """INSERT OR REPLACE INTO nonprofit_financial_health
               (ein, assessment_date, reserve_ratio, reserve_months_ideal,
                health_signal, signal_confidence)
               VALUES (?, ?, ?, 6.0, ?, ?)""",
            batch,
        )
        db.commit()
        processed += len(batch)
        batch = []
        if processed % LOG_EVERY < BATCH_SIZE:
            log(f"  health: {processed:,}/{total:,}")

    log(f"✅ Financial health scored: {processed:,} orgs")
    return processed


def compute_per_org_benchmarks(db):
    """Per-org reserve-ratio rank within (NTEE1 x revenue band) peer group.

    Only writes benchmarks for peer groups with >= 20 members so small
    cells don't produce misleading ranks (P4: small-org fairness).
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    db.execute("DELETE FROM peer_benchmarking WHERE metric_type = 'reserve_ratio'")
    db.commit()

    groups = db.execute(
        """SELECT re.NTEE1, re.merit_band_v5_label, COUNT(*)
           FROM nonprofit_financial_health fh
           JOIN registry_enriched re ON re.EIN = fh.ein
           WHERE re.NTEE1 IS NOT NULL AND re.merit_band_v5_label IS NOT NULL
           GROUP BY re.NTEE1, re.merit_band_v5_label
           HAVING COUNT(*) >= 20"""
    ).fetchall()
    log(f"Benchmarking {len(groups)} peer groups (NTEE1 x size band, min 20 members)")

    total_written = 0
    for ntee, band, count in groups:
        members = db.execute(
            """SELECT fh.ein, fh.reserve_ratio
               FROM nonprofit_financial_health fh
               JOIN registry_enriched re ON re.EIN = fh.ein
               WHERE re.NTEE1 = ? AND re.merit_band_v5_label = ?
               ORDER BY fh.reserve_ratio ASC""",
            (ntee, band),
        ).fetchall()

        values = [m[1] for m in members]
        n = len(values)
        median = values[n // 2]
        p25 = values[n // 4]
        p75 = values[(3 * n) // 4]
        group_name = f"{ntee}|{band}"

        batch = []
        for rank, (ein, value) in enumerate(members, start=1):
            if value >= median:
                interp = "Your reserves are at or above the peer median"
            elif value >= p25:
                interp = "Your reserves are below the peer median"
            else:
                interp = "Your reserves are in the bottom quartile of peers"
            batch.append(
                (ein, group_name, "reserve_ratio", value, median, p25, p75,
                 rank, n, interp, now)
            )
        db.executemany(
            """INSERT INTO peer_benchmarking
               (ein, peer_group, metric_type, your_value, peer_median,
                peer_25th_percentile, peer_75th_percentile, your_rank,
                peer_total, interpretation, benchmarked_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )
        db.commit()
        total_written += len(batch)

    log(f"✅ Per-org benchmarks written: {total_written:,} rows across {len(groups)} groups")
    return total_written


def main():
    start = time.time()
    log("=== Full-scale financial health pipeline ===")
    db = sqlite3.connect(DB_PATH)
    try:
        scored = score_all_orgs(db)
        benchmarked = compute_per_org_benchmarks(db)
    finally:
        db.close()
    mins = (time.time() - start) / 60
    log(f"=== Done in {mins:.1f} min — {scored:,} scored, {benchmarked:,} benchmarks ===")


if __name__ == "__main__":
    main()
