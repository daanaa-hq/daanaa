#!/usr/bin/env python3
"""
scripts/compute_diamonds.py

Computes the durable "Hidden Gem" (diamond) signal from longitudinal IRS/990 data.
Replaces the shallow single-point flag with a multi-year eligibility check.

Eligibility requires ALL of:
  1. Median reserve months >= 4 across 3+ years (reserve = netassets / (expenses/12))
  2. Net assets > 0 in most recent 2 filing years
  3. Latest revenue >= 50% of median revenue, and median revenue > 0 (not in freefall)
  4. Latest total_revenue > 0 and < $500K (small org requirement)
  5. Ruling date >= 5 years ago (survived startup window)
  6. Program expense pct >= 70% (mission efficiency)
  7. cause_tags present (discoverable)

Writes:
  - registry_enriched.is_hidden_gem  (1/0)
  - registry_enriched.diamond_factors (JSON, for transparency — never shown as score)

Run: python3 scripts/compute_diamonds.py
     python3 scripts/compute_diamonds.py --dry-run   # report counts only, no writes
     python3 scripts/compute_diamonds.py --limit 10000  # test on first N EINs

Idempotent — safe to rerun after each scoring refresh.
"""

import sqlite3, json, argparse, statistics, datetime
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
CUTOFF_DATE = (datetime.date.today() - datetime.timedelta(days=5 * 365)).isoformat()
MAX_REVENUE = 500_000
MIN_RESERVE_MONTHS = 4
MIN_PROGRAM_PCT = 70.0
MIN_YEARS = 3


def _add_column_if_missing(db: sqlite3.Connection) -> None:
    cols = {r[1] for r in db.execute("PRAGMA table_info(registry_enriched)")}
    if "diamond_factors" not in cols:
        db.execute("ALTER TABLE registry_enriched ADD COLUMN diamond_factors TEXT")
        db.commit()
        print("[schema] added diamond_factors column")


def _load_financials(db: sqlite3.Connection, limit: int | None) -> dict:
    """Load propublica_financials grouped by EIN. Returns {EIN: [(yr, rev, exp, net), ...]}"""
    print("[load] reading propublica_financials …")
    query = """
        SELECT f.EIN, f.tax_prd_yr, f.totrevenue, f.totfuncexpns, f.totnetassetend
        FROM propublica_financials f
        INNER JOIN registry_enriched r ON r.EIN = f.EIN
        WHERE f.totfuncexpns > 0
          AND f.totnetassetend IS NOT NULL
          AND f.totrevenue IS NOT NULL
        ORDER BY f.EIN, f.tax_prd_yr
    """
    rows = db.execute(query).fetchall()
    print(f"[load] {len(rows):,} financial rows loaded")

    grouped: dict[str, list] = {}
    for ein, yr, rev, exp, net in rows:
        grouped.setdefault(ein, []).append((yr, rev, exp, net))

    # Filter to EINs with 3+ years
    eligible = {ein: yrs for ein, yrs in grouped.items() if len(yrs) >= MIN_YEARS}
    if limit:
        eligible = dict(list(eligible.items())[:limit])
    print(f"[load] {len(eligible):,} EINs with {MIN_YEARS}+ qualifying years")
    return eligible


def _load_registry(db: sqlite3.Connection) -> dict:
    """Load registry fields needed for criteria 4-7."""
    print("[load] reading registry_enriched fields …")
    rows = db.execute("""
        SELECT EIN, total_revenue, program_expense_pct, ruling_date, cause_tags
        FROM registry_enriched
    """).fetchall()
    return {r[0]: {"total_revenue": r[1], "program_pct": r[2],
                   "ruling_date": r[3], "cause_tags": r[4]}
            for r in rows}


