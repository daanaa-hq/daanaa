# Post-Launch Monitoring & Optimization

**Timeline**: Week 4+ (ongoing)  
**Owner**: Engineering + Product  
**Cadence**: Daily (week 1), Weekly (ongoing)

---

## Week 4: Critical Monitoring

### Daily Health Checks (Monday-Friday)

**9am PT**: Morning standup review

```bash
# 1. API health
curl -s https://daanaa.org/health | jq .

# 2. Error rate (check logs)
tail -n 100 /var/log/daanaa/error.log | grep -c "ERROR\|500"
# Should be < 10 errors per 100k requests

# 3. Database integrity
sqlite3 data/merit_registry.db "PRAGMA integrity_check;" | head -1
# Should show "ok"

# 4. Response time (sample 10 requests)
for i in {1..10}; do time curl -s https://daanaa.org/api/organizations/391214392 > /dev/null; done
# All should be <200ms
```

**3pm PT**: Metrics snapshot

```bash
# Check adoption metrics
curl -s https://daanaa.org/api/stats | jq '{
  total_orgs,
  scored_v5: scored_orgs_v5,
  coverage: coverage_pct
}'

# Check null rates
sqlite3 data/merit_registry.db "
  SELECT COUNT(*) as null_v5_count 
  FROM registry_enriched 
  WHERE merit_archetype_v5 IS NULL
" 
# Should show ~1.6M (unscored orgs)
```

**6pm PT**: User feedback review

```bash
# Check for new error reports
tail -n 50 feedback_v5.jsonl | grep '"clarity": "unclear"' | wc -l
# Should be < 5 per day

# Sentiment check
tail -n 100 feedback_v5.jsonl | grep -c '"feedback": "positive"'
# Should be > 70%
```

### Alert Thresholds (Page On-Call If Exceeded)

| Metric | Yellow Alert | Red Alert |
|--------|--------------|-----------|
| Error rate | >0.5% | >1% |
| Response time | >200ms avg | >500ms |
| Null rate | >85% | >90% |
| Feedback negative % | >25% | >40% |
| API downtime | >5 min | >15 min |

---

## Week 4+ Metrics Dashboard

### Create Real-Time Dashboard

**Location**: Internal dashboard at `daanaa.org/admin/v5-metrics`

**Sections**:

#### 1. Adoption Metrics

```
Live Users Seeing v5_context: [████████░░ 95%]
  - Last 24h views: 4,250
  - Last 7d views: 28,400
  - Unique users: 2,100

Org Detail Page Views: [████████░░ 95%]
  - With v5_context: 4,040
  - Without v5_context: 210 (unscored)
  - Coverage: 95%
```

#### 2. Error Tracking

```
API Error Rate: [██░░░░░░░░ 0.08%]
  - Critical (500): 2
  - Client (400): 12
  - v5_context specific: 0

Top Errors Today:
  1. Database locked (1)
  2. Timeout on search (1)
  3. Malformed EIN (10)
```

#### 3. Performance

```
API Response Time (p99): [████░░░░░░ 87ms]
  - With v5_context: 95ms
  - Trend: stable ↔️
  
Frontend Load Time: [███░░░░░░░ 1.2s]
  - V5Context render: 150ms
  - Trend: ↓ (improving)
```

#### 4. User Feedback

```
Form Response Rate: [██░░░░░░░░ 2%]
  - Total responses: 56
  - Clarity: 81% ("clear")
  - Preference: 72% (peer-based)
  - NTEE accuracy: 92% (≤8% misclass)

Sentiment Distribution:
  Positive:  44 (79%)
  Neutral:   10 (18%)
  Negative:   2 (3%)
```

### Automated Alerts (Send via Slack)

```
Configuration:
  Channel: #daanaa-v5-alerts
  Severity: CRITICAL|WARNING|INFO
  
Examples:
  
CRITICAL: API error rate >1% (currently 2.3%)
WARNING: Response time >200ms (p99: 245ms)
INFO: v5.0 now live for 100% of users (28,400 views, 2,100 unique)
```

---

## Week 1 (Launch Week) Focus

