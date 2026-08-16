#!/usr/bin/env python3
"""
Phase 4 to Phase 5 Bridge — Validates Phase 4 output and prepares for Phase 5.

Phase 4 output: Orgs with newly-discovered websites (via web_finder_agent).
This bridge filters Phase 4 candidates and outputs a JSON manifest for Phase 5
(mission generation + cause extraction).

Pipeline:
1. Load orgs where website_status='beta' (Phase 4 discovery marker)
2. Filter: deductibility='1', org_status='active', total_revenue > $50K
3. Exclude: orgs with existing missions (already covered)
4. Output JSON: ein, organization_name, current_mission (null), website (if any)
5. Format compatibility check: ensure all Phase 5 required fields present

Usage:
    python3 scripts/phase4_to_phase5_bridge.py --limit 100 --dry-run
    python3 scripts/phase4_to_phase5_bridge.py --output /tmp/phase5_input.json
"""

import sqlite3
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
DEFAULT_OUTPUT = Path("/tmp/phase4_to_phase5_bridge_output.json")

def log(msg: str):
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}", flush=True)

def validate_phase4_output(
    limit: Optional[int] = None,
    dry_run: bool = False,
    output_path: Path = DEFAULT_OUTPUT
) -> dict:
    """
    Validate Phase 4 output and prepare Phase 5 input.

    Returns: {
        'input_count': int,
        'output_count': int,
        'drop_count': int,
        'drop_rate': float,
        'missing_fields': int,
        'output_file': str,
        'sample': list[dict]  # First 5 orgs
    }
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    log("Starting Phase 4 → Phase 5 validation...")

    # === STEP 1: Load Phase 4 output candidates ===
    # Phase 4 markers: websites discovered via web_finder (status='ok' or new discovery)
    # Currently, web_finder marks as status='ok', but Phase 4 would add website_status='beta'
    # For now, use orgs with websites and missing missions (Phase 5 targets)
    query = """
    SELECT
        EIN,
        organization_name,
        NTEE1,
        CITY,
        STATE,
        total_revenue,
        mission,
        website,
        website_status,
        deductibility,
        org_status
    FROM registry_enriched
    WHERE
        deductibility = '1'
        AND org_status = 'active'
        AND total_revenue > 50000
        AND website IS NOT NULL
        AND website_status IN ('ok', 'beta', 'verified')
        AND mission IS NULL
    ORDER BY total_revenue DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    phase4_rows = cursor.fetchall()
    input_count = len(phase4_rows)

    log(f"Loaded {input_count} Phase 4 candidates")

    # === STEP 2: Validate and filter ===
    validated_orgs = []
    drop_count = 0
    missing_fields_count = 0

    for row in phase4_rows:
        org = {
            'ein': row['EIN'],
            'organization_name': row['organization_name'],
            'ntee1': row['NTEE1'],
            'city': row['CITY'],
            'state': row['STATE'],
            'total_revenue': row['total_revenue'],
            'current_mission': row['mission'],  # May be None
            'website': row['website'],  # Should not be None for Phase 4
            'website_status': row['website_status'],
        }

        # Validation rules:
        # 1. All required fields must be present
        validation_errors = []

        if not org['ein']:
            validation_errors.append("missing EIN")
        if not org['organization_name']:
            validation_errors.append("missing organization_name")
        if not org['website']:
            # Phase 4 output must have website
            validation_errors.append("missing website (Phase 4 should have discovered it)")

        # Check field types/ranges
        if org['total_revenue'] is not None and org['total_revenue'] <= 50000:
            validation_errors.append(f"revenue {org['total_revenue']} <= $50K threshold")

        if validation_errors:
            drop_count += 1
            if org.get('current_mission') is None:
                missing_fields_count += 1
            continue

        # 2. Check for missing Phase 5 required fields
        # Phase 5 only needs: ein, organization_name, current_mission
        if org.get('current_mission') is None:
            missing_fields_count += 1

        validated_orgs.append(org)

    output_count = len(validated_orgs)
    drop_rate = drop_count / input_count if input_count > 0 else 0.0

    log(f"Validation complete:")
    log(f"  Input count: {input_count}")
    log(f"  Output count: {output_count}")
    log(f"  Dropped: {drop_count} ({drop_rate*100:.1f}%)")
    log(f"  Orgs missing mission (Phase 5 target): {missing_fields_count}")

    # === STEP 3: Output JSON ===
    output_json = {
        'metadata': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'phase': '4→5_bridge',
            'input_count': input_count,
            'output_count': output_count,
            'drop_count': drop_count,
            'drop_rate': round(drop_rate, 4),
            'missing_mission_count': missing_fields_count,
            'db_path': str(DB_PATH),
        },
        'orgs': validated_orgs
    }

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_json, f, indent=2)
        log(f"Output written to {output_path}")
    else:
        log("Dry-run mode: no output file written")

    # === STEP 4: Format compatibility check ===
    # Verify Phase 5 required schema
    phase5_required_fields = {'ein', 'organization_name', 'current_mission'}
    sample_missing_fields = 0

    if validated_orgs:
        for org in validated_orgs[:5]:
            for field in phase5_required_fields:
                if field not in org or org[field] is None:
                    sample_missing_fields += 1

    log(f"Phase 5 schema compatibility: {phase5_required_fields}")
    log(f"  Sample check (first 5): {sample_missing_fields} missing field instances")

    # === STEP 5: Summary ===
    result = {
        'input_count': input_count,
        'output_count': output_count,
        'drop_count': drop_count,
        'drop_rate': round(drop_rate, 4),
        'missing_fields': sample_missing_fields,
        'output_file': str(output_path),
        'sample': validated_orgs[:5] if validated_orgs else []
    }

    conn.close()
    return result

def main():
    parser = argparse.ArgumentParser(
        description="Phase 4 → Phase 5 Bridge: Validate and prepare for mission generation"
    )
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of Phase 4 candidates (default: all)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Validate only; do not write output file')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT,
                        help=f'Output JSON path (default: {DEFAULT_OUTPUT})')

    args = parser.parse_args()

    result = validate_phase4_output(
        limit=args.limit,
        dry_run=args.dry_run,
        output_path=args.output
    )

    print("\n" + "="*60)
    print("PHASE 4 → PHASE 5 BRIDGE VALIDATION REPORT")
    print("="*60)
    print(f"Input count:          {result['input_count']:,}")
    print(f"Output count:         {result['output_count']:,}")
    print(f"Dropped:              {result['drop_count']:,} ({result['drop_rate']*100:.2f}%)")
    print(f"Missing mission:      {result['missing_fields']} (sample)")
    print(f"Output file:          {result['output_file']}")
    print("="*60)

    if result['sample']:
        print("\nFirst 5 validated orgs:")
        for i, org in enumerate(result['sample'], 1):
            print(f"\n  [{i}] {org['organization_name']} (EIN: {org['ein']})")
            print(f"      Revenue: ${org['total_revenue']:,.0f if org['total_revenue'] else 'N/A'}")
            print(f"      Mission: {org['current_mission'][:60] if org['current_mission'] else '(null - Phase 5 target)'}")
            print(f"      Website: {org['website']}")

if __name__ == '__main__':
    main()
