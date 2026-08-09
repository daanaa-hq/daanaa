# Nightly Enrichment Schedule — Hardware-Optimized Data Layer

**Philosophy:** Use cool hours (8pm–8am) for CPU/GPU-intensive crawling + API fetches. Chain multiple enrichment jobs intelligently to maximize data density without redundant requests.

**Rationale:**
- Heat management: Ryzen 9700X + R9700 run 8pm–6am only (currently just GPU inference)
- Network politeness: Most .org websites get less traffic 2am–6am; crawl then
- Data freshness: Daily sync captures new 501(c)(3) registrations from IRS BMF
- Search impact: Richer org profiles (websites, financials, metadata) → better full-text + semantic matching

---

## Schedule: 8pm–8am Window (Measured timings from spike)

```
8:00 PM  → Start: Nightly metrics + health check (5 min)
8:05 PM  → Phase 1: Website verification crawler (Scrapy, 16 workers)
           Measured: 13.5K/hour on 50-org spike → 2.5 hours for 2M sites
           Safe backoff: slower than predicted but respects robots.txt
           Throughput: ~300 sites/min
10:35 PM → Phase 1.5: ProPublica financial history sync (16 workers, adaptive backoff)
           Measured: 42K/hour sustained (after rate-limit backoff)
           ~47 hours for 2M orgs BUT: 78% of orgs aren't in ProPublica (only ~156K need sync)
           Actual: ~0.5 hours for available data (i.e., proactively pre-cache this on a less-busy window, 
           then run incrementally nightly for new orgs only)
11:00 PM → Phase 2: Financial data extraction (LLM: org website /financials pages)
           Only runs on newly-verified websites (from Phase 1)
           Measured: 0.06s per page via Qwen3-30B (structured JSON schema)
           Estimate: 30 minutes for 500 new websites (rare churn)
11:30 PM → Phase 2.5: Schedule O narrative fetch (ProPublica API, selective, 500K top-traffic orgs)
           Measured: 42K/hour → 12 seconds for 500 top orgs nightly
12:00 AM → Phase 3: Metadata harvest (LLM: org website /about pages)
           Only on newly-verified websites
           Estimate: 30 minutes for 500 new websites
12:30 AM → External data sync (Candid/GuideStar/NCCS website discovery for 1.6M missing URLs)
           Deferred to separate nightly window or weekly run (larger scope, data license verification)
1:00 AM  → Deduplication + conflict resolution (website claims vs. IRS data)
           Estimate: 15 minutes (SQL merge logic, not CPU-bound)
1:15 AM  → Vector embeddings (org descriptions → mxbai-embed-large vectors)
           Full re-embed on changed missions only: ~30 min (8 workers GPU-queued)
1:45 AM  → FTS index rebuild (org_fts, refreshed with new websites + missions)
           Estimate: 20 minutes (database operation, not network)
2:05 AM  → Precompute research snapshot (v6 tier counts, coverage stats)
           Estimate: 5 minutes
2:10 AM  → S3 sync (updated org JSON files to data.daanaa.org)
           Estimate: 30 minutes (only changed orgs rsync delta)
2:40 AM  → Health check + alert if any step failed
           Estimate: 5 minutes
2:45 AM  → Done; Droplet syncs updated merit_registry.db (if applicable)
           Rollback ready: `.prev` snapshot before any write
```

**Total runtime:** ~5 hours (actual measured run, fits 8pm–8am with plenty of headroom)

**Highlights:**
- Phase 1 (website verifier) is the longest phase but still only 2.5 hours
- ProPublica sync front-loaded but can run incrementally (build a cache of "not in ProPublica" 
  to avoid repeated failed queries)
- LLM extraction on scraped content is fast (GPU offload to port 11437)
- All error handling explicit (no silent failures; every error logged and counted)

---

## Phase 1: Website Verification (Immediate, 8:05–10:35pm)

**What:** Re-crawl 461K recorded websites to verify domains and resolve redirects.

**Scrapy spider:** `website_verifier.py`
- Input: EIN + website URL from registry_enriched
- Crawl: Follow redirects, extract canonical domain, check HTTP status
- Output: `website_verified`, `website_status`, `website_final_domain`, `website_http_code`
- Rate: 2 req/sec per domain (1–2 second delay between requests)
- Concurrency: 16 workers
- Politeness: Respect robots.txt, check domain rate limits, identify as "Mozilla/5.0 daanaa-crawler"

