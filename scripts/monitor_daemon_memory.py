#!/usr/bin/env python3
"""
Monitor daemon memory usage hourly. Pause daemon if RAM exceeds 27GB.
Auto-resume when RAM drops below 20GB.
"""

import subprocess
import time
import logging
import os
import signal
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/daemon_memory_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PAUSE_THRESHOLD_GB = 27
RESUME_THRESHOLD_GB = 20
CHECK_INTERVAL = 3600  # 1 hour


def get_memory_usage_gb():
    """Get current RAM usage in GB."""
    try:
        result = subprocess.run(
            ["free", "-b"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Mem:'):
                parts = line.split()
                bytes_used = int(parts[2])
                return bytes_used / (1024**3)
    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
    return 0


def get_daemon_pid():
    """Find discovery_daemon.py PID."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python3 scripts/discovery_daemon.py"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.stdout else None
    except Exception as e:
        logger.error(f"Failed to get daemon PID: {e}")
        return None


def pause_daemon(pid):
    """Pause daemon with SIGSTOP."""
    try:
        os.kill(int(pid), signal.SIGSTOP)
        logger.warning(f"⚠️  PAUSED daemon (PID {pid}) due to memory pressure (>{PAUSE_THRESHOLD_GB}GB)")
    except Exception as e:
        logger.error(f"Failed to pause daemon: {e}")


def resume_daemon(pid):
    """Resume daemon with SIGCONT."""
    try:
        os.kill(int(pid), signal.SIGCONT)
        logger.info(f"✅ RESUMED daemon (PID {pid}) - memory pressure eased (<{RESUME_THRESHOLD_GB}GB)")
    except Exception as e:
        logger.error(f"Failed to resume daemon: {e}")


def main():
    logger.info(f"Starting memory monitor (pause at {PAUSE_THRESHOLD_GB}GB, resume at {RESUME_THRESHOLD_GB}GB)")

    paused = False

    while True:
        time.sleep(CHECK_INTERVAL)

        mem_gb = get_memory_usage_gb()
        daemon_pid = get_daemon_pid()

        if not daemon_pid:
            logger.warning("Daemon not running, skipping check")
            continue

        if mem_gb > PAUSE_THRESHOLD_GB and not paused:
            pause_daemon(daemon_pid)
            paused = True
        elif mem_gb < RESUME_THRESHOLD_GB and paused:
            resume_daemon(daemon_pid)
            paused = False
        else:
            status = "PAUSED" if paused else "running"
            logger.info(f"Memory OK: {mem_gb:.1f}GB (daemon {status})")


if __name__ == '__main__':
    main()
