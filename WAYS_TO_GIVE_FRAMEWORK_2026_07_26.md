# Ways to Give — Strategic Framework (2026-07-26)

**Status:** Board proposal awaiting approval  
**Scope:** Comprehensive giving methods map + compliance audit + phased rollout  
**Board decision points:** 8 (marked below)  
**Legal posture:** All methods respect P8 (never handle funds)

---

## Executive Summary

Daanaa currently supports two giving methods:
1. **Direct donate links** (org's own processor or EIN-based router)
2. **Donor-Advised Funds (DAF)** — launched 2026-07-26

This framework proposes expanding to 6-8 additional methods, each with a help page + org integration, aligned with Stewardship Principles and legal posture.

**Board decisions required:** 8 (see section 5)  
**Total effort (phased):** ~60 human-hours over 12 weeks  
**Risk:** Low (all methods link-based; Daanaa never touches money)  
**Revenue impact:** None (all link-based; no transaction fee opportunity)

---

## Section 1: All Giving Methods (Mapped)

### Currently Live ✅

| Method | What is it? | Org role | Daanaa role | Current status |
|--------|-----------|---------|------------|----------|
| **Direct link** | Org's own donate page | Recipient + processor | Discovery + link | Live on org pages |
| **Donor-Advised Fund** | Donor's account; org receives grant | Recipient | Education + EIN lookup | Live 2026-07-26 |

### Proposed (Phased Rollout)

#### Phase 1 (High Priority — Weeks 1-4)

| Method | What is it? | Org role | Daanaa role | P8 Status | Effort | Risk |
|--------|-----------|---------|------------|-----------|--------|------|
| **Check by mail** | Physical check; donor writes it | Recipient | Education + mailing address | ✅ Safe | 0.5h | Low |
| **Stocks/appreciated assets** | Donor's broker; avoid cap gains tax | Recipient | Education + tax ID | ✅ Safe | 1h | Low |
| **EIN-based donation routers** | DAF-like; org receives funds via EIN | Recipient | Link to established routers | ✅ Safe | 0.5h | Low |

#### Phase 2 (Medium Priority — Weeks 5-8)

| Method | What is it? | Org role | Daanaa role | P8 Status | Effort | Risk |
|--------|-----------|---------|------------|-----------|--------|------|
| **Workplace giving** | Employer matching + CyberGrants/NP Easy | Recipient | Education + links | ✅ Safe | 1h | Low |
| **Recurring gifts** | Donor sets up autopay via org's processor | Recipient | Education + UX for tracking | ✅ Safe | 2h | Low |
| **Cryptocurrency** | Donor transfers crypto; org keeps or converts | Recipient | Education + legal framing | ⚠️ Compliance | 2h | Med |

#### Phase 3 (Lower Priority — Weeks 9-12)

| Method | What is it? | Org role | Daanaa role | P8 Status | Effort | Risk |
|--------|-----------|---------|------------|-----------|--------|------|
| **In-kind donations** | Goods, services, volunteering hours | Recipient | Education only | ✅ Safe | 1h | Low |
| **Sponsorships/grants** | Foundation/corporate grants | Recipient | Directory of grant databases | ✅ Safe | 1.5h | Low |

---

## Section 2: Stewardship Alignment (P1-P11)

### All Methods Pass Core Gates

✅ **P1 (Mission before growth):** No revenue model; all link-based; no incentive misalignment  
✅ **P2 (Privacy is core):** No donor tracking; no account required; no data to external services  
✅ **P3 (Evidence-based):** All methods reference public, auditable sources (IRS, SEC, tax code)  
✅ **P4 (Small orgs fair):** All methods equally available to all org sizes  
✅ **P5 (No pressure):** All methods presented as equal options; no primary CTA  
✅ **P6 (Mistakes corrected):** Help pages versioned; corrections surface via /feedback  
✅ **P7 (Independence protected):** No partner influence; no sponsored methods  
✅ **P8 (Never handle funds)** ← **CRITICAL:** All methods link-based; Daanaa never touches money  
✅ **P9 (Decisions explainable):** Help pages document reasoning + links to tax code  
✅ **P10 (AI as tool):** No AI in this plan; all methods from tax code + IRS guidance  
✅ **P11 (Principles over convenience):** Some methods are friction (checks, crypto) but honest  

### Method-Specific Notes

**Stocks/appreciated assets:**
- P8 compliance: Donor's broker handles transfer; org receives proceeds. Daanaa never touches assets.
- Tax framing: Explain Section 170(e)(1)(B)(i) benefits clearly (avoid cap gains tax).
- Risk: Low. Org must have brokerage account; most mid+ orgs do.

**Cryptocurrency:**
- ⚠️ **Board decision point 1:** Does Daanaa explicitly endorse crypto as a giving method, or educate neutrally?
  - **Option A:** Endorse (mention on /giving-via-crypto help page + org pages)
  - **Option B:** Educate only (help page explains taxes + links to guides; org decides whether to accept)
  - **Recommendation:** Option B (neutral education) — preserves independence + lets orgs decide based on their constituency
- P8 compliance: Donor's wallet → org's wallet. Daanaa never holds keys or processes conversion.
- Tax framing: Mention Section 170(c) (charitable contributions) + capital gains treatment for long-held crypto.
- Risk: Medium. Tax treatment is evolving; Daanaa's help page disclaims ("not tax advice") and links to IRS guidance.

**Workplace giving (matching + CyberGrants/NP Easy):**
- Two sub-flows:
  1. Employer matching: Employer's payroll processor (ADP, Workday, etc.) → org
  2. Workplace charity platforms: CyberGrants, Benevity, NP Easy → org
- P8 compliance: Employer/platform handles funds. Daanaa links to employer guides + platform listings.
- Risk: Low. Both platforms are established (30+ years); compliance already built in.

**Recurring gifts:**
- Org's processor (Stripe, PayPal, GiveWP, etc.) handles recurring charge.
- Daanaa role: Educate donors about setting up recurrence; optionally show "recurring" badge on org pages if org enables it.
- P8 compliance: Processor holds funds; org receives periodic deposits.
- Risk: Low. Org already integrated with processor.

**In-kind donations:**
- Goods, volunteer hours, pro-bono services.
- Daanaa role: Help page + UX for donor to log in-kind gift (time, miles, service value).
- Wallet UX: "You've given 10 volunteer hours to [org]" + social sharing (optional, off by default per P2).
- P8 compliance: Daanaa records intent only; no funds or goods touch us.
- Risk: Low. No financial data, no processor integration needed.

**Sponsorships/grants:**
- Foundation grants (Ford, Gates, etc.) + corporate grants (Google.org, etc.) + government grants (HHS, NSF).
- Daanaa role: Directory of grant databases + links to IRS 990 data (who gives to whom).
- Not giving per se — strategic research tool for orgs seeking institutional funding.
- P8 compliance: N/A (Daanaa is not in the flow).
- Risk: Low. Reference only.

---

## Section 3: Legal Posture Audit

### P8 Deep Dive: "Never Handle Funds"

**Current state:**
- Direct donate links: Org's processor (Stripe, PayPal, etc.) or EIN-based router (Facebook, GitHub, PayPal Giving Fund)
- Daanaa role: Display link. No account, no gateway, no money touch.
- Compliance: Audited 2026-07-01 (see COMPLIANCE LOG in STEWARDSHIP.md).

**Proposed methods:**
1. Check by mail: Donor → org (USPS). Daanaa: none. ✅
2. Stocks: Donor's broker → org's brokerage. Daanaa: none. ✅
3. DAF: Donor's DAF sponsor → org (via EIN). Daanaa: none. ✅
4. EIN routers: Third-party platform → org. Daanaa: link. ✅
5. Workplace giving: Employer payroll → org OR platform → org. Daanaa: education. ✅
6. Recurring: Org's existing processor (recurring charge). Daanaa: education. ✅
7. Crypto: Donor wallet → org wallet. Daanaa: none. ✅
8. In-kind: Donor time/goods → org. Daanaa: logging only (no funds). ✅
9. Sponsorships: Foundation/corp grants (not Daanaa). Daanaa: directory only. ✅

**Verdict:** All methods maintain P8. Daanaa is never merchant of record, never processor, never intermediary, never holds funds.

### Tax Compliance Framings

**Board decision point 2:** Should Daanaa add tax disclaimers to help pages?

- **Current:** Some pages mention Section 170(c) or Form 990; none say "not tax advice."
- **Options:**
  - **A)** Every giving method page includes: "Not tax advice. Consult a tax professional." (defensive)
  - **B)** Only Stocks + Crypto pages include disclaimers; others cite IRS guidance (balanced)
  - **C)** No disclaimers; link to IRS.gov only (trusts donor's tax pro) (lean)
- **Recommendation:** **B** — Stocks + Crypto are most complex; others are straightforward ("donate to 501c3, deduct up to AGI limit").

### Section 501(c)(3) Gating

All help pages should reinforce: "All methods below work ONLY with IRS-recognized 501(c)(3) organizations."

**Board decision point 3:** Should Daanaa block giving methods for non-501c3 orgs on Daanaa?

- **Options:**
  - **A)** Hide all giving methods if org isn't verified 501c3 (strict)
  - **B)** Show all methods but add warning banner: "Verify this org's 501c3 status before giving" (educational)
  - **C)** Show methods as-is; users responsible (current state)
