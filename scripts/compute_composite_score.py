"""
compute_composite_score.py
--------------------------
Peer-distribution composite score with regional fallback.

  composite = 65% × revenue_pct_within_group + 35% × reserve_pct_within_group

Group selection (hybrid):
  - If subcategory+band+region has ≥ MIN_GROUP_SIZE orgs → use regional group
  - Otherwise → fall back to national subcategory+band group

Regions: Northeast / Midwest / South / West (US Census)
Threshold: MIN_GROUP_SIZE = 30

Run: python3 scripts/compute_composite_score.py [--dry-run]
"""

import sqlite3, sys
from collections import defaultdict

DB             = "data/merit_registry.db"
DRY_RUN        = "--dry-run" in sys.argv
MIN_GROUP      = 30
REV_W, RSV_W   = 0.65, 0.35
SCORER_VERSION = "v1"

STATE_REGION = {
    'CT':'Northeast','ME':'Northeast','MA':'Northeast','NH':'Northeast',
    'NJ':'Northeast','NY':'Northeast','PA':'Northeast','RI':'Northeast','VT':'Northeast',
    'IL':'Midwest','IN':'Midwest','MI':'Midwest','MN':'Midwest','OH':'Midwest',
    'WI':'Midwest','IA':'Midwest','KS':'Midwest','MO':'Midwest','NE':'Midwest',
    'ND':'Midwest','SD':'Midwest',
    'DE':'South','FL':'South','GA':'South','MD':'South','NC':'South','SC':'South',
    'VA':'South','WV':'South','DC':'South','AL':'South','KY':'South','MS':'South',
    'TN':'South','AR':'South','LA':'South','OK':'South','TX':'South',
    'AZ':'West','CO':'West','ID':'West','MT':'West','NV':'West','NM':'West',
    'UT':'West','WY':'West','AK':'West','CA':'West','HI':'West','OR':'West','WA':'West',
}

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur  = conn.cursor()

rows = cur.execute("""
    SELECT EIN, organization_name, NTEE1, peer_group, STATE,
           total_revenue, total_assets, peer_percentile
    FROM registry_enriched
    WHERE peer_group IS NOT NULL AND total_revenue > 0
""").fetchall()
orgs = [dict(r) for r in rows]
print(f"Loaded {len(orgs):,} orgs  |  mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")

# Attach region and compute reserve ratio
for o in orgs:
    o['_region']  = STATE_REGION.get(o['STATE'] or '', 'Other')
    o['_ratio']   = max(0.0, o['total_assets'] or 0.0) / o['total_revenue']
    o['_reg_key'] = f"{o['peer_group']}:{o['_region']}"

# Build group buckets
national = defaultdict(list)
regional = defaultdict(list)
for o in orgs:
    national[o['peer_group']].append(o)
    regional[o['_reg_key']].append(o)

# Determine which regional groups are viable
viable_regional = {k for k, v in regional.items() if len(v) >= MIN_GROUP}

def assign_percentiles(group):
    n = len(group)
    if n == 1:
        for o in group:
            o['_rev_pct'] = o['_rsv_pct'] = 100.0
        return
    for rank, o in enumerate(sorted(group, key=lambda x: x['total_revenue'], reverse=True), 1):
        o['_rev_pct'] = round((n - rank) / (n - 1) * 100, 1)
    for rank, o in enumerate(sorted(group, key=lambda x: x['_ratio']), 1):
        o['_rsv_pct'] = round((rank - 1) / (n - 1) * 100, 1)

# Score each org against its best available group
national_used = regional_used = 0
for o in orgs:
    if o['_reg_key'] in viable_regional:
        group_key, group = o['_reg_key'], regional[o['_reg_key']]
        regional_used += 1
    else:
        group_key, group = o['peer_group'], national[o['peer_group']]
        national_used += 1
    o['_group_used'] = group_key
    o['_group_size'] = len(group)

# Assign percentiles per group (compute once per group)
for group in national.values():
    assign_percentiles(group)
for key, group in regional.items():
    if key in viable_regional:
        assign_percentiles(group)

# Build updates
updates      = []
before_after = []
for o in orgs:
    # Pick percentiles from correct group
    if o['_reg_key'] in viable_regional:
        rev_pct = o.get('_rev_pct', 0.0)
        rsv_pct = o.get('_rsv_pct', 0.0)
    else:
        rev_pct = o.get('_rev_pct', 0.0)
        rsv_pct = o.get('_rsv_pct', 0.0)
    composite = round(max(0.0, min(100.0, REV_W * rev_pct + RSV_W * rsv_pct)), 1)
    updates.append((composite, o['EIN']))
    before_after.append({
        'name': o['organization_name'], 'ein': o['EIN'],
        'old': o['peer_percentile'] or 0.0, 'new': composite,
        'group': o['_group_used'], 'n': o['_group_size'],
        'rev_pct': rev_pct, 'rsv_pct': rsv_pct, 'ratio': o['_ratio'],
    })

n_reg_groups = len(viable_regional)
n_nat_groups = len(national)
print(f"Regional groups viable (≥{MIN_GROUP}): {n_reg_groups:,} of {n_reg_groups + len([k for k in regional if k not in viable_regional]):,}")
print(f"Orgs scored regionally: {regional_used:,}  |  nationally: {national_used:,}")

deltas = [b['new'] - b['old'] for b in before_after]
print(f"Moved >5 up:   {sum(1 for d in deltas if d>5):,}  |  "
      f"Stable:  {sum(1 for d in deltas if -5<=d<=5):,}  |  "
      f"Moved >5 down: {sum(1 for d in deltas if d<-5):,}")

SPOTLIGHT = {
    '742181456':'Houston Food Bank',
    '521231983':'Aga Khan Foundation USA',
    '133957095':'Doctors Without Borders',
    '530196605':'American Red Cross',
    '042103583':'Harvard University',
}
print("\nSpotlight:")
by_ein = {b['ein']: b for b in before_after}
for ein, label in SPOTLIGHT.items():
    b = by_ein.get(ein)
    if b:
        print(f"  {label:<36} {b['old']:>5.1f} → {b['new']:>5.1f}  "
              f"rev={b['rev_pct']:.0f}% rsv={b['rsv_pct']:.0f}%  [{b['group']} n={b['n']}]")

if not DRY_RUN:
    cur.executemany("UPDATE registry_enriched SET peer_percentile=? WHERE EIN=?", updates)

    import datetime
    today = datetime.date.today().isoformat()
    snapshots = [
        (
            o['EIN'], today,
            o['total_revenue'], o['total_assets'] or 0.0,
            o['peer_group'], o['STATE'], o['_region'],
            SCORER_VERSION,
            b['new'], b['rev_pct'], b['rsv_pct'],
            o['_ratio'], o['_group_size'], o['_group_used'],
        )
        for o, b in zip(orgs, before_after)
    ]
    cur.executemany("""
        INSERT OR IGNORE INTO score_snapshots
          (EIN, snapshot_date, total_revenue, total_assets,
           peer_group, STATE, region, scorer_version,
           peer_percentile, rev_pct, rsv_pct,
           reserve_ratio, group_size, group_key)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, snapshots)

    conn.commit()
    print(f"\nWrote {len(updates):,} rows  |  {len(snapshots):,} snapshots → score_snapshots.")
else:
    print("\nDry run — pass no flag to apply.")

conn.close()
