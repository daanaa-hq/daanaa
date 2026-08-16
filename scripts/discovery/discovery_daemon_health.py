"""
GATE 1 Issue 2: Watchdog uses health.json state, not log parsing
Integrates daemon_health_lib for robust state-based health checks
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from scripts.ops.daemon_health_lib import evaluate_health, read_state

HEALTH_FILE = "/tmp/discovery_daemon.health.json"
STALE_THRESHOLD = 900  # 15 minutes

def check_daemon_health():
    """
    Read daemon health from state file (not logs).
    Return: {'status': 'healthy'|'unhealthy', 'action': 'continue'|'restart'}
    """
    if not Path(HEALTH_FILE).exists():
        return {
            'status': 'unknown',
            'action': 'start',
            'reason': 'No health state file found'
        }
    
    try:
        state = read_state(HEALTH_FILE)
        result = evaluate_health(
            state,
            pid_alive=True,  # Caller checks this
            current_pid=None,  # Caller provides this
            stale_heartbeat_seconds=STALE_THRESHOLD
        )
        return result
    except Exception as e:
        return {
            'status': 'error',
            'action': 'restart',
            'reason': f'Health check failed: {e}'
        }

if __name__ == '__main__':
    result = check_daemon_health()
    print(json.dumps(result))
    sys.exit(0 if result['action'] == 'continue' else 1)
