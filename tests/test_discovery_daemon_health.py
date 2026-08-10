"""
Tests for scripts/discovery_daemon_health.py — the decision logic that
replaced the watchdog's log-text-grepping, which silently broke for ~15.4
days (2026-08-10 lesson) when the daemon's batch-size parameter drifted out
of sync with a hardcoded string in a different file.

These tests exist specifically so that class of regression is caught here,
automatically, instead of requiring another manual audit.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from discovery_daemon_health import (  # noqa: E402
    FULL_TIMEOUT_STREAK_THRESHOLD,
    ITERATIONS_SINCE_CHANGE_THRESHOLD,
    STALE_HEARTBEAT_SECONDS,
    evaluate_health,
    read_state,
)

NOW = datetime(2026, 8, 10, 19, 30, 0, tzinfo=timezone.utc)


def healthy_state(pid=1979175, **overrides):
    state = {
        "pid": pid,
        "batch_size": 100,
        "workers": 8,
        "iteration": 50,
        "verified_total": 2400,
        "iterations_since_verified_change": 0,
        "full_timeout_streak": 0,
        "last_updated_at": NOW.isoformat(),
        "started_at": (NOW - timedelta(hours=2)).isoformat(),
    }
    state.update(overrides)
    return state


def test_process_not_alive_always_restarts_regardless_of_state():
    result = evaluate_health(healthy_state(), pid_alive=False, current_pid=1979175, now=NOW)
    assert result["action"] == "restart"


def test_no_state_file_returns_unknown_not_a_false_healthy():
    """This is the critical regression guard: absence of information must
    never be silently treated as 'ok' - that's exactly how the original bug
    stayed invisible. Caller is expected to fall back to another check."""
    result = evaluate_health(None, pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "unknown_no_state"
    assert result["action"] != "ok"


def test_stale_pid_in_state_file_is_flagged_not_trusted():
    """State file from a previous process (before a restart) must not be
    read as current - same class of bug as the July append-only-log issue."""
    state = healthy_state(pid=999999)  # different from current_pid below
    result = evaluate_health(state, pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "unknown_stale_pid"


def test_genuinely_healthy_state_is_ok():
    result = evaluate_health(healthy_state(), pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "ok"


def test_stuck_thread_leak_pattern_triggers_restart():
    """Reproduces the actual 2026-08-10 incident state: verified counter
    frozen for many iterations, every recent batch a full timeout."""
    state = healthy_state(
        iterations_since_verified_change=20,
        full_timeout_streak=20,
    )
    result = evaluate_health(state, pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "restart"
    assert "thread leak" in result["reason"]


def test_below_both_thresholds_does_not_restart():
    """A couple of timeouts happen normally (one tarpit site, etc.) - must
    not be trigger-happy below the proven thresholds."""
    state = healthy_state(
        iterations_since_verified_change=ITERATIONS_SINCE_CHANGE_THRESHOLD - 1,
        full_timeout_streak=FULL_TIMEOUT_STREAK_THRESHOLD - 1,
    )
    result = evaluate_health(state, pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "ok"


def test_only_one_threshold_met_does_not_restart():
    """Both conditions must hold together - matches the proven 2026-07-21
    semantics (frozen counter AND repeated full timeouts), not either alone."""
    state = healthy_state(
        iterations_since_verified_change=ITERATIONS_SINCE_CHANGE_THRESHOLD,
        full_timeout_streak=0,  # counter frozen but not from batch timeouts
    )
    result = evaluate_health(state, pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "ok"

    state2 = healthy_state(
        iterations_since_verified_change=0,
        full_timeout_streak=FULL_TIMEOUT_STREAK_THRESHOLD,
    )
    result2 = evaluate_health(state2, pid_alive=True, current_pid=1979175, now=NOW)
    assert result2["action"] == "ok"


def test_exactly_at_threshold_triggers():
    """Boundary condition: >= threshold, not > threshold."""
    state = healthy_state(
        iterations_since_verified_change=ITERATIONS_SINCE_CHANGE_THRESHOLD,
        full_timeout_streak=FULL_TIMEOUT_STREAK_THRESHOLD,
    )
    result = evaluate_health(state, pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "restart"


def test_stale_heartbeat_restarts_even_with_healthy_counters():
    """A daemon that stopped looping entirely (hung outside the batch-timeout
    path) won't show frozen-counter symptoms because it never gets far enough
    to log a new iteration at all. Heartbeat staleness is a separate,
    independent check for exactly that case."""
    old_time = NOW - timedelta(seconds=STALE_HEARTBEAT_SECONDS + 60)
    state = healthy_state(last_updated_at=old_time.isoformat())
    result = evaluate_health(state, pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "restart"
    assert "stale" in result["reason"]


def test_heartbeat_just_under_threshold_does_not_restart():
    recent_time = NOW - timedelta(seconds=STALE_HEARTBEAT_SECONDS - 60)
    state = healthy_state(last_updated_at=recent_time.isoformat())
    result = evaluate_health(state, pid_alive=True, current_pid=1979175, now=NOW)
    assert result["action"] == "ok"


def test_read_state_missing_file_returns_none_not_exception(tmp_path):
    result = read_state(tmp_path / "does-not-exist.json")
    assert result is None


def test_read_state_corrupt_json_returns_none_not_exception(tmp_path):
    bad_file = tmp_path / "corrupt.json"
    bad_file.write_text("{not valid json")
    result = read_state(bad_file)
    assert result is None


def test_read_state_valid_file_roundtrips(tmp_path):
    import json

    state_file = tmp_path / "state.json"
    original = healthy_state()
    state_file.write_text(json.dumps(original))
    result = read_state(state_file)
    assert result == original


def test_this_exact_regression_would_have_been_caught():
    """Directly encodes the 2026-08-10 incident: batch_size=100 in the
    daemon's real state, which the OLD watchdog's hardcoded 'abandoning 50
    stuck' grep could never match regardless of actual health. This test
    proves the new decision logic doesn't care what the batch size is at
    all - it reads the daemon's own counters, not a string that has to stay
    in sync with them."""
    state_batch_50 = healthy_state(
        batch_size=50, iterations_since_verified_change=20, full_timeout_streak=20
    )
    state_batch_100 = healthy_state(
        batch_size=100, iterations_since_verified_change=20, full_timeout_streak=20
    )
    result_50 = evaluate_health(state_batch_50, pid_alive=True, current_pid=1979175, now=NOW)
    result_100 = evaluate_health(state_batch_100, pid_alive=True, current_pid=1979175, now=NOW)
    assert result_50["action"] == "restart"
    assert result_100["action"] == "restart"
    assert result_50["action"] == result_100["action"]  # batch_size is irrelevant to the decision
