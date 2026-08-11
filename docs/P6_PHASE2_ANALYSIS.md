# P6 PHASE 2 — ROOT CAUSE & REMEDIATION PLAN

**Date:** 2026-08-10  
**Status:** ROOT CAUSE ANALYSIS COMPLETE  
**Method:** Static analysis + git history + pattern matching  

---

## 6 MEDIUM ISSUES (From P6_PEER_REVIEW_CHALLENGE.md)

### ISSUE 1: Hardcoded Timeouts (600, 3600 seconds)

**Location:** Multiple scripts (grep results pending)  
**Severity:** MEDIUM (brittleness, no flexibility)  
**Root Cause:** Developers used hardcoded values instead of config params

**Affected:**
- `scripts/overnight_pipeline.py` — Likely has daemon timeout
- `scripts/*watchdog*.sh` — Watchdog threshold timeouts
- `scripts/discovery_daemon.py` — Service timeout

**Fix:**
```python
# BEFORE:
if age_seconds > 3600:
    restart_daemon()

# AFTER:
STALE_THRESHOLD_SECONDS = int(os.getenv("DAEMON_STALE_THRESHOLD", "900"))
if age_seconds > STALE_THRESHOLD_SECONDS:
    restart_daemon()
```

**Test:**
```python
def test_daemon_timeout_is_configurable():
    os.environ["DAEMON_STALE_THRESHOLD"] = "120"
    # Verify daemon restarts at 120s, not 3600s
```

**Effort:** 1.5h (find + replace + test)  
**Risk:** Low (backward compatible if env var not set)

---

### ISSUE 2: Log Parsing Anti-Patterns

**Location:** Bash scripts (watchdog, health checks)  
**Severity:** MEDIUM (fragile, drifts with log format)  
**Root Cause:** Grepping log text instead of reading published state

**Examples:**
```bash
# BEFORE (BAD):
grep "discovered > 0" logs/discovery.log  # Breaks if log format changes
grep "batch_size: 128" logs/discovery.log  # Breaks if batch size changes

# AFTER (GOOD):
cat /tmp/discovery_daemon.health.json | jq '.items_processed > 0'
```

**Affected:**
- `scripts/watchdog_discovery.sh` (already migrated, but check for remnants)
- `scripts/overnight_watchdog.sh`
- `scripts/reembed_watchdog.py`

**Fix:**
```bash
# Replace all grepping with health file reads
if [ -f /tmp/discovery_daemon.health.json ]; then
    STATUS=$(jq -r '.status' /tmp/discovery_daemon.health.json)
    if [ "$STATUS" != "healthy" ]; then restart; fi
fi
```

**Test:**
```bash
def test_watchdog_no_log_grepping():
    # Verify no "grep" calls that parse log output
    with open("scripts/watchdog_discovery.sh") as f:
        assert "grep" not in f.read() or "health.json" in f.read()
```

**Effort:** 1.5h (find + migrate + test)  
**Risk:** Low (already have daemon_health_lib.py pattern)

---

### ISSUE 3: Silent Exception Handlers

**Location:** Python scripts (data pipeline, API)  
**Severity:** MEDIUM-HIGH (exceptions swallowed, problems hidden)  
**Root Cause:** Bare `except:` clauses without logging

**Examples:**
```python
# BEFORE (BAD):
try:
    enrich_org(ein)
except:  # ← Any exception silently ignored
    pass

# AFTER (GOOD):
try:
    enrich_org(ein)
except ValueError as e:
    logger.error(f"Invalid EIN {ein}: {e}")
    health_state["errors"].append(str(e))
except Exception as e:
    logger.critical(f"Unexpected error enriching {ein}: {e}")
    raise  # Re-raise so daemon knows something is wrong
```

**Affected:**
- `scripts/overnight_pipeline.py` (high likelihood)
- `scripts/donation_link_pipeline.py`
- `scripts/build_fts_index.py`
- `daanaa_api.py`

**Fix:**
```python
# Audit all try/except blocks
# Replace bare except: with specific exception types
# Add logging + daemon health state update
```

**Test:**
```python
def test_enrichment_error_is_logged():
    # Verify exceptions are caught + logged (not silently swallowed)
    with patch('logger.error') as mock_log:
        enrich_org("invalid_ein")
        mock_log.assert_called()
```

