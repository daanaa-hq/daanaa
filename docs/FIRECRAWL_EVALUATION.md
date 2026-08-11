# Firecrawl Evaluation for Daanaa

**Date:** 2026-08-11  
**Scope:** Read-only exploration; separate from Phase 1-4 (not a blocker)  
**Status:** Assessment only — no installation, configuration, or deployment

---

## Executive Recommendation

**DEFER** firecrawl adoption until:
1. Daanaa's current discovery pipeline reaches coverage limitations or reliability issues
2. Privacy/data retention policies are clarified with firecrawl in writing
3. Cost-benefit is validated against current in-house solution
4. Independence constraints are explicitly addressed

**Do NOT adopt** until founder explicitly authorizes cloud API dependency and potential vendor lock-in.

---

## What Firecrawl Is

**Overview:** Firecrawl is a cloud-based web scraping and content extraction API that converts websites into LLM-ready data formats.

**Core Capabilities:**
- Full-page scraping (HTML, markdown, JSON, screenshots)
- Browser automation (clicking, scrolling before extraction)
- Website crawling and URL discovery
- Rate limit orchestration + rotating proxies
- robots.txt + CAPTCHA detection
- P95 latency: 3.4 seconds, 96% web coverage claimed

**Pricing Model:** Credit-based (freemium + paid tiers)
- Free: 1,000 credits/month, 2 concurrent browsers
- Hobby: 5 concurrent ($16/month estimated)
- Standard: 50 concurrent (~$83/month estimated)
- Enterprise: Custom (zero data retention option available)
- Cost per page: $0.0032–$0.0006 depending on tier

**License:** AGPL-3.0 (core) + MIT (SDKs)

---

## Comparison with Daanaa's Current Discovery Pipeline

### Daanaa's Current Approach

**File:** `scripts/donation_link_pipeline.py` + related discovery scripts

**Strengths:**
- ✅ Pure Python + network, zero external dependencies
- ✅ Deterministic rate-limiting (3–5s per domain, transparent)
- ✅ robots.txt checking built into every request
- ✅ CAPTCHA detection + graceful handling (stop on 403/429)
- ✅ No vendor lock-in, full code control
- ✅ Confidence-based scoring (≥90% required)
- ✅ Evidence records for every verified link
- ✅ Respects ethical constraints from STEWARDSHIP.md
- ✅ No data sent to external APIs, no privacy ambiguity

**Limitations:**
- ❌ Single-threaded per-domain (one request at a time)
- ❌ No browser automation (JavaScript-heavy sites require different approach)
- ❌ Manual scaling (adding concurrency requires careful threading)
- ❌ No cloud redundancy (local failures can block progress)
- ❌ Manual implementation of each feature (more engineering work per new capability)

### Firecrawl's Approach

**Strengths:**
- ✅ Browser automation (handles JavaScript-heavy pages without code changes)
- ✅ Managed infrastructure (rotating proxies, orchestration, scaling)
- ✅ Fast (P95 3.4s, high concurrency)
- ✅ Zero engineering work (API, not custom code)
- ✅ Handles bot detection + CAPTCHA signals
- ✅ robots.txt respected by default

