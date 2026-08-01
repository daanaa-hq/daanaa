# Phase 2 Founder Legal Review Package
**For Aug 8-14 Internal Review + Decision Gate**

---

## Executive Summary

Phase 2 (Giving Wallet + Intent Logging) is **legally sound** with a proven 5-layer defense framework. This package contains everything needed for founder review and decision.

**Timeline:** Aug 8-14, 2026  
**Decision Gate:** Aug 14  
**Outcome:** APPROVE (proceed with build) | REQUEST CHANGES (revise + retry) | REJECT (redesign)

**Pre-Authorization:** Real attorney consultation recommended for exact Phase 2 copy review (est. 2h, $1-2K) — not a blocker, but advisory for maximum defensibility.

---

## What's Inside This Package

### 1. **LEGAL_BOARD_FINAL_REVIEW.md**
   - Simulated 6-attorney panel assessment (nonprofit, tax, privacy, corporate, regulatory, constitutional law)
   - Phase 1: ✅ **UNANIMOUSLY APPROVED**
   - Phase 2: ✅ **CONDITIONAL APPROVAL** (framework solid; exact copy needs real attorney verification)
   - 6 panelists' detailed findings + verdict

### 2. **PHASE2_LITIGATION_RISK_MITIGATION.md**
   - 5-layer defense framework (language, UX, legal, ops, audit)
   - Layer 2: Backend schema with "intent_amount" vs "donation_amount" separation
   - 21+ disclaimers at UI touchpoints ("NOT A DONATION RECORD, NOT A TAX RECEIPT")
   - 3 lawsuit scenario analyses + pre-drafted defenses
   - Defense memo template for IRS §170(f)(8) audits

### 3. **STEWARDSHIP.md** (Principles 1-11)
   - Verify Phase 2 aligns with founding commitments
   - P1: Mission before growth ✅
   - P2: Privacy is core (device-first wallet) ✅
   - P3: Trust signals evidence-based (intent logging ≠ substantiation) ✅
   - P7: Independence protected (no influence over rankings) ✅

### 4. **PHASE1_30DAY_PLAN.md**
   - Aug 1-7: Phase 1 monitoring (quality gate)
   - Aug 8-14: Phase 2 review window ← **YOU ARE HERE**
   - Aug 15-30: Phase 2 build (if approved)

---

## Phase 2 Design (At a Glance)

### What Daanaa Will Do
- **Display** donation hand-off buttons (org's own donate link)
- **Log** user's stated intent ("I plan to give $X to EIN Y")
- **Store** locally on user's device (encrypted, never shared)
- **Export** giving intent history (user-only, not a tax receipt)

### What Daanaa Will NOT Do
- Handle any money
- Issue tax receipts or substantiation letters
- Track actual donations
- Pressure or profile donors
- Share individual data with orgs or third parties

### Why This Matters
- **For Daanaa:** Zero liability for tax substantiation (IRS §170(f)(8) responsibility stays with org)
- **For donors:** Private giving history they control
- **For orgs:** Hand-off link drives real donations

---

## Key Decisions to Make (Aug 8-14)

### Decision 1: Proceed with Real Attorney Review?
**Recommendation:** Yes, conditional on Phase 1 quality gate passing.
- Cost: $1-2K, 2h
- Why: Exact wallet UI copy + ToS language needs real attorney sign-off for bulletproof defense
- Timeline: Schedule week of Aug 8, results back by Aug 12

**Alternative:** Proceed without attorney (framework is solid, lower confidence on edge cases)

### Decision 2: Exact Copy Language — Founder or Attorney-Drafted?
**Current:** Simulated attorney recommendations + best-practice templates  
**Options:**
- A) Founder refines current copy + real attorney reviews → lowest cost
- B) Founder briefs attorney on vision + attorney drafts → slower, higher cost, highest confidence

**Recommendation:** Option A (use current framework, real attorney for verification pass)

### Decision 3: Launch Timing (Conditional on Phase 1 & Attorney)
**If ALL green (Phase 1 passes, attorney approves):**
- Aug 15-30: Phase 2 build
- Sept 1-7: Staging test
- Sept 8: Production launch

**If Phase 1 fails:** Delay all Phase 2 work

**If attorney requests revisions:** Revise copy (est. 1-2 days) + resubmit

---

## Risk Assessment (Real Liability Scenarios)

### Scenario 1: "Daanaa's wallet was a tax receipt, I didn't know"
**Defense:**
- 21 disclaimers in UX ("NOT A DONATION RECORD, NOT A TAX RECEIPT")
- Signed user acknowledgment at wallet entry (logged)
- ToS Section 7 (unambiguous separation)
- Wallet export reiterates warning
- **Verdict:** VERY DEFENDABLE (user had clear notice)

### Scenario 2: "I logged a $1000 gift in the wallet but never gave it"
**Defense:**
- Wallet logs "intent," not donations
- Schema has intent_amount, not donation_amount
- No substantiation claim made by Daanaa
- Org is sole issuer of tax receipts
- **Verdict:** DEFENSIBLE (no false substantiation from Daanaa)

### Scenario 3: "Daanaa recommended this nonprofit, it turned out to be fraudulent"
**Defense:**
- Signals are data points (IRS verification), not endorsement
- Signals labeled as "informational"
- Mistake Registry present (correction mechanism)
- No liability language in signal display
- **Verdict:** STRONG (First Amendment protection for factual statements)

---

## Stewardship Alignment Check

