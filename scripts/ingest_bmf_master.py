#!/usr/bin/env python3
"""
MeritGiving BMF Ingestion Engine v1.0
Scans local NCCS Monthly BMF files, builds master registry, applies filters.

Run on ecomargins:
    cd ~/meritgiving
    python3 scripts/ingest_bmf_master.py

Assumes data is in: ~/meritgiving/NCCS Monthly DAtA/
"""

import pandas as pd
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys

# ============================================================================
# PATHS
# ============================================================================
HOME = Path.home()
DATA_DIR = HOME / "meritgiving" / "NCCS Monthly DAtA"
OUT_DIR = HOME / "meritgiving" / "data"
DB_PATH = OUT_DIR / "meritgiving.db"
REPORT_PATH = OUT_DIR / "bmf_ingest_report.json"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# MERITGIVING FILTERS
# ============================================================================
MIN_REVENUE = 50000
MAX_REVENUE = 100000000
MIN_AGE_YEARS = 3
TARGET_SUBSECCD = "03"  # 501(c)(3)
TARGET_STATUS = "01"      # Active

# ============================================================================
# STEP 1: DISCOVER FILES
# ============================================================================
print("=" * 60)
print("MeritGiving BMF Ingestion Engine")
print("=" * 60)

if not DATA_DIR.exists():
    print(f"ERROR: Data directory not found: {DATA_DIR}")
    print("Please ensure your NCCS BMF files are in ~/meritgiving/NCCS Monthly DAtA/")
    sys.exit(1)

all_csvs = sorted(DATA_DIR.glob("*.csv"))
processed_files = [f for f in all_csvs if "_processed" in f.name and f.name.startswith("bmf_")]
dict_files = [f for f in all_csvs if "_data_dictionary" in f.name and f.name.startswith("bmf_")]
master_files = [f for f in all_csvs if "bmf_master" in f.name]
rev_files = [f for f in all_csvs if "bmf_rev" in f.name]

print(f"\nFound {len(processed_files)} monthly processed files")
print(f"Found {len(dict_files)} data dictionaries")
print(f"Found {len(master_files)} master files")
print(f"Found {len(rev_files)} revocation files")

# ============================================================================
# STEP 2: PARSE DATA DICTIONARY (latest)
# ============================================================================
print("\n[STEP 2] Loading data dictionary...")

if dict_files:
    # Pick the latest dictionary
    latest_dict = sorted(dict_files)[-1]
    print(f"  Using: {latest_dict.name}")
    try:
        dd = pd.read_csv(latest_dict)
        print(f"  Dictionary columns: {list(dd.columns)}")
        if 'variable_name' in dd.columns and 'description' in dd.columns:
            for _, row in dd.head(20).iterrows():
                print(f"    {row['variable_name']:25s} → {row['description'][:60]}...")
    except Exception as e:
        print(f"  Could not parse dictionary: {e}")
else:
    print("  No dictionary found — will infer columns from data")

# ============================================================================
# STEP 3: LOAD LATEST MONTHLY BMF (Registry)
# ============================================================================
print("\n[STEP 3] Loading latest monthly BMF...")

if not processed_files:
    print("ERROR: No processed BMF files found!")
    sys.exit(1)

# Sort by date embedded in filename: bmf_YYYY_MM_processed.csv
latest_bmf = sorted(processed_files)[-1]
print(f"  Loading: {latest_bmf.name}")

# Read with low_memory=False to avoid dtype warnings
bmf = pd.read_csv(latest_bmf, low_memory=False)
print(f"  Rows: {len(bmf):,}")
print(f"  Columns: {list(bmf.columns)}")

# Show sample data
print(f"\n  Sample rows:")
print(bmf.head(3).to_string())

# ============================================================================
# STEP 4: PROFILE KEY FIELDS
# ============================================================================
print("\n[STEP 4] Profiling key fields...")

key_fields = {
    'EIN': 'EIN',
    'NAME': 'Organization Name',
    'STATE': 'State',
    'NTEE1': 'NTEE Code',
    'SUBSECCD': 'Subsection (03=501c3)',
    'STATUS': 'Status (01=Active)',
    'RULING': 'Ruling Date',
    'REVENUE_AMT': 'Revenue Amount',
    'ASSET_AMT': 'Asset Amount',
    'INCOME_AMT': 'Income Amount',
    'FOUNDATION': 'Foundation Code',
    'ORGANIZATION': 'Organization Code',
}