- **Recommendation:** **B** — Balances caution with user autonomy. Daanaa's data is audited 2026-07-01; warning is sufficient.

---

## Section 4: Board Decision Points (8)

| # | Decision | Options | Recommendation | Rationale |
|---|----------|---------|-----------------|-----------|
| **1** | Crypto method: endorse or educate neutral? | A: Endorse / B: Neutral education | B | Preserves org autonomy; tax law evolving |
| **2** | Tax disclaimers: where required? | A: All pages / B: Stocks+Crypto only / C: None | B | Proportionate to complexity; other methods simple |
| **3** | 501c3 gating: how strict? | A: Hide if not verified / B: Warning banner / C: No action | B | Educational without friction |
| **4** | Workplace giving: link to platform directory only, or verify participating orgs? | A: Directory link + trust orgs to verify / B: Pre-screen orgs on platforms | A | Platforms manage compliance; Daanaa curates link only |
| **5** | Recurring gifts: surface as UX feature or education-only? | A: Wallet integration (show recurring badges) / B: Help page link only | B | Org processor handles state; Daanaa just informs |
| **6** | In-kind gifts: allow logging in Wallet? | A: Yes (hours, miles, goods value) / B: Help page only (no Wallet logging) | A | Wallet is for personal record; logging hours is low-risk intent capture |
| **7** | Sponsorships/grants: include in "Ways to Give" hub or separate "Funding Opportunities"? | A: Separate "Opportunities" hub / B: Include in Ways to Give / C: Out of scope | A | Different flow (institutional, not donor-giving); deserves own section |
| **8** | Phase rollout: proceed with Phase 1 immediately, or wait for all board approvals? | A: Phase 1 → Phase 2/3 pending feedback / B: All phases ship together / C: Staggered board approvals | A | Phase 1 is low-complexity, low-risk; enables learning before Phase 2 |

