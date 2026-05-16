#!/usr/bin/env python3
"""
AGENT 2: SCORE CALCULATOR
Mission: Fix broken MERIT score, build all 5 gauges.
"""
import os, glob, sys, json
import pandas as pd
import numpy as np

print("[AGENT 2] Loading data sources...")

master = pd.read_csv("data/csv/master_orgs.csv", dtype=str)
master['EIN'] = master['EIN'].astype(str).str.replace('.0', '').str.strip()
print(f"[AGENT 2] Master orgs: {len(master)}")

fin = pd.read_csv("data/csv/extracted_financials.csv", dtype=str)
fin['ein'] = fin['ein'].astype(str).str.replace('.0', '').str.strip()
fin_cols = {c: c + '_ext' for c in fin.columns if c != 'ein'}
fin.rename(columns=fin_cols, inplace=True)
print(f"[AGENT 2] Extracted financials: {len(fin)}")

pct_files = sorted(glob.glob("data/csv/percentile_engine_*.csv"), reverse=True)
pct = pd.DataFrame()
if pct_files:
    pct = pd.read_csv(pct_files[0], dtype=str)
    pct['ein'] = pct['ein'].astype(str).str.replace('.0', '').str.strip()
    pct = pct.rename(columns={'ein': 'EIN'})
    print(f"[AGENT 2] Percentile engine: {len(pct)} rows")
else:
    print("[AGENT 2] No percentile engine found")

df = master.merge(fin, left_on='EIN', right_on='ein', how='left')
df.drop(columns=['ein'], inplace=True, errors='ignore')
if not pct.empty and 'percentile' in pct.columns:
    df = df.merge(pct[['EIN', 'percentile']], on='EIN', how='left')
    df['percentile'] = pd.to_numeric(df['percentile'], errors='coerce')
else:
    df['percentile'] = np.nan

print(f"[AGENT 2] Merged dataset: {len(df)} rows")

num_cols = ['total_revenue_ext', 'contributions_ext', 'total_expenses_ext', 
            'program_expenses_ext', 'mgmt_expenses_ext', 'fundraising_expenses_ext',
            'total_assets_ext', 'net_assets_ext']
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')

df['revenue_num'] = pd.to_numeric(df.get('revenue', df.get('REVENUE')), errors='coerce')

def revenue_band(r):
    if pd.isna(r): return 'Unknown'
    if r < 50000: return '0-50K'
    if r < 200000: return '50K-200K'
    if r < 1000000: return '200K-1M'
    if r < 5000000: return '1M-5M'
    return '5M+'

df['revenue_band'] = df['revenue_num'].apply(revenue_band)

print("[AGENT 2] Building peer cohorts...")
peer_medians = {}
for (ntee, state, band), group in df.groupby(['NTEE', 'STATE', 'revenue_band']):
    if len(group) >= 5:
        peer_medians[(ntee, state, band)] = {
            'program_ratio_median': group['program_expenses_ext'].sum() / group['total_expenses_ext'].sum() if group['total_expenses_ext'].sum() > 0 else np.nan,
            'revenue_median': group['revenue_num'].median(),
            'count': len(group)
        }

df['financial_health'] = df['percentile'].fillna(50)

def rough_percentile(row):
    peers = df[(df['NTEE'] == row['NTEE']) & (df['STATE'] == row['STATE'])]
    if len(peers) < 5:
        peers = df[df['NTEE'] == row['NTEE']]
    if len(peers) < 2:
        return 50.0
    return (peers['revenue_num'] < row['revenue_num']).mean() * 100

mask = df['financial_health'].isna()
df.loc[mask, 'financial_health'] = df[mask].apply(rough_percentile, axis=1)
df['financial_health'] = df['financial_health'].clip(0, 100).round(1)

print("[AGENT 2] Calculating Operational Efficiency...")
df['program_ratio'] = (df['program_expenses_ext'] / df['total_expenses_ext']).clip(0, 1)

def peer_program_median(row):
    key = (row['NTEE'], row['STATE'], row['revenue_band'])
    if key in peer_medians and peer_medians[key]['count'] >= 5:
        return peer_medians[key]['program_ratio_median']
    peers = df[df['NTEE'] == row['NTEE']]
    return (peers['program_expenses_ext'].sum() / peers['total_expenses_ext'].sum()) if peers['total_expenses_ext'].sum() > 0 else 0.75

df['peer_median_program_ratio'] = df.apply(peer_program_median, axis=1)
df['operational_efficiency'] = ((df['program_ratio'] - df['peer_median_program_ratio']) / df['peer_median_program_ratio'].replace(0, 0.75) * 50 + 50).clip(0, 100).round(1)
no_prog = df['program_ratio'].isna()
df.loc[no_prog, 'operational_efficiency'] = df[no_prog].groupby('NTEE')['revenue_num'].transform(lambda x: x.rank(pct=True) * 100).fillna(50)