**Weaknesses:**
- ❌ Cloud vendor dependency (firecrawl.dev goes down → Daanaa can't discover)
- ❌ **Privacy unknown**: Data retention policy not disclosed; no written SLA
- ❌ **Cost**: ~$0.0032/page on free tier, scales with usage
- ❌ **Data provenance**: Unclear what firecrawl does with scraped page content
- ❌ **Rotating proxies**: Less transparent than local rate-limiting; harder to debug
- ❌ **Vendor lock-in**: Switching away after adoption is expensive
- ❌ **No direct control**: Rate limits, blocking behavior, algorithm changes set by vendor
- ❌ **Enterprise pricing**: Vague until you negotiate; potential surprise costs
- ❌ **AGPL license**: Viral copyleft; any integration must be open source (may conflict with licensing)

---

## Stewardship Alignment Assessment

### Principle 2: Privacy is a Core Principle

**Risk:** ⚠️ **MEDIUM-HIGH**

Firecrawl's privacy policy does not state:
- How long scraped page content is retained
- Whether content is used for training firecrawl's own systems
- How European GDPR/UK DPA data is handled
- Whether anonymization is applied
- Auditing/compliance certifications

**Current Daanaa approach:** No external data sharing; full control.

**Verdict:** Firecrawl's cloud model introduces third-party data exposure. Without written commitments on data retention (<1 day?) and non-training guarantees, this violates P2 minimization principle.

### Principle 7: Independence Must Be Protected

**Risk:** ⚠️ **MEDIUM**

- Firecrawl service outage = Daanaa can't discover new links
- Firecrawl could theoretically rate-limit or block Daanaa if commercial incentives shift
- Pricing changes could make large-scale discovery unaffordable
- AGPL requirement creates open-source obligation (not harmful, but new constraint)

**Current approach:** Local-only; Daanaa owns reliability and independence.

**Verdict:** Adopting firecrawl introduces a hard dependency on a third party's operational decisions.

### Principle 1: Mission Before Growth

**Risk:** 🟡 **LOW-MEDIUM**

Cost pressure: Once firecrawl is adopted, Daanaa may optimize for "cheaper queries" rather than "better discovery," subtly prioritizing vendor economics over mission.

**Verdict:** Not a showstopper, but worth watching.

### Principle 10: AI is a Tool, Not a Replacement for Responsibility

**Risk:** 🟡 **LOW**

Firecrawl uses internal AI/ML for content extraction. Daanaa would have zero visibility into how that works or when it fails.

**Verdict:** Acceptable if Daanaa maintains separate verification (confidence scoring, evidence records), but introduces a layer of indirection.

---

## Rate Limits & Reliability

### Firecrawl Rate Limits

| Tier | Concurrent | Cost/month | Est. pages/month |
|------|-----------|----------|-------------------|
| Free | 2 | $0 | ~300–600 (1K credits) |
| Hobby | 5 | $16 | ~5K |
| Standard | 50 | $83 | ~100K |
| Growth | 100 | $250+ | ~400K+ |

For Daanaa's scale (2M orgs, ~10% update rate per month = 200K new/modified orgs), **Standard or Growth tier required** ($83–$250+/month minimum).

### Daanaa's Current Rate Limits

- 3–5 seconds between requests per domain
- Roughly 720–1,440 requests per domain per day
- ~100K domains in registry → ~72M–144M requests/month on full crawl
- Single-threaded per domain, but horizontally scalable with multiple workers

**Cost:** $0 (electricity only). **Scaling:** Run more worker processes.

---

## Local Alternatives to Firecrawl

### 1. **Beautiful Soup + Requests** (status: Daanaa uses)
- Pure Python, zero cost
- No JavaScript support
- Suitable for 80% of nonprofit websites (mostly static)

### 2. **Selenium + Python** (status: not currently used)
- Browser automation via Selenium WebDriver
- Local control, works offline
- Slower than firecrawl (requires spawning browser processes)
- Good for high-value targets (executive pages, donation flows)

### 3. **Puppeteer + Node.js** (status: not currently used)
- Headless browser, lightweight
- Faster than Selenium, still local control
- Cost: engineering time to integrate

### 4. **Playwright (Python binding)** (status: not currently used)
- Modern browser automation, similar to Puppeteer
- Cross-browser support
- Local, zero API calls

### 5. **Firecrawl Self-Hosted** (status: possible, not evaluated)
- Deploy firecrawl on own infrastructure
- Retain privacy guarantees + control
- Cost: DevOps complexity + GPU/CPU for browser workers
- Licensing: AGPL (OK for internal use)

---

## Cost-Benefit Analysis

### When Firecrawl Makes Sense

✅ **Adopt if:**
- Daanaa discovers that JavaScript-heavy pages are a major coverage gap (>5% of targets)
- Current pipeline is hitting reliability issues (timeout rate >3%)
- Volunteer engineering capacity is constrained and automation value justifies $83–250/month
- Founder explicitly authorizes cloud vendor dependency

### When Daanaa Should NOT Adopt Firecrawl

❌ **Defer if:**
- Current pipeline covers >95% of targets (status: likely true)
- Reliability is acceptable (<1% failure rate, based on logs)
- Privacy/independence concerns outweigh engineering convenience
- No pressing need that local browser automation (Playwright) wouldn't solve

---

## Recommendation: DEFER + Explore Local Alternative

### Action 1: Defer Firecrawl (Recommended Path)

**Rationale:**
- Daanaa's current discovery pipeline is mature, controlled, and mission-aligned
- Privacy/independence risks are real and not offset by current capability gaps
- Cost ($83–250/month) is not justified without evidence of discovery bottlenecks
- Self-hosting or local browser automation are more privacy-preserving alternatives

**Condition for reconsideration:** When (and if) Daanaa hits discovery limitations:
- Coverage drops below 90% due to JavaScript sites
- Reliability degrades (timeouts, blocking >2% of requests)
- Founder explicitly authorizes cloud dependency

### Action 2: Explore Playwright for Selective Use (Low-Risk Path)

**Rationale:**
- Solves JavaScript problem locally without vendor lock-in
- Zero cost (open source)
- Daanaa retains control + privacy
- Can be deployed incrementally (high-value targets only)

**Scope:**
1. Pilot Playwright on 100 nonprofit websites with JS-heavy donation flows
2. Measure coverage gain vs. engineering time
3. Compare cost (developer hours) vs. firecrawl subscription
4. Document results for future board decision

### Action 3: If Firecrawl Is Adopted Later

**Prerequisites:**
1. Written privacy agreement: data retention ≤7 days, no training use, GDPR compliance
2. Founder written approval: acknowledges vendor dependency and cost commitment
3. Hybrid strategy: Keep local pipeline as fallback; use firecrawl for high-value scale
4. Legal review: Clarify AGPL implications for proprietary code
5. Exit plan: Design system so firecrawl can be replaced with local alternative within 30 days

---

## Key Questions for Firecrawl (If Reconsidered)

1. **Data retention:** How long is scraped content stored? Can we request deletion after processing?
2. **Training:** Is our content used to train firecrawl's models or bundled into datasets sold to third parties?
3. **GDPR/DPA:** What compliance certifications or data processing agreements does firecrawl offer?
4. **Reliability SLA:** What uptime guarantee is offered? What's the RTO/RPO for outages?
5. **Rate limiting:** Can we control which domains firecrawl hits? Audit trail of requests?
6. **Cost transparency:** Enterprise pricing breakdown; can we cap monthly spend?
7. **Integration:** Can we self-host a Daanaa-specific instance? AGPL implications?

---

## References

- Current discovery pipeline: `scripts/donation_link_pipeline.py`
- Firecrawl GitHub: [mendableai/firecrawl](https://github.com/mendableai/firecrawl)
- Firecrawl docs: [docs.firecrawl.dev](https://docs.firecrawl.dev)
- Pricing sources:
  - [Firecrawl Pricing 2026 (WebScraping.AI)](https://webscraping.ai/blog/firecrawl-guide)
  - [Firecrawl Pricing Plans (Scribe)](https://scribehow.com/page/Decoding_Firecrawl_Pricing_Plans)
  - [Firecrawl Pricing Breakdown (eesel AI)](https://www.eesel.ai/blog/firecrawl-pricing)
- Rate limits: [docs.firecrawl.dev/rate-limits](https://docs.firecrawl.dev/rate-limits)
- Stewardship principles: `STEWARDSHIP.md` (especially P2, P7, P10)

---

**Status:** This evaluation is read-only and informational. No firecrawl components have been installed, configured, or deployed. Phase 1-4 is not blocked by this assessment.

**Next step:** Flag this recommendation to founder for consideration in Q3 roadmap planning, separate from Phase 1-4 execution.
