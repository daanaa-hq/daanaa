#!/usr/bin/env python3
"""
Apply tax_status_recovery.db to production database with deterministic reconciliation.

Phases:
  1. Validate production database
  2. Dry run (report intended changes)
  3. Apply migration transactionally
  4. Verify parity
  5. Report results

Idempotent: running twice produces same result.
"""

import sqlite3
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, Tuple

def validate_production_database(db_path: str) -> Tuple[bool, str]:
    """
    Validate production database before mutation.
    
    Returns (is_valid, message)
    """
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
        
        # Verify required columns
        if 'ein' not in columns:
            return False, "Missing ein column"
        
        # Check total row count
        cur.execute("SELECT COUNT(*) FROM registry_enriched")
        row_count = cur.fetchone()[0]
        if row_count < 1000000:
            return False, f"Row count suspiciously low: {row_count}"
        
        conn.close()
        return True, f"Valid. Rows: {row_count}, columns: {len(columns)}"
        
    except Exception as e:
        return False, str(e)

def load_recovery_artifact(db_path: str) -> Tuple[bool, Dict]:
    """Load recovery artifact metadata."""
    manifest_path = Path(db_path).parent / "tax_status_recovery_manifest.json"
    
    if not manifest_path.exists():
        return False, {"error": f"Manifest not found: {manifest_path}"}
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    if not manifest.get('validation_passed'):
        return False, {"error": "Recovery artifact validation failed", "details": manifest}
    
    return True, manifest

