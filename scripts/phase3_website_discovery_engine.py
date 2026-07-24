#!/usr/bin/env python3
"""
Phase 3: Nonprofit Website Discovery Engine
8 parallel workers find missing/broken nonprofit websites
Audit logs all attempts (no PII, event-type based)
"""

import sqlite3
import sys
import time
import random
import requests
import threading
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import json

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"

# Configuration
WORKERS = 8
BATCH_SIZE = 50  # Orgs per worker
TIMEOUT = 10  # HTTP timeout per request
RETRY_COUNT = 3

# Discovery strategies (in priority order)
DISCOVERY_STRATEGIES = [
    "google_search",
    "charity_navigator",
    "guidestar_lookup",
    "state_registry",
    "event_sites",
]

# Tracking
discovery_stats = {
    'total_queried': 0,
    'websites_found': 0,
    'websites_failed': 0,
    'events_found': 0,
    'errors_by_type': defaultdict(int),
    'strategies_successful': defaultdict(int),
}
stats_lock = threading.Lock()


def get_db():
    """Thread-safe database connection."""
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def log_audit(event_type, org_ein, success, error_code=None, details=None):
    """Log discovery event to audit_log (no PII)."""
    try:
        db = get_db()
        db.execute("""
            INSERT INTO audit_log (
                event_type, timestamp, org_ein, user_auth, user_role,
                success, error_code, ip_address_anonymized, user_agent_category
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_type,
            datetime.utcnow().isoformat(),
            org_ein,
            'discovery-bot',
            'admin',
            success,
            error_code,
            '0.0.0.0',  # Batch process, no client IP
            'batch',
        ))
        db.commit()
        db.close()
    except Exception as e:
        print(f"[audit_log] Error logging {event_type} for {org_ein}: {e}", flush=True)


def get_missing_websites():
    """Get orgs with missing/broken websites (priority: high impact first)."""
    db = get_db()
    rows = db.execute("""
        SELECT ein, name, state, ntee1
        FROM registry_enriched
        WHERE (website IS NULL OR website_status IN ('broken', 'timeout', '404'))
        AND ein NOT NULL
        ORDER BY ntee1_percentile DESC, ein
        LIMIT ?
    """, (WORKERS * BATCH_SIZE * 2,)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def discover_website_google(org):
    """Try to find org website via Google Search."""
    try:
        query = f'{org["name"]} {org["state"]} nonprofit website'
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; discovery-bot)'}

        # Note: In production, would use Google Custom Search API or Selenium
        # For MVP, attempt direct URL guess + fallback
        base_url = f"http://{org['name'].lower().replace(' ', '')}.org"

        resp = requests.head(base_url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code < 400:
            return {'url': base_url, 'status': 'found', 'strategy': 'direct_guess'}
    except requests.Timeout:
        return {'status': 'timeout', 'error': 'REQUEST_TIMEOUT'}
    except requests.RequestException as e:
        return {'status': 'error', 'error': str(type(e).__name__)}

    return {'status': 'not_found', 'error': 'NO_MATCH'}


def discover_website_charity_navigator(org):
    """Try to find org via Charity Navigator."""
    try:
        # Charity Navigator has a public API (rate limited, free tier available)
        query_url = f"https://api.charitynavigator.org/v2/Organizations?search={org['ein']}"
        resp = requests.get(query_url, timeout=TIMEOUT)

        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                org_data = data[0]
                if org_data.get('websiteURL'):
                    return {'url': org_data['websiteURL'], 'status': 'found', 'strategy': 'charity_navigator'}
    except Exception as e:
        pass  # Fallback to next strategy

    return {'status': 'not_found', 'error': 'NOT_IN_CHARITY_NAVIGATOR'}


def discover_website_state_registry(org):
    """Lookup in state nonprofit registry (if available)."""
    # This would connect to each state's registry
    # For MVP, note that this requires state-specific APIs
    # Example: California uses ICNP database
    return {'status': 'not_attempted', 'error': 'STATE_LOOKUP_UNAVAILABLE'}


def attempt_discovery(org):
    """Try all discovery strategies for an org."""
    org_ein = org['ein']

    with stats_lock:
        discovery_stats['total_queried'] += 1

    # Try strategies in order
    for strategy in DISCOVERY_STRATEGIES[:2]:  # Limit to fast strategies for MVP
        if strategy == 'google_search':
            result = discover_website_google(org)
        elif strategy == 'charity_navigator':
            result = discover_website_charity_navigator(org)
        else:
            continue

        if result.get('status') == 'found':
            # Success!
            url = result['url']
            strategy_used = result['strategy']

            # Update database
            db = get_db()
            db.execute("""
                UPDATE registry_enriched
                SET website = ?, website_status = 'valid', website_discovery_strategy = ?
                WHERE ein = ?
            """, (url, strategy_used, org_ein))
            db.commit()
            db.close()

            # Log success
            log_audit('website_discovered', org_ein, True)

            with stats_lock:
                discovery_stats['websites_found'] += 1
                discovery_stats['strategies_successful'][strategy_used] += 1

            print(f"[FOUND] {org_ein}: {url} ({strategy_used})", flush=True)
            return result

        # Track failures for learning
        error_code = result.get('error', 'UNKNOWN')
        with stats_lock:
            discovery_stats['errors_by_type'][error_code] += 1

    # All strategies exhausted
    log_audit('website_discovery_failed', org_ein, False, 'NO_MATCH_FOUND')
    with stats_lock:
        discovery_stats['websites_failed'] += 1

    return {'status': 'failed', 'org_ein': org_ein}


def worker_thread(worker_id, orgs_slice):
    """Worker thread: discover websites for assigned orgs."""
    print(f"[WORKER {worker_id}] Started (processing {len(orgs_slice)} orgs)", flush=True)

    for i, org in enumerate(orgs_slice):
        try:
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 2))

            # Attempt discovery
            result = attempt_discovery(org)

            if (i + 1) % 10 == 0:
                print(f"[WORKER {worker_id}] Progress: {i+1}/{len(orgs_slice)}", flush=True)

        except Exception as e:
            print(f"[WORKER {worker_id}] ERROR for {org['ein']}: {e}", flush=True)
            log_audit('website_discovery_error', org['ein'], False, 'EXCEPTION')

    print(f"[WORKER {worker_id}] Complete", flush=True)


def run_discovery_engine():
    """Launch 8-worker discovery engine."""
    print("════════════════════════════════════════════════════════════════")
    print("PHASE 3: WEBSITE DISCOVERY ENGINE — LAUNCHING 8 WORKERS")
    print("════════════════════════════════════════════════════════════════")
    print()

    # Get orgs to process
    print(f"[DISCOVERY] Querying database for missing websites...")
    orgs = get_missing_websites()
    print(f"[DISCOVERY] Found {len(orgs)} orgs needing websites")
    print()

    if not orgs:
        print("✓ No websites to discover (all current)")
        return

    # Split into worker batches
    worker_batches = []
    batch_size = max(1, len(orgs) // WORKERS)
    for i in range(WORKERS):
        start = i * batch_size
        end = start + batch_size if i < WORKERS - 1 else len(orgs)
        worker_batches.append(orgs[start:end])

    # Launch workers
    print(f"[DISCOVERY] Launching {WORKERS} worker threads...")
    threads = []
    start_time = time.time()

    for worker_id in range(WORKERS):
        t = threading.Thread(
            target=worker_thread,
            args=(worker_id, worker_batches[worker_id]),
            daemon=False
        )
        threads.append(t)
        t.start()

    # Wait for all workers
    print(f"[DISCOVERY] Waiting for workers to complete...")
    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    # Print summary
    print()
    print("════════════════════════════════════════════════════════════════")
    print("PHASE 3: DISCOVERY ENGINE COMPLETE")
    print("════════════════════════════════════════════════════════════════")
    print()
    print(f"Results:")
    print(f"  Total queried:        {discovery_stats['total_queried']}")
    print(f"  Websites found:       {discovery_stats['websites_found']}")
    print(f"  Websites failed:      {discovery_stats['websites_failed']}")
    print(f"  Success rate:         {100 * discovery_stats['websites_found'] / max(1, discovery_stats['total_queried']):.1f}%")
    print()
    print(f"  Successful strategies:")
    for strategy, count in discovery_stats['strategies_successful'].items():
        print(f"    • {strategy}: {count}")
    print()
    print(f"  Error types (top 5):")
    sorted_errors = sorted(discovery_stats['errors_by_type'].items(), key=lambda x: x[1], reverse=True)
    for error_type, count in sorted_errors[:5]:
        print(f"    • {error_type}: {count}")
    print()
    print(f"  Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f}min)")
    print(f"  Rate: {discovery_stats['total_queried'] / max(1, elapsed):.1f} orgs/sec")
    print()

    # Log summary to audit trail
    log_audit('website_discovery_batch_complete', 'BATCH', True,
              error_code='DISCOVERY_STATS',
              details=json.dumps({
                  'total': discovery_stats['total_queried'],
                  'found': discovery_stats['websites_found'],
                  'success_rate': discovery_stats['websites_found'] / max(1, discovery_stats['total_queried']),
                  'elapsed_sec': elapsed,
              }))

    print("✓ Audit log updated with discovery results")
    print()
    return discovery_stats


if __name__ == "__main__":
    try:
        stats = run_discovery_engine()
        sys.exit(0)
    except Exception as e:
        print(f"[FATAL] Discovery engine crashed: {e}", flush=True)
        sys.exit(1)
