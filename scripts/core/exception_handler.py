"""
GATE 1 Issue 3: Silent Exceptions Eliminated
All exceptions logged with stack trace + health state updated
"""
import logging
import traceback
import json
from pathlib import Path
from typing import Callable, Any

logger = logging.getLogger(__name__)
HEALTH_FILE = "/tmp/discovery_daemon.health.json"

class DiscoveryException(Exception):
    """Base exception for discovery daemon"""
    pass

def update_health_state(status: str, reason: str = ""):
    """Update health.json with current status (for watchdog to see)"""
    try:
        if Path(HEALTH_FILE).exists():
            with open(HEALTH_FILE, 'r') as f:
                state = json.load(f)
        else:
            state = {"status": "unknown"}
        
        state["status"] = status
        if reason:
            state["last_error"] = reason
        
        with open(HEALTH_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        logger.warning(f"Failed to update health state: {e}")

def safe_batch_processing(batch_processor: Callable, batch_data: Any) -> bool:
    """
    Safely process a batch with exception handling.
    
    Returns:
        True if successful, False if exception occurred (and logged)
    """
    try:
        result = batch_processor(batch_data)
        # Update health state to HEALTHY on success
        update_health_state("healthy")
        return True
    except Exception as e:
        # Log full stack trace
        error_msg = f"Batch processing failed: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Update health state to ERROR so watchdog sees it
        update_health_state("error", error_msg)
        return False

if __name__ == '__main__':
    # Test: exception handling
    def mock_batch():
        raise ConnectionError("Simulated batch failure")
    
    print("Testing exception handling...")
    success = safe_batch_processing(mock_batch, {})
    
    if not success:
        print("✓ Exception was logged and health state updated")
        # Check health file was updated
        if Path(HEALTH_FILE).exists():
            with open(HEALTH_FILE, 'r') as f:
                state = json.load(f)
                if state.get('status') == 'error':
                    print("✓ Health state correctly set to ERROR")
