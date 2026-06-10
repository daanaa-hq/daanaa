#!/usr/bin/env python3
"""
MERIT Score Engine v3.3 — Reads NTEE from xml_extracted.json directly
Expands scorable set from ~11k to ~15k+ orgs
"""
import json, argparse, sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from scoring_audit import start_run, complete_run

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"

WEIGHTS = {
    'program_ratio': 0.30,
    'sustainability_ratio': 0.25,
    'reserves_ratio': 0.25,
    'leverage_ratio': 0.20,
}

PEER_BANDS = [
    (0, 100_000), (100_000, 500_000), (500_000, 1_000_000),
    (1_000_000, 5_000_000), (5_000_000, 20_000_000),
    (20_000_000, 100_000_000), (100_000_000, float('inf'))
]

def load_xml_data():
    """Load xml_extracted.json — has 990 data + NTEE + mission."""
    with open(DATA / "xml_extracted.json") as f:
        return json.load(f)

def get_revenue_band(rev):
    for i, (low, high) in enumerate(PEER_BANDS):
        if low <= rev < high:
            return i
    return len(PEER_BANDS) - 1

def get_peer_key(ein, org):
    ntee = str(org.get('NTEE', '')).strip().upper()
    ntee_major = ntee[:1] if len(ntee) >= 1 else 'U'
    try:
        rev = float(org.get('REVENUE', 0))
    except:
        rev = 0
    band = get_revenue_band(rev)
    return f"{ntee_major}_{band}"

def safe_div(n, d):
    try:
        nn, dd = float(n), float(d)
        return nn / dd if dd != 0 else None
    except:
        return None

def extract_metrics(org):
    metrics = {}
    total_exp = org.get('TOTAL_EXPENSES', 0)
    program_exp = org.get('PROGRAM_EXPENSES', 0)
    revenue = org.get('REVENUE', 0)
    net_assets = org.get('NET_ASSETS', 0)
    total_assets = org.get('TOTAL_ASSETS', 0)
    metrics['program_ratio'] = safe_div(program_exp, total_exp)
    metrics['sustainability_ratio'] = safe_div(revenue, total_exp)
    metrics['reserves_ratio'] = safe_div(net_assets, total_exp)
    metrics['leverage_ratio'] = safe_div(net_assets, total_assets)
    return metrics

def percentile_rank(value, peer_values, higher_is_better=True):
    if value is None:
        return 50.0
    clean = [v for v in peer_values if v is not None]
    if not clean:
        return 50.0
    if not higher_is_better:
        value = -value
        clean = [-v for v in clean]
    below = sum(1 for v in clean if v < value)
    equal = sum(1 for v in clean if v == value)
    n = len(clean)
    return round((below + equal / 2.0) / n * 100, 1)

def score_band(score):
    if score >= 85: return "Blazing"
    elif score >= 70: return "Burning Bright"
    elif score >= 55: return "Steady Flame"
    elif score >= 35: return "Growing"
    else: return "Just Starting"

def calculate_merit(ein, org, peer_groups):
    peer_key = get_peer_key(ein, org)
    peers = peer_groups.get(peer_key, [])
    
    if len(peers) < 5:
        try:
            rev = float(org.get('REVENUE', 0))
        except:
            rev = 0
        band = get_revenue_band(rev)
        fallback = f"ALL_{band}"
        peers = peer_groups.get(fallback, peers)
    
    if len(peers) < 2:
        return {
            'merit_score': None,
            'merit_band': 'Insufficient Data',
            'peer_group': peer_key,
            'peer_count': len(peers),
            'metrics': {},
            'percentiles': {}
        }
    
    my_metrics = extract_metrics(org)
    peer_dists = defaultdict(list)
    for p in peers:
        pm = extract_metrics(p)
        for k, v in pm.items():
            peer_dists[k].append(v)
    
    percentiles = {}
    for metric in ['program_ratio', 'sustainability_ratio', 'reserves_ratio', 'leverage_ratio']:
        pct = percentile_rank(my_metrics.get(metric), peer_dists.get(metric, []), higher_is_better=True)
        percentiles[metric] = pct
    
    total_weight = 0
    weighted_sum = 0
    for metric, weight in WEIGHTS.items():
        pct = percentiles.get(metric)
        if pct is not None:
            weighted_sum += pct * weight
            total_weight += weight
    
    final = weighted_sum / total_weight if total_weight > 0 else 50.0
    final = round(max(0, min(100, final)))
    
    return {
        'merit_score': final,
        'merit_band': score_band(final),
        'peer_group': peer_key,
        'peer_count': len(peers),
        'metrics': {k: round(v, 4) if v is not None else None for k, v in my_metrics.items()},
        'percentiles': percentiles,
        'version': '3.3'
    }

