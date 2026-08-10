#!/usr/bin/env python3
"""
Direct Phase 4 launcher — bypasses shell by invoking subprocess directly.
Useful when bash execution is restricted.
"""
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.home() / "meritgiving"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"
PHASE4_SCRIPT = PROJECT_ROOT / "scripts" / "phase4_semantic_verification.py"
PROGRESS_LOG = Path("/tmp/phase4_progress.log")
PID_FILE = Path("/tmp/phase4.pid")

def log(msg: str):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(PROGRESS_LOG, "a") as f:
        f.write(line + "\n")

def main():
    # Check if already running
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            os.kill(old_pid, 0)  # Signal 0 = check if process exists
            log(f"Phase 4 already running (PID: {old_pid})")
            return 0
        except (ProcessLookupError, ValueError):
            log("Stale PID file; removing")
            PID_FILE.unlink(missing_ok=True)

    # Clear old log
    PROGRESS_LOG.write_text("")
    log("Phase 4 launcher started (direct Python launch)")

    # Check Ollama health
    log("Checking Ollama embedding service...")
    import requests
    try:
        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if resp.status_code == 200 and "mxbai-embed-large" in resp.text:
            log("✓ Ollama embedding server healthy (mxbai-embed-large available)")
        else:
            log("✗ Ollama embedding model not available")
            return 1
    except Exception as e:
        log(f"✗ Ollama health check failed: {e}")
        return 1

    # Parse args
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    # Launch Phase 4 as subprocess
    log(f"Starting Phase 4 (limit={limit}, workers={workers})...")
    try:
        # Use Popen to launch detached process
        proc = subprocess.Popen(
            [str(VENV_PYTHON), str(PHASE4_SCRIPT), "--limit", str(limit), "--workers", str(workers)],
            stdout=open(PROGRESS_LOG, "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True  # Detach from parent
        )

        PID_FILE.write_text(str(proc.pid))
        log(f"Phase 4 launched in background (PID: {proc.pid})")
        log(f"Progress: tail -f {PROGRESS_LOG}")

        return 0
    except Exception as e:
        log(f"✗ Failed to launch Phase 4: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
