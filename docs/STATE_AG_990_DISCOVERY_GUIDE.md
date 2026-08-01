# State AG 990 Discovery Initiative — Complete Implementation Guide

**Status:** Phase 1 Ready for Launch  
**Target:** 350+ new organizations with websites  
**Timeline:** Weeks 1-4 (with potential for 300-400K orgs in full scope)  
**Owner:** Agent 20 - State AG 990 Discovery  
**Updated:** 2026-07-30

---

## Quick Start

### Phase 1 (Week 1-2): High-Value Quick Wins

#### Step 1: ProPublica Bulk Website Extraction
```bash
cd ~/meritgiving
source venv/bin/activate

# Dry run: test on 1,000 orgs
python3 scripts/state_ag_discovery_propublica.py --limit 1000 --dry-run

# Full run: extract websites from all 1.8M ProPublica orgs
python3 scripts/state_ag_discovery_propublica.py --all --output propublica_discovery.csv
```

**Expected Results:**
- 50K-100K new organizations discovered
- 50-60% website coverage in results
- CSV export to: `data/state_ag_discovery/propublica_discovery.csv`

#### Step 2: Colorado CSV Import
```bash
# Download Colorado data first (if not already available)
# Source: https://data.colorado.gov/
# Dataset: "Colorado Nonprofits" CSV

# Process with deduplication
python3 scripts/state_ag_discovery_colorado.py \
  --csv colorado_nonprofits.csv \
  --dry-run \
  --output colorado_discovery.csv

# Production run
python3 scripts/state_ag_discovery_colorado.py \
  --csv colorado_nonprofits.csv \
  --output colorado_discovery.csv
```

**Expected Results:**
- 5K-8K new organizations
- 35-45% website coverage
- CSV export + database ingest

### Phase 2 (Week 3-4): Scraper-Based Sources

#### New York (30K-50K orgs)
```bash
# Build NY scraper (requires development)
python3 scripts/state_ag_discovery_ny_scraper.py --dry-run
# Expected: 15K-25K new websites
```

#### Illinois (25K-40K orgs)
```bash
# Build IL scraper
python3 scripts/state_ag_discovery_illinois_scraper.py --dry-run
# Expected: 8K-15K new websites
```

---

## Architecture

### Data Flow

```
ProPublica API / State CSV
    ↓
Fetch & Parse (source-specific)
    ↓
Deduplication Framework
  ├─ EIN exact match
  ├─ Fuzzy name match
  └─ New org detection
    ↓
Website Validation (optional)
  └─ HTTP 200 status check
    ↓
Export CSV / Database Ingest
    ↓
Registry Enriched Table
```

### Scripts & Responsibilities

| Script | Purpose | Status |
|--------|---------|--------|
| `state_ag_discovery_propublica.py` | ProPublica API extraction | ✅ Ready |
| `state_ag_discovery_colorado.py` | Colorado CSV import | ✅ Ready |
| `state_ag_discovery_framework.py` | Generic dedup/validate framework | ✅ Ready |
| `state_ag_discovery_ny_scraper.py` | NY AG scraper (TBD) | 📋 Planned |
| `state_ag_discovery_illinois_scraper.py` | IL AG scraper (TBD) | 📋 Planned |

### Database Schema

**New/Modified Columns:**
- `website_source`: Track origin ('state_ag_california', 'propublica_state_ag', etc.)
- `website_checked_at`: Timestamp of validation
- `website_last_verified`: Last HTTP check
- `state_ag_discovered_at`: When org was discovered via state registry

**Unchanged:**
- `website`: The actual URL
- `website_status`: 'valid' | 'dead_link' | 'unknown'

---

## Deduplication Strategy

### Match Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **HIGH** | Exact EIN match + valid website | Ingest (95%+ confidence) |
| **MEDIUM** | Fuzzy name match (85%+ similarity) + valid website | Ingest (75-94% confidence) |
| **LOW** | No match, new org, no website | Skip or flag for review |

### Deduplication Process

1. **Load existing Daanaa EINs** (~1.7M) into memory
2. **For each new org:**
   - Try exact EIN match → if found, done (mark as enrichment candidate)
   - Try fuzzy name match (Levenshtein) → if found, done
   - No match → new org (candidate for insertion)
