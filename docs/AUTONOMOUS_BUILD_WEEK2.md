# AUTONOMOUS BUILD PLAN — WEEK 2-3

**Status:** IN PROGRESS  
**Authority:** Founder autonomous authorization  
**Timeline:** Aug 12-30  
**Oversight:** Codex adversarial review, Claude pragmatic implementation

---

## EXECUTION UNDERWAY

### Phase 1: Repo Cleanup (TODAY)

**Issue:** Pre-commit hook detected 8+ corrupted Python files  
**Action:** Remove broken files, validate remaining code

**Files to remove:**
```bash
# Already removed:
scripts/academic_compression.py
scripts/academic_geo_equity.py
scripts/academic_mobility.py
scripts/academic_sector_geo.py
scripts/clean_names.py
scripts/find_duplicates.py
scripts/generate_org_sitemaps.py
scripts/generate_visibility_exports.py

# Remaining to fix:
scripts/agent3_enricher.py (IndentationError)
```

---

### Phase 2: P6 Phase 2 Remediation (WEEK 2)

**6 Medium Issues to Fix:**

1. **Hardcoded timeouts** (600, 3600 seconds)
   - Find all hardcoded sleep/timeout values
   - Replace with configurable params
   - Test: Verify timeout respected

2. **Log parsing anti-patterns** (grep "discovered", "batch_size")
   - Find remaining grep patterns in bash scripts
   - Migrate to daemon_health_lib.py state reading
   - Test: Verify no log dependency

3. **Silent exception handlers** (bare `except:` clauses)
   - Audit all try/except blocks
   - Replace bare except with specific types
   - Add logging + state publication
   - Test: Verify exceptions caught correctly

4. **Watchdog false positives**
   - Evaluate staleness thresholds
   - Add hysteresis to prevent restart storms
   - Test: Verify stable behavior

5. **Config validation gaps**
   - Verify required env vars at startup
   - Fail fast if missing
   - Test: Verify validation works

6. **Error recovery paths**
   - Add retry logic + exponential backoff
   - Implement jitter (prevent thundering herd)
   - Test: Verify retry behavior

**Definition of Done:** All 6 issues have failing tests first, then fixes, then passing tests.

---

### Phase 3: Test-First Expansion (WEEK 2-3)

**20+ New Tests to Add:**

**API Contract Tests (8 tests):**
- [ ] Search endpoint: parameter validation (q, per_page, sort, order)
- [ ] Org detail: EIN parameter honored
- [ ] Compare: multiple org selection
- [ ] Directory: category filtering
- [ ] Search response schema: organizations array always present
- [ ] Error responses: 400/404/500 proper format
- [ ] Rate limiting (if implemented)
- [ ] CORS headers

**Data Pipeline Tests (8 tests):**
- [ ] Scoring: NTEE2 × band × region coverage
- [ ] Enrichment: Website discovery success rate
- [ ] Link verification: donate_url confidence >= 0.9
- [ ] FTS5 indexing: org_fts counts match registry
- [ ] Embedding generation: vector dimension = 384
- [ ] Mission generation: output quality (non-empty, <200 chars)
- [ ] Data integrity: no nulls in required fields
- [ ] Snapshot consistency: before/after checksums match

