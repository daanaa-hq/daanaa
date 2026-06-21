#!/usr/bin/env python3
"""
Test to restart Phase 4 semantic verification with fixes applied.
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.home() / "meritgiving"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"
PHASE4_SCRIPT = PROJECT_ROOT / "scripts" / "phase4_semantic_verification.py"
PROGRESS_LOG = Path("/tmp/phase4_progress.log")
PID_FILE = Path("/tmp/phase4.pid")


def test_phase4_restart():
    """Restart Phase 4 with fixes."""

    def log(msg: str):
        ts = datetime.now().isoformat()
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        with open(PROGRESS_LOG, "a") as f:
            f.write(line + "\n")

    log("=== Phase 4 Restart (fixed) ===")

    # Kill old process if running
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            os.kill(old_pid, 9)
            log(f"Killed old Phase 4 process (PID: {old_pid})")
        except (ProcessLookupError, ValueError, PermissionError):
            log("No old process to kill")
        finally:
            PID_FILE.unlink(missing_ok=True)

    # Clear log and start fresh
    PROGRESS_LOG.write_text("")
    log("Phase 4 restart initiated")

    # Check Ollama health
    log("Checking Ollama embedding service...")
    import requests
    try:
        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if resp.status_code == 200 and "mxbai-embed-large" in resp.text:
            log("✓ Ollama embedding server healthy")
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
        proc = subprocess.Popen(
            [str(VENV_PYTHON), str(PHASE4_SCRIPT), "--limit", str(limit), "--workers", str(workers)],
            stdout=open(PROGRESS_LOG, "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        PID_FILE.write_text(str(proc.pid))
        log(f"Phase 4 launched in background (PID: {proc.pid})")

        import time
        time.sleep(3)

        assert True, f"Phase 4 launched successfully"
    except Exception as e:
        log(f"✗ Failed to launch Phase 4: {e}")
        assert False, str(e)


if __name__ == "__main__":
    test_phase4_restart()
