# V6 Implementation Phases 5–8

**Status:** Complete workflow specifications for automated fairness gating, scheduling, staging QA, and founder approval  
**Date:** 2026-07-27  
**Scope:** Phases 5–8 of v6 deployment workflow

---

## PHASE 5 — AUTOMATED FAIRNESS GATES

### Overview

The fairness workflow must block a candidate automatically if any of the following conditions fail. These are **machine-checkable** conditions; violations prevent the candidate from advancing to staging QA or production.

### Blocking Conditions

The fairness report must fail and block the candidate if:

1. **Revocation percentage is invalid**
   - Must be ≥ 0% and ≤ 100%
   - Calculated as: (revoked_numeric_tiers / abs(coverage_change)) × 100
   - If > 100%: data integrity issue (revoked count exceeds reduction)

2. **Revoked organizations in Tiers 1–4**
   - Must be exactly 0
   - Both fields checked: `irs_revoked = 1` OR `org_status = 'revoked'`
   - Blocks activation immediately

3. **Small-organization analysis is empty**
   - Must have baseline small-org count > 0
   - Must have transition data populated
   - Blocking conditions:
     - No grassroots/small organizations in baseline
     - Small-org tier transitions not computed

4. **Numeric coverage changes without explanation**
   - Coverage reduction must be explained (revocation ≥ some threshold)
   - If reduction > 5% and revocation explains < 50%, flag for review
   - Tier 5 growth > 5% without explanation requires investigation

5. **Revenue-band distribution changes materially**
   - "Material" = any band disappears entirely or drops > 50%
   - Must be traceable to data source change (not scoring logic)
   - Example: If "grassroots" band shrinks from 50K to 1K, investigate

6. **Regional distribution changes unexpectedly**
   - All Census regions (Northeast, Midwest, South, West) must have ≥ 100 orgs
   - If a region drops below 50 orgs, flag for review
   - Missing states from a region require investigation

7. **NTEE coverage changes materially**
   - NTEE codes with < 10 orgs in baseline must have < 10 in new candidate
   - Large NTEE categories (> 1000 orgs) must not drop > 50%

8. **Numeric peer groups fall below 5 orgs**
   - All Tiers 1–4 must have ≥ 5 scoreable peers per group
   - Blocks if any peer group < 5

9. **Tier 5 contains numeric peer values**
   - Tier 5 must have zero `peer_median`, `p25`, `p75` values
   - Any numeric value = data integrity violation

10. **Expected report fields are missing**
    - All sections must be populated (no NULL or empty expected values)
    - Report must contain: revocation analysis, coverage analysis, small-org analysis, tier distribution, validation errors

### Automatic Blocking Behavior

If any gate fails:

1. Report marks candidate status: 🔴 **BLOCKED**
2. Fairness section lists all validation errors
3. Candidate remains `status='candidate'` (not auto-promoted)
4. Weekly workflow exits non-zero
5. Founder is notified (via report saved to `reports/v6/`)
6. No staging activation allowed until issues resolved

### Fairness Report Will NOT Auto-Approve

The fairness report may identify a candidate as:
- ✅ "Eligible for review" (all gates passed, no blocking issues)
- ⏳ "Ready for staging QA" (after founder approval + integrity check)

But **the report will never auto-approve or recommend production activation**. Founder approval is always explicit and manual.

---

## PHASE 6 — SCHEDULING

### Daily Operations

**Time:** 01:00 UTC  
**Frequency:** Every day  
**Duration:** ~15 minutes  
**Lock:** `.v6_daily_lock`

**Cron entry:**
```bash
0 1 * * * cd /home/akbar/meritgiving && bash scripts/v6_daily_operations_automated.sh >> /var/log/v6_daily.log 2>&1
```

**Systemd timer (alternative):**
```ini
[Unit]
Description=V6 Daily Data Ingestion
After=network.target

[Timer]
OnCalendar=*-*-* 01:00:00
Unit=v6-daily.service

[Install]
WantedBy=timers.target
```

**Systemd service:**
```ini
[Unit]
Description=V6 Daily Data Ingestion
After=network.target

[Service]
Type=oneshot
User=akbar
WorkingDirectory=/home/akbar/meritgiving
ExecStart=/bin/bash scripts/v6_daily_operations_automated.sh
StandardOutput=journal
StandardError=journal
```

### Weekly Candidate Generation

**Time:** Monday, 02:00 UTC  
**Frequency:** Weekly  
**Duration:** ~30 minutes  
**Lock:** Shares `.v6_daily_lock` with daily operations

