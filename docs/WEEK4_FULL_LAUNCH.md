# Week 4: v5.0 Full Launch Procedures

**Timeline**: Monday-Friday, June 16-20, 2026  
**Triggered By**: Friday EOD Week 3 decision ≥80% on all metrics  
**Scope**: 100% user deployment, v4 removal, public communication

---

## Pre-Launch Checklist (Monday AM)

### Decision Confirmation
- [ ] Clarity ≥80% verified
- [ ] Preference ≥70% verified
- [ ] NTEE accuracy ≤20% verified
- [ ] Coverage ≥98% verified
- [ ] No blockers identified

### Code Review & Validation
- [ ] Final code review on all v5 changes
- [ ] Database backup taken
- [ ] Rollback plan confirmed with operations
- [ ] Performance test: API response time <100ms with v5_context
- [ ] Privacy checks passed (no third-party trackers)
- [ ] Accessibility audit on V5Context component

### Communication Prep
- [ ] Blog post drafted: "How Daanaa Compares Nonprofits"
- [ ] Email template ready (users, partners, media)
- [ ] FAQ updated with v5.0 info
- [ ] Methodology page final review
- [ ] Social media posts drafted

### Monitoring Setup
- [ ] Dashboards created (adoption, errors, engagement)
- [ ] Alert thresholds set (API errors, null rates, performance)
- [ ] Runbook prepared (incident response procedures)
- [ ] Log aggregation configured

---

## Launch Sequence (Monday 10am PT)

### Phase 1: Prepare (1 hour)

```bash
# Verify current state
curl -s https://daanaa.org/health | jq .

# Check database integrity
sqlite3 data/merit_registry.db "PRAGMA integrity_check;" | head

# Confirm backup exists
ls -lh data/backups/merit_registry.db.backup*

# Verify v5 data in database
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE merit_archetype_v5 IS NOT NULL;"
# Should show: 447557
```

### Phase 2: Remove v4 Scores (30 min)

**In daanaa_api.py**, modify `_strip_scores()`:

```python
def _strip_scores(org):
  """Remove v4 scores, keep v5 context (now primary)"""
  # Remove v4 fields (confidence levels vary by deployment)
  fields_to_remove = [
    'merit_score',        # Old v4 absolute score
    'merit_tier',         # Old v4 tier label
    'merit_band',         # Old v4 band
    'visibility_tier',    # Legacy
    'financial_health',   # v4 label
    'peer_percentile',    # Superseded by v5
    'ntee1_percentile',   # Superseded by v5
  ]
  
  for field in fields_to_remove:
    org.pop(field, None)
  
  # v5_context is now the primary scoring system
  return org
```

**Test locally**:
```bash
curl -s http://localhost:5000/api/organizations/391214392 | jq 'keys | sort' | grep -E "v5|merit_score|visibility"
# Should show v5_context present, no merit_score/visibility_tier
```

### Phase 3: Deploy (30 min)

```bash
cd ~/meritgiving

# Build frontend
npm run build --prefix frontend

# Test build
npm run preview --prefix frontend &

# Verify V5Context component in bundle
grep -q "V5Context" frontend/dist/assets/*.js && echo "✓ V5Context bundled"

# Deploy to production
SKIP_FAISS=1 bash scripts/safe_deploy_droplet.sh

# Wait for completion
# Monitor: tail -f /var/log/daanaa/deploy.log
```

### Phase 4: Verify (30 min)

```bash
# API is live
curl -s https://daanaa.org/health | jq .status

# v5_context present in responses
curl -s https://daanaa.org/api/organizations/391214392 | jq '.v5_context.archetype'
# Should show: "Donation-Funded Programs"

# v4 fields removed
curl -s https://daanaa.org/api/organizations/391214392 | jq 'keys' | grep -c "merit_score\|visibility_tier"
# Should show: 0

# Performance acceptable
time curl -s https://daanaa.org/api/organizations/391214392 > /dev/null
# Should be <100ms

# Unscored orgs return null correctly
curl -s https://daanaa.org/api/organizations/999999999 | jq '.v5_context'
# Should show: null
```

---

## Post-Launch Communications (Monday 2pm PT)

### 1. User Email

**Subject**: Daanaa's New Financial Perspective

```
Hi [Name],

We're excited to share a major update to how Daanaa compares nonprofit finances.

Instead of a single "score" from 0-100, we now show you how each organization 
compares to financially similar peers. This is fairer and more meaningful.

For example: A $50K community clinic is now compared to other $50K clinics 
(not $500M hospitals). You'll see:

  • What type of organization it is (e.g., "Donation-Funded Programs")
  • Its percentile rank within that group (e.g., "42nd percentile")
  • How its reserves compare to peers (e.g., "3 months vs 11-month median")

Why peer comparison? Because nonprofits are incredibly diverse. A "healthy" 
reserves level for a food bank looks very different from a legal aid org. 
Peer comparison shows what healthy actually looks like for that specific type.

See an example: daanaa.org/org/[featured-ein]
Learn the full methodology: daanaa.org/methodology

Questions? Reply to this email. We'd love to hear what you think.

— The Daanaa team
```

