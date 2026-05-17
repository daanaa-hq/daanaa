"""
compute_composite_score.py
--------------------------
Recomputes peer_percentile as a composite of two within-peer-group percentiles:

  revenue_pct  = where this org's revenue falls in its peer group's distribution
  reserve_pct  = where this org's reserve ratio falls in its peer group's distribution
                 reserve_ratio = total_assets / total_revenue  (clamped ≥ 0)

  composite = 0.65 × revenue_pct + 0.35 × reserve_pct

Both dimensions use the same peer group (NTEE subcategory + revenue band), so
each org is judged against category-specific norms — a food bank's reserves are
compared to other food banks, not to hospitals or foundations.

Percentile formula (within each group of n orgs, sorted ascending):
  pct = (rank_asc - 1) / (n - 1) × 100
  rank 1 = lowest value → 0th percentile
  rank n = highest value → 100th percentile
  Single-org groups: 100th percentile on both dimensions.

Run from ~/meritgiving with venv active:
    python3 scripts/compute_composite_score.py [--dry-run]
"""

import sqlite3
import sys
from collections import defaultdict

DB = "data/merit_registry.db"
DRY_RUN = "--dry-run" in sys.argv

REV_W = 0.65
RSV_W = 0.35

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== Composite Score Engine — Peer-Distribution Model ===")
print(f"Formula: {REV_W:.0%} × revenue_percentile_within_peer_group")
print(f"       + {RSV_W:.0%} × reserve_percentile_within_peer_group")
print(f"  (reserve_ratio = total_assets / total_revenue, clamped ≥ 0)")
print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE UPDATE'}\n")

rows = cur.execute("""
    SELECT EIN, organization_name, NTEE1, peer_group,
           total_revenue, total_assets,
           peer_percentile, peer_rank, peer_total
    FROM registry_enriched
    WHERE peer_group IS NOT NULL
      AND peer_rank IS NOT NULL
      AND peer_total IS NOT NULL
      AND peer_total > 0
""").fetchall()

orgs = [dict(r) for r in rows]
print(f"Loaded {len(orgs):,} orgs across peer groups")

# Group by peer_group
by_group = defaultdict(list)
for org in orgs:
    by_group[org["peer_group"]].append(org)

updates    = []
before_after = []

for pg, group in by_group.items():
    n = len(group)

    # ── Revenue percentile ──────────────────────────────────────────────────
    # Recompute fresh from live data — stored peer_rank can be stale.
    sorted_by_rev = sorted(group, key=lambda r: r["total_revenue"] or 0, reverse=True)
    for rev_rank, org in enumerate(sorted_by_rev, start=1):
        if n == 1:
            org["_rev_pct"] = 100.0
        else:
            # rank 1 (highest rev) → 100th pct, rank n → 0th pct
            org["_rev_pct"] = round((n - rev_rank) / (n - 1) * 100, 1)

    # ── Reserve ratio + within-group percentile ─────────────────────────────
    for org in group:
        rev = org["total_revenue"] or 0.0
        assets = max(0.0, org["total_assets"] or 0.0)
        org["_reserve_ratio"] = (assets / rev) if rev > 0 else 0.0

    # Sort ascending by reserve ratio → assign rank 1..n
    sorted_by_rsv = sorted(group, key=lambda r: r["_reserve_ratio"])
    for rsv_rank_asc, org in enumerate(sorted_by_rsv, start=1):
        if n == 1:
            org["_rsv_pct"] = 100.0
        else:
            org["_rsv_pct"] = round((rsv_rank_asc - 1) / (n - 1) * 100, 1)

    # ── Composite ───────────────────────────────────────────────────────────
    for org in group:
        composite = round(REV_W * org["_rev_pct"] + RSV_W * org["_rsv_pct"], 1)
        composite = max(0.0, min(100.0, composite))
        updates.append((composite, org["EIN"]))
        before_after.append({
            "name":     org["organization_name"],
            "ein":      org["EIN"],
            "ntee1":    org["NTEE1"] or "?",
            "pg":       pg,
            "rev_pct":  org["_rev_pct"],
            "rsv_pct":  org["_rsv_pct"],
            "ratio":    org["_reserve_ratio"],
            "old":      org["peer_percentile"] or 0.0,
            "new":      composite,
            "delta":    round(composite - (org["peer_percentile"] or 0.0), 1),
        })

