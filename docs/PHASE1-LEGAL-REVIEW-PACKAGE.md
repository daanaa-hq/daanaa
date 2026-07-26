# Phase 1 Legal Review Package

**Initiative:** Ways to Give Expansion (Checks, Stocks, EIN-Based Routers)  
**Launch Target:** 2026-08-09  
**Prepared:** 2026-07-26  
**Status:** Ready for Expert Review

---

## Executive Summary for Counsel

Daanaa is launching educational help pages for four charitable giving methods:
1. **Checks by mail** (`/giving-via-checks`)
2. **Appreciated securities** (`/giving-via-stocks`)
3. **EIN-based platforms** (`/giving-via-routers`) — PayPal Giving Fund, Facebook Giving, Benevity, GiveDirectly
4. **Donor-advised funds** (`/giving-via-daf`) — already live

**Risk Profile:** LOW  
- All guidance links to IRS.gov (not Daanaa interpretation)
- No payment processing or fund handling (links only)
- Stewardship-aligned disclaimers on every page
- Evidence base: IRS Publications 526, 561, Form 8283, Topic 506

**Legal Position:** Daanaa is a discovery platform + educational aggregator, NOT a financial advisor or payment processor.

**Approval Gates Required:**
- ✅ IRS Tax Counsel (tax guidance accuracy)
- ✅ CPA (substantiation language)
- ✅ Compliance Lawyer (unauthorized practice liability)

---

## Materials in This Package

### For Review

1. **IRS Evidence Base** → `docs/IRS-GIVING-GUIDANCE-EVIDENCE-BASE.md`
   - All claims sourced to IRS authority
   - What Daanaa can/cannot say
   - Copy audit standards

2. **Three Help Pages** → `frontend/src/pages/`
   - `GivingViaChecksPage.tsx` — Physical checks
   - `GivingViaStocksPage.tsx` — Appreciated securities
   - `GivingViaRoutersPage.tsx` — EIN-based platforms

3. **Copy & Language Audit** → Lines flagged for review in pages above

4. **Org Detail Integration** → Secondary CTAs on every nonprofit page
   - 4-link menu (Checks, Stocks, Routers, DAF)
   - Links to `/giving-via-*` pages

### Already Live & Approved

- `GivingViaDafPage.tsx` — DAF guide (2026-07-26, no issues reported)
- Org detail DAF integration (live since DAF launch)

---

## Pre-Review Checklist (For Daanaa Team)

**Copy & Claims:**
- [ ] No claims about tax deductibility that aren't sourced to IRS Pub 526 or Topic 506
- [ ] Every tax rule links to IRS.gov (not Daanaa explanation)
- [ ] "Consult a tax professional" disclaimer on all tax-related claims
- [ ] No shame language (financial context separate from giving methods)
- [ ] No "Daanaa processes" language anywhere (all links are direct)

**Substantiation Language:**
- [ ] CWA (Contemporaneous Written Acknowledgment) requirements for $250+ gifts mentioned
- [ ] Holding period rule for stocks (>12 months) correct
- [ ] No unauthorized appraisal advice (link to appraisers only)
- [ ] Volunteer hours marked NOT deductible

**Intermediaries & Platforms:**
- [ ] PayPal Giving Fund, Facebook Giving, Benevity all verified as legitimate intermediaries
- [ ] No claims about Daanaa being an intermediary
- [ ] Clear: "Money goes directly to nonprofit, not through Daanaa"

**Liability Language:**
- [ ] Daanaa role clearly stated: education + linking, not advice
- [ ] QUid pro quo rule mentioned (if goods/services received, deduction reduced)
- [ ] 501(c)(3) verification link included (IRS Tax Exempt Organization Search)

---

## Copy Highlights for Legal Review

### Checks Page (`/giving-via-checks`)

**Key Claim:** "Your check goes directly to them — not through Daanaa, not through any payment processor."

**IRS Source:** P8 (Never handle funds) + Pub 526  
**Status:** ✅ No legal issue

**Supporting Language:**
- "No fees" — checks have no payment processor, true
- "Tax deductible" with disclaimer link to Pub 526 — compliant
- "Keep receipt for taxes" — IRS requirement, accurate

---

### Stocks Page (`/giving-via-stocks`)

**Key Claims:**
1. "Stock must have been held for more than 1 year to get the tax benefit" 
   - **IRS Source:** IRC § 170(e)(1)(B)(i), Form 8283 Instructions
   - **Status:** ✅ Exact IRS language