### 2. Blog Post

**Title**: "How Daanaa Compares Nonprofits: From Scores to Peer Context"

**Sections**:
- The Problem: "Why absolute scores are misleading"
- The Solution: "Peer-based financial comparison"
- How It Works: "5 archetypes × 3 revenue bands = 15 peer groups"
- Examples: "3 real organizations, side-by-side"
- Methodology: "Based on 1.75M org-years of IRS 990 data"
- Limitations: "We cover 21.6% of nonprofits (IRS data gaps)"
- Call to Action: "See it live on daanaa.org"

### 3. Partner Communications

**For nonprofit partners** (those claiming pages):

```
Subject: New Financial Context Tool for Nonprofits

If you've claimed your organization's page on Daanaa, you can now see 
exactly which peer group we're comparing you against — no surprises, 
full transparency.

You can also verify your funding sources in the beta questionnaire, 
which helps us assign you to the most accurate peer group.

Log in to daanaa.org/for-nonprofits to see your organization's peer context.
```

### 4. Social Media Posts

**LinkedIn/Twitter**:
```
We just rewrote how Daanaa compares nonprofit finances. Instead of 
scoring 447K orgs on a 0-100 scale, we now show peer-based context.

A $50K clinic compared to $50K clinics (not $500M hospitals). Fair, 
transparent, real. See it live: daanaa.org
```

---

## Frontend Changes (Monday)

### Remove v4 UI Elements

**In OrganizationDetail.tsx**, remove v4 score display:

```tsx
// REMOVE THIS SECTION:
{apiOrg!.financial_health && (
  <div className="merit-score-display">
    <span className="score-number">{apiOrg!.merit_score}</span>
    <span className="tier-label">{apiOrg!.merit_tier}</span>
  </div>
)}

// KEEP THIS (v5 is now primary):
{apiOrg! && (
  <div className="mb-8">
    <V5Context org={apiOrg!} />
  </div>
)}
```

### Update Feature Flag

**In useFeatureFlag.ts**, change rollout percentage:

```typescript
// Change from 1% to 100% deployment
export function useFeatureFlag(flagName: string, percentage: number = 100): boolean {
  // Now all users see v5_context
  // ...
}
```

Or, simpler — just remove the check:

```tsx
// In OrganizationDetail.tsx
// Remove this:
// const showV5Beta = useFeatureFlag('v5_peer_taxonomy', 1)

// Replace with:
const showV5 = true  // Now all users see v5_context

// Render V5Context unconditionally:
{apiOrg! && showV5 && (
  <div className="mb-8">
    <V5Context org={apiOrg!} />
  </div>
)}
```

### Update Styling

- Change "Financial Context (Beta)" → "Financial Context"
- Remove beta badges/disclaimers
- Update disclosure language in component

---

## Backend Changes (Monday)

### Update API Response

**In daanaa_api.py**, add deprecation notice:

```python
def get_organization(ein):
  # ... existing code ...
  
  # v5 context is now primary (v4 removed)
  # Add deprecation note to response
  result = _strip_scores(org)
  result['_version'] = 'v5.0'
  result['_methodology_url'] = 'https://daanaa.org/methodology'
  
  return jsonify(result)
```

### Update Disclosures

Remove old disclaimers:

```python
# OLD (remove):
SCORE_DISCLAIMER = (
  "⚠️ Financial Health is a peer-group ranking relative to similar organizations..."
)

# NEW (add):
V5_METHODOLOGY_NOTICE = (
  "This organization is compared to financially similar nonprofits in its peer group. "
  "See daanaa.org/methodology for details on how peer groups are formed and limitations."
)
```

---

## Database Updates (Monday)

### Archive v4 Scoring

```bash
# Keep v4 columns in database (don't drop) but mark as deprecated
sqlite3 data/merit_registry.db << 'EOF'

-- Add deprecation timestamp
ALTER TABLE registry_enriched ADD COLUMN merit_v4_deprecated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Document in metadata
INSERT INTO schema_metadata (version, description, deprecated_at)
VALUES ('v4.0', 'Absolute 0-100 scoring (superseded by v5.0 peer-based)', datetime('now'));

EOF
```

### Update Stats Endpoint

```python
# In /api/stats endpoint, update counts:

stats = {
  'total_orgs': 2064612,
  'scored_orgs_v5': 447557,  # Changed from merit_score count
  'coverage_pct': 21.6,
  'scoring_methodology': 'v5.0',  # Updated from 'v4.0'
  'scoring_updated_at': '2026-06-11T12:00:00Z',
  'methodology_url': 'https://daanaa.org/methodology'
}
```

---

## Publish Methodology Page (Monday)

### Create daanaa.org/methodology

**Content** (from `docs/methodology.md`):