for col, desc in key_fields.items():
    if col in bmf.columns:
        nulls = bmf[col].isna().sum()
        print(f"  {col:15s} | {desc:30s} | Nulls: {nulls:,} ({nulls/len(bmf)*100:.1f}%)")
    else:
        print(f"  {col:15s} | {desc:30s} | ⚠️  COLUMN NOT FOUND")

# ============================================================================
# STEP 5: APPLY MERITGIVING FILTERS
# ============================================================================
print("\n[STEP 5] Applying MeritGiving filters...")
print(f"  Criteria: >{MIN_AGE_YEARS} years old, ${MIN_REVENUE:,}-${MAX_REVENUE:,} revenue, 501(c)(3), Active")

# Make a working copy
registry = bmf.copy()

# Parse ruling date → age
if 'RULING' in registry.columns:
    # RULING is typically YYYYMM format
    registry['RULING_YEAR'] = pd.to_numeric(registry['RULING'].astype(str).str[:4], errors='coerce')
    registry['RULING_MONTH'] = pd.to_numeric(registry['RULING'].astype(str).str[4:6], errors='coerce')
    current_year = datetime.now().year
    registry['AGE_YEARS'] = current_year - registry['RULING_YEAR']
    print(f"  Age computed from RULING date (YYYYMM format)")
else:
    print("  ⚠️  RULING column not found — cannot filter by age!")
    registry['AGE_YEARS'] = 999  # bypass filter

# Revenue filter
if 'REVENUE_AMT' in registry.columns:
    registry['REVENUE_AMT'] = pd.to_numeric(registry['REVENUE_AMT'], errors='coerce')
else:
    print("  ⚠️  REVENUE_AMT not found — using INCOME_AMT as proxy")
    if 'INCOME_AMT' in registry.columns:
        registry['REVENUE_AMT'] = pd.to_numeric(registry['INCOME_AMT'], errors='coerce')
    else:
        registry['REVENUE_AMT'] = 0

# Apply filters
mask = (
    (registry['AGE_YEARS'] >= MIN_AGE_YEARS) &
    (registry['REVENUE_AMT'] >= MIN_REVENUE) &
    (registry['REVENUE_AMT'] <= MAX_REVENUE) &
    (registry['SUBSECCD'].astype(str) == TARGET_SUBSECCD) &
    (registry['STATUS'].astype(str) == TARGET_STATUS)
)

# Also filter out private foundations (FOUNDATION code 15 = private operating, 16 = private non-operating)
if 'FOUNDATION' in registry.columns:
    # Foundation codes: 00=public charity, 15=private operating, 16=private non-op
    # Keep only public charities (00, 02, 03, 04) — drop 15, 16
    foundation_mask = ~registry['FOUNDATION'].astype(str).isin(['15', '16'])
    mask = mask & foundation_mask
    print(f"  Excluding private foundations (codes 15, 16)")

filtered = registry[mask].copy()

print(f"\n  BEFORE filters: {len(registry):,} orgs")
print(f"  AFTER filters:  {len(filtered):,} orgs")
print(f"  Retention rate: {len(filtered)/len(registry)*100:.1f}%")

# ============================================================================
# STEP 6: REVOCATION CHECK
# ============================================================================
print("\n[STEP 6] Cross-checking revoked organizations...")

revoked_eins = set()
for rev_file in rev_files:
    try:
        rev_df = pd.read_csv(rev_file, low_memory=False)
        if 'EIN' in rev_df.columns:
            revoked_eins.update(rev_df['EIN'].astype(str).tolist())
            print(f"  Loaded {len(rev_df):,} revoked records from {rev_file.name}")
    except Exception as e:
        print(f"  ⚠️  Could not load {rev_file.name}: {e}")

if revoked_eins:
    before_drop = len(filtered)
    filtered = filtered[~filtered['EIN'].astype(str).isin(revoked_eins)].copy()
    dropped = before_drop - len(filtered)
    print(f"  Dropped {dropped:,} revoked orgs")
    print(f"  Final registry: {len(filtered):,} orgs")

# ============================================================================
# STEP 7: BUILD SQLITE DATABASE
# ============================================================================
print("\n[STEP 7] Building SQLite database...")

conn = sqlite3.connect(str(DB_PATH))

# Main registry table
filtered.to_sql('registry', conn, if_exists='replace', index=False)

# Create indexes
conn.executescript("""
CREATE INDEX IF NOT EXISTS idx_reg_ein ON registry(EIN);
CREATE INDEX IF NOT EXISTS idx_reg_state ON registry(STATE);
CREATE INDEX IF NOT EXISTS idx_reg_ntee ON registry(NTEE1);
CREATE INDEX IF NOT EXISTS idx_reg_revenue ON registry(REVENUE_AMT);
CREATE INDEX IF NOT EXISTS idx_reg_city ON registry(CITY);
CREATE INDEX IF NOT EXISTS idx_reg_name ON registry(NAME);
""")

