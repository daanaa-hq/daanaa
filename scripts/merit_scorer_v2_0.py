#!/usr/bin/env python3
"""
MERIT Scorer v2.0 — Cause-Aware Peer Groups
============================================
Universe  : deductibility='1' (tax-deductible 501(c)(3) only)
Peer cells: 4 operating model groups × 6 revenue bands = 24 cells
Metrics   : group-specific weighted composite of revenue, reserve,
            asset intensity, and program spend percentiles

Key fixes over v1.0:
  - Non-deductible orgs excluded
  - program_expense_pct used as-is (0-100 scale — NOT multiplied by 100)
  - months_of_reserve sentinel (=120) excluded from reserve percentile calc
  - Endowment & Capital group: asset intensity replaces reserve metric
  - Auto-revoked orgs excluded from scoring

Run:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/merit_scorer_v2_0.py [--dry-run] [--limit N]
"""
import sqlite3, json, argparse, sys, time, statistics
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DB   = Path.home() / "meritgiving/data/merit_registry.db"
LOG  = Path.home() / "meritgiving/logs/scorer_v2.log"

SCORER_VERSION = "v2.0"
SENTINEL       = 120.0   # months_of_reserve cap — exclude from percentile

# ── Operating model groups ────────────────────────────────────────────────────
GROUPS = {
    'Direct_Service': [
        'human services','employment','crime prevention','mental health',
        'international','food','recreation','youth development','animals',
        'religion','early childhood','literacy','legal aid','civil rights',
        'social science','disaster relief','spiritual','buddhist','jewish',
        'international development','humanitarian aid','family services',
        'addiction recovery','civic','vocational training','food security',
        # common unmatched primaries — generic cause labels
        'youth','youth sports','children','animal rescue','community service',
        'agriculture','charity','outreach','social services','supportive services',
        'community health','immigrant services','refugee services','senior care',
        'hunger','homelessness','domestic violence','substance abuse',
        'veterans services','disability','hospice','palliative care',
        'job training','workforce development','financial literacy',
    ],
    'Mission_Infrastructure': [
        'education','health','arts','environment','science',
        'community development','k-12 education','health advocacy',
        'music','theater','visual arts','advocacy','sustainability',
        'civic engagement','social enterprise','community',
        'research','stem education','media','journalism','public health',
        'maternal health','child health','behavioral health',
        'environmental education','climate','clean energy',
    ],
    'Asset_Stewards': [
        'housing','public safety','cultural heritage','mutual aid',
        'animal welfare','sports','higher education','disability support',
        'economic development','senior services','libraries','museums',
        'affordable housing','elderly housing','healthcare facilities',
        'community facilities','recreational facilities','parks',
    ],
    'Endowment_Capital': [
        'grantmaking','conservation','historical preservation',
        'disease research','scholarships','faith','religious',
        'veterans','medical research','philanthropy',
        'foundation','community foundation','private foundation',
        'land conservation','nature conservancy','endowment',
    ],
}

SYNONYMS = {
    'healthcare': 'health', 'mental-health': 'mental health',
    'wildlife': 'animals', 'wildlife-conservation': 'conservation',
    'child development': 'early childhood', 'job training': 'employment',
    'workforce': 'employment', 'human-services': 'human services',
    'faith-based': 'faith', 'religious organizations': 'religious',
    'philanthropy': 'philanthropy',  # keep — now in Endowment_Capital
    'voluntarism': 'philanthropy', 'grantmaking foundation': 'grantmaking',
    'community foundation': 'community foundation',
    'animal rescue': 'animal rescue', 'animal shelter': 'animal welfare',
    'youth sports': 'youth sports', 'youth services': 'youth development',
    'community service': 'community service',
    'mental illness': 'mental health', 'behavioral health': 'behavioral health',
}

CAUSE_TO_GROUP = {}
for grp, causes in GROUPS.items():
    for c in causes:
        CAUSE_TO_GROUP[c] = grp