1. **Executive Summary**: "Peer-based financial comparison for 447K nonprofits"
2. **The Problem**: Why absolute scores mislead
3. **How It Works**: 
   - 5 archetypes (donation-funded, fee-for-service, etc.)
   - 3 revenue bands (micro, professional, established)
   - 15 peer groups with benchmarked percentiles
4. **Data Source**: 1.75M org-years IRS 990 (2019-2024)
5. **Validation**: 92.5% year-over-year stability
6. **Health Signals**: HEALTHY/STABLE/CAUTION based on reserves
7. **Limitations**:
   - 21.6% coverage (IRS data gaps)
   - Health discrimination weaker than ideal (49-55%)
   - 7 NTEE categories need user clarification
8. **Examples**: 3 real organizations side-by-side
9. **FAQ**: Common questions answered
10. **Contact**: How to report issues or provide feedback

---

## Week 4 Daily Checklist

### Monday (Launch Day)
- [ ] Pre-launch validation complete
- [ ] Code changes deployed
- [ ] Communications sent
- [ ] Monitoring dashboards live
- [ ] v5.0 live for 100% of users
- [ ] Error rate monitoring (target: <0.1%)

### Tuesday-Thursday (Stabilization)
- [ ] Daily error log review
- [ ] Monitor adoption metrics
- [ ] Response time tracking
- [ ] User feedback analysis
- [ ] Engage with early feedback

### Friday (Week Review)
- [ ] Summarize metrics
- [ ] Document learnings
- [ ] Plan Week 5+ improvements
- [ ] Archive old data

---

## Rollback Plan (If Needed)

### Quick Rollback (< 5 min)

If critical issue discovered:

```bash
# 1. Restore v4 response format temporarily
export ROLLBACK_TO_V4=1

# 2. Restart API
systemctl restart daanaa_api

# 3. Revert frontend to v4 display
git checkout frontend/ -- src/pages/OrganizationDetail.tsx

# 4. Redeploy frontend
npm run build --prefix frontend
SKIP_FAISS=1 bash scripts/safe_deploy_droplet.sh

# 5. Monitor error rate
curl -s https://daanaa.org/health | jq .
```

### Graceful Rollback (≤1 hour)

If gradual migration needed:

```bash
# Revert to 50% v5, 50% v4 (A/B test)
export V5_ROLLOUT_PCT=50
systemctl restart daanaa_api

# Monitor for 30 min
# If stable, increase to 75%
# If issues, decrease to 0%
```

### Full Rollback (Database)

If data corruption:

```bash
# Restore from backup
cp data/backups/merit_registry.db.backup data/merit_registry.db

# Restart services
systemctl restart daanaa_api
systemctl restart nginx

# Revert to v4 API
export ENABLE_V5=0
systemctl restart daanaa_api
```

---

## Success Metrics (Week 4+)

### Technical (Monitor Daily)

| Metric | Target | Alert |
|--------|--------|-------|
| API error rate | <0.1% | >1% = page on-call |
| Response time | <100ms | >500ms = investigate |
| v5_context null rate | 78% (unscored) | >85% = data corruption |
| Database integrity | PRAGMA ok | FAIL = restore backup |

### User Engagement (Monitor Weekly)

| Metric | Target | Action |
|--------|--------|--------|
| Page load time | <2s | Monitor for regression |
| Org detail view duration | ≥45s | Check if users reading |
| Search → org detail conversion | ≥15% | Should not regress |
| Bounce rate | ≤20% | Track with v4 baseline |

### Feedback (Ongoing)

| Signal | What It Means |
|--------|---------------|
| Positive comments | "This makes more sense now!" |
| Confusion queries | "What does Donation-Funded mean?" |
| Feature requests | "Can I compare to other orgs?" |
| Bugs reported | Triage and fix immediately |

---

## Success Scenario

```
Monday 10am PT: v5.0 launches to 100% of users
Monday 2pm PT: Communications sent to 50K users
Monday EOD: Error rate <0.1%, no alerts
Tuesday: Positive user feedback starts flowing in
Wednesday: Blog post gets 500+ social shares
Friday: Metrics show 95%+ users understand peer context
           All systems stable, no rollbacks needed
```

---

## Post-Launch Optimization (Week 5+)

### Quick Wins (1-2 days)
- Terminology tweaks based on feedback
- FAQ updates with most common questions
- Link improvements (help docs, examples)

### Medium Term (1-2 weeks)
- Comparison tool: "Show me other orgs like this"
- Trend tracking: "How has this org's health changed?"
- Export functionality: "Download peer group data"

### Long Term (1+ months)
- Mobile app with v5.0 context
- Bulk organization analysis
- Nonprofit dashboard (see your org's peer group)
- Research features (what do healthy orgs do?)

---

**Prepared by**: Claude Code  
**Timeline**: June 16-20, 2026  
**Approval**: Required before Phase 1 (Monday 10am)