---

## Section 5: Effort Estimate (by phase)

**Assumption:** All effort figures assume use of existing pattern from DAF integration (help page template, org detail link, minimal code).

### Phase 1 (Weeks 1-4) — ~12 human-hours + ~2 CC-hours

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| Check by mail help page + copy | 0.5h | Human | Reuse DAF template; add mailing address section |
| Stocks help page + tax framing | 1h | CC + Human | Explain Section 170(e); link to SEC/IRS guidance |
| EIN router directory page | 0.5h | CC | Link to PayPal Giving Fund, Facebook Giving, etc. |
| Org detail integrations (all 3 methods) | 2h | CC | Add secondary links alongside DAF |
| Testing + QA | 1h | QA | Smoke tests; link verification |
| **Phase 1 Total** | **~5h human + ~2h CC** | — | Can ship in 1-2 weeks |

### Phase 2 (Weeks 5-8) — ~12 human-hours + ~3 CC-hours

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| Workplace giving help page | 1h | Human | Explain employer matching + CyberGrants/Benevity/NP Easy |
| Recurring gifts help page | 1h | Human | Link to org's processor; explain auto-renewal |
| Cryptocurrency help page | 2h | Human + CC | Tax treatment; wallet security; fraud warning |
| Org detail links (Phase 2 methods) | 2h | CC | Add toggles for crypto/recurring (org can disable) |
| Wallet UX for recurring badges | 2h | CC | Show "recurring donor" status if org enabled |
| Testing + QA | 1h | QA | Focus on crypto edge cases (wallet addresses, verification) |
| **Phase 2 Total** | **~7h human + ~3h CC** | — | Crypto is most complex; can ship in 3-4 weeks |

### Phase 3 (Weeks 9-12) — ~8 human-hours + ~2 CC-hours

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| In-kind gifts help page | 1h | Human | Logging hours, miles, pro-bono services |
| Wallet UX for in-kind logging | 1.5h | CC | "You've given 10 volunteer hours" card |
| Sponsorships/grants directory page | 1h | CC | Link to Foundation Center, Grants.gov, IRS 990 data |
| Org detail links (Phase 3 methods) | 1h | CC | In-kind logging button + sponsorship resources link |
| Testing + QA | 1h | QA | In-kind privacy (no public sharing without opt-in) |
| **Phase 3 Total** | **~4.5h human + ~2h CC** | — | Can ship in 2-3 weeks |

**GRAND TOTAL:** ~16.5 human-hours + ~7 CC-hours over 12 weeks (1.5h/week human, 0.6h/week CC)

---

## Section 6: Risk Assessment

### Legal Risk: LOW

