# Continuous Nonprofit Website Discovery Initiative
**Date:** 2026-08-13  
**Status:** 🚀 NEW INITIATIVE — Parallel to Donation Link Extraction  
**Owner:** Codex (Discovery Team — Branch 2)  
**Objective:** Find websites for nonprofits currently missing them

---

## The Opportunity

**Current State:**
- 2,056,834 total US nonprofits
- 461,682 with discovered websites (22.4%)
- **1,595,152 with NO website discovered yet (77.6%)**

**Bottleneck by Size:**
- Micro-orgs (<$150K): 19.0% website coverage (1.04M with websites)
- Professional ($150K-$700K): 28.6% coverage
- Established (>$700K): 25.3% coverage

**Hidden Opportunity:** 77.6% of nonprofits are invisible in search because we haven't found their websites yet.

---

## Mission

**Find websites for the 1.59 million nonprofits without one.**

This is parallel to the donation link extraction work (which improves giving for the 461K we already found). Website discovery directly enables Task #11 Phase 1 (small org visibility).

---

## Discovery Strategies

### Strategy 1: Domain Guessing (Fast, 70% success rate)

**Pattern:** `[org_name][org_acronym][domain_extensions]`

Examples:
- "habitat for humanity" → `habitatforhumanity.org` ✅
- "YWCA Boston" → `ywcaboston.org`, `ywcaboston.com` ✅
- "Local Food Bank" → `localfoodbank.org`, `localfoodbank.com` ✅

**Algorithm:**
1. Extract org name from registry
2. Generate domain variants:
   - Full name: `[full name slugified].org`
   - Acronym: `[acronym].org`, `[acronym].com`
   - City + name: `[city][name].org` (for local orgs)
3. DNS lookup: Check if domain exists
4. HEAD request: Verify it's live (200 OK)
5. Store: `website`, `website_status`

**Cost:** Free (DNS lookups) or cheap (bulk HEAD requests)  
**Throughput:** 1,000-5,000 orgs/hour (depends on parallelization)  
**Expected yield:** ~70% success rate = ~1.1M websites from 1.59M

---

### Strategy 2: Search Engine Cross-Check

**Pattern:** Google + Bing + DuckDuckGo for "[Org Name] nonprofit"

**Algorithm:**
1. For orgs with no website from Strategy 1
2. Search: "[full org name] nonprofit site:org"
3. Parse top 3 results for `.org` domains
4. Verify domain (HEAD request)
5. Store: `website`, `website_status`, `search_source`

**Cost:** $0 (use public search API or scraping with rotation)  
**Throughput:** 100-500 orgs/hour (rate-limited by search engines)  
**Expected yield:** ~40% of remaining = ~600K additional websites

---

### Strategy 3: Wayback Machine (For Dead Sites & Old Records)

**Pattern:** Internet Archive snapshot of org website

**Algorithm:**
1. For orgs with dead websites from Strategy 1/2
2. Query Wayback Machine API for domain
3. If snapshot exists:
   - Extract live site links from snapshot
   - Verify current status
   - Store: `website`, `archived_snapshot_url`, `website_status`

**Cost:** Free (Wayback API)  
**Throughput:** 500-2,000 orgs/hour  
**Expected yield:** ~10% of domains that used to exist = ~160K

---

### Strategy 4: Nonprofit Directory Cross-Reference

**Sources:**
- Charity Navigator (2.1M nonprofits, publishes bulk data)
- GiveWell (high-confidence sites for rated orgs)
- Candid/GuideStar (website field in nonprofit profiles)
- ProPublica (website URLs from 990 filings)

**Algorithm:**
1. For highest-priority orgs (micro-orgs in high-need categories)
2. Cross-check against directory APIs/bulk exports
3. If website found in external DB:
   - Verify current status (HEAD request)
   - Store with source attribution
   - Store: `website`, `website_source`, `website_status`

**Cost:** Free to $500/month (bulk data licensing)  
**Throughput:** One-time bulk import (50K-200K in first run)  
**Expected yield:** ~50-200K additional websites (high confidence)

---

## Phased Rollout

### Phase 1: Domain Guessing (This Week)

**Goal:** Quick win on 1.1M orgs with guessable domains

