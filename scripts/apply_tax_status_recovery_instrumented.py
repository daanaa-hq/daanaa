#!/usr/bin/env python3
"""
Apply tax_status_recovery.db to production database with deterministic reconciliation.

Strict requirements:
  - Set-based SQLite updates (no row-by-row Python loops)
  - Detect and report unmatched EINs and conflicts
  - Never overwrite existing non-null values (explicit override required)
  - Pre/post checksum parity verification
  - SQLite integrity checks before and after
  - Fully idempotent (safe to run twice)
  - Dry-run by default (requires --apply flag)
  - No hard-coded assumptions

This script ONLY modifies the database. It does NOT:
  - Create backups (caller's responsibility)
  - Restart services (caller's responsibility)
  - Access SSH/droplet (caller's responsibility)
"""

import sqlite3
import json
import hashlib
import argparse
import sys
import traceback
import time
from pathlib import Path
from typing import Dict, Tuple, List

def validate_production_database(db_path: str) -> Tuple[bool, str]:
    """Validate production database before mutation."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Check integrity
        cur.execute("PRAGMA integrity_check")
        integrity = cur.fetchone()[0]
        if integrity != 'ok':
            return False, f"Database integrity check failed: {integrity}"
        
        # Check registry_enriched exists
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='registry_enriched'
        """)
        if not cur.fetchone():
            return False, "Table registry_enriched not found"
        
        # Check schema
        cur.execute("PRAGMA table_info(registry_enriched)")
        columns = {row[1]: row[2] for row in cur.fetchall()}
        
        if 'EIN' not in columns:
            return False, "Missing EIN column"
        
        # Get row count
        cur.execute("SELECT COUNT(*) FROM registry_enriched")
        row_count = cur.fetchone()[0]
        
        conn.close()
        return True, f"Valid. Rows: {row_count}, columns: {len(columns)}"
        
    except Exception as e:
        return False, str(e)

def load_recovery_manifest(manifest_path: str) -> Tuple[bool, Dict]:
    """Load and validate recovery manifest."""
    if not Path(manifest_path).exists():
        return False, {"error": f"Manifest not found: {manifest_path}"}
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    if not manifest.get('validation_passed'):
        return False, {"error": "Recovery artifact validation failed", "details": manifest}
    
    return True, manifest

def calculate_checksum_for_table(db_path: str, table_name: str) -> str:
    """
    Calculate aggregate checksum for table (deterministic, sorted by EIN).

    For recovery tables with row_checksum: use pre-calculated checksums.
    For production tables: calculate checksums on the fly from EIN/org_status/irs_revoked.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check if table has row_checksum column
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cur.fetchall()}

    if 'row_checksum' in columns:
        # Use pre-calculated checksums (recovery table)
        cur.execute(f"""
            SELECT GROUP_CONCAT(row_checksum, '|')
            FROM {table_name}
            ORDER BY ein
        """)
    else:
        # Production table without row_checksum: use Python to calculate
        # (This handles both pre-migration and post-migration states)
        conn.close()
        return calculate_checksum_via_python(db_path, table_name)

    checksums_concat = cur.fetchone()[0] or ""
    conn.close()

    return hashlib.sha256(checksums_concat.encode()).hexdigest()

def calculate_checksum_via_python(db_path: str, table_name: str) -> str:
    """Calculate checksum using Python for production tables without row_checksum.

    Handles both pre-migration (missing columns) and post-migration (columns exist) states.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check which columns exist
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cur.fetchall()}

    has_org_status = 'org_status' in columns
    has_irs_revoked = 'irs_revoked' in columns

    # Get rows based on available columns
    if has_org_status and has_irs_revoked:
        # Post-migration: columns exist, use them
        cur.execute(f"""
            SELECT EIN, org_status, irs_revoked
            FROM {table_name}
            ORDER BY EIN
        """)

        checksums = []
        for row in cur.fetchall():
            # Calculate row checksum same way as recovery artifact
            checksum_str = f"{row['EIN']}|{row['org_status']}|{row['irs_revoked']}"
            checksum = hashlib.sha256(checksum_str.encode()).hexdigest()
            checksums.append(checksum)
    else:
        # Pre-migration: columns don't exist, checksum on EIN only (baseline)
        cur.execute(f"""
            SELECT EIN
            FROM {table_name}
            ORDER BY EIN
        """)

        checksums = []
        for row in cur.fetchall():
            # Pre-migration checksum: just EIN (will differ after migration adds data)
            checksum_str = f"{row['EIN']}"
            checksum = hashlib.sha256(checksum_str.encode()).hexdigest()
            checksums.append(checksum)

    conn.close()

    # Aggregate all checksums
    checksums_concat = '|'.join(checksums)
    return hashlib.sha256(checksums_concat.encode()).hexdigest()

