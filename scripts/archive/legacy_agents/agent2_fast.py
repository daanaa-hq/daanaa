#!/usr/bin/env python3
import os, glob, pandas as pd, numpy as np

print("[AGENT 2] Loading data...")
master = pd.read_csv("data/csv/master_orgs.csv", dtype=str)
master['EIN'] = master['EIN'].astype(str).str.replace('.0', '').str.strip()

fin = pd.read_csv("data/csv/extracted_financials.csv", dtype=str)
fin['ein'] = fin['ein'].astype(str).str.replace('.0', '').str.strip()
fin.rename(columns={c: c + '_ext' for c in fin.columns if c != 'ein'}, inplace=True)

pct_files = sorted(glob.glob("data/csv/percentile_engine_*.csv"), reverse=True)
pct = pd.DataFrame()
if pct_files:
    pct = pd.read_csv(pct_files[0], dtype=str)
    pct['ein'] = pct['ein'].astype(str).str.replace('.0', '').str.strip()

df = master.merge(fin, left_on='EIN', right_on='ein', how='left')
df.drop(columns=['ein'], inplace=True, errors='ignore')
if not pct.empty and 'percentile' in pct.columns:
    df = df.merge(pct[['ein', 'percentile']].rename(columns={'ein': 'EIN'}), on='EIN', how='left')
    df['percentile'] = pd.to_numeric(df['percentile'], errors='coerce')
else:
    df['percentile'] = np.nan

num_cols = ['total_revenue_ext', 'total_expenses_ext', 'program_expenses_ext', 
            'mgmt_expenses_ext', 'fundraising_expenses_ext', 'total_assets_ext', 'net_assets_ext']
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

# === FAST PEER COHORTS using transform ===
print("[AGENT 2] Building peer cohorts (vectorized)...")
df['program_ratio'] = (df['program_expenses_ext'] / df['total_expenses_ext']).clip(0, 1)

# Group-level median program ratio
df['peer_median_program_ratio'] = df.groupby(['NTEE', 'STATE', 'revenue_band'])['program_ratio'].transform('median')
# Fill missing with NTEE-only median
df['peer_median_program_ratio'] = df['peer_median_program_ratio'].fillna(
    df.groupby('NTEE')['program_ratio'].transform('median')
).fillna(0.75)

# OE Score
df['operational_efficiency'] = ((df['program_ratio'] - df['peer_median_program_ratio']) / 
                                 df['peer_median_program_ratio'].replace(0, 0.75) * 50 + 50).clip(0, 100).round(1)
no_prog = df['program_ratio'].isna()
df.loc[no_prog, 'operational_efficiency'] = df[no_prog].groupby('NTEE')['revenue_num'].transform(lambda x: x.rank(pct=True) * 100).fillna(50)

# Financial Health
df['financial_health'] = df['percentile'].fillna(50)
mask = df['financial_health'].isna()
df.loc[mask, 'financial_health'] = df[mask].groupby('NTEE')['revenue_num'].transform(lambda x: x.rank(pct=True) * 100).fillna(50)
df['financial_health'] = df['financial_health'].clip(0, 100).round(1)

# Sustainability
monthly_burn = df['total_expenses_ext'] / 12
df['months_runway'] = (df['net_assets_ext'] / monthly_burn.replace(0, np.nan)).clip(0, 120)
df['sustainability_score'] = (df['months_runway'] / 24 * 100).clip(0, 100).round(1).fillna(50)

# Scale & Compliance
filing_counts = df.groupby('EIN').size().reset_index(name='filing_count')
df = df.merge(filing_counts, on='EIN', how='left')

def scale_score(row):
    fc = row['filing_count'] if pd.notna(row['filing_count']) else 1
    if fc >= 5: return 95.0
    if fc >= 3: return 75.0
    if fc == 2: return 55.0
    return 35.0
df['scale_trajectory'] = df.apply(scale_score, axis=1)

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

# MERIT Score
df['MERIT_score'] = (
    df['financial_health'] * 0.35 +
    df['operational_efficiency'].fillna(50) * 0.30 +
    df['sustainability_score'] * 0.20 +
    df['compliance_score'] * 0.15
).clip(0, 100).round(1)

print(f"[AGENT 2] MERIT Score: min={df['MERIT_score'].min():.1f}, max={df['MERIT_score'].max():.1f}, mean={df['MERIT_score'].mean():.1f}")