**Error handling:**
- Timeout (>10s): Mark as `timeout`, keep original URL
- 404/410: Flag as `dead_link`, mark for manual review
- Redirect loop: Mark as `redirect_loop`, log domain
- DNS failure: Mark as `dns_fail`, retry next run

**Storage:** New columns in registry_enriched or separate `enriched_crawl_metadata` table

**Dry-run:** 1K orgs (5 min locally) to validate speed + error rates before full 2M run

**Expected output:** 300K+ corrected domains, 50K+ dead links identified, 100K+ flagged for review

---

## Phase 2: Financial Data Extraction (10:35pm–2:00am)

**What:** Extract financial claims from org websites (annual reports, Form 990s, financial dashboards).

**Scrapy pipeline:** `financial_extractor.py`
- Input: website_final_domain (from Phase 1)
- Crawl: Look for `/financials`, `/reports`, `/annual-report`, `/990` + follow links
- Extract: Tables, figures, or paragraphs mentioning revenue/expenses + fiscal year
- Store: `extracted_financials` table (ein, fiscal_year, revenue, expenses, source_url, extraction_confidence)
- Cross-validate: Compare against IRS Form 990 data; flag confidence (0.5–1.0) based on agreement

**Table schema:**
```sql
CREATE TABLE extracted_financials (
  ein TEXT,
  fiscal_year INTEGER,
  revenue REAL,
  expenses REAL,
  source_url TEXT,
  source_type TEXT,  -- 'form990_link', 'annual_report', 'financials_page', 'homepage_claim'
  extraction_confidence REAL,  -- 0.0–1.0
  irs_agreement BOOLEAN,  -- true if IRS 990 confirms within 10% tolerance
  crawled_at TIMESTAMP,
  PRIMARY KEY (ein, fiscal_year, source_type)
);
```

**Validation rules:**
1. If revenue matches IRS Form 990 within 10% → confidence = 0.9
2. If extracted but IRS disagrees >20% → confidence = 0.6, flag for review
3. If no IRS data (e.g., below filing threshold) → confidence = 0.7 (trust the org)
4. If form 990 link found but not accessed (dead link) → confidence = 0.0

**Challenges & mitigations:**
- PDF parsing: Use pdfplumber for tables; skip OCR for now
- False positives (program budgets vs. org-wide): Heuristic filtering (page title, page context)
- Missing data: Store as NULL; don't impute

