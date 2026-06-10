#!/usr/bin/env python3
"""
Nightly web discovery pipeline orchestrator.
Runs Phase 2-4 in sequence: HTTP verification → Donation extraction → GPU semantic verification.
"""

import subprocess
import time
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
SCRIPT_DIR = Path.home() / "meritgiving/scripts"
LOG_DIR = Path.home() / "meritgiving/logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"web_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(msg: str):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

def get_counts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    websites = c.execute("SELECT COUNT(*) FROM registry_enriched WHERE website_status = 'beta'").fetchone()[0]
    donations = c.execute("SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL AND donate_url_status = 'beta'").fetchone()[0]
    conn.close()
    return websites, donations

def run_phase(name: str, script: str, timeout: int, *args):
    """Run a pipeline phase with timeout."""
    log(f"🚀 Starting {name}...")
    start_time = time.time()

    try:
        cmd = [
            'timeout', str(timeout),
            'python3', str(SCRIPT_DIR / script),
            *args
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = int(time.time() - start_time)

        if result.returncode == 124:
            log(f"⏱️  {name} timed out after {elapsed}s (expected)")
        elif result.returncode == 0:
            log(f"✅ {name} completed in {elapsed}s")
        else:
            log(f"❌ {name} failed with code {result.returncode}")
            if result.stderr:
                log(f"   Error: {result.stderr[:200]}")

        return result.returncode in [0, 124]  # Success if completed or timed out as expected
    except Exception as e:
        log(f"❌ {name} error: {e}")
        return False

def main():
    log("=" * 70)
    log("WEB DISCOVERY PIPELINE ORCHESTRATOR")
    log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)

    # Phase 2: HTTP verification (20 min timeout)
    websites_before, _ = get_counts()
    if run_phase("Phase 2: HTTP Verification", "verify_web_candidates.py", 1200, "--limit", "100000", "--workers", "30"):
        websites_after, _ = get_counts()
        new_websites = websites_after - websites_before
        log(f"📊 Phase 2 result: +{new_websites} websites ({websites_after} total)")

    # Phase 3: Donation extraction (10 min timeout)
    websites, donations_before = get_counts()
    if run_phase("Phase 3: Donation Link Extraction", "donation_link_extractor.py", 600):
        _, donations_after = get_counts()
        new_donations = donations_after - donations_before
        log(f"🔗 Phase 3 result: +{new_donations} donation links ({donations_after} total)")

    # Phase 4: GPU semantic verification (waits for embedding server to be ready)
    # The run_phase4.sh wrapper ensures the embedding server is healthy before starting.
    log("🔍 Phase 4: GPU Semantic Verification (waiting for embed server...)")
    try:
        result = subprocess.run(
            ['bash', str(SCRIPT_DIR / 'run_phase4.sh'), '300'],
            capture_output=True,
            text=True,
            timeout=14400  # 4 hours max
        )
        if result.returncode == 0:
            log("✅ Phase 4 GPU verification completed")
        else:
            log(f"⚠️  Phase 4 did not complete (embed server unavailable or timeout)")
            if "Embed server failed to start" in result.stdout:
                log("   Embedding server failed to start within timeout")
    except subprocess.TimeoutExpired:
        log("⏱️  Phase 4 timed out after 4 hours (may still be running)")
    except Exception as e:
        log(f"⚠️  Phase 4 error: {e}")

    websites_final, donations_final = get_counts()
    log("")
    log("=" * 70)
    log("PIPELINE COMPLETE")
    log(f"Final state: {websites_final} websites, {donations_final} donation links")
    log(f"Logged to: {LOG_FILE}")
    log("=" * 70)

if __name__ == '__main__':
    main()