# Labels
def plain_english(score, name):
    if pd.isna(score): return 'Insufficient Data'
    if name == 'financial_health':
        return 'Well Funded' if score >= 80 else 'Adequately Funded' if score >= 60 else 'Moderately Funded' if score >= 40 else 'Limited Funding'
    if name == 'operational_efficiency':
        return 'Highly Efficient' if score >= 80 else 'Above Average' if score >= 60 else 'Average' if score >= 40 else 'Below Average'
    if name == 'sustainability':
        return 'Very Stable' if score >= 80 else 'Stable' if score >= 60 else 'Moderate Risk' if score >= 40 else 'High Risk'
    if name == 'scale':
        return 'Growing Rapidly' if score >= 80 else 'Growing' if score >= 60 else 'Stable' if score >= 40 else 'Early Stage'
    if name == 'compliance':
        return 'Excellent' if score >= 80 else 'Good' if score >= 60 else 'Adequate' if score >= 40 else 'Limited'
    return 'Unknown'

df['financial_health_label'] = df['financial_health'].apply(lambda x: plain_english(x, 'financial_health'))
df['operational_efficiency_label'] = df['operational_efficiency'].apply(lambda x: plain_english(x, 'operational_efficiency'))
df['sustainability_label'] = df['sustainability_score'].apply(lambda x: plain_english(x, 'sustainability'))
df['scale_label'] = df['scale_trajectory'].apply(lambda x: plain_english(x, 'scale'))
df['compliance_label'] = df['compliance_score'].apply(lambda x: plain_english(x, 'compliance'))

# Cohort size
df['cohort_size'] = df.groupby(['NTEE', 'STATE', 'revenue_band'])['EIN'].transform('count')
df['cohort_warning'] = df['cohort_size'].apply(lambda x: 'Insufficient peer data (<30 peers)' if x < 30 else '')

df.to_csv("data/csv/scored_orgs.csv", index=False)
print(f"[AGENT 2] Wrote scored_orgs.csv ({len(df)} rows)")
print(f"[AGENT 2] OE coverage: {df['operational_efficiency'].notna().sum()}/{len(df)} ({df['operational_efficiency'].notna().mean()*100:.1f}%)")
import pandas as pd, numpy as np, glob

print("[AGENT 2] Loading...")
m = pd.read_csv('data/csv/master_orgs.csv', dtype=str)
m['EIN'] = m['EIN'].astype(str).str.replace('.0', '').str.strip()

f = pd.read_csv('data/csv/extracted_financials.csv', dtype=str)
f['ein'] = f['ein'].astype(str).str.replace('.0', '').str.strip()
f.rename(columns={c: c + '_ext' for c in f.columns if c != 'ein'}, inplace=True)

p = pd.read_csv(sorted(glob.glob('data/csv/percentile_engine_*.csv'), reverse=True)[0], dtype=str)
p['ein'] = p['ein'].astype(str).str.replace('.0', '').str.strip()

d = m.merge(f, left_on='EIN', right_on='ein', how='left')
d = d.merge(p[['ein', 'percentile']].rename(columns={'ein': 'EIN'}), on='EIN', how='left')

d['percentile'] = pd.to_numeric(d['percentile'], errors='coerce').fillna(50)
for c in ['total_expenses_ext', 'program_expenses_ext', 'net_assets_ext']:
    d[c] = pd.to_numeric(d[c], errors='coerce')

d['program_ratio'] = (d['program_expenses_ext'] / d['total_expenses_ext']).clip(0, 1)
d['peer_median_program_ratio'] = d.groupby(['NTEE', 'STATE'])['program_ratio'].transform('median').fillna(0.75)
d['operational_efficiency'] = ((d['program_ratio'] - d['peer_median_program_ratio']) / d['peer_median_program_ratio'].replace(0, 0.75) * 50 + 50).clip(0, 100).round(1).fillna(50)
d['financial_health'] = d['percentile'].clip(0, 100).round(1)
d['sustainability_score'] = ((d['net_assets_ext'] / (d['total_expenses_ext'] / 12).replace(0, np.nan)) / 24 * 100).clip(0, 100).round(1).fillna(50)

fc = d.groupby('EIN').size().reset_index(name='filing_count')
d = d.merge(fc, on='EIN', how='left')
d['compliance_score'] = d['filing_count'].map({1: 20, 2: 40, 3: 60, 4: 80}).fillna(100)

d['MERIT_score'] = (d['financial_health'] * 0.35 + d['operational_efficiency'] * 0.30 + d['sustainability_score'] * 0.20 + d['compliance_score'] * 0.15).clip(0, 100).round(1)

print(f"[AGENT 2] Impact: {d['MERIT_score'].min():.1f}-{d['MERIT_score'].max():.1f} mean={d['MERIT_score'].mean():.1f}")
d.to_csv('data/csv/scored_orgs.csv', index=False)
print(f"[AGENT 2] Wrote {len(d)} rows to scored_orgs.csv")
print(f"[AGENT 2] OE coverage: {d['operational_efficiency'].notna().sum()}/{len(d)} ({d['operational_efficiency'].notna().mean()*100:.1f}%)")
