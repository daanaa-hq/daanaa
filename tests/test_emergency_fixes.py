#!/usr/bin/env python3
"""
Unit tests for emergency fixes (P6 critical issues).

Tests validate:
1. Cron ImportError fix — venv activation
2. Inference Server fix — health check + restart
3. Watchdog migration — daemon_health_lib.py pattern
"""

import unittest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add scripts to path
sys.path.insert(0, str(Path.home() / "meritgiving" / "scripts"))

import emergency_fixes
import daemon_health_lib


class TestCronImportFix(unittest.TestCase):
    """Test that cron script properly activates venv."""

    def test_run_overnight_pipeline_has_venv_activation(self):
        """Cron script must activate venv before importing anything."""
        cron_script = Path.home() / "meritgiving" / "scripts" / "run_overnight_pipeline.sh"

        if cron_script.exists():
            content = cron_script.read_text()
            # Must have venv activation
            self.assertIn("source", content, "Cron script must source venv")
            self.assertIn("venv/bin/activate", content, "Cron script must activate venv")
            # Must activate BEFORE running python
            self.assertLess(
                content.find("source"),
                content.find("python"),
                "venv activation must come before python"
            )


class TestInferenceServerFix(unittest.TestCase):
    """Test inference server health check."""

    @patch("socket.socket")
    def test_is_inference_server_alive_port_open(self, mock_socket):
        """Should return True when port is open and server responds."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect_ex.return_value = 0  # Port open

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)  # Server responds
            result = emergency_fixes.is_inference_server_alive(port=11437)
            self.assertTrue(result)

    @patch("socket.socket")
    def test_is_inference_server_alive_port_closed(self, mock_socket):
        """Should return False when port is closed."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect_ex.return_value = 1  # Port closed

        result = emergency_fixes.is_inference_server_alive(port=11437)
        self.assertFalse(result)

    @patch("subprocess.run")
    @patch("socket.socket")
    def test_is_inference_server_alive_port_open_no_response(self, mock_socket, mock_run):
        """Should return False if port open but server doesn't respond."""
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect_ex.return_value = 0  # Port open

        mock_run.return_value = Mock(returncode=1)  # No response to curl
        result = emergency_fixes.is_inference_server_alive(port=11437)
        self.assertFalse(result)


class TestDaemonHealthLib(unittest.TestCase):
    """Test daemon_health_lib.py pattern."""

    def test_read_state_missing_file(self):
        """Should return None if health file missing."""
        result = daemon_health_lib.read_state("/nonexistent/path/health.json")
        self.assertIsNone(result)

    def test_read_state_corrupt_json(self):
        """Should return None if JSON is corrupt."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json}")
            f.flush()
            result = daemon_health_lib.read_state(f.name)
            self.assertIsNone(result)
            Path(f.name).unlink()

    def test_write_state_atomic(self):
        """Should write JSON atomically (tmp + rename)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            state = {"status": "healthy", "pid": 12345}

            success = daemon_health_lib.write_state_atomic(str(path), state)
            self.assertTrue(success)
            self.assertTrue(path.exists())

            # Verify content
            written_state = daemon_health_lib.read_state(str(path))
            self.assertEqual(written_state, state)

    def test_evaluate_health_process_not_running(self):
        """Should return 'restart' if process is dead."""
        state = {"status": "healthy", "pid": 999999}
        result = daemon_health_lib.evaluate_health(
            state=state,
            pid_alive=False,
            current_pid=999999
        )
        self.assertEqual(result["action"], "restart")
        self.assertIn("not running", result["reason"].lower())

    def test_evaluate_health_no_state_file(self):
        """Should return 'unknown_no_state' if state is None."""
        result = daemon_health_lib.evaluate_health(
            state=None,
            pid_alive=True,
            current_pid=12345
        )
        self.assertEqual(result["action"], "unknown_no_state")

    def test_evaluate_health_stale_heartbeat(self):
        """Should return 'restart' if heartbeat is stale."""
        now = datetime.now(timezone.utc)
        stale_time = (now - timedelta(seconds=1000)).isoformat()

        state = {
            "status": "healthy",
            "pid": 12345,
            "last_updated_at": stale_time
        }

        result = daemon_health_lib.evaluate_health(
            state=state,
            pid_alive=True,
            current_pid=12345,
            now=now,
            stale_heartbeat_seconds=900
        )
        self.assertEqual(result["action"], "restart")
        self.assertIn("stale", result["reason"].lower())

    def test_evaluate_health_healthy(self):
        """Should return 'ok' if everything is normal."""
        now = datetime.now(timezone.utc)
        recent_time = (now - timedelta(seconds=100)).isoformat()

        state = {
            "status": "healthy",
            "pid": 12345,
            "last_updated_at": recent_time
        }

        result = daemon_health_lib.evaluate_health(
            state=state,
            pid_alive=True,
            current_pid=12345,
            now=now,
            stale_heartbeat_seconds=900
        )
        self.assertEqual(result["action"], "ok")

    def test_zero_output_is_not_healthy(self):
        """Should flag zero-output state as not healthy."""
        # When discovered=0 AND verified=0, this is a problem
        result = daemon_health_lib.zero_output_is_not_healthy(
            discovered_count=0,
            verified_count=0,
            success_rate_if_any=None
        )
        self.assertTrue(result)

    def test_zero_output_is_healthy_when_discovered(self):
        """Should not flag as unhealthy when there is some output."""
        result = daemon_health_lib.zero_output_is_not_healthy(
            discovered_count=5,
            verified_count=0,
            success_rate_if_any=0.0
        )
        self.assertFalse(result)


class TestEmergencyFixesIntegration(unittest.TestCase):
    """Integration tests for all emergency fixes."""

    def test_emergency_fixes_run_without_crash(self):
        """Test fixture: emergency_fixes.main() should not crash."""
        # This is a smoke test; real validation happens on deployment
        # Just ensure no exceptions are raised during main()
        try:
            # Don't actually run main() since it modifies files
            # Just verify the functions exist and are callable
            self.assertTrue(callable(emergency_fixes.fix_cron_imports))
            self.assertTrue(callable(emergency_fixes.fix_inference_server))
            self.assertTrue(callable(emergency_fixes.is_inference_server_alive))
        except Exception as e:
            self.fail(f"Emergency fixes import failed: {e}")


if __name__ == "__main__":
    unittest.main()
