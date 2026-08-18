"""
Tests for scripts/daemon_health_lib.py — the generic pattern extracted from
discovery_daemon_health.py so future daemons don't reinvent (or subtly
mis-copy) the same state-based health decision.

discovery_daemon_health.py's own tests (test_discovery_daemon_health.py)
cover the discovery-specific thresholds and phrasing; these tests cover the
library's generic behavior independent of any one daemon's field names.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "ops"))

from daemon_health_lib import (  # noqa: E402
    evaluate_health,
    read_state,
    write_state_atomic,
    zero_output_is_not_healthy,
)

NOW = datetime(2026, 8, 10, 19, 30, 0, tzinfo=timezone.utc)


def test_process_not_alive_restarts_regardless_of_state():
    result = evaluate_health({"pid": 1}, pid_alive=False, current_pid=1, now=NOW)
    assert result["action"] == "restart"


def test_no_state_is_unknown_not_healthy():
    """Absence of information must never resolve to 'ok' - that's exactly
    how both 2026-08-10 bugs stayed invisible."""
    result = evaluate_health(None, pid_alive=True, current_pid=1, now=NOW)
    assert result["action"] == "unknown_no_state"


def test_stale_pid_flagged_not_trusted():
    result = evaluate_health({"pid": 999}, pid_alive=True, current_pid=1, now=NOW)
    assert result["action"] == "unknown_stale_pid"


def test_healthy_with_no_stuck_thresholds_configured():
    """A daemon with no meaningful stuck-pattern (e.g. a plain HTTP
    health-check daemon) can pass stuck_thresholds=None and get liveness +
    staleness checking only."""
    state = {"pid": 1, "last_updated_at": NOW.isoformat()}
    result = evaluate_health(state, pid_alive=True, current_pid=1, now=NOW, stuck_thresholds=None)
    assert result["action"] == "ok"


def test_stale_heartbeat_restarts_with_no_stuck_thresholds():
    old = NOW - timedelta(seconds=1000)
    state = {"pid": 1, "last_updated_at": old.isoformat()}
    result = evaluate_health(
        state, pid_alive=True, current_pid=1, now=NOW,
        stale_heartbeat_seconds=900, stuck_thresholds=None,
    )
    assert result["action"] == "restart"
    assert "stale" in result["reason"]


def test_custom_stuck_thresholds_all_must_be_met():
    """Generic mechanism: ALL configured thresholds must be met simultaneously,
    mirroring the proven discovery-daemon semantics but with arbitrary
    counter names for a different daemon."""
    thresholds = {"errors_in_a_row": 3, "requests_since_last_2xx": 10}

    state_partial = {
        "pid": 1,
        "last_updated_at": NOW.isoformat(),
        "errors_in_a_row": 3,
        "requests_since_last_2xx": 5,  # below threshold
    }
    result_partial = evaluate_health(
        state_partial, pid_alive=True, current_pid=1, now=NOW, stuck_thresholds=thresholds
    )
    assert result_partial["action"] == "ok"

    state_both = {
        "pid": 1,
        "last_updated_at": NOW.isoformat(),
        "errors_in_a_row": 5,
        "requests_since_last_2xx": 15,
    }
    result_both = evaluate_health(
        state_both, pid_alive=True, current_pid=1, now=NOW, stuck_thresholds=thresholds
    )
    assert result_both["action"] == "restart"
    assert "errors_in_a_row=5" in result_both["reason"]
    assert "requests_since_last_2xx=15" in result_both["reason"]


def test_missing_counter_in_state_defaults_to_zero_not_exception():
    """A daemon that hasn't started tracking a counter yet shouldn't crash
    the evaluator - missing means 0, which is 'below threshold' (ok) for any
    positive threshold, not a KeyError."""
    thresholds = {"some_counter": 5}
    state = {"pid": 1, "last_updated_at": NOW.isoformat()}  # no 'some_counter' key
    result = evaluate_health(
        state, pid_alive=True, current_pid=1, now=NOW, stuck_thresholds=thresholds
    )
    assert result["action"] == "ok"


def test_read_state_missing_file_returns_none(tmp_path):
    assert read_state(tmp_path / "nope.json") is None


def test_read_state_corrupt_returns_none(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not json")
    assert read_state(f) is None


def test_write_state_atomic_roundtrip(tmp_path):
    f = tmp_path / "state.json"
    state = {"pid": 123, "foo": "bar"}
    assert write_state_atomic(f, state) is True
    assert read_state(f) == state
    # tmp file must not be left behind
    assert not (tmp_path / "state.json.tmp").exists()


def test_write_state_atomic_no_partial_file_visible_mid_write(tmp_path):
    """The tmp+rename pattern means a concurrent reader never sees a
    half-written file - verify the final file is exactly the last write,
    never a torn/partial one, across repeated writes."""
    f = tmp_path / "state.json"
    for i in range(5):
        write_state_atomic(f, {"pid": 1, "iteration": i})
    assert read_state(f) == {"pid": 1, "iteration": 4}


def test_zero_output_is_flagged():
    """Directly encodes the second 2026-08-10 bug: monitor_discovery_health.py's
    alert condition required `discovered > 0`, which meant zero discovered
    (the daemon doing nothing at all) silently bypassed the alert entirely.
    This helper makes that state explicitly checkable, separate from the
    ordinary success-rate-below-threshold check."""
    assert zero_output_is_not_healthy(discovered_count=0, verified_count=0, success_rate_if_any=0) is True


def test_nonzero_output_is_not_flagged_by_this_check():
    """This helper only flags true zero-output; an ordinary low-but-nonzero
    success rate is a different (still valid) check the caller does separately."""
    assert zero_output_is_not_healthy(discovered_count=50, verified_count=2, success_rate_if_any=4.0) is False
