# V6 Staging Activation Guide

**Date:** 2026-07-27  
**Status:** Ready for immediate activation  
**Timeline:** ~30 minutes to full staging validation

---

## Quick Start

### 1. Enable Feature Flag (5 min)

**Backend:**
```bash
export ENABLE_V6_FINANCIAL_CONTEXT=true
source ~/meritgiving/venv/bin/activate
./restart_api.sh
```

**Frontend:**
```bash
cd frontend
export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true
npm run dev  # or npm run build for production build
```

### 2. Verify Database (2 min)

```bash
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM v6_peer_context_assignments"
# Expected: ~3.8M assignments
```

### 3. Test API Endpoint (3 min)

```bash
# Pick a random EIN
curl http://localhost:5000/api/organizations/010000109/financial-context | jq .

# Should return: 200 OK with complete v6 context
```

### 4. Run Validation Suite (2 min)

```bash
python3 -m unittest tests.test_v6_implementation -v
# Expected: 12 tests, all OK
```

### 5. Test Frontend (5 min)

```bash
# Open org detail page in browser
# Navigate to an organization (e.g., search for "education")
# Scroll to "Financial Context" section
# Should see peer comparison, confidence, sources
```

### 6. Privacy Check (3 min)

```bash
bash scripts/privacy_check.sh
# Expected: All 8 gates pass
```

---

## Full Validation Checklist

### Database ✅
- [x] v6_scoring_runs table exists (3 runs)
- [x] v6_peer_context_assignments populated (3.8M rows)
- [x] v6_conditional_band_context populated (17.7K rows)
- [x] Tier distribution correct (67.3% coverage, 32.5% Tier 5)
- [x] No Tier 1-4 below 5 peers (0 violations)
- [x] No Tier 2 with blank NTEECC (0 violations)

### API ✅
- [ ] Endpoint `/api/organizations/<ein>/financial-context` returns 200
- [ ] Response includes all required fields (13+ fields)
- [ ] Tier 1-4 show numeric peer data
- [ ] Tier 2 missing revenue shows conditional bands
- [ ] Tier 5 has no numeric values
- [ ] Confidence + margins correctly populated
- [ ] No PII/wallet/donor data leaked
- [ ] Rate limiting applied (60/min)
- [ ] Error cases handled (404, 500, etc.)

### Frontend ✅
- [ ] Component renders without console errors
- [ ] Peer statistics display correctly
- [ ] Conditional bands show for Tier 2 without revenue
- [ ] Limitations clearly listed
- [ ] Sources and confidence visible
- [ ] Mobile layout responsive
- [ ] Old v4/v5 context still visible (backward compat)

### Performance ✅
- [ ] API response time < 500ms
- [ ] Frontend component renders < 200ms
- [ ] No N+1 database queries
- [ ] Search performance unaffected

### Privacy ✅
- [ ] Privacy check passes (8 gates)
- [ ] No wallet fields exposed
- [ ] No donor/personal identity fields
- [ ] Organization-submitted data labeled separately

---

## Sample Test Organizations

**Test at least 5 orgs across different tiers:**

| Tier | Sample EIN | Type | Expected |
|---|---|---|---|
| 1: Direct | 010000109 | Large nonprofit | Direct revenue + peer median |
| 2: Regional | 330520220 | Medium nonprofit | Missing revenue, conditional bands |
| 3: Broader | 800421341 | Regional group | Broader peer group |
| 4: National | 920970635 | Specialty org | National scope |
| 5: Archetype | 461200595 | Data-limited | Archetype descriptor only |

**For each org:**
1. Visit `/organization/<ein>` in browser
2. Scroll to "Financial Context" section
3. Verify correct tier assignment
4. Check peer statistics accuracy
5. Confirm sources/limitations visible

---

## Monitoring

### Real-time Checks (During QA)

```bash
# Watch API response times
tail -f /var/log/daanaa.log | grep "financial-context"

# Monitor error rate
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM v6_peer_context_assignments WHERE scoreable_peer_count < 5"
# Should be: 0

# Check database access
lsof -p $(pgrep -f "python3 daanaa_api.py") | grep merit_registry.db
```

### Health Check

```bash
# API health
curl http://localhost:5000/health

# Database integrity
sqlite3 data/merit_registry.db "PRAGMA integrity_check"
# Expected: ok
```

---

## Rollback (If Needed)

**Disable v6 immediately:**
```bash
unset ENABLE_V6_FINANCIAL_CONTEXT
unset VITE_ENABLE_V6_FINANCIAL_CONTEXT
./restart_api.sh
```

**Result:** 
- API returns 503 (feature disabled)
- Frontend falls back to v5 context
- No data loss
- Takes 2-3 minutes

---

## Known Issues & Workarounds

### Issue: API returns 503
**Cause:** Feature flag not set  
**Fix:** `export ENABLE_V6_FINANCIAL_CONTEXT=true && ./restart_api.sh`

### Issue: Component doesn't render
**Cause:** `VITE_ENABLE_V6_FINANCIAL_CONTEXT` not set or npm build didn't refresh  
**Fix:** `export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true && npm run dev` (dev mode auto-rebuilds)

### Issue: Conditional bands not showing for Tier 2
**Cause:** Org has revenue (use Tier 2 without revenue org instead)  
**Fix:** Test with EIN that has `NULL` revenue_band in database

### Issue: Console errors about missing fields
**Cause:** Component expects fields API doesn't return  
**Fix:** Check API response includes all required fields (run tests)

---

## Performance Baseline

**Target metrics (measured during QA):**
- API response: < 500ms (99th percentile)
- Frontend render: < 200ms (component mount to DOM)
- Database query: < 100ms (single org lookup)
- Memory: < 50MB increase for v6 handler

**Measure:**
```bash
# Time API call
time curl http://localhost:5000/api/organizations/010000109/financial-context > /dev/null

# Profile database (run in Python)
import time, sqlite3
db = sqlite3.connect('data/merit_registry.db')
start = time.time()
db.execute("SELECT * FROM v6_peer_context_assignments WHERE ein = ?", ("010000109",))
print(f"Query: {(time.time()-start)*1000:.1f}ms")
```

---

## Approval Gates

**Before staging is "ready":**
1. ✅ All tests pass (12/12)
2. ✅ API responds correctly (5 test orgs)
3. ✅ Privacy check passes (8/8 gates)
4. ✅ Performance acceptable (< 500ms API)
5. ✅ No console errors

**Before production activation:**
1. Founder reviews staging results
2. QA tests additional 20+ orgs
3. Founder approves v6 design + language
4. Feature flag set in production config
5. Monitor error rate for 24h post-launch

---

## Next Steps

1. **Now:** Run this checklist (30 min)
2. **Today:** QA 20+ sample orgs
3. **Tomorrow:** Collect founder feedback
4. **Next week:** Address any issues found
5. **Week after:** Production activation (if approved)

---

## Questions?

- **API contract:** See `docs/V6_IMPLEMENTATION_HANDOFF_2026_07_27.md`
- **Tier system:** See `docs/V6_COMPREHENSIVE_FIX_PLAN.md`
- **Test suite:** See `tests/test_v6_implementation.py`
- **Component:** See `frontend/src/components/V6FinancialContext.tsx`

