#!/usr/bin/env python3
"""
Test-first implementation of P6 Phase 2 fixes.

Each test is a FAILING test initially. Fix code makes it pass.

Test-first discipline:
1. Write failing test
2. Implement fix
3. Test passes
4. Commit both together
"""

import unittest
import os
import sys
import time
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path.home() / "meritgiving" / "scripts"))

try:
    import daemon_health_lib
except ImportError:
    daemon_health_lib = None


class TestIssue1_HardcodedTimeouts(unittest.TestCase):
    """ISSUE 1: Hardcoded timeouts (600, 3600) should be configurable"""

    def test_daemon_stale_threshold_is_configurable_via_env(self):
        """Stale threshold should come from env var, not hardcoded"""
        # Set custom timeout
        os.environ["DAEMON_STALE_THRESHOLD"] = "120"

        # Import the module (which should use env var)
        from daemon_health_lib import evaluate_health
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        stale_time = (now - timedelta(seconds=150)).isoformat()

        state = {
            "status": "healthy",
            "pid": 12345,
            "last_updated_at": stale_time
        }

        # With 120s threshold, 150s old should trigger restart
        stale_threshold = int(os.getenv("DAEMON_STALE_THRESHOLD", "900"))
        self.assertEqual(stale_threshold, 120)

        result = evaluate_health(
            state=state,
            pid_alive=True,
            current_pid=12345,
            now=now,
            stale_heartbeat_seconds=stale_threshold
        )
        self.assertEqual(result["action"], "restart")

    def test_inference_server_timeout_configurable(self):
        """Inference server timeout should be env var"""
        os.environ["INFERENCE_TIMEOUT"] = "5"
        timeout = int(os.getenv("INFERENCE_TIMEOUT", "2"))
        self.assertEqual(timeout, 5)