BANDS = [
    (0,           25_000,      'Nano'),
    (25_000,      100_000,     'Micro'),
    (100_000,     500_000,     'Small'),
    (500_000,     5_000_000,   'Medium'),
    (5_000_000,   50_000_000,  'Large'),
    (50_000_000,  float('inf'),'Major'),
]

def get_band(rev: float) -> str:
    for lo, hi, label in BANDS:
        if lo <= rev < hi:
            return label
    return 'Major'

# ── Group-specific metric weights ─────────────────────────────────────────────
# Each tuple: (revenue_w, reserve_w, asset_w, program_w)
# Fallback (no program_pct available): weights renormalized across first 3
WEIGHTS = {
    'Direct_Service':       (0.30, 0.25, 0.10, 0.35),
    'Mission_Infrastructure':(0.30, 0.35, 0.10, 0.25),
    'Asset_Stewards':       (0.30, 0.15, 0.40, 0.15),
    'Endowment_Capital':    (0.30, 0.00, 0.55, 0.15),  # reserve excluded (sentinel distortion)
}

TIER_THRESHOLDS = [
    (85, 'Blazing'),
    (70, 'Burning Bright'),
    (55, 'Steady Flame'),
    (35, 'Growing'),
    ( 0, 'Just Starting'),
]

def score_to_tier(score: float) -> str:
    for threshold, label in TIER_THRESHOLDS:
        if score >= threshold:
            return label
    return 'Just Starting'

def score_to_band(score: float) -> str:
    if score >= 80: return 'Beacon'
    if score >= 60: return 'Lantern'
    if score >= 40: return 'Flame'
    if score >= 20: return 'Ember'
    return 'Spark'

def bulk_percentile_ranks(values: list) -> list:
    """
    Compute percentile ranks for all values at once using numpy.
    Returns a list of floats (0-100) aligned with input.
    None inputs get 50.0. ~100x faster than per-value iteration.
    """
    import numpy as np
    out = [50.0] * len(values)
    valid_idx = [i for i, v in enumerate(values) if v is not None]
    if not valid_idx:
        return out
    vals = np.array([values[i] for i in valid_idx], dtype=float)
    # For each value, compute (below + equal/2) / n * 100
    n = len(vals)
    sorted_vals = np.sort(vals)
    below = np.searchsorted(sorted_vals, vals, side='left')
    equal = np.searchsorted(sorted_vals, vals, side='right') - below
    pcts  = (below + equal / 2.0) / n * 100.0
    for i, idx in enumerate(valid_idx):
        out[idx] = round(float(pcts[i]), 2)
    return out