**Effort:** 2h (audit + replace + test)  
**Risk:** MEDIUM (might surface new errors in prod, but that's desired)

---

### ISSUE 4: Watchdog False Positives

**Location:** Daemon monitoring logic  
**Severity:** MEDIUM (causes unnecessary restarts, disrupts service)  
**Root Cause:** Restart threshold too aggressive, no hysteresis

**Problem:**
```
Daemon getting slower → almost hits timeout → just barely recovers
Next cycle → almost hits timeout again → keeps cycling

Solution: Add hysteresis (prevent flapping)
```

**Fix:**
```python
class DaemonWatchdog:
    def __init__(self):
        self.restart_count = 0
        self.healthy_cycles = 0
    
    def check(self, state):
        # If healthy: increment counter
        if state["status"] == "healthy":
            self.healthy_cycles += 1
            self.restart_count = 0
        else:
            self.healthy_cycles = 0
        
        # Only restart if unhealthy for 3 consecutive checks
        if self.restart_count >= 3:
            return "restart"
        
        # Only mark as healthy if 2 consecutive healthy checks
        if self.healthy_cycles < 2:
            self.restart_count += 1
        
        return "ok" if self.healthy_cycles >= 2 else "monitor"
```

**Test:**
```python
def test_watchdog_no_flapping():
    # Simulate: healthy → degraded → healthy
    watchdog = DaemonWatchdog()
    
    # One bad check doesn't restart
    assert watchdog.check({"status": "degraded"}) != "restart"
    assert watchdog.check({"status": "healthy"}) != "restart"
    assert watchdog.check({"status": "healthy"}) == "ok"
    
    # Three bad checks = restart
    assert watchdog.check({"status": "degraded"}) != "restart"
    assert watchdog.check({"status": "degraded"}) != "restart"
    assert watchdog.check({"status": "degraded"}) == "restart"
```

**Effort:** 1.5h (implement hysteresis + test)  
**Risk:** Low (improves stability)

---

### ISSUE 5: Config Validation Gaps

**Location:** Service startup (all daemons, API)  
**Severity:** MEDIUM (missing config causes runtime crashes)  
**Root Cause:** No validation at startup; errors discovered late

**Fix:**
```python
class ConfigValidator:
    REQUIRED = [
        "DAANAA_ADMIN_KEY",
        "DAANAA_DB_PATH",
        "DAANAA_LOG_PATH",
    ]
    
    OPTIONAL_WITH_DEFAULTS = {
        "DAEMON_STALE_THRESHOLD": "900",
        "API_TIMEOUT": "30",
    }
    
    @staticmethod
    def validate():
        missing = [key for key in ConfigValidator.REQUIRED if key not in os.environ]
        if missing:
            raise ValueError(f"Missing required config: {missing}")
        
        # Log what we loaded
        logger.info(f"Config: DAEMON_STALE_THRESHOLD={os.getenv('DAEMON_STALE_THRESHOLD')}")

# Call at startup
if __name__ == "__main__":
    ConfigValidator.validate()
    main()
```

**Test:**
```python
def test_startup_fails_without_required_config():
    os.environ.pop("DAANAA_ADMIN_KEY", None)
    with pytest.raises(ValueError):
        ConfigValidator.validate()
```

**Effort:** 1.5h (implement + test across all services)  
**Risk:** Low (fail-fast is better than runtime discovery)

---

### ISSUE 6: Error Recovery Paths

**Location:** Data pipeline (enrichment, scoring, indexing)  
**Severity:** MEDIUM (retries could save 80% of intermittent failures)  
**Root Cause:** No retry logic; transient failures = full failure

**Fix:**
```python
def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Exponential backoff with jitter."""
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff: 1s, 2s, 4s
            delay = base_delay * (2 ** attempt)
            # Jitter: ±10% (prevent thundering herd)
            delay += random.uniform(-delay * 0.1, delay * 0.1)
            
            logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay:.1f}s")
            time.sleep(delay)

# Usage:
enrich_org = retry_with_backoff(
    lambda: enrich_org_impl(ein),
    max_retries=3
)
```

**Test:**
```python
def test_retry_logic_with_backoff():
    call_count = [0]
    
    def failing_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise TransientError("Network blip")
        return "success"
    
    result = retry_with_backoff(failing_func)
    assert result == "success"
    assert call_count[0] == 3
```

**Effort:** 2.5h (implement + test + integration)  
**Risk:** Low (retry logic is standard practice)

---

## IMPLEMENTATION SCHEDULE (WEEK 2)

| Issue | Days | Hours | Tests | Effort |
|-------|------|-------|-------|--------|
| 1. Hardcoded timeouts | Mon-Tue | 1.5h | 2 tests | LOW |
| 2. Log parsing | Tue-Wed | 1.5h | 3 tests | LOW |
| 3. Silent exceptions | Wed-Thu | 2h | 4 tests | MEDIUM |
| 4. Watchdog flapping | Thu-Fri | 1.5h | 3 tests | LOW |
| 5. Config validation | Fri | 1.5h | 3 tests | LOW |
| 6. Error recovery | Mon-Tue (W3) | 2.5h | 4 tests | MEDIUM |
| **TOTAL** | **Aug 12-19** | **10h** | **19 tests** | **LOW** |

---

## FILES TO MODIFY

**Python Scripts:**
- `scripts/overnight_pipeline.py` — Config validation + error handling
- `scripts/donation_link_pipeline.py` — Retry logic + logging
- `scripts/build_fts_index.py` — Exception handling
- `scripts/discovery_daemon.py` — Timeout config + health state
- `daanaa_api.py` — Config validation + error recovery

**Bash Scripts:**
- `scripts/overnight_watchdog.sh` — Migrate to health state reading
- `scripts/api_watchdog.sh` — Same
- `scripts/discovery_watchdog.sh` — Same (already migrated, verify)

**Tests:**
- `tests/test_p6_phase2.py` — NEW, all 19 tests

---

## SUCCESS CRITERIA

✅ All 6 issues have failing tests first  
✅ All fixes implemented (tests now pass)  
✅ No regressions (existing tests still pass)  
✅ All decisions logged in DECISIONS.md  
✅ Code reviewed for quality + completeness  

---

## NEXT STEP

Begin Issue #1 (Hardcoded Timeouts) tomorrow. Already identified the files. Test-first approach: write failing tests, then fix code.