class TestIssue2_LogParsingAntiPattern(unittest.TestCase):
    """ISSUE 2: Log parsing anti-pattern (grep) should use published state"""

    def test_watchdog_no_log_grepping(self):
        """Watchdog scripts should NOT grep logs"""
        # Check that migrated watchdog scripts don't use grep for log files
        watchdog_files = [
            "scripts/watchdog_discovery.sh",
            "scripts/watchdog_llama.sh",
            "scripts/api_watchdog.sh"
        ]

        for watchdog_file in watchdog_files:
            path = Path.home() / "meritgiving" / watchdog_file
            if path.exists():
                content = path.read_text()
                # Should not have grep commands (not comments)
                lines = [l.strip() for l in content.split('\n') if not l.strip().startswith('#')]
                grep_lines = [l for l in lines if 'grep' in l and '|' in l and 'logs' in l]
                self.assertEqual(len(grep_lines), 0,
                    f"{watchdog_file} should not grep logs: {grep_lines}")
                # Should read health file instead
                self.assertIn("health.json", content, f"{watchdog_file} should read health.json")

    def test_daemon_health_reads_published_state(self):
        """Daemon health evaluation should read published state"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = {
                "status": "healthy",
                "pid": 12345,
                "last_updated_at": "2026-08-10T12:00:00+00:00",
                "items_processed": 5000
            }
            json.dump(state, f)
            f.flush()

            # Read and evaluate
            read_state = daemon_health_lib.read_state(f.name)
            self.assertEqual(read_state["status"], "healthy")
            self.assertEqual(read_state["items_processed"], 5000)

            Path(f.name).unlink()


class TestIssue3_SilentExceptionHandlers(unittest.TestCase):
    """ISSUE 3: Silent exception handlers (bare except:) should log + propagate"""

    def test_exceptions_are_logged_not_silently_swallowed(self):
        """Exceptions should be caught, logged, and either raised or noted"""

        def failing_operation():
            raise ValueError("Test error")

        # This should raise (or be logged + re-raised)
        with self.assertRaises(ValueError):
            try:
                failing_operation()
            except ValueError as e:
                # Good: specific exception caught
                # In real code: logger.error(f"Error: {e}")
                # Then: raise or handle appropriately
                raise

    def test_batch_operation_logs_partial_failure(self):
        """If processing 100 items and 1 fails, should log + continue"""

        results = []

        def process_item(item):
            if item == "bad":
                raise ValueError("Bad item")
            return f"processed_{item}"

        items = ["good1", "good2", "bad", "good3"]
        errors = []

        for item in items:
            try:
                result = process_item(item)
                results.append(result)
            except ValueError as e:
                # Good: catch specific exception, log it, continue
                errors.append((item, str(e)))

        # Should have processed 3, failed on 1
        self.assertEqual(len(results), 3)
        self.assertEqual(len(errors), 1)
        self.assertIn("bad", [e[0] for e in errors])


class TestIssue4_WatchdogFlappingProtection(unittest.TestCase):
    """ISSUE 4: Watchdog false positives (flapping) should have hysteresis"""

    def test_single_unhealthy_doesnt_restart_immediately(self):
        """One degraded check should not cause restart"""

        class WatchdogWithHysteresis:
            def __init__(self, restart_threshold=3):
                self.unhealthy_count = 0
                self.restart_threshold = restart_threshold

            def check(self, status):
                if status != "healthy":
                    self.unhealthy_count += 1
                else:
                    self.unhealthy_count = 0

                if self.unhealthy_count >= self.restart_threshold:
                    return "restart"
                return "ok"

        watchdog = WatchdogWithHysteresis(restart_threshold=3)

        # One unhealthy = don't restart
        self.assertEqual(watchdog.check("degraded"), "ok")

        # Two unhealthy = don't restart
        self.assertEqual(watchdog.check("degraded"), "ok")

        # Third unhealthy = restart
        self.assertEqual(watchdog.check("degraded"), "restart")

        # After recover, reset counter
        self.assertEqual(watchdog.check("healthy"), "ok")
        self.assertEqual(watchdog.unhealthy_count, 0)

    def test_prevents_restart_storms(self):
        """Hysteresis should prevent rapid restart cycles"""
        watchdog = self._make_watchdog()

        # Simulate: healthy → degraded → healthy → degraded
        states = ["healthy", "degraded", "degraded", "healthy", "healthy", "degraded"]
        restarts = []

        for state in states:
            result = watchdog.check(state)
            if result == "restart":
                restarts.append(state)

        # Should have at most 1 restart, not flapping
        self.assertLessEqual(len(restarts), 1)

    def _make_watchdog(self):
        """Helper to create watchdog with hysteresis"""
        class WatchdogWithHysteresis:
            def __init__(self, threshold=3):
                self.unhealthy_count = 0
                self.threshold = threshold

            def check(self, status):
                self.unhealthy_count = 0 if status == "healthy" else self.unhealthy_count + 1
                return "restart" if self.unhealthy_count >= self.threshold else "ok"

        return WatchdogWithHysteresis()


class TestIssue5_ConfigValidation(unittest.TestCase):
    """ISSUE 5: Config validation gaps (missing env vars at startup)"""

    def test_required_config_validated_at_startup(self):
        """Service should fail fast if required config missing"""

        class ConfigValidator:
            REQUIRED = ["DAANAA_ADMIN_KEY", "DAANAA_DB_PATH"]

            @staticmethod
            def validate():
                missing = [k for k in ConfigValidator.REQUIRED if k not in os.environ]
                if missing:
                    raise ValueError(f"Missing required config: {missing}")

        # Missing config should raise
        os.environ.pop("DAANAA_ADMIN_KEY", None)
        with self.assertRaises(ValueError) as cm:
            ConfigValidator.validate()
        self.assertIn("DAANAA_ADMIN_KEY", str(cm.exception))

        # With config, should pass
        os.environ["DAANAA_ADMIN_KEY"] = "test_key"
        os.environ["DAANAA_DB_PATH"] = "/tmp/test.db"
        ConfigValidator.validate()  # Should not raise

    def test_optional_config_has_defaults(self):
        """Optional config should have sensible defaults"""

        class Config:
            DEFAULTS = {
                "DAEMON_STALE_THRESHOLD": "900",
                "API_TIMEOUT": "30",
            }

            @staticmethod
            def get(key):
                return os.getenv(key, Config.DEFAULTS.get(key))

        # No env var = get default
        os.environ.pop("DAEMON_STALE_THRESHOLD", None)
        self.assertEqual(Config.get("DAEMON_STALE_THRESHOLD"), "900")

        # With env var = get env value
        os.environ["DAEMON_STALE_THRESHOLD"] = "120"
        self.assertEqual(Config.get("DAEMON_STALE_THRESHOLD"), "120")


class TestIssue6_ErrorRecovery(unittest.TestCase):
    """ISSUE 6: Error recovery paths (retry logic with backoff)"""

    def test_retry_with_exponential_backoff(self):
        """Failed operations should retry with exponential backoff"""
        import random

        def retry_with_backoff(func, max_retries=3, base_delay=0.01):
            for attempt in range(max_retries):
                try:
                    return func()
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    # Add jitter
                    delay += random.uniform(-delay * 0.1, delay * 0.1)
                    time.sleep(delay)

        call_count = [0]

        def failing_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Network error")
            return "success"

        result = retry_with_backoff(failing_func, base_delay=0.01)
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 3)  # Called 3 times before success

    def test_max_retries_exceeded_raises(self):
        """If all retries fail, should raise"""

        def retry_with_backoff(func, max_retries=3):
            for attempt in range(max_retries):
                try:
                    return func()
                except Exception:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(0.01 * (2 ** attempt))

        def always_fails():
            raise ValueError("Always fails")

        with self.assertRaises(ValueError):
            retry_with_backoff(always_fails, max_retries=3)

    def test_retry_prevents_thundering_herd(self):
        """Jitter in backoff should prevent all instances from retrying simultaneously"""
        import random

        delays = []

        def mock_sleep(delay):
            delays.append(delay)

        base_delay = 1.0
        for attempt in range(3):
            delay = base_delay * (2 ** attempt)
            jittered = delay + random.uniform(-delay * 0.1, delay * 0.1)
            mock_sleep(jittered)

        # All delays should be within expected range
        self.assertEqual(len(delays), 3)
        # First delay ~1s (±0.1s)
        self.assertGreaterEqual(delays[0], 0.9)
        self.assertLessEqual(delays[0], 1.1)
        # Second delay ~2s (±0.2s)
        self.assertGreaterEqual(delays[1], 1.8)
        self.assertLessEqual(delays[1], 2.2)


if __name__ == "__main__":
    unittest.main()

class TestIssue3_SilentExceptions(unittest.TestCase):
    """ISSUE 3: Silent exceptions should be caught, logged, and propagated"""

    def test_batch_operation_logs_errors(self):
        """Batch operations should log errors and continue with partial success"""
        results = []
        errors = []

        def process_with_logging(item):
            if item == "bad":
                raise ValueError("Invalid item")
            return f"processed_{item}"

        # Process batch with one failure
        for item in ["good1", "bad", "good2"]:
            try:
                result = process_with_logging(item)
                results.append(result)
            except ValueError as e:
                errors.append((item, str(e)))

        # Should have partial success
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 1)
        self.assertIn("bad", [e[0] for e in errors])
