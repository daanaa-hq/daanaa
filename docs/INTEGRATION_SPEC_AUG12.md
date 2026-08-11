# Integration Specification: Security + Reliability Modules
**Date:** Aug 12, 2026 | **Phase:** API + Daemon Integration | **Rework Tolerance:** 0

---

## INTEGRATION POINTS: daanaa_api.py

### 1. App Initialization (Line ~1, before routes)
```python
# ADD THESE IMPORTS
from scripts.rate_limiter_v2 import RateLimiterV2
from scripts.admin_key_validator_v2 import AdminKeyValidator
from scripts.input_validator_v2 import InputValidator
from scripts.error_handler_v2 import ProductionErrorHandler
from scripts.analytics_privacy import AnalyticsPrivacyValidator

# ADD THESE SINGLETONS AT APP START
app.rate_limiter = RateLimiterV2(use_redis=True)  # Redis or SQLite fallback
app.admin_validator = AdminKeyValidator()
app.input_validator = InputValidator()
app.error_handler = ProductionErrorHandler(is_production=DAANAA_PROD)
app.analytics_privacy = AnalyticsPrivacyValidator()
```

### 2. Middleware: Before Request (Add after app initialization)
```python
@app.before_request
def rate_limit_check():
    """Check rate limits on every request (except health)"""
    if request.path == '/health':
        return
    
    client_id = app.rate_limiter.get_client_id(request.headers)
    is_limited, meta = app.rate_limiter.is_rate_limited(client_id, request.path)
    
    if is_limited:
        return jsonify({"error": "Rate limited"}), 429
```

### 3. Admin Key Decorator (Add as new function)
```python
def require_admin_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_id = app.rate_limiter.get_client_id(request.headers)
        is_valid, msg = app.admin_validator.validate_admin_key(
            app.admin_validator.extract_admin_key_from_header(request.headers),
            client_id,
            request.path
        )
        if not is_valid:
            return jsonify({"error": msg}), 401
        return f(*args, **kwargs)
    return decorated_function
```

### 4. Admin Routes (Apply decorator to existing /api/admin/* routes)
```python
@app.route('/api/admin/stats')
@require_admin_key
def admin_stats():
    # existing code
```

### 5. Input Validation (Add to /api/organizations route)
```python
@app.route('/api/organizations')
def list_organizations():
    # VALIDATE INPUTS
    sort = request.args.get('sort', 'name')
    valid, sort = app.input_validator.validate_sort_parameter(sort)
    if not valid:
        return jsonify({"error": sort}), 400
    
    order = request.args.get('order', 'asc')
    valid, order = app.input_validator.validate_order_parameter(order)
    if not valid:
        return jsonify({"error": order}), 400
    
    # existing code
```

### 6. Error Handler (Replace @app.errorhandler blocks)
```python
@app.errorhandler(500)
def internal_error(error):
    status, response = app.error_handler.handle_api_error(
        error, 
        request.path, 
        request.headers.get('X-Request-ID', 'unknown')
    )
    return jsonify(response), status
```

### 7. Analytics Privacy (Wrap Plausible calls)
```python
# Before sending analytics event
event = {"page": request.path, "event_name": "pageview"}
is_valid, issues = app.analytics_privacy.validate_event(event)
if not is_valid:
    logger.warning(f"Blocked analytics event: {issues}")
    return  # Don't send to Plausible

# Send to Plausible (sanitize URL first)
safe_url = app.analytics_privacy.sanitize_url(request.url)
```

---

## INTEGRATION POINTS: discovery_daemon.py

### 1. Config Validation (At startup, line ~1)
```python
# ADD
from scripts.daemon_config_retry_v2 import DaemonConfig, RetryLogic

# ADD AT STARTUP
try:
    config = DaemonConfig()  # Reads DAEMON_TIMEOUT, DAEMON_WORKERS, DAEMON_BATCH_SIZE
except ValueError as e:
    logger.error(f"Invalid daemon config: {e}")
    sys.exit(1)
```

### 2. Exception Handling (Wrap batch processing)
```python
# ADD
from scripts.daemon_exception_handler_v2 import DaemonExceptionHandler, WatchdogHysteresis

exception_handler = DaemonExceptionHandler()
watchdog = WatchdogHysteresis()

# WRAP batch processing
@exception_handler.safe_batch_processing("org_discovery")
def discover_organizations(batch):
    # existing org discovery code
    pass

# ON SUCCESS
watchdog.record_success()

# ON FAILURE (caught by exception handler)
watchdog.record_failure()  # Will trigger RESTART if 3 failures
```

### 3. Retry Logic (Wrap transient failures)
```python
retry = RetryLogic(max_retries=3)

for org in batch:
    success, result, error = retry.retry(process_org, org)
    if not success:
        logger.warning(f"Failed to process org after retries: {error}")
        # Continue with next org (batch resilience)
```

---

## SMOKE TESTS (Aug 12 Afternoon)

### Test 1: Health Check
```bash
curl http://localhost:5000/health
# Expect: 200 OK
```

### Test 2: Rate Limiting
```bash
for i in {1..51}; do curl -s http://localhost:5000/api/search?q=test; done | tail -1
# Expect: 429 Too Many Requests on request 51
```

### Test 3: Admin Key Validation
```bash
curl -H "X-Admin-Key: wrong_key" http://localhost:5000/api/admin/stats
# Expect: 401 Unauthorized
```

### Test 4: Input Validation
```bash
curl http://localhost:5000/api/organizations?sort=invalid
# Expect: 400 Bad Request
```

### Test 5: Daemon Health
```bash
python3 scripts/discovery_daemon_health.py
# Expect: {"status": "healthy", "action": "continue"}
```

---

## REWORK PREVENTION

**Critical checkpoints (Codex validates each):**
1. ✅ Rate limiter integrates without breaking existing routes
2. ✅ Admin key decorator doesn't interfere with public routes
3. ✅ Error handler preserves all existing error response formats
4. ✅ Input validation only rejects invalid, allows all valid
5. ✅ Daemon health state persists across restarts
6. ✅ Watchdog state machine doesn't false-alarm on transient failures

**Rollback plan (if rework needed):**
- Each module has v2 (new) and v1 (original) available
- Can quickly revert to v1 if integration causes issues
- All changes behind feature flags (disabled by default until validated)

---

**Status:** Ready for Codex review + Aug 12 execution
**Rework tolerance:** 0 (Codex validates each checkpoint)
**Timeline:** 8 hours (6am-2pm CDT Aug 12)
