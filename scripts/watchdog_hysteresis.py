"""
GATE 1 Issue 4: Watchdog Flapping Prevention
Hysteresis: HEALTHY → SUSPICIOUS (3 checks) → ERROR → RESTART
Prevents false restarts from single transient failures
"""
import json
from typing import Literal
from pathlib import Path

Health = Literal["healthy", "suspicious", "error"]

class WatchdogStateMachine:
    """
    State machine to prevent watchdog flapping.
    
    States:
      healthy → suspicious (1 failed check)
      suspicious → healthy (1 passed check)
      suspicious → error (3 consecutive failed checks)
      error → restart
    """
    
    def __init__(self, state_file: str = "/tmp/watchdog_state.json"):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        if Path(self.state_file).exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "status": "healthy",
            "consecutive_failures": 0,
            "restart_count": 0
        }
    
    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)
    
    def check_health(self, is_healthy: bool) -> str:
        """
        Report a health check result.
        
        Args:
            is_healthy: Result of health check (True = daemon ok, False = daemon failed)
        
        Returns:
            Action: 'continue' or 'restart'
        """
        if is_healthy:
            # Passed check: reset to healthy, zero failures
            self.state["status"] = "healthy"
            self.state["consecutive_failures"] = 0
            self._save_state()
            return "continue"
        
        # Failed check
        self.state["consecutive_failures"] += 1
        
        if self.state["consecutive_failures"] == 1:
            # First failure: move to SUSPICIOUS
            self.state["status"] = "suspicious"
            self._save_state()
            return "continue"  # Don't restart yet
        
        elif self.state["consecutive_failures"] < 3:
            # 2nd failure: stay SUSPICIOUS
            self._save_state()
            return "continue"  # Still no restart
        
        else:
            # 3+ failures: move to ERROR and restart
            self.state["status"] = "error"
            self.state["restart_count"] += 1
            self._save_state()
            return "restart"

if __name__ == '__main__':
    # Test hysteresis
    watchdog = WatchdogStateMachine("/tmp/test_watchdog_state.json")
    
    print("Testing watchdog hysteresis...")
    print(f"Initial state: {watchdog.state['status']}")
    
    # Scenario: single transient failure (should NOT restart)
    result1 = watchdog.check_health(False)
    print(f"Check 1 (fail): {result1} (state: {watchdog.state['status']})")
    assert result1 == "continue", "Single failure should not trigger restart"
    
    # Recovery
    result2 = watchdog.check_health(True)
    print(f"Check 2 (pass): {result2} (state: {watchdog.state['status']})")
    assert result2 == "continue", "Recovery should keep running"
    assert watchdog.state['status'] == "healthy", "Should return to healthy"
    
    # Scenario: 3 consecutive failures (SHOULD restart)
    for i in range(3):
        result = watchdog.check_health(False)
        print(f"Check {i+1} (fail): {result} (state: {watchdog.state['status']})")
    
    assert watchdog.state["consecutive_failures"] == 3, "Should count 3 failures"
    assert result == "restart", "3 failures should trigger restart"
    print("✓ Hysteresis working: single failure no-op, 3 failures trigger restart")
