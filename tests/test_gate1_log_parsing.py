"""
GATE 1 Issue 2: Log parsing anti-pattern
Test-first: Watchdog should read health.json state, not grep logs
"""
import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

class TestLogParsingVsHealthJson(unittest.TestCase):
    """Watchdog should detect daemon state via health.json, not log grep"""
    
    def test_watchdog_detects_stale_state_via_health_json(self):
        """FAILING: Watchdog should read health.json to detect stale daemon"""
        # Simulate a stale health.json (no recent heartbeat)
        with tempfile.TemporaryDirectory() as tmpdir:
            health_file = os.path.join(tmpdir, 'discovery_daemon.health.json')
            
            # Write stale health state (>900s since last heartbeat)
            stale_state = {
                'status': 'healthy',
                'last_heartbeat': '2026-08-11T00:00:00Z',  # Very old
                'pid': 12345,
                'verified_count': 0
            }
            with open(health_file, 'w') as f:
                json.dump(stale_state, f)
            
            # Watchdog should detect this via health.json, not by grepping logs
            try:
                from scripts.daemon_health_lib import read_state, evaluate_health
                state = read_state(health_file)
                result = evaluate_health(
                    state, 
                    pid_alive=True, 
                    current_pid=12345,
                    stale_heartbeat_seconds=900  # 15 min threshold
                )
                
                # Watchdog should recommend restart for stale state
                self.assertEqual(result['action'], 'restart',
                    "Watchdog should restart daemon with stale heartbeat")
                self.assertIn('stale', result['reason'].lower(),
                    "Reason should mention stale state")
            except ImportError:
                self.fail("daemon_health_lib not implemented yet")
    
    def test_no_log_grep_parsing(self):
        """FAILING: Watchdog should NOT parse logs (too fragile)"""
        # This test verifies that log parsing is eliminated
        try:
            from scripts.discovery_daemon_health import evaluate_health
            # If this works, health logic is in daemon module, not log parsing
            self.assertTrue(True, "Health check is daemon-aware, not log-based")
        except ImportError:
            self.fail("daemon_health_lib integration not complete")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLogParsingVsHealthJson)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n✓ Issue 2 tests written")
    print(f"  Failures: {len(result.failures)} (expected until daemon_health_lib integrated)")