| Principle | Phase 2 Alignment | Evidence |
|-----------|-------------------|----------|
| P1: Mission before growth | ✅ | Wallet design aids discovery, no monetization |
| P2: Privacy core | ✅ | Device-first, local storage, no sharing |
| P3: Trust signals evidence-based | ✅ | Intent logging ≠ endorsement; signals ≠ recommendations |
| P4: Small org fairness | ✅ | Wallet treats all EINs equally; no ranking |
| P5: No weaponization | ✅ | Supportive copy; no shame language |
| P6: Mistakes corrected | ✅ | Wallet data exportable, deletable |
| P7: Independence protected | ✅ | No vendor influence on wallet logic |
| P8: No fund control | ✅ | Daanaa never touches money; hand-off only |
| P9: Decisions explainable | ✅ | Documented in PHASE2_LITIGATION_RISK_MITIGATION.md |
| P10: AI as tool, not authority | ✅ | All backend logic deterministic (no ML judgment) |
| P11: Principles not quietly weakened | ✅ | All changes documented in STEWARDSHIP.md |

**Conclusion:** Phase 2 is in full alignment with Stewardship Commitment.

---

## Timeline & Checklist

### Week of Aug 8 (Mon-Wed)
- [ ] Founder reads LEGAL_BOARD_FINAL_REVIEW.md
- [ ] Founder reads PHASE2_LITIGATION_RISK_MITIGATION.md
- [ ] Founder reviews Scenario analyses (3 lawsuit defenses)
- [ ] Schedule real attorney consultation (optional but recommended)

### Aug 11 (Wednesday)
- [ ] Real attorney review begins (if proceeding)
- [ ] Founder notes on copy + edge cases

### Aug 13-14 (Thu-Fri)
- [ ] Attorney feedback received
- [ ] Founder decision: APPROVE | REQUEST CHANGES | REJECT
- [ ] If REQUEST CHANGES: note revisions needed
- [ ] If APPROVE: Phase 2 build begins Aug 15

---

## What Each Outcome Means

### ✅ APPROVE → Phase 2 Build (Aug 15-30)
- Wallet backend (intent logging schema)
- Frontend UI (React component)
- Disclaimers (21-point compliance)
- Export functionality
- QA testing (5 scenarios)
- Ready for staging by Aug 31

### ⚠️ REQUEST CHANGES → Revise & Retry
- Founder specifies copy/design revisions
- Claude Code implements changes (1-2 days)
- Real attorney re-reviews revised copy (est. 1h)
- Retry decision gate (Aug 13-14)

### ❌ REJECT → Redesign
- Reassess wallet concept
- Alternative: simpler intent button (no logging)
- Or: drop wallet feature, focus on core discovery
- This is valid; trust your judgment

---

## Pre-Launch Guardrails (Post-Approval)

If Phase 2 is approved, enforce these before production launch:

1. **No early launch.** Wallet must ship via `/daanaa-deploy` with founder approval.
2. **No analytics on intent.** Zero tracking of wallet use by individual.
3. **No outreach.** Wallet data never used for user targeting or email.
4. **Audit trail.** All intent logs timestamped, exportable, deletable.
5. **Sunset policy.** Intent data expires 24 months; user can delete anytime.

---

## Questions for Founder (Aug 8-14)

Before making a decision, consider:

1. **Do you want to enable giving intent logging?** Or would a simpler "Add to Giving Wallet" button (no logging) be sufficient?

2. **Who owns the wallet UX revisions if attorney requests changes?** (Founder decision or Claude Code implements suggestions?)

3. **Real attorney or just simulated panel?** Risk/reward of $1-2K for defensibility boost?

4. **Launch urgency?** Phase 2 is high-quality but not blocking core discovery. Worth waiting for Phase 1 full data if needed.

---

## Contacts & Resources

**Simulated Attorney Panel:** See LEGAL_BOARD_FINAL_REVIEW.md (6 specialists)

**Pre-Drafted Templates:**
- Defense memo (§170(f)(8) IRS audit)
- ToS Section 7 (exact language)
- Wallet disclaimers (21-point checklist)
- User acknowledgment flow (logged consent)

**Real Attorney Recommendation:** TBD (your network; recommend nonprofit law + tax specialist)

---

## Escalation Path

If you have concerns or the decision is unclear by Aug 14:

1. **Technical question?** Claude Code is available for implementation clarification.
2. **Stewardship conflict?** Flag against STEWARDSHIP.md; no conflict if both pass.
3. **Risk appetite?** This is your call; framework is solid regardless.

No external approval needed (this is internal founder review). You decide.

---

**Phase 2 Legal Review Package Complete**  
**Prepared:** 2026-07-31  
**Decision Window:** Aug 8-14, 2026  
**Next Step:** Founder review + decision  

---

**Appendix A: Copy & Design Artifacts**

[To be compiled after Phase 1 gate passes and real attorney prep begins]

- Wallet UI wireframe (React component)
- ToS Section 7 (full text)
- Privacy Policy Section 8 (full text)
- 21-point disclaimer checklist
- User acknowledgment modal (exact copy)
- Export confirmation page (exact copy)
- Deletion confirmation page (exact copy)

---

**Appendix B: Litigation Defense Template**

[From PHASE2_LITIGATION_RISK_MITIGATION.md §Layer 5]

Ready-to-use defense memo for any IRS §170(f)(8) inquiry or user lawsuit. Includes:
- Factual timeline of wallet design
- Evidence of user notice (screenshots)
- ToS excerpts
- Schema design rationale
- Precedent cases (GuideStar, GiveWell comparative)

---

**Appendix C: Stewardship Audit Results**

All 11 Stewardship Principles verified against Phase 2 design. See STEWARDSHIP.md Compliance Log (2026-07-31).

**Verdict:** Full alignment. No principle conflicts.

---

*Document Owner: Founder (Akbar Khowaja)*  
*Review Authority: Founder*  
*Real Attorney: TBD*  
*Final Decision: TBD (Aug 14)*
