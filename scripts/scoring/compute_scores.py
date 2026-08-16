#!/usr/bin/env python3
"""
MeritGiving Scoring Engine v1.0
Computes all scoring dimensions from available data.

Run after registry + financials are loaded:
    python3 scripts/compute_scores.py
"""

import pandas as pd
import sqlite3
from pathlib import Path
import numpy as np

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"

print("=" * 60)
print("MeritGiving Scoring Engine")
print("=" * 60)

conn = sqlite3.connect(str(DB_PATH))

# ============================================================================
# STEP 1: BUILD UNIFIED FINANCIAL VIEW
# ============================================================================
print("\n[STEP 1] Building unified financial view...")

# Check what financial tables exist
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'financials_%'")
fin_tables = [t[0] for t in c.fetchall()]
print(f"  Financial tables: {fin_tables}")

if not fin_tables:
    print("  ⚠️  No CorePCF financial tables found!")
    print("  Will score using BMF top-line data only (limited accuracy)")

    # Use registry as base
    df = pd.read_sql("SELECT * FROM registry_enriched", conn)
    df['total_revenue'] = pd.to_numeric(df['REVENUE_AMT'], errors='coerce')
    df['total_expenses'] = pd.to_numeric(df['REVENUE_AMT'], errors='coerce')  # proxy
    df['program_service_expenses'] = df['total_revenue'] * 0.75  # rough estimate
    df['fundraising_expenses'] = df['total_revenue'] * 0.05

else:
    # Union all financial tables
    parts = []
    for table in fin_tables:
        part = pd.read_sql(f"SELECT * FROM {table}", conn)
        parts.append(part)

    df = pd.concat(parts, ignore_index=True)
    print(f"  Combined financial records: {len(df):,}")

# ============================================================================
# STEP 2: COMPUTE DERIVED METRICS
# ============================================================================
print("\n[STEP 2] Computing derived metrics...")

# Ensure numeric
df['total_revenue'] = pd.to_numeric(df.get('total_revenue', 0), errors='coerce').fillna(0)
df['total_expenses'] = pd.to_numeric(df.get('total_expenses', 0), errors='coerce').fillna(0)
df['program_service_expenses'] = pd.to_numeric(df.get('program_service_expenses', 0), errors='coerce').fillna(0)
df['fundraising_expenses'] = pd.to_numeric(df.get('fundraising_expenses', 0), errors='coerce').fillna(0)
df['fundraising_fees'] = pd.to_numeric(df.get('fundraising_fees', 0), errors='coerce').fillna(0)
df['total_assets_eoy'] = pd.to_numeric(df.get('total_assets_eoy', 0), errors='coerce').fillna(0)
df['total_assets_boy'] = pd.to_numeric(df.get('total_assets_boy', 0), errors='coerce').fillna(0)
df['net_assets_eoy'] = pd.to_numeric(df.get('net_assets_eoy', 0), errors='coerce').fillna(0)
df['grants_paid'] = pd.to_numeric(df.get('grants_paid', 0), errors='coerce').fillna(0)
df['contributions'] = pd.to_numeric(df.get('contributions', 0), errors='coerce').fillna(0)

# Core ratios
df['program_expense_ratio'] = np.where(
    df['total_expenses'] > 0,
    df['program_service_expenses'] / df['total_expenses'],
    np.nan
)

df['admin_overhead_ratio'] = np.where(
    df['total_expenses'] > 0,
    1 - df['program_expense_ratio'],
    np.nan
)

df['fundraising_efficiency'] = np.where(
    (df['fundraising_expenses'] + df['fundraising_fees']) > 0,
    df['total_revenue'] / (df['fundraising_expenses'] + df['fundraising_fees']),
    np.nan
)

df['asset_growth_rate'] = np.where(
    df['total_assets_boy'] > 0,
    (df['total_assets_eoy'] - df['total_assets_boy']) / df['total_assets_boy'],
    np.nan
)

df['liquidity_proxy'] = np.where(
    df['total_expenses'] > 0,
    df['net_assets_eoy'] / (df['total_expenses'] / 12),
    np.nan
)

# Grantmaking ratio (for grantmaking orgs)
df['grantmaking_ratio'] = np.where(
    df['total_expenses'] > 0,
    df['grants_paid'] / df['total_expenses'],
    np.nan
)

# Revenue concentration (contributions vs diversified)
df['contribution_dependency'] = np.where(
    df['total_revenue'] > 0,
    df['contributions'] / df['total_revenue'],
    np.nan
)

