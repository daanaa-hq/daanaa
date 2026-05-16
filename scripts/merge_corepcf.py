#!/usr/bin/env python3
"""
Merge CorePCF financials into MeritGiving registry.
Run after CorePCF files are downloaded.
"""

import pandas as pd
import sqlite3
from pathlib import Path
import glob

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"
COREPCF_DIR = Path.home() / "meritgiving" / "data" / "corepcf"

print("=" * 60)
print("Merging CorePCF Financials INTO registry_enriched")
print("=" * 60)

# Find CorePCF files
csv_files = sorted(glob.glob(str(COREPCF_DIR / "corepcf_*.csv")))
print(f"Found {len(csv_files)} CorePCF files")

if not csv_files:
    print("ERROR: No CorePCF files found. Run download_corepcf.sh first.")
    exit(1)

conn = sqlite3.connect(str(DB_PATH))

for csv_file in csv_files:
    year = Path(csv_file).stem.split('_')[-1]
    print(f"\nLoading {year}...")

    df = pd.read_csv(csv_file, low_memory=False)
    print(f"  Rows: {len(df):,}, Columns: {len(df.columns)}")

    # CorePCF key financial columns (standard NCCS naming)
    # These vary slightly by year but common ones include:
    financial_cols = ['EIN', 'FISYR', 'TOTREV', 'TOTEXP', 'ASS_EOY', 'ASS_BOY',
                      'LIAB_EOY', 'NETASS_EOY', 'PROGREV', 'PROGEXP',
                      'FUNDEXP', 'FUNDFEES', 'GRANTSPAY', 'SALARIES',
                      'CONTRIB', 'INVINC', 'OTHREV']

    # Only keep columns that exist
    available_cols = [c for c in financial_cols if c in df.columns]
    df = df[available_cols].copy()

    # Rename to MeritGiving standard
    rename_map = {
        'TOTREV': 'total_revenue',
        'TOTEXP': 'total_expenses',
        'ASS_EOY': 'total_assets_eoy',
        'ASS_BOY': 'total_assets_boy',
        'LIAB_EOY': 'total_liabilities_eoy',
        'NETASS_EOY': 'net_assets_eoy',
        'PROGREV': 'program_service_revenue',
        'PROGEXP': 'program_service_expenses',
        'FUNDEXP': 'fundraising_expenses',
        'FUNDFEES': 'fundraising_fees',
        'GRANTSPAY': 'grants_paid',
        'SALARIES': 'salaries',
        'CONTRIB': 'contributions',
        'INVINC': 'investment_income',
        'OTHREV': 'other_revenue',
    }

    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    df['data_source'] = f'corepcf_{year}'

    # Save to SQLite
    table_name = f'financials_{year}'
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f"  Saved to table: {table_name}")

    # Create index
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_ein ON {table_name}(EIN)")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("CorePCF merge complete")
print("=" * 60)
print("Next: Run scoring computation")
print("  python3 $HOME/meritgiving/scripts/compute_scores.py")