# Summary stats table
conn.execute("""
CREATE TABLE IF NOT EXISTS summary_stats (
    metric TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

stats = [
    ('total_orgs_in_bmf', str(len(registry))),
    ('filtered_orgs', str(len(filtered))),
    ('filter_retention_pct', f"{len(filtered)/len(registry)*100:.2f}"),
    ('min_revenue_threshold', str(MIN_REVENUE)),
    ('max_revenue_threshold', str(MAX_REVENUE)),
    ('min_age_years', str(MIN_AGE_YEARS)),
    ('target_subseccd', TARGET_SUBSECCD),
    ('latest_bmf_file', latest_bmf.name),
    ('ingested_at', datetime.now().isoformat()),
]

conn.executemany("INSERT OR REPLACE INTO summary_stats (metric, value) VALUES (?, ?)", stats)
conn.commit()
conn.close()

print(f"  Database saved: {DB_PATH}")
print(f"  Table: registry ({len(filtered):,} rows)")

# ============================================================================
# STEP 8: GENERATE REPORT
# ============================================================================
print("\n[STEP 8] Generating ingest report...")

report = {
    "ingest_date": datetime.now().isoformat(),
    "source_file": latest_bmf.name,
    "source_rows": len(registry),
    "filtered_rows": len(filtered),
    "retention_rate_pct": round(len(filtered)/len(registry)*100, 2),
    "filters_applied": {
        "min_age_years": MIN_AGE_YEARS,
        "min_revenue": MIN_REVENUE,
        "max_revenue": MAX_REVENUE,
        "subseccd": TARGET_SUBSECCD,
        "status": TARGET_STATUS,
        "exclude_foundations": ["15", "16"]
    },
    "columns_available": list(bmf.columns),
    "revenue_distribution": {
        "min": int(filtered['REVENUE_AMT'].min()) if len(filtered) > 0 else None,
        "max": int(filtered['REVENUE_AMT'].max()) if len(filtered) > 0 else None,
        "median": int(filtered['REVENUE_AMT'].median()) if len(filtered) > 0 else None,
        "mean": int(filtered['REVENUE_AMT'].mean()) if len(filtered) > 0 else None,
    },
    "top_states": filtered['STATE'].value_counts().head(10).to_dict() if 'STATE' in filtered.columns else {},
    "top_ntee": filtered['NTEE1'].value_counts().head(10).to_dict() if 'NTEE1' in filtered.columns else {},
    "age_distribution": filtered['AGE_YEARS'].describe().to_dict() if 'AGE_YEARS' in filtered.columns else {},
    "revoked_orgs_dropped": len(revoked_eins) if revoked_eins else 0,
    "next_steps": [
        "Download NCCS CorePCF 2019-2022 for detailed financials (program expenses, fundraising costs)",
        "Download 2023-2024 990 XML selectively for EINs in this registry",
        "Build scoring dimensions: program_expense_ratio, fundraising_efficiency, liquidity",
        "Add ProPublica API enrichment for filing recency and PDF links",
        "Add Charity Navigator API for external trust signals",
    ]
}

with open(REPORT_PATH, 'w') as f:
    json.dump(report, f, indent=2, default=str)

print(f"  Report saved: {REPORT_PATH}")

# ============================================================================
# STEP 9: PRINT SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print("INGEST COMPLETE")
print("=" * 60)
print(f"Registry size:      {len(filtered):,} organizations")
print(f"Revenue range:      ${filtered['REVENUE_AMT'].min():,.0f} - ${filtered['REVENUE_AMT'].max():,.0f}")
print(f"Median revenue:     ${filtered['REVENUE_AMT'].median():,.0f}")
print(f"Median age:         {filtered['AGE_YEARS'].median():.0f} years")
print(f"Top state:          {filtered['STATE'].value_counts().index[0] if 'STATE' in filtered.columns else 'N/A'}")
print(f"Top NTEE:           {filtered['NTEE1'].value_counts().index[0] if 'NTEE1' in filtered.columns else 'N/A'}")
print(f"Database:           {DB_PATH}")
print(f"Report:             {REPORT_PATH}")
print("=" * 60)
print("\nNext: Run the monthly-change tracker to see org lifecycle data")
print("      python3 scripts/track_bmf_changes.py")