def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def main():
    parser = argparse.ArgumentParser(description='MERIT Scorer v2.0')
    parser.add_argument('--dry-run', action='store_true', help='Compute scores but do not write to DB')
    parser.add_argument('--limit',   type=int, default=0,  help='Limit number of orgs to score (0=all)')
    parser.add_argument('--group',   type=str, default='', help='Score only this group')
    args = parser.parse_args()

    log('=' * 65)
    log(f'MERIT Scorer {SCORER_VERSION} starting')
    log(f'dry_run={args.dry_run}  limit={args.limit or "all"}  group={args.group or "all"}')
    log('=' * 65)

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row

    # ── Load all scoreable orgs ───────────────────────────────────────────────
    log('Loading orgs...')
    limit_clause = f'LIMIT {args.limit}' if args.limit else ''
    rows = conn.execute(f"""
        SELECT
            r.EIN, r.organization_name, r.total_revenue, r.total_assets,
            r.net_assets, r.total_expenses, r.program_expense_pct,
            r.months_of_reserve, r.cause_tags, r.revenue_band
        FROM registry_enriched r
        WHERE r.deductibility = '1'
          AND r.total_revenue > 0
          AND r.total_assets IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM revoked_eins rv WHERE rv.EIN = r.EIN
          )
        {limit_clause}
    """).fetchall()
    log(f'Loaded {len(rows):,} scoreable orgs')

    # ── Classify each org ─────────────────────────────────────────────────────
    log('Classifying into peer cells...')
    orgs = []
    group_counter = defaultdict(int)
    unmatched_causes = defaultdict(int)

    for r in rows:
        try:
            tags = json.loads(r['cause_tags'] or '[]')
        except:
            tags = []
        primary = SYNONYMS.get((tags[0] if tags else '').lower(), (tags[0] if tags else '').lower())
        group   = CAUSE_TO_GROUP.get(primary)

        if not group:
            unmatched_causes[primary] += 1
            group = 'Direct_Service'  # safe default — most common model

        if args.group and group != args.group:
            continue

        band = get_band(r['total_revenue'])
        cell = f"{group}|{band}"

        # Reserve: exclude sentinel
        reserve = r['months_of_reserve']
        reserve_valid = reserve if (reserve is not None and abs(reserve - SENTINEL) > 0.5 and reserve >= 0) else None

        # Asset intensity (cap extreme outliers)
        ai = None
        if r['total_revenue'] > 0 and r['total_assets'] is not None:
            ai = r['total_assets'] / r['total_revenue']
            if ai < 0 or ai > 500:
                ai = None

        # Program pct (already 0-100 scale)
        prog = r['program_expense_pct']
        prog = prog if (prog is not None and prog > 0) else None

        orgs.append({
            'ein':     r['EIN'],
            'group':   group,
            'band':    band,
            'cell':    cell,
            'revenue': r['total_revenue'],
            'reserve': reserve_valid,
            'ai':      ai,
            'prog':    prog,
        })
        group_counter[group] += 1

    log(f'Classified: {len(orgs):,} orgs into {len(set(o["cell"] for o in orgs))} peer cells')
    for grp, n in sorted(group_counter.items()):
        log(f'  {grp:<30} {n:>8,}')
    if unmatched_causes:
        top = sorted(unmatched_causes.items(), key=lambda x: -x[1])[:10]
        log(f'  Top unmatched causes (→ Direct_Service): {top}')

    # ── Build peer cell distributions ─────────────────────────────────────────
    log('Building peer distributions...')
    cell_revenues = defaultdict(list)
    cell_reserves = defaultdict(list)
    cell_ais      = defaultdict(list)
    cell_progs    = defaultdict(list)

    for o in orgs:
        c = o['cell']
        cell_revenues[c].append(o['revenue'])
        if o['reserve'] is not None: cell_reserves[c].append(o['reserve'])
        if o['ai']      is not None: cell_ais[c].append(o['ai'])
        if o['prog']    is not None: cell_progs[c].append(o['prog'])

    # Cells with < 30 orgs fall back to group-level
    MIN_CELL = 30
    group_revenues = defaultdict(list)
    group_reserves = defaultdict(list)
    group_ais      = defaultdict(list)
    group_progs    = defaultdict(list)
    for o in orgs:
        g = o['group']
        group_revenues[g].append(o['revenue'])
        if o['reserve'] is not None: group_reserves[g].append(o['reserve'])
        if o['ai']      is not None: group_ais[g].append(o['ai'])
        if o['prog']    is not None: group_progs[g].append(o['prog'])

    thin_cells = sum(1 for c, v in cell_revenues.items() if len(v) < MIN_CELL)
    log(f'Thin cells (< {MIN_CELL} orgs, using group fallback): {thin_cells}')

    # ── Score all orgs in bulk per cell (fast numpy path) ────────────────────
    log('Computing scores (bulk numpy)...')
    t0 = time.time()

    # Group orgs by scoring pool key (cell if large enough, else group)
    pool_key = {}
    for o in orgs:
        c, g = o['cell'], o['group']
        use_cell = len(cell_revenues[c]) >= MIN_CELL
        pool_key[o['ein']] = c if use_cell else f"__group__{g}"

    # Build merged pools for thin-cell fallback
    for g in GROUPS:
        k = f"__group__{g}"
        cell_revenues[k] = group_revenues[g]
        cell_reserves[k] = group_reserves[g]
        cell_ais[k]      = group_ais[g]
        cell_progs[k]    = group_progs[g]

    # Compute bulk percentiles per pool
    from collections import defaultdict as dd
    pool_orgs = dd(list)
    for o in orgs:
        pool_orgs[pool_key[o['ein']]].append(o)

    scored = []
    for pool, pool_list in pool_orgs.items():
        g_sample = pool_list[0]['group']
        w_rev, w_res, w_ai, w_prog = WEIGHTS[g_sample]

        rev_pcts  = bulk_percentile_ranks([o['revenue'] for o in pool_list])
        res_pcts  = bulk_percentile_ranks([o['reserve'] for o in pool_list])
        ai_pcts   = bulk_percentile_ranks([o['ai']      for o in pool_list])
        prog_pcts = bulk_percentile_ranks([o['prog']    for o in pool_list])

        for i, o in enumerate(pool_list):
            total_w = w_rev
            total_s = w_rev * rev_pcts[i]

            if o['reserve'] is not None and w_res > 0:
                total_w += w_res; total_s += w_res * res_pcts[i]

            if o['ai'] is not None and w_ai > 0:
                total_w += w_ai; total_s += w_ai * ai_pcts[i]

            if o['prog'] is not None and w_prog > 0:
                total_w += w_prog; total_s += w_prog * prog_pcts[i]

            score = round(max(0.0, min(100.0, total_s / total_w if total_w > 0 else 50.0)), 2)
            scored.append({
                'ein':     o['ein'],
                'score':   score,
                'tier':    score_to_tier(score),
                'band':    score_to_band(score),
                'group':   o['group'],
                'cell':    o['cell'],
                'n_peers': len(cell_revenues[pool]),
            })

    elapsed = time.time() - t0
    log(f'Scoring complete: {len(scored):,} orgs in {elapsed:.1f}s ({len(scored)/elapsed:.0f}/s)')

    # ── Score distribution summary ────────────────────────────────────────────
    all_scores = [o['score'] for o in scored]
    log(f'Score distribution:')
    log(f'  Mean:   {statistics.mean(all_scores):.2f}')
    log(f'  Median: {statistics.median(all_scores):.2f}')
    log(f'  StdDev: {statistics.stdev(all_scores):.2f}')
    for threshold, label in TIER_THRESHOLDS:
        count = sum(1 for s in all_scores if s >= threshold)
        log(f'  {label:<20} {count:>8,} ({count/len(all_scores)*100:.1f}%)')

    if args.dry_run:
        log('DRY RUN — not writing to DB')
        return

    # ── Write scores to DB ────────────────────────────────────────────────────
    log('Writing scores to DB...')
    t1 = time.time()
    conn2 = sqlite3.connect(str(DB))
    batch = []

    for o in scored:
        batch.append((o['score'], o['tier'], o['band'], o['ein']))
        if len(batch) >= 5000:
            conn2.executemany(
                "UPDATE registry_enriched SET merit_score=?, merit_tier=?, merit_band=? WHERE EIN=?",
                batch
            )
            conn2.commit()
            batch = []

    if batch:
        conn2.executemany(
            "UPDATE registry_enriched SET merit_score=?, merit_tier=?, merit_band=? WHERE EIN=?",
            batch
        )
        conn2.commit()

    conn2.close()
    conn.close()

    elapsed = time.time() - t1
    log(f'Wrote {len(scored):,} scores in {elapsed:.1f}s')

    # ── Log the scoring run ───────────────────────────────────────────────────
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from scoring_audit import start_run, complete_run
        run_id = start_run(SCORER_VERSION, {
            'universe': 'deductibility=1, not revoked',
            'groups': list(GROUPS.keys()),
            'total_scored': len(scored),
        })
        complete_run(run_id, len(scored), 0)
        log(f'Scoring run logged (run_id={run_id})')
    except Exception as e:
        log(f'scoring_audit skipped: {e}')

    log('=' * 65)
    log(f'v2.0 scoring complete. {len(scored):,} orgs scored.')
    log('Next: rebuild FTS index → restart API')
    log('=' * 65)

if __name__ == '__main__':
    main()