**Cron entry:**
```bash
0 2 * * 1 cd /home/akbar/meritgiving && bash scripts/v6_weekly_candidate_generation.sh >> /var/log/v6_weekly.log 2>&1
```

**Systemd timer:**
```ini
[Unit]
Description=V6 Weekly Candidate Generation
After=network.target

[Timer]
OnCalendar=Mon *-*-* 02:00:00
Unit=v6-weekly.service

[Install]
WantedBy=timers.target
```

### Lock Management

- **Single lock file:** `.v6_daily_lock` (shared by daily + weekly)
- **Lock timeout:** 3600 seconds (1 hour)
- **Stale lock cleanup:** If process with PID in lock file doesn't exist, lock is removed
- **Concurrent protection:**
  - If daily ingestion is running, weekly scoring exits safely
  - If weekly scoring is running, daily ingestion exits safely
  - No timeout-based auto-forcing; manual intervention required if blocked > 1h

### Failure Handling

Failed jobs:
- Exit non-zero and log failure
- Do NOT retry mutating operations without manual verification
- Retain logs and reports for ≥ 90 days
- Founder reviews failures and decides on recovery

**No automatic recovery of failed database mutations.**

### Log Retention

- **Daily reports:** `reports/v6/daily_YYYYMMDDTHHMMSSZ.md` (90+ days)
- **Weekly reports:** `reports/v6/candidate_YYYYMMDDTHHMMSSZ.md` (90+ days)
- **Backups:** `data/backups/v6/*.db` (14 daily + 12 weekly)
- **Logs:** `/var/log/v6_*.log` (30 days via logrotate)

---

## PHASE 7 — STAGING QA

### Prerequisites

Only proceed with staging QA if ALL of these have passed:

- ✅ Phase 1: Local verification (fairness, tests, privacy)
- ✅ Phase 2: Quiet-window integrity check returns exactly `ok`
- ✅ Weekly workflow: Candidate generated without errors
- ✅ Fairness gates: No blocking conditions

### Enabling Staging

1. **Stop production services:**
   ```bash
   ./restart_api.sh  # or stop gunicorn
   pkill -f "npm run dev" || true
   ```

2. **Enable v6 feature flags (staging only):**
   ```bash
   export ENABLE_V6_FINANCIAL_CONTEXT=true
   export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true
   ```

3. **Restart API and frontend:**
   ```bash
   source ~/meritgiving/venv/bin/activate
   ./restart_api.sh
   
   cd frontend
   npm run dev &
   cd ..
   ```

4. **Verify startup:**
   ```bash
   sleep 3
   curl -s http://localhost:5000/health
   curl -s http://localhost:5173/
   ```

### Test Organizations

Test the following real organizations in staging:

| Organization | EIN | Expected Tier | Purpose |
|--------------|-----|---------------|---------|
| Large education nonprofit | TBD | Tier 1 | Verify direct financial data + peer context |
| Regional nonprofit | TBD | Tier 2 | Verify conditional bands (missing revenue) |
| Smaller org with partial data | TBD | Tier 3 | Verify broader regional fallback |
| National-scope org | TBD | Tier 4 | Verify national context message |
| New/all-volunteer org | TBD | Tier 5 | Verify archetype-only (no numeric) |
| Grassroots org | TBD | Any | Verify small-org fair treatment |
| Organization with zero revenue | TBD | Any | Verify zero ≠ unknown |
| Organization with missing revenue | TBD | Tier 2+ | Verify missing data handling |
| Revoked org (if any active) | TBD | Blocked | Verify revoked = not shown |
| Claimed/corrected org | TBD | Any | Verify claim flow (if implemented) |

### Page Verification

For each test organization, verify:

**Tier 1 page (direct financial data):**
- [ ] Org name, mission, status visible
- [ ] Financial context section shows peer median + range
- [ ] "Peer group size" shows count with data note
- [ ] "IRS Form 990, [year] filing" clearly stated
- [ ] No rank, rating, or shame language
- [ ] Limitations about age of data
- [ ] No numeric values for Tier 5

**Tier 2 page (conditional bands):**
- [ ] "We don't have recent direct revenue data" message
- [ ] Conditional bands shown (e.g., "If revenue is $50K–$200K")
- [ ] Multiple band options provided
- [ ] Source and last update date visible

**Tier 5 page (archetype-only):**
- [ ] No numeric peer values (peer_median, range, etc.)
- [ ] "Limited public financial data available" message
- [ ] Archetype description (e.g., "donation-funded")
- [ ] "Not a judgment" language prominent
- [ ] Link to claim/update profile

