"""
GATE 1 Issue 5: Config Validation - Fail-fast on invalid daemon config
GATE 1 Issue 6: Retry Logic - Exponential backoff (1s, 2s, 4s, 8s max)

Ensures daemon starts with valid config or exits immediately;
retries transient failures without retry storms
"""
import os
import time
import logging
from typing import Tuple, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class DaemonConfig:
    """Daemon configuration with validation"""
    
    REQUIRED_KEYS = ['timeout_seconds', 'workers', 'batch_size']
    VALID_RANGES = {
        'timeout_seconds': (10, 3600),      # 10s to 1h
        'workers': (1, 128),                 # 1 to 128
        'batch_size': (10, 10000),           # 10 to 10k orgs per batch
    }
    
    def __init__(self):
        """Load config from environment, fail-fast if invalid"""
        self.config = {}
        self.errors = []
        self._load_from_env()
        self._validate()
    
    def _load_from_env(self):
        """Load config from environment variables"""
        # Read from env with defaults
        self.config = {
            'timeout_seconds': int(os.environ.get('DAEMON_TIMEOUT', '300')),
            'workers': int(os.environ.get('DAEMON_WORKERS', '8')),
            'batch_size': int(os.environ.get('DAEMON_BATCH_SIZE', '1000')),
        }
        logger.info(f"Config loaded: timeout={self.config['timeout_seconds']}s, workers={self.config['workers']}, batch_size={self.config['batch_size']}")
    
    def _validate(self):
        """Validate config, collect errors"""
        # Check required keys
        for key in self.REQUIRED_KEYS:
            if key not in self.config:
                self.errors.append(f"Missing required config: {key}")
        
        # Check value ranges
        for key, (min_val, max_val) in self.VALID_RANGES.items():
            if key in self.config:
                value = self.config[key]
                if not (min_val <= value <= max_val):
                    self.errors.append(f"{key}={value} out of range [{min_val}, {max_val}]")
        
        # Fail-fast on validation errors
        if self.errors:
            for error in self.errors:
                logger.error(f"❌ Config error: {error}")
            raise ValueError(f"Invalid daemon config: {'; '.join(self.errors)}")
        
        logger.info("✓ Config validation passed")
    
    def get(self, key: str) -> Any:
        """Get config value"""
        return self.config.get(key)
    
    def is_valid(self) -> bool:
        """Check if config is valid"""
        return len(self.errors) == 0

class RetryLogic:
    """Exponential backoff retry logic for transient failures"""
    
    def __init__(self, max_retries: int = 3):
        """
        max_retries: max attempts (total = 1 + max_retries)
        Backoff: 1s, 2s, 4s, 8s max
        """
        self.max_retries = max_retries
        self.backoff_delays = [1, 2, 4, 8]  # Exponential: 2^n seconds
    
    def retry(self, func: Callable, *args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute function with retry logic
        
        Returns: (success, result, error_message)
        """
        for attempt in range(1 + self.max_retries):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"✓ Recovered after {attempt} retry(ies)")
                return True, result, None
            except Exception as e:
                error_msg = str(e)
                
                if attempt < self.max_retries:
                    # Transient failure: retry
                    delay = self.backoff_delays[min(attempt, len(self.backoff_delays) - 1)]
                    logger.warning(f"⚠️  Attempt {attempt + 1} failed: {error_msg}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    # Final failure: give up
                    logger.error(f"❌ All {1 + self.max_retries} attempts failed: {error_msg}")
                    return False, None, error_msg
        
        return False, None, "Unknown error"
    
    def batch_process_with_retry(self, items: list, processor: Callable) -> Tuple[int, int]:
        """
        Process batch of items with retry for each item
        
        Returns: (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for item in items:
            success, result, error = self.retry(processor, item)
            if success:
                successful += 1
            else:
                failed += 1
                logger.warning(f"Failed to process item: {error}")
        
        return successful, failed

# Test both components
if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Test 1: Config validation with valid env
    print("Test 1: Config validation (valid)")
    os.environ['DAEMON_TIMEOUT'] = '300'
    os.environ['DAEMON_WORKERS'] = '8'
    os.environ['DAEMON_BATCH_SIZE'] = '1000'
    
    try:
        config = DaemonConfig()
        assert config.is_valid(), "Config should be valid"
        print("✓ Valid config accepted")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Test 2: Config validation with invalid values
    print("\nTest 2: Config validation (invalid timeout)")
    os.environ['DAEMON_TIMEOUT'] = '5'  # Below minimum
    
    try:
        config = DaemonConfig()
        print("❌ Should have rejected invalid timeout")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Rejected invalid config: {e}")
    
    # Test 3: Retry logic with transient failure
    print("\nTest 3: Retry logic (transient failure)")
    
    attempt_count = [0]
    
    def flaky_function():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ConnectionError("Transient network error")
        return "Success"
    
    retry = RetryLogic(max_retries=3)
    success, result, error = retry.retry(flaky_function)
    
    assert success and result == "Success", "Should succeed after retries"
    print(f"✓ Retry succeeded: {result} (took {attempt_count[0]} attempts)")
    
    # Test 4: Retry logic with permanent failure
    print("\nTest 4: Retry logic (permanent failure)")
    
    def always_fails():
        raise ValueError("Permanent error")
    
    retry = RetryLogic(max_retries=2)
    success, result, error = retry.retry(always_fails)
    
    assert not success, "Should fail after all retries"
    assert "Permanent error" in error, "Should report error"
    print(f"✓ Permanent failure detected: {error}")
    
    # Test 5: Batch processing with retry
    print("\nTest 5: Batch processing with retry")
    
    def process_org(org_ein):
        if org_ein == "111111111":
            raise ConnectionError("Network error")
        return f"Processed {org_ein}"
    
    retry = RetryLogic(max_retries=1)
    orgs = ["222222222", "111111111", "333333333"]
    
    successful, failed = retry.batch_process_with_retry(orgs, process_org)
    
    assert successful >= 2, "Should process at least 2 items"
    print(f"✓ Batch processing: {successful} successful, {failed} failed")
    
    print("\n✅ All config validation and retry logic tests passed")
