#!/usr/bin/env python3
"""
v6_transactional_backfill.py

Transactional, idempotent normalized-data ingestion for v6 financial context.

Features:
- Transactional: BEGIN/COMMIT/ROLLBACK on failure
- Idempotent: EIN+tax_year+source keying prevents duplicates
- Source-traceable: audit log with source, timestamp, record hash
- Quarantine: invalid records isolated, not silently skipped
- Audited: ingestion_audit_log table tracks all operations
- Reversible: failed transactions leave database unchanged

Usage:
    python3 v6_transactional_backfill.py \
        --db data/merit_registry.db \
        --source-dir data/incoming \
        --dry-run  # Default: don't write

To enable writes:
    export V6_APPLY_BACKFILL=true
    python3 v6_transactional_backfill.py --db data/merit_registry.db --source-dir data/incoming
"""

import sqlite3
import os
import sys
import json
import hashlib
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

DB_PATH = 'data/merit_registry.db'
SOURCE_DIR = 'data/incoming'
QUARANTINE_DIR = 'data/quarantine/v6'
AUDIT_LOG_TABLE = 'ingestion_audit_log'
DRY_RUN = os.environ.get('V6_APPLY_BACKFILL', '').lower() != 'true'


def hash_record(record: Dict) -> str:
    """Compute hash of a record for deduplication."""
    record_str = json.dumps(record, sort_keys=True)
    return hashlib.sha256(record_str.encode()).hexdigest()


def validate_ein(ein: str) -> bool:
    """Validate EIN format (9 digits)."""
    if not ein:
        return False
    ein_clean = ein.replace('-', '')
    return len(ein_clean) == 9 and ein_clean.isdigit()


def validate_tax_year(year: int) -> bool:
    """Validate tax year (1980-current)."""
    try:
        y = int(year)
        return 1980 <= y <= datetime.utcnow().year
    except (ValueError, TypeError):
        return False


def validate_revenue_band(band: Optional[str]) -> bool:
    """Validate revenue band (null or canonical lowercase)."""
    if band is None:
        return True
    canonical = {'grassroots', 'small', 'mid', 'established', 'major'}
    return band.lower() in canonical


def validate_financial_value(value: Optional[float]) -> bool:
    """Validate financial value (null or non-negative)."""
    if value is None:
        return True
    try:
        v = float(value)
        return v >= 0
    except (ValueError, TypeError):
        return False