print("[AGENT 2] Calculating Sustainability...")
monthly_burn = df['total_expenses_ext'] / 12
df['months_runway'] = (df['net_assets_ext'] / monthly_burn.replace(0, np.nan)).clip(0, 120)
df['sustainability_score'] = (df['months_runway'] / 24 * 100).clip(0, 100).round(1)
df['sustainability_score'] = df['sustainability_score'].fillna(50)

print("[AGENT 2] Calculating Scale Trajectory...")
filing_counts = df.groupby('EIN').size().reset_index(name='filing_count')
df = df.merge(filing_counts, on='EIN', how='left')

def scale_score(row):
    fc = row['filing_count'] if pd.notna(row['filing_count']) else 1
    if fc >= 5: return 95.0
    if fc >= 3: return 75.0
    if fc == 2: return 55.0
    return 35.0

df['scale_trajectory'] = df.apply(scale_score, axis=1)

print("[AGENT 2] Calculating Compliance...")
def compliance_score(row):
    fc = row['filing_count'] if pd.notna(row['filing_count']) else 1
    mapping = {1: 20, 2: 40, 3: 60, 4: 80}
    return mapping.get(min(fc, 5), 100)

df['compliance_score'] = df.apply(compliance_score, axis=1)

def confidence(row):
    fc = row['filing_count'] if pd.notna(row['filing_count']) else 1
    has_program = pd.notna(row['program_ratio'])
    if fc >= 3 and has_program: return 'High'
    if fc >= 2 or has_program: return 'Medium'
    return 'Low'

df['confidence'] = df.apply(confidence, axis=1)

print("[AGENT 2] Building composite MERIT Score...")
df['MERIT_score'] = (
    df['financial_health'] * 0.35 +
    df['operational_efficiency'].fillna(50) * 0.30 +
    df['sustainability_score'] * 0.20 +
    df['compliance_score'] * 0.15
).clip(0, 100).round(1)

print(f"[AGENT 2] MERIT Score stats: min={df['MERIT_score'].min():.1f}, max={df['MERIT_score'].max():.1f}, mean={df['MERIT_score'].mean():.1f}, unique={df['MERIT_score'].nunique()}")

df['overhead_ratio'] = ((df['mgmt_expenses_ext'] + df['fundraising_expenses_ext']) / df['total_expenses_ext']).clip(0, 1)
df['fundraising_efficiency'] = (df['fundraising_expenses_ext'] / df['contributions_ext'].replace(0, np.nan)).clip(0, 10)

def plain_english_gauge(score, gauge_name):
    if pd.isna(score): return 'Insufficient Data'
    if gauge_name == 'financial_health':
        if score >= 80: return 'Well Funded'
        if score >= 60: return 'Adequately Funded'
        if score >= 40: return 'Moderately Funded'
        return 'Limited Funding'
    if gauge_name == 'operational_efficiency':
        if score >= 80: return 'Highly Efficient'
        if score >= 60: return 'Above Average Efficiency'
        if score >= 40: return 'Average Efficiency'
        return 'Below Average Efficiency'
    if gauge_name == 'sustainability':
        if score >= 80: return 'Very Stable'
        if score >= 60: return 'Stable'
        if score >= 40: return 'Moderate Risk'
        return 'High Risk'
    if gauge_name == 'scale':
        if score >= 80: return 'Growing Rapidly'
        if score >= 60: return 'Growing'
        if score >= 40: return 'Stable'
        return 'Early Stage'
    if gauge_name == 'compliance':
        if score >= 80: return 'Excellent Record'
        if score >= 60: return 'Good Record'
        if score >= 40: return 'Adequate Record'
        return 'Limited History'
    return 'Unknown'

df['financial_health_label'] = df['financial_health'].apply(lambda x: plain_english_gauge(x, 'financial_health'))
df['operational_efficiency_label'] = df['operational_efficiency'].apply(lambda x: plain_english_gauge(x, 'operational_efficiency'))
df['sustainability_label'] = df['sustainability_score'].apply(lambda x: plain_english_gauge(x, 'sustainability'))
df['scale_label'] = df['scale_trajectory'].apply(lambda x: plain_english_gauge(x, 'scale'))
df['compliance_label'] = df['compliance_score'].apply(lambda x: plain_english_gauge(x, 'compliance'))

def cohort_size(row):
    key = (row['NTEE'], row['STATE'], row['revenue_band'])
    if key in peer_medians:
        return peer_medians[key]['count']
    return df[(df['NTEE'] == row['NTEE']) & (df['STATE'] == row['STATE'])].shape[0]

df['cohort_size'] = df.apply(cohort_size, axis=1)
df['cohort_warning'] = df['cohort_size'].apply(lambda x: 'Insufficient peer data (<30 peers)' if x < 30 else '')

OUT = "data/csv/scored_orgs.csv"
df.to_csv(OUT, index=False)
print(f"[AGENT 2] Wrote scored master to {OUT}")
print(f"[AGENT 2] OE coverage: {df['operational_efficiency'].notna().sum()}/{len(df)} ({df['operational_efficiency'].notna().mean()*100:.1f}%)")