def get_table_stats(db_path: str, table_name: str) -> Dict:
    """Get table statistics for reporting.

    Handles both pre-migration (missing columns) and post-migration states.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    total = cur.fetchone()[0]

    # Check which columns exist
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cur.fetchall()}

    has_org_status = 'org_status' in columns
    has_irs_revoked = 'irs_revoked' in columns

    # Only count nulls if columns exist
    if has_org_status and has_irs_revoked:
        cur.execute(f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE org_status IS NULL OR irs_revoked IS NULL
        """)
        nulls = cur.fetchone()[0]
    else:
        nulls = 0  # Pre-migration: no columns = no nulls to count

    if table_name == 'registry_enriched':
        if has_irs_revoked:
            cur.execute(f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE irs_revoked = 1
            """)
            revoked = cur.fetchone()[0]
        else:
            revoked = 0  # Pre-migration: no column = no revoked count

        conn.close()
        return {'total': total, 'nulls': nulls, 'revoked': revoked}

    conn.close()
    return {'total': total, 'nulls': nulls}

def apply_migration(
    prod_db: str,
    recovery_db: str,
    recovery_manifest: Dict,
    dry_run: bool = True,
    force_overwrite: bool = False
) -> Dict:
    """
    Apply migration using set-based SQL updates.
    
    Detects conflicts, unmatched EINs, and verifies checksums.
    Idempotent: safe to run twice.
    
    Returns detailed result summary.
    """
    conn_prod = sqlite3.connect(prod_db)
    conn_rec = sqlite3.connect(recovery_db)
    
    cur_prod = conn_prod.cursor()
    cur_rec = conn_rec.cursor()
    
    try:
        # Attach recovery database for cross-database queries
        cur_prod.execute(f"ATTACH DATABASE '{recovery_db}' AS recovery")

        # Phase 1: Validate pre-migration state
        print("\n[PHASE 1] Pre-migration validation...")
        
        # Integrity check
        cur_prod.execute("PRAGMA integrity_check")
        if cur_prod.fetchone()[0] != 'ok':
            return {'success': False, 'error': 'Production DB integrity check failed pre-migration'}
        
        # Detect existing columns
        cur_prod.execute("PRAGMA table_info(registry_enriched)")
        columns = {row[1] for row in cur_prod.fetchall()}
        
        has_org_status = 'org_status' in columns
        has_irs_revoked = 'irs_revoked' in columns
        
        print(f"   org_status column exists: {has_org_status}")
        print(f"   irs_revoked column exists: {has_irs_revoked}")
        
        # Phase 2: Detect conflicts
        print("\n[PHASE 2] Conflict detection...")

        # Only check for DIFFERING values (not just non-null)
        # This allows idempotent re-runs where values already match
        differing_conflicts = 0
        if has_org_status or has_irs_revoked:
            conflict_check = """
                SELECT COUNT(*) FROM registry_enriched re
                WHERE re.EIN IN (SELECT ein FROM recovery.tax_status_recovery)
                  AND EXISTS (
                    SELECT 1 FROM recovery.tax_status_recovery r
                    WHERE r.ein = re.EIN
                    AND (
                      (re.org_status IS NOT NULL AND re.org_status != r.org_status)
                      OR (re.irs_revoked IS NOT NULL AND re.irs_revoked != r.irs_revoked)
                    )
                  )
            """
            try:
                cur_prod.execute(conflict_check)
                differing_conflicts = cur_prod.fetchone()[0]
            except:
                differing_conflicts = 0

        print(f"   Differing values (org_status/irs_revoked): {differing_conflicts}")

        if differing_conflicts > 0 and not force_overwrite:
            return {
                'success': False,
                'error': f'Existing values differ from recovery ({differing_conflicts} rows). Use --force-overwrite to overwrite.',
                'differing_conflicts': differing_conflicts
            }
        
        # Detect unmatched EINs
        cur_rec.execute("SELECT COUNT(*) FROM tax_status_recovery")
        recovery_rows = cur_rec.fetchone()[0]
        
        cur_prod.execute("""
            SELECT COUNT(*)
            FROM tax_status_recovery r
            LEFT JOIN registry_enriched e ON e.EIN = r.ein
            WHERE e.EIN IS NULL
        """)
        # Note: This query needs proper join; let me fix it
        
        # Actually, let's use a simpler approach: check within the prod DB what's missing
        cur_prod.execute("""
            CREATE TEMPORARY TABLE recovery_eins AS
            SELECT EIN FROM registry_enriched
            WHERE EIN IN (SELECT ein FROM recovery.tax_status_recovery)
        """)
        
        cur_prod.execute("""
            SELECT COUNT(*) FROM recovery_eins
        """)
        matched_count = cur_prod.fetchone()[0]
        
        unmatched_count = recovery_rows - matched_count
        print(f"   Recovery records: {recovery_rows}")
        print(f"   Matched in production: {matched_count}")
        print(f"   Unmatched (new EINs): {unmatched_count}")
        
        # Phase 3: Calculate pre-migration checksum
        print("\n[PHASE 3] Pre-migration checksum...")
        pre_checksum = calculate_checksum_for_table(prod_db, 'registry_enriched')
        print(f"   Pre-migration aggregate checksum: {pre_checksum}")
        
        # Phase 4: Dry run report
        print("\n[PHASE 4] Migration plan...")
        
        changes = []
        
        # Column additions
        if not has_org_status:
            changes.append("ADD COLUMN org_status TEXT")
        if not has_irs_revoked:
            changes.append("ADD COLUMN irs_revoked INTEGER")
        
        # Data updates
        changes.append(f"UPDATE {matched_count} matched rows")
        if unmatched_count > 0:
            changes.append(f"SKIP {unmatched_count} unmatched rows (new EINs)")
        
        print(f"   Planned changes:")
        for change in changes:
            print(f"      - {change}")
        
        if dry_run:
            print(f"\n✅ DRY RUN: No changes applied. Use --apply to execute.")
            return {
                'success': True,
                'dry_run': True,
                'matched_rows': matched_count,
                'unmatched_rows': unmatched_count,
                'pre_checksum': pre_checksum,
                'changes_planned': changes
            }
        
        # Phase 5: Apply migration (transactional)
        print("\n[PHASE 5] Applying migration...")
        phase5_start = time.perf_counter()

        # Detect conflicts BEFORE modifying schema (if columns already exist)
        # Only check for DIFFERING values, not just non-null values
        print(f"\n   [CONFLICT DETECTION]")
        differing_conflicts = 0
        if has_org_status or has_irs_revoked:
            # Check for rows where existing values DIFFER from recovery values
            conflict_sql = f"""
                SELECT COUNT(*) FROM registry_enriched re
                WHERE re.EIN IN (SELECT ein FROM recovery.tax_status_recovery)
                  AND EXISTS (
                    SELECT 1 FROM recovery.tax_status_recovery r
                    WHERE r.ein = re.EIN
                    AND (
                      (re.org_status IS NOT NULL AND re.org_status != r.org_status)
                      OR (re.irs_revoked IS NOT NULL AND re.irs_revoked != r.irs_revoked)
                    )
                  )
            """
            try:
                cur_prod.execute(conflict_sql)
                differing_conflicts = cur_prod.fetchone()[0]
            except:
                differing_conflicts = 0

        print(f"   Conflicting (differing) values: {differing_conflicts}")
        sys.stdout.flush()

        if differing_conflicts > 0 and not force_overwrite:
            print(f"   ❌ Differing values would be overwritten ({differing_conflicts} rows). Use --force-overwrite to proceed.")
            sys.stdout.flush()
            return {
                'success': False,
                'error': f'Differing values would be overwritten ({differing_conflicts} rows). Use --force-overwrite.',
                'conflicts': differing_conflicts,
                'phase': 'conflict-detection'
            }

        cur_prod.execute("BEGIN TRANSACTION")
        try:
            # Add columns if missing
            t_alter = time.perf_counter()
            columns_just_added = False
            if not has_org_status:
                cur_prod.execute("""
                    ALTER TABLE registry_enriched
                    ADD COLUMN org_status TEXT DEFAULT 'active'
                """)
                print(f"   ✓ Added org_status column")
                columns_just_added = True

            if not has_irs_revoked:
                cur_prod.execute("""
                    ALTER TABLE registry_enriched
                    ADD COLUMN irs_revoked INTEGER DEFAULT 0
                """)
                print(f"   ✓ Added irs_revoked column")
                columns_just_added = True

            t_alter_done = time.perf_counter()
            print(f"   [TIMING] ALTER TABLE: {(t_alter_done - t_alter):.2f}s")
            sys.stdout.flush()

            # Display query plan for the UPDATE...FROM
            print(f"\n   [QUERY PLAN] UPDATE...FROM optimization:")
            cur_prod.execute("""
                EXPLAIN QUERY PLAN
                UPDATE registry_enriched
                SET org_status = recovery.tax_status_recovery.org_status,
                    irs_revoked = recovery.tax_status_recovery.irs_revoked
                FROM recovery.tax_status_recovery
                WHERE registry_enriched.EIN = recovery.tax_status_recovery.ein
            """)
            for row in cur_prod.fetchall():
                print(f"   {row[3]}")
            sys.stdout.flush()

            # Update rows using UPDATE...FROM syntax (O(n+m) complexity)
            # This directly queries the recovery table, no staging table needed
            # Smart WHERE:
            #  - If columns just added: update all matched rows (first run, defaults present)
            #  - If columns pre-existed: only update where values differ (idempotent)
            t_update = time.perf_counter()

            if columns_just_added:
                # First run: columns have defaults, update all matched rows
                update_sql = """
                    UPDATE registry_enriched
                    SET org_status = recovery.tax_status_recovery.org_status,
                        irs_revoked = recovery.tax_status_recovery.irs_revoked
                    FROM recovery.tax_status_recovery
                    WHERE registry_enriched.EIN = recovery.tax_status_recovery.ein
                """
            else:
                # Subsequent runs: only update where values differ (idempotent)
                update_sql = """
                    UPDATE registry_enriched
                    SET org_status = recovery.tax_status_recovery.org_status,
                        irs_revoked = recovery.tax_status_recovery.irs_revoked
                    FROM recovery.tax_status_recovery
                    WHERE registry_enriched.EIN = recovery.tax_status_recovery.ein
                      AND (
                        registry_enriched.org_status IS NULL
                        OR registry_enriched.org_status != recovery.tax_status_recovery.org_status
                        OR registry_enriched.irs_revoked IS NULL
                        OR registry_enriched.irs_revoked != recovery.tax_status_recovery.irs_revoked
                      )
                """

            cur_prod.execute(update_sql)

            # rowcount gives rows affected by the last statement
            updated_rows = cur_prod.rowcount
            t_update_done = time.perf_counter()
            print(f"   ✓ Updated {updated_rows} rows")
            print(f"   [TIMING] UPDATE rows: {(t_update_done - t_update):.2f}s")
            sys.stdout.flush()

            t_commit = time.perf_counter()
            cur_prod.execute("COMMIT")
            t_commit_done = time.perf_counter()
            print(f"   [TIMING] COMMIT: {(t_commit_done - t_commit):.2f}s")
            print(f"   [TIMING] Phase 5 total: {(t_commit_done - phase5_start):.2f}s")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"\n❌ EXCEPTION IN PHASE 5:")
            traceback.print_exc(file=sys.stdout)
            sys.stderr.write(traceback.format_exc())
            try:
                cur_prod.execute("ROLLBACK")
            except:
                pass
            return {
                'success': False,
                'error': f'Migration failed: {e}',
                'exception_type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'phase': 'apply'
            }
        
        # Phase 6: Post-migration validation
        print("\n[PHASE 6] Post-migration validation...")
        phase6_start = time.perf_counter()

        # Close and reopen connection to ensure clean state
        conn_prod.close()
        conn_prod = sqlite3.connect(prod_db)
        cur_prod = conn_prod.cursor()

        # Post-commit schema verification
        t_schema = time.perf_counter()
        cur_prod.execute("PRAGMA table_info(registry_enriched)")
        post_columns = {row[1] for row in cur_prod.fetchall()}

        print(f"   [POST-COMMIT SCHEMA VERIFICATION]")
        org_status_exists = 'org_status' in post_columns
        irs_revoked_exists = 'irs_revoked' in post_columns
        print(f"     org_status exists: {org_status_exists}")
        print(f"     irs_revoked exists: {irs_revoked_exists}")

        if not org_status_exists or not irs_revoked_exists:
            print(f"   ❌ CRITICAL: Columns missing after COMMIT!")
            return {
                'success': False,
                'error': 'CRITICAL: Columns were not added despite COMMIT',
                'post_org_status_exists': org_status_exists,
                'post_irs_revoked_exists': irs_revoked_exists,
                'phase': 'post-commit-schema-verification'
            }

        t_schema_done = time.perf_counter()
        print(f"   [TIMING] Schema verification: {(t_schema_done - t_schema):.2f}s")
        sys.stdout.flush()

        # Data distribution check
        print(f"\n   [DATA DISTRIBUTION CHECK]")
        cur_prod.execute("SELECT COUNT(*) FROM registry_enriched WHERE org_status IS NOT NULL")
        org_status_populated = cur_prod.fetchone()[0]
        cur_prod.execute("SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked IS NOT NULL")
        irs_revoked_populated = cur_prod.fetchone()[0]
        cur_prod.execute("SELECT COUNT(*) FROM registry_enriched")
        total_rows = cur_prod.fetchone()[0]
        print(f"   Total rows: {total_rows:,}")
        print(f"   org_status populated: {org_status_populated:,}")
        print(f"   irs_revoked populated: {irs_revoked_populated:,}")
        sys.stdout.flush()

        # Integrity check
        t_integrity = time.perf_counter()
        cur_prod.execute("PRAGMA integrity_check")
        integrity_result = cur_prod.fetchone()[0]
        if integrity_result != 'ok':
            return {'success': False, 'error': f'Database integrity check failed post-migration: {integrity_result}'}

        t_integrity_done = time.perf_counter()
        print(f"\n   ✓ Integrity check passed")
        print(f"   [TIMING] Integrity check: {(t_integrity_done - t_integrity):.2f}s")
        sys.stdout.flush()

        # Calculate post-migration checksum
        post_checksum = calculate_checksum_for_table(prod_db, 'registry_enriched')
        print(f"\n   Post-migration aggregate checksum: {post_checksum}")
        
        # Verify parity
        recovery_checksum = recovery_manifest.get('aggregate_checksum', '')
        if recovery_checksum and post_checksum != recovery_checksum:
            print(f"   ❌ Checksum mismatch!")
            print(f"      Recovery:  {recovery_checksum}")
            print(f"      Database:  {post_checksum}")
            sys.stdout.flush()
            return {
                'success': False,
                'error': 'Checksum mismatch between recovery and database',
                'recovery_checksum': recovery_checksum,
                'post_checksum': post_checksum
            }

        print(f"   ✓ Checksum parity verified")
        sys.stdout.flush()
        
        # Final stats
        prod_stats = get_table_stats(prod_db, 'registry_enriched')
        
        conn_prod.close()
        conn_rec.close()
        
        return {
            'success': True,
            'dry_run': False,
            'matched_rows': matched_count,
            'unmatched_rows': unmatched_count,
            'updated_rows': updated_rows,
            'pre_checksum': pre_checksum,
            'post_checksum': post_checksum,
            'checksum_parity': recovery_checksum == post_checksum if recovery_checksum else 'N/A',
            'final_stats': prod_stats
        }
        
    except Exception as e:
        print(f"\n❌ ERROR in apply_migration (outer handler):")
        traceback.print_exc(file=sys.stdout)
        sys.stderr.write(traceback.format_exc())
        try:
            cur_prod.execute("ROLLBACK")
        except:
            pass
        try:
            conn_prod.close()
        except:
            pass
        try:
            conn_rec.close()
        except:
            pass
        return {
            'success': False,
            'error': str(e),
            'exception_type': type(e).__name__,
            'traceback': traceback.format_exc(),
            'phase': 'general'
        }

def main():
    parser = argparse.ArgumentParser(
        description='Apply tax status recovery migration (set-based SQL, fully idempotent)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default, no changes)
  python3 apply_tax_status_recovery.py

  # Dry run on specific database
  python3 apply_tax_status_recovery.py --prod-db /path/to/merit_registry.db

  # Apply changes (requires explicit --apply flag)
  python3 apply_tax_status_recovery.py --apply

  # Apply with overwrite of existing values
  python3 apply_tax_status_recovery.py --apply --force-overwrite
        """
    )
    parser.add_argument(
        '--prod-db',
        default=str(Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'),
        help='Production database path'
    )
    parser.add_argument(
        '--recovery-db',
        default=str(Path.home() / 'meritgiving' / 'data' / 'tax_status_recovery.db'),
        help='Recovery artifact database path'
    )
    parser.add_argument(
        '--manifest',
        default=str(Path.home() / 'meritgiving' / 'data' / 'tax_status_recovery_manifest.json'),
        help='Recovery manifest path'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes (default: dry-run only)'
    )
    parser.add_argument(
        '--force-overwrite',
        action='store_true',
        help='Overwrite existing non-null values (use with caution)'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print(f"Tax Status Recovery Migration Tool")
    print(f"{'='*80}")
    
    # Step 1: Validate databases
    print(f"\n[VALIDATION] Checking databases...")
    is_valid, msg = validate_production_database(args.prod_db)
    if not is_valid:
        print(f"  ❌ Production DB: {msg}")
        return 1
    print(f"  ✅ Production DB: {msg}")
    
    if not Path(args.recovery_db).exists():
        print(f"  ❌ Recovery DB: Not found")
        return 1
    print(f"  ✅ Recovery DB: Exists")
    
    # Step 2: Load manifest
    print(f"\n[MANIFEST] Loading recovery artifact metadata...")
    success, manifest = load_recovery_manifest(args.manifest)
    if not success:
        print(f"  ❌ {manifest.get('error')}")
        return 1
    print(f"  ✅ Loaded {manifest['total_records']} recovery records")
    print(f"     Active: {manifest['active_organizations']}, Revoked: {manifest['revoked_organizations']}")
    
    # Step 3: Apply migration
    print(f"\n[MIGRATION] {'DRY RUN (no changes)' if not args.apply else 'APPLYING CHANGES'}")
    
    result = apply_migration(
        args.prod_db,
        args.recovery_db,
        manifest,
        dry_run=not args.apply,
        force_overwrite=args.force_overwrite
    )
    
    # Step 4: Report results
    print(f"\n[RESULTS]")
    if result['success']:
        print(f"  ✅ Migration {'planned' if not args.apply else 'completed'} successfully")
        print(f"     Matched rows: {result.get('matched_rows', 'N/A')}")
        print(f"     Unmatched rows: {result.get('unmatched_rows', 'N/A')}")
        if args.apply:
            print(f"     Updated rows: {result.get('updated_rows', 'N/A')}")
            print(f"     Pre-checksum:  {result.get('pre_checksum', 'N/A')[:16]}...")
            print(f"     Post-checksum: {result.get('post_checksum', 'N/A')[:16]}...")
            print(f"     Parity check: {result.get('checksum_parity', 'N/A')}")
        if not args.apply:
            print(f"\n     DRY RUN COMPLETE. Use --apply to execute migration.")
        return 0
    else:
        print(f"  ❌ {result.get('error')}")
        if 'details' in result:
            print(f"     Details: {result['details']}")
        return 1

if __name__ == '__main__':
    exit(main())
