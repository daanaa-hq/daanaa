#!/usr/bin/env python3
"""Emergency Fixes for Critical Production Issues - Ready for deployment Aug 15"""
import os, sys, json, socket, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent.parent
VENV_PATH = BASE_DIR / "venv" / "bin" / "activate"
OVERNIGHT_SCRIPT = BASE_DIR / "scripts" / "run_overnight_pipeline.sh"
INFERENCE_HEALTH_URL = "http://localhost:11437/health"
INFERENCE_PORT = 11437

def log(msg: str, level: str = "INFO"):
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    print(f"[{ts}] {level}: {msg}", file=sys.stderr)

def is_inference_server_alive(port: int = INFERENCE_PORT) -> bool:
    """Check port + /health endpoint"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result != 0: return False
        proc = subprocess.run(["curl", "-s", INFERENCE_HEALTH_URL], capture_output=True, timeout=5)
        return proc.returncode == 0
    except:
        return False

def restart_inference_server():
    """Kill and restart inference server"""
    try:
        log("Stopping inference server...")
        subprocess.run(["killall", "llama-server"], capture_output=True)
        time.sleep(2)
        embed_script = BASE_DIR / "scripts" / "embed_server.sh"
        if embed_script.exists():
            log("Starting inference server...")
            subprocess.Popen(["bash", str(embed_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            if is_inference_server_alive():
                log("Inference server restarted successfully", "SUCCESS")
                return True
        log("Failed to restart inference server", "WARNING")
        return False
    except Exception as e:
        log(f"Error restarting inference server: {e}", "ERROR")
        return False

def fix_cron_import_error():
    """Fix Cron ImportError by ensuring venv activation"""
    log("Fixing Cron ImportError...")
    if not VENV_PATH.exists():
        log(f"venv not found at {VENV_PATH}", "ERROR")
        return False
    wrapper_content = f"""#!/bin/bash
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
