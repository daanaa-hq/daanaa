# Nightly Orchestrator Design — Lessons from Retired Discovery Daemon

**Problem Statement:** Previous 24/7 `discovery_daemon.py` had efficiency issues. We're building v2 for nightly enrichment (8pm–8am) applying learned lessons.

---

## Key Failures & Lessons

### 1. **Liveness ≠ Health**

**What went wrong:** Daemon reported "alive" via `pgrep`, but was actually stuck (0 links verified for 12+ hours). Watchdog checked process existence, not productivity.

**Lesson applied:** 
- Don't check `pgrep -f discovery_daemon` (process alive = false confidence)
- Check **productivity metrics**: last successful work timestamp, throughput (orgs/hour), error rate
- If no new records in 30 min, restart (not "maybe later")

**Implementation:**
```python
class ProductivityWatchdog:
    def __init__(self, min_records_per_hour=10):
        self.min_records_per_hour = min_records_per_hour
        self.last_success_time = time.time()
        self.success_count_in_window = 0
    
    def record_success(self):
        self.last_success_time = time.time()
        self.success_count_in_window += 1
    
    def is_healthy(self):
        elapsed = (time.time() - self.last_success_time) / 3600
        if elapsed > 0.5 and self.success_count_in_window < self.min_records_per_hour * elapsed:
            return False  # Not meeting throughput target
        if time.time() - self.last_success_time > 1800:  # 30 min silence
            return False
        return True
```

---

### 2. **Thread Pool Resource Leaks**

**What went wrong:** Batch timeout handler created threads without cleanup. Pool size = 8, but 456 live threads accumulated. Process stayed "alive" but was effectively dead (all workers blocked).

**Lesson applied:**
- Never spawn threads in exception handlers without explicit cleanup
- Use `ThreadPoolExecutor` context managers (`with` blocks) to guarantee cleanup
- Cap max_workers; never exceed available CPU cores (our case: 16 for Ryzen 9700X)
- Monitor thread count on every iteration

**Implementation:**
```python
class SafeWorkerPool:
    def __init__(self, max_workers=8):
        self.max_workers = min(max_workers, cpu_count())
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def submit_batch(self, tasks, timeout=300):
        """Submit batch with guaranteed cleanup."""
        futures = []
        try:
            for task in tasks:
                futures.append(self.executor.submit(task))
            
            # Wait for all with timeout
            completed, timed_out = wait(futures, timeout=timeout)
            
            # Log thread health
            active = threading.active_count()
            if active > self.max_workers * 2:
                logging.warning(f"Thread leak detected: {active} threads for {self.max_workers} workers")
                return False  # Signal restart needed
            
            return len(timed_out) == 0
        finally:
            # Cleanup even if exception
            for future in futures:
                if not future.done():
                    future.cancel()
```

---

### 3. **Silent Failures (except: pass)**

**What went wrong:** When discovery link fetch failed, code just silently passed (`except: pass`). No log, no indication. Daemon queued 0 links but reported success.

**Lesson applied:**
- Never use `except: pass` — always log minimum `logger.warning()`
- Distinguish between expected errors (404, timeout) and unexpected (network error)
- Emit metrics for each error type
- Fail fast if error rate exceeds threshold (e.g., >50% timeouts = stop, restart)

**Implementation:**
```python
class ErrorHandler:
    def __init__(self, max_error_rate=0.5):
        self.max_error_rate = max_error_rate
        self.errors_in_batch = 0
        self.total_in_batch = 0
    
    def handle_scrape_error(self, ein, url, error):
        self.total_in_batch += 1
        self.errors_in_batch += 1
        
        if isinstance(error, TimeoutError):
            logging.warning(f"Timeout scraping {ein} ({url})")
        elif isinstance(error, HTTPError):
            logging.info(f"HTTP {error.code} for {ein} ({url})")
        else:
            logging.error(f"Unexpected error scraping {ein}: {error}", exc_info=True)
        
        rate = self.errors_in_batch / max(1, self.total_in_batch)
        if rate > self.max_error_rate:
            logging.critical(f"Error rate {rate:.0%} exceeds {self.max_error_rate:.0%}; aborting")
            return False  # Signal to stop phase
        return True
```

