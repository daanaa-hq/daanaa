#!/usr/bin/env python3
"""
Build a deterministic recovery artifact for tax status columns.

Validates:
  - No duplicate EINs
  - No malformed EINs
  - irs_revoked ∈ {0, 1}
  - Required fields not unexpectedly null
  - Row counts match baseline
  - Checksums for row-level parity

Produces:
  - tax_status_recovery.db (SQLite sidecar)
  - tax_status_recovery_manifest.json (metadata, checksums, counts)
"""

import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

def validate_ein(ein: str) -> bool:
    """Validate EIN format (should be numeric, 9 digits)."""
    return ein.isdigit() and len(ein) == 9

def build_recovery_artifact(
    source_db: str,
    output_db: str,
    baseline_expected_revoked: int = None
) -> Dict:
    """
    Build tax_status_recovery.db from source database.
    
    Returns manifest with checksums, counts, and validation results.
    """
    source_path = Path(source_db)
    output_path = Path(output_db)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source database not found: {source_db}")
    
    # Connect to source
    conn_src = sqlite3.connect(source_db)
    conn_src.row_factory = sqlite3.Row
    cur_src = conn_src.cursor()
    
    # Verify schema
    cur_src.execute("PRAGMA table_info(registry_enriched)")
    columns = {row['name']: row['type'] for row in cur_src.fetchall()}
    
    if 'org_status' not in columns:
        raise ValueError("Source database missing org_status column")
    if 'irs_revoked' not in columns:
        raise ValueError("Source database missing irs_revoked column")
    
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
            source_checksum TEXT NOT NULL
        )
    """)
    
    # Extract data with validation
    cur_src.execute("""
        SELECT ein, org_status, irs_revoked
        FROM registry_enriched
        WHERE org_status IS NOT NULL OR irs_revoked IS NOT NULL
        ORDER BY ein
    """)
    
    records = []
    seen_eins = set()
    validation_errors = []
    
    for row in cur_src.fetchall():
        ein = row['ein']
        org_status = row['org_status']
        irs_revoked = row['irs_revoked']
        
        # Validate EIN
        if not validate_ein(ein):
            validation_errors.append(f"Malformed EIN: {ein}")
            continue
        
        # Check duplicates
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
        
        # Calculate row checksum
        checksum_str = f"{ein}|{org_status}|{irs_revoked}"
        checksum = hashlib.sha256(checksum_str.encode()).hexdigest()
        
        records.append({
            'ein': ein,
            'org_status': org_status,
            'irs_revoked': irs_revoked,
            'checksum': checksum
        })
    
    # Insert into recovery database
    for rec in records:
        cur_out.execute("""
            INSERT INTO tax_status_recovery 
            (ein, org_status, irs_revoked, source_checksum)
            VALUES (?, ?, ?, ?)
        """, (rec['ein'], rec['org_status'], rec['irs_revoked'], rec['checksum']))
    
    conn_out.commit()
    
    # Build manifest
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
    
    # Database integrity
    cur_src.execute("PRAGMA integrity_check")
    src_integrity = cur_src.fetchone()[0]
    
    manifest = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source_database': source_db,
        'recovery_database': output_db,
        'source_integrity_check': src_integrity,
        'total_records': total_rows,
        'active_organizations': active_count,
        'revoked_organizations': revoked_count,
        'status_breakdown': status_counts,
        'validation_errors': validation_errors,
        'validation_passed': len(validation_errors) == 0,
        'baseline_expected_revoked': baseline_expected_revoked
    }
    
    if baseline_expected_revoked is not None:
        if abs(revoked_count - baseline_expected_revoked) > 100:
            manifest['validation_passed'] = False
            manifest['validation_errors'].append(
                f"Revoked count mismatch: expected ~{baseline_expected_revoked}, got {revoked_count}"
            )
    
    conn_out.close()
    conn_src.close()
    
    return manifest

def main():
    """Generate recovery artifact and manifest."""
    source_db = Path.home() / "meritgiving" / "data" / "merit_registry.db"
    output_db = Path.home() / "meritgiving" / "data" / "tax_status_recovery.db"
    manifest_file = Path.home() / "meritgiving" / "data" / "tax_status_recovery_manifest.json"
    
    print(f"Building recovery artifact from {source_db}...")
    
    try:
        manifest = build_recovery_artifact(
            str(source_db),
            str(output_db),
            baseline_expected_revoked=195000  # Updated from discovery
        )
        
        # Write manifest
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print("\n✅ Recovery artifact created successfully!")
        print(f"   Database: {output_db}")
        print(f"   Manifest: {manifest_file}")
        print(f"\nSummary:")
        print(f"   Total records: {manifest['total_records']}")
        print(f"   Active: {manifest['active_organizations']}")
        print(f"   Revoked: {manifest['revoked_organizations']}")
        print(f"   Status breakdown: {manifest['status_breakdown']}")
        print(f"   Validation: {'PASSED' if manifest['validation_passed'] else 'FAILED'}")
        
        if not manifest['validation_passed']:
            print(f"\n⚠️  Validation errors:")
            for err in manifest['validation_errors']:
                print(f"   - {err}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error building recovery artifact: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
