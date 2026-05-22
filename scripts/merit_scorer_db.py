#!/usr/bin/env python3
"""
Merit Scorer DB — reads directly from registry_enriched, writes scores back.

Three tiers based on available data:
  full         — 4-metric v3.3 algorithm (revenue + expenses + net_assets + total_assets)
  partial      — 2-metric (leverage + revenue percentile; no expense data)
  revenue_only — revenue percentile within NTEE1 peer group only

Usage:
  python3 scripts/merit_scorer_db.py --sample 100 --dry-run   # test, no DB writes
  python3 scripts/merit_scorer_db.py                          # score all, write to DB
"""

import argparse, bisect, sqlite3, datetime
from collections import defaultdict
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

WEIGHTS_FULL = {
    'program_ratio':        0.30,
    'sustainability_ratio': 0.25,
    'reserves_ratio':       0.25,
    'leverage_ratio':       0.20,
}
WEIGHTS_PARTIAL = {
    'leverage_ratio': 0.55,
    'revenue_pct':    0.45,
}

PEER_BANDS = [
    (0,           100_000),
    (100_000,     500_000),
    (500_000,   1_000_000),
    (1_000_000,  5_000_000),
    (5_000_000, 20_000_000),
    (20_000_000, 100_000_000),
    (100_000_000, float('inf')),
]


def revenue_band(rev: float) -> int:
    for i, (lo, hi) in enumerate(PEER_BANDS):
        if lo <= rev < hi:
            return i
    return len(PEER_BANDS) - 1


def safe_div(n, d) -> float | None:
    try:
        n, d = float(n), float(d)
        return n / d if d != 0 else None
    except (TypeError, ValueError):
        return None


def percentile_rank_sorted(value, sorted_vals: list) -> float:
    """O(log n) percentile rank against a pre-sorted, None-free list."""
    if value is None or not sorted_vals:
        return 50.0
    n = len(sorted_vals)
    below = bisect.bisect_left(sorted_vals, value)
    above = bisect.bisect_right(sorted_vals, value)
    equal = above - below
    return round((below + equal / 2.0) / n * 100, 1)


def score_band(score: int) -> str:
    if score >= 85: return "Blazing"
    if score >= 70: return "Burning Bright"
    if score >= 55: return "Steady Flame"
    if score >= 35: return "Growing"
    return "Just Starting"


def detect_tier(row: dict) -> str:
    has_expenses = row["total_expenses"] is not None and row["total_expenses"] > 0
    has_net      = row["net_assets"] is not None
    has_assets   = row["total_assets"] is not None and row["total_assets"] > 0
    if has_expenses and has_net and has_assets:
        return "full"
    if has_net and has_assets:
        return "partial"
    return "revenue_only"


def extract_metrics(row: dict, tier: str) -> dict:
    rev  = float(row["total_revenue"] or 0)
    exp  = float(row["total_expenses"] or 0) if row["total_expenses"] else None
    prog = float(row["program_expenses"] or 0) if row.get("program_expenses") else None
    net  = float(row["net_assets"] or 0) if row["net_assets"] is not None else None
    ast  = float(row["total_assets"] or 0) if row["total_assets"] else None

    if tier == "full":
        return {
            "program_ratio":        safe_div(prog, exp),
            "sustainability_ratio": safe_div(rev, exp),
            "reserves_ratio":       safe_div(net, exp),
            "leverage_ratio":       safe_div(net, ast),
        }
    if tier == "partial":
        return {"leverage_ratio": safe_div(net, ast)}
    return {}


def build_group_cache(peers: list, tier: str) -> dict:
    """Pre-compute sorted metric distributions for a peer group (runs once per group)."""
    peer_revs = sorted(float(p["total_revenue"]) for p in peers if p["total_revenue"])

    if tier == "revenue_only":
        return {"peer_revs": peer_revs}

    metric_lists: dict[str, list] = defaultdict(list)
    for p in peers:
        for k, v in extract_metrics(p, tier).items():
            if v is not None:
                metric_lists[k].append(v)

    cache = {k: sorted(v) for k, v in metric_lists.items()}
    if tier == "partial":
        cache["peer_revs"] = peer_revs
    return cache