---

### 4. **Concurrent Writer Contention**

**What went wrong:** SQLite `.backup()` would restart from page 0 whenever discovery_daemon committed. Backup could never complete (livelock, not hang). 34-minute snapshot attempt got stuck at 11.1GB of 15GB.

**Lesson applied:**
- Before any full-DB operation (backup, vacuum), quiesce continuous writers
- Use `SIGSTOP` / `SIGCONT` — pauses process without losing work
- Guarantee resume even if script dies (use EXIT trap)
- For nightly jobs: no concurrent writers during backup window (schedule phases sequentially)

**Implementation:**
```bash
# In orchestrator shell wrapper
quiesce_writers() {
    local pids=$(pgrep -f "discovery_daemon\|enrich_batch\|verify_donate")
    if [ -n "$pids" ]; then
        echo "Pausing writers: $pids"
        kill -STOP $pids
        trap "kill -CONT $pids" EXIT  # Guaranteed resume on exit
    fi
}

# Usage before backup:
quiesce_writers
sqlite3 data/merit_registry.db ".backup /tmp/backup.db"
# EXIT trap auto-resumes writers
```

---

### 5. **Uncontrolled Batch Sizes & Timeouts**

**What went wrong:** Daemon batched 1000 orgs at a time, but inference was slow (10–250ms per link), causing timeouts. No adaptive backoff.

**Lesson applied:**
- Start with small batches; grow based on observed latency
- Track p95 latency per phase; adjust batch size to fit timeout window
- Respect local inference server saturation (monitor port 11436/11437 response times)
- Fail fast: if p95 > timeout/2, reduce batch size next iteration

**Implementation:**
```python
class AdaptiveBatcher:
    def __init__(self, target_p95_ms=500, timeout_ms=10000):
        self.target_p95_ms = target_p95_ms
        self.timeout_ms = timeout_ms
        self.batch_size = 100
        self.latencies = deque(maxlen=1000)
    
    def record_latency(self, ms):
        self.latencies.append(ms)
    
    def adjust_batch_size(self):
        if len(self.latencies) < 100:
            return  # Wait for enough data
        
        p95 = sorted(self.latencies)[int(len(self.latencies) * 0.95)]
        if p95 > self.target_p95_ms:
            self.batch_size = max(1, self.batch_size // 2)
            logging.info(f"Latency high ({p95}ms); reducing batch to {self.batch_size}")
        elif p95 < self.target_p95_ms / 2:
            self.batch_size = min(1000, self.batch_size * 2)
            logging.info(f"Latency low ({p95}ms); increasing batch to {self.batch_size}")
```

---

### 6. **Checkpoint & Resume**

**What went wrong:** Daemon couldn't restart gracefully. No checkpoint, so restart would reprocess already-done orgs (duplicate work) or skip work (loss of state).

**Lesson applied:**
- Store checkpoint every N records: (phase, last_ein, record_count)
- On restart, query "where EIN > checkpoint_ein" to resume
- Log checkpoint boundaries clearly (helps debugging)

**Implementation:**
```python
class CheckpointManager:
    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_checkpoints (
            phase TEXT,
            run_date DATE,
            last_ein TEXT,
            record_count INTEGER,
            checkpoint_time TIMESTAMP,
            PRIMARY KEY (phase, run_date)
        )
        """)
    
    def save_checkpoint(self, phase, last_ein, record_count):
        self.db.execute("""
        INSERT OR REPLACE INTO enrichment_checkpoints
        VALUES (?, date('now'), ?, ?, datetime('now'))
        """, (phase, last_ein, record_count))
        self.db.commit()
    
    def load_checkpoint(self, phase):
        cursor = self.db.execute("""
        SELECT last_ein, record_count FROM enrichment_checkpoints
        WHERE phase = ? AND run_date = date('now')
        """, (phase,))
        row = cursor.fetchone()
        return row or (None, 0)
```

