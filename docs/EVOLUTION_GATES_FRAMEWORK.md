# EVOLUTION GATES FRAMEWORK

**Principle:** Not time-driven. Gates-driven.  
**Question:** What must be true before we can evolve to the next phase?  
**Authority:** Stewardship principles + operational evidence  

---

## GATE HIERARCHY

### FOUNDATIONAL GATES (Must Pass Before ANY Evolution)

**Gate 0: Operational Stability**
- Cron ImportError: 0/day (was 1,081)
- Inference uptime: >99% (was 8h down/day)
- Watchdog accuracy: 0 false positives
- Search sync: 0 drift from registry

**Status:** 🟡 PASSING (Emergency fixes deployed Fri 8/15)  
**Evidence required:** 1-week monitoring (Aug 15-22) confirming stability  
**Unlock:** Everything downstream depends on this

---

**Gate 1: Verification Integrity (P3, P6)**
- All scoring must be evidence-based + reproducible
- Verification state must be published + auditable
- Error recovery must work (no silent failures)
- Config must be explicit + validated

**Status:** 🟡 IN PROGRESS (P6 Phase 2 fixes Week 2)  
**Evidence required:**
  - All 6 medium issues fixed + tested
  - Silent exceptions eliminated
  - Config validation enforced
  - Retry logic + backoff working

**Unlock:** Search quality audit, scoring transparency, methodolody updates

---

**Gate 2: Privacy By Design (P2)**
- All new data collection must be opt-in
- No tracking or inference of browsing
- Wallet data device-first (not server-by-default)
- Website scraping respects robots.txt + GDPR

**Status:** ✅ PASSING (Current architecture meets P2)  
**Evidence required:** Privacy audit (quarterly)  
**Unlock:** Website discovery, enrichment expansion, data partnerships

---

### OPERATIONAL GATES (Enable New Capabilities)

**Gate 3: Search Quality (Foundational for Discovery)**
- Search results ranked by relevance + quality
- Typo tolerance working
- Semantic search (if used) audited for bias
- False negatives logged + reduced

**Status:** 🔴 NOT STARTED  
**Evidence required:**
  - Query analysis: 100 common searches benchmarked
  - Precision: >90% for top-5 results
  - Recall: >95% for exact name/EIN matches
  - Bias audit: No systematic ranking bias by org size/geography

**Gate passes:** → Unlocks website discovery confidence  
**Gate fails:** → Must fix search before expanding discovery

---

**Gate 4: Website Verification (Required Before Using URLs)**
- Website URL confidence >0.9 (current: 85%)
- Donation link confidence >0.9 (current: 90%)
- About page text quality (mission extraction)
- SSL/HTTPS validation + security check

**Status:** 🟡 PARTIAL (Links 90% confident; discovery 85%)  
**Evidence required:**
  - Spot audit: 100 websites verified manually
  - Link broken-link detection running
  - HTTPS enforcement + certificate validation
  - About-page extraction quality tested

**Gate passes:** → Unlocks website data in scoring/ranking  
**Gate fails:** → Keep separate; don't use in decisions until verified

---

**Gate 5: Small Org Fairness (P4 Gate)**
- Website discovery doesn't bias against small orgs
  - Small orgs have comparable website discovery rate as large
  - Small orgs with no website not penalized
  - Website quality not used as ranking signal
  
**Status:** 🔴 NOT STARTED  
**Evidence required:**
  - Cohort analysis: 100 small orgs (<$150K) vs large (>$1M)
  - Website discovery rate comparison
  - Scoring before/after audit (no small-org regression)
  - Methodology statement (website is context, not judgment)

**Gate passes:** → Website data can safely appear in public scoring  
**Gate fails:** → Website data private; disclosed only as supporting evidence, not ranking factor

---

**Gate 6: Explanation Completeness (P9 Gate)**
- Every org's score must be explainable to the org
- Peer group method documented + public
- Website inclusion/exclusion documented
- Confidence scores shown (not false certainty)

**Status:** 🟡 PARTIAL (P9 work ongoing)  
**Evidence required:**
  - Methodology page updated (website discovery explained)
  - Org detail page shows: peer group + methodology + website facts
  - Confidence scores visible (not hidden)
  - Correction flow documents why data was used/not used

**Gate passes:** → Website data surfaced publicly  
**Gate fails:** → Keep private pending transparency work

