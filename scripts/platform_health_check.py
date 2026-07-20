#!/usr/bin/env python3
"""
Platform Health Dashboard — Daily audit of Daanaa infrastructure.

Checks:
1. Droplet uptime & response times
2. Search performance (FTS + semantic)
3. Link confidence distribution
4. Enrichment backlog size
5. Inference server load (llama.cpp)

Usage:
  python3 scripts/platform_health_check.py
  (Runs nightly from overnight_pipeline.py)
"""

import sqlite3
import requests
import time
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
API_BASE = "http://localhost:5000"
INFERENCE_BASE_EMBED = "http://127.0.0.1:11436"
INFERENCE_BASE_CHAT = "http://127.0.0.1:11437"

def log(msg):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{t}] {msg}')

def check_droplet_health():
    """Check if API is responding."""
    try:
        start = time.time()
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        elapsed_ms = (time.time() - start) * 1000
        if resp.status_code == 200:
            log(f'✅ Droplet API healthy ({elapsed_ms:.0f}ms)')
            return True
        else:
            log(f'⚠️  Droplet API returned {resp.status_code}')
            return False
    except Exception as e:
        log(f'❌ Droplet unreachable: {e}')
        return False

def check_api_performance():
    """Sample API response times."""
    try:
        queries = [
            ("education", "cause query"),
            ("San Francisco", "location"),
            ("healthcare", "cause"),
        ]
        times = []
        for q, desc in queries:
            start = time.time()
            resp = requests.get(f"{API_BASE}/api/organizations?q={q}&per_page=5", timeout=10)
            elapsed_ms = (time.time() - start) * 1000
            if resp.status_code == 200:
                times.append(elapsed_ms)
            else:
                log(f'  ⚠️  Query "{q}" returned {resp.status_code}')
        if times:
            avg = sum(times) / len(times)
            max_t = max(times)
            log(f'✅ API performance: avg={avg:.0f}ms max={max_t:.0f}ms (n={len(times)})')
            return avg < 5000  # Healthy if avg < 5s
    except Exception as e:
        log(f'⚠️  API performance check failed: {str(e)[:100]}')
        return False

def check_link_confidence():
    """Audit link confidence distribution."""
    try:
        conn = sqlite3.connect(str(DB))
        c = conn.cursor()

        # Sample donation_confidence and website_status
        c.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN donate_confidence >= 90 THEN 1 ELSE 0 END) as high_conf,
                   SUM(CASE WHEN donate_confidence >= 75 THEN 1 ELSE 0 END) as med_conf,
                   SUM(CASE WHEN donate_confidence IS NULL THEN 1 ELSE 0 END) as no_conf
            FROM registry_enriched
            WHERE donate_url IS NOT NULL
        """)
        row = c.fetchone()
        if row:
            total, high, med, null_conf = row
            high = high or 0
            med = med or 0
            null_conf = null_conf or 0
            if total > 0:
                pct_high = (high / total * 100) if total > 0 else 0
                log(f'✅ Donation links: {total} total, {high} high-confidence ({pct_high:.0f}%)')

        # Website status distribution
        c.execute("""
            SELECT website_status, COUNT(*) as cnt
            FROM registry_enriched
            WHERE website IS NOT NULL
            GROUP BY website_status
        """)
        statuses = dict(c.fetchall() or [])
        if statuses:
            status_str = ', '.join(f'{k}={v}' for k, v in sorted(statuses.items()))
            log(f'✅ Websites: {status_str}')
        else:
            log('ℹ️  Websites: no status breakdown')

        conn.close()
        return True
    except Exception as e:
        log(f'⚠️  Link confidence check failed: {str(e)[:100]}')
        return False

def check_enrichment_backlog():
    """Check pending enrichment work."""
    try:
        conn = sqlite3.connect(str(DB))
        c = conn.cursor()

        # Count orgs missing key enrichments
        c.execute("""
            SELECT
                SUM(CASE WHEN mission IS NULL THEN 1 ELSE 0 END) as no_mission,
                SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) as no_website,
                SUM(CASE WHEN donate_url IS NULL THEN 1 ELSE 0 END) as no_donate
            FROM registry_enriched
            WHERE org_status = 'active'
        """)
        row = c.fetchone()
        if row:
            no_mission, no_website, no_donate = row
            log(f'📊 Enrichment gaps: {no_mission or 0} missing missions, '
                f'{no_website or 0} missing websites, {no_donate or 0} missing donate links')

        conn.close()
        return True
    except Exception as e:
        log(f'⚠️  Enrichment backlog check failed: {str(e)[:100]}')
        return False

def check_inference_servers():
    """Check if embedding/chat inference servers are responsive."""
    healthy = True

    # Check embedding server (11436)
    try:
        resp = requests.post(
            f"{INFERENCE_BASE_EMBED}/api/embeddings",
            json={"input": "test", "model": "mxbai-embed-large"},
            timeout=5
        )
        if resp.status_code == 200:
            log('✅ Embedding server (11436) responsive')
        else:
            log(f'⚠️  Embedding server returned {resp.status_code}')
            healthy = False
    except Exception as e:
        log(f'❌ Embedding server (11436) unreachable: {str(e)[:50]}')
        healthy = False

    # Check chat server (11437)
    try:
        resp = requests.post(
            f"{INFERENCE_BASE_CHAT}/api/chat/completions",
            json={"model": "qwen", "messages": [{"role": "user", "content": "hi"}]},
            timeout=5
        )
        if resp.status_code == 200:
            log('✅ Chat server (11437) responsive')
        else:
            log(f'⚠️  Chat server returned {resp.status_code}')
            healthy = False
    except Exception as e:
        log(f'❌ Chat server (11437) unreachable: {str(e)[:50]}')
        healthy = False

    return healthy

def main():
    log('=' * 60)
    log('Platform Health Check Started')
    log('=' * 60)

    checks = {
        'droplet': check_droplet_health(),
        'api_perf': check_api_performance(),
        'links': check_link_confidence(),
        'enrichment': check_enrichment_backlog(),
        'inference': check_inference_servers(),
    }

    log('=' * 60)
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    log(f'Health check: {passed}/{total} checks passed')

    if passed == total:
        log('✅ All systems nominal')
    elif passed >= total * 0.75:
        log('⚠️  Minor issues detected (see above)')
    else:
        log('🚨 CRITICAL: Multiple systems down (escalate)')

    log('=' * 60)

if __name__ == '__main__':
    main()
