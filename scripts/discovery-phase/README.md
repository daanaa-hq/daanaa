# Discovery Phase Experimental Scripts

**Status:** Active development, not production-ready  
**Date created:** 2026-07-31  
**Owner:** Engineering (Extended Discovery Phase agents)  
**Budget:** GPU time (night window, 8pm-6am)

---

## Purpose

These scripts are part of the **Extended Discovery Phase** — enriching org data through website discovery, leadership network extraction, state AG registries, and volunteer/donation platform integration. They run as autonomous agents with human oversight.

---

## Scripts by Category

### Website Discovery (3 scripts)

| Script | Purpose | Status | Last Run |
|--------|---------|--------|----------|
| `nonprofit_website_discovery.py` | Discover orgs via volunteer/civic engagement platforms | Active | 2026-07-30 |
| `extract_990n_websites.py` | Extract websites from Form 990-N e-postcard data | Active | 2026-07-30 |
| `extract_990n_websites_parallel.py` | Parallel variant for faster extraction | Testing | 2026-07-30 |

### Leadership Network Discovery (2 scripts)

| Script | Purpose | Status | Last Run |
|--------|---------|--------|----------|
| `agent6_leadership_network_discovery.py` | Map nonprofit websites via 990 executive/board networks | Active | 2026-07-30 |
| `agent6_leadership_network_fast.py` | Fast variant (lower coverage, higher speed) | Testing | 2026-07-30 |

### State AG Registry Discovery (3 scripts)

| Script | Purpose | Status | Last Run |
|--------|---------|--------|----------|
| `state_ag_discovery_framework.py` | Generic framework for multi-state 990 ingestion | Active | 2026-07-30 |
| `state_ag_discovery_colorado.py` | Colorado AG registry integration | Testing | 2026-07-30 |
| `state_ag_discovery_propublica.py` | ProPublica API integration for state AG data | Testing | 2026-07-30 |

### Donation Platform Discovery (1 script)

| Script | Purpose | Status | Last Run |
|--------|---------|--------|----------|
| `extract_from_donation_platforms.py` | Extract org data from GiveWell, Giving USA, etc. | Active | 2026-07-30 |

### General Purpose Scraper (1 script)

| Script | Purpose | Status | Last Run |
|--------|---------|--------|----------|
| `intelligent_nonprofit_webscraper.py` | Smart web scraping for org websites (fallback) | Testing | 2026-07-30 |

### 990-N Comprehensive Extraction (1 script)

| Script | Purpose | Status | Last Run |
|--------|---------|--------|----------|
| `extract_990n_comprehensive.py` | Comprehensive e-postcard extraction with validation | Active | 2026-07-30 |

### Volunteer Platform Consolidation (four scripts in `volunteer-consolidation/`, one at this directory root)

| Script | Purpose | Status | Notes |
|--------|---------|--------|-------|
| `volunteer_platform_aggressive_scraper.py` | Aggressive crawl of volunteer platforms | Variant A | Consolidate into one best version |
| `volunteer_platform_comprehensive_scraper.py` | Comprehensive variant | Variant B | Consolidate into one best version |
| `comprehensive_volunteer_platform_extraction.py` | Complete extraction | Variant C | Consolidate into one best version |
| `extract_volunteer_platform_websites.py` | Dedicated extraction | Variant D | Consolidate into one best version |
| `final_volunteer_websites_extractor.py` | Marked as "final" | Variant E | Consolidate into one best version |

**Note:** These 5 scripts do similar work. Need to consolidate into one canonical version.

---

## Running These Scripts

### Prerequisites
```bash
# Activate venv
source ~/meritgiving/venv/bin/activate

# For parallel jobs
export WORKERS=8  # or higher if GPU headroom available
```

### Individual Script Runs

```bash
# Website discovery
python3 scripts/discovery-phase/nonprofit_website_discovery.py

# Leadership network discovery (slower, high-quality)
python3 scripts/discovery-phase/agent6_leadership_network_discovery.py --limit 5000

# State AG discovery
python3 scripts/discovery-phase/state_ag_discovery_framework.py --source colorado --validate

# Donation platform extraction
python3 scripts/discovery-phase/extract_from_donation_platforms.py

# 990-N extraction (parallel)
python3 scripts/discovery-phase/extract_990n_websites.py --workers 8
```

### Batch Run (Orchestrated)

This experimental directory is not part of the production orchestrator. Any future
integration with `scripts/core/overnight_pipeline.py` is planned, not yet built.

---

## Output & Storage

All scripts write to:
- **Staging:** `/tmp/discovery-phase-<date>/` (temporary)
- **Database:** Directly to `data/merit_registry.db` tables (after validation)
- **Logs:** `logs/discovery-phase-<script>.log`

**Data flow:**
1. Script discovers/extracts org data
2. Validation checks (EIN uniqueness, data integrity)
3. Staging in temp database
4. Manual review (if needed)
5. Merge to production `merit_registry.db`

---

## Known Issues & Gaps

- **Volunteer scripts (5 variants):** Need consolidation. Choose one best version or merge best-of-all.
- **Slow discovery:** Leadership network discovery is slow (~1K orgs/hour). Fast variant available but lower coverage.
- **Rate limiting:** Website scrapers respect robots.txt but may hit rate limits on some platforms.
- **Data freshness:** 990-N data is updated annually; websites may lag by months.

---

## Performance & Budget

**GPU requirements:** Night window (8pm-6am UTC) preferred to avoid daytime load

| Script | Estimated Time | Data Volume | GPU/CPU |
|--------|---|---|---|
| Website discovery | 2-3h | 50K websites | CPU-bound |
| Leadership networks | 4-6h | 20K networks | CPU-bound |
| State AG discovery | 1-2h | 100K orgs | Network-bound |
| 990-N extraction | 1h | 200K orgs | CPU-bound |
| Volunteer platforms | 3-4h | 10K platforms | Network-bound |

**Total estimated per run:** 12-18 hours (can parallelize, but GPU window is limited)

---

## Maintenance Notes

- **Last consolidation:** 2026-07-31 (moved from root scripts/ to organized subdirs)
- **Next review:** 2026-08-31 (consolidate volunteer variants)
- **Owner:** Engineering team + autonomous agents (weekly review)

---

## Decision Points for Founder

1. **Volunteer script consolidation:** Which is best version? Merge all, or pick one?
2. **Run frequency:** Daily, weekly, or monthly?
3. **Data freshness priority:** Breadth (fast, all platforms) or depth (slow, high quality)?
4. **Budget allocation:** How much GPU time per week?

---

**Last updated:** 2026-07-31 14:41 CDT  
**Status:** Committed to git; the former `ACTIVE_INITIATIVES.md` tracking reference
was moved to `docs/ACTIVE_INITIATIVES.md`.