---

### 7. **Observability & Debugging**

**What went wrong:** Append-only logs across daemon restarts made it hard to isolate failures. A restart entry got buried in thousands of lines; debugging tools couldn't distinguish pre-restart from post-restart failures.

**Lesson applied:**
- Emit clear restart markers in logs: `===== ENRICHMENT RUN: 2026-08-09 20:00:00 =====`
- Log phase start/end with timestamps and metrics
- Write structured metrics to separate table (not just logs)
- Include thread count, memory, active workers in every 5-min tick

**Implementation:**
```python
class MetricsLogger:
    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_metrics (
            phase TEXT,
            timestamp TIMESTAMP,
            records_processed INTEGER,
            records_per_hour REAL,
            error_count INTEGER,
            error_rate REAL,
            thread_count INTEGER,
            memory_mb INTEGER,
            elapsed_seconds INTEGER,
            status TEXT  -- 'running', 'success', 'timeout', 'error', 'incomplete'
        )
        """)
    
    def log_phase_tick(self, phase, records, errors, elapsed_s):
        memory = psutil.Process().memory_info().rss // 1024 // 1024
        threads = threading.active_count()
        rph = (records / elapsed_s * 3600) if elapsed_s > 0 else 0
        
        self.db.execute("""
        INSERT INTO enrichment_metrics VALUES
        (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
        """, (phase, records, rph, errors, errors/(records or 1), threads, memory, elapsed_s, 'running'))
        self.db.commit()
```

---

## Nightly Orchestrator Improvements Over Daemon

| Issue | Daemon Problem | Nightly Fix |
|-------|---|---|
| **Liveness** | Check process alive | Check productivity (last work timestamp, throughput) |
| **Thread leaks** | `except: pass` thread spawn | Context managers, explicit cleanup, thread count monitoring |
| **Silent failures** | No logging in errors | Explicit log level per error type; fail fast on error rate |
| **Contention** | Concurrent writers during backup | Sequential phases; SIGSTOP writers before backup |
| **Batching** | Fixed batch size (1000) | Adaptive batching based on p95 latency |
| **Recovery** | No checkpoint | Checkpoint every N records; resume from EIN |
| **Observability** | Append-only logs | Structured metrics table; clear run markers |
| **Timing** | 24/7 (always on, heat/interference) | 8pm–8am only (cool hours, scheduled) |
| **Scope** | Single discovery job | Multi-phase orchestration with sequencing |

---

## Nightly Orchestrator: Robust Architecture

```
orchestrator.py
├── Phase 1-8 (sequential, not concurrent)
├── ProductivityWatchdog (per phase)
├── CheckpointManager (resume on restart)
├── MetricsLogger (structured + logs)
├── ErrorHandler (fail-fast on >50% errors)
├── SafeWorkerPool (cleanup guarantee)
├── AdaptiveBatcher (adjust to latency)
└── MonitorLoop (5-min ticks: thread count, memory, throughput)

watchdog.sh
├── Monitor orchestrator.py process
├── Check productivity metrics table (not just liveness)
├── Alert if phase takes >2 hours or stalls >30 min
├── Restart with checkpoint resume if unhealthy
└── SIGSTOP/SIGCONT writers during critical operations
```

---

## Go-Live Checklist

- [ ] Productivity watchdog tests (synthetic stall, verify restart)
- [ ] Thread leak prevention (run 8 hours, verify thread count stable)
- [ ] Checkpoint resume test (kill mid-phase, verify restart from checkpoint)
- [ ] Error rate abort test (inject 60% timeouts, verify phase exits)
- [ ] Concurrent writer test (run backup during phase, verify SIGSTOP/CONT works)
- [ ] Dry-run on 1K orgs (2h window, validate metrics table)
- [ ] Live dry-run (8pm–6am one night, collect baseline metrics)
- [ ] Enable alerting (Slack/email on phase timeout or stall)