---

**Gate 7: Independence Verification (P7 Gate)**
- Website discovery is not influenced by vendors/partners
- No paid placement for website inclusion
- Small vendors treated same as large
- Reproducible + auditable (not hand-curation)

**Status:** ✅ STRUCTURAL (Algorithmic discovery; no curation)  
**Evidence required:**
  - Code review: No hardcoded exclusions/inclusions
  - Vendor log: All external data sources disclosed
  - Conflict-of-interest policy (VENDOR-POLICY.md) referenced

**Gate passes:** → Safe to use website data  
**Gate fails:** → System design issue; must fix

---

### EVOLUTION GATES (Unlock Next-Phase Capabilities)

**Gate 8: Comprehensive Discovery (Prerequisite for Rank-by-Quality)**
- 95%+ of 501c3 orgs have verified websites
- Website quality metrics recorded (response time, SSL, about-page)
- Mission text extracted + verified
- Geographic/sector clustering enabled

**Status:** 🔴 NOT STARTED  
**Unlock:** Rank-by-quality, geographic discovery, cohort analysis  
**Blocks:** Cannot use website as ranking signal until this passes

---

**Gate 9: Donor Intent Intelligence (Prerequisite for Giving Wallet 2.0)**
- Wallet captures: giving intent, impact focus, geography
- Intent is NOT tracked to orgs (privacy P2)
- Aggregate patterns: "Donors interested in health + climate"
- Recommendations: "Cohorts similar donors support"

**Status:** 🟡 PARTIAL (Wallet exists; intent capture basic)  
**Evidence required:**
  - Privacy audit: No org tracking
  - Aggregate patterns valid (no bias)
  - Recommendations don't pressure users (P5)
  - Opt-out always available

**Gate passes:** → Enable smart discovery recommendations  
**Gate fails:** → Keep wallet minimal (just bookmarks)

---

**Gate 10: Community Verification (Prerequisite for Peer Networks)**
- Orgs can claim/correct their data
- Peers can vouch for quality
- Verification badges mean: "Other orgs trust this"
- Transparency: All claims logged + versioned

**Status:** 🟡 PARTIAL (Claim flow exists; peer verification not built)  
**Evidence required:**
  - Claim audit: 100 claims processed, impact tracked
  - Peer network: 50+ reciprocal peer claims
  - Fraud detection: 0 false claims pass verification
  - Transparency: All claims visible in public audit log

**Gate passes:** → Enable community-sourced verification  
**Gate fails:** → Claims remain unverified; no public trust signals

---

## GATE MAP → WEBSITE SEARCH EVOLUTION

**Current question:** "When can we start website search?"

**Real question:** "What gates must pass before website data is trustworthy for discovery/ranking?"

```
┌─ Gate 0: Operational Stability (Aug 15-22)
│  └─ ALL downstream work depends on this
│
├─ Gate 1: Verification Integrity (Aug 12-23, Week 2-3)
│  └─ P6 fixes + error recovery working
│
├─ Gate 3: Search Quality Audit (Week 3-4, 6h)
│  └─ If search is already good, Gate 4 is safer
│  
├─ Gate 4: Website Verification (Week 4, 4h)
│  └─ Spot audit 100 websites; verify URLs working
│  
├─ Gate 5: Small Org Fairness (Week 4-5, 6h)
│  └─ Cohort analysis; no regression for small orgs
│  
├─ Gate 6: Explanation Completeness (Week 5-6, 8h)
│  └─ Methodology page + org detail disclosure
│  
├─ Gate 7: Independence Verification (Week 2, 2h)
│  └─ Code review; no vendor influence
│  
└─ Gate 8: Comprehensive Discovery (Week 6-8, 20h)
   └─ 95%+ of orgs have verified websites
   
WHEN ALL GATES PASS:
  → Website data can be SAFE in scoring/ranking
  → Unlock Gate 9 (donor intent) + Gate 10 (community verification)
```

---

## DECISION FRAMEWORK: WHAT TO BUILD NEXT

**Not:** "What can we build in 40 hours?"  
**But:** "What gates must pass to enable our mission?"

### Week 2-3 Priority (Autonomous, No Approval Needed)

**Gate 0 (Operational Stability):** 
- Emergency fixes deployed Fri 8/15
- Monitor 1 week (8/15-8/22)
- Target: 0 ImportError/day, >99% uptime