**All pages:**
- [ ] Methodology version visible
- [ ] V6 Financial Context label (not v4/v5)
- [ ] Transparent limitations
- [ ] No auto-ranking by score
- [ ] Search/discovery independent of score coverage

### API Verification

- [ ] GET `/api/organizations/:ein/financial-context` returns v6 fields
- [ ] Response includes `v6_tier`, `v6_confidence`, `v6_peer_context`
- [ ] Tier 5 has zero numeric values
- [ ] Error handling: missing data returns 200 + explanatory tier
- [ ] Performance: response < 500ms
- [ ] No leakage of internal revocation fields

### Feature Regressions

- [ ] Directory search works (keyword + filters)
- [ ] Wallet works (add/remove orgs)
- [ ] Compare page works (side-by-side tier view)
- [ ] Mobile layout renders correctly
- [ ] Print layout includes tier + limitations
- [ ] Slow network (simulate 3G): no infinite loading

### Console & Logs

- [ ] No JavaScript errors in browser console
- [ ] No React warnings about missing props
- [ ] API logs show v6 requests (no errors)
- [ ] No privacy check violations in logs

### Save QA Report

Create `reports/v6/staging_qa_YYYYMMDD.md` with:
- Date and tester name
- Test organizations (EINs tested)
- Tier distribution (how many of each tier tested)
- Pass/fail for each verification
- Screenshots of Tier 1, 2, 5 pages
- Any regressions or issues found
- Overall staging readiness (PASS / WARN / FAIL)

### Disabling Staging

If issues found:

```bash
unset ENABLE_V6_FINANCIAL_CONTEXT
unset VITE_ENABLE_V6_FINANCIAL_CONTEXT

./restart_api.sh
```

**Result:** API returns v5 context, frontend shows v5 display. No data loss; reverts to prior version.

---

## PHASE 8 — APPROVAL GATE

### Founder Approval Checklist

Founder must explicitly approve **each of these** before production activation:

| Item | Evidence | Status |
|------|----------|--------|
| Corrected fairness report passes | No blocking conditions in report | ⏳ |
| SQLite integrity check = `ok` | `PRAGMA integrity_check;` result | ⏳ |
| Daily workflow tested | Daily operations run without error | ⏳ |
| Weekly workflow tested | Weekly candidate generation passes | ⏳ |
| Staging QA complete | All test organizations pass + no regressions | ⏳ |
| Organization page messaging approved | Founder reviews Tier 1/2/5 samples | ⏳ |
| Privacy checks pass | All 8/8 privacy gates pass | ✅ |
| Rollback procedure tested | Founder confirmed 2–3 minute disable works | ⏳ |
| Candidate remains inactive | `status='candidate'` until approval | ✅ |
| Approval record documented | Founder signature + date in approval_log | ⏳ |

### Approval Record

When founder approves, create `docs/V6_APPROVAL_LOG_20260727.md`:

```markdown
# V6 Production Approval

**Date:** 2026-07-27  
**Approved by:** [Founder name]  
**Candidate run:** v6_foundation_candidate_20260728_revised  
**Baseline run:** v6_foundation_candidate_20260727_corrected  

## Approval Checklist

- [x] Fairness report passes (0% ≤ revocation ≤ 100%, small-org data complete)
- [x] Integrity check returns `ok`
- [x] All tests pass (24/24 + privacy 8/8)
- [x] Staging QA complete (10+ test orgs, no regressions)
- [x] Page messaging approved (Tier 1/2/5)
- [x] Rollback procedure tested
- [x] Candidate inactive until approval

## Activation Command

```bash
# Activate candidate
sqlite3 data/merit_registry.db \
  "UPDATE v6_scoring_runs SET status='approved' WHERE run_id='v6_foundation_candidate_20260728_revised';"

# Enable v6 in production
export ENABLE_V6_FINANCIAL_CONTEXT=true
export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true

# Restart
./restart_api.sh && cd frontend && npm run build
```

## Rollback Command

```bash
# Disable v6
unset ENABLE_V6_FINANCIAL_CONTEXT
unset VITE_ENABLE_V6_FINANCIAL_CONTEXT

# Restart (reverts to v5)
./restart_api.sh
```

---
```

### Production Activation (Post-Approval)

Only after founder approval:

