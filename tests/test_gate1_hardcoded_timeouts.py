"""
GATE 1 Issue 1: Hardcoded Timeouts
Test-first: Write failing test, then implement fix
"""
import unittest
import time
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, '.')

class TestHardcodedTimeouts(unittest.TestCase):
    """Test that discovery batch timeout is configurable, not hardcoded."""
    
    def test_timeout_respects_config(self):
        """FAILING: Timeout should come from config, not hardcoded"""
        # This test FAILS until we add DISCOVERY_BATCH_TIMEOUT config var
        import os
        
        # Set custom timeout via environment
        os.environ['DISCOVERY_BATCH_TIMEOUT'] = '30'
        
        # Mock a slow API response (simulate slow discovery)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{"verified": 0}'
            mock_run.return_value.returncode = 0
            
            # Try to process batch with custom timeout
            # This should use the env var, not hardcoded 600
            start = time.time()
            try:
                # Import and test the config reading
                from scripts.config import get_discovery_timeout
                timeout = get_discovery_timeout()
                self.assertEqual(timeout, 30, 
                    f"Expected timeout 30 (from env), got {timeout}. "
                    "Hardcoded timeout detected!")
            except ImportError:
                self.fail("EXPECTED FAILURE: Config module doesn't exist yet")
    
    def test_default_timeout_applied(self):
        """FAILING: Default timeout should be 600s if not set"""
        import os
        os.environ.pop('DISCOVERY_BATCH_TIMEOUT', None)
        
        try:
            from scripts.config import get_discovery_timeout
            timeout = get_discovery_timeout()
            self.assertEqual(timeout, 600, 
                f"Default timeout should be 600, got {timeout}")
        except ImportError:
            self.fail("EXPECTED FAILURE: Config module doesn't exist yet")

if __name__ == '__main__':
    # Run tests, expect FAILURES (this is the test-first pattern)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHardcodedTimeouts)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Expected: 2 failures (because we haven't implemented the config yet)
    print(f"\n✓ Test-first pattern: {result.testsRun} tests written")
    print(f"  Failures: {len(result.failures)} (EXPECTED - we haven't coded the fix yet)")
    print(f"  Next step: Implement config reading to make tests pass")