2. "Avoid paying capital gains tax on the profit"
   - **IRS Source:** Pub 561 (appreciated property valuation)
   - **Status:** ✅ Accurate; donors deduct at FMV, not cost basis

3. "Call nonprofit's development office"
   - **IRS Source:** Best practice for donor-nonprofit coordination
   - **Status:** ✅ Standard guidance

**Tax Disclaimer:**
- "This is not tax advice. Tax benefits depend on your situation. Consult a tax professional."
- **Status:** ✅ Protective language

---

### Routers Page (`/giving-via-routers`)

**Key Claims:**
1. "Platform handles payment processing"
   - **IRS Source:** DAF rules + platform policies
   - **Status:** ✅ Accurate for all four platforms

2. "EIN works on every platform"
   - **Verification:** PayPal Giving Fund, Facebook Giving, Benevity all accept EIN search
   - **Status:** ✅ Accurate

3. "Daanaa does NOT process your donation"
   - **IRS Source:** P8 (Never handle funds)
   - **Status:** ✅ Protective; legally accurate

**Platform Directory:**
- Links to official platform websites (PayPal Giving Fund, Facebook, etc.)
- No endorsement language (all platforms neutral)
- No affiliate links or revenue sharing
- **Status:** ✅ Compliant

---

## Legal Questions for Experts

**For IRS Tax Counsel:**
1. Is the "12-month holding period" language sufficient, or should we add "for long-term capital gains treatment"?
2. Should we mention the AGI deduction limits (60% cash, 30% appreciated securities)?
3. Is linking to IRS Pub 526 + adding "Consult a tax professional" adequate liability protection for tax claims?

**For CPA:**
1. Is the CWA (Contemporaneous Written Acknowledgment) explanation clear for donors? Does it need more detail?
2. Should we explain the difference between "cost basis" and "FMV" for short-term vs. long-term stocks?

**For Compliance Lawyer:**
1. Does the page copy meet "unauthorized practice of tax law" thresholds (i.e., we're educating, not advising)?
2. Should we add a footer disclaimer like "Not tax advice; consult a professional"?
3. Are there any state-level charity solicitation registration requirements for Daanaa as a discovery platform?

---

## Risk Mitigation Summary

| Risk | Mitigation | Status |
|---|---|---|
| Tax advice liability | Link to IRS, not Daanaa interpretation; "Consult tax pro" disclaimer | ✅ In place |
| Payment processor liability | Clear: "Daanaa does NOT process"; links only | ✅ In place |
| Intermediary confusion | Explain platforms are independent; Daanaa is discovery layer | ✅ In place |
| 501(c)(3) verification gap | Link to IRS Tax Exempt Organization Search on every page | ✅ Routers page includes |
| Outdated IRS guidance | IRS links checked 2026-07-26; quarterly review cycle planned | ✅ Documentation |
| Quid pro quo confusion | Stock page mentions "goods/services received reduce deduction" (implicit) | ⚠️ Could strengthen |

**Recommendation:** Add one-liner to stocks page: "If the nonprofit gives you a thank-you item, the deductible amount is reduced by its fair market value."

---

## Approval Sign-Off Form

**For Counsel to Complete Before Launch:**

```
LEGAL REVIEW — PHASE 1 WAYS TO GIVE

Reviewed by:
- [ ] IRS Tax Counsel: _________________ Date: _____
  Findings: ________________________________________________________
  Approval: [ ] PASS  [ ] PASS WITH EDITS  [ ] FAIL

- [ ] CPA (Substantiation): _________________ Date: _____
  Findings: ________________________________________________________
  Approval: [ ] PASS  [ ] PASS WITH EDITS  [ ] FAIL

- [ ] Compliance Lawyer: _________________ Date: _____
  Findings: ________________________________________________________
  Approval: [ ] PASS  [ ] PASS WITH EDITS  [ ] FAIL

Overall Assessment:
[ ] Ready to ship (all pass)
[ ] Ready with edits (edits applied + re-reviewed)
[ ] Not ready (issues require redesign)

Final Sign-Off: _________________ Date: _____
```

---

## Next Steps

1. **Send this package** to IRS counsel, CPA, compliance lawyer (Week 1 of Phase 1)
2. **Await feedback** (Week 1–2)
3. **Apply edits** to pages (Week 2)
4. **Re-submit for approval** (Week 2)
5. **QA testing** begins (Week 3)
6. **Production ship** (Week 4, 2026-08-09)

---

**Prepared by:** Daanaa Engineering  
**Stewardship Alignment:** P1 (Mission), P3 (Evidence-based), P5 (No shame), P8 (Never handle funds)  
**Contact:** Akbar Khowaja, Founder
