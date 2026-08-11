# Codex Security Review — Remediation Checklist
**Date:** Aug 11, 2026 | **Reviewer:** Codex | **Status:** IN PROGRESS

## 5 SHIPPING BLOCKERS

### PRIORITY 1: CRITICAL SECURITY FLAWS (Ship-blocking)

#### ❌ Issue 1: org_claims_verification.py — Token Security
**Codex finding:** Tokens stored plaintext; no email sending; attempt_count broken

**Fixes Required:**
- [ ] Hash tokens with SHA256 (store hash as PK, plaintext only in URL)
- [ ] Implement email sending integration (SendGrid/SES/SMTP)
- [ ] Fix attempt_count increment logic (currently never incremented)
- [ ] Add CSRF token to verification URL
- [ ] Replace datetime.utcnow() → datetime.now(timezone.utc)
- [ ] Add rate limiting on token generation (prevent email spam)

**Test suite:**
- [ ] Token hash validation
- [ ] Email dispatch confirmation
- [ ] Brute force blocked after 5 attempts
- [ ] CSRF token validated on verification click
- [ ] Attempt counter increments correctly

**Owner:** Me (Claude) | **ETA:** 4 hours | **Status:** NOT STARTED

---

#### ❌ Issue 2: admin_key_validator.py — Timing Attack
**Codex finding:** Early exit on length mismatch leaks key length via response time

**Fixes Required:**
- [ ] Rewrite constant-time compare to read full length always
- [ ] Persist failed_attempts to SQLite (survive restart)
- [ ] Add cleanup task for stale attempts (>1h old)
- [ ] Add audit logging for all admin access (success + failure)
- [ ] Add key rotation mechanism (env var swap without restart)

**Test suite:**
- [ ] Constant-time compare passes Codex test (no early exit)
- [ ] Failed attempts persist across app restart
- [ ] Stale attempts cleaned up after 1h
- [ ] All admin endpoints logged with timestamp + success/failure
- [ ] Key rotation doesn't break in-flight requests

**Owner:** Me (Claude) | **ETA:** 2 hours | **Status:** NOT STARTED

---

#### ❌ Issue 3: rate_limiter.py — Ephemeral State
**Codex finding:** In-memory dict resets on restart; allows bypass via DoS+restart

**Fixes Required:**
- [ ] Migrate to Redis persistence (or SQLite for fallback)
- [ ] Add bucket state TTL (auto-cleanup after 1h)
- [ ] Implement background cleanup task
- [ ] Add metrics/instrumentation (log all rate-limit events)
- [ ] Tighten client fingerprint (IP-based, not IP+UA)
- [ ] Adjust limits (50 req/s for /api/search may be too tight for aggregators)

**Test suite:**
- [ ] Rate-limit state persists across restart
- [ ] Stale buckets auto-cleaned after 1h
- [ ] Rate-limit events logged to metrics
- [ ] Client ID is stable (IP-only)
- [ ] Endpoints that should be tighter (admin) are tighter

**Owner:** Me (Claude) | **ETA:** 3 hours | **Status:** NOT STARTED

---

### PRIORITY 2: NON-FUNCTIONAL CODE (Blocking Gate launches)

#### ❌ Issue 4: gpu_night_orchestration.sh — Mock Data
**Codex finding:** Runs on fake results; doesn't call real discovery_daemon

**Fixes Required:**
- [ ] Replace mock calculation with real discovery_daemon.py call
- [ ] Add GPU load threshold check (skip if GPU >90%)
- [ ] Implement watchdog (restart if batch hangs >8h)
- [ ] Replace bash loop with systemd timer (more robust)
- [ ] Add real-time progress logging (batch N of 4 complete)

**Test suite:**
- [ ] Script calls discovery_daemon.py (not mock calculation)
- [ ] GPU load checked before launch
- [ ] Watchdog detects hung batch and kills after 8h
- [ ] Progress logged to discoverynight.log
- [ ] Completion status returns actual discovered count

**Owner:** Me (Claude) | **ETA:** 2 hours | **Status:** NOT STARTED

---

#### ❌ Issue 5: gate3_search_benchmark.py — Fake Ground Truth
**Codex finding:** Hardcoded fake EINs (111111111); mock results; can't validate Gate 3

**Fixes Required:**
- [ ] Query real production EINs for ground truth (100+ queries)
- [ ] Replace mock results with live API calls to /api/search
- [ ] Add latency measurement (p50, p99, p99.9)
- [ ] Implement alerting (email if precision drops below 85%)
- [ ] Persist results to DB for trend analysis
- [ ] Document benchmark methodology (reproducibility)

**Test suite:**
- [ ] Query uses real EINs from production DB
- [ ] Results from real /api/search endpoint (not mock)
- [ ] Latency measured and reported
- [ ] Alert triggered if precision <85%
- [ ] Results persisted with timestamp + query set version

**Owner:** Codex (needs to curate real EIN ground truth) + Me (API integration) | **ETA:** 3 hours | **Status:** BLOCKED (waiting for EIN dataset)

---

### PRIORITY 3: PRODUCTION HARDENING (Ship-ready with fixes)

#### ⚠️ Issue 6: error_handler.py — Production Logging
**Codex finding:** No production logging; in-memory only; deprecated datetime

**Fixes Required:**
- [ ] Integrate CloudLogging (Google Cloud Logging)
- [ ] Scrub stack traces (remove local variable values)
- [ ] Replace datetime.utcnow() → datetime.now(timezone.utc)
- [ ] Increase error ID from 8 to 16 hex chars (collision resistance)
- [ ] Add error categorization (retryable vs. fatal)

