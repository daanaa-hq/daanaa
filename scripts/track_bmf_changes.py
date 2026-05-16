#!/usr/bin/env python3
"""
MeritGiving BMF Change Tracker v1.0
Analyzes multiple monthly BMF snapshots to track org lifecycle,
revenue trajectory, and compliance history.

This is a UNIQUE advantage of having monthly data vs a single snapshot.

Run on ecomargins:
    cd ~/meritgiving
    python3 scripts/track_bmf_changes.py
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import re
import sys

HOME = Path.home()
DATA_DIR = HOME / "meritgiving" / "NCCS Monthly DAtA"
DB_PATH = HOME / "meritgiving" / "data" / "meritgiving.db"

print("=" * 60)
print("MeritGiving BMF Change Tracker")
print("=" * 60)

if not DATA_DIR.exists():
    print(f"ERROR: {DATA_DIR} not found")
    sys.exit(1)

# ============================================================================
# STEP 1: DISCOVER & SORT MONTHLY FILES
# ============================================================================
print("\n[STEP 1] Discovering monthly snapshots...")

processed_files = sorted([f for f in DATA_DIR.glob("bmf_*_processed.csv") if re.match(r"bmf_\d{4}_\d{2}_processed\.csv", f.name)])
print(f"  Found {len(processed_files)} monthly snapshots")

# Extract dates from filenames: bmf_YYYY_MM_processed.csv
file_dates = []
for f in processed_files:
    m = re.match(r"bmf_(\d{4})_(\d{2})_processed\.csv", f.name)
    if m:
        file_dates.append((f, f"{m.group(1)}-{m.group(2)}"))

for f, d in file_dates:
    print(f"    {d}: {f.name}")

if len(file_dates) < 2:
    print("  Need at least 2 monthly files to track changes. Skipping.")
    sys.exit(0)

# ============================================================================
# STEP 2: LOAD KEY COLUMNS FROM EACH MONTH
# ============================================================================
print("\n[STEP 2] Loading key columns from each month...")

key_cols = ['EIN', 'NAME', 'STATE', 'NTEE1', 'SUBSECCD', 'STATUS', 'RULING', 'REVENUE_AMT', 'ASSET_AMT', 'INCOME_AMT', 'FOUNDATION']

monthly_data = {}
for f, date_str in file_dates:
    print(f"  Loading {date_str}...", end=" ")
    try:
        # Only load columns that exist
        df = pd.read_csv(f, usecols=lambda c: c in key_cols, low_memory=False)
        df['snapshot_date'] = date_str
        monthly_data[date_str] = df
        print(f"{len(df):,} rows")
    except Exception as e:
        print(f"ERROR: {e}")

# ============================================================================
# STEP 3: BUILD CHANGE DETECTION TABLES
# ============================================================================
print("\n[STEP 3] Detecting changes across snapshots...")

dates = sorted(monthly_data.keys())
first_date, last_date = dates[0], dates[-1]
first_df = monthly_data[first_date]
last_df = monthly_data[last_date]

# --- 3A: ORGS THAT ENTERED THE REGISTRY (new EINs) ---
first_eins = set(first_df['EIN'].astype(str))
last_eins = set(last_df['EIN'].astype(str))
new_eins = last_eins - first_eins
print(f"  New orgs since {first_date}: {len(new_eins):,}")

# --- 3B: ORGS THAT LEFT THE REGISTRY (dropped EINs) ---
dropped_eins = first_eins - last_eins
print(f"  Dropped orgs since {first_date}: {len(dropped_eins):,}")

# --- 3C: REVENUE TRAJECTORY (orgs crossing thresholds) ---
print(f"  Analyzing revenue trajectory...")

# Merge first and last on EIN
first_sub = first_df[['EIN', 'REVENUE_AMT', 'NTEE1', 'STATUS']].copy()
first_sub.columns = ['EIN', 'rev_first', 'ntee_first', 'status_first']
last_sub = last_df[['EIN', 'REVENUE_AMT', 'NTEE1', 'STATUS']].copy()
last_sub.columns = ['EIN', 'rev_last', 'ntee_last', 'status_last']

trajectory = pd.merge(first_sub, last_sub, on='EIN', how='inner')
trajectory['rev_first'] = pd.to_numeric(trajectory['rev_first'], errors='coerce')
trajectory['rev_last'] = pd.to_numeric(trajectory['rev_last'], errors='coerce')

# Filter to MeritGiving band
MIN_REV, MAX_REV = 50000, 100000000
traj_filtered = trajectory[
    (trajectory['rev_first'].notna()) & 
    (trajectory['rev_last'].notna())
].copy()

# Revenue growth rate
traj_filtered['rev_growth_pct'] = (traj_filtered['rev_last'] - traj_filtered['rev_first']) / traj_filtered['rev_first'] * 100

# Crossed INTO band (was below $50K, now inside)
crossed_in = traj_filtered[
    (traj_filtered['rev_first'] < MIN_REV) & 
    (traj_filtered['rev_last'] >= MIN_REV) & 
    (traj_filtered['rev_last'] <= MAX_REV)
]
print(f"    Orgs that crossed INTO $50K-$100M band: {len(crossed_in):,}")

# Crossed OUT of band (was inside, now above $100M or below $50K)
crossed_out = traj_filtered[
    (traj_filtered['rev_first'] >= MIN_REV) & 
    (traj_filtered['rev_first'] <= MAX_REV) & 
    ((traj_filtered['rev_last'] < MIN_REV) | (traj_filtered['rev_last'] > MAX_REV))
]
print(f"    Orgs that crossed OUT of $50K-$100M band: {len(crossed_out):,}")

# Fast growers inside band (2x+ revenue growth)
fast_growers = traj_filtered[
    (traj_filtered['rev_first'] >= MIN_REV) & 
    (traj_filtered['rev_first'] <= MAX_REV) &
    (traj_filtered['rev_last'] >= MIN_REV) & 
    (traj_filtered['rev_last'] <= MAX_REV) &
    (traj_filtered['rev_growth_pct'] >= 100)
]
print(f"    Fast growers (2x+ revenue) inside band: {len(fast_growers):,}")

# --- 3D: STATUS CHANGES ---
status_changes = traj_filtered[traj_filtered['status_first'] != traj_filtered['status_last']]
print(f"  Orgs with status changes: {len(status_changes):,}")

# --- 3E: NTEE CHANGES (mission pivots) ---
ntee_changes = traj_filtered[traj_filtered['ntee_first'] != traj_filtered['ntee_last']]
print(f"  Orgs with NTEE/mission changes: {len(ntee_changes):,}")

# ============================================================================
# STEP 4: SAVE TO DATABASE
# ============================================================================
print("\n[STEP 4] Saving change tracking tables to database...")

conn = sqlite3.connect(str(DB_PATH))

# Table: org_lifecycle
crossed_in[['EIN', 'rev_first', 'rev_last', 'rev_growth_pct']].to_sql(
    'orgs_crossed_in_band', conn, if_exists='replace', index=False
)
crossed_out[['EIN', 'rev_first', 'rev_last']].to_sql(
    'orgs_crossed_out_band', conn, if_exists='replace', index=False
)
fast_growers[['EIN', 'rev_first', 'rev_last', 'rev_growth_pct']].to_sql(
    'fast_growers', conn, if_exists='replace', index=False
)
status_changes[['EIN', 'status_first', 'status_last']].to_sql(
    'status_changes', conn, if_exists='replace', index=False
)
ntee_changes[['EIN', 'ntee_first', 'ntee_last']].to_sql(
    'ntee_changes', conn, if_exists='replace', index=False
)

# Summary table
summary_data = [
    ('snapshot_first', first_date),
    ('snapshot_last', last_date),
    ('months_covered', str(len(dates))),
    ('new_orgs', str(len(new_eins))),
    ('dropped_orgs', str(len(dropped_eins))),
    ('crossed_into_band', str(len(crossed_in))),
    ('crossed_out_of_band', str(len(crossed_out))),
    ('fast_growers', str(len(fast_growers))),
    ('status_changes', str(len(status_changes))),
    ('ntee_changes', str(len(ntee_changes))),
    ('tracked_at', datetime.now().isoformat()),
]

conn.execute("CREATE TABLE IF NOT EXISTS change_summary (metric TEXT PRIMARY KEY, value TEXT)")
conn.executemany("INSERT OR REPLACE INTO change_summary (metric, value) VALUES (?, ?)", summary_data)
conn.commit()
conn.close()

print("  Tables created:")
print("    - orgs_crossed_in_band")
print("    - orgs_crossed_out_band")
print("    - fast_growers")
print("    - status_changes")
print("    - ntee_changes")
print("    - change_summary")

# ============================================================================
# STEP 5: PRINT INSIGHTS
# ============================================================================
print("\n" + "=" * 60)
print("CHANGE TRACKING COMPLETE")
print("=" * 60)
print(f"Period analyzed:     {first_date} → {last_date}")
print(f"Snapshots compared:    {len(dates)}")
print(f"New orgs:            {len(new_eins):,}")
print(f"Dropped orgs:          {len(dropped_eins):,}")
print(f"Crossed INTO band:     {len(crossed_in):,}")
print(f"Crossed OUT of band:   {len(crossed_out):,}")
print(f"Fast growers (2x+):    {len(fast_growers):,}")
print(f"Status changes:        {len(status_changes):,}")
print(f"Mission pivots:        {len(ntee_changes):,}")
print("=" * 60)
print("\nThese tables enable MERIT scoring dimensions:")
print("  - Growth trajectory (fast_growers)")
print("  - Stability (status_changes count per org)")
print("  - Mission consistency (ntee_changes count)")
print("  - Entry/exit dynamics (crossed_in / crossed_out)")