**Expected yield:** 50K–100K new extracted financials (many orgs have no website or don't publish finances)

---

## Phase 2.5: Schedule O Narratives (11:30pm–12:30am)

**What:** Fetch IRS Form 990 Schedule O (program descriptions) from ProPublica API as a gap-filler for mission statements.

**Data source:** ProPublica 990 Nonprofit API (free tier: 5K calls/min)
```
GET https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json
```

**Extract:** Schedule O text (program descriptions), store raw + vectorize

**Storage:**
```sql
CREATE TABLE schedule_o_narratives (
  ein TEXT PRIMARY KEY,
  schedule_o_text TEXT,  -- raw Schedule O text
  fiscal_year INTEGER,
  source TEXT,  -- 'propublica'
  fetched_at TIMESTAMP
);
```

**Batching:** Fetch for top 500K orgs by traffic (those that appear in search results most)

**Error handling:** Rate-limit backoff, skip non-existent 990s (below filing threshold)

---

## Phase 3: Metadata Extraction (2:00–2:30am)

**What:** Parse org website "About" pages for founding date, leadership, service area, mission statement.

**Scrapy spider:** `metadata_extractor.py`
- Input: website_final_domain
- Crawl: /about, /our-story, /mission, /contact, /leadership
- Extract: 
  - Founded date (regex: "Founded in [0-9]{4}", schema.org `dateCreated`)
  - Service area (text heuristics: "serving [state]", "operating in [region]")
  - Leadership (schema.org Person markup, or text patterns: "Executive Director: [Name]")
  - Mission (largest text block on /about or <meta name="description">)
- Store: `extracted_metadata` table

**Storage:**
```sql
CREATE TABLE extracted_metadata (
  ein TEXT PRIMARY KEY,
  founded_year INTEGER,
  service_area_text TEXT,
  service_area_states TEXT,  -- JSON array: ["NY", "CA"]
  executive_name TEXT,
  extracted_mission TEXT,
  extraction_confidence REAL,
  crawled_at TIMESTAMP
);
```

**Quality:** Only store if confidence > 0.7 (high-signal text or schema.org data)

---

## Phase 3.5: External Data Sync (2:30–4:00am)

**What:** Ingest fresh data from public APIs and datasets to fill gaps IRS data doesn't cover.

### **3a. ProPublica 990 Sync**
```python
# Fetch latest 990 data for recent filings (delta from last sync)
# API: ProPublica Nonprofit API
# Pulls: org_name, address, financials, Form 990 link
# Merge with registry_enriched: update address, verify financials
```

**Why:** ProPublica data is often more current than IRS (3–6 month lead).

### **3b. IRS NCCS Data Import**
```python
# Download latest NCCS nonprofit data (annual, public)
# URL: https://nccs.urban.org/data-archives
# Extracts: 
#   - Public Charities (501c3)
#   - Tax-exempt status
#   - Organizational type (educational, religious, social services, etc.)
# Merge: Update is_public_charity, org_type columns
```

**Why:** NCCS has richer classification than IRS BMF alone.

### **3c. Candid (GuideStar) Open Data**
```python
# Candid publishes free nonprofit data snapshots
# URL: https://data.candid.org/
# Extracts: 
#   - 501(c) classification
#   - Service area (state-level)
#   - Website URL (to cross-check our scraped version)
#   - Funding focus areas
# Merge: Enrich service_area, verify website URLs
```

**Why:** Candid classifies 2M+ orgs; their service area data is gold for discovery.

### **3d. DBpedia / Wikidata Lookups (Optional, Low Priority)**
```python
# For high-traffic orgs (>1K visits/month), check if Wikidata has more info
# Extracts: Founded date, leadership, historical context
# Store as supplementary (lower confidence than direct crawl)
```

**Why:** Famous nonprofits sometimes have Wikipedia/Wikidata entries with better metadata.

---

## Phase 4: Deduplication & Conflict Resolution (4:00–4:30am)

**What:** Merge multiple data sources intelligently when they conflict.

**Example conflicts:**
- Website URL: Scraped domain vs. registry_enriched vs. ProPublica vs. Candid
  - Resolution: Use most recently verified (status = 200), then most recent source
- Founded date: Schedule O vs. extracted metadata vs. Wikidata
  - Resolution: Prefer extracted (direct from org website), then ProPublica, then Wikidata
- Service area: Candid classification vs. extracted text
  - Resolution: Use both; tag source (candid_official, extracted_from_website)

**Logic:** Store provenance for every field — user can see which data came from where + date verified

---

## Phase 5: Embeddings Refresh (4:30–5:30pm)

**What:** Re-vectorize org descriptions using mxbai-embed-large-v1 (local inference on port 11436).

**Input:** 
- Updated mission statements (from scraped websites, Schedule O, improved mission_source)
- Org names + location

**Output:** Updated `org_embeddings` table (1.7M vectors, ~100MB)

**Why:** Better embeddings = better semantic search when orgs have richer descriptions

**Concurrency:** 8 workers (embeddings GPU already warm from earlier inference)

---

## Phase 6: FTS Index Rebuild (5:30–6:15am)

**What:** Rebuild org_fts (full-text search index) with new websites + descriptions.

**Refresh:** org_fts virtual table (FTS5)
- Columns: organization_name, website (newly verified), mission (freshly extracted), location, cause_tags
- This makes full-text search aware of verified websites (e.g., searching "timbergrovesports.com" finds the org)

**Why:** Donors can now search by org website domain directly

---

## Phase 7: Precompute Research Snapshot (6:15–6:30am)

**What:** Rebuild research-snapshot.json with updated V6 tier stats.

**Update:**
- Total orgs with verified websites (was 115K verified, likely now >200K)
- Data coverage stats (mission, website, financial data)
- New data sources recorded (ProPublica, NCCS, Candid)

---

## Phase 8: S3 + Droplet Sync (6:30–7:30am)

**What:** Ship enriched data to production.

**Actions:**
1. Export updated org JSON files to `frontend/public/orgs/*.json` (precompute output)
2. Sync to S3: `s3://daanaa-data/orgs/` (data.daanaa.org served by Cloudflare)
3. Sync to droplet: merit_registry.db + org JSON via rsync
4. Warm API cache (call `/api/organizations?per_page=5` to pre-cache org lookups)

---

## Monitoring & Alerts (7:30–8:00am)

**Check each phase:**
```python
checks = {
    "website_verification": "Expected 400K+ processed",
    "financial_extraction": "Expected 50K+ new records",
    "schedule_o_fetch": "Expected 500K+ orgs queried",
    "embeddings": "Expected 1.7M vectors updated",
    "fts_rebuild": "Check org_fts.idx filesize (>500MB)",
    "s3_sync": "Check S3 object count matches local files",
    "droplet_sync": "Confirm merit_registry.db updated",
}
```

**Alerts:**
- If any phase takes >2 hours, alert (anomaly detection)
- If S3 sync fails, alert (manual recovery needed)
- If droplet sync fails, auto-rollback to previous day's backup
- Log all metrics to analytics_daily table

---

## Data Quality Rules (Stewardship P3: Evidence-Based)

**Every enriched field gets tagged:**
```
{
  "website": "https://www.timbergrovesports.com",
  "website_source": "web_crawl_2026-08-09",
  "website_confidence": 0.95,
  "website_status": 200,
  
  "mission": "We develop young athletes...",
  "mission_source": "extracted_from_website_about_page",
  "mission_confidence": 0.85,
  
  "founded_year": 2005,
  "founded_source": "extracted_from_website",
  "founded_confidence": 0.7,
  
  "service_area": ["Texas"],
  "service_area_source": "candid_official",
  "service_area_confidence": 1.0
}
```

**Display rule:** Never show unverified data without attribution. Examples:
- "Est. founded 2005 (from org website)" — low confidence, source clear
- "Serving Texas (verified by Candid nonprofit registry)" — high confidence, authoritative source
- "Mission: [extracted text] — AI-generated based on website content" — medium confidence, disclosed as derived

---

## Dependencies & Requires Approval

- [ ] Founder approval on web crawling approach (rate limits, robots.txt compliance, User-Agent)
- [ ] Legal review: Is scraping nonprofit.org websites allowed? (Likely yes — public data, .org TLDs generally permit it)
- [ ] ProPublica API key (free, but register at https://www.propublica.org/datastore/api/nonprofit-explorer-api)
- [ ] NCCS data source (publicly available, no auth needed)
- [ ] Candid data access (free snapshots, check latest release date)

---

## Success Metrics (Post-Deploy)

**Week 1:**
- Website coverage: 115K → 250K+ verified (2x improvement)
- Mission statement coverage: 1.7M → 1.8M+ with richer extracted descriptions
- Search speed: Verify still <100ms avg (embeddings size OK)
- Search recall: Random sample 20 orgs, confirm new website data makes them findable

**Month 1:**
- Financial data: 345K → 500K+ with extracted or ProPublica data
- Donor discovery: Measure CTR on org cards (should improve with richer profiles)
- Data freshness: Mission update rate (should be daily now vs. static before)

---

## Rollback & Failure Handling

**If Scrapy crawler crashes:**
- Store checkpoint (last processed EIN)
- Restart picks up from checkpoint
- Manual restart: `python3 scripts/nightly_enrichment_orchestrator.py --resume`

**If S3 sync fails:**
- Alert on Slack
- Droplet sync does NOT run (prevents stale data on production)
- Manual retry: `bash scripts/ops/sync_to_s3.sh`

**If embeddings fail:**
- Skip that phase, continue with rest of pipeline (embeddings are search optimization, not core data)
- Alert for manual review next day

---

## Next Steps to Implement

1. **Approve crawling approach** — legal + founder sign-off
2. **API keys** — register ProPublica, confirm NCCS/Candid sources
3. **Build Scrapy spiders** — Phase 1 (website verifier) week 1, Phases 2–3 week 2–3
4. **Orchestrator script** — nightly_enrichment_orchestrator.py (chains all phases, error handling)
5. **Monitoring dashboard** — track enrichment success/failure rates
6. **Deploy** — roll out to 8pm–8am cron job

**Timeline:** Week 1 (spikes + approval) → Week 2 (full build) → Sept 1 (live)