3. **Output:**
   - CSV with all results (for review)
   - New orgs to ingest
   - Enrichment candidates (existing orgs with new website)

---

## Phase-by-Phase Execution

### Phase 1: ProPublica & Colorado (Weeks 1-2)

**Week 1, Day 1-2: ProPublica**
```bash
python3 scripts/state_ag_discovery_propublica.py --limit 10000 --dry-run
# Check results in logs
python3 scripts/state_ag_discovery_propublica.py --limit 10000 --output propublica_10k.csv
# Review: data/state_ag_discovery/propublica_10k.csv
```

**Week 1, Day 3-5: Colorado**
```bash
# Download CO data
wget https://data.colorado.gov/api/views/... -O colorado_nonprofits.csv

# Test
python3 scripts/state_ag_discovery_colorado.py \
  --csv colorado_nonprofits.csv \
  --dry-run \
  --output colorado_test.csv

# Production
python3 scripts/state_ag_discovery_colorado.py \
  --csv colorado_nonprofits.csv \
  --output colorado_final.csv
```

**Week 2: Evaluate Results**
- Measure new org discovery rate
- Measure website coverage
- Measure deduplication accuracy
- Decision: Proceed to Phase 2?

### Phase 2: Scrapers (Weeks 3-4)

**Week 3: NY & Illinois Scrapers**
```bash
# NY scraper build & deploy
python3 scripts/state_ag_discovery_ny_scraper.py --dry-run

# Illinois scraper build & deploy
python3 scripts/state_ag_discovery_illinois_scraper.py --dry-run
```

**Week 4: Scale & Validate**
```bash
# Run full scrapers, validate websites, ingest
python3 scripts/state_ag_discovery_framework.py \
  --source all \
  --validate \
  --ingest
```

---

## Success Metrics

### Phase 1 Goals
- [ ] 50K-100K websites discovered from ProPublica
- [ ] 5K-8K websites discovered from Colorado
- [ ] 70-80% deduplication accuracy
- [ ] <5% dead link rate
- [ ] 75-150 new organizations added to registry

### Phase 2 Goals
- [ ] 40K-60K websites from NY + IL scrapers
- [ ] 90-150 additional new organizations
- [ ] **Total by end of Week 4: 350+ new organizations with websites** ✅

---

## Monitoring & Alerting

### Pre-Execution Checklist
- [ ] Database backup created
- [ ] ProPublica API rate limits understood
- [ ] Colorado CSV downloaded (if using)
- [ ] Dry-run successful on sample data
- [ ] Logs configured and monitored

### During Execution
```bash
# Monitor progress
tail -f logs/state_ag_discovery.log

# Check database changes
sqlite3 data/merit_registry.db \
  "SELECT COUNT(*) FROM registry_enriched WHERE website_source LIKE 'propublica%'"
```

### Post-Execution
```bash
# Verify ingestion
python3 << 'EOF'
import sqlite3
db = sqlite3.connect('data/merit_registry.db')
c = db.cursor()
c.execute("SELECT website_source, COUNT(*) FROM registry_enriched WHERE website_source LIKE '%state%' OR website_source LIKE 'propublica%' GROUP BY website_source")
for row in c.fetchall():
    print(f"{row[0]}: {row[1]:,}")
EOF
```

---

## Known Issues & Mitigations

### Issue 1: ProPublica API Rate Limiting
**Symptom:** 429 (Too Many Requests) errors  
**Mitigation:** Script includes 0.2s delay between requests (max 5/sec)  
**Fix:** If occurs, reduce limit or add exponential backoff

### Issue 2: EIN Field Missing in State Data
**Symptom:** Fuzzy matching less accurate than expected  
**Mitigation:** Use name + city/state for additional validation  
**Fix:** Manual review queue for ambiguous matches

### Issue 3: Website URLs Dead/Outdated
**Symptom:** High dead link rate in state data  
**Mitigation:** HTTP validation before insertion  
**Fix:** Mark as 'unknown' status, skip insertion if dead