def _compute(ein: str, years: list, reg: dict) -> tuple[bool, dict]:
    """
    Returns (is_diamond, factors_dict).
    factors_dict records each criterion result for transparency.
    """
    meta = reg.get(ein, {})
    factors: dict = {"ntee1": None}  # filled from caller

    # Sort years ascending
    years_sorted = sorted(years, key=lambda x: x[0])
    recent_two = years_sorted[-2:]

    # --- Criterion 1: median reserve months >= 4 ---
    reserve_months = []
    for _, rev, exp, net in years_sorted:
        if exp > 0:
            reserve_months.append(net / (exp / 12))
    if not reserve_months:
        return False, {}
    med_reserve = statistics.median(reserve_months)
    factors["median_reserve_months"] = round(med_reserve, 2)
    if med_reserve < MIN_RESERVE_MONTHS:
        factors["fail"] = "median_reserve_months"
        return False, factors

    # --- Criterion 2: net assets > 0 in most recent 2 years ---
    for yr, _, _, net in recent_two:
        if net <= 0:
            factors["fail"] = f"net_assets_nonpositive_{yr}"
            return False, factors
    factors["recent_net_assets_positive"] = True

    # --- Criterion 3: not in revenue freefall ---
    revenues = [r[1] for r in years_sorted if r[1] is not None]
    if not revenues:
        return False, {}
    med_rev = statistics.median(revenues)
    latest_rev = years_sorted[-1][1]
    factors["median_revenue"] = round(med_rev, 0)
    factors["latest_fin_revenue"] = round(latest_rev, 0)
    if med_rev <= 0 or latest_rev < 0.5 * med_rev:
        factors["fail"] = "revenue_freefall"
        return False, factors

    # --- Criterion 4: registry total_revenue > 0 and < $500K ---
    reg_revenue = meta.get("total_revenue") or 0
    factors["registry_revenue"] = reg_revenue
    if reg_revenue <= 0 or reg_revenue >= MAX_REVENUE:
        factors["fail"] = "revenue_out_of_range"
        return False, factors

    # --- Criterion 5: ruling date >= 5 years ago ---
    ruling_date = meta.get("ruling_date") or ""
    factors["ruling_date"] = ruling_date
    if not ruling_date or ruling_date[:10] > CUTOFF_DATE:
        factors["fail"] = "too_young"
        return False, factors

    # --- Criterion 6: program expense pct >= 70 ---
    prog_pct = meta.get("program_pct")
    factors["program_expense_pct"] = prog_pct
    if prog_pct is None or prog_pct < MIN_PROGRAM_PCT:
        factors["fail"] = "program_pct_low"
        return False, factors

    # --- Criterion 7: cause_tags present ---
    cause_tags = meta.get("cause_tags")
    has_tags = bool(cause_tags and cause_tags.strip() not in ("", "[]", "null"))
    factors["has_cause_tags"] = has_tags
    if not has_tags:
        factors["fail"] = "no_cause_tags"
        return False, factors

    factors["years_of_data"] = len(years_sorted)
    return True, factors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")

    if not args.dry_run:
        _add_column_if_missing(db)

    financials = _load_financials(db, args.limit)
    registry   = _load_registry(db)

    # Build NTEE1 lookup for diamond_factors
    ntee_lookup = {r[0]: r[1] for r in db.execute(
        "SELECT EIN, NTEE1 FROM registry_enriched"
    )}

    print(f"[compute] evaluating {len(financials):,} EINs …")
    diamonds, non_diamonds = [], []
    fail_reasons: dict[str, int] = {}

    for i, (ein, years) in enumerate(financials.items()):
        if i % 50_000 == 0 and i > 0:
            print(f"  … {i:,} processed, {len(diamonds):,} diamonds so far")
        is_diamond, factors = _compute(ein, years, registry)
        factors["ntee1"] = ntee_lookup.get(ein)
        if is_diamond:
            diamonds.append((ein, factors))
        else:
            non_diamonds.append(ein)
            reason = factors.get("fail", "unknown")
            fail_reasons[reason] = fail_reasons.get(reason, 0) + 1

    print(f"\n[result] {len(diamonds):,} diamonds / {len(financials):,} evaluated")
    print("[result] fail breakdown:")
    for reason, count in sorted(fail_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count:,}")

    if args.dry_run:
        print("\n[dry-run] no writes performed")
        return

    print(f"\n[write] updating {len(diamonds):,} diamonds + resetting others …")
    diamond_eins = {ein for ein, _ in diamonds}

    # Batch update in chunks for speed
    CHUNK = 2000

    # Reset all is_hidden_gem to 0 for the EINs we evaluated
    all_eins = list(financials.keys())
    for i in range(0, len(all_eins), CHUNK):
        chunk = all_eins[i:i + CHUNK]
        placeholders = ",".join("?" * len(chunk))
        db.execute(
            f"UPDATE registry_enriched SET is_hidden_gem=0, diamond_factors=NULL WHERE EIN IN ({placeholders})",
            chunk
        )
    db.commit()
    print(f"[write] reset {len(all_eins):,} evaluated EINs")

    # Write diamonds
    for i in range(0, len(diamonds), CHUNK):
        chunk = diamonds[i:i + CHUNK]
        db.executemany(
            "UPDATE registry_enriched SET is_hidden_gem=1, diamond_factors=? WHERE EIN=?",
            [(json.dumps(f), ein) for ein, f in chunk]
        )
    db.commit()
    print(f"[write] {len(diamonds):,} diamonds committed")

    # Verify
    count = db.execute("SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1").fetchone()[0]
    print(f"[verify] is_hidden_gem=1 in DB: {count:,}")
    db.close()
    print("[done]")


if __name__ == "__main__":
    main()
