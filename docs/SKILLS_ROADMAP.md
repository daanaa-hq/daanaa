# Skills & Integration Roadmap

**Prepared:** 2026-07-31  
**Scope:** Phase 1 monitoring through Phase 2 implementation  
**Goal:** Automate routine checks, document key workflows

---

## HIGH-PRIORITY (Aug 1-7)

### /phase1-monitor — Quality Gate Automation
**Why:** 7-day monitoring is manual and repetitive. Need structured daily checks.

**Function:**
```bash
/phase1-monitor --daily
  ✅ Plausible: Check signal endpoint error rate (<5%)
  ✅ Accuracy: Sample 10 random orgs, verify signals vs IRS.gov
  ✅ Performance: Verify org pages stay <200ms (regression check)
  ✅ Freshness: Confirm daily IRS sync ran (<24h lag)
  ✅ Report: PASS/FAIL on all criteria
  ✅ Post: Auto-comment to DECISIONS.md if FAIL
```

**Effort:** 2-3 hours to build (Python + API queries)  
**ROI:** High (eliminates 10-15 min/day of manual work, auto-escalates issues)  
**Owner:** Build during Phase 1 kickoff (July 31-Aug 1)

---

## MEDIUM-PRIORITY (Aug 15-30)

### /wallet-qa — Phase 2 Compliance Testing
**Why:** Wallet ships with legal disclaimers; need automated compliance verification.

**Function:**
```bash
/wallet-qa [--scenario save|export|acknowledge|delete]
  ✅ User flow: Save org → Verify intent stored
  ✅ Disclaimer: Verify ToS/Privacy/wallet disclaimer displayed
  ✅ Export: Verify PDF includes all disclaimers, no donation data
  ✅ Privacy: Verify no PII stored, no tracking, no 3rd-party sharing
  ✅ Compliance: Cross-check against PHASE2_LITIGATION_RISK_MITIGATION.md
  ✅ Report: 5-scenario checklist + PASS/FAIL
```

**Effort:** 3-4 hours to build (extend /qa, add wallet-specific assertions)  
**ROI:** Medium (prevents compliance issues, speeds Phase 2 QA)  
**Owner:** Build during Phase 2 implementation (Aug 15-20)

---

## LOWER-PRIORITY (Sept+)

### /small-org-search — Visibility Metrics
**Why:** Measure success of small org visibility roadmap (+20% CTR target).

**Function:**
```bash
/small-org-search --report monthly
  ✅ CTR: small orgs vs all orgs (baseline vs current)
  ✅ Hidden gems: clicks/week since launch
  ✅ Geographic: "food banks in [zip]" success rate
  ✅ Wallet: aggregate user interest by org size
  ✅ Report: Dashboard-ready metrics for founder review
```

**Effort:** 2-3 hours to build (Plausible API + analytics)  
**ROI:** Medium (visibility roadmap validation)  
**Owner:** Build during Sept, after Phase 2 ships

---

## GitHub Repos to Consider

### Open-Source Contributions (Strategic)
1. **daanaa-org-dataset** (Public, post-Phase-1)
   - Anonymized org data + scoring methodology
   - Why: Research partnerships, transparency, regulatory goodwill
   - When: After Phase 1 succeeds

2. **nonprofit-website-corpus** (Public, post-Phase-1)
   - 2,307 discovered websites + verification notes
   - Why: Help other platforms improve discovery
   - When: After small org visibility roadmap launches

3. **donor-verification-toolkit** (Reference link)
   - Link to external best-practices repo
   - Why: Stakeholder alignment
   - When: Not urgent, link-only

### Operational Integration (GitHub Actions)
1. **Pre-commit automation**
   - Route privacy_check.sh → GitHub hooks
   - Benefit: Block commits with sensitive data pre-push
   - Effort: 2-3 hours

2. **Nightly pipeline dashboard**
   - Public GitHub wiki summarizing pipeline health
   - Benefit: Transparency, easier debugging
   - Effort: 3-4 hours

3. **Deployment logs**
   - Archive logs to GitHub + link from issues
   - Benefit: Audit trail, debugging
   - Effort: 2-3 hours

---

## Implementation Timeline

| Date | Skill | Effort | Owner |
|------|-------|--------|-------|
| Aug 1 | /phase1-monitor | 2-3h | Build now (before monitoring starts) |
| Aug 15 | /wallet-qa | 3-4h | Build during Phase 2 implementation |
| Sept | /small-org-search | 2-3h | Build after Phase 2 ships |
| Sept+ | Open-source repos | 1-2 days | If community interest validates |
| Oct+ | GitHub Actions | 3-4h | Parallel with Phase 3 work |

---

## Success Metrics

- `/phase1-monitor` reduces daily checking time from 15 min → 2 min
- `/wallet-qa` catches 95%+ of compliance issues before staging
- `/small-org-search` proves +20% small org CTR target achievable
- Open-source repos get 10+ stars on GitHub (validation of approach)

---

**Recommendation:** Start with `/phase1-monitor`. It directly supports the Aug 7 quality gate and pays for itself in time saved within 3 days.

