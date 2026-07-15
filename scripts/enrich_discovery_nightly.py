#!/usr/bin/env python3
"""
Integration module for website discovery enrichment in the nightly pipeline.

Called by overnight_pipeline.py to run active website discovery on organizations
with missing donation links and volunteer pages.
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

LOG = Path.home() / 'meritgiving' / 'logs' / 'overnight.log'


def log(msg):
    """Log to both stdout and overnight.log."""
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    s = '[' + t + '] ' + msg
    print(s)
    sys.stdout.flush()
    try:
        with open(LOG, 'a') as f:
            f.write(s + '\n')
    except:
        pass


def run_discovery_enrichment(batch_size=100, max_orgs=10000):
    """
    Run website discovery enrichment as part of the nightly pipeline.

    Args:
        batch_size: Organizations to process per batch (default 100)
        max_orgs: Total organizations to process (default 10,000, adjust based on time budget)

    Returns:
        (total_processed, donation_links_found, volunteer_links_found, errors)
    """
    log('Starting website discovery enrichment...')

    script_path = Path.home() / 'meritgiving' / 'scripts' / 'enrich_discovery_batch.py'

    if not script_path.exists():
        log('⚠️  Discovery enrichment script not found, skipping')
        return 0, 0, 0, 0

    try:
        result = subprocess.run(
            ['python3', str(script_path), str(batch_size), str(max_orgs)],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            cwd=str(Path.home() / 'meritgiving'),
        )

        # Parse stats from output
        stats = {'total_processed': 0, 'donation_links_found': 0, 'volunteer_links_found': 0, 'errors': 0}

        # Look for JSON stats in output
        lines = (result.stdout or '').strip().splitlines()
        for i, line in enumerate(lines):
            if 'FINAL RESULTS' in line:
                # Next non-empty line should be the JSON
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith('{'):
                        try:
                            stats = json.loads('\n'.join(lines[j:]))
                            break
                        except:
                            pass
                break

        # Log results
        log(f"Discovery enrichment: {stats['total_processed']} processed, " +
            f"{stats['donation_links_found']} donation links, " +
            f"{stats['volunteer_links_found']} volunteer links, " +
            f"{stats['errors']} errors")

        if result.returncode != 0:
            log(f'⚠️  Discovery enrichment returned non-zero exit code: {result.returncode}')

        return (
            stats.get('total_processed', 0),
            stats.get('donation_links_found', 0),
            stats.get('volunteer_links_found', 0),
            stats.get('errors', 0),
        )

    except subprocess.TimeoutExpired:
        log('🚨 Discovery enrichment timed out (1 hour limit)')
        return 0, 0, 0, 1
    except Exception as e:
        log(f'⚠️  Discovery enrichment error (non-fatal): {str(e)[:200]}')
        return 0, 0, 0, 1


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run website discovery enrichment')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    parser.add_argument('--max-orgs', type=int, default=10000, help='Max orgs to process')
    args = parser.parse_args()

    processed, donations, volunteers, errors = run_discovery_enrichment(
        batch_size=args.batch_size,
        max_orgs=args.max_orgs
    )

    print(f'\nSummary:')
    print(f'  Processed: {processed}')
    print(f'  Donations: {donations}')
    print(f'  Volunteers: {volunteers}')
    print(f'  Errors: {errors}')
