"""
GATE 1 Issue 2: Watchdog uses health.json state, not log parsing

The decision logic that replaced the watchdog's log-text-grepping, which
silently broke for ~15.4 days (2026-08-10 lesson) when the daemon's
batch-size parameter drifted out of sync with a hardcoded string in a
different file. See docs/DAEMON_HEALTH_STANDARD.md and
scripts/ops/daemon_health_lib.py (the generic library this wraps).

2026-08-18: rewritten to actually delegate to daemon_health_lib.evaluate_health
instead of the ad-hoc HEALTH_FILE/check_daemon_health() implementation this
file had drifted to -- that version's signature and constants didn't match
this module's own test suite (tests/test_discovery_daemon_health.py),
which was written against the intended wrapper pattern and never actually
passed against the file it was testing. Found via a folder-migration-style
ModuleNotFoundError while investigating why the tests couldn't even import;
fixing the import surfaced this deeper mismatch.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ops"))
from daemon_health_lib import evaluate_health as _evaluate_health_generic
from daemon_health_lib import read_state  # noqa: F401 (re-exported for callers/tests)

# Proven thresholds (2026-07-20/21 incident, see daemon_health_lib.py docstring):
# BOTH counters frozen simultaneously indicates the actual thread-leak pattern
# observed in production -- a live daemon can legitimately hit either counter
# alone during normal operation (one slow site, one batch timeout), so only
# the conjunction is a real signal.
ITERATIONS_SINCE_CHANGE_THRESHOLD = 15
FULL_TIMEOUT_STREAK_THRESHOLD = 15
STALE_HEARTBEAT_SECONDS = 900  # matches watchdog_llama.sh / watchdog_discovery.sh


def evaluate_health(state, pid_alive, current_pid, now=None):
    """Discovery-daemon-specific wrapper over the generic decision function:
    bakes in this daemon's proven thresholds so callers don't have to
    reconstruct them, and rewrites the stuck-pattern reason into this
    daemon's own domain language ("thread leak") so log output stays
    consistent with how this specific incident class has always been
    described in this codebase.
    """
    result = _evaluate_health_generic(
        state,
        pid_alive=pid_alive,
        current_pid=current_pid,
        now=now,
        stale_heartbeat_seconds=STALE_HEARTBEAT_SECONDS,
        stuck_thresholds={
            "iterations_since_verified_change": ITERATIONS_SINCE_CHANGE_THRESHOLD,
            "full_timeout_streak": FULL_TIMEOUT_STREAK_THRESHOLD,
        },
    )
    if result["action"] == "restart" and result["reason"].startswith("stuck pattern:"):
        result = dict(result)
        result["reason"] = "thread leak pattern (" + result["reason"].split("stuck pattern: ", 1)[1] + ")"
    return result


if __name__ == "__main__":
    import json

    HEALTH_FILE = "/tmp/discovery_daemon.health.json"
    state = read_state(HEALTH_FILE)
    result = evaluate_health(state, pid_alive=True, current_pid=None)
    print(json.dumps(result))
    sys.exit(0 if result["action"] == "ok" else 1)
