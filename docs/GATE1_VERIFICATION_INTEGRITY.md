# GATE 1: Verification Integrity (P3, P6)

**Timeline:** Aug 12-23 (2 weeks, test-first, 10h of work)  
**Blocker:** None (Gate 0 passes = proceed)  
**Unlocker:** Search quality audit (Gate 3), scoring transparency  

---

## Pass Criteria

- [x] All 6 P6 Phase 2 issues fixed + tested
- [ ] Silent exceptions eliminated (full error propagation)
- [ ] Config validation enforced at startup
- [ ] Retry logic + exponential backoff working
- [ ] Hardcoded timeouts replaced with config
- [ ] Health state machine working (no flapping)

---

## Issues to Fix (Priority Order)

### Issue 1: Hardcoded Timeouts (1.5h, test-first)
**Location:** daanaa_api.py:47-51, scripts/discovery_daemon.py:312  
**Problem:** 600s timeout for batch, no config override  
**Test-First:** Write failing test that mocks slow API (10s response)  
**Fix:** Add config var DISCOVERY_BATCH_TIMEOUT, default 600s  
**Verify:** Test passes with 10s mock, 5min real API  

### Issue 2: Log Parsing → Health.json (1.5h)
**Location:** watchdog_discovery.sh uses grep  
**Problem:** Silent breakage when log format changes  
**Test-First:** Mock different log formats, verify watchdog detects stale state  
**Fix:** Switch to daemon_health_lib.py (published state, not grep)  
**Verify:** Watchdog catches hanging daemon in 2x normal detection time  

### Issue 3: Silent Exceptions (2h)
**Location:** discovery_daemon.py error handlers silently catch errors  
**Problem:** No alert when batch fails  
**Test-First:** Inject exception in batch processing, verify it's logged  
**Fix:** Propagate exception, log stack trace, update health state to ERROR  
**Verify:** Exception log + health state change both recorded  

### Issue 4: Watchdog Flapping (1.5h)
**Location:** watchdog_discovery.sh restarts daemon every 10min on edge cases  
**Problem:** False restarts cause data loss  
**Test-First:** Create state machine: HEALTHY→SUSPICIOUS (3 checks)→ERROR→RESTART  
**Fix:** Add hysteresis (must fail 3 consecutive checks before restart)  
**Verify:** Transient failures don't trigger restart  

### Issue 5: Config Validation (1.5h)
**Location:** config.py reads env vars without validation  
**Problem:** Bad config values silently used  
**Test-First:** Pass invalid timeout (-1), verify error at startup  
**Fix:** Validate all config at daemon startup, fail fast  
**Verify:** Bad config blocks daemon startup  

### Issue 6: Error Recovery (2.5h)
**Location:** discovery_daemon.py, batch retry logic missing  
**Problem:** Transient failures lose orgs  
**Test-First:** Mock transient API error, verify retry succeeds  
**Fix:** Implement exponential backoff (1s, 2s, 4s, 8s) + max 3 retries  
**Verify:** 1000 org batch with 1 transient error → all 1000 recover  

---

## Execution Plan

**Aug 12-14 (3 days, parallel with Gate 3 Phase 2-3):**
- Issues 1, 2, 5 (config, timeouts, health.json)
- Write tests FIRST (6 failing tests)
- Fix + verify (3 tests pass)

**Aug 15-16 (2 days, parallel with Gate 3 complete):**
- Issues 3, 4 (exceptions, hysteresis)
- Write tests FIRST (6 failing tests)
- Fix + verify (3 tests pass)

**Aug 17-19 (3 days, parallel with Gate 0 complete):**
- Issue 6 (retry logic)
- Write tests FIRST (3 failing tests)
- Fix + verify (3 tests pass)
- Integration test: 100-org batch with random transient errors

**Aug 20-23 (4 days, buffer):**
- Full test suite run
- Smoke tests on droplet
- Documentation + DECISIONS.md entry

---

## Evidence Required for Gate 1 PASS

- [ ] 19 unit tests all passing (tests/test_p6_phase2_fixes.py)
- [ ] 0 flapping watchdog restarts in 72h monitoring (Aug 20-23)
- [ ] Zero silent exceptions in logs (Aug 20-23)
- [ ] Config validation blocks bad startup (demo)
- [ ] Retry logic recovers from transient failures (demo)

---

## Dates

- **Parallel with:** Gate 3 (Aug 12-14), Gate 0 complete (Aug 17)
- **Blocks:** None (unblocks downstream)
- **Unblocked by:** Gate 0 passing (Aug 17)

