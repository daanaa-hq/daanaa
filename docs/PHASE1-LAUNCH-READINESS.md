# Phase 1 Launch Readiness — Production Deployment

**Initiative:** Ways to Give (Checks, Stocks, Routers)  
**Target Launch:** Friday 2026-08-09 (Week 4)  
**Status:** Pre-Launch Prep (Weeks 1–3)  
**Owner:** Akbar Khowaja (Founder)

---

## Launch Timeline

| Week | Task | Owner | Status | Sign-Off |
|---|---|---|---|---|
| **Week 1 (7/29–8/2)** | Build 3 help pages + org integration | Claude | ✅ COMPLETE | ☐ |
| **Week 1–2 (7/29–8/6)** | Expert legal review (parallel) | Counsel/CPA | 🔄 IN PROGRESS | ☐ |
| **Week 2 (8/5)** | Apply legal edits, re-review | Claude | Pending legal | ☐ |
| **Week 3 (8/5–8/9)** | QA testing + smoke tests | QA Lead | Pending legal | ☐ |
| **Week 4 (8/9)** | Final approval + production ship | Akbar | Pending all | ☐ |

---

## Pre-Launch Checklist (All Must Pass)

### Code Quality

- [ ] TypeScript builds clean (`npm run build` → 0 errors)
- [ ] No console errors in DevTools (warnings OK)
- [ ] All three pages load without 404s
- [ ] Org detail CTAs visible on 100% of test orgs
- [ ] No broken links (IRS, platforms, internal routes)
- [ ] Lighthouse performance score > 85
- [ ] Mobile layout responsive (tested on iPhone, Pixel)

### Legal Compliance

- [ ] IRS Tax Counsel reviewed and approved copy ✅
- [ ] CPA reviewed substantiation language ✅
- [ ] Compliance Lawyer cleared liability language ✅
- [ ] All edits from legal review applied ✅
- [ ] Copy audit passed (no shame language, no unauthorized advice) ✅
- [ ] Evidence base (`IRS-GIVING-GUIDANCE-EVIDENCE-BASE.md`) filed for audit trail ✅

### QA Testing

- [ ] Critical path tests: 100% pass (see `PHASE1-QA-TEST-PLAN.md`) ✅
- [ ] External links verified (no 404s, no redirects) ✅
- [ ] Responsive design tested (mobile + desktop) ✅
- [ ] Donor journey scenarios completed (4 scenarios) ✅
- [ ] No P0/P1 bugs remain ✅
- [ ] QA sign-off obtained ✅

### Security & Privacy

- [ ] Privacy check passed (pre-commit hook) ✅
- [ ] No hardcoded secrets in code ✅
- [ ] No tracking of donor giving activity ✅
- [ ] No changes to Daanaa data handling (read-only pages) ✅
- [ ] Stewardship principles alignment verified ✅

### Deployment

- [ ] Droplet is at last known-good version (no unrelated changes) ✅
- [ ] Production database verified (no test data) ✅
- [ ] Backup of current state taken (`daanaa_backup.sh`) ✅
- [ ] Rollback plan documented (see "Rollback Plan" below) ✅
- [ ] Monitoring alerts enabled for uptime ✅

### Documentation

- [ ] Legal review package filed (`PHASE1-LEGAL-REVIEW-PACKAGE.md`) ✅
- [ ] QA test results documented (`PHASE1-QA-TEST-PLAN.md`) ✅
- [ ] Deployment decisions logged in `DECISIONS.md` ✅
- [ ] Any bugs found + fixed logged in `LESSONS.md` ✅

---

## Deployment Steps (Week 4, 2026-08-09)

### Step 1: Final Build & Verification (08:00 AM)

```bash
cd /home/akbar/meritgiving
git status                    # Verify clean working tree
git log --oneline -5          # Check recent commits
npm run build                 # Rebuild frontend (watch for errors)
```

**Expected Output:**
```
✓ built in <5s
```

**Sign-Off:** Akbar ☐

---

### Step 2: Smoke Test (Local) (08:15 AM)

```bash
# Start dev server
npm run dev &

# In another terminal, verify routes
curl http://localhost:5173/giving-via-checks
curl http://localhost:5173/giving-via-stocks
curl http://localhost:5173/giving-via-routers
```

**Expected:** All three return 200 + HTML  
**Sign-Off:** Akbar ☐

---

### Step 3: Backup Current State (08:30 AM)

```bash
# Create backup of current droplet state
bash scripts/daanaa_backup.sh

# Verify backup exists
ls -lh backups/ | tail -1
```

