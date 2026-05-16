#!/usr/bin/env python3
"""
MERIT Score Engine — v1.0
Calculates peer-benchmarked MERIT scores from 990 data.
"""
import json, argparse, math
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev

WEIGHTS = {
    'program_ratio': 0.30,
    'fundraising_efficiency': 0.15,
    'liability_ratio': 0.15,
    'admin_ratio': 0.10,
    'revenue_growth': 0.20,
    'reserves_ratio': 0.10,
}

PEER_BANDS = [(0, 100_000),(100_000, 500_000),(500_000, 1_000_000),(1_000_000, 5_000_000),(5_000_000, 20_000_000),(20_000_000, 100_000_000),(100_000_000, float('inf'))]

def get_revenue_band(revenue):
    for i, (low, high) in enumerate(PEER_BANDS):
        if low <= revenue < high: return i
    return len(PEER_BANDS) - 1

def get_peer_group(org):
    ntee = str(org.get('ntee_code', org.get('ntee', ''))).strip().upper()
    ntee_major = ntee[:2] if len(ntee) >= 2 else 'UN'
    revenue = org.get('total_revenue', org.get('revenue', 0))
    try: revenue = float(revenue)
    except: revenue = 0
    band = get_revenue_band(revenue)
    return f"{ntee_major}_{band}"

def safe_divide(numerator, denominator):
    try:
        n, d = float(numerator), float(denominator)
        if d == 0: return None
        return n / d
    except: return None

def calculate_raw_metrics(org):
    total_rev = safe_divide(org.get('total_revenue', 0), 1) or 0
    total_exp = safe_divide(org.get('total_expenses', 0), 1) or 0
    program_exp = safe_divide(org.get('program_expenses', org.get('program_service_expenses', 0)), 1) or 0
    admin_exp = safe_divide(org.get('administrative_expenses', 0), 1) or 0
    fundraising_exp = safe_divide(org.get('fundraising_expenses', 0), 1) or 0
    total_assets = safe_divide(org.get('total_assets', 0), 1) or 0
    total_liab = safe_divide(org.get('total_liabilities', 0), 1) or 0
    net_assets = safe_divide(org.get('net_assets', 0), 1) or 0
    metrics = {}
    metrics['program_ratio'] = safe_divide(program_exp, total_exp)
    pf_sum = program_exp + fundraising_exp
    metrics['fundraising_efficiency'] = safe_divide(program_exp, pf_sum) if pf_sum > 0 else None
    metrics['liability_ratio'] = safe_divide(total_liab, total_assets)
    metrics['admin_ratio'] = safe_divide(admin_exp, total_exp)
    history = org.get('revenue_history', [])
    if len(history) >= 2:
        try:
            latest = float(history[-1]); earliest = float(history[0]); years = len(history) - 1
            if earliest > 0 and latest > 0: metrics['revenue_growth'] = (latest / earliest) ** (1/years) - 1
        except: metrics['revenue_growth'] = None
    else: metrics['revenue_growth'] = 0.0
    metrics['reserves_ratio'] = safe_divide(net_assets, total_exp)
    return metrics

def percentile_rank(value, peer_values, higher_is_better=True):
    if value is None: return 50.0
    clean = [v for v in peer_values if v is not None]
    if not clean: return 50.0
    if not higher_is_better: value = -value; clean = [-v for v in clean]
    below = sum(1 for v in clean if v < value)
    equal = sum(1 for v in clean if v == value)
    n = len(clean)
    pct = (below + equal / 2) / n * 100
    return round(pct, 1)

def score_band(score):
    if score >= 90: return "Exceptional"
    elif score >= 75: return "Strong"
    elif score >= 60: return "Solid"
    elif score >= 40: return "Mixed"
    else: return "Concerns"

