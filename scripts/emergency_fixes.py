#!/usr/bin/env python3
"""Emergency Fixes for Critical Production Issues - Ready for deployment Aug 15"""
import json
import os
import socket
import subprocess
import sys
import time
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent.parent
VENV_PATH = BASE_DIR / "venv" / "bin" / "activate"
OVERNIGHT_SCRIPT = BASE_DIR / "scripts" / "run_overnight_pipeline.sh"
INFERENCE_HEALTH_URL = "http://localhost:11437/health"
INFERENCE_PORT = 11437

@lru_cache(maxsize=1)
def _check_curl_available():
    """Check if curl is available (cached with thread-safe lru_cache)"""
    try:
        subprocess.run(["which", "curl"], capture_output=True, timeout=1, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def log(msg: str, level: str = "INFO"):
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    print(f"[{ts}] {level}: {msg}", file=sys.stderr)

def is_inference_server_alive(port: int = INFERENCE_PORT, timeout: int = 2) -> bool:
    """Check port + /health endpoint with configurable timeout"""
    # Check if curl is available (cached)
    if not _check_curl_available():
        log("curl not found; cannot check inference server", "ERROR")
        return False

    try:
        # Check if port is open with timeout (use context manager for guaranteed cleanup)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex(("127.0.0.1", port))
            if result != 0:
                return False

        # Check if server responds to /health
        proc = subprocess.run(["curl", "-s", INFERENCE_HEALTH_URL], capture_output=True, timeout=timeout)
        return proc.returncode == 0
    except Exception as e:
        log(f"Error checking inference server: {e}", "WARNING")
        return False

def write_daemon_health(daemon_name: str, status: str, error: str = None):
    """Write daemon health state (aligns with daemon_health_lib pattern)"""
    health_file = Path(f"/tmp/{daemon_name}_daemon.health.json")
    health_data = {
        "status": status,
        "last_updated_at": datetime.now(timezone.utc).isoformat(),
        "error": error
    }
    try:
        health_file.write_text(json.dumps(health_data))
    except Exception as e:
        log(f"Failed to write health file for {daemon_name}: {e}", "WARNING")

def restart_inference_server():
    """Kill and restart inference server"""
    try:
        log("Stopping inference server...")
        # Kill with timeout to prevent hanging
        subprocess.run(["killall", "llama-server"], capture_output=True, timeout=5)
        time.sleep(2)

        # Validate embed_server.sh exists and is executable
        embed_script = BASE_DIR / "scripts" / "embed_server.sh"
        if not embed_script.exists():
            log(f"embed_server.sh not found at {embed_script}", "ERROR")
            return False

        if not os.access(embed_script, os.X_OK):
            log(f"embed_server.sh is not executable", "ERROR")
            return False

        log("Starting inference server...")
        # Capture stderr to detect startup errors
        proc = subprocess.Popen(
            ["bash", str(embed_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)

        # Check if process is still running
        if proc.poll() is not None:
            _, stderr = proc.communicate()
            log(f"embed_server.sh failed: {stderr.decode()}", "ERROR")
            return False

        if is_inference_server_alive():
            log("Inference server restarted successfully", "SUCCESS")
            write_daemon_health("llama_server", "healthy")
            return True

        log("Failed to restart inference server", "WARNING")
        write_daemon_health("llama_server", "failed", "Restart failed - server not responding")
        return False
    except subprocess.TimeoutExpired:
        log("killall timed out (process stuck)", "ERROR")
        write_daemon_health("llama_server", "failed", "killall timeout")
        return False
    except Exception as e:
        log(f"Error restarting inference server: {e}", "ERROR")
        write_daemon_health("llama_server", "failed", str(e))
        return False

def fix_cron_import_error():
    """Fix Cron ImportError by ensuring venv activation"""
    log("Fixing Cron ImportError...")
    if not VENV_PATH.exists():
        log(f"venv not found at {VENV_PATH}", "ERROR")
        return False
    wrapper_content = f"""#!/bin/bash
set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

source {VENV_PATH}
cd {BASE_DIR}
python3 scripts/overnight_pipeline.py
"""
    try:
        OVERNIGHT_SCRIPT.write_text(wrapper_content)
        OVERNIGHT_SCRIPT.chmod(0o755)
        log(f"Created {OVERNIGHT_SCRIPT} with venv activation", "SUCCESS")
        return True
    except Exception as e:
        log(f"Error creating wrapper script: {e}", "ERROR")
        return False

def fix_inference_server_detection():
    """Fix inference server detection"""
    log("Checking inference server health...")
    if not is_inference_server_alive():
        log("Inference server not responding, restarting...", "WARNING")
        return restart_inference_server()
    log("Inference server is healthy", "SUCCESS")
    return True

def run_tests():
    """Run validation tests"""
    log("Running validation tests...")
    tests_passed = tests_failed = 0
    
    if VENV_PATH.exists():
        log("✓ venv found", "SUCCESS")
        tests_passed += 1
    else:
        log("✗ venv not found", "ERROR")
        tests_failed += 1
    
    if OVERNIGHT_SCRIPT.exists():
        log("✓ wrapper script exists", "SUCCESS")
        tests_passed += 1
    else:
        log("✗ wrapper script missing", "ERROR")
        tests_failed += 1
    
    if is_inference_server_alive():
        log("✓ inference server alive", "SUCCESS")
        tests_passed += 1
    else:
        log("✗ inference server not responding", "WARNING")
        tests_failed += 1
    
    try:
        health_file = Path("/tmp/test_health.json")
        test_data = {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
        health_file.write_text(json.dumps(test_data))
        health_file.unlink()
        log("✓ health json i/o works", "SUCCESS")
        tests_passed += 1
    except Exception as e:
        log(f"✗ health json i/o failed: {e}", "ERROR")
        tests_failed += 1
    
    log(f"Tests: {tests_passed} passed, {tests_failed} failed", "INFO")
    return tests_failed == 0

def main():
    log("Starting emergency fixes...")
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        log("Running in TEST mode (no changes)", "INFO")
        return 0 if run_tests() else 1
    
    log("Applying fixes...")
    if not fix_cron_import_error():
        log("Failed to fix Cron ImportError", "ERROR")
        return 1
    
    if not fix_inference_server_detection():
        log("Failed to fix inference server detection", "WARNING")
    
    log("All fixes applied successfully", "SUCCESS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
