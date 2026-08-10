#!/usr/bin/env python3
"""
Generic daemon health-decision library.

Standard pattern (see docs/DAEMON_HEALTH_STANDARD.md): any long-running
process publishes its own authoritative state atomically; its watchdog/
monitor reads that state and applies a pure, testable decision function —
never greps log text or infers throughput from log symbols/line-counting.

Extracted 2026-08-10 from scripts/discovery_daemon_health.py after two
independent incidents in the same session, both caused by the anti-pattern
this library replaces:

  1. watchdog_discovery.sh grepped log text for a hardcoded batch-size
     string; the daemon's actual batch size drifted, the grep silently
     stopped matching, and a proven kill-and-restart fix sat dead for
     ~15.4 days while still reporting healthy.
  2. monitor_discovery_health.py counted ✅/⚪ symbols in the last 1000 log
     lines as a "discovered" proxy, and its alert condition required
     `discovered > 0` (to avoid a division-by-zero at startup) — which
     meant the alert was silently skipped exactly when discovered==0,
     the very state it most needed to catch.

Both bugs share a root cause: deriving health from a side channel (log
text) that can drift out of sync with the thing it's trying to measure,
instead of from state the process itself publishes as its primary duty.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def read_state(path):
    """Returns the parsed state dict, or None if missing/corrupt. Never
    raises — an unreadable state file must fail toward 'use fallback' or
    'flag as unknown', never crash the caller or silently mean 'healthy'."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_state_atomic(path, state):
    """Atomic write (tmp + rename). Never raises — callers should treat a
    failed write as non-fatal to the process doing real work; a monitor
    reading a missing/stale file should already fail toward 'unknown', not
    'healthy' (see evaluate_health)."""
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        tmp_path.replace(path)
        return True
    except OSError:
        return False


def evaluate_health(
    state,
    pid_alive,
    current_pid,
    now=None,
    stale_heartbeat_seconds=900,
    stuck_thresholds=None,
):
    """Pure decision function — no file/process I/O. Everything needed is
    passed in, so any caller (bash via CLI wrapper, Python directly, tests)
    gets identical, independently-testable behavior.

    stuck_thresholds: optional dict of {counter_name: min_value} that must
    ALL be met simultaneously for a "stuck" verdict (mirrors the proven
    2026-07-20/21 semantics: frozen progress counter AND repeated full
    timeouts, not either alone). If None, only liveness/staleness are
    checked — callers with no meaningful stuck-pattern (e.g. a simple HTTP
    health-check daemon) can skip this entirely rather than fake thresholds.

    Returns {"action": ..., "reason": "..."} where action is one of:
      "restart"           - kill and restart, a real problem was found
      "ok"                - genuinely healthy
      "unknown_no_state"  - no state file; caller should use a fallback
                             check instead of assuming healthy
      "unknown_stale_pid" - state file belongs to a PID that isn't the
                             currently running process (stale snapshot
                             from before a prior restart)
    """
    now = now or datetime.now(timezone.utc)

    if not pid_alive:
        return {"action": "restart", "reason": "process not running"}

    if state is None:
        return {
            "action": "unknown_no_state",
            "reason": "no state file yet; process may have just started or "
                      "predates this instrumentation",
        }

    if state.get("pid") != current_pid:
        return {
            "action": "unknown_stale_pid",
            "reason": f"state file pid {state.get('pid')} does not match "
                      f"running pid {current_pid}; stale snapshot from a "
                      f"prior process",
        }

    last_updated_at = state.get("last_updated_at")
    if last_updated_at:
        try:
            last_updated = datetime.fromisoformat(last_updated_at)
            age_seconds = (now - last_updated).total_seconds()
        except ValueError:
            age_seconds = None
        if age_seconds is not None and age_seconds > stale_heartbeat_seconds:
            return {
                "action": "restart",
                "reason": f"heartbeat stale ({age_seconds:.0f}s since last "
                          f"update, threshold {stale_heartbeat_seconds}s)",
            }

    if stuck_thresholds:
        unmet = [
            name
            for name, min_value in stuck_thresholds.items()
            if state.get(name, 0) < min_value
        ]
        if not unmet:
            reasons = ", ".join(
                f"{name}={state.get(name)}" for name in stuck_thresholds
            )
            return {"action": "restart", "reason": f"stuck pattern: {reasons}"}

    return {"action": "ok", "reason": "producing output normally"}


def zero_output_is_not_healthy(discovered_count, verified_count, success_rate_if_any):
    """Codifies the fix for the second 2026-08-10 bug: zero attempts in the
    measurement window must never be silently treated as healthy just
    because a `count > 0` guard was needed elsewhere to avoid a
    division-by-zero. Call this explicitly at any callsite that computes a
    success-rate-style metric with a similar guard.

    Returns True if this specific zero-output state should itself be
    flagged as a problem (not evaluate whether the rate is good enough --
    that's a separate, ordinary threshold check the caller still does)."""
    return discovered_count == 0 and verified_count == 0