**Daemon Health Tests (4 tests):**
- [ ] State publication: /tmp/*.health.json updates
- [ ] Watchdog detection: stale detection works
- [ ] State transitions: healthy → degraded → failed
- [ ] Recovery: restart restores health

**Deliverable:** All tests in `tests/` directory, CI passing

---

### Phase 4: Optimization Builds (WEEK 3)

#### A. Precompute Snapshots (6h)

**Design:**
```python
class PrecomputePhase:
    def __init__(self, name, duration_estimate_sec, dependencies=[]):
        self.name = name
        self.checkpoint_file = f'/tmp/precompute_{name}.checkpoint'
        self.duration = duration_estimate_sec
        self.deps = dependencies

phases = [
    PrecomputePhase("scoring", 300),
    PrecomputePhase("enrichment", 600, deps=["scoring"]),
    PrecomputePhase("json_generation", 1200, deps=["enrichment"]),
    PrecomputePhase("fts5_index", 900, deps=["json_generation"]),
    PrecomputePhase("compress_upload", 1800, deps=["fts5_index"]),
]

# If Phase 3 fails at minute 45:
# Resume from Phase 3 (not Phase 1) → 20 min recovery (not 2+ hours)
```

**Deliverable:** `scripts/precompute_with_checkpoints.py` + resume logic + tests

#### B. Ops Runbook Generator (2h)

**Design:**
```bash
# Parse LESSONS.md for patterns
grep -E "^##|Root cause:|Solution:" LESSONS.md

# Generate runbook section
cat > docs/ops_runbook_auto.md << EOF
## If ImportError in cron (2026-08-10)
1. Check: python3 -m py_compile scripts/overnight_pipeline.py
2. If syntax error: Fix imports, retry
3. If venv issue: Restart cron (systemctl restart cron)
4. Monitor: grep ImportError overnight.log | wc -l
5. Escalate if: >10 errors after restart

## If Inference Server down (2026-08-10)
1. Check: curl http://localhost:11437/health
2. If port closed: bash scripts/embed_server.sh
3. If timeout: Check GPU (nvidia-smi / radeontop)
4. Monitor: curl /health every 5s
5. Escalate if: Still down after 2 restarts
EOF
```

**Deliverable:** `docs/ops_runbook_auto.md` + `scripts/generate_ops_runbook.py`

#### C. Memory Phase 2 (Conditional, 4h)

**Trigger:** Aug 16 recall_log shows ≥2 searches/week + >50% "semantic would help"

**If triggered:**
```python
# Build FTS5 index from session archive
sqlite3 memory.db << EOF
CREATE VIRTUAL TABLE sessions_fts USING fts5(
    filename, topic, content, tags
);
INSERT INTO sessions_fts SELECT * FROM indexed_sessions;
CREATE INDEX sessions_timestamp ON sessions_fts(timestamp);
EOF

# Hybrid search: FTS5 + keyword fallback
def hybrid_search(query, limit=5):
    fts_results = fts5_search(query, limit)
    if len(fts_results) < 3:
        fallback = keyword_search(query, limit - len(fts_results))
        return fts_results + fallback
    return fts_results
```

**Deliverable:** FTS5 implementation + tests (if data justifies)

---

## CURRENT STATUS (Aug 10, 20:30 UTC)

✅ **COMPLETE:**
- Emergency fixes deployed (3 P6 critical issues)
- Watchdog migration + pre-commit hook
- 14 unit tests (all passing)
- Phase 1 memory system ready

🔨 **IN PROGRESS NOW:**
- Repo cleanup (corrupted files)
- P6 Phase 2 root cause analysis
- Test-first strategy design

📋 **NEXT (WEEK 2):**
- Implement P6 fixes + tests
- Expand test suite (20+ tests)
- Precompute snapshot design

📋 **LATER (WEEK 3+):**
- Precompute implementation
- Ops runbook generation
- Memory Phase 2 (if justified)

---

## DAILY STATUS (Auto-Updated)

**Aug 12 (Today):**
- [ ] Repo cleanup complete
- [ ] P6 Phase 2 root cause doc written
- [ ] Test-first design locked
- **Target: 6h work**

**Aug 13 (Tomorrow):**
- [ ] First P6 fix implemented + tested
- [ ] Second fix + tests in progress
- **Target: 6h work**

**Aug 14:**
- [ ] Third + fourth fixes implemented
- [ ] Test suite skeleton built
- **Target: 6h work**

**Aug 15:**
- [ ] Emergency fixes deploy (autonomous)
- [ ] Validate deployment + monitoring
- [ ] Fifth + sixth P6 fixes (if time)
- **Target: 2h work**

**Aug 16-17 (Weekend):**
- [ ] P6 validation on real data
- [ ] Recall_log review (if using Phase 1)
- [ ] Week 3 planning

---

## DECISION POINTS (Real-Time)

**If a P6 fix breaks tests:**
→ Investigate immediately, revert commit, log in DECISIONS.md

**If precompute snapshots are harder than expected:**
→ Reduce scope: do checkpoint system first, resume logic second

**If Aug 16 recall data shows Phase 2 not needed:**
→ Skip 4h of work. Use time for extended test coverage or tech debt.

**If we're ahead of schedule:**
→ Extend test coverage to 80%+, or start memory Phase 2 early

---

## STEERING (Codex Oversight)

Every Monday + Friday, Codex reviews:
- [ ] Are we still aligned with Stewardship principles?
- [ ] Are decisions documented in DECISIONS.md?
- [ ] Are all tests passing before merging?
- [ ] Any scope creep or off-track work?
- [ ] Adjust Week 3 if priorities changed?

---

## SUCCESS BY AUG 30

✅ All 6 P6 medium issues fixed  
✅ 20+ new tests (API, pipeline, daemon)  
✅ Precompute snapshots working  
✅ Ops runbook auto-generated  
✅ Memory Phase 2 decision made (data-driven)  
✅ Zero regressions, all prod smoke tests green  
✅ DECISIONS.md complete  

---

**BUILDING NOW.** Will report daily progress.