**Gate 1 (Verification Integrity):**
- Fix 6 P6 medium issues (10h)
- Error recovery + retry logic (2.5h)
- Tests for all fixes (8h)
- Target: All silent exceptions eliminated

**Gate 7 (Independence — Quick Win):**
- Code review: No hardcoded inclusions (2h)
- Vendor policy audit (1h)
- Log all external data sources (1h)
- Target: Structural independence confirmed

**Total Week 2-3: 24.5h autonomous work**

---

### Week 4-5 (If Gates 0-7 Passing)

**Gate 3 (Search Quality Audit):**
- Benchmark 100 common queries
- Precision/recall audit
- Typo tolerance testing
- Bias analysis (name/EIN/geography)
- **Time: 6h**
- **Decision:** If passing → proceed to Gate 4. If failing → fix search first.

**Gate 4 (Website Verification):**
- Spot audit 100 websites
- Broken-link detection
- SSL certificate validation
- About-page quality testing
- **Time: 4h**
- **Decision:** If confidence >0.9 → safe to use in data. If <0.9 → keep private.

**Total Week 4: 10h, decision-gated**

---

### Week 5-6 (If Gates 3-4 Passing)

**Gate 5 (Small Org Fairness):**
- Cohort analysis: 100 small vs large orgs
- Website discovery rate comparison
- Scoring regression test
- **Time: 6h**
- **Decision:** If unbiased → website data can appear in public scoring. If biased → private data only.

**Gate 6 (Explanation Completeness):**
- Methodology page: Website discovery explained
- Org detail: Show peer group + method + website facts
- Confidence scores + data provenance
- **Time: 8h**
- **Decision:** If clear → launch. If not → delay until docs complete.

**Total Week 5-6: 14h, decision-gated**

---

### Week 6-8 (If All Gates Passing)

**Gate 8 (Comprehensive Discovery):**
- Scale website discovery to 95%+ coverage
- Quality metrics: response time, SSL, mission quality
- Geographic/sector clustering enabled
- **Time: 20h**
- **Decision:** Complete coverage → unlock rank-by-quality feature.

**Then Unlock:**
- Gate 9: Donor intent → "Smart recommendations"
- Gate 10: Community verification → "Peer-trusted badges"

---

## THE REAL ROADMAP (Gates-Driven, Not Time-Driven)

**Aug 15-22 (Week 1): Gate 0 Monitoring**
- Emergency fixes live
- Confirm: Stability + no regressions

**Aug 12-23 (Week 2-3): Gates 0, 1, 7**
- P6 fixes + verification integrity
- Independence code review
- Target: All green before proceeding

**Aug 19-30 (Week 4-5, Conditional):**
- IF Gate 0-1-7 passing → Gate 3 + 4 (search quality + website verification)
- IF Gate 3-4 passing → Gate 5 + 6 (fairness + explanation)
- IF all passing → Gate 8 (scale discovery)

**Sept 1+ (Post-Gates):**
- Gate 9 (donor intent intelligence)
- Gate 10 (community verification)
- New discovery features enabled

---

## YOUR DECISION

**You asked:** "When can we start website search?"

**I'm asking:** "Which gates matter most for your vision?"

**Options:**

**Option A: Fast Track** (If you're confident in current search quality)
```
Skip Gates 3-4, go straight to fairness + explanation
Timeline: Website data in scoring by Week 5
Risk: Search quality not audited first
```

**Option B: High Confidence** (Recommended)
```
Pass all gates sequentially (0→1→3→4→5→6→8)
Timeline: Comprehensive discovery by Week 8, launch by Sept 1
Risk: Slower, but gates ensure safety + fairness
```

**Option C: Minimal Gates** (Move fastest)
```
Only require: Gates 0 + 7 + 5 (stability + independence + fairness)
Skip: Search quality audit, explanation completion
Timeline: Website in scoring by Week 4
Risk: Unexplained data, trust issues

---

**What's your stance on gates?**

- 🚀 **Fast:** Skip audit phases; move to production based on structural checks
- ⚖️ **Balanced:** Full gate sequence (recommended); gates unlock features
- 🔒 **Conservative:** Add extra gates for edge cases; slower but airtight

I'll build the roadmap around whichever gates you prioritize.