# ── Stats ────────────────────────────────────────────────────────────────────
deltas = [b["delta"] for b in before_after]
moved_up   = sum(1 for d in deltas if d > 5)
moved_down = sum(1 for d in deltas if d < -5)
unchanged  = len(deltas) - moved_up - moved_down

print(f"\nScore change summary vs. current composite ({len(before_after):,} orgs):")
print(f"  Moved up   >5 pts: {moved_up:>7,}  ({moved_up/len(deltas)*100:.1f}%)")
print(f"  Moved down >5 pts: {moved_down:>7,}  ({moved_down/len(deltas)*100:.1f}%)")
print(f"  Stable  (≤5 pts): {unchanged:>7,}  ({unchanged/len(deltas)*100:.1f}%)")

print("\nBiggest improvements:")
print(f"  {'Name':<44} {'PG':<14} {'Rev%':>5} {'Rsv%':>5} {'Ratio':>6}  Old → New   (Δ)")
for b in sorted(before_after, key=lambda x: x["delta"], reverse=True)[:10]:
    print(f"  {b['name'][:42]:<44} {b['pg']:<14} {b['rev_pct']:5.1f} {b['rsv_pct']:5.1f} {b['ratio']:6.2f}  {b['old']:5.1f} → {b['new']:5.1f}  ({b['delta']:+.1f})")

print("\nBiggest decreases:")
for b in sorted(before_after, key=lambda x: x["delta"])[:8]:
    print(f"  {b['name'][:42]:<44} {b['pg']:<14} {b['rev_pct']:5.1f} {b['rsv_pct']:5.1f} {b['ratio']:6.2f}  {b['old']:5.1f} → {b['new']:5.1f}  ({b['delta']:+.1f})")

# ── Spotlight ────────────────────────────────────────────────────────────────
SPOTLIGHT = {
    "521231983": "Aga Khan Foundation USA",
    "742181456": "Houston Food Bank",
    "760311190": "Houston Food Bank Endowment",
    "133957095": "Doctors Without Borders",
    "530242652": "Smithsonian Institution",
    "530196605": "American Red Cross",
    "042103583": "Harvard University",
    "131628021": "UNICEF USA",
}
print("\nSpotlight orgs:")
print(f"  {'Name':<44} {'PG':<14} {'Rev%':>5} {'Rsv%':>5} {'Ratio':>7}  Old → New")
by_ein = {b["ein"]: b for b in before_after}
for ein, label in SPOTLIGHT.items():
    b = by_ein.get(ein)
    if b:
        print(f"  {label:<44} {b['pg']:<14} {b['rev_pct']:5.1f} {b['rsv_pct']:5.1f} {b['ratio']:7.2f}  {b['old']:5.1f} → {b['new']:5.1f}")
    else:
        print(f"  {label:<44} not in scored set")

# ── Per-category summary ──────────────────────────────────────────────────────
print("\nPer-NTEE1 average score (old vs new):")
by_ntee = defaultdict(list)
for b in before_after:
    by_ntee[b["ntee1"]].append(b)
for ntee1 in sorted(by_ntee):
    g = by_ntee[ntee1]
    avg_old = sum(x["old"] for x in g) / len(g)
    avg_new = sum(x["new"] for x in g) / len(g)
    avg_ratio = sum(x["ratio"] for x in g) / len(g)
    print(f"  {ntee1:2s}  orgs={len(g):>6,}  avg_ratio={avg_ratio:>8.2f}  old={avg_old:5.1f} → new={avg_new:5.1f}  (Δ={avg_new-avg_old:+.1f})")

# ── Write ─────────────────────────────────────────────────────────────────────
if not DRY_RUN:
    print(f"\nWriting {len(updates):,} updates …")
    cur.executemany(
        "UPDATE registry_enriched SET peer_percentile = ? WHERE EIN = ?",
        updates
    )
    conn.commit()
    print("Done.")
    for ein, label in [("742181456", "Houston Food Bank"), ("521231983", "Aga Khan"), ("133957095", "MSF")]:
        r = cur.execute("SELECT peer_percentile FROM registry_enriched WHERE EIN=?", (ein,)).fetchone()
        if r:
            print(f"  {label}: {r[0]}")
else:
    print("\nDry run complete. Run without --dry-run to apply.")

conn.close()
