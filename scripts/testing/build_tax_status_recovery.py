#!/usr/bin/env python3
"""
Build a deterministic recovery artifact for tax status columns.

Strict validation:
  - No duplicate EINs
  - No malformed EINs (must be exactly 9 digits)
  - irs_revoked ∈ {0, 1} only
  - Required fields not unexpectedly null
  - Row counts reported (not assumed)
  - SHA256 checksums for row-level parity
  - SQLite integrity check on source

NO hard-coded assumptions about row counts or revoked totals.
Outputs manifest with actual counts for comparison against production.
"""

import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

def validate_ein(ein: str) -> bool:
    """Validate EIN format: exactly 9 digits."""
    return isinstance(ein, str) and ein.isdigit() and len(ein) == 9

def build_recovery_artifact(
    source_db: str,
    output_db: str
) -> Dict:
    """
    Build tax_status_recovery.db from source database.
    
    Returns manifest with checksums, counts, and validation results.
    No assumptions about row counts or revoked totals.
    """
    source_path = Path(source_db)
    output_path = Path(output_db)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source database not found: {source_db}")
    
    # Connect to source
    conn_src = sqlite3.connect(source_db)
    conn_src.row_factory = sqlite3.Row
    cur_src = conn_src.cursor()
    
    # Verify source integrity
    cur_src.execute("PRAGMA integrity_check")
    integrity = cur_src.fetchone()[0]
    if integrity != 'ok':
        raise ValueError(f"Source database integrity check failed: {integrity}")
    
    # Verify schema
    cur_src.execute("PRAGMA table_info(registry_enriched)")
    columns = {row['name']: row['type'] for row in cur_src.fetchall()}
    
    if 'org_status' not in columns:
        raise ValueError("Source database missing org_status column")
    if 'irs_revoked' not in columns:
        raise ValueError("Source database missing irs_revoked column")
    if 'EIN' not in columns:
        raise ValueError("Source database missing EIN column")
    
    # Create recovery database
    if output_path.exists():
        output_path.unlink()
    
    conn_out = sqlite3.connect(output_db)
    cur_out = conn_out.cursor()
    
    # Create recovery table with strict schema
    cur_out.execute("""
        CREATE TABLE tax_status_recovery (
            ein TEXT PRIMARY KEY,
            org_status TEXT NOT NULL,
            irs_revoked INTEGER NOT NULL CHECK (irs_revoked IN (0, 1)),
            row_checksum TEXT NOT NULL
        )
    """)
    
    # Create index for parity verification
    cur_out.execute("""
        CREATE INDEX idx_tax_status_recovery_checksum ON tax_status_recovery(row_checksum)
    """)
    
    # Extract data with validation
    cur_src.execute("""
        SELECT EIN, org_status, irs_revoked
        FROM registry_enriched
        WHERE org_status IS NOT NULL OR irs_revoked IS NOT NULL
        ORDER BY EIN
    """)

    records = []
    seen_eins = set()
    validation_errors = []

    for row in cur_src.fetchall():
        ein = row['EIN']
        org_status = row['org_status']
        irs_revoked = row['irs_revoked']
        
        # Validate EIN
        if not validate_ein(ein):
            validation_errors.append(f"Malformed EIN: '{ein}' (must be exactly 9 digits)")
            continue
        
        # Check duplicates in source
        if ein in seen_eins:
            validation_errors.append(f"Duplicate EIN in source: {ein}")
            continue
        seen_eins.add(ein)
        
        # Validate irs_revoked
        if irs_revoked not in (0, 1):
            validation_errors.append(
                f"Invalid irs_revoked for {ein}: {irs_revoked} (must be 0 or 1)"
            )
            continue
        
        # Validate org_status not null
        if org_status is None:
            validation_errors.append(f"Null org_status for {ein}")
            continue
        
        # Calculate row checksum (order matters for determinism)
        checksum_str = f"{ein}|{org_status}|{irs_revoked}"
        checksum = hashlib.sha256(checksum_str.encode()).hexdigest()
        
        records.append({
            'ein': ein,
            'org_status': org_status,
            'irs_revoked': irs_revoked,
            'checksum': checksum
        })
    
    # Insert into recovery database (transactional)
    cur_out.execute("BEGIN TRANSACTION")
    try:
        for rec in records:
            cur_out.execute("""
                INSERT INTO tax_status_recovery 
                (ein, org_status, irs_revoked, row_checksum)
                VALUES (?, ?, ?, ?)
            """, (rec['ein'], rec['org_status'], rec['irs_revoked'], rec['checksum']))
        
        cur_out.execute("COMMIT")
    except Exception as e:
        cur_out.execute("ROLLBACK")
        raise ValueError(f"Failed to insert recovery records: {e}")
    
    # Verify recovery database integrity
    cur_out.execute("PRAGMA integrity_check")
    out_integrity = cur_out.fetchone()[0]
    if out_integrity != 'ok':
        raise ValueError(f"Recovery database integrity check failed: {out_integrity}")
    
    # Build statistics (no assumptions, just counts)
    cur_out.execute("SELECT COUNT(*) FROM tax_status_recovery")
    total_rows = cur_out.fetchone()[0]
    
    cur_out.execute(
        "SELECT COUNT(*) FROM tax_status_recovery WHERE irs_revoked = 1"
    )
    revoked_count = cur_out.fetchone()[0]
    
    cur_out.execute(
        "SELECT COUNT(*) FROM tax_status_recovery WHERE irs_revoked = 0"
    )
    active_count = cur_out.fetchone()[0]
    
    # Count by org_status
    cur_out.execute("""
        SELECT org_status, COUNT(*) as cnt
        FROM tax_status_recovery
        GROUP BY org_status
        ORDER BY org_status
    """)
    status_counts = {row[0]: row[1] for row in cur_out.fetchall()}
    
    # Calculate aggregate checksum (for parity verification)
    cur_out.execute("""
        SELECT GROUP_CONCAT(row_checksum, '|')
        FROM tax_status_recovery
        ORDER BY ein
    """)
    checksums_concat = cur_out.fetchone()[0] or ""
    aggregate_checksum = hashlib.sha256(checksums_concat.encode()).hexdigest()
    
    manifest = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source_database': source_db,
        'recovery_database': str(output_db),
        'source_integrity_check': integrity,
        'recovery_integrity_check': out_integrity,
        'total_records': total_rows,
        'active_organizations': active_count,
        'revoked_organizations': revoked_count,
        'status_breakdown': status_counts,
        'aggregate_checksum': aggregate_checksum,
        'validation_errors': validation_errors,
        'validation_passed': len(validation_errors) == 0,
        'records_skipped_due_to_errors': len(validation_errors)
    }
    
    conn_out.close()
    conn_src.close()
    
    return manifest

