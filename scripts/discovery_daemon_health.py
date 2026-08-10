#!/usr/bin/env python3
"""
Discovery-daemon-specific health decision — thin wrapper over
scripts/daemon_health_lib.py (see docs/DAEMON_HEALTH_STANDARD.md for the
general pattern this instantiates).

CLI used by watchdog_discovery.sh; evaluate_health() also directly
importable for tests (tests/test_discovery_daemon_health.py).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from daemon_health_lib import evaluate_health as _generic_evaluate_health  # noqa: E402
from daemon_health_lib import read_state  # noqa: E402, F401 (re-exported for callers/tests)

# Thresholds proven live in the 2026-07-20/21 incident: 4 consecutive
# full-batch timeouts AND the verified counter frozen across 6 iterations,
# both required together (not either alone) before declaring a thread leak.
ITERATIONS_SINCE_CHANGE_THRESHOLD = 6
FULL_TIMEOUT_STREAK_THRESHOLD = 4

# Generous relative to the daemon's own 600s per-batch timeout, so this
# never fires on a single slow-but-fine batch.
STALE_HEARTBEAT_SECONDS = 900

_STUCK_THRESHOLDS = {
    "iterations_since_verified_change": ITERATIONS_SINCE_CHANGE_THRESHOLD,
    "full_timeout_streak": FULL_TIMEOUT_STREAK_THRESHOLD,
}


def evaluate_health(state, pid_alive, current_pid, now=None):
    result = _generic_evaluate_health(
        state,
        pid_alive=pid_alive,
        current_pid=current_pid,
        now=now,
        stale_heartbeat_seconds=STALE_HEARTBEAT_SECONDS,
        stuck_thresholds=_STUCK_THRESHOLDS,
    )
    # Keep the domain-specific "thread leak" phrasing established in
    # governance/LESSONS.md 2026-07-20/21 for this particular stuck pattern,
    # rather than the library's generic "stuck pattern: ..." wording.
    if result["action"] == "restart" and "stuck pattern:" in result["reason"]:
        iterations = state.get("iterations_since_verified_change")
        timeouts = state.get("full_timeout_streak")
        result["reason"] = (
            f"thread leak: verified counter unchanged for {iterations} "
            f"iterations, {timeouts} consecutive full-batch timeouts"
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--pid", type=int, required=True,
                         help="Currently running daemon PID, from the caller's own pgrep")
    parser.add_argument("--pid-alive", choices=["true", "false"], required=True)
    args = parser.parse_args()

    state = read_state(args.state_file)
    result = evaluate_health(
        state, pid_alive=(args.pid_alive == "true"), current_pid=args.pid
    )
    import json
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
