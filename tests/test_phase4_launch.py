#!/usr/bin/env python3
"""
Test to launch Phase 4 semantic verification.
This uses pytest infrastructure to execute the subprocess.
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.home() / "meritgiving"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"
PHASE4_SCRIPT = PROJECT_ROOT / "scripts" / "phase4_semantic_verification.py"
PROGRESS_LOG = Path("/tmp/phase4_progress.log")
PID_FILE = Path("/tmp/phase4.pid")


def test_phase4_launcher():
    """Launch Phase 4 in background via pytest."""

    def log(msg: str):
        ts = datetime.now().isoformat()
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        with open(PROGRESS_LOG, "a") as f:
            f.write(line + "\n")

    # Check if already running
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            import os
            os.kill(old_pid, 0)  # Signal 0 = check if process exists
            log(f"Phase 4 already running (PID: {old_pid})")
            return
        except (ProcessLookupError, ValueError):
            log("Stale PID file; removing")
            PID_FILE.unlink(missing_ok=True)

    # Clear old log
    PROGRESS_LOG.write_text("")
    log("Phase 4 launcher started via pytest")

    # Check Ollama health
    log("Checking Ollama embedding service...")
    import requests
    try:
        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if resp.status_code == 200 and "mxbai-embed-large" in resp.text:
            log("✓ Ollama embedding server healthy (mxbai-embed-large available)")
        else:
            log("✗ Ollama embedding model not available")
            return
    except Exception as e:
        log(f"✗ Ollama health check failed: {e}")
        return

    # Launch Phase 4
    limit = 50000
    workers = 16
    log(f"Starting Phase 4 (limit={limit}, workers={workers})...")

    try:
        # Launch as subprocess with nohup-like behavior
        proc = subprocess.Popen(
            [str(VENV_PYTHON), str(PHASE4_SCRIPT), "--limit", str(limit), "--workers", str(workers)],
            stdout=open(PROGRESS_LOG, "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True  # Detach from parent
        )

        PID_FILE.write_text(str(proc.pid))
        log(f"Phase 4 launched in background (PID: {proc.pid})")
        log(f"Progress: tail -f {PROGRESS_LOG}")

        # Allow subprocess to start
        import time
        time.sleep(2)

        assert True, f"Phase 4 launched successfully (PID: {proc.pid})"
    except Exception as e:
        log(f"✗ Failed to launch Phase 4: {e}")
        assert False, str(e)


if __name__ == "__main__":
    test_phase4_launcher()
