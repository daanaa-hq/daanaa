#!/usr/bin/env python3
"""
MERIT Score Engine v3 — Uses xml_extracted.json (real 990 data)
Cross-references NTEE from ProPublica cache for peer grouping.
"""
import json, argparse
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"

WEIGHTS = {
    'program_ratio': 0.30,      # PROGRAM_EXPENSES / TOTAL_EXPENSES (higher = better)
    'sustainability_ratio': 0.25,  # REVENUE / TOTAL_EXPENSES (>=1 = good)
    'reserves_ratio': 0.25,     # NET_ASSETS / TOTAL_EXPENSES (runway months)
    'leverage_ratio': 0.20,     # NET_ASSETS / TOTAL_ASSETS (financial independence)
}

PEER_BANDS = [
    (0, 100_000), (100_000, 500_000), (500_000, 1_000_000),
    (1_000_000, 5_000_000), (5_000_000, 20_000_000),
    (20_000_000, 100_000_000), (100_000_000, float('inf'))
]

def load_ntee_lookup():
    """Build EIN -> NTEE lookup from ProPublica cache."""
    cache_dir = DATA / "propublica_cache"
    lookup = {}
    for f in cache_dir.glob("*.json"):
        try:
            with open(f) as fh:
                d = json.load(fh)
            org = d.get('organization', {})
            ein = str(org.get('ein', '')).strip()
            ntee = str(org.get('ntee_code', '')).strip().upper()
            if ein and ntee and ntee != 'NON':
                lookup[ein] = ntee
        except:
            pass
    print(f"Loaded NTEE lookup: {len(lookup)} EINs")
    return lookup

def get_revenue_band(rev):
    for i, (low, high) in enumerate(PEER_BANDS):
        if low <= rev < high:
            return i
    return len(PEER_BANDS) - 1

def get_peer_key(ein, ntee_lookup, revenue):
    ntee = ntee_lookup.get(ein, 'UN')
    ntee_major = ntee[:2] if len(ntee) >= 2 else 'UN'
    try:
        rev = float(revenue)
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
    if score >= 90: return "Exceptional"
    elif score >= 75: return "Strong"
    elif score >= 60: return "Solid"
    elif score >= 40: return "Mixed"
    else: return "Concerns"

def calculate_merit(ein, org, ntee_lookup, peer_groups):
    peer_key = get_peer_key(ein, ntee_lookup, org.get('REVENUE', 0))
    peers = peer_groups.get(peer_key, [])
    
    # Fallback to broader group
    if len(peers) < 5:
        ntee = ntee_lookup.get(ein, 'UN')
        ntee_major = ntee[:1] if len(ntee) >= 1 else 'U'
        try:
            rev = float(org.get('REVENUE', 0))
        except:
            rev = 0
        band = get_revenue_band(rev)
        fallback = f"{ntee_major}_{band}"
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
        'version': '3.0'
    }

def build_peer_groups(xml_data, ntee_lookup):
    groups = defaultdict(list)
    for ein, org in xml_data.items():
        key = get_peer_key(ein, ntee_lookup, org.get('REVENUE', 0))
        groups[key].append(org)
        # Broad fallback
        ntee = ntee_lookup.get(ein, 'UN')
        ntee_major = ntee[:1] if len(ntee) >= 1 else 'U'
        try:
            rev = float(org.get('REVENUE', 0))
        except:
            rev = 0
        band = get_revenue_band(rev)
        broad = f"{ntee_major}_{band}"
        if broad != key:
            groups[broad].append(org)
    return groups

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output JSON")
    parser.add_argument("--sample", type=int, default=0, help="Process N orgs (0=all)")
    args = parser.parse_args()
    
    print("Loading xml_extracted.json...")
    with open(DATA / "xml_extracted.json") as f:
        xml_data = json.load(f)
    print(f"Loaded {len(xml_data)} organizations with 990 data")
    
    print("Loading NTEE lookup from ProPublica cache...")
    ntee_lookup = load_ntee_lookup()
    
    # Filter to orgs that have both 990 data and NTEE
    scorable = {}
    for ein, org in xml_data.items():
        if ntee_lookup.get(ein):
            scorable[ein] = org
    print(f"Scorable orgs (have 990 + NTEE): {len(scorable)}")
    
    orgs = list(scorable.items())
    if args.sample > 0:
        orgs = orgs[:args.sample]
    
    print("Building peer groups...")
    peer_groups = build_peer_groups(scorable, ntee_lookup)
    print(f"Peer groups: {len(peer_groups)}")
    sizes = [len(v) for v in peer_groups.values()]
    print(f"Sizes: min={min(sizes)}, max={max(sizes)}, median={sorted(sizes)[len(sizes)//2]}")
    
    print("Calculating MERIT scores...")
    scored = {}
    bands = defaultdict(int)
    scores = []
    
    for ein, org in orgs:
        result = calculate_merit(ein, org, ntee_lookup, peer_groups)
        scored[ein] = {
            'org': org,
            'merit': result
        }
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

if __name__ == "__main__":
    main()