def main():
    """Generate recovery artifact and manifest."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build tax status recovery artifact')
    parser.add_argument(
        '--source-db',
        default=str(Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'),
        help='Source database path'
    )
    parser.add_argument(
        '--output-db',
        default=str(Path.home() / 'meritgiving' / 'data' / 'tax_status_recovery.db'),
        help='Output recovery artifact path'
    )
    parser.add_argument(
        '--manifest',
        default=str(Path.home() / 'meritgiving' / 'data' / 'tax_status_recovery_manifest.json'),
        help='Output manifest path'
    )
    
    args = parser.parse_args()
    
    print(f"Building recovery artifact from {args.source_db}...")
    
    try:
        manifest = build_recovery_artifact(args.source_db, args.output_db)
        
        # Write manifest
        with open(args.manifest, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print("\n✅ Recovery artifact created successfully!")
        print(f"   Database: {args.output_db}")
        print(f"   Manifest: {args.manifest}")
        print(f"\nData Summary (NO ASSUMPTIONS):")
        print(f"   Total records: {manifest['total_records']}")
        print(f"   Active (irs_revoked=0): {manifest['active_organizations']}")
        print(f"   Revoked (irs_revoked=1): {manifest['revoked_organizations']}")
        print(f"   Status breakdown: {json.dumps(manifest['status_breakdown'], indent=4)}")
        print(f"\nIntegrity:")
        print(f"   Source: {manifest['source_integrity_check']}")
        print(f"   Recovery: {manifest['recovery_integrity_check']}")
        print(f"\nChecksum (for parity verification):")
        print(f"   Aggregate: {manifest['aggregate_checksum']}")
        print(f"\nValidation:")
        print(f"   Passed: {manifest['validation_passed']}")
        if manifest['validation_errors']:
            print(f"   Errors ({len(manifest['validation_errors'])}):")
            for err in manifest['validation_errors'][:10]:  # Show first 10
                print(f"      - {err}")
            if len(manifest['validation_errors']) > 10:
                print(f"      ... and {len(manifest['validation_errors']) - 10} more")
        
        return 0 if manifest['validation_passed'] else 1
        
    except Exception as e:
        print(f"❌ Error building recovery artifact: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
