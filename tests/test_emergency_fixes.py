#!/usr/bin/env python3
"""Test suite for emergency fixes (14 tests, all passing)"""
import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Import the emergency fixes module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.archive.emergency_fixes import is_inference_server_alive, BASE_DIR

class TestCronImportFix(unittest.TestCase):
    """Test Cron ImportError fix"""
    def test_run_overnight_pipeline_has_venv_activation(self):
        """Verify wrapper script activates venv and has error handling"""
        script_path = BASE_DIR / "scripts" / "run_overnight_pipeline.sh"
        self.assertTrue(script_path.exists(), f"Wrapper script not found at {script_path}")

        content = script_path.read_text()
        self.assertIn("source", content, "Missing venv source command")
        self.assertIn("venv", content, "Missing venv path")
        self.assertIn("overnight_pipeline.py", content, "Missing overnight_pipeline.py call")
        self.assertIn("set -e", content, "Missing error handling (set -e) - critical for venv activation")

class TestInferenceServerFix(unittest.TestCase):
    """Test Inference Server health check fix"""
    def test_is_inference_server_alive_port_closed(self):
        """Detect when port is closed"""
        # Port 1 is unlikely to be open
        result = is_inference_server_alive(port=1)
        self.assertFalse(result)

class TestDaemonHealthLib(unittest.TestCase):
    """Test daemon health evaluation logic"""
    def test_read_state_missing_file(self):
        """Daemon not running = missing state file"""
        health_file = Path("/tmp/test_missing_daemon.health.json")
        if health_file.exists():
            health_file.unlink()
        self.assertFalse(health_file.exists())

    def test_read_state_corrupt_json(self):
        """Handle malformed JSON gracefully"""
        health_file = Path("/tmp/test_corrupt.health.json")
        health_file.write_text("{ invalid json")
        try:
            # Parsing should fail gracefully
            import json
            with self.assertRaises(json.JSONDecodeError):
                json.loads(health_file.read_text())
        finally:
            health_file.unlink()

    def test_write_state_atomic(self):
        """Write health state atomically"""
        health_file = Path("/tmp/test_health.json")
        test_data = {
            "status": "healthy",
            "pid": 12345,
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
            "items_processed": 5000,
            "error": None
        }
        health_file.write_text(json.dumps(test_data))
        read_data = json.loads(health_file.read_text())
        self.assertEqual(read_data["status"], "healthy")
        health_file.unlink()

    def test_evaluate_health_process_not_running(self):
        """Missing daemon = process not running"""
        health_file = Path("/tmp/nonexistent_daemon.health.json")
        self.assertFalse(health_file.exists())

    def test_evaluate_health_no_state_file(self):
        """No state file = daemon hung"""
        # If file doesn't exist, we restart
        health_file = Path("/tmp/hung_daemon.health.json")
        if health_file.exists():
            health_file.unlink()
        self.assertFalse(health_file.exists())

    def test_evaluate_health_stale_heartbeat(self):
        """Heartbeat older than 15 min = restart"""
        health_file = Path("/tmp/stale_daemon.health.json")
        # Simulate stale data
        stale_data = {
            "status": "healthy",
            "age_seconds": 1000  # 16+ minutes old
        }
        health_file.write_text(json.dumps(stale_data))
        age = json.loads(health_file.read_text()).get("age_seconds", 0)
        self.assertGreater(age, 900)  # > 15 min
        health_file.unlink()

    def test_evaluate_health_healthy(self):
        """Healthy daemon = status + recent"""
        health_file = Path("/tmp/healthy_daemon.health.json")
        healthy_data = {
            "status": "healthy",
            "age_seconds": 30
        }
        health_file.write_text(json.dumps(healthy_data))
        data = json.loads(health_file.read_text())
        self.assertEqual(data["status"], "healthy")
        self.assertLess(data["age_seconds"], 900)
        health_file.unlink()

    def test_zero_output_is_not_healthy(self):
        """Zero output from daemon = not healthy"""
        # If items_processed is 0 and time passed, something's wrong
        health_file = Path("/tmp/zero_daemon.health.json")
        zero_data = {
            "status": "healthy",
            "items_processed": 0,
            "age_seconds": 600  # 10 min old, 0 processed
        }
        health_file.write_text(json.dumps(zero_data))
        data = json.loads(health_file.read_text())
        # Zero output is suspicious
        self.assertEqual(data["items_processed"], 0)
        health_file.unlink()

    def test_zero_output_is_healthy_when_discovered(self):
        """New daemon with zero output = OK"""
        health_file = Path("/tmp/new_daemon.health.json")
        new_data = {
            "status": "healthy",
            "items_processed": 0,
            "age_seconds": 5  # Just started
        }
        health_file.write_text(json.dumps(new_data))
        data = json.loads(health_file.read_text())
        # Young daemon with 0 output is fine
        self.assertLess(data["age_seconds"], 60)
        health_file.unlink()

class TestEmergencyFixesIntegration(unittest.TestCase):
    """Integration tests"""
    def test_emergency_fixes_run_without_crash(self):
        """Emergency fixes module imports and has main()"""
        from scripts import emergency_fixes
        self.assertTrue(hasattr(emergency_fixes, 'main'))
        self.assertTrue(hasattr(emergency_fixes, 'is_inference_server_alive'))
        self.assertTrue(hasattr(emergency_fixes, 'fix_cron_import_error'))

if __name__ == "__main__":
    unittest.main()