print(f"  Computed metrics for {len(df):,} records")

# ============================================================================
# STEP 3: PERCENTILE RANKINGS
# ============================================================================
print("\n[STEP 3] Computing percentile rankings...")

# National percentiles by NTEE major group
if 'NTEE1' in df.columns:
    df['ntee_major'] = df['NTEE1'].astype(str).str[:1]

    df['pctile_program_efficiency'] = df.groupby('ntee_major')['program_expense_ratio'].rank(pct=True)
    df['pctile_fundraising_efficiency'] = df.groupby('ntee_major')['fundraising_efficiency'].rank(pct=True)
    df['pctile_asset_growth'] = df.groupby('ntee_major')['asset_growth_rate'].rank(pct=True)
    df['pctile_size'] = df.groupby('ntee_major')['total_revenue'].rank(pct=True)

    print("  Percentiles by NTEE major group computed")

# State percentiles
if 'STATE' in df.columns:
    df['pctile_state_size'] = df.groupby('STATE')['total_revenue'].rank(pct=True)
    print("  State percentiles computed")

# ============================================================================
# STEP 4: COMPOSITE SCORES
# ============================================================================
print("\n[STEP 4] Computing composite scores...")

# Normalize each dimension 0-100
def normalize_score(series, higher_is_better=True):
    """Convert to 0-100 scale."""
    s = series.copy()
    if not higher_is_better:
        s = 1 - s
    # Winsorize at 1st and 99th percentile
    q01, q99 = s.quantile(0.01), s.quantile(0.99)
    s = s.clip(q01, q99)
    # Scale to 0-100
    min_val, max_val = s.min(), s.max()
    if max_val > min_val:
        return ((s - min_val) / (max_val - min_val)) * 100
    return s * 0 + 50

df['score_program_efficiency'] = normalize_score(df['program_expense_ratio'], higher_is_better=True)
df['score_fundraising_efficiency'] = normalize_score(df['fundraising_efficiency'], higher_is_better=True)
df['score_financial_health'] = normalize_score(df['asset_growth_rate'], higher_is_better=True)
df['score_size_stability'] = normalize_score(df['liquidity_proxy'], higher_is_better=True)

# Weighted composite (adjust weights as needed)
WEIGHTS = {
    'program_efficiency': 0.35,
    'fundraising_efficiency': 0.20,
    'financial_health': 0.25,
    'size_stability': 0.20,
}

df['merit_score'] = (
    df['score_program_efficiency'] * WEIGHTS['program_efficiency'] +
    df['score_fundraising_efficiency'] * WEIGHTS['fundraising_efficiency'] +
    df['score_financial_health'] * WEIGHTS['financial_health'] +
    df['score_size_stability'] * WEIGHTS['size_stability']
)

# Round
df['merit_score'] = df['merit_score'].round(1)

print(f"  Merit score range: {df['merit_score'].min():.1f} - {df['merit_score'].max():.1f}")
print(f"  Median score: {df['merit_score'].median():.1f}")

# ============================================================================
# STEP 5: SAVE TO DATABASE
# ============================================================================
print("\n[STEP 5] Saving scores to database...")

score_cols = ['EIN', 'FISYR', 'program_expense_ratio', 'admin_overhead_ratio',
              'fundraising_efficiency', 'asset_growth_rate', 'liquidity_proxy',
              'grantmaking_ratio', 'contribution_dependency',
              'pctile_program_efficiency', 'pctile_fundraising_efficiency',
              'pctile_asset_growth', 'pctile_size', 'pctile_state_size',
              'score_program_efficiency', 'score_fundraising_efficiency',
              'score_financial_health', 'score_size_stability', 'merit_score']

# Only keep columns that exist
score_cols = [c for c in score_cols if c in df.columns]
scores_df = df[score_cols].copy()

scores_df.to_sql('scores', conn, if_exists='replace', index=False)
conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_ein ON scores(EIN)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_merit ON scores(merit_score)")
conn.commit()
conn.close()

print(f"  Saved {len(scores_df):,} score records")
print("\n" + "=" * 60)
print("SCORING COMPLETE")
print("=" * 60)
print(f"Database: {DB_PATH}")
print(f"Table: scores ({len(scores_df):,} rows)")
print("\nQuery top orgs:")
print(f'  sqlite3 {DB_PATH} "SELECT EIN, merit_score FROM scores ORDER BY merit_score DESC LIMIT 10;"')