**Test suite:**
- [ ] Errors logged to CloudLogging (not stdout)
- [ ] Stack traces scrubbed of variable values
- [ ] Error ID is 16+ chars
- [ ] Error categorization applied
- [ ] Dev mode still includes full traceback

**Owner:** Me (Claude) | **ETA:** 2 hours | **Status:** NOT STARTED

---

#### ⚠️ Issue 7: daemon_exception_handler.py — State Persistence
**Codex finding:** Health file world-readable; state lost on reboot

**Fixes Required:**
- [ ] Move health files to /var/run/daanaa/ (perms 0600)
- [ ] Persist state to SQLite (survive restarts)
- [ ] Add file locking on state writes (fcntl.flock)
- [ ] Add config for thresholds (1 suspicious, 3 error)
- [ ] Document separation of concerns (handler vs watchdog)

**Test suite:**
- [ ] Health files in /var/run/daanaa/ with 0600 perms
- [ ] State persists across daemon restart
- [ ] File lock prevents corruption on concurrent writes
- [ ] Thresholds configurable via env var
- [ ] Watchdog correctly reads persisted state

**Owner:** Me (Claude) | **ETA:** 2 hours | **Status:** NOT STARTED

---

#### ⚠️ Issue 8: input_validator.py — RFC Compliance
**Codex finding:** Email/URL regex too restrictive; no Unicode normalization

**Fixes Required:**
- [ ] Use email-validator library (RFC 5322 compliant)
- [ ] Use urllib.parse.urlparse (handles IDN, fragments)
- [ ] Add Unicode normalization (NFC) to prevent homograph attacks
- [ ] Document NTEE pattern limitations
- [ ] Add field-specific integer validators

**Test suite:**
- [ ] Email validation accepts `user+tag@sub.example.com`
- [ ] URL validation accepts international domains
- [ ] Homograph attack (ä vs a+diacritic) normalized
- [ ] Integer validators field-specific (not one-size-fits-all)

**Owner:** Me (Claude) | **ETA:** 1 hour | **Status:** NOT STARTED

---

#### ⚠️ Issue 9: analytics_privacy.py — Pattern Gaps
**Codex finding:** EIN unformatted missed; zip code exception too broad; false positives

**Fixes Required:**
- [ ] Add `\d{9}` pattern for unformatted EINs
- [ ] Restrict zip code exception to "country"/"region" only
- [ ] Tighten email regex (require 2+ letter TLD)
- [ ] Anchor IP pattern (prevent false positives on version strings)
- [ ] Add sampling/threshold for validation rate-limiting

**Test suite:**
- [ ] EIN detection catches both formats (12-3456789 and 123456789)
- [ ] Zip code only flagged outside "country"/"region"
- [ ] Email regex accepts standard formats, rejects "v@1.2.3"
- [ ] IP pattern anchored (doesn't match version strings)
- [ ] Validation rate-limited to reasonable threshold

**Owner:** Me (Claude) | **ETA:** 45 min | **Status:** NOT STARTED

---

#### ✅ Issue 10: daemon_config_retry.py — Ready (Minor Fixes)
**Codex finding:** Ready to ship; add jitter and error handling

**Fixes Required:**
- [ ] Add random jitter (±10%) to backoff delays
- [ ] Document max backoff (30s constant)
- [ ] Improve error message on env var parse failure
- [ ] Remove dead REQUIRED_KEYS code

**Test suite:**
- [ ] Jitter applied to delays (uniform distribution)
- [ ] Max backoff never exceeds 30s
- [ ] Invalid env var produces clear error message

**Owner:** Me (Claude) | **ETA:** 45 min | **Status:** NOT STARTED

---

## DEPENDENCY MAP

```
Issue 5 (Gate3 benchmark) BLOCKED ON → Real EIN ground truth dataset
Issue 4 (GPU orchestrator) BLOCKED ON → Nothing (can fix immediately)
Issue 1 (Org claims) BLOCKED ON → Email service decision (SendGrid/SES/SMTP)
Issues 2-3, 6-10 READY → Can fix now
```

## TIMELINE

**Today (Aug 11):** 
- [ ] Fix Issues 2, 3, 4, 6, 7, 8, 9, 10 (14 hours, can run parallel)
- [ ] Await your email service decision + EIN dataset

**Tomorrow (Aug 12):**
- [ ] Fix Issue 1 (4 hours, once email service chosen)
- [ ] Fix Issue 5 (3 hours, once EIN dataset available)
- [ ] Smoke test all 5 modules
- [ ] Codex validation pass

**Aug 13:**
- [ ] Integration into daanaa_api.py (3 hours)
- [ ] Integration into discovery_daemon.py (3 hours)
- [ ] Full smoke test + Gate 3 Phase 1 launch

## DECISIONS NEEDED FROM AKBAR

1. **Email service**: SendGrid, AWS SES, or SMTP? (Deadline: before Issue 1 fix)
2. **Redis availability**: Is Redis on droplet, or provision SQLite fallback? (Deadline: before Issue 3 fix)
3. **EIN ground truth**: Provide 100 EIN+query pairs for benchmark (Deadline: before Issue 5 fix)
4. **Go/No-go**: Rework all 5 blockers this week, or defer any?

---

## SIGN-OFF

**Codex Review Status:** COMPLETE (5 blockers identified, 10 issues total)  
**Remediation Start:** NOW (Aug 11, 4:45pm CDT)  
**Expected Completion:** Aug 12, 6pm CDT (if decisions above provided)  
**Ship Readiness:** Aug 13, morning

All work test-first, all changes committed, no rework tolerance.
