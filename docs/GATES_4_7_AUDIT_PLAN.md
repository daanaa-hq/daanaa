# Gates 4-7: Qualification Audit Plan

**Timeline:** Aug 11-13 (parallel execution, 12 hours total)
**Authority:** Toyota lean + test-first validation

## Gate 4: Website Verification (4 hours)

**Scope:** 100 random orgs with websites

**Tests:**
- HTTP 200 status check
- HTTPS/certificate validation
- Redirect chains (max 3 hops)
- Link confidence scoring
- Donation URL validity

**Pass criteria:**
- ≥85% return HTTP 200
- ≥90% HTTPS valid
- No redirect chains >3
- Confidence score ≥0.8

**Failure handling:**
- Timeout: Retry with longer window
- 404/500: Log, skip, check sample size
- Redirect loops: Flag for manual review

---

## Gate 5: Small Org Fairness (6 hours)

**Scope:** 100 small (<$150K) vs 100 large (>$1M) orgs

**Tests:**
- Search by name: Both cohorts equally findable?
- Search by cause: Small orgs ranked fairly?
- Website discovery rate: Any bias?
- Financial context: Equal score distribution?

**Metrics:**
- Recall parity: small recall vs large recall
- Rank position parity: avg rank small vs large
- Visibility score: search top-5 appearance rate

**Pass criteria:**
- Recall ratio: 0.95-1.05 (parity within 5%)
- Rank parity: avg position within 2 slots
- No systematic small-org disadvantage

**Failure handling:**
- If recall gap >5%: Investigate FTS index
- If rank gap >2: Review scoring algorithm
- Root cause → fix → re-test

---

## Gate 7: Independence Verification (2 hours, parallel)

**Scope:** Code audit + transaction analysis

**Tests:**
- No paid placement code paths
- No vendor scoring boost logic
- No size-based ranking penalty
- No special-case orgs

**Methodology:**
- Grep for: "paid", "sponsored", "partner", "premium"
- Review: score calculation, ranking logic
- Verify: no hardcoded EIN whitelists
- Check: all orgs use same algorithm

**Pass criteria:**
- 0 paid placement code found
- 0 special-case logic detected
- All scoring deterministic from IRS data
- No donor influence vectors

---

## Execution Model (Autonomous)

Each gate runs in parallel:
- Gate 4: Website audit (4h, full sample)
- Gate 5: Fairness analysis (6h, cohort study)
- Gate 7: Code audit (2h, parallel)

**Sequential decision:**
```
Gate 3 PASSED ✅
  └─ Gate 4 → (PASS: proceed, FAIL: fix, re-test)
  └─ Gate 5 → (PASS: proceed, FAIL: fix, re-test)
  └─ Gate 7 → (PASS: proceed, FAIL: escalate)
  
If all PASS:
  └─ Gate 8 (Comprehensive Discovery): Proceed
```

**Quality gates:**
- All failures logged with root cause
- Re-tests required after fixes
- No shipping without all passing
- Board decision gate if any manual review needed

---

## Success Definition

**Gate 4 Passes:** 100 org websites verified, 85%+ HTTP 200, ready for public indexing
**Gate 5 Passes:** Small orgs have equal visibility/ranking, no algorithm bias
**Gate 7 Passes:** Platform independence verified, no special-case logic

**All three pass:** Ready for Phase 2 pilot + public launch