- All methods respect P8 (Daanaa never touches money)
- No new compliance obligations (referral-based only)
- Tax disclaimers mitigate liability on Stocks + Crypto
- All methods link to official sources (IRS, SEC, platforms)

### Operational Risk: MEDIUM

- Crypto: Tax law evolving; IRS guidance changes. Mitigated by "not tax advice" + links to IRS.gov.
- Workplace giving: Platform APIs may change; mitigated by education-only (no integration).
- Recurring gifts: Org's processor state may diverge from Daanaa display; mitigated by education-only.

### Adoption Risk: LOW

- Users already give via other methods; this educates about all options.
- Orgs may disable some methods (crypto, in-kind); toggle support needed.
- Wallet integration for recurring/in-kind is opt-in (orgs enable, users see).

### Maintenance Risk: MEDIUM (long-term)

- Help pages need annual review (tax law, platform links).
- Org toggles/settings need documentation.
- Wallet UX scaling with more method types.

---

## Section 7: Not in Scope (Explicitly)

❌ **Payment processing:** Daanaa will never be a payment processor or merchant of record.  
❌ **Tax preparation:** Help pages educate; they do not prepare tax forms.  
❌ **Regulatory compliance:** Org is responsible for 501c3 status and tax receipt issuance.  
❌ **Fundraising automation:** Daanaa shows methods; it doesn't automate outreach.  
❌ **Recurring payment processing:** Org's processor (Stripe, etc.) handles recurring logic.  
❌ **Crypto wallet custody:** Users control their wallets; Daanaa never holds keys.  

---

## Section 8: Success Metrics (Post-Launch)

How we measure impact:

1. **Engagement:** % of org pages that enable each giving method (toggle analysis)
2. **Discovery:** Traffic to `/giving-via-*` pages (Plausible dashboard)
3. **Adoption:** Donors logging gifts via each method in Wallet (cohort analysis)
4. **Feedback:** Corrections/questions via /feedback (search for "giving", "donate", etc.)
5. **Org autonomy:** % of orgs that disable crypto/recurring (signals comfort threshold)

**Success threshold:** Each Phase method reaches 3%+ of active orgs enabling it within 4 weeks of launch.

---

## Section 9: Phased Rollout Timeline

```
WEEK 1-2   │ Phase 1 approval + build (checks, stocks, routers)
WEEK 3     │ Phase 1 ship → monitor feedback
WEEK 4-6   │ Phase 2 approval + build (workplace, recurring, crypto)
WEEK 7     │ Phase 2 ship → monitor feedback
WEEK 8-10  │ Phase 3 approval + build (in-kind, sponsorships)
WEEK 11    │ Phase 3 ship → monitor feedback
WEEK 12    │ Retrospective + next iteration planning
```

If board requests changes mid-phase, pause that phase and adjust.

---

## Section 10: Board Recommendation

**Proceed with "Ways to Give" framework:**
1. ✅ Phase 1 (Checks, Stocks, Routers) approved → build immediately
2. ✅ Phase 2 (Workplace, Recurring, Crypto) approved subject to Board Decision Point 1 (crypto)
3. ✅ Phase 3 (In-kind, Sponsorships) approved subject to Board Decision Point 7 (separate hub)
4. ✅ All methods Stewardship-compliant (P1-P11)
5. ✅ All methods respect P8 (Daanaa never handles funds)

**8 board decision points require explicit approval** (see Section 4). Once approved, rollout is low-risk, low-effort, high-impact.

---

## Appendix A: Tax Code References

- **501(c)(3) charitable contributions:** IRC Section 170(c)
- **Appreciated asset deduction:** IRC Section 170(e)(1)(B)(i)
- **Cryptocurrency treatment:** IRC Section 1231 (long-term capital gains)
- **Donor-Advised Funds:** IRC Section 4966
- **Workplace giving:** Employer deduction under IRC Section 162

All help pages link to IRS.gov source + general education only (no personalized tax advice).

---

## Appendix B: Org Toggles (Config)

Each org will have a settings page to enable/disable methods:

```
☑️ Direct donate link (always enabled)
☑️ Donor-Advised Fund
☑️ Check by mail
☑️ Stocks/appreciated assets
☑️ EIN-based routers
☑️ Workplace giving
☑️ Recurring gifts
☑️ Cryptocurrency      [⚠️ requires 501c3 verification]
☑️ In-kind donations
☑️ Sponsorship resources
```

Each org chooses which methods to show on their detail page (all methods available in help pages regardless).

---

**Document prepared by:** Claude Code  
**Date:** 2026-07-26  
**Status:** Awaiting board approval on 8 decision points

**Next step:** Board review → decisions on 8 points → Phase 1 build (starting Week 1)
