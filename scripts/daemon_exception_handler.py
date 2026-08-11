"""
GATE 1 Issue 3: Exception Handling - Wraps discovery daemon processing
GATE 1 Issue 4: Watchdog Hysteresis - State machine prevents flapping

Integrated module: exception_handler + watchdog work together
- Exception → update health.json with ERROR
- Watchdog reads health.json (not logs) → counts failures
- 1 failure → SUSPICIOUS (no action)
- 3 failures → ERROR (restart needed)
- Persistent state prevents flapping
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Callable, Any, Dict
import logging
import sys

logger = logging.getLogger(__name__)

class DaemonExceptionHandler:
    """Wraps daemon functions with exception logging + health state updates"""
    
    def __init__(self, health_file: str = "/tmp/discovery_daemon.health.json"):
        self.health_file = health_file
    
    def update_health_state(self, state: str, details: str = ""):
        """Update daemon health state (used by exception handlers)"""
        try:
            health_data = {"state": state, "timestamp": datetime.now().isoformat(), "details": details}
            Path(self.health_file).write_text(json.dumps(health_data))
            logger.info(f"✓ Health state updated: {state}")
        except Exception as e:
            logger.error(f"Failed to update health state: {e}")
    
    def safe_batch_processing(self, func: Callable, batch_name: str) -> Callable:
        """
        Decorator: wrap batch processing with exception handling
        
        Usage:
            @handler.safe_batch_processing("discover_websites")
            def discover_websites():
                ...
        """
        def wrapper(*args, **kwargs):
            try:
                logger.info(f"▶ Starting batch: {batch_name}")
                result = func(*args, **kwargs)
                self.update_health_state("HEALTHY")
                logger.info(f"✓ Batch complete: {batch_name}")
                return result
            except Exception as e:
                logger.error(f"❌ Exception in {batch_name}: {e}", exc_info=True)
                self.update_health_state("ERROR", f"Exception: {str(e)[:100]}")
                # Don't re-raise; let watchdog decide on restart
                return None
        
        return wrapper
    
    def safe_org_processing(self, org_processor: Callable) -> Callable:
        """
        Wrap org processing with per-org exception handling
        """
        def wrapper(orgs: list):
            results = []
            for org in orgs:
                try:
                    result = org_processor(org)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Exception processing org {org.get('ein')}: {e}")
                    # Continue processing other orgs (don't fail entire batch)
                    continue
            
            return results
        
        return wrapper

class WatchdogHysteresis:
    """
    State machine for watchdog (prevents restart flapping)
    
    States:
    - HEALTHY: All systems go
    - SUSPICIOUS: 1 failure detected; continue monitoring
    - ERROR: 3 consecutive failures; trigger restart
    - RESTARTING: Restart in progress
    """
    
    def __init__(self, state_file: str = "/tmp/watchdog_state.json"):
        self.state_file = state_file
        self.state_thresholds = {
            "SUSPICIOUS": 1,  # Trigger after 1 failure
            "ERROR": 3        # Trigger after 3 consecutive failures
        }
        self._load_state()
    
    def _load_state(self):
        """Load persistent state from disk"""
        try:
            if Path(self.state_file).exists():
                data = json.loads(Path(self.state_file).read_text())
                self.state = data.get("state", "HEALTHY")
                self.failure_count = data.get("failure_count", 0)
                self.last_failure = data.get("last_failure")
                logger.info(f"✓ Watchdog state loaded: {self.state} ({self.failure_count} failures)")
            else:
                self.state = "HEALTHY"
                self.failure_count = 0
                self.last_failure = None
        except Exception as e:
            logger.warning(f"Failed to load watchdog state: {e}")
            self.state = "HEALTHY"
            self.failure_count = 0
            self.last_failure = None
    
    def _save_state(self):
        """Persist state to disk"""
        try:
            data = {
                "state": self.state,
                "failure_count": self.failure_count,
                "last_failure": self.last_failure
            }
            Path(self.state_file).write_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to save watchdog state: {e}")
    
    def record_failure(self) -> Dict:
        """Record a failure and update state machine"""
        self.failure_count += 1
        self.last_failure = datetime.now().isoformat()
        
        # Hysteresis: move to next state if threshold reached
        if self.failure_count >= self.state_thresholds["ERROR"]:
            self.state = "ERROR"
            self._save_state()
            return {"action": "RESTART", "reason": "3 consecutive failures"}
        elif self.failure_count >= self.state_thresholds["SUSPICIOUS"]:
            self.state = "SUSPICIOUS"
            self._save_state()
            return {"action": "CONTINUE", "reason": "Monitoring closely"}
        
        self._save_state()
        return {"action": "CONTINUE", "reason": "First failure"}
    
    def record_success(self) -> Dict:
        """Record a success; reset failure count"""
        if self.state != "HEALTHY":
            self.failure_count = 0
            self.state = "HEALTHY"
            self._save_state()
            logger.info("✓ Watchdog reset to HEALTHY")
            return {"action": "CONTINUE", "reason": "Recovery confirmed"}
        
        return {"action": "CONTINUE", "reason": "Still healthy"}
    
    def check_stale_failure(self, max_age_minutes: int = 30) -> bool:
        """Check if failures are too old to count (reset if stale)"""
        if not self.last_failure or self.state == "HEALTHY":
            return False
        
        last_failure_time = datetime.fromisoformat(self.last_failure)
        age_minutes = (datetime.now() - last_failure_time).total_seconds() / 60
        
        if age_minutes > max_age_minutes:
            logger.info(f"Watchdog: Failures stale ({age_minutes:.1f}m old), resetting")
            self.failure_count = 0
            self.state = "HEALTHY"
            self._save_state()
            return True
        
        return False

# Test the integrated system
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test exception handler
    handler = DaemonExceptionHandler("/tmp/test_daemon_health.json")
    
    @handler.safe_batch_processing("test_batch")
    def test_batch():
        # Simulate successful processing
        return "Success"
    
    result = test_batch()
    assert result == "Success", "Batch should succeed"
    print("✓ Exception handler: successful batch")
    
    # Test exception in batch
    @handler.safe_batch_processing("failing_batch")
    def failing_batch():
        raise ValueError("Simulated error")
    
    result = failing_batch()
    assert result is None, "Failed batch should return None"
    print("✓ Exception handler: caught exception, updated health")
    
    # Test watchdog hysteresis
    watchdog = WatchdogHysteresis("/tmp/test_watchdog_state.json")
    assert watchdog.state == "HEALTHY", "Should start HEALTHY"
    
    # First failure
    action = watchdog.record_failure()
    assert action["action"] == "CONTINUE", "First failure should continue"
    assert watchdog.state == "SUSPICIOUS", "Should move to SUSPICIOUS"
    print(f"✓ Watchdog: 1st failure → {watchdog.state} (action: {action['action']})")
    
    # Success resets
    action = watchdog.record_success()
    assert watchdog.state == "HEALTHY", "Success should reset to HEALTHY"
    print(f"✓ Watchdog: Success → {watchdog.state} (action: {action['action']})")
    
    # Three failures → restart
    watchdog.failure_count = 0
    watchdog.state = "HEALTHY"
    for i in range(3):
        action = watchdog.record_failure()
    
    assert action["action"] == "RESTART", "Third failure should trigger restart"
    assert watchdog.state == "ERROR", "Should move to ERROR"
    print(f"✓ Watchdog: 3rd failure → {watchdog.state} (action: {action['action']})")
    
    print("\n✅ Exception handler + watchdog hysteresis tests passed")
