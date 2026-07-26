# Website Discovery: Implementation & Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the winning website discovery strategies to production and scaling to 500K+ orgs.

## Pre-Deployment Checklist

### Phase 0: Validation (Before First Deployment)
- [ ] Sprint results show top 3 strategies with >15% success rate
- [ ] High-confidence (≥0.8) websites tested for HTTP 200 status
- [ ] No SSL certificate errors or redirect loops detected
- [ ] Response times within acceptable bounds (<5s per org)
- [ ] Rate limiting doesn't exceed API limits
- [ ] Database schema updated to track discovery metadata

### Phase 1: API-First Discovery (Days 1-7)

#### 1.1 Charity Navigator Integration

**File:** `scripts/discovery_daemon.py` (already has CN_verifier support)

**Status:** READY - Already integrated as fallback

**Deployment:**
```bash
# In discovery_daemon.py, enable CN verifier
self.cn_verifier = CharityNavigatorVerifier(timeout=10)
```

**Expected coverage gain:** 200K-250K websites

**Monitoring:**
- Track: `stats['cn_verified']` from daemon logs
- Alert if: Success rate drops below 20%
- Dashboard: `SELECT COUNT(*) FROM registry_enriched WHERE website_source = 'charity_navigator'`

#### 1.2 ProPublica Integration

**File:** `scripts/discovery_daemon.py` (needs new strategy)

**Implementation:**
```python
# Add to discovery_daemon.py strategies list
class ProPublicaDiscoveryStrategy(StrategyBase):
    def discover(self, ein: str, org_data: Dict) -> Optional[str]:
        # Query ProPublica 990 API by EIN
        # Return website if found with high confidence
        pass
```

**Expected coverage gain:** 150K-200K websites (some overlap with CN)

**Rate Limiting:** ProPublica has no documented rate limit; use 5 req/sec conservatively

**Deployment:**
```bash
# Add to overnight_pipeline.py
discovery_daemon.run_with_strategies(['charity_navigator', 'propublica'])
```

### Phase 2: Pattern Matching (Days 8-14)

#### 2.1 Domain Pattern Strategy

**File:** Create `scripts/domain_pattern_discovery.py`

**Key patterns to try (in order):**
1. `https://{org_name_clean}.org` (exact match)
2. `https://www.{org_name_clean}.org` (with www)
3. `https://{org_initials}.org` (abbreviation)
4. `https://{org_name_hyphenated}.org` (hyphenated)
5. `https://{org_name_clean}.com` (fallback TLD)

**Confidence scoring:**
- Exact match (.org): 95% confidence
- With www: 90% confidence
- Initials: 70% confidence
- .com fallback: 60% confidence

**Deployment:**
```bash
# Run on all orgs without websites
python3 scripts/domain_pattern_discovery.py \
  --batch-size=1000 \
  --workers=20 \
  --min-confidence=0.70
```

**Expected coverage gain:** 180K-220K websites

**Parallelization:** 20+ workers (network I/O bound, not CPU bound)

**Rate limiting:** 1.5s between requests to same domain (robots.txt compliant)

### Phase 3: Google Search Pattern (Days 15-21)

#### 3.1 Google Search Strategy

**Option A: Free (Basic Domain Pattern)**
- Already covered in Phase 2

**Option B: Premium (Serper API)**
- Cost: $5 per 1,000 queries
- Coverage: Likely 10-15% new org websites
- Use case: Org names with special characters, synonyms

**Deployment (if using Serper):**
```python
import serper

def search_nonprofit_website(org_name: str) -> Optional[str]:
    results = serper.search(f'nonprofit "{org_name}" .org')
    for result in results:
        if result['domain'].endswith('.org'):
            return verify_website(result['url'])
    return None
```

**Expected coverage gain:** 100K-150K (if using Serper)

**Cost:** $5-10 for full 2M registry (if 15% success rate)

### Phase 4: Fallback & Enrichment (Days 22-30)

#### 4.1 Archive.org Fallback

**Use case:** Defunct orgs, historical sites

**Deployment:**
```bash
python3 scripts/archive_org_discovery.py \
  --filter-by-website-status=null \
  --batch-size=500 \
  --confidence-threshold=0.65
```

**Expected coverage gain:** 30K-50K (archived sites)

#### 4.2 State Registry Enrichment (Optional)

**Use case:** State-registered nonprofits without websites

**Effort:** Requires per-state scraper development

**Expected gain:** 20K-40K (state-specific)

## Database Schema Updates

### Add tracking columns:

```sql
ALTER TABLE registry_enriched ADD COLUMN website_discovery_source TEXT;
ALTER TABLE registry_enriched ADD COLUMN website_discovery_timestamp TIMESTAMP;
ALTER TABLE registry_enriched ADD COLUMN website_discovery_confidence REAL;
ALTER TABLE registry_enriched ADD COLUMN website_verification_status TEXT;
```

### Create discovery log table:

```sql
CREATE TABLE website_discovery_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    strategy TEXT NOT NULL,
    discovered_website TEXT,
    confidence REAL,
    http_status INTEGER,
    verified_at TIMESTAMP,
    INDEX idx_ein (ein),
    INDEX idx_strategy (strategy)
);
```

### Sample queries for monitoring:

```sql
-- Coverage by strategy
SELECT website_discovery_source, COUNT(*) as count
FROM registry_enriched
WHERE website IS NOT NULL
GROUP BY website_discovery_source;

-- Verification rates by strategy
SELECT strategy, 
       COUNT(*) as total,
       SUM(CASE WHEN verification_status = 'live' THEN 1 ELSE 0 END) as verified
FROM website_discovery_log
GROUP BY strategy;

-- Coverage improvement over time
SELECT DATE(website_discovery_timestamp) as date,
       COUNT(DISTINCT ein) as new_websites
FROM website_discovery_log
GROUP BY DATE(website_discovery_timestamp)
ORDER BY date DESC;
```

