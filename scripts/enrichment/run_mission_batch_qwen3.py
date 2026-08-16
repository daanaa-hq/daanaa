#!/usr/bin/env python3
"""
Wrapper to run mission generation on ~21,000 orgs (excluding thin-content)
using Qwen3 30B A3B via the model router.

Temporarily overrides generate_missions.py's hardcoded MODEL and GEN_URL,
filters out thin-content orgs, and logs progress.
"""
import sys
import subprocess
import sqlite3
import time
import re
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VENV = REPO_ROOT / "venv" / "bin" / "activate"
SCRIPT = REPO_ROOT / "scripts" / "generate_missions.py"
LOG_FILE = REPO_ROOT / "logs" / f"mission_batch_qwen3_{int(time.time())}.log"

def log(msg):
    """Log to file and stdout."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def identify_thin_content_orgs():
    """Return set of EINs that have thin (<400 char) cached content."""
    db = sqlite3.connect(REPO_ROOT / "data" / "merit_registry.db")

    thin = set()
    q = """
        SELECT DISTINCT ein FROM page_cache WHERE html_gz IS NOT NULL
    """
    for (ein,) in db.execute(q):
        row = db.execute(
            "SELECT html_gz FROM page_cache WHERE ein=? AND html_gz IS NOT NULL ORDER BY fetched_at DESC LIMIT 1",
            (ein,)
        ).fetchone()
        if row and row[0]:
            try:
                html = zlib.decompress(row[0]).decode("utf-8", errors="replace")
                text_only = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
                text_only = re.sub(r'<[^>]+>', ' ', text_only)
                text_only = re.sub(r'\s+', ' ', text_only).strip()
                if len(text_only) < 400:
                    thin.add(ein)
            except:
                thin.add(ein)  # err on side of caution

    db.close()
    return thin

def count_target_orgs():
    """Count orgs that will be processed (excluding thin-content)."""
    thin = identify_thin_content_orgs()
    db = sqlite3.connect(REPO_ROOT / "data" / "merit_registry.db")

    q = """
        SELECT COUNT(*) as cnt
        FROM registry_enriched re
        WHERE (re.mission_source IS NULL OR re.mission_source IN ('ai_generated', 'ai_ntee'))
          AND re.website IS NOT NULL AND re.website != ''
          AND re.EIN IN (SELECT DISTINCT ein FROM page_cache WHERE html_gz IS NOT NULL)
          AND re.source NOT IN ('IRS_BMF', 'bmf_stub')
          AND re.merit_score IS NOT NULL
    """
    total = db.execute(q).fetchone()[0]
    db.close()

    return total, len(thin)

if __name__ == "__main__":
    log("="*70)
    log("Mission generation batch: Qwen3 30B A3B (21K orgs, skip thin-content)")
    log("="*70)

    # Identify thin-content orgs
    log("Scanning for thin-content orgs...")
    start = time.time()
    thin_orgs = identify_thin_content_orgs()
    elapsed = time.time() - start
    log(f"Identified {len(thin_orgs)} thin-content orgs in {elapsed:.1f}s")

    # Count target batch
    total, thin_count = count_target_orgs()
    target = total - thin_count
    log(f"Target batch: {target} orgs (total {total} - thin {thin_count})")

    # Estimate time
    tokens_per_org = 400
    total_tokens = target * tokens_per_org
    qwen3_speed = 178  # tok/s from benchmark
    estimated_hours = total_tokens / (qwen3_speed * 3600)
    log(f"Estimated time: ~{estimated_hours:.1f} hours at {qwen3_speed} tok/s")

    # Run generate_missions.py with Qwen3 config
    # The script already has --regen-generic-with-site logic; we just need to
    # point it to port 11440 (Qwen3 30B A3B)
    log("Starting mission generation...")
    log(f"Log: {LOG_FILE}")

    env_override = {
        # Point generate_missions.py to the router-managed Qwen3 server on port 11440
        "GEN_URL": "http://127.0.0.1:11440/v1/chat/completions",
        "GEN_MODEL": "qwen3-30b-a3b",
    }

    # Build command
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--regen-generic-with-site",
        "--workers", "1",
    ]

    log(f"Command: {' '.join(cmd)}")
    log(f"Model: Qwen3 30B A3B (port 11440)")

    # Run (let it stream to our log)
    result = subprocess.run(cmd, cwd=REPO_ROOT)

    if result.returncode == 0:
        log("✓ Mission generation batch completed successfully")
    else:
        log(f"✗ Mission generation failed with code {result.returncode}")

    log("="*70)
    sys.exit(result.returncode)
