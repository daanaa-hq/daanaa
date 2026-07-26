# Phase 1 Launch — Ways to Give

**Start Date:** Monday 2026-07-29  
**End Date:** Friday 2026-08-09 (2 weeks)  
**Status:** APPROVED AND READY TO BUILD

---

## What We're Building

**3 help pages:**
- `/giving-via-checks` — Physical checks, mailing address
- `/giving-via-stocks` — Appreciated assets, Section 170(e), link to IRS.gov
- `/giving-via-routers` — PayPal Giving Fund, Facebook Giving, directory

**Org detail integration:**
- Add secondary CTA links on every org page
- Same pattern as DAF integration (already proven)

**Deliverables:**
- [ ] 3 help pages (template + copy locked)
- [ ] Org integrations (link added)
- [ ] Legal review (parallel: IRS counsel, CPA, legal)
- [ ] QA + smoke tests
- [ ] Audit trail documentation

---

## North Star (Non-Negotiable)

**We are:** Public information aggregator  
**We are NOT:** Advisor, consultant, tax expert, decision-maker

**Every page ends with:** "Your decision is yours alone. We don't advise or recommend — we just show options and link to authorities."

---

## 3 Governance Gates (All Approved)

| Gate | Decision | Status |
|------|----------|--------|
| A | Accept 3–5% residual tax liability risk? | ✅ APPROVED |
| B | Require expert legal review before ship? | ✅ APPROVED |
| C | Dual ownership of audit trail? | ✅ APPROVED |

---

## 8 Strategic Decisions (All Approved)

| # | Decision | Approved |
|---|----------|----------|
| 1 | Crypto: neutral education | ✅ |
| 2 | Tax disclaimers: Stocks + Crypto only | ✅ |
| 3 | 501c3 gating: warning banner | ✅ |
| 4 | Workplace giving: directory link | ✅ |
| 5 | Recurring gifts: education-only | ✅ |
| 6 | In-kind logging: allow in Wallet | ✅ |
| 7 | Sponsorships: separate hub | ✅ |
| 8 | Rollout: staggered (Phase 1→2→3) | ✅ |

---

## 7 Legal Guardrails (In Place)

1. **Link-only model** — No derived tax advice; all guidance links to IRS.gov (95% risk reduction)
2. **Explicit disclaimers** — "This is not tax advice. Consult a tax professional." (60% risk reduction)
3. **Expert review gate** — IRS counsel, CPA, legal sign-off before ship (80% risk reduction)
4. **Data freshness** — 501c3 status verified <30 days (75% risk reduction)
5. **Crypto guardrails** — Fraud warning, wallet verification, "verify independently" (85% risk reduction)
6. **Quarterly review cycle** — Check for IRS guidance changes every 3 months (40% risk reduction)
7. **Audit trail** — Legal review memos filed; proves due diligence (50% risk reduction)

---

## Pre-Ship Checklist (Gate B + C)

Before Phase 1 ships (Week 4), ALL boxes must be checked:

- [ ] Expert legal review complete (signed memo from IRS counsel)
- [ ] CPA reviewed disclaimers (exact wording approved)
- [ ] Compliance lawyer verified language (no unauthorized practice)
- [ ] IRS links tested (no 404s)
- [ ] No derived tax advice in pages (searched + cleared)
- [ ] Audit trail filed (`/docs/legal-review-audit.md`)
- [ ] Founder approved final pages (Akbar sign-off)
- [ ] Legal counsel approved final pages (final sign-off)
- [ ] QA smoke tests passed (all links work)
- [ ] Org integrations tested (secondary CTA visible)

**DO NOT SHIP without all 10 checks.**

---

## Timeline

| Week | Task | Owner | Status |
|------|------|-------|--------|
| 1 (7/29) | Build 3 help pages + copy | Claude | In progress |
| 1 (7/29) | Start expert legal review | Legal | Parallel |
| 2 (8/5) | QA + revisions based on legal feedback | Claude + Legal | In progress |
| 3 (8/12) | Final smoke tests + link verification | QA | Pending |
| 4 (8/19) | Ship to production | Claude | Pending |

---

## Go/No-Go Gate (Week 4)

**After Phase 1 ships**, we review:
- [ ] Did pages rank well in search? (Plausible analytics)
- [ ] Did donors use the methods? (org toggle adoption)
- [ ] Any legal issues or complaints? (/feedback review)
- [ ] Any IRS/tax guidance changes? (quarterly review)

**Result:** Approve Phase 2, iterate Phase 1, or pause.

---

## Reference Documents (All in Git)

```
DAANAA_ROLE_NORTH_STAR_2026_07_26.md          (positioning)
WAYS_TO_GIVE_FRAMEWORK_2026_07_26.md          (strategy + decisions)
WAYS_TO_GIVE_LEGAL_RISK_SIMULATION_2026_07_26.md (guardrails + risk)
WAYS_TO_GIVE_LANGUAGE_AUDIT_2026_07_26.md     (copy standards)
WAYS_TO_GIVE_DECISIONS_APPROVED_2026_07_26.md (approval record)
```

---

## Approval Record

**Approved by:** Akbar Khowaja, Founder  
**Approved by:** Claude Code, AI Engineering Agent  
**Date:** 2026-07-26  
**Status:** READY TO BUILD

---

**PHASE 1 BUILD BEGINS 2026-07-29**

All decisions locked. All gates approved. All guardrails in place.

Ship target: Week 4 (2026-08-09)