**Expected:** Backup file created, size > 100MB  
**Sign-Off:** Akbar ☐

---

### Step 4: Deploy to Droplet (08:45 AM)

**Choose deployment method based on changes:**

Since this is **code-only** (frontend routes + org detail integration, no API/data changes):

```bash
bash scripts/safe_deploy_droplet.sh --code-only
```

**Expected Output:**
```
[✓] Building SPA...
[✓] Syncing to droplet...
[✓] Verifying deployment...
[✓] Smoke tests passed
```

**Duration:** ~5 minutes  
**Sign-Off:** Akbar ☐

---

### Step 5: Production Smoke Tests (09:00 AM)

**Test from command line:**

```bash
# 1. Homepage loads
curl -s https://daanaa.org/ | grep -q "Daanaa" && echo "✓ Home 200" || echo "✗ Home failed"

# 2. Directory loads
curl -s https://daanaa.org/directory | grep -q "Browse" && echo "✓ Directory 200" || echo "✗ Directory failed"

# 3. Org detail with CTAs
curl -s https://daanaa.org/org/264837170 | grep -q "giving-via" && echo "✓ Org detail 200" || echo "✗ Org failed"

# 4. New giving pages exist
curl -s https://daanaa.org/giving-via-checks | grep -q "Give by Check" && echo "✓ Checks page 200" || echo "✗ Checks failed"
curl -s https://daanaa.org/giving-via-stocks | grep -q "appreciated" && echo "✓ Stocks page 200" || echo "✗ Stocks failed"
curl -s https://daanaa.org/giving-via-routers | grep -q "PayPal\|Facebook" && echo "✓ Routers page 200" || echo "✗ Routers failed"

# 5. IRS links work (sample check)
curl -sI https://www.irs.gov/publications/p526 | grep -q "200\|301\|302" && echo "✓ IRS link valid" || echo "✗ IRS link broken"
```

**Expected:** All ✓ checks pass  
**Sign-Off:** Akbar ☐

---

### Step 6: Manual Browser Testing (09:15 AM)

**Open browser, test on live site:**

1. **Checks page:** https://daanaa.org/giving-via-checks
   - ✓ Hero loads, 4 steps visible, EIN info shown
   - ✓ Links to /directory work
   - ✓ IRS Pub 526 link works

2. **Stocks page:** https://daanaa.org/giving-via-stocks
   - ✓ Hero loads, "12-month" rule mentioned
   - ✓ "Contact nonprofit" step clear
   - ✓ Form 8283 link works

3. **Routers page:** https://daanaa.org/giving-via-routers
   - ✓ Hero loads, 4 platforms shown
   - ✓ PayPal, Facebook, Benevity, GiveDirectly links work
   - ✓ EIN section visible

4. **Org Detail:** https://daanaa.org/org/264837170 (or any org)
   - ✓ 4 giving method CTAs visible
   - ✓ "Give by check" → /giving-via-checks
   - ✓ "Give appreciated stock" → /giving-via-stocks
   - ✓ "Give via PayPal or Facebook" → /giving-via-routers
   - ✓ "Give via donor-advised fund" → /giving-via-daf

5. **Mobile:** Test on iPhone or dev tools (iPhone 14 size)
   - ✓ Text readable, no layout breaks
   - ✓ Links tappable
   - ✓ CTAs appear on org page

**Sign-Off:** Akbar ☐

---

### Step 7: Verify Analytics Baseline (09:30 AM)

**Check Plausible (no new spike = expected for educational pages):**

- Open https://plausible.io → Daanaa dashboard
- Note traffic on `/giving-via-*` routes (should be ~0 initially)
- Check that `/directory`, `/org/*` traffic is normal (not degraded)

**Expected:** No unexpected errors or traffic spikes  
**Sign-Off:** Akbar ☐

---

### Step 8: Announce & Monitor (09:45 AM)

**Send internal notification:**
```
✅ Phase 1 (Ways to Give) is LIVE

New pages:
- /giving-via-checks — Physical checks
- /giving-via-stocks — Appreciated securities
- /giving-via-routers — PayPal Giving Fund, Facebook Giving, etc.

All org pages now show 4 giving method options.

Monitor for 24h for any issues. Report in #daanaa-ops.
```

**Monitor for 24 hours:**
- Watch Plausible for errors
- Check feedback flow for "broken link" reports
- Watch Droplet logs: `tail -f logs/gunicorn.log`
- Check Sentry (if enabled) for JavaScript errors

**Sign-Off:** Akbar ☐

---

## Rollback Plan (If Something Goes Wrong)

### Scenario: Page doesn't load (404 on /giving-via-checks)

