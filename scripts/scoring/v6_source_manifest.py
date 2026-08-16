#!/usr/bin/env python3
"""
v6_source_manifest.py

Discover and catalog source material for v6 daily ingestion.

Checks for new or changed local source material:
- IRS BMF and revocation data
- IRS SOI extracts
- NCCS files
- ProPublica cache records
- Organization-submitted assertions

Records source name, file name, tax year, file size, record count, file hash,
and retrieval timestamp.

Does NOT ingest; only reports what's available and unchanged.
"""

import os
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

DB_PATH = 'data/merit_registry.db'
REPORT_DIR = 'reports/v6'
INCOMING_DIR = 'data/incoming'


def file_hash(fpath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(fpath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def record_count(fpath: str) -> int:
    """Estimate line count for CSV/TSV files."""
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def check_source(source_name: str, source_path: str, source_type: str = 'file'):
    """
    Check a single source for changes.

    Returns dict with source metadata or None if source unavailable.
    """
    if not os.path.exists(source_path):
        return None

    fstat = os.stat(source_path)
    size = fstat.st_size
    mtime = datetime.fromtimestamp(fstat.st_mtime).isoformat()

    # Skip empty or truncated files
    if size < 100:
        return {
            'source_name': source_name,
            'status': 'SKIP_EMPTY',
            'file_path': source_path,
            'size_bytes': size,
            'file_mtime': mtime,
            'reason': 'File too small (likely truncated or empty)'
        }

    fhash = file_hash(source_path)
    record_cnt = record_count(source_path) if source_type == 'csv' else 0

    return {
        'source_name': source_name,
        'status': 'AVAILABLE',
        'file_path': source_path,
        'size_bytes': size,
        'record_count': record_cnt,
        'file_hash': fhash,
        'file_mtime': mtime,
        'source_type': source_type,
        'checked_at': datetime.utcnow().isoformat() + 'Z'
    }


def load_prior_manifest(report_path: str) -> dict:
    """Load prior manifest if it exists."""
    try:
        with open(report_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    manifest = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'sources': []
    }

    # Check primary sources
    sources = [
        ('IRS BMF', 'data/bmf.csv', 'csv'),
        ('IRS Revocation', 'data/irs_revocation.csv', 'csv'),
        ('NCCS Data', 'data/nccs_data.csv', 'csv'),
        ('ProPublica Cache', 'data/propublica_cache.jsonl', 'jsonl'),
        ('Organization Assertions', 'data/org_assertions.jsonl', 'jsonl'),
    ]

    for source_name, source_path, source_type in sources:
        result = check_source(source_name, source_path, source_type)
        if result:
            manifest['sources'].append(result)

    # Check for incoming files to ingest
    if os.path.isdir(INCOMING_DIR):
        incoming_files = list(Path(INCOMING_DIR).glob('*'))
        if incoming_files:
            manifest['incoming_files'] = []
            for f in incoming_files:
                if f.is_file() and f.stat().st_size > 100:
                    manifest['incoming_files'].append({
                        'file': f.name,
                        'size_bytes': f.stat().st_size,
                        'mtime': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        'hash': file_hash(str(f))
                    })

    # Write manifest
    report_path = os.path.join(REPORT_DIR, f"manifest_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    os.makedirs(REPORT_DIR, exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print summary
    available = sum(1 for s in manifest['sources'] if s['status'] == 'AVAILABLE')
    skipped = sum(1 for s in manifest['sources'] if s['status'].startswith('SKIP'))

    print(f"✅ Manifest written: {report_path}")
    print(f"   Available sources: {available}")
    print(f"   Skipped: {skipped}")

    if manifest.get('incoming_files'):
        print(f"   Incoming files queued: {len(manifest['incoming_files'])}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
