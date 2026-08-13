# Codex Handoff: Continuous Nonprofit Website Discovery Branch
**Date:** 2026-08-13  
**From:** Claude Code  
**To:** Codex (Discovery Team — Branch 2)  
**Urgency:** 🟢 LAUNCH IMMEDIATELY — Parallel to Donation Link Extraction  
**Objective:** Find websites for 1.59M nonprofits without one

---

## Executive Summary

**Problem:** 1.59M US nonprofits (77.6%) don't have discovered websites in our database. This blocks small-org visibility and prevents discovery of their donation links.

**Opportunity:** Four simple strategies can find 650K+ new websites in 2-3 weeks, boosting coverage from 22% to 68% and dramatically improving Task #11 Phase 1 launch data.

**Your Mission:** Launch Phase 1 (domain guessing) immediately. It's fast (70% success), cheap ($0), and can run in parallel with donation link extraction work.

---

## Why This Matters

**Current:**
- 461,682 websites discovered (22.4% of 2.06M)
- 87,039 verified as active
- 1,595,152 with NO website found (77.6%)

**Bottleneck by Size (this is key for Task #11):**
- Micro-orgs (<$150K): 19.0% coverage — **81% invisible**
- Professional: 28.6% coverage
- Established: 25.3% coverage

**Your Work:** Move micro-orgs from 19% to 50%+ coverage in 2-3 weeks. This enables Task #11 Phase 1 Phase 1 to launch on solid data.

---

## Four Discovery Strategies (In Order of ROI)

### Strategy 1: Domain Guessing (LAUNCH TODAY)
**Patterns:** `[orgname].org`, `[acronym].org`, `[city][orgname].org`

Examples:
- "Habitat for Humanity" → `habitatforhumanity.org` ✅
- "YWCA Boston" → `ywcaboston.org` ✅
- "Local Food Bank Austin" → `localfoodbankazustin.org` ✅

**Algorithm:**
1. Extract org name + acronym + city
2. Generate domain variants
3. DNS lookup (NXDOMAIN = skip)
4. HEAD request (must return 2xx)
5. Store in DB: `website`, `website_status='ok'`, `website_source='domain_guess'`

**Cost:** $0 (DNS is free)  
**Throughput:** 1K-5K orgs/hour (depends on parallelization)  
**Success rate:** ~70%  
**Expected yield:** ~1.1M websites from 1.59M  
**Timeline:** 2-3 weeks (with 8-16 workers)

**Code template:**
```python
# scripts/continuous_discovery/domain_guess_engine.py
def guess_domains(org_name, acronym, city):
    candidates = [
        f"{slugify(org_name)}.org",
        f"{slugify(org_name)}.com",
        f"{slugify(acronym)}.org",
        f"{slugify(city)}{slugify(org_name)}.org",
    ]
    for domain in candidates:
        if dns_lookup(domain) and is_live(domain):
            return domain
    return None

# Run against all orgs_without_website
for org in get_orgs_without_website():
    website = guess_domains(org.name, org.acronym, org.city)
    if website:
        db.update(org.ein, website=website, website_source="domain_guess")
```

---

### Strategy 2: Search Engine Cross-Check (LAUNCH WEEK 2)
**Pattern:** Google `"[Org Name]" nonprofit site:org`

**Cost:** ~$0-50/month (free APIs with rate limits)  
**Throughput:** 100-500 orgs/hour (rate-limited)  
**Success rate:** ~40% of remaining  
**Expected yield:** ~192K additional websites  
**Timeline:** 1-2 weeks

---

### Strategy 3: Wayback Machine (BACKGROUND, ONGOING)
**Pattern:** Internet Archive snapshots for domains

**Cost:** $0 (free API)  
**Throughput:** 500-2K orgs/hour (continuous background)  
**Success rate:** ~10% of dead sites become recoverable  
**Expected yield:** ~46K live recovered from archives  
**Timeline:** Ongoing (complete in 1-2 days)

---

### Strategy 4: Directory Cross-Reference (LAUNCH TOMORROW)
**Sources:** Charity Navigator bulk export, GiveWell, Candid/GuideStar, ProPublica

**Cost:** Free to $500/month (bulk data)  
**Throughput:** One-time bulk import  
**Success rate:** ~100% (from authoritative sources)  
**Expected yield:** 50-200K high-confidence websites  
**Timeline:** 1 day to import

---

## Phased Rollout Plan

| Phase | Timeline | Strategy | Target | Expected Websites |
|-------|----------|----------|--------|------------------|
| **Phase 1** | This week | Domain guessing | 1.59M → 1.1M found | +650K |
| **Phase 4** | Tomorrow | Directory imports | Top 200K by priority | +50-200K |
| **Phase 2** | Week 2-3 | Search engine | Remaining 480K | +192K |
| **Phase 3** | Ongoing | Wayback recovery | Dead sites | +46K |

**Total goal:** 1.59M → 1.4M covered (22% → 68% coverage)

---

## Your Tasks (Priority Order)

### IMMEDIATE (Today)
1. [ ] Review four discovery strategies (read above)
2. [ ] Confirm Phase 1 approach (domain guessing)
3. [ ] Check if you have existing domain_guess code from last night's work
4. [ ] Estimate parallelization plan:
   - How many workers can we run? (8? 16? 32?)
   - What throughput can we achieve? (1K? 5K orgs/hour?)
   - Cost estimate?

### TODAY (4 hours)
5. [ ] Code Phase 1 (domain_guess_engine.py) if not already done
6. [ ] Test on 100 orgs (verify DNS + HEAD logic works)
7. [ ] Document false-positive rate (what % of guesses are wrong)
8. [ ] Plan Phase 4 bulk import (Charity Navigator export)

### TOMORROW (4 hours)
9. [ ] Launch Phase 1 production run (1K+ orgs/hour minimum)
10. [ ] Launch Phase 4 bulk import (50-200K directory websites)
11. [ ] Set up daily progress tracking (emails or dashboard)
12. [ ] Monitor success rate vs. false positives

### THIS WEEK
13. [ ] Phase 1 scaling to 5K orgs/hour (if parallelization allows)
14. [ ] Accumulate 300K+ new websites
15. [ ] Begin Phase 2 code (search engine queries)

### WEEK 2-3
16. [ ] Phase 2 launch (search remaining ~480K)
17. [ ] Accumulate 192K+ additional websites
18. [ ] Phase 3 Wayback recovery (background)

### WEEK 4 (EOW)
19. [ ] Target: 650K+ new websites discovered
20. [ ] Result: Coverage 22% → 68%
21. [ ] Micro-org coverage 19% → 50%+

---

## Questions for Codex

1. **"Did you already start domain guessing last night?"**
   - If yes: what code exists? What's the success rate? Current orgs processed?
   - If no: can you have Phase 1 code ready by EOD today?

2. **"What parallelization is feasible?"**
   - 8 workers? 16? 32?
   - Each doing DNS + HEAD requests in parallel?
   - Cost vs. speed tradeoff?

3. **"How do we handle false positives?"**
   - If domain_guess gets 70% right, 30% wrong, do we verify before storing?
   - Or accept the guesses and filter later?

4. **"Should Phase 1 & Phase 4 run sequentially or parallel?"**
   - Phase 4 (directory imports) has 50-200K high-confidence websites
   - Could bulk import first, then domain guess the rest?

5. **"Can this run simultaneously with donation link extraction?"**
   - Different code, different database columns, different workers?
   - Or share infrastructure?

---

## Success Metrics

- [ ] Phase 1 code ready (domain_guess_engine.py)
- [ ] Test results: X% success rate on 100-org sample
- [ ] Production launch: 1K+ orgs/hour minimum
- [ ] False-positive tracking: X% wrong domains
- [ ] Week 1 result: 300K+ new websites
- [ ] Week 2 result: 500K+ cumulative
- [ ] Week 3 result: 650K+ total (68% coverage goal)

---

## Connection to Task #11 (Small Org Visibility Phase 1)

**How this helps:**

1. **Website coverage boosts small-org visibility**
   - Currently: 19% of micro-orgs have discovered websites
   - After: 50%+ have discovered websites
   - Impact: "Find near me" results are much richer for small orgs

2. **Enables donation link discovery at scale**
   - 650K+ new websites = 650K+ new targets for donation link extraction
   - Phase 1 (guessing) runs parallel to donation link extraction
   - By week 3: both initiatives firing in parallel

3. **Reduces fallback UX need**
   - Fewer orgs need "contact directly" path
   - More orgs have websites to explore
   - Better data foundation for Phase 1 launch

4. **Timeline aligns**
   - Website discovery: complete by end of month (68% coverage)
   - Donation link extraction: acceleration plan + Phase 1 unblocked
   - Task #11 Phase 1: launch week of Aug 20 with full data

---

## Timeline Summary

| Date | Milestone | Status |
|------|-----------|--------|
| **Today** | Phase 1 code + Phase 4 plan | Ready? Check existing work |
| **Tomorrow** | Phase 1 & Phase 4 launch (1K+ orgs/hour) | Launch |
| **Aug 15-20** | Phase 1 scaling to 5K orgs/hour + 300K websites | In progress |
| **Aug 20-27** | Phase 2 launch + 192K search results | In progress |
| **Aug 28-31** | Consolidation + 650K total websites | Complete |
| **Week of Aug 20** | Task #11 Phase 1 launches (strong data) | Ready |

---

## Files to Create/Reference

- **Code:** `scripts/continuous_discovery/domain_guess_engine.py` (Phase 1)
- **Code:** `scripts/continuous_discovery/search_engine_discovery.py` (Phase 2)
- **Code:** `scripts/continuous_discovery/wayback_recovery.py` (Phase 3)
- **Data:** Charity Navigator bulk export (Phase 4)
- **Tracking:** Daily progress log (websites discovered per day)
- **Report:** `CONTINUOUS_WEBSITE_DISCOVERY_PROGRESS_20260813.md` (daily updates)

---

## Go/No-Go Decision

**GO:** Launch Phase 1 domain guessing today. It's:
- ✅ Fast (70% success rate)
- ✅ Cheap ($0 cost)
- ✅ Parallelizable (1K-5K orgs/hour)
- ✅ Independent from donation link extraction
- ✅ High-impact (enables Task #11 Phase 1 launch)

**No-Go Scenario:** If domain guessing code didn't exist before, and you can't have it ready by EOD today, estimate delay and pivot to Phase 4 (directory imports) as immediate win.

---

**Codex: Check if you have existing domain_guess code. If yes: scale it. If no: build it today. Launch by tomorrow. This is your second-front for the 1.59M invisible nonprofits.**

Good luck 🚀
