#!/usr/bin/env python3
"""
Fast batch NCCS ingestion using LEFT JOIN instead of loop-based UPDATEs.
Imports governance + balance sheet + expenses in single transaction.
"""
import sqlite3
import pandas as pd
import logging
from pathlib import Path

DB_PATH = Path('/home/akbar/meritgiving/data/merit_registry.db')
NCCS_DIR = Path('/home/akbar/meritgiving/data/nccs')
LOG_DIR = Path('/home/akbar/meritgiving/logs')

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'nccs_batch_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

GOVERNANCE_MAP = {
    'F9_06_GVRN_NUM_VOTING_MEMB': 'board_size',
    'F9_06_GVRN_NUM_VOTING_MEMB_IND': 'board_independent_count',
    'F9_06_POLICY_COI_X': 'has_coi_policy',
    'F9_06_POLICY_WHSTLBLWR_X': 'has_whistleblower_policy',
    'F9_06_POLICY_DOC_RETENTION_X': 'has_doc_retention_policy',
}

BALANCE_MAP = {
    'F9_10_ASSET_TOT_EOY': 'total_assets',
    'F9_10_LIAB_TOT_EOY': 'total_liabilities',
    'F9_10_NAFB_TOT_EOY': 'net_assets',
}

EXPENSE_MAP = {
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
        df = pd.read_csv(csv_files[0], usecols=['ORG_EIN'] + list(GOVERNANCE_MAP.keys() if 'GVRN' in part_prefix else (BALANCE_MAP.keys() if 'BALANCE' in part_prefix else EXPENSE_MAP.keys())))
        logger.info(f"Loaded {len(df):,} rows from {csv_files[0].name}")
        return df
    except Exception as e:
        logger.error(f"Error loading {csv_files[0].name}: {e}")
        return None

def ingest_batch_via_temp_tables():
    """
    Ingest NCCS data using temporary tables + JOIN instead of loop.
    Much faster for large datasets.
    """
    logger.info("Starting fast batch ingestion via temp tables...")

    # Load data
    logger.info("Loading NCCS data (2023)...")
    gov_df = load_nccs_data('F9-P06-T00-GOVERNANCE')
    bal_df = load_nccs_data('F9-P10-T00-BALANCE-SHEET')
    exp_df = load_nccs_data('F9-P09-T00-EXPENSES')

    if not any([gov_df is not None, bal_df is not None, exp_df is not None]):
        logger.error("No NCCS data loaded!")
        return

    # Connect to DB
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Create temp table for governance
        if gov_df is not None:
            logger.info(f"Creating temp governance table ({len(gov_df):,} rows)...")
            gov_df_clean = gov_df[gov_df['ORG_EIN'].notna()].copy()
            gov_df_clean.columns = ['ORG_EIN'] + list(GOVERNANCE_MAP.values())
            gov_df_clean = gov_df_clean.drop_duplicates(subset=['ORG_EIN'])

            cursor.execute("DROP TABLE IF EXISTS temp_nccs_governance")
            gov_df_clean.to_sql('temp_nccs_governance', conn, if_exists='replace', index=False)
            logger.info(f"✓ Temp governance table created ({len(gov_df_clean):,} rows)")

            # Update via JOIN
            update_sql = """
            UPDATE registry_enriched
            SET
                board_size = COALESCE(temp.board_size, registry_enriched.board_size),
                board_independent_count = COALESCE(temp.board_independent_count, registry_enriched.board_independent_count),
                has_coi_policy = COALESCE(temp.has_coi_policy, registry_enriched.has_coi_policy),
                has_whistleblower_policy = COALESCE(temp.has_whistleblower_policy, registry_enriched.has_whistleblower_policy),
                has_doc_retention_policy = COALESCE(temp.has_doc_retention_policy, registry_enriched.has_doc_retention_policy)
            FROM temp_nccs_governance temp
            WHERE registry_enriched.ein = temp.ORG_EIN;
            """
            cursor.execute(update_sql)
            rows_updated = cursor.rowcount
            logger.info(f"✓ Updated {rows_updated:,} orgs with governance data")

        # Create temp table for balance sheet
        if bal_df is not None:
            logger.info(f"Creating temp balance sheet table ({len(bal_df):,} rows)...")
            bal_df_clean = bal_df[bal_df['ORG_EIN'].notna()].copy()
            bal_df_clean.columns = ['ORG_EIN'] + list(BALANCE_MAP.values())
            bal_df_clean = bal_df_clean.drop_duplicates(subset=['ORG_EIN'])

            cursor.execute("DROP TABLE IF EXISTS temp_nccs_balance")
            bal_df_clean.to_sql('temp_nccs_balance', conn, if_exists='replace', index=False)
            logger.info(f"✓ Temp balance sheet table created ({len(bal_df_clean):,} rows)")

            update_sql = """
            UPDATE registry_enriched
            SET
                total_assets = COALESCE(temp.total_assets, registry_enriched.total_assets),
                total_liabilities = COALESCE(temp.total_liabilities, registry_enriched.total_liabilities),
                nccs_net_assets = COALESCE(temp.net_assets, registry_enriched.nccs_net_assets)
            FROM temp_nccs_balance temp
            WHERE registry_enriched.ein = temp.ORG_EIN;
            """
            cursor.execute(update_sql)
            rows_updated = cursor.rowcount
            logger.info(f"✓ Updated {rows_updated:,} orgs with balance sheet data")

        # Create temp table for expenses
        if exp_df is not None:
            logger.info(f"Creating temp expenses table ({len(exp_df):,} rows)...")
            exp_df_clean = exp_df[exp_df['ORG_EIN'].notna()].copy()
            exp_df_clean.columns = ['ORG_EIN'] + list(EXPENSE_MAP.values())
            exp_df_clean = exp_df_clean.drop_duplicates(subset=['ORG_EIN'])

            # Compute ratios
            exp_df_clean['program_expense_ratio'] = (
                exp_df_clean['program_expenses'] /
                exp_df_clean['total_functional_expenses'].where(exp_df_clean['total_functional_expenses'] > 0, 1)
            ).round(4)
            exp_df_clean['overhead_ratio'] = (
                (exp_df_clean['management_expenses'] + exp_df_clean['fundraising_expenses']) /
                exp_df_clean['total_functional_expenses'].where(exp_df_clean['total_functional_expenses'] > 0, 1)
            ).round(4)

            cursor.execute("DROP TABLE IF EXISTS temp_nccs_expenses")
            exp_df_clean.to_sql('temp_nccs_expenses', conn, if_exists='replace', index=False)
            logger.info(f"✓ Temp expenses table created ({len(exp_df_clean):,} rows)")

            update_sql = """
            UPDATE registry_enriched
            SET
                program_expenses = COALESCE(temp.program_expenses, registry_enriched.program_expenses),
                management_expenses = COALESCE(temp.management_expenses, registry_enriched.management_expenses),
                fundraising_expenses = COALESCE(temp.fundraising_expenses, registry_enriched.fundraising_expenses),
                nccs_program_ratio = COALESCE(temp.program_expense_ratio, registry_enriched.nccs_program_ratio),
                nccs_overhead_ratio = COALESCE(temp.overhead_ratio, registry_enriched.nccs_overhead_ratio)
            FROM temp_nccs_expenses temp
            WHERE registry_enriched.ein = temp.ORG_EIN;
            """
            cursor.execute(update_sql)
            rows_updated = cursor.rowcount
            logger.info(f"✓ Updated {rows_updated:,} orgs with expense data")

        conn.commit()
        logger.info("✓ All updates committed successfully")

        # Cleanup
        cursor.execute("DROP TABLE IF EXISTS temp_nccs_governance")
        cursor.execute("DROP TABLE IF EXISTS temp_nccs_balance")
        cursor.execute("DROP TABLE IF EXISTS temp_nccs_expenses")

        logger.info("NCCS batch ingestion complete!")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during ingestion: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    ingest_batch_via_temp_tables()