```bash
# 1. Activate in database
sqlite3 data/merit_registry.db \
  "UPDATE v6_scoring_runs SET status='approved' WHERE run_id='v6_foundation_candidate_20260728_revised';"

# 2. Enable feature flags in production
export ENABLE_V6_FINANCIAL_CONTEXT=true
export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true

# 3. Rebuild frontend
cd frontend && npm run build && cd ..

# 4. Restart API
./restart_api.sh

# 5. Monitor for 24 hours
# - Check /health endpoint
# - Monitor API response times
# - Check error logs for issues
# - Gather user feedback
```

### 24-Hour Monitoring

After production activation, monitor:

- **API health:** All `/health` checks return 200
- **Response times:** Org pages < 200ms, `/api/organizations` < 500ms
- **Error rates:** No spike in 5xx errors
- **User feedback:** Check support channels for issues
- **Coverage:** Verify v6 is displayed on ~95% of org pages

If issues detected during monitoring → execute rollback command above.

---

## AUTOMATIC IMPROVEMENT POLICY

### What the System MAY Do Automatically

The following operations may run without founder approval each cycle:

1. **Discover new source files**
   - IRS SOI filings
   - ProPublica 990 updates
   - Donation link crawls

2. **Validate records**
   - Check EIN format, revenue values, NTEE codes
   - Quarantine invalid records
   - Log data quality metrics

3. **Update normalized tables transactionally**
   - Insert new orgs + update existing
   - Maintain state + local values
   - Preserve prior filing years

4. **Generate new candidate run**
   - Fresh run ID every week
   - Apply v6 scoring logic
   - Exclude revoked orgs

5. **Build conditional context**
   - Peer groups for Tier 2 (by revenue band)
   - Regional distribution stats
   - NTEE metrics

6. **Produce fairness reports**
   - Compare new candidate vs. baseline
   - Quantify coverage changes
   - Analyze small-org impact

7. **Produce QA reports**
   - Data quality summary
   - Validation results
   - Revocation status

### What the System MUST NOT Do Automatically

The following require explicit founder action:

1. ❌ **Activate a candidate**
   - Remains `status='candidate'` until founder approval
   - No auto-promotion

2. ❌ **Change public methodology**
   - Tier definitions, peer group rules, archetype mappings
   - Published only via versioned release

3. ❌ **Publish a new score**
   - Must be activated by founder
   - Switching from v5 → v6 is irreversible

4. ❌ **Alter nonprofit visibility**
   - Tier 5 does not hide orgs (archetype-only)
   - No org is removed from directory

5. ❌ **Penalize for missing information**
   - Missing data = Tier 2+ or Tier 5, not shame
   - Tier 5 is neutral (not "bad")

6. ❌ **Repair disputed records without source**
   - Revocation mismatches flagged for manual review
   - Ingestion errors logged, not silently fixed
   - Founder determines source-backed corrections

7. ❌ **Delete historical scoring runs**
   - All runs preserved as audit trail
   - Never destructively rewrite history

8. ❌ **Overwrite prior source records**
   - Source data append-only with hash tracking
   - Prior years never deleted

### Release Metadata

Each public v6 release must record:

| Field | Example | Purpose |
|-------|---------|---------|
| run_id | v6_foundation_candidate_20260728_revised | Unique ID |
| source_snapshot | IRS 2024, ProPublica 2024.07.15 | Input versions |
| methodology_version | v6.0 | Scoring logic version |
| git_commit | abc123def456... | Code version |
| validation_results | All 10 gates pass | Audit |
| fairness_report | reports/v6/fairness_...md | Analysis |
| privacy_result | 8/8 gates pass | Compliance |
| approval_date | 2026-07-27 | Sign-off |
| approval_by | Founder name | Authority |
| rollback_target | v5_foundation_active | Fallback |

---

## Summary

| Phase | Owner | Status |
|-------|-------|--------|
| 1. Local Verification | Automation | Script ready |
| 2. Quiet-Window Integrity | Automation | Procedure ready |
| 3. Daily Operations | Automation | Script ready (dry-run default) |
| 4. Weekly Candidate | Automation | Script ready |
| 5. Fairness Gates | Automation | Built into fairness script |
| 6. Scheduling | Ops | Cron/systemd templates provided |
| 7. Staging QA | Founder | Checklist ready |
| 8. Approval Gate | Founder | Log template ready |

**No phase proceeds automatically without passing all gates for that phase.**

**Founder approval is required only for:**
- Staging activation (Phase 7 QA complete)
- Production activation (Phase 8 approval checklist signed)

All other phases are automated.

