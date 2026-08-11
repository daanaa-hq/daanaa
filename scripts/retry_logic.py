"""
GATE 1 Issue 6: Exponential backoff retry logic
Handles transient failures, prevents data loss from temporary errors
"""
import time
import logging
from typing import Callable, Any, TypeVar

T = TypeVar('T')
logger = logging.getLogger(__name__)

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
) -> T:
    """
    Retry a function with exponential backoff.
    
    Backoff schedule: 1s, 2s, 4s, 8s (doubling each time)
    Max 3 retries = 4 attempts total
    
    Args:
        func: Callable to retry
        max_retries: Maximum retry attempts (default 3)
        initial_delay: Initial backoff delay in seconds (default 1s)
    
    Returns:
        Result of successful function call
    
    Raises:
        Last exception if all retries fail
    """
    attempt = 0
    delay = initial_delay
    last_exception = None
    
    while attempt <= max_retries:
        try:
            result = func()
            if attempt > 0:
                logger.info(f"Retry successful after {attempt} attempt(s)")
            return result
        except (ConnectionError, TimeoutError, IOError) as e:
            last_exception = e
            attempt += 1
            
            if attempt <= max_retries:
                logger.warning(
                    f"Attempt {attempt} failed ({type(e).__name__}). "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"All {max_retries + 1} attempts failed. Giving up."
                )
    
    raise last_exception

def batch_process_with_retry(orgs: list, processor: Callable) -> int:
    """
    Process a batch of orgs, retrying transient failures.
    
    Args:
        orgs: List of org data to process
        processor: Function that processes org data
    
    Returns:
        Number of orgs successfully processed
    """
    processed = 0
    failed_orgs = []
    
    for i, org in enumerate(orgs):
        try:
            def process_org():
                return processor(org)
            
            retry_with_backoff(process_org, max_retries=3, initial_delay=1.0)
            processed += 1
        except Exception as e:
            logger.error(f"Org {org.get('ein', '?')} processing failed: {e}")
            failed_orgs.append(org)
    
    if failed_orgs:
        logger.warning(f"Failed to process {len(failed_orgs)} orgs after retries")
    
    return processed

if __name__ == '__main__':
    # Test: mock transient error
    attempt_count = 0
    def mock_api():
        global attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ConnectionError("Simulated transient error")
        return {"success": True}
    
    try:
        result = retry_with_backoff(mock_api, max_retries=3, initial_delay=0.1)
        print(f"✓ Retry logic working: {result}")
        print(f"  Succeeded on attempt {attempt_count}")
    except Exception as e:
        print(f"✗ Retry failed: {e}")
