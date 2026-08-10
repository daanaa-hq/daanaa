"""
Tests for the check_health() alert logic in scripts/monitor_discovery_health.py.

Specifically guards against the 2026-08-10 bug: the alert condition was
`success_rate < THRESHOLD and discovered > 0`, which meant discovered == 0
(daemon alive, producing nothing) silently bypassed the alert and returned
"✅ Daemon healthy" every hour for ~15.4 days. These tests exercise
check_health() with mocked I/O so that regression can never return
unnoticed.
"""

import importlib.util
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "monitor_discovery_health", REPO_ROOT / "scripts" / "monitor_discovery_health.py"
)
mdh = importlib.util.module_from_spec(SPEC)
sys.modules["monitor_discovery_health"] = mdh
SPEC.loader.exec_module(mdh)


def test_zero_discovered_and_zero_verified_alerts_not_silently_healthy():
    """The exact 2026-08-10 incident state, reproduced directly against
    check_health(): discovered=0, verified=0, success_rate=0 (from the
    div-by-zero guard in get_discovery_stats). Must return False, not True."""
    with mock.patch.object(mdh, "check_daemon_running", return_value=True), \
         mock.patch.object(mdh, "get_discovery_stats",
                            return_value={"discovered": 0, "verified": 0,
                                          "success_rate": 0, "errors": 0}), \
         mock.patch.object(mdh, "get_queue_depth", return_value=0), \
         mock.patch.object(mdh, "read_state", return_value=None):
        result = mdh.check_health()
    assert result is False


def test_healthy_nonzero_output_returns_true():
    with mock.patch.object(mdh, "check_daemon_running", return_value=True), \
         mock.patch.object(mdh, "get_discovery_stats",
                            return_value={"discovered": 100, "verified": 40,
                                          "success_rate": 40.0, "errors": 2}), \
         mock.patch.object(mdh, "get_queue_depth", return_value=316), \
         mock.patch.object(mdh, "read_state", return_value={"iteration": 9}):
        result = mdh.check_health()
    assert result is True


def test_daemon_not_running_alerts_regardless_of_stats():
    with mock.patch.object(mdh, "check_daemon_running", return_value=False), \
         mock.patch.object(mdh, "get_discovery_stats",
                            return_value={"discovered": 100, "verified": 40,
                                          "success_rate": 40.0, "errors": 0}), \
         mock.patch.object(mdh, "get_queue_depth", return_value=0), \
         mock.patch.object(mdh, "read_state", return_value=None):
        result = mdh.check_health()
    assert result is False


def test_low_but_nonzero_success_rate_still_alerts_on_threshold():
    """Distinguishes the two DIFFERENT alert conditions: zero-output is one
    check, low-nonzero-success-rate is a separate ordinary threshold check.
    Both must still work independently after the fix."""
    with mock.patch.object(mdh, "check_daemon_running", return_value=True), \
         mock.patch.object(mdh, "get_discovery_stats",
                            return_value={"discovered": 100, "verified": 5,
                                          "success_rate": 5.0, "errors": 0}), \
         mock.patch.object(mdh, "get_queue_depth", return_value=0), \
         mock.patch.object(mdh, "read_state", return_value=None):
        result = mdh.check_health()
    assert result is False  # below 25% threshold, correctly still alerts


def test_missing_daemon_state_file_does_not_crash_or_mask_zero_output():
    """read_state() returning None (file missing/corrupt) must not prevent
    the zero-output alert from firing - the daemon state file is a
    cross-check, not a required dependency for this alert."""
    with mock.patch.object(mdh, "check_daemon_running", return_value=True), \
         mock.patch.object(mdh, "get_discovery_stats",
                            return_value={"discovered": 0, "verified": 0,
                                          "success_rate": 0, "errors": 0}), \
         mock.patch.object(mdh, "get_queue_depth", return_value=0), \
         mock.patch.object(mdh, "read_state", return_value=None):
        result = mdh.check_health()
    assert result is False