### Issue 4: Database Lock During Long Ingest
**Symptom:** Database locked error mid-ingest  
**Mitigation:** Use transactions, batch commits every 100 records  
**Fix:** See `state_ag_discovery_framework.py` for implementation

---

## Cost & Resource Analysis

### Compute Resources
- **CPU:** Minimal (CSV parsing, HTTP checks)
- **Storage:** 500MB temp CSV, 100MB processed data
- **Network:** 10-20 hours API/scraper bandwidth
- **Database:** <1 second per record insertion

### Time Estimate
- Phase 1: 14-20 engineering hours
- Phase 2: 20-35 engineering hours
- Phase 3: 30-50 engineering hours (optional)
- **Total:** 64-105 hours

### API Costs
- ProPublica: $0 (free, public API)
- Colorado: $0 (free, public data)
- California (Candid): $1K-5K/year (optional, pending licensing decision)
- Web scrapers: $0 (owned infrastructure)

---

## Decision Gates

### Gate 1: Approve Phase 1 ✅
**Status:** Ready to proceed  
**Action:** Launch ProPublica + Colorado in Week 1  
**Approval:** Owner sign-off

### Gate 2: Phase 1 Results Review
**When:** End of Week 2  
**Criteria:**
- New org discovery >50K
- Website coverage >30%
- Dedup accuracy >70%
**Outcome:** Proceed to Phase 2 or iterate Phase 1

### Gate 3: Scraper Deployment (Phase 2)
**When:** Start of Week 3  
**Criteria:**
- NY scraper prototype working
- IL scraper prototype working
- Rate limiting configured
**Outcome:** Full deployment with monitoring

### Gate 4: Production Launch
**When:** End of Week 4  
**Criteria:**
- 350+ new organizations discovered
- Website coverage >30%
- Integration with existing pipelines verified
**Outcome:** Auto-refresh scheduling (weekly/monthly)

---

## Next Steps

1. **Immediately:**
   - [ ] Review this guide with team
   - [ ] Approve Phase 1 scope
   - [ ] Schedule Week 1 kick-off

2. **Week 1:**
   - [ ] Run ProPublica extraction (limit 10K, review)
   - [ ] Download Colorado data
   - [ ] Build CI/CD for discovery scripts

3. **Week 2:**
   - [ ] Full ProPublica run (1.8M orgs)
   - [ ] Full Colorado import
   - [ ] Evaluate results
   - [ ] Decide on Phase 2 timeline

4. **Week 3-4:**
   - [ ] Build NY scraper
   - [ ] Build IL scraper
   - [ ] Scale to full Phase 2

5. **Ongoing:**
   - [ ] Set up weekly refresh schedule
   - [ ] Monitor website URL quality
   - [ ] Document learnings in DECISIONS.md

---

## Questions & Support

- **Technical:** See `state_ag_discovery_framework.py` documentation
- **Data Quality:** Review deduplication statistics in logs
- **Legal Compliance:** All data sources are public record; see STEWARDSHIP.md
- **Scaling:** Framework supports 40+ state sources

---

## Appendix: State Source Details

### ProPublica Nonprofit Explorer
- **URL:** `https://projects.propublica.org/nonprofits/api/v2/`
- **Coverage:** 1.8M nonprofits
- **Website Coverage:** 50-60%
- **EIN Available:** Yes
- **Rate Limit:** 5 req/sec
- **Status:** Production-ready

### Colorado State Database
- **URL:** `https://data.colorado.gov/`
- **Dataset:** Colorado Nonprofits
- **Coverage:** 15K-25K organizations
- **Website Coverage:** 35-45%
- **EIN Available:** Partial
- **Format:** CSV download
- **Status:** Production-ready

### New York Charities Bureau (Phase 2)
- **URL:** `https://www.charitiesnys.com/`
- **Coverage:** 30K-50K organizations
- **Website Coverage:** 40-50%
- **Format:** Web scraping required
- **Status:** Scraper development needed

### Illinois Charitable Trusts (Phase 2)
- **URL:** Illinois Attorney General
- **Coverage:** 25K-40K organizations
- **Website Coverage:** 30-40%
- **Format:** Web scraping required
- **Status:** Scraper development needed

---

**Ready to launch Phase 1. Proceed with approval.**