def score_org_cached(row: dict, cache: dict, tier: str, pk: str) -> dict:
    """Score one org using pre-built peer distributions. O(log n) per metric."""
    rev = float(row["total_revenue"])
    peer_revs = cache.get("peer_revs", [])

    if tier == "revenue_only":
        pct = percentile_rank_sorted(rev, peer_revs)
        score = round(max(0, min(100, pct)))
        return {"merit_score": score, "merit_band": score_band(score),
                "peer_group": pk, "score_tier": tier}

    my_metrics = extract_metrics(row, tier)
    weights = WEIGHTS_FULL if tier == "full" else WEIGHTS_PARTIAL

    if tier == "partial":
        my_metrics["revenue_pct"] = percentile_rank_sorted(rev, peer_revs)

    weighted_sum = total_weight = 0.0
    for metric, weight in weights.items():
        val = my_metrics.get(metric)
        if metric == "revenue_pct":
            pct = val if val is not None else 50.0
        else:
            pct = percentile_rank_sorted(val, cache.get(metric, []))
        weighted_sum += pct * weight
        total_weight  += weight

    score = round(max(0, min(100, weighted_sum / total_weight))) if total_weight else 50
    return {"merit_score": score, "merit_band": score_band(score),
            "peer_group": pk, "score_tier": tier}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample",    type=int, default=0,  help="Limit orgs (0=all)")
    ap.add_argument("--dry-run",   action="store_true",  help="Print results, skip DB writes")
    ap.add_argument("--min-peers", type=int, default=2,  help="Min peers needed to score")
    args = ap.parse_args()

    db = sqlite3.connect(DB_PATH, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.row_factory = sqlite3.Row

    cols = {r[1] for r in db.execute("PRAGMA table_info(registry_enriched)").fetchall()}
    if "score_tier" not in cols:
        db.execute("ALTER TABLE registry_enriched ADD COLUMN score_tier TEXT")
        db.commit()
        print("Added score_tier column to registry_enriched")

    all_rows = [dict(r) for r in db.execute("""
        SELECT EIN, organization_name, NTEE1, total_revenue, total_expenses,
               net_assets, total_assets
        FROM registry_enriched
        WHERE NTEE1 IS NOT NULL
          AND total_revenue IS NOT NULL
          AND total_revenue > 0
        ORDER BY total_revenue DESC
    """).fetchall()]
    for r in all_rows:
        r.setdefault("program_expenses", None)

    total  = len(all_rows)
    target = all_rows[:args.sample] if args.sample else all_rows
    print(f"Scoreable orgs in DB: {total:,}  (scoring: {len(target):,})")

    # Build peer groups from ALL rows (ensures full peer distributions even in --sample runs)
    pg_primary: dict[str, list]  = defaultdict(list)
    pg_fallback: dict[str, list] = defaultdict(list)
    for row in all_rows:
        rev  = float(row["total_revenue"])
        band = revenue_band(rev)
        pg_primary[f"{row['NTEE1']}_{band}"].append(row)
        pg_fallback[f"ALL_{band}"].append(row)

    # Pre-build sorted distributions once per (group_key, tier) — O(n log n) total
    print("Pre-building peer distributions...")
    group_caches: dict[str, dict] = {}
    for gk, peers in {**pg_primary, **pg_fallback}.items():
        for t in ("full", "partial", "revenue_only"):
            group_caches[f"{gk}|{t}"] = build_group_cache(peers, t)
    print(f"Cached {len(group_caches)} group×tier distributions")

    # Score each target org — O(log n) per org per metric
    results: list[dict]         = []
    tier_counts: dict[str, int] = defaultdict(int)
    skipped = 0
    report_every = max(1, len(target) // 20)

    for i, row in enumerate(target):
        rev  = float(row["total_revenue"])
        band = revenue_band(rev)
        pk   = f"{row['NTEE1']}_{band}"
        fk   = f"ALL_{band}"

        if len(pg_primary[pk]) >= args.min_peers:
            used_pk = pk
        elif len(pg_fallback[fk]) >= args.min_peers:
            used_pk = fk
        else:
            skipped += 1
            continue

        tier   = detect_tier(row)
        result = score_org_cached(row, group_caches[f"{used_pk}|{tier}"], tier, used_pk)
        result["EIN"]  = row["EIN"]
        result["name"] = row["organization_name"]
        results.append(result)
        tier_counts[tier] += 1

        if (i + 1) % report_every == 0:
            print(f"  {i+1:,}/{len(target):,} ({(i+1)/len(target)*100:.0f}%) ...")

    scored = len(results)
    print(f"\nScored: {scored:,}  Skipped (too few peers): {skipped:,}")
    print(f"Tiers: full={tier_counts['full']:,}  partial={tier_counts['partial']:,}  "
          f"revenue_only={tier_counts['revenue_only']:,}")

    bands: dict[str, int] = defaultdict(int)
    for r in results:
        bands[r["merit_band"]] += 1
    print("Bands:", dict(sorted(bands.items())))

    print("\nSample (first 10):")
    for r in results[:10]:
        print(f"  {r['EIN']}  {r['name'][:40]:<40}  score={r['merit_score']:>3}  "
              f"band={r['merit_band']:<15}  tier={r['score_tier']}")

    if args.dry_run:
        print("\n[dry-run] No changes written to DB.")
        return

    updated = 0
    for r in results:
        db.execute("""
            UPDATE registry_enriched
            SET merit_score=?, merit_band=?, peer_group=?, score_tier=?
            WHERE EIN=?
        """, (r["merit_score"], r["merit_band"], r["peer_group"], r["score_tier"], r["EIN"]))
        updated += db.execute("SELECT changes()").fetchone()[0]

    db.commit()
    print(f"\nWrote {updated:,} scores to DB.")
    print(f"Run at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