### Primary: Stability

**Goal**: Ensure no data loss, errors, or performance regression

**Daily checklist**:
- [ ] Zero database corruption incidents
- [ ] Error rate <0.1%
- [ ] Response time <100ms (p99)
- [ ] No rollback needed
- [ ] All systems operational

### Secondary: Adoption Tracking

**Monitor**:
- % of users who see v5_context (should be ~95%+)
- % of users who interact with V5Context UI
- Average time spent reading V5Context
- Click-through to methodology page

---

## Week 2-4 Focus

### Primary: User Feedback Integration

**Collect**:
- Archetype clarity (free-form comments)
- Peer comparison helpfulness
- NTEE questionnaire accuracy
- Missing data (which orgs lack v5_context?)

**Act on**:
- Terminology confusion → rename/clarify
- Preference shifts → adjust messaging
- NTEE misclassification → refine defaults

### Secondary: Quality Metrics

**Track**:
- Org view engagement (time on page, scroll depth)
- Conversion rates (search → org detail)
- Search ranking impact (any regressions?)
- Mobile responsiveness (new component works on mobile)

---

## Week 5+ Focus

### Primary: Feature Requests

**Expected asks**:
- "Can I compare two orgs side-by-side?"
- "Show me other orgs like this one"
- "How has this org changed over time?"
- "Which peer groups are healthiest?"

**Prioritize**:
1. High-value (impacts many users)
2. Quick-win (small engineering effort)
3. Strategic (advances mission)

### Secondary: Optimization

**Performance**:
- Cache v5_context responses (Redis)
- Lazy-load benchmarks on scroll
- Precompute peer summaries
- Optimize database queries

**User Experience**:
- Add peer group examples (real orgs)
- Create archetype video explanations
- Build peer comparison tool
- Develop nonprofit dashboard

---

## Data Validation (Ongoing)

### Weekly Integrity Check

```bash
# Run validation script (scripts/validate_v5_scores.py)
python3 scripts/validate_v5_scores.py

# Check output:
# - Coverage: ≥98% of viewed orgs have v5_context
# - Coherence: within-group variance <4.0
# - Discrimination: between-group difference ≥3pp
# - Sample audit: 100 random orgs validate correctly
```

### Monthly Deep Dive

```
1. Compare Q with Q-1 metrics
   - Same orgs in same peer groups?
   - Percentile ranks stable?
   - Health signals unchanged?

2. Identify outliers
   - Which archetypes moved groups?
   - Why? (data quality issue or real change?)

3. Validate methodology
   - K=5 clustering still optimal?
   - Revenue bands still relevant?
   - Benchmarks reflect current reality?
```

---

## Incident Response Plan

### Scenario 1: High Error Rate (>1%)

**Detect**: Automated alert on error rate  
**Respond** (< 5 min):
```
1. Check recent deployments (git log -5)
2. Check database (PRAGMA integrity_check)
3. Check logs (tail -100 error.log)
4. Is v5_context causing errors?
   - Check error type distribution
   - Are v5-specific endpoints failing?
```

**Fix**:
- If v5_context null rate high → data corruption, restore backup
- If API crash → check memory usage, restart service
- If database issue → run PRAGMA optimize, check indexes

**Prevent**:
- Add pre-deployment test: 1000 v5_context calls with random EINs
- Add circuit breaker: if error rate >0.5%, fallback to v4
- Add health check: database integrity on startup

---

### Scenario 2: Negative User Feedback (>25%)

**Detect**: Manual review of feedback forms, social media  
**Respond** (1 hour):
```
1. Categorize feedback
   - Is it about archetype names? → rename
   - Is it about peer concept? → explain more
   - Is it about data? → check coverage

2. Identify pattern
   - Same issue across users? → systemic
   - Isolated complaints? → clarify one-on-one

3. Decide: iterate or educate
   - If confusing → add examples, clarify messaging
   - If misunderstanding → better onboarding
   - If real issue → iterate methodology
```

**Fix**:
- Deploy clarifications to FAQ, help docs
- Update V5Context component copy
- Create short video explaining peer groups

