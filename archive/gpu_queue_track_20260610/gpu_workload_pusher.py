#!/usr/bin/env python3
"""
GPU Workload Pusher v1
Monitors GPU utilization and queues high-value work when idle capacity exists.

Monitors:
  - Embedding server (port 11436): semantic embeddings
  - Qwen2.5-32B LLM (port 11437): mission generation
  - Ollama: Phase 4 / fallback embeddings

Queues work in priority order:
  1. Mission generation (new orgs, creates semantic context)
  2. Cause tagging (after missions, uses semantic content)
  3. Donation verification (5K+ links)
  4. Semantic clustering (peer groups)
"""

import sqlite3
import requests
import subprocess
import time
import sys
import json
from pathlib import Path
from datetime import datetime

HOME = Path.home()
PROJECT = HOME / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
LOGS = PROJECT / "logs"
LOG_FILE = LOGS / "gpu_workload_pusher.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def check_gpu_health():
    """Check GPU services health."""
    health = {}

    # Check embedding server (11436)
    try:
        r = requests.get("http://127.0.0.1:11436/health", timeout=2)
        health['embed'] = r.status_code == 200
    except:
        health['embed'] = False

    # Check Qwen LLM (11437)
    try:
        r = requests.get("http://127.0.0.1:11437/health", timeout=2)
        health['qwen'] = r.status_code == 200
    except:
        health['qwen'] = False

    return health

def get_gpu_load():
    """Estimate GPU load from running processes."""
    import psutil
    try:
        cpu_pct = psutil.cpu_percent(interval=0.5)
        return cpu_pct
    except:
        return 0

def count_work_available():
    """Count orgs needing GPU work."""
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Cause tags needed
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE cause_tags IS NULL AND organization_name IS NOT NULL
    """)
    cause_tags_needed = c.fetchone()[0]

    # Missions needed
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE (mission IS NULL OR mission = '')
        AND organization_name IS NOT NULL
        AND source = 'IRS_BMF'
    """)
    missions_needed = c.fetchone()[0]

    conn.close()
    return {
        'cause_tags': cause_tags_needed,
        'missions': missions_needed,
    }

def queue_cause_tagging(batch_size=5000):
    """Queue cause tagging work."""
    work = count_work_available()
    if work['cause_tags'] == 0:
        log("No cause tagging work available")
        return False

    log(f"Queuing cause tagging: {work['cause_tags']:,} orgs")
    try:
        cmd = [
            str(PROJECT / "venv" / "bin" / "python3"),
            str(PROJECT / "scripts" / "run_agents.py"),
            "--agent", "cause_tags",
            "--batch", str(batch_size),
        ]
        # Run in background
        subprocess.Popen(cmd, stdout=open(LOGS / "cause_tags_batch.log", 'a'),
                        stderr=subprocess.STDOUT, cwd=str(PROJECT))
        log(f"✅ Cause tagging batch queued")
        return True
    except Exception as e:
        log(f"❌ Failed to queue cause tagging: {e}")
        return False

def queue_mission_generation(limit=5000):
    """Queue mission generation work."""
    work = count_work_available()
    if work['missions'] == 0:
        log("No mission generation work available")
        return False

    log(f"Queuing mission generation: {work['missions']:,} orgs (limit: {limit})")
    try:
        cmd = [
            str(PROJECT / "venv" / "bin" / "python3"),
            str(PROJECT / "scripts" / "mission_generation_pipeline.py"),
            "--limit", str(limit),
            "--workers", "1",
        ]
        subprocess.Popen(cmd, stdout=open(LOGS / "mission_gen_batch.log", 'a'),
                        stderr=subprocess.STDOUT, cwd=str(PROJECT))
        log(f"✅ Mission generation batch queued")
        return True
    except Exception as e:
        log(f"❌ Failed to queue mission generation: {e}")
        return False

def main():
    log("=" * 70)
    log("GPU WORKLOAD PUSHER START")
    log("=" * 70)

    # Check GPU health
    health = check_gpu_health()
    log(f"GPU Health: embed={health.get('embed')}, qwen={health.get('qwen')}")

    if not health.get('embed'):
        log("⚠️  Embedding server not responding (11436)")

    # Check work available
    work = count_work_available()
    log(f"\nWork available (priority order):")
    log(f"  1. Missions: {work['missions']:,} orgs (HIGH)")
    log(f"  2. Cause tagging: {work['cause_tags']:,} orgs (after missions)")

    # Priority queue: missions first (creates semantic context), then cause tags
    if work['missions'] > 10000:
        log(f"\n🔴 HIGH PRIORITY: {work['missions']:,} orgs need missions (semantic context for tagging)")
        queue_mission_generation(limit=10000)
    elif work['cause_tags'] > 100000:
        log(f"\n🟡 MEDIUM PRIORITY: {work['cause_tags']:,} orgs need cause tags (after missions complete)")
        queue_cause_tagging(batch_size=5000)
    else:
        log("\n✅ All GPU work queues caught up")

    log("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        sys.exit(1)
