# Scrapy Integration Plan — Website & Financial Data Enrichment

**Goal:** Use Scrapy to enrich 2.05M orgs with verified websites and 5-year financial context.

**Status:** Concept phase (not implemented yet).

---

## Phase 1: Website Verification (High ROI)

**Problem:** 345K+ recorded websites are unverified (many stale like Timbergrove).

**Scrapy approach:**
- Spider: `website_verifier.py` — crawl each org's recorded website URL
- Resolve: redirects, check HTTP status, extract domain from final URL
- Extract: meta tags (canonical, og:url) to find canonical domain
- Store: `website_final_domain_verified`, `website_verification_status` (200/404/timeout/redirect)
- Rate limit: 1-2 req/sec per domain, respect robots.txt/sitemap
- Dry-run: 100 sites (~5 min) to validate before production

**Output:** Update registry_enriched with verified domains; flag 404s for manual review

**Effort:** 8-12 hours (spider + pipeline + error handling + testing)

**Timeline:** Phase 1 ready Week 1

---

## Phase 2: Financial Data Extraction (Medium ROI, Higher Complexity)

**Goal:** Extract financial data from org websites (annual reports, Form 990s, "Financials" pages).

**Approach:**
1. Identify pages: Look for links like "/financials", "/reports", "/annual-report", "/990"
2. Extract: Tables with revenue/expenses (regex + table parsing)
3. Store: `extracted_financials` table (ein, fiscal_year, revenue, expenses, source_url)
4. Validate: Cross-check against IRS Form 990 data to catch bad extractions

**Challenges:**
- Tables vary wildly (HTML, embedded PDFs, images)
- OCR needed for PDF scans → out of scope for now
- False positives (e.g., budget tables for individual programs, not org-wide)

**Scrapy implementation:**
- Spider: `financial_extractor.py` — crawl org website → extract financial claims
- Pipeline: financial_validation.py — cross-validate against IRS data
- Store: `extracted_financials` (keep raw data, flag confidence)

**Effort:** 20-30 hours (spider + PDF handling decision + validation + testing)

**Timeline:** Phase 2 ready Week 3-4

---

## Phase 3: Metadata Extraction (Medium ROI, Lower Risk)

**Extract:** Founded date, CEO/Executive Director, service area (states, counties) from "About" pages.

**Why:** Useful for discovery (filters: "orgs founded in last 5 years") and organizational context.

**Spider:** metadata_extractor.py (schema.org markup + heuristic text parsing)

**Effort:** 10-15 hours

**Timeline:** Phase 3 ready Week 4

---

## Infrastructure Decisions

**Hardware:** Use local Ryzen 9700X + R9700 server (no cloud crawler charges)

**Rate limiting:**
- 1-2 requests/sec per domain (respectful, won't trigger 429s)
- Crawl windows: 8am-6pm only (avoid hammering servers during their downtime)
- Concurrency: 8-16 workers (depends on DNS/socket limits)

**Database:** `enriched_website_crawl` table (ein, url, status, final_domain, extracted_data, crawled_at, checksum)

**Resume capability:** Spider stores last crawled EIN; restart to resume from interruptions

**Dry-run testing:**
1. Local: crawl 100 test orgs, validate output
2. Smoke test: check that valid 200s are stored, 404s flagged
3. Comparison: spot-check 10 extracted financials against Form 990

---

## Integration with Existing Pipeline

**Placement:** Add as Phase 1.5 of overnight pipeline (after v6 scoring, before FTS rebuild)

**Scheduler:** Nightly 10pm–6am (lightweight GPU window already free)

**Dependency:** Add `scrapy` to requirements.txt; configure settings.py for politeness

---

## Stewardship & Risk

**P3 (Evidence-based):** Extracted data flagged with `source: "org_website"` + `confidence: 0-1`; never presented as authoritative without IRS cross-check.

**P5 (No weaponization):** Website discovery is neutral (helps users find correct org, not rank orgs).

**P7 (Independence):** No ranking changes; data is additive only.

**Risk:** High-volume crawling could trigger rate limiting or IP bans.
- Mitigation: Respectful delays, User-Agent compliance, check robots.txt, stop if 429

---

## Go/No-Go Gate (before implementation)

- [ ] Founder approval on crawling approach (robots.txt respect, rate limits)
- [ ] Legal: check if scraping financials from .org websites requires explicit permission
- [ ] ETA reality-check: can 2M sites be crawled in 8h window nightly? (rough: 2M / 16 workers / 2 req/sec = ~2.5 hours → feasible)

---

## Next Steps

1. **Spike (4 hours):** Prototype website_verifier spider on 1K test orgs, measure speed
2. **Decide:** Phase 1 (web verification) ship without Phase 2/3, or bundle?
3. **Implement:** Phase 1 ready for nightly cron by end of week