---

### Scenario 3: Data Accuracy Concern

**Detect**: User reports org in wrong peer group  
**Respond** (< 1 hour):
```
1. Validate claim
   - Check org's archetype (via questionnaire)
   - Check org's revenue band
   - Is assignment correct?

2. Investigate root cause
   - IRS data incomplete?
   - NTEE mapping wrong?
   - K=5 clustering failing?

3. Decide: update data or explain
   - If error → fix and backfill
   - If edge case → document limitation
   - If real issue → retrain scorer
```

---

## Success Metrics (Month 1)

### Must-Haves
- [ ] Zero data corruption incidents
- [ ] Error rate <0.1% (sustained)
- [ ] User feedback clarity ≥75%
- [ ] No major regressions vs v4

### Nice-to-Haves
- [ ] Adoption >90% of org detail views
- [ ] Positive sentiment >70% of feedback
- [ ] Blog post >1K views
- [ ] Zero critical incidents

---

## Maintenance Schedule

### Daily (5 min)
- Health check
- Error log review
- Feedback volume check

### Weekly (30 min)
- Metrics review meeting
- Trend analysis
- User feedback synthesis
- Priority any urgent fixes

### Monthly (2 hours)
- Deep data validation
- Performance analysis
- Plan next improvements
- Update roadmap

---

## Runbook for Common Issues

### v5_context returns null (shouldn't)

```
Diagnosis:
1. Is org in registry_enriched?
   sqlite3 data/merit_registry.db \
     "SELECT COUNT(*) FROM registry_enriched WHERE EIN = '391214392';"

2. Does org have merit_archetype_v5?
   sqlite3 data/merit_registry.db \
     "SELECT merit_archetype_v5 FROM registry_enriched WHERE EIN = '391214392';"

3. Is enrich_api_responses.py loaded?
   ps aux | grep daanaa_api | grep -v grep

Fix:
- If missing: run scripts/migrate_to_v5_scores.py
- If null: org is unscored (expected, IRS data gap)
- If process issue: restart API (systemctl restart daanaa_api)
```

### API response slow (>200ms)

```
Diagnosis:
1. Check database size
   sqlite3 data/merit_registry.db "SELECT page_count * page_size / 1024.0 / 1024.0 FROM pragma_page_count(), pragma_page_size();"

2. Check slow queries
   strace -e openat curl -s https://daanaa.org/api/organizations/391214392

3. Check memory usage
   free -h

Fix:
- Database: PRAGMA optimize
- Connection pool: increase max connections
- Memory: restart service to clear caches
- Network: check latency to droplet
```

### User reports wrong peer group

```
Diagnosis:
1. Check org's actual NTEE code
   sqlite3 data/merit_registry.db \
     "SELECT NTEE1, NTEECC FROM registry_enriched WHERE EIN = 'X';"

2. Check NTEE→archetype mapping
   cat scripts/ntee_questionnaire_v5_0.py | grep -A 5 "def ntee_to_archetype"

3. Check if high-risk category (B, C, E, L, N, S, U)
   # If yes, ask user for funding source via questionnaire

Fix:
- For wrong mapping: update ntee_to_archetype() logic
- For missing user input: show questionnaire
- For unscored org: user is outside 21.6% coverage
```

---

## Documentation Updates

### Keep Current
- docs/WEEK3_FEEDBACK_COLLECTION.md (during Week 3)
- docs/WEEK4_FULL_LAUNCH.md (during Week 4)
- docs/POSTLAUNCH_MONITORING.md (ongoing)
- docs/API_V5_RESPONSE_FORMAT.md (reference)
- docs/methodology.md (public-facing)

### Archive After Launch
- docs/WEEK3_BETA_STATUS.md (move to /archive/week3_*)
- docs/WEEK3_BETA_DEPLOYMENT.md (move to /archive/week3_*)
- docs/V5_LAUNCH_CHECKLIST.md (move to /archive/week3_*)

---

**Prepared by**: Claude Code  
**Timeline**: Week 4 onwards  
**Review**: Adjust thresholds based on actual data