def calculate_merit_score(org, peer_groups):
    peer_key = get_peer_group(org)
    peers = peer_groups.get(peer_key, [])
    if len(peers) < 5:
        ntee = str(org.get('ntee_code', org.get('ntee', ''))).strip().upper()
        ntee_major = ntee[:1] if len(ntee) >= 1 else 'U'
        revenue = org.get('total_revenue', org.get('revenue', 0))
        try: revenue = float(revenue)
        except: revenue = 0
        band = get_revenue_band(revenue)
        fallback_key = f"{ntee_major}_{band}"
        peers = peer_groups.get(fallback_key, peers)
    if len(peers) < 2:
        return {'merit_score': None, 'merit_band': 'Insufficient Data', 'peer_group': peer_key, 'peer_count': len(peers), 'metrics': {}, 'percentiles': {}, 'methodology_version': '1.0'}
    my_metrics = calculate_raw_metrics(org)
    peer_distributions = defaultdict(list)
    for p in peers:
        pm = calculate_raw_metrics(p)
        for k, v in pm.items(): peer_distributions[k].append(v)
    percentiles = {}
    for metric in ['program_ratio', 'fundraising_efficiency', 'revenue_growth', 'reserves_ratio']:
        percentiles[metric] = percentile_rank(my_metrics.get(metric), peer_distributions[metric], higher_is_better=True)
    for metric in ['liability_ratio', 'admin_ratio']:
        percentiles[metric] = percentile_rank(my_metrics.get(metric), peer_distributions[metric], higher_is_better=False)
    total_weight = 0; weighted_sum = 0
    for metric, weight in WEIGHTS.items():
        pct = percentiles.get(metric)
        if pct is not None:
            weighted_sum += pct * weight
            total_weight += weight
    final_score = weighted_sum / total_weight if total_weight > 0 else 50.0
    final_score = round(max(0, min(100, final_score)))
    return {'merit_score': final_score, 'merit_band': score_band(final_score), 'peer_group': peer_key, 'peer_count': len(peers), 'metrics': {k: round(v, 4) if v is not None else None for k, v in my_metrics.items()}, 'percentiles': percentiles, 'methodology_version': '1.0'}

def build_peer_groups(orgs):
    groups = defaultdict(list)
    for org in orgs:
        key = get_peer_group(org)
        groups[key].append(org)
        ntee = str(org.get('ntee_code', org.get('ntee', ''))).strip().upper()
        ntee_major = ntee[:1] if len(ntee) >= 1 else 'U'
        revenue = org.get('total_revenue', org.get('revenue', 0))
        try: revenue = float(revenue)
        except: revenue = 0
        band = get_revenue_band(revenue)
        broad_key = f"{ntee_major}_{band}"
        if broad_key != key: groups[broad_key].append(org)
    return groups

def main():
    parser = argparse.ArgumentParser(description="Calculate MERIT scores")
    parser.add_argument("--input", required=True, help="Input JSON with org records")
    parser.add_argument("--output", required=True, help="Output JSON for scored orgs")
    args = parser.parse_args()
    print(f"Loading orgs from {args.input}...")
    with open(args.input, 'r') as f: data = json.load(f)
    orgs = data if isinstance(data, list) else data.get('organizations', [])
    print(f"Loaded {len(orgs)} organizations")
    print("Building peer groups...")
    peer_groups = build_peer_groups(orgs)
    print(f"Created {len(peer_groups)} peer groups")
    sizes = [len(v) for v in peer_groups.values()]
    print(f"Peer group sizes: min={min(sizes)}, max={max(sizes)}, median={sorted(sizes)[len(sizes)//2]}")
    print("Calculating MERIT scores...")
    scored = []; score_distribution = defaultdict(int)
    for org in orgs:
        result = calculate_merit_score(org, peer_groups)
        org['_merit'] = result
        scored.append(org)
        if result['merit_score'] is not None: score_distribution[result['merit_band']] += 1
    print("\nScore distribution:")
    for band, count in sorted(score_distribution.items()): print(f"  {band}: {count}")
    with open(args.output, 'w') as f: json.dump(scored, f, indent=2)
    print(f"\nSaved to {args.output}")
    print("\nNext: 1) Review distribution 2) Tune WEIGHTS if needed 3) Port to CMS 4) Build /methodology page")

if __name__ == "__main__": main()