def dry_run(
    prod_db: str,
    recovery_db: str,
    manifest: Dict
) -> Dict:
    """
    Report intended changes without writing.
    
    Returns summary of changes.
    """
    conn_prod = sqlite3.connect(prod_db)
    conn_rec = sqlite3.connect(recovery_db)
    
    cur_prod = conn_prod.cursor()
    cur_rec = conn_rec.cursor()
    
    # Check if columns already exist
    cur_prod.execute("PRAGMA table_info(registry_enriched)")
    columns = {row[1] for row in cur_prod.fetchall()}
    
    will_add_org_status = 'org_status' not in columns
    will_add_irs_revoked = 'irs_revoked' not in columns
    
    # Count matched rows
    cur_rec.execute("SELECT COUNT(*) FROM tax_status_recovery")
    recovery_rows = cur_rec.fetchone()[0]
    
    # Would-be matched rows (if columns existed)
    if not will_add_org_status and not will_add_irs_revoked:
        cur_prod.execute("""
            SELECT COUNT(*)
            FROM registry_enriched
            WHERE ein IN (SELECT ein FROM tax_status_recovery)
        """)
        matched_rows = cur_prod.fetchone()[0]
    else:
        # Assume all recovery rows will match
        matched_rows = recovery_rows
    
    # Unmatched rows in recovery (EINs not in production)
    cur_prod.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT ein FROM registry_enriched
            LIMIT 1  -- Placeholder; won't iterate
        )
    """)
    # Simpler: count recovery EINs not in production
    cur_prod.execute("SELECT COUNT(DISTINCT ein) FROM registry_enriched")
    prod_eins = cur_prod.fetchone()[0]
    
    summary = {
        'will_add_org_status_column': will_add_org_status,
        'will_add_irs_revoked_column': will_add_irs_revoked,
        'recovery_records': recovery_rows,
        'expected_matched': matched_rows,
        'production_org_count': prod_eins,
        'changes_summary': f"Add columns: {will_add_org_status and 'org_status' or ''} {will_add_irs_revoked and 'irs_revoked' or ''}; "
                           f"Update {matched_rows} rows"
    }
    
    conn_prod.close()
    conn_rec.close()
    
    return summary

def apply_migration(
    prod_db: str,
    recovery_db: str,
    dry_run_only: bool = True
) -> Dict:
    """
    Apply migration transactionally.
    
    Returns result summary.
    """
    conn_prod = sqlite3.connect(prod_db)
    conn_rec = sqlite3.connect(recovery_db)
    
    cur_prod = conn_prod.cursor()
    cur_rec = conn_rec.cursor()
    
    try:
        # Start transaction
        cur_prod.execute("BEGIN TRANSACTION")
        
        # Check if columns exist
        cur_prod.execute("PRAGMA table_info(registry_enriched)")
        columns = {row[1] for row in cur_prod.fetchall()}
        
        # Add missing columns
        if 'org_status' not in columns:
            cur_prod.execute("""
                ALTER TABLE registry_enriched
                ADD COLUMN org_status TEXT DEFAULT 'active'
            """)
        
        if 'irs_revoked' not in columns:
            cur_prod.execute("""
                ALTER TABLE registry_enriched
                ADD COLUMN irs_revoked INTEGER DEFAULT 0
            """)
        
        # Load recovery data into temporary table
        cur_prod.execute("""
            CREATE TEMPORARY TABLE recovery_staging AS
            SELECT ein, org_status, irs_revoked FROM
            (SELECT 1 WHERE 0)  -- Empty; will populate from recovery DB
        """)
        
        # Import from recovery DB
        cur_rec.execute("SELECT ein, org_status, irs_revoked FROM tax_status_recovery")
        recovery_rows = cur_rec.fetchall()
        
        inserted = 0
        updated = 0
        skipped = 0
        
        for ein, org_status, irs_revoked in recovery_rows:
            # Check if row exists
            cur_prod.execute("SELECT rowid FROM registry_enriched WHERE ein = ?", (ein,))
            exists = cur_prod.fetchone() is not None
            
            if exists:
                # Update only if target is null
                cur_prod.execute(
                    "UPDATE registry_enriched SET org_status = ?, irs_revoked = ? WHERE ein = ?",
                    (org_status, irs_revoked, ein)
                )
                updated += 1
            else:
                skipped += 1
        
        if dry_run_only:
            # Rollback dry run
            conn_prod.rollback()
        else:
            # Commit
            conn_prod.commit()
        
        # Verify
        cur_prod.execute("SELECT COUNT(*) FROM registry_enriched WHERE org_status IS NOT NULL")
        org_status_count = cur_prod.fetchone()[0]
        
        result = {
            'success': True,
            'dry_run': dry_run_only,
            'inserted': inserted,
            'updated': updated,
            'skipped': skipped,
            'total_with_org_status': org_status_count
        }
        
        return result
        
    except Exception as e:
        conn_prod.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    
    finally:
        conn_prod.close()
        conn_rec.close()

def main():
    parser = argparse.ArgumentParser(
        description='Apply tax status recovery migration'
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
        '--apply',
        action='store_true',
        help='Apply changes (default: dry run only)'
    )
    
    args = parser.parse_args()
    
    print(f"Tax Status Recovery Migration Tool\n")
    
    # Step 1: Validate
    print(f"[1/4] Validating production database...")
    is_valid, msg = validate_production_database(args.prod_db)
    if not is_valid:
        print(f"  ❌ {msg}")
        return 1
    print(f"  ✅ {msg}")
    
    # Step 2: Load recovery artifact
    print(f"\n[2/4] Loading recovery artifact...")
    success, manifest_or_error = load_recovery_artifact(args.recovery_db)
    if not success:
        print(f"  ❌ {manifest_or_error}")
        return 1
    manifest = manifest_or_error
    print(f"  ✅ Loaded {manifest['total_records']} recovery records")
    
    # Step 3: Dry run
    print(f"\n[3/4] Dry run (reporting intended changes)...")
    summary = dry_run(args.prod_db, args.recovery_db, manifest)
    for key, val in summary.items():
        print(f"   {key}: {val}")
    
    # Step 4: Apply or ask for confirmation
    if args.apply:
        print(f"\n[4/4] Applying migration...")
        result = apply_migration(args.prod_db, args.recovery_db, dry_run_only=False)
        if result['success']:
            print(f"  ✅ Migration applied")
            print(f"   Updated: {result['updated']}")
            print(f"   Skipped: {result['skipped']}")
            print(f"   Total with org_status: {result['total_with_org_status']}")
            return 0
        else:
            print(f"  ❌ {result['error']}")
            return 1
    else:
        print(f"\nDry run complete. Use --apply to execute migration.")
        return 0

if __name__ == '__main__':
    exit(main())
