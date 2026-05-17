"""
compute_composite_score.py
--------------------------
Recomputes peer_percentile as a composite of revenue rank (65%) + reserve
health score (35%) within each NTEE-subcategory + revenue-band peer group.

Reserve health = min(100, log(reserve_ratio + 1) / log(4) × 100)
  where reserve_ratio = total_assets / total_revenue

Why reserve ratio instead of pure revenue rank:
  Revenue rank alone is a scale signal, not a health signal. Endowment-funded
  orgs (e.g. Aga Khan Foundation: $65M revenue but $580M assets) score 26th
  percentile by revenue alone despite holding the 3rd-largest balance sheet
  in their peer group. The reserve ratio is the standard working-capital proxy
  used by Charity Navigator and validated by academic literature (Tuckman &
  Chang, Bowman, Calabrese). Log scale applies diminishing returns so an org
  with 8x assets-to-revenue doesn't score 8x better than one with 1x.

Formula:
  reserve_score  = min(100, log(total_assets/total_revenue + 1) / log(4) × 100)
  composite_pct  = 0.65 × revenue_percentile + 0.35 × reserve_score

Run from ~/meritgiving with venv active:
    python3 scripts/compute_composite_score.py [--dry-run]
"""

import math
import sqlite3
import sys
from collections import defaultdict

DB = "data/merit_registry.db"
DRY_RUN = "--dry-run" in sys.argv

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== Composite Score Engine (reserve-ratio formula) ===")
print(f"Formula: 0.65 × revenue_percentile + 0.35 × reserve_score")
print(f"  reserve_score = min(100, log(assets/revenue + 1) / log(4) × 100)")
print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE UPDATE'}\n")

# Load all orgs that have a peer group and a revenue percentile
rows = cur.execute("""
    SELECT EIN, organization_name, peer_group, total_revenue, total_assets,
           peer_percentile, peer_rank, peer_total, merit_tier
    FROM registry_enriched
    WHERE peer_group IS NOT NULL
      AND peer_percentile IS NOT NULL
""").fetchall()

orgs = [dict(r) for r in rows]
print(f"Loaded {len(orgs):,} orgs across peer groups")


def reserve_score(total_assets, total_revenue):
    """Reserve health score [0–100] using log-scaled assets/revenue ratio."""
    if not total_revenue or total_revenue <= 0:
        return 0.0
    assets = max(0.0, total_assets or 0.0)  # clamp: negative net assets → 0
    ratio = assets / total_revenue
    score = math.log(ratio + 1) / math.log(4) * 100
    return min(100.0, max(0.0, round(score, 1)))


updates = []       # (composite_pct, EIN)
before_after = []  # for reporting

for org in orgs:
    rev_pct = org["peer_percentile"] or 0.0
    rsv = reserve_score(org["total_assets"], org["total_revenue"])
    composite = round(0.65 * rev_pct + 0.35 * rsv, 1)
    composite = max(0.0, min(100.0, composite))

    updates.append((composite, org["EIN"]))
    before_after.append({
        "name": org["organization_name"],
        "ein": org["EIN"],
        "peer_group": org["peer_group"] or "",
        "rev_pct": rev_pct,
        "rsv_score": rsv,
        "old": rev_pct,
        "new": composite,
        "delta": round(composite - rev_pct, 1),
        "tier": org["merit_tier"],
        "reserve_ratio": (org["total_assets"] or 0) / org["total_revenue"] if org["total_revenue"] else 0,
    })

# Stats
deltas = [b["delta"] for b in before_after]
moved_up   = sum(1 for d in deltas if d > 5)
moved_down = sum(1 for d in deltas if d < -5)
unchanged  = len(deltas) - moved_up - moved_down
print(f"\nScore change summary (across {len(before_after):,} scored orgs):")
print(f"  Moved up   >5 pts: {moved_up:>7,}  ({moved_up/len(deltas)*100:.1f}%)")
print(f"  Moved down >5 pts: {moved_down:>7,}  ({moved_down/len(deltas)*100:.1f}%)")
print(f"  Stable  (≤5 pts): {unchanged:>7,}  ({unchanged/len(deltas)*100:.1f}%)")

# Biggest movers
biggest_up   = sorted(before_after, key=lambda x: x["delta"], reverse=True)[:12]
biggest_down = sorted(before_after, key=lambda x: x["delta"])[:8]

print("\nBiggest improvements (asset-rich orgs previously undercounted):")
print(f"  {'Name':<46} {'Peer group':<14} {'Rev%':>5}  {'Rsv':>5}  Old → New   (Δ)")
for b in biggest_up:
    print(f"  {b['name'][:44]:<46} {b['peer_group']:<14} {b['rev_pct']:5.1f}  {b['rsv_score']:5.1f}  {b['old']:5.1f} → {b['new']:5.1f}  ({b['delta']:+.1f})")

print("\nBiggest decreases (revenue-heavy orgs with thin balance sheets):")
for b in biggest_down:
    print(f"  {b['name'][:44]:<46} {b['peer_group']:<14} {b['rev_pct']:5.1f}  {b['rsv_score']:5.1f}  {b['old']:5.1f} → {b['new']:5.1f}  ({b['delta']:+.1f})")

# Spotlight orgs for sanity check
SPOTLIGHT_EINS = {
    "521231983": "Aga Khan Foundation USA",
    "133957095": "Doctors Without Borders",
    "237297442": "Khan Academy",
    "941651015": "Wikimedia Foundation",
    "530242652": "Smithsonian Institution",
}
print("\nSpotlight orgs:")
print(f"  {'Name':<44} {'Rev%':>5}  {'Rsv':>5}  Old → New   (ratio)")
by_ein = {b["ein"]: b for b in before_after}
for ein, label in SPOTLIGHT_EINS.items():
    b = by_ein.get(ein)
    if b:
        print(f"  {label:<44} {b['rev_pct']:5.1f}  {b['rsv_score']:5.1f}  {b['old']:5.1f} → {b['new']:5.1f}  (ratio={b['reserve_ratio']:.2f})")
    else:
        print(f"  {label:<44} not in scored set")

if not DRY_RUN:
    print(f"\nWriting {len(updates):,} updates to registry_enriched.peer_percentile …")
    cur.executemany(
        "UPDATE registry_enriched SET peer_percentile = ? WHERE EIN = ?",
        updates
    )
    conn.commit()
    print("Done.")
    result = cur.execute(
        "SELECT EIN, organization_name, peer_percentile FROM registry_enriched WHERE EIN='521231983'"
    ).fetchone()
    if result:
        print(f"  Verified Aga Khan Foundation: peer_percentile = {result[2]}")
else:
    print("\nDry run complete. Run without --dry-run to apply.")

conn.close()