def build_peer_groups(xml_data):
    groups = defaultdict(list)
    for ein, org in xml_data.items():
        key = get_peer_key(ein, org)
        groups[key].append(org)
        try:
            rev = float(org.get('REVENUE', 0))
        except:
            rev = 0
        band = get_revenue_band(rev)
        broad = f"ALL_{band}"
        if broad != key:
            groups[broad].append(org)
    return groups

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output JSON")
    parser.add_argument("--sample", type=int, default=0, help="Process N orgs (0=all)")
    parser.add_argument("--notes", default=None, help="Optional note logged to audit trail")
    args = parser.parse_args()

    input_file = str(DATA / "xml_extracted.json")
    run_id = start_run(scorer_version="3.3", input_file=input_file, notes=args.notes)

    print("Loading xml_extracted.json...")
    xml_data = load_xml_data()
    print(f"Loaded {len(xml_data)} organizations")
    
    # Filter to orgs with NTEE and financials
    scorable = {}
    for ein, org in xml_data.items():
        ntee = str(org.get('NTEE', '')).strip().upper()
        revenue = org.get('REVENUE', 0)
        expenses = org.get('TOTAL_EXPENSES', 0)
        if ntee and ntee not in ['NON', 'NONE', ''] and revenue and expenses:
            scorable[ein] = org
    
    print(f"Scorable orgs (have NTEE + 990 financials): {len(scorable)}")
    
    orgs = list(scorable.items())
    if args.sample > 0:
        orgs = orgs[:args.sample]
    
    print("Building peer groups...")
    peer_groups = build_peer_groups(scorable)
    print(f"Peer groups: {len(peer_groups)}")
    sizes = [len(v) for v in peer_groups.values()]
    print(f"Sizes: min={min(sizes)}, max={max(sizes)}, median={sorted(sizes)[len(sizes)//2]}")
    
    print("Calculating MERIT scores...")
    scored = {}
    bands = defaultdict(int)
    scores = []
    
    for ein, org in orgs:
        result = calculate_merit(ein, org, peer_groups)
        scored[ein] = {'org': org, 'merit': result}
        if result['merit_score'] is not None:
            bands[result['merit_band']] += 1
            scores.append(result['merit_score'])
    
    print(f"\nScored {len(scored)} organizations")
    print("Band distribution:")
    for b, c in sorted(bands.items()):
        print(f"  {b}: {c}")
    if scores:
        print(f"Score range: {min(scores)} - {max(scores)}")
        print(f"Mean: {sum(scores)/len(scores):.1f}")
        print(f"Median: {sorted(scores)[len(scores)//2]}")
    
    with open(args.output, 'w') as f:
        json.dump(scored, f, indent=2)
    print(f"\nSaved to {args.output}")

    complete_run(run_id, {
        "output_file":      args.output,
        "scorable_count":   len(scorable),
        "output_ein_count": len(scored),
        "peer_group_count": len(peer_groups),
        "scores":           scores,
        "bands":            dict(bands),
    })

if __name__ == "__main__":
    main()
