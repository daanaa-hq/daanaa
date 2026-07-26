# Legal Review Handoff: Peer Inference v6

**Date:** 2026-07-26  
**Requestor:** Claude Code (AI Engineering)  
**Feature:** Peer Inference Tier System (T1 Direct + T2 Inferred)  
**Scope:** TOS/Privacy/Liability language for public launch  
**Timeline:** 1–2 weeks review preferred; no hard deadline until Aug 5 (soft launch target)

---

## Summary for Legal Team

**What is Peer Inference v6?**

We show nonprofits' regional peer financial context when they lack recent IRS Form 990 filings. Instead of hiding them ("we're still learning"), we display: "Nonprofits in this group [same type + state + funding model] typically maintain 2.1 months of operating reserves" — based on actual peer 990 data.

**Why it matters:**
- 72% of nonprofits lack recent 990 data (small/grassroots orgs)
- Before: invisible to donors
- After: visible with peer context (labeled as "inferred," not actual)
- Expected impact: +750K orgs with meaningful context (28% → 97% coverage)

**Stewardship safeguards:**
- Evidence-based: only peer medians from actual 990 filings
- Explainable: badge + confidence margins shown to donors
- Fair: small orgs treated with equal dignity as large ones
- Transparent: methodology published, data sources disclosed

---

## Materials for Review

### 1. **Inference Liability Language** (Primary)
**File:** `docs/INFERENCE_LIABILITY_LANGUAGE.md` (500 lines)

**Contains:**
- TOS update language (Tier 2 definition, limitations, what it is NOT)
- Privacy policy update (how we calculate inference, data sources, no sharing)
- In-product disclaimer copy (badge text, tooltip, methodology link)
- Help center FAQ (6 Q&A pairs for donors + nonprofits)
- Liability risk assessment (4 risks, all rated low–medium with mitigations)
- Legal sign-off checklist (5 items to review)

**Key sections to review:**
1. **TOS Tier 2 section** (lines 15–60): Does "inferred context" language accurately describe what's shown?
2. **Privacy update** (lines 61–85): Do we correctly describe data sources + handling?
3. **In-product disclaimers** (lines 90–107): Are disclaimers prominent + clear enough?
4. **Liability matrix** (lines 131–160): Do risks and mitigations align with your counsel's view?

### 2. **Methodology Document** (Reference)
**File:** `docs/METHODOLOGY_V6_INFERENCE.md` (346 lines)

**Use for:**
- Understanding technical soundness (peer group definition, confidence intervals)
- Donor-facing explanation (how inference works, what to do with it)
- Evidence of transparency (full methodology published for scrutiny)

**Key sections:**
- Peer Group Definition (lines 35–48): NTEE2 + state + archetype matching
- Confidence Calculation (lines 61–74): How margins of error are determined
- Validation (lines 194–208): Board review + donor testing results
- Appendix (lines 301–346): Real examples (T1 vs T2 display)

### 3. **Board-Approved Decision Record**
**File:** `DECISIONS.md` (lines 1–100)

**Summarizes:**
- Peer inference approved by Stewardship Board (2026-07-26)
- Alignment with 11 founding principles (P3/P4/P9 primary)
- Risk mitigations + validation approach
- Decision reasoning (why inference instead of alternatives)

---

## Sign-Off Checklist

**Legal review should verify:**

- [ ] **TOS Language**
  - [ ] "Tier 2 (Regional Context — Inferred)" section accurately defines scope
  - [ ] "What this IS NOT" bullets are clear + comprehensive
  - [ ] Limitations (data lag, peer variation, incomplete coverage) are disclosed
  - [ ] No language implies we know org's actual finances (we don't)
  - [ ] Margin of error (±5–15%) is disclosed