**Implementation:**
```python
# scripts/continuous_discovery/domain_guess_engine.py
def guess_domains(ein, org_name, city, state):
    """Generate domain variants and check if live"""
    candidates = [
        f"{slugify(org_name)}.org",
        f"{slugify(org_name)}.com",
        f"{extract_acronym(org_name)}.org",
        f"{slugify(city)}{slugify(org_name)}.org",
    ]
    
    for domain in candidates:
        if dns_lookup(domain) and is_live(domain):
            return domain
    return None

# Run against all 1.59M with no website
for org in orgs_without_website:
    website = guess_domains(org)
    if website:
        db.update(ein=org.ein, website=website, website_source="domain_guess")
```

**Throughput:** 1K-5K orgs/hour = 1.59M in 320-1,590 hours (13-66 days, depending on parallelization)

**Target:** 70% success = 1.11M websites discovered

**Timeline:** 2-3 weeks (with 8-16 parallel workers)

---

### Phase 2: Search Engine Cross-Check (Week 2-3)

**Goal:** Find websites for remaining ~480K orgs (those without guessable domains)

**Implementation:**
```python
# scripts/continuous_discovery/search_engine_discovery.py
def search_for_website(org_name, city):
    """Search Google/Bing for nonprofit website"""
    query = f'"{org_name}" nonprofit {city} site:org'
    results = search(query)  # Use google-search-api or similar
    
    for result in results[:3]:
        if is_nonprofit_site(result):
            return result.url
    return None
```

**Throughput:** 100-500 orgs/hour (rate-limited)  
**Expected yield:** ~40% of 480K = 192K additional websites  
**Timeline:** 1-2 weeks

---

### Phase 3: Wayback Machine (Ongoing)

**Goal:** Recover websites for organizations with dead links

**Implementation:**
- Run as background job (low priority, continuous)
- Check Wayback for any domain previously found but marked `dead`
- If live snapshot found, update status + archive link

**Throughput:** 500-2,000 orgs/hour (continuous background)  
**Expected yield:** ~10% of 461K dead sites = 46K recoveries  
**Timeline:** Ongoing (complete in 1-2 days, then maintain)

---

### Phase 4: Directory Cross-Reference (Parallel to Phase 1)

**Goal:** High-confidence websites from external authoritative sources

**Implementation:**
- Import Charity Navigator bulk export (2.1M nonprofits, website field)
- Match by EIN + org name
- Verify URL is live
- Store with source attribution

**Throughput:** Bulk import (one-time 50K-200K)  
**Timeline:** 1 day

---

## Success Metrics

| Phase | Target | Current | Goal |
|-------|--------|---------|------|
| **Phase 1 (Guessing)** | 1.59M needs → 1.11M found | 461K total | +650K websites |
| **Phase 2 (Search)** | 480K needs → 192K found | — | +192K websites |
| **Phase 3 (Wayback)** | 461K dead → 46K recovered | 37,871 dead | +46K live |
| **Phase 4 (Directories)** | Top 200K orgs → 50-200K found | — | +50-200K websites |
| **Total Goal** | 1.59M → ~1.4M covered | 461K (22.4%) | +939K (46% coverage) |

**Result:** Website coverage from 22.4% → 68.4% (46 percentage points)

---

## Resource Requirements

**Codex Tasks (Parallel Branches):**
- **Branch 1 (Donation Link Extraction):** 1 stream, ongoing (current audit + acceleration)
- **Branch 2 (Website Discovery):** 1 stream, high throughput (this initiative)

**Machines:**
- Domain guessing: 8-16 parallel workers (CPU-only, cheap)
- Search: 4-8 workers (network-bounded, cheap)
- Wayback: Background job (minimal resources)

**Cost:**
- Domain guessing: ~$0 (DNS is free)
- Search engine queries: ~$0-50/month (use free APIs or bulk deals)
- Wayback: ~$0 (free API)
- Infrastructure: Reuse existing workers

**Timeline:** 2-3 weeks for 650K+ new websites

---

## Data Quality & Verification

**For Each Discovered Website:**

```json
{
  "ein": "123456789",
  "website": "habitatforhumanity.org",
  "website_source": "domain_guess | search_engine | wayback | charity_navigator",
  "website_status": "ok | dead | redirect | error",
  "discovery_date": "2026-08-13T12:00:00Z",
  "verification_method": "dns_lookup | head_request | screenshot",
  "confidence": 0.95,
  "notes": "Verified live, responded with HTTP 200"
}
```

