#!/usr/bin/env python3
"""
Ingest NCCS Form 990 data into org profiles.
Adds: board size, governance policies, asset/liability data, expense ratios.
Uses latest year (2023) with fallback to prior years if data missing.
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

DB_PATH = Path('/home/akbar/meritgiving/data/merit_registry.db')
NCCS_DIR = Path('/home/akbar/meritgiving/data/nccs')
LOG_DIR = Path('/home/akbar/meritgiving/logs')

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'nccs_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Profile fields to extract and add to registry_enriched
GOVERNANCE_FIELDS = {
    'F9_06_GVRN_NUM_VOTING_MEMB': 'board_size',
    'F9_06_GVRN_NUM_VOTING_MEMB_IND': 'board_independent_count',
    'F9_06_POLICY_COI_X': 'has_coi_policy',
    'F9_06_POLICY_WHSTLBLWR_X': 'has_whistleblower_policy',
    'F9_06_POLICY_DOC_RETENTION_X': 'has_doc_retention_policy',
}

BALANCE_SHEET_FIELDS = {
    'F9_10_ASSET_TOT_EOY': 'total_assets',
    'F9_10_LIAB_TOT_EOY': 'total_liabilities',
    'F9_10_NAFB_TOT_EOY': 'net_assets',
}

EXPENSE_FIELDS = {
    'F9_09_EXP_TOT_PROG': 'program_expenses',
    'F9_09_EXP_TOT_MGMT': 'management_expenses',
    'F9_09_EXP_TOT_FUNDR': 'fundraising_expenses',
    'F9_09_EXP_TOT_TOT': 'total_functional_expenses',
}

def load_nccs_data(part_prefix, year=2023):
    """Load NCCS data for a given part and year."""
    csv_files = list(NCCS_DIR.glob(f'{part_prefix}*{year}.CSV'))
    if not csv_files:
        logger.warning(f"No {part_prefix} files found for {year}")
        return None

    try:
        df = pd.read_csv(csv_files[0])
        logger.info(f"Loaded {len(df):,} orgs from {csv_files[0].name}")
        return df
    except Exception as e:
        logger.error(f"Error loading {csv_files[0].name}: {e}")
        return None

def extract_profile_fields(df, field_map):
    """Extract specified fields from dataframe, rename to profile names."""
    extracted = pd.DataFrame()
    extracted['ORG_EIN'] = df.get('ORG_EIN', df.get('EIN2'))

    for nccs_col, profile_col in field_map.items():
        if nccs_col in df.columns:
            extracted[profile_col] = pd.to_numeric(df[nccs_col], errors='coerce')

    return extracted.dropna(subset=['ORG_EIN'])

def compute_expense_ratios(expenses_df):
    """Compute program expense ratio and efficiency metrics."""
    if expenses_df.empty:
        return expenses_df

    expenses_df['program_expense_ratio'] = (
        expenses_df.get('program_expenses', 0) /
        expenses_df.get('total_functional_expenses', 1)
    ).round(4)

    expenses_df['overhead_ratio'] = (
        (expenses_df.get('management_expenses', 0) +
         expenses_df.get('fundraising_expenses', 0)) /
        expenses_df.get('total_functional_expenses', 1)
    ).round(4)

    return expenses_df

def ingest_to_db(governance_df, balance_df, expenses_df):
    """Merge NCCS data into registry_enriched."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    updated = 0
    skipped = 0

    # Get all EINs from governance data (widest coverage)
    eins = governance_df['ORG_EIN'].unique() if governance_df is not None else []

    if len(eins) == 0:
        logger.warning("No EINs to process")
        return

    logger.info(f"Processing {len(eins):,} orgs from NCCS data...")

    for ein in eins:
        try:
            updates = {}

            # Governance data
            if governance_df is not None:
                gov_row = governance_df[governance_df['ORG_EIN'] == ein]
                if not gov_row.empty:
                    for col in ['board_size', 'board_independent_count', 'has_coi_policy',
                               'has_whistleblower_policy', 'has_doc_retention_policy']:
                        if col in gov_row.columns:
                            val = gov_row[col].values[0]
                            if pd.notna(val):
                                updates[col] = int(val) if col != 'board_size' else int(val)

            # Balance sheet data
            if balance_df is not None:
                bal_row = balance_df[balance_df['ORG_EIN'] == ein]
                if not bal_row.empty:
                    for col in ['total_assets', 'total_liabilities', 'net_assets']:
                        if col in bal_row.columns:
                            val = bal_row[col].values[0]
                            if pd.notna(val):
                                updates[col] = int(val)

            # Expense data + ratios
            if expenses_df is not None:
                exp_row = expenses_df[expenses_df['ORG_EIN'] == ein]
                if not exp_row.empty:
                    for col in ['program_expenses', 'management_expenses', 'fundraising_expenses',
                               'program_expense_ratio', 'overhead_ratio']:
                        if col in exp_row.columns:
                            val = exp_row[col].values[0]
                            if pd.notna(val):
                                updates[col] = float(val) if '_ratio' in col else int(val)

            if updates:
                # Build dynamic UPDATE query
                set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                query = f"UPDATE registry_enriched SET {set_clause} WHERE ein = ?"
                cursor.execute(query, list(updates.values()) + [ein])
                updated += 1
            else:
                skipped += 1

        except Exception as e:
            logger.error(f"Error updating {ein}: {e}")
            skipped += 1

    conn.commit()
    conn.close()

    logger.info(f"\nIngestion Complete:")
    logger.info(f"  Updated: {updated:,} orgs")
    logger.info(f"  Skipped: {skipped:,}")

def main():
    logger.info("NCCS Data Ingestion — Starting")
    logger.info("Loading latest year (2023) with profile fields...")

    # Load all three key parts
    governance_df = load_nccs_data('F9-P06-T00-GOVERNANCE')
    balance_df = load_nccs_data('F9-P10-T00-BALANCE-SHEET')
    expenses_df = load_nccs_data('F9-P09-T00-EXPENSES')

    # Extract and transform
    if governance_df is not None:
        governance_df = extract_profile_fields(governance_df, GOVERNANCE_FIELDS)

    if balance_df is not None:
        balance_df = extract_profile_fields(balance_df, BALANCE_SHEET_FIELDS)

    if expenses_df is not None:
        expenses_df = extract_profile_fields(expenses_df, EXPENSE_FIELDS)
        expenses_df = compute_expense_ratios(expenses_df)

    # Ingest to database
    if governance_df is not None or balance_df is not None or expenses_df is not None:
        ingest_to_db(governance_df, balance_df, expenses_df)
    else:
        logger.error("No NCCS data loaded!")

if __name__ == '__main__':
    main()
