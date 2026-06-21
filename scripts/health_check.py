#!/usr/bin/env python3
"""
Health check cron job — monitors API health and gunicorn process
Checks:
  - /health endpoint returns 200 within 2s
  - gunicorn process running and RSS memory < 1GB
  - Gracefully restarts if unhealthy (pkill -HUP)
"""
import os
import sys
import subprocess
import requests
import psutil
import logging
import json
import time
from datetime import datetime
from pathlib import Path

# Configuration
API_URL = "http://localhost:5000/health"
API_TIMEOUT = 2.0
MEMORY_LIMIT_MB = 1000  # 1GB in MB
MAX_RESTARTS_PER_HOUR = 3
LOG_FILE = os.path.expanduser("~/meritgiving/logs/health_check.log")
STATE_FILE = os.path.expanduser("~/meritgiving/logs/health_check_state.json")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_restart_state():
    """Load restart count state"""
    if not os.path.exists(STATE_FILE):
        return {'restarts': [], 'last_restart': None}
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load state file: %s", e)
        return {'restarts': [], 'last_restart': None}

def save_restart_state(state):
    """Save restart count state"""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        logger.warning("Failed to save state file: %s", e)

def check_api_health():
    """Check /health endpoint"""
    try:
        resp = requests.get(API_URL, timeout=API_TIMEOUT)
        return resp.status_code == 200, resp.status_code
    except requests.Timeout:
        return False, "TIMEOUT"
    except requests.RequestException as e:
        return False, str(e)

def find_gunicorn_process():
    """Find gunicorn process"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'gunicorn' in proc.name() or (proc.info['cmdline'] and 'gunicorn' in ' '.join(proc.info['cmdline'])):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass
    return None

def check_gunicorn_memory(proc):
    """Check gunicorn RSS memory"""
    try:
        rss_mb = proc.memory_info().rss / 1024 / 1024
        return rss_mb, rss_mb < MEMORY_LIMIT_MB
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        return None, False

def restart_gunicorn():
    """Gracefully restart gunicorn"""
    try:
        # Try systemctl first
        result = subprocess.run(
            ['systemctl', 'restart', 'daanaa-api'],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info("Gunicorn restarted via systemctl")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: pkill -HUP
    try:
        result = subprocess.run(
            ['pkill', '-HUP', 'gunicorn'],
            capture_output=True,
            timeout=5
        )
        logger.info("Gunicorn HUP signal sent (pkill -HUP)")
        return True
    except Exception as e:
        logger.error("Failed to restart gunicorn: %s", e)
        return False

def record_restart(state):
    """Record a restart event and check hourly limit"""
    now = datetime.now()
    state['restarts'] = [t for t in state.get('restarts', []) if (now - datetime.fromisoformat(t)).total_seconds() < 3600]
    state['restarts'].append(now.isoformat())
    state['last_restart'] = now.isoformat()
    save_restart_state(state)
    return len(state['restarts']) <= MAX_RESTARTS_PER_HOUR

def main():
    logger.info("=" * 70)
    logger.info("Health check started")
    logger.info("=" * 70)

    all_ok = True
    state = load_restart_state()

    # Check API health
    api_ok, api_status = check_api_health()
    if api_ok:
        logger.info("API health: OK (status %s)", api_status)
    else:
        logger.error("API health: FAILED (status %s)", api_status)
        all_ok = False

    # Check gunicorn process
    gunicorn_proc = find_gunicorn_process()
    if not gunicorn_proc:
        logger.error("Gunicorn process: NOT FOUND")
        all_ok = False
    else:
        logger.info("Gunicorn process: OK (PID %d)", gunicorn_proc.pid)

        # Check memory
        if gunicorn_proc:
            rss_mb, mem_ok = check_gunicorn_memory(gunicorn_proc)
            if rss_mb is not None:
                logger.info("Gunicorn memory: %.1f MB", rss_mb)
                if not mem_ok:
                    logger.warning("Gunicorn memory usage HIGH (%.1f MB > %d MB)", rss_mb, MEMORY_LIMIT_MB)
                    all_ok = False
            else:
                logger.warning("Could not read gunicorn memory")

    # If any check failed, attempt restart
    if not all_ok:
        logger.warning("Health check FAILED, attempting restart...")
        record_ok = record_restart(state)
        if record_ok:
            if restart_gunicorn():
                logger.info("Restart triggered, will re-check in next cycle")
                return 1
            else:
                logger.error("Restart failed")
                return 2
        else:
            logger.error("Too many restarts in the last hour (limit: %d)", MAX_RESTARTS_PER_HOUR)
            return 2

    logger.info("Health check: ALL OK")
    logger.info("=" * 70)
    return 0

if __name__ == '__main__':
    sys.exit(main())
