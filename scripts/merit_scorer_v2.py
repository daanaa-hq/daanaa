#!/usr/bin/env python3
import json, argparse
from pathlib import Path
from collections import defaultdict

WEIGHTS = {
    'reserves_ratio': 0.25,
    'leverage_ratio': 0.25,
    'revenue_growth': 0.25,
    'sustainability_ratio': 0.25,
}

PEER_BANDS = [
    (0, 100_000), (100_000, 500_000), (500_000, 1_000_000),
    (1_000_000, 5_000_000), (5_000_000, 20_000_000),
    (20_000_000, 100_000_000), (100_000_000, float('inf'))
]

def get_revenue_band(rev):
    for i, (low, high) in enumerate(PEER_BANDS):
        if low <= rev < high:
            return i
    return len(PEER_BANDS) - 1

def get_peer_key(org_meta, latest_filing):
    ntee = str(org_meta.get('ntee_code', org_meta.get('ntee_classification', ''))).strip().upper()
    ntee_major = ntee[:2] if len(ntee) >= 2 else 'UN'
    rev = latest_filing.get('total_revenue', 0)
    try:
        rev = float(rev)
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

def extract_metrics(org_meta, filings):
    if not filings:
        return {}
    try:
        sorted_filings = sorted(filings, key=lambda f: str(f.get('tax_period', '')), reverse=True)
    except:
        sorted_filings = filings
    latest = sorted_filings[0]
    metrics = {}
    net_assets = latest.get('net_assets_eoy', latest.get('net_assets_boy', 0))
    total_exp = latest.get('total_expenses', 0)
    metrics['reserves_ratio'] = safe_div(net_assets, total_exp)
    total_assets = latest.get('total_assets_eoy', latest.get('total_assets_boy', 0))
    total_liab = latest.get('total_liabilities_eoy', latest.get('total_liabilities_boy', 0))
    lev = safe_div(total_liab, total_assets)
    metrics['leverage_ratio'] = 1.0 - lev if lev is not None else None
    revenues = []
    for f in sorted_filings:
        rev = f.get('total_revenue')
        if rev is not None:
            try:
                revenues.append(float(rev))
            except:
                pass
    if len(revenues) >= 2:
        try:
            latest_rev = revenues[0]
            oldest_rev = revenues[-1]
            years = len(revenues) - 1
            if oldest_rev > 0 and latest_rev > 0:
                metrics['revenue_growth'] = (latest_rev / oldest_rev) ** (1.0 / years) - 1
        except:
            metrics['revenue_growth'] = 0.0
    else:
        metrics['revenue_growth'] = 0.0
    total_rev = latest.get('total_revenue', 0)
    metrics['sustainability_ratio'] = safe_div(total_rev, total_exp)
    metrics['_tax_period'] = str(latest.get('tax_period', ''))
    metrics['_filing_count'] = len(filings)
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
    if score >= 90:
        return "Exceptional"
    elif score >= 75:
        return "Strong"
    elif score >= 60:
        return "Solid"
    elif score >= 40:
        return "Mixed"
    else:
        return "Concerns"

def calculate_merit(cache_data, peer_groups):
    org_meta = cache_data.get('organization', {})
    filings = cache_data.get('filings_with_data', [])
    if not org_meta or not filings:
        return None
    peer_key = get_peer_key(org_meta, filings[0] if filings else {})
    peers = peer_groups.get(peer_key, [])
    if len(peers) < 5:
        ntee = str(org_meta.get('ntee_code', org_meta.get('ntee_classification', ''))).strip().upper()
        ntee_major = ntee[:1] if len(ntee) >= 1 else 'U'
        rev = filings[0].get('total_revenue', 0) if filings else 0
        try:
            rev = float(rev)
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
    my_metrics = extract_metrics(org_meta, filings)
    peer_dists = defaultdict(list)
    for p in peers:
        pm = extract_metrics(p.get('organization', {}), p.get('filings_with_data', []))
        for k, v in pm.items():
            if not k.startswith('_'):
                peer_dists[k].append(v)
    percentiles = {}
    for metric in ['reserves_ratio', 'leverage_ratio', 'revenue_growth', 'sustainability_ratio']:
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
        'metrics': {k: round(v, 4) if v is not None else None for k, v in my_metrics.items() if not k.startswith('_')},
        'percentiles': percentiles,
        'version': '2.0'
    }

def build_peer_groups(cache_files):
    groups = defaultdict(list)
    for f in cache_files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            org = data.get('organization', {})
            filings = data.get('filings_with_data', [])
            if not org or not filings:
                continue
            key = get_peer_key(org, filings[0])
            groups[key].append(data)
            ntee = str(org.get('ntee_code', org.get('ntee_classification', ''))).strip().upper()
            ntee_major = ntee[:1] if len(ntee) >= 1 else 'U'
            rev = filings[0].get('total_revenue', 0)
            try:
                rev = float(rev)
            except:
                rev = 0
            band = get_revenue_band(rev)
            broad = f"{ntee_major}_{band}"
            if broad != key:
                groups[broad].append(data)
        except:
            pass
    return groups

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="data/propublica_cache", help="Directory with cache JSONs")
    parser.add_argument("--output", required=True, help="Output JSON")
    parser.add_argument("--sample", type=int, default=0, help="Process N files (0=all)")
    args = parser.parse_args()
    cache_dir = Path(args.input_dir)
    files = sorted(cache_dir.glob("*.json"))
    if args.sample > 0:
        files = files[:args.sample]
    print(f"Processing {len(files)} cache files...")
    print("Building peer groups...")
    peer_groups = build_peer_groups(files)
    print(f"Peer groups: {len(peer_groups)}")
    sizes = [len(v) for v in peer_groups.values()]
    print(f"Sizes: min={min(sizes)}, max={max(sizes)}, median={sorted(sizes)[len(sizes)//2]}")
    print("Scoring...")
    scored = []
    bands = defaultdict(int)
    scores = []
    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            result = calculate_merit(data, peer_groups)
            if result:
                data['_merit'] = result
                scored.append(data)
                if result['merit_score'] is not None:
                    bands[result['merit_band']] += 1
                    scores.append(result['merit_score'])
        except:
            pass
    print(f"\nScored {len(scored)} organizations")
    print("Band distribution:")
    for b, c in sorted(bands.items()):
        print(f"  {b}: {c}")
    if scores:
        print(f"Score range: {min(scores)} - {max(scores)}")
        print(f"Mean: {sum(scores)/len(scores):.1f}")
    with open(args.output, 'w') as f:
        json.dump(scored, f, indent=2)
    print(f"\nSaved to {args.output}")

if __name__ == "__main__":
    main()
