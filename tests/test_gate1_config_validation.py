"""
GATE 1 Issue 5: Config validation at startup
Test-first: Bad config must block daemon startup immediately
"""
import unittest
import subprocess
import sys
import os

class TestConfigValidation(unittest.TestCase):
    """Config must be validated at daemon startup, fail fast on bad values"""
    
    def test_bad_timeout_blocks_startup(self):
        """FAILING: Invalid timeout should prevent startup"""
        env = os.environ.copy()
        env['DISCOVERY_BATCH_TIMEOUT'] = '-1'  # Invalid
        
        result = subprocess.run(
            [sys.executable, 'scripts/config.py'],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )
        
        # Should fail (exit code 1)
        self.assertNotEqual(result.returncode, 0,
            "Daemon should not start with invalid timeout")
        self.assertIn('ERROR', result.stderr,
            "Error message should be printed for invalid config")
    
    def test_bad_worker_count_blocks_startup(self):
        """FAILING: Worker count >128 should prevent startup"""
        env = os.environ.copy()
        env['DISCOVERY_WORKERS'] = '200'  # Too high
        
        result = subprocess.run(
            [sys.executable, 'scripts/config.py'],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )
        
        self.assertNotEqual(result.returncode, 0,
            "Daemon should not start with invalid worker count")
    
    def test_valid_config_starts_successfully(self):
        """Valid config should pass validation"""
        env = os.environ.copy()
        env['DISCOVERY_BATCH_TIMEOUT'] = '300'
        env['DISCOVERY_WORKERS'] = '48'
        env['DISCOVERY_BATCH_SIZE'] = '2000'
        
        result = subprocess.run(
            [sys.executable, 'scripts/config.py'],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )
        
        self.assertEqual(result.returncode, 0,
            "Valid config should pass validation")
        self.assertIn('300', result.stdout,  # Timeout
            "Output should show validated timeout")
        self.assertIn('48', result.stdout,   # Workers
            "Output should show validated worker count")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfigValidation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n✓ Issue 5 tests written")
    print(f"  Passing: {result.testsRun - len(result.failures)}")
    print(f"  Failing: {len(result.failures)}")