**Validation Rules:**
- DNS must resolve (NXDOMAIN = discard)
- HEAD request must return 2xx (not 4xx/5xx)
- Domain must match `.org` (nonprofits) or `.com` (backup)
- No redirect loops or parked domains
- Screenshot confidence: >80% for "nonprofit" signals (nav, mission statement, etc.)

---

## Integration with Task #11 (Small Org Visibility)

**How This Helps:**

1. **Website coverage:** 22% → 68% enables "Find near me" discovery
2. **Micro-org boost:** Current 19% → 50%+ (most gain in small-org cohort)
3. **Fallback UX:** Fewer orgs need "contact directly" path (more have websites)
4. **Donation link base:** 939K new websites = 939K new targets for donation link extraction
5. **Timeline:** Complete Phase 1-2 by end of month → Phase 1 launches on strong data foundation

---

## Handoff to Codex

### Immediate (Today)
1. Review discovery strategies (domain guessing, search, wayback, directories)
2. Prioritize Phase 1 (domain guessing) — fast, 70% success rate
3. Estimate parallelization plan (8-16 workers?)
4. Confirm throughput target: 1.59M orgs in 2-3 weeks?

### Tomorrow
1. Phase 1 code ready (domain_guess_engine.py)
2. Phase 4 bulk import ready (Charity Navigator export)
3. Launch domain guessing at scale

### This Week
1. Phase 1 in production: 1K-5K orgs/hour discovering new websites
2. Phase 4 bulk import: 50-200K high-confidence websites
3. Monitor: success rate, false positives, dead-link rate

### Week 2-3
1. Phase 2: Search engine queries for remaining ~480K
2. Phase 3: Wayback recovery for dead links (background)
3. Target: 650K+ new websites, 46% coverage achieved

---

## Questions for Codex

1. **"Can we parallelize domain guessing to 5K orgs/hour?"**
   - Would need 10-20 workers with DNS rotation
   - Cost estimate?

2. **"Should we batch Phase 1 & Phase 4 together?"**
   - Phase 4 (directories) has 50-200K high-confidence sites
   - Could do bulk import first, domain guessing second?

3. **"What's our false-positive tolerance?"**
   - If domain_guess gets 70% right and 30% wrong, should we verify before storing?
   - Or accept the guesses and fix later?

4. **"How do we handle parked domains and redirect loops?"**
   - Is the verification logic robust enough for 1.59M domains?

---

## Success Criteria

- [ ] Phase 1 code ready (domain_guess_engine.py)
- [ ] Phase 4 bulk import ready (Charity Navigator export)
- [ ] Parallelization plan documented (workers, throughput, cost)
- [ ] False-positive detection strategy in place
- [ ] Production launch: 1K+ orgs/hour discovering websites
- [ ] Daily progress tracking (emails or dashboard)
- [ ] Target: 650K+ new websites by end of month

---

## Timeline

| Date | Phase | Target | Owner |
|------|-------|--------|-------|
| **Today** | Planning + Phase 1 code | Ready to launch | Codex |
| **Tomorrow** | Phase 1 + Phase 4 launch | 1K orgs/hour | Codex |
| **Week 1 (Aug 15-20)** | Phase 1 scaling | 5K orgs/hour + 300K websites | Codex |
| **Week 2 (Aug 21-27)** | Phase 2 launch | 100-500 orgs/hour + 192K websites | Codex |
| **Week 3 (Aug 28-31)** | Consolidation | 650K+ total new websites (68% coverage) | Codex |

---

## Impact on Small Org Visibility (Task #11)

**Before Website Discovery Initiative:**
- Micro-org website coverage: 19%
- Fallback UX required for 81% of micro-orgs
- Limited "find near me" results

**After Website Discovery Initiative:**
- Micro-org website coverage: 50%+
- Fallback UX needed for 50% or less
- "Find near me" discovery much richer
- 650K+ new orgs visible to donors/volunteers

**Result:** Task #11 Phase 1 launches with massively improved data foundation

---

**Codex: Launch when ready. This runs parallel to donation link extraction. Both are needed for Task #11 success.**

Good luck 🚀