- [ ] **Privacy Policy Language**
  - [ ] Data sources are accurately listed (IRS, NCCS, NTEE, state, archetype)
  - [ ] "No personal data is used" is correct (we aggregate, don't expose individuals)
  - [ ] "Your data is never shared with peers" is enforced at code level
  - [ ] Aggregation method (peer medians) is accurately described

- [ ] **In-Product Disclaimers**
  - [ ] Badge text ("Context based on X similar organizations") is non-misleading
  - [ ] Tooltip explains inference basis + confidence level
  - [ ] "Although we don't have revenue data..." copy is fair + honest
  - [ ] Methodology link is present + accessible (daanaa.org/methodology)
  - [ ] Confidence margins (±X%) are shown

- [ ] **Liability & Risk**
  - [ ] Inference is defended as legitimate statistical practice (not prediction)
  - [ ] Confidence intervals mitigate accuracy risk (donors see margins)
  - [ ] Explicit "inferred" labeling mitigates misrepresentation risk
  - [ ] Methodology transparency mitigates bias risk (changes can be audited)
  - [ ] No implied warranty that inferred data predicts org's actual finances

- [ ] **Compliance**
  - [ ] FTC/CAN-SPAM compliance for any related emails (if applicable)
  - [ ] GDPR/CCPA compliance if we have international users (data minimization)
  - [ ] Charitable solicitation laws (inference is not a solicitation, just transparency)
  - [ ] No claims of professional financial assessment (we disclaim this)

---

## Key Language to Lockdown

**Must be in TOS/Privacy:**

```
"Tier 2 (Regional Context — Inferred) displays statistical inferred context 
based on peer organizations, NOT actual financial data from this organization. 
This organization has not provided or verified this data.

Inferred context should not be the sole basis for funding decisions. 
We recommend contacting the organization directly to verify financial practices."
```

**Must be in product UI (before any T2 reserves number):**

```
"ⓘ Although we don't have revenue data for this organization, nonprofits in 
this group typically carry [X] months of operating reserves.

Data source: Similar organizations in this region and category | Confidence: [Good ±10%]"
```

**Must be in privacy policy:**

```
"Inference does not include personal data. We analyze only:
- IRS Form 990 public data (aggregated medians)
- NCCS publicly available governance data
- NTEE nonprofit category codes (public classification)
- State location (public)
- Archetype classification (derived from public data only)

Organizations do not see each other's names or identifying information 
— only aggregate median statistics."
```

---

## Risk Assessment (Pre-Litigation Privilege)

| Risk | Scenario | Severity | Mitigation |
|------|----------|----------|-----------|
| **Misrepresentation** | Donor thinks T2 is org's actual data | Medium | Explicit "inferred" badge + disclaimer before reserves number |
| **Undisclosed Bias** | Peer groups have systematic bias (e.g., underrepresent rural orgs) | Medium | Documented methodology, confidence intervals, peer group definition shown to donors |
| **Accuracy Challenge** | T2 org later claims inference was "way off" | Low | Confidence margins disclosed (±5–15%), methodology published, no implied warranty |
| **Competitive Challenge** | Competitor claims unfair comparison of tiers | Low | All peer groups algorithmic (no human curation), methodology objective + reproducible |

**Overall Risk Level:** Low (assuming TOS/Privacy language in place)

---

## Questions for Legal

1. **Confidence Margin Disclosure:** Must we show ±5–15% on every T2 reserve number, or can we link to methodology?
   - *Current approach:* Show on hover tooltip + methodology link
   - *Question:* Sufficient or needs to be prominent on page?

2. **"Inferred" Terminology:** Is "inferred from peer data" legally distinct from "predicted" or "estimated"?
   - *Current approach:* Use "inferred" + "peer median," explicitly avoid "predict" or "model"
   - *Question:* OK for TOS/marketing language?

3. **Nonprofit Rights:** Can we show T2 context for a nonprofit without their permission to collect/display peer group composition?
   - *Current approach:* Peer groups are algorithmic; nonprofit doesn't need to consent to be in a peer group, only to display their own data
   - *Question:* Any consent/notification requirements?

4. **Failure Scenarios:** If a T2 org later files actual 990 + it's very different from peer median, do we have liability?
   - *Current approach:* Confidence margins + "starting point" framing shield us
   - *Question:* Sufficient, or need additional language?

5. **Charitable Solicitation:** Does Tier 2 inference count as "solicitation" under state charitable fundraising laws?
   - *Current approach:* No — we're transparency, not a solicitation vehicle (donors initiate, we don't ask)
   - *Question:* Any states where inference + "donate link" proximity triggers registration?

---

## Approval Process

**Step 1 (You):** Review this checklist + the 3 materials above  
**Step 2 (Counsel):** Flag any language needing changes  
**Step 3 (We iterate):** Refine TOS/Privacy language based on feedback  
**Step 4 (Final sign-off):** Legal approves final language  
**Step 5 (Publish):** Update live TOS/Privacy + deploy v6 publicly

**Timeline Goal:** 1–2 weeks for steps 1–4; step 5 happens after UX testing passes (2026-08-01)

---

## Escalation

If legal identifies a deal-breaker concern:
1. Flag it here with specific language/section reference
2. We prioritize a fix or adjustment
3. Not expected to block the feature; inference is sound practice + well-disclosed

**Questions?** ping claude@daanaa.org (or use your preferred contact method)

---

## Appendix: What We're NOT Doing

To scope legal review, here's what we **explicitly avoided:**

- ❌ Predicting org's actual finances (we show peer medians)
- ❌ Ranking orgs by financial health (we show peer context, not a verdict)
- ❌ Collecting org-specific data without consent (we use public 990 data only)
- ❌ Soliciting donations (we link to org's own donate page)
- ❌ Handling funds (Daanaa is a discovery layer, not a payment processor)
- ❌ Profiling donors based on peer context (we show stats, not individual tracking)

These explicit non-goals reduce regulatory surface area significantly.