**Recovery (< 2 minutes):**
```bash
# 1. Verify droplet deployment worked
ssh root@162.243.97.179
ls -la /opt/daanaa/dist/index.html

# 2. If missing, restore from backup
bash scripts/daanaa_backup.sh --restore <backup-file>

# 3. Verify homepage loads
curl https://daanaa.org/

# 4. If still broken, rollback code
git revert <commit-hash>
bash scripts/safe_deploy_droplet.sh --code-only
```

### Scenario: Org detail CTAs broken (links go to 404)

**Recovery:**
```bash
# Issue is likely in App.tsx routes
# Check if routes were deployed
curl https://daanaa.org/api/organizations/264837170 # org data OK?

# If org data loads, issue is frontend routing
# Redeploy frontend only
cd /home/akbar/meritgiving/frontend
npm run build
# Push to droplet manually or via script
```

### Scenario: IRS link returns 404 (IRS changed URL)

**Recovery (immediate, < 5 minutes):**
1. Update the broken IRS URL in the page component
2. Rebuild frontend (`npm run build`)
3. Redeploy to droplet (`bash scripts/safe_deploy_droplet.sh --code-only`)

### Nuclear Option: Revert Entire Deploy

```bash
# If something is very wrong:
git revert <commit-hash>  # Revert Phase 1 commit
bash scripts/safe_deploy_droplet.sh --code-only
# Pages will be gone; CTAs removed from org pages
# Investigate offline, redeploy when ready
```

**Rollback Signal:** If any of these occur:
- Homepage 500 error (not just giving pages)
- Org detail page broken (CTAs crash page)
- > 10% of requests failing
- Positive signal: one broken link is OK, escalate but don't panic

---

## Post-Launch: 24-Hour & 1-Week Monitoring

### First 24 Hours

**Hourly checks (auto or manual):**
- Homepage: `curl https://daanaa.org/ -o /dev/null -w "%{http_code}"`
- One giving page: `curl https://daanaa.org/giving-via-checks -o /dev/null -w "%{http_code}"`
- One org detail: `curl https://daanaa.org/org/264837170 -o /dev/null -w "%{http_code}"`
- All should return 200

**Watch feedback flow:**
- Any reports of broken links?
- Any tax-related complaints?
- Anything in Sentry (JS errors)?

**Decision:** If all green after 24h, proceed to normal monitoring.

### Week 1 Review (2026-08-16)

**Check metrics:**
- `DECISIONS.md`: Log deployment decision + any issues
- `LESSONS.md`: Any lessons from launch?
- Traffic on giving pages: Are donors discovering them?
- Feedback received: Any user confusion?

**Go/No-Go for Phase 2:**
- If Phase 1 is solid: Begin planning Phase 2 (workplace giving, recurring, crypto)
- If issues found: Hotfix, re-test, then proceed

---

## Stewardship Alignment Checklist

Before shipping, confirm alignment with Stewardship principles:

- [ ] **P1 (Mission before growth):** Pages educate, don't upsell. Simple methods first (checks), complex methods documented. ✅
- [ ] **P2 (Privacy):** No donor data collected. Giving methods are anonymous. No tracking. ✅
- [ ] **P3 (Evidence-based):** Every tax claim sourced to IRS. No speculation. ✅
- [ ] **P5 (No shame language):** Financial context scoring separate from giving methods. No shaming. ✅
- [ ] **P8 (Never handle funds):** All links are direct to nonprofit or intermediary. Daanaa never touches money. ✅

---

## Go/No-Go Decision Gate

**Before 09:00 AM on 2026-08-09, confirm:**

- [ ] Legal review complete and approved
- [ ] QA testing complete (all tests pass)
- [ ] Code builds clean
- [ ] Backup verified
- [ ] Rollback plan confirmed
- [ ] Monitoring enabled
- [ ] Team notified

**Founder Decision:**
- [ ] GO — Ship Phase 1
- [ ] NO-GO — Delay (explain why in `DECISIONS.md`)

**Decision Time:** 09:00 AM 2026-08-09  
**Founder Sign-Off:** _________________ Date: _____

---

## Contacts & Escalation

**If something breaks during deployment:**

| Issue | Contact | Response Time |
|---|---|---|
| Technical (code/deploy issue) | Claude (available) | Immediate |
| Legal question | [Counsel name] | 2 hours |
| Panic/emergency | Akbar | Immediate |

---

**Prepared:** 2026-07-26  
**Last Updated:** 2026-07-26  
**Next Review:** Pre-launch (Week 4)  
**Status:** Ready for Weeks 1–3 execution