## Deployment Architecture

### Option 1: Daemon Integration (Recommended)

**File:** `scripts/discovery_daemon.py` (already handles this)

**Modifications needed:**
- Add ProPublica strategy class
- Add domain pattern fallback
- Increase workers from 4 to 10-20 (for pattern matching)

**Run schedule:**
- Continuous (existing pattern)
- Prioritize high-revenue orgs (existing)
- Phase strategies (CN → ProPublica → Domain Pattern)

**Deployment:**
```bash
# Restart daemon with new strategies
systemctl restart daanaa-discovery-daemon

# Or manually:
python3 scripts/discovery_daemon.py --enable-all-strategies
```

### Option 2: Batch Processing (Alternative)

**For one-time bulk runs:**

```bash
# Phase 1: API strategies
python3 scripts/discovery_daemon.py --strategy=charity_navigator,propublica --batch-size=10000

# Phase 2: Pattern matching
python3 scripts/domain_pattern_discovery.py --batch-size=50000 --workers=20

# Phase 3: Archive
python3 scripts/archive_org_discovery.py --batch-size=5000
```

## Monitoring & Observability

### Key Metrics to Track

```python
# In discovery_daemon.py or batch scripts
stats = {
    "phase": "Phase 1 - API Discovery",
    "strategy": "charity_navigator",
    "total_tested": 10000,
    "found": 2500,
    "success_rate": 0.25,
    "avg_response_time_ms": 450,
    "high_confidence_count": 2400,
    "errors": 50,
    "coverage_gain_estimated": 250000,  # Extrapolated to full registry
}
```

### Dashboard Queries

```sql
-- Real-time coverage %
SELECT 
    ROUND(100 * COUNT(CASE WHEN website IS NOT NULL THEN 1 END) / 
    COUNT(*), 1) as coverage_pct,
    COUNT(CASE WHEN website IS NOT NULL THEN 1 END) as with_website,
    COUNT(*) as total
FROM registry_enriched;

-- Discovery throughput (websites/hour)
SELECT 
    DATE_TRUNC('hour', website_discovery_timestamp) as hour,
    COUNT(*) as discovered,
    COUNT(DISTINCT website_discovery_source) as strategies_used
FROM website_discovery_log
WHERE website_discovery_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', website_discovery_timestamp)
ORDER BY hour DESC;

-- Confidence distribution
SELECT 
    ROUND(website_discovery_confidence, 2) as confidence_band,
    COUNT(*) as count
FROM website_discovery_log
GROUP BY ROUND(website_discovery_confidence, 2)
ORDER BY confidence_band DESC;
```

### Alerts

Set up alerts for:
- Success rate drops below 10% for any strategy
- Response time exceeds 5 seconds average
- API rate limit errors (429 status codes)
- Database disk space usage for discovery_log table
- Daemon crashes or stuck processes

## Rollback Plan

If issues detected:

### Immediate (< 1 hour)
1. Stop new discovery: `systemctl stop daanaa-discovery-daemon`
2. Query affected orgs: `SELECT * FROM registry_enriched WHERE website_discovery_timestamp > NOW() - INTERVAL '1 hour'`
3. Rollback websites: `UPDATE registry_enriched SET website = NULL WHERE website_discovery_source = 'problematic_strategy' AND website_discovery_timestamp > ?`

### Validation
1. Re-verify website URLs for HTTP 200
2. Spot-check 50 random websites for relevance
3. Check for false positives (wrong org URLs discovered)

### Restart
- Fix issue in strategy code
- Re-run validation on small batch (100 orgs)
- Gradually scale back up (1000 → 10K → 100K)

## Success Criteria

### Phase 1 (Week 1-2)
- [ ] Deploy CN + ProPublica strategies
- [ ] Reach 500K+ websites discovered
- [ ] Coverage ≥ 25%
- [ ] High-confidence websites ≥ 90%

### Phase 2 (Week 3-4)
- [ ] Deploy domain pattern strategy
- [ ] Discover 200K+ additional websites
- [ ] Coverage ≥ 35%
- [ ] Quality metrics stable

### Phase 3 (Week 5-6)
- [ ] All fallback strategies deployed
- [ ] Coverage ≥ 40%+
- [ ] Cost-to-discovery ≤ $0.01/website

## Cost Summary

| Phase | Strategy | Cost | Coverage Gain | Cumulative |
|-------|----------|------|---------------|------------|
| 1 | CN + ProPublica | Free | +500K | 25% |
| 2 | Domain Pattern | Free | +200K | 35% |
| 3 | Archive.org | Free | +40K | 37% |
| 3 | State Registry | Free | +30K | 38% |
| **Total** | **All** | **Free** | **770K** | **39%** |

**Optional premium tiers:**
- Google Serper API: +$5-10 for +100K websites
- Manual curation: +$500-1000 for +50K high-value websites

## Next Steps

1. **Today:** Validate sprint results
2. **Tomorrow:** Prepare Phase 1 PR (CN + ProPublica integration)
3. **This week:** Deploy Phase 1, measure coverage gain
4. **Next week:** Begin Phase 2 preparation (domain pattern strategy)
5. **Week 3:** Deploy Phase 2, complete full roadmap plan

---

**Owner:** Website Discovery Team  
**Last updated:** 2026-07-25  
**Next review:** 2026-08-01