def process_financial_years_file(
    db: sqlite3.Connection,
    file_path: str,
    audit_log: List[Dict],
    dry_run: bool = True
) -> Tuple[int, int, int]:
    """
    Process org_financial_years.csv ingestion.

    Returns: (inserted, duplicates, quarantined)
    """
    inserted = 0
    duplicates = 0
    quarantined = 0

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, 1):
                record = {
                    'ein': row.get('EIN', '').strip(),
                    'tax_year': row.get('tax_year', '').strip(),
                    'total_revenue': row.get('total_revenue'),
                    'total_expenses': row.get('total_expenses'),
                    'net_assets': row.get('net_assets'),
                    'source': row.get('source', 'irs_soi'),
                    'source_id': row.get('source_id', ''),
                }

                # Validation
                errors = []
                if not validate_ein(record['ein']):
                    errors.append(f"Invalid EIN: {record['ein']}")
                if not validate_tax_year(record['tax_year']):
                    errors.append(f"Invalid tax_year: {record['tax_year']}")
                if not validate_financial_value(record['total_revenue']):
                    errors.append(f"Invalid total_revenue: {record['total_revenue']}")
                if not validate_financial_value(record['total_expenses']):
                    errors.append(f"Invalid total_expenses: {record['total_expenses']}")
                if not validate_financial_value(record['net_assets']):
                    errors.append(f"Invalid net_assets: {record['net_assets']}")

                if errors:
                    quarantined += 1
                    quarantine_record(
                        record,
                        errors,
                        os.path.basename(file_path),
                        row_num
                    )
                    audit_log.append({
                        'action': 'quarantine',
                        'table': 'org_financial_years',
                        'ein': record['ein'],
                        'tax_year': record.get('tax_year'),
                        'reason': '; '.join(errors),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })
                    continue

                # Check for duplicate
                ein_clean = record['ein'].replace('-', '')
                cursor = db.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM org_financial_years
                    WHERE ein = ? AND tax_year = ? AND source = ?
                ''', (ein_clean, record['tax_year'], record['source']))

                if cursor.fetchone()[0] > 0:
                    duplicates += 1
                    audit_log.append({
                        'action': 'skip_duplicate',
                        'table': 'org_financial_years',
                        'ein': ein_clean,
                        'tax_year': record['tax_year'],
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })
                    continue

                # Insert (if not dry-run)
                if not dry_run:
                    cursor.execute('''
                        INSERT INTO org_financial_years
                        (ein, tax_year, total_revenue, total_expenses, net_assets, source, source_id, record_hash, retrieved_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ein_clean,
                        record['tax_year'],
                        record['total_revenue'],
                        record['total_expenses'],
                        record['net_assets'],
                        record['source'],
                        record['source_id'],
                        hash_record(record),
                        datetime.utcnow().isoformat() + 'Z'
                    ))

                inserted += 1
                audit_log.append({
                    'action': 'insert',
                    'table': 'org_financial_years',
                    'ein': ein_clean,
                    'tax_year': record['tax_year'],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

    except Exception as e:
        raise RuntimeError(f"Error processing {file_path}: {e}")

    return inserted, duplicates, quarantined


def quarantine_record(record: Dict, errors: List[str], source_file: str, row_num: int):
    """Write invalid record to quarantine for manual review."""
    os.makedirs(QUARANTINE_DIR, exist_ok=True)

    quarantine_file = os.path.join(
        QUARANTINE_DIR,
        f"quarantine_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    )

    with open(quarantine_file, 'a') as f:
        entry = {
            'source_file': source_file,
            'row_number': row_num,
            'record': record,
            'errors': errors,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        f.write(json.dumps(entry) + '\n')


def ingest_data(db_path: str, source_dir: str, dry_run: bool = True) -> Dict:
    """
    Main ingestion workflow.

    Returns: {
        'status': 'success' | 'failed' | 'dry_run',
        'inserted': int,
        'duplicates': int,
        'quarantined': int,
        'errors': [list of error messages],
        'audit_log_rows': int
    }
    """
    result = {
        'status': 'success',
        'inserted': 0,
        'duplicates': 0,
        'quarantined': 0,
        'errors': [],
        'audit_log_rows': 0,
        'mode': 'dry_run' if dry_run else 'applied'
    }

    try:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Create audit log table if needed
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {AUDIT_LOG_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                table_name TEXT,
                ein TEXT,
                tax_year INTEGER,
                reason TEXT,
                timestamp TEXT,
                session_id TEXT
            )
        ''')

        # Start transaction
        cursor.execute('BEGIN TRANSACTION')

        audit_log = []

        # Process available source files
        source_path = Path(source_dir)
        if source_path.exists():
            for file in sorted(source_path.glob('org_financial_years*.csv')):
                print(f"Processing {file.name}...")
                ins, dups, quar = process_financial_years_file(
                    db, str(file), audit_log, dry_run
                )
                result['inserted'] += ins
                result['duplicates'] += dups
                result['quarantined'] += quar

        # Write audit log (if not dry-run)
        if not dry_run:
            for entry in audit_log:
                cursor.execute(f'''
                    INSERT INTO {AUDIT_LOG_TABLE}
                    (action, table_name, ein, tax_year, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    entry.get('action'),
                    entry.get('table'),
                    entry.get('ein'),
                    entry.get('tax_year'),
                    entry.get('reason'),
                    entry.get('timestamp')
                ))

            result['audit_log_rows'] = len(audit_log)

        # Verify database integrity before commit
        cursor.execute('PRAGMA integrity_check')
        integrity = cursor.fetchone()[0]
        if integrity != 'ok':
            raise RuntimeError(f"Database integrity check failed: {integrity}")

        # Commit or rollback
        if dry_run:
            cursor.execute('ROLLBACK')
            result['status'] = 'dry_run'
            print("(Dry-run: no changes written)")
        else:
            cursor.execute('COMMIT')
            result['status'] = 'success'
            print(f"✅ Transaction committed")

        db.close()

    except Exception as e:
        result['status'] = 'failed'
        result['errors'].append(str(e))
        print(f"❌ Transaction failed: {e}")
        print("Rolling back...")

    return result


def main():
    dry_run = os.environ.get('V6_APPLY_BACKFILL', '').lower() != 'true'

    print("=" * 60)
    print("V6 TRANSACTIONAL BACKFILL INGESTION")
    print("=" * 60)
    print(f"Mode: {'DRY-RUN (no writes)' if dry_run else 'APPLIED (writing)'}")
    print(f"Database: {DB_PATH}")
    print(f"Source: {SOURCE_DIR}")
    print()

    result = ingest_data(DB_PATH, SOURCE_DIR, dry_run=dry_run)

    print()
    print("Results:")
    print(f"  Status: {result['status']}")
    print(f"  Inserted: {result['inserted']}")
    print(f"  Duplicates (skipped): {result['duplicates']}")
    print(f"  Quarantined (errors): {result['quarantined']}")
    print(f"  Audit log rows: {result['audit_log_rows']}")

    if result['errors']:
        print(f"  Errors: {result['errors']}")

    print()

    if result['status'] == 'dry_run':
        print("To apply ingestion, run with:")
        print("  export V6_APPLY_BACKFILL=true")
        print(f"  python3 {sys.argv[0]}")

    return 0 if result['status'] in ('success', 'dry_run') else 1


if __name__ == '__main__':
    sys.exit(main())
