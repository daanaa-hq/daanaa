# Legal Counsel Primer
## Board Meeting July 22, 2026

**Your Role:** Compliance review, risk mitigation, and legal approval for all decisions.

**Time to read:** 5 minutes | **Decisions:** 5 key (11–15) + 2 adjacent (1, 6, 12)

---

## Critical Compliance Surfaces

### Decision 1: Student Account Model ⚠️ **LEGAL REVIEW REQUIRED**

**Question:** Parent-dependent, student-owned, or tiered by age?

**Your compliance angle:** COPPA (Children's Online Privacy Protection Act) is your primary concern.

| Model | Age <13 | Age 13–18 | Compliance Risk |
|-------|---|---|---|
| **Parent-dependent** | ✅ Fully compliant | ⚠️ Over-protective | Low |
| **Student-owned** | ❌ COPPA violation | ✅ Compliant | High (if open to <13) |
| **Tiered (school verification)** | ✅ COPPA-safe via school | ✅ Compliant | Low |

**COPPA Deep Dive:**
- COPPA applies to any online service directed to children <13 or knowingly collecting data from <13.
- **Parent-dependent account:** Parents provide consent on behalf of child. We collect parent email + verification. FTC-safe.
- **Student-owned account:** If we open to <13, we MUST get verifiable parental consent (not just parent email; they need to affirmatively authorize). Complex and expensive.
- **Tiered (school verification):** Schools verify students (they're in FERPA compliance already). We trust school verification as proxy for parental awareness. COPPA-safe.

**Recommendation:** Tiered by age OR Parent-dependent (ages <13). Both COPPA-compliant. School verification (Decision 12, Option B) strengthens both models.

**Action items for legal:**
- [ ] Draft COPPA-compliant Terms of Service (separate for <13 vs 13+)
- [ ] If parent-dependent, draft parental consent form
- [ ] If school-tiered, draft school partnership agreement with FERPA acknowledgment

---

### Decision 6: Minimum Student Age ⚠️ **LEGAL REVIEW REQUIRED**

**Question:** 13+, 16+, or 18+ minimum age?

**Your compliance angle:** COPPA, labor law, and volunteer liability.

| Age | COPPA Compliance | Labor Law Risk | Liability Risk | Recommendation |
|-----|---|---|---|---|
| **13+** | Only if parent-dependent or school-verified | Lower (13+ can legally volunteer) | Medium | ✅ If account model is parent-dependent or school-tiered |
| **16+** | ✅ Automatic COPPA-safe | Lower (most labor-law exempt age) | Low | ✅ Safest overall |
| **18+** | ✅ Automatic COPPA-safe | ✅ None (adult) | Very Low | ✅ Safest but limits adoption |

**Legal deep dive:**
- COPPA: 13+ is the magic number. If we allow <13, parental consent is non-negotiable.
- Labor law: 13–14 year-olds have limited volunteer hours (generally 3h/school day, 8h/non-school day per state). 16+ has fewer restrictions. 18+ = no restrictions.
- Liability: Younger volunteers = higher duty of care. 16+ is a "sweet spot" in many state courts (youth but not child).

**Recommendation:** 16+ minimum age. Balances COPPA safety, labor law compliance, and liability. If board wants 13+, **MUST pair with parent-dependent accounts and school verification (Decision 12, Option B).**

---

### Decision 11: Volunteer Liability Structure ⚠️ **VOTE NEEDED + INSURANCE REQUIREMENT**

**Question:** Who is liable if volunteer causes damage? Nonprofit, Daanaa, or shared?

**Your compliance angle:** Negligent supervision, negligent placement, and volunteer liability law (varies by state).

| Option | Daanaa Liability Exposure | Legal Risk | Insurance Requirement |
|--------|---|---|---|
| **Nonprofit bears all** | Medium (negligent placement claim) | If we negligently matched volunteer to org, we could be sued | Optional, but risky |
| **Shared liability** | Low (insured) | Fair split, defendable in court | ✅ Required: E&O insurance |
| **Daanaa assumes** | Very High (all claims) | We're the deep pocket; every claim hits us | ✅ Required: High-limit GL + E&O |

**Negligent Placement Doctrine:**
- If we place a volunteer at an org, and that volunteer causes harm, the org may claim we negligently screened/placed them.
- Example: We place an unverified volunteer (who turns out to be a registered sex offender) at a youth org. Org sues us for negligent placement.
- Defense: "We verified the volunteer's age, identity, and background." (Requires Decision 12: Verification)

**Recommendation:** Option B (Shared liability) + robust verification (Decision 12). Pair with E&O insurance ($20–30K/year).

**Action items for legal:**
- [ ] Draft volunteer liability waiver (org indemnifies Daanaa, Daanaa's insurer covers org)
- [ ] Clarify verification standards (what counts as "reasonable" verification per state law)
- [ ] Review and coordinate with insurance broker on coverage terms

---

### Decision 12: Volunteer Verification ⚠️ **VOTE NEEDED**

**Question:** Self-attestation, school-mediated, third-party ID, or hybrid?

**Your compliance angle:** COPPA, negligent placement defense, and FERPA (if schools involved).

| Option | COPPA Compliant | Negligent Placement Defense | FERPA Risk | Recommendation |
|--------|---|---|---|---|
| **Self-attestation** | ❌ Only if parent-dependent (13+) | ❌ Weak (we didn't verify) | N/A | ❌ Risky |
| **School-mediated** | ✅ COPPA-safe (school verifies) | ✅ Strong (school verified) | ⚠️ Careful access (FERPA-compliant) | ✅ Recommended |
| **Third-party ID** | ✅ Compliant | ✅ Strong (ID verified) | N/A | ⚠️ Privacy risk (Decision 2: P2) |
| **Hybrid** | ✅ Compliant | ✅ Strong | ⚠️ Same as school-mediated | ✅ Recommended |

**FERPA Deep Dive (if school-mediated):**
- FERPA (Family Educational Rights and Privacy Act) restricts how schools can share student data.
- If we receive student data from schools (even just "Jane is a 15yo student"), we become a "school official" under FERPA.
- **We must sign a Data Use Agreement (DUA) with the school.** DUA limits what we do with that data (can't share with third parties, must delete on graduation, etc.).

**Recommendation:** Option D (Hybrid: school primary, third-party fallback). Pair with:
- School Data Use Agreement (DUA) per FERPA
- No PII beyond age + email (minimizes data collection per Stewardship P2)
- Third-party verification only for non-school students (fall-back, not primary path)

**Action items for legal:**
- [ ] Draft FERPA-compliant Data Use Agreement (DUA) for schools
- [ ] Define "reasonable verification" standard (meets negligent placement defense bar)
- [ ] If third-party ID used, review privacy terms of verification vendor (Socure, Mitek, etc.)

---

### Decision 13: Data Retention & Privacy Policy ⚠️ **VOTE NEEDED**

**Question:** Permanent, 7-year, 1-year, or hybrid PII + aggregates?

**Your compliance angle:** GDPR, CCPA, COPPA right-to-deletion, and IRS record retention.

| Option | GDPR | CCPA | COPPA | IRS 7-Yr | Recommendation |
|--------|---|---|---|---|---|
| **Permanent** | ❌ Violates (no deletion right) | ❌ Violates (no deletion right) | ❌ Violates (parental deletion) | ✅ OK | ❌ Non-compliant |
| **7-Year** | ✅ Compliant (deletion honored) | ✅ Compliant (deletion honored) | ✅ Compliant (parental deletion) | ✅ OK | ✅ Recommended |
| **1-Year** | ✅ Compliant | ✅ Compliant | ✅ Compliant | ❌ Risky (IRS audit) | ⚠️ Compliant but risky for audits |
| **Hybrid (PII 7yr, agg ∞)** | ✅ Compliant | ✅ Compliant | ✅ Compliant | ✅ OK | ✅ Best option |

**Regulatory Deep Dive:**

**GDPR (applies if EU users):**
- Users (volunteers, donors) have right to deletion ("right to be forgotten").
- We must delete within 30 days of request.
- Exception: If legally required (tax records, audit holds), we can retain.
- Implication: Permanent storage violates GDPR.

**CCPA (California):**
- California consumers have right to deletion.
- Same as GDPR, with limited exceptions.

**COPPA (US under-13):**
- Parents have right to review and delete their child's data.
- We must delete within 30 days of parental request.
- Implication: Permanent storage violates COPPA.

**IRS (US tax law):**
- IRS requires 7-year record retention for substantiation (nonprofit must be able to prove what donations were made).
- Deleting before 7 years opens audit risk.

**Recommendation:** Option D (Hybrid). PII deleted after 7 years (GDPR/CCPA/COPPA/IRS-compliant). Aggregate data (totals, not PII) retained indefinite (no legal downside, enables research).

**Action items for legal:**
- [ ] Draft data retention policy (7-year PII, indefinite aggregates)
- [ ] Draft deletion request process (respond within 30 days per GDPR/CCPA/COPPA)
- [ ] Plan for automated deletion (scheduled purge every 7 years)
- [ ] If EU users, draft GDPR Data Processing Agreement (DPA) with Privacy Policy

---

### Decision 14: Board Governance & Conflicts of Interest ⚠️ **VOTE NEEDED**

**Question:** Trust-based, formal conflict policy, independence firewall, or hybrid?

**Your compliance angle:** Nonprofit law, board fiduciary duty, and conflict-of-interest liability.

| Option | Board Fiduciary Duty | Conflict Liability | IRS Form 990 | Recommendation |
|--------|---|---|---|---|
| **Trust-based** | ⚠️ Informal (risky) | ⚠️ High (no policy) | ⚠️ Flagged by IRS | ❌ Not recommended |
| **Formal policy** | ✅ Documented (safe) | ✅ Low (policy in place) | ✅ Approved | ✅ Recommended |
| **Independence firewall** | ✅ Strictest | ✅ Lowest | ✅ Strongest | ✅ Recommended if corporate members |
| **Hybrid (policy + advisory)** | ✅ Documented + flexibility | ✅ Low | ✅ Approved | ✅ Recommended |

**Nonprofit Law Deep Dive:**
- **Fiduciary duty:** Board members owe duty of care, loyalty, and obedience to the nonprofit.
- **Loyalty duty:** Board members must avoid self-dealing and conflicts.
- **Form 990 disclosure:** IRS requires nonprofits to disclose they have a conflict-of-interest policy. If they don't, IRS flags it.
- **Corporate board members:** If we have corporate board members (e.g., from a CSR team), they may have conflicting loyalty to their employer. Formal conflict policy mitigates risk.

**Recommendation:** Formal conflict policy + advisory board (if corporate partners). Policy should:
- Require annual conflict disclosure
- Automatic recusal on self-interested votes
- Board veto power on corporate partnerships
- Clear separation between nonprofit mission and corporate revenue

**Action items for legal:**
- [ ] Draft formal Conflict of Interest Policy (if not already in place)
- [ ] Add to next Form 990 Schedule O ("nonprofit has COI policy")
- [ ] If corporate advisory board, draft charter with no-vote provision
- [ ] Annual conflict disclosure process (each board member signs annually)

---

### Decision 15: Insurance & Risk Management ⚠️ **VOTE NEEDED**

**Question:** Bare minimum, moderate, comprehensive, or progressive coverage?

**Your compliance angle:** Legal exposure and insurable risks.

| Risk | Coverage | Insurable | Notes |
|------|---|---|---|
| Volunteer causes injury at org | GL (General Liability) | ✅ Yes | $1M recommended |
| We rank org, ranking causes financial harm | E&O (Errors & Omissions) | ✅ Yes | $1M recommended |
| Data breach (volunteer emails, birth dates) | Cyber | ✅ Yes | $1M recommended |
| Board member sued personally | D&O (Directors & Officers) | ✅ Yes | $1M recommended |
| Employment lawsuit (discrimination) | EPLI | ✅ Yes | $250–500K recommended |

**Recommendation:** Progressive (Year 1: GL + E&O, Year 2: add Cyber + D&O).

**Action items for legal:**
- [ ] Get insurance quotes for GL, E&O, Cyber, D&O
- [ ] Review policy exclusions (what's NOT covered?)
- [ ] Coordinate with Finance on premium vs. deductible trade-offs
- [ ] Add insurance requirement to liability decision (Decision 11)

---

## Legal Red Flags (Stop and Escalate)

**If any board member says:**
- "We'll verify volunteers with Facebook" → FERPA risk (if schools involved), weak negligent placement defense
- "Permanent data retention is fine" → GDPR/CCPA/COPPA violations
- "We'll keep raising funds indefinitely" → May need UBI analysis (Decision 10)
- "Let's not bother with a conflict policy" → IRS Form 990 flag, fiduciary risk

---

## Questions to Raise in Meeting

1. **Account model (Decision 1):**
   - "If we open to <13 without parents, are we getting verifiable parental consent or just parent email?"

2. **Minimum age (Decision 6):**
   - "If 13+, do we REQUIRE school verification (per COPPA)?"

3. **Verification (Decision 12):**
   - "If using schools, do we have DUA templates ready?"
   - "What counts as 'reasonable' verification to defend negligent placement?"

4. **Data retention (Decision 13):**
   - "Do we have any government grants requiring longer than 7-year retention?"
   - "Are we subject to GDPR (EU users)?"

5. **Board governance (Decision 14):**
   - "Do we have a formal COI policy? Is it in Form 990?"
   - "If corporate board members, how do we firewall their corporate interests?"

6. **Insurance (Decision 15):**
   - "What's our volunteer volume projection? (affects GL premium)"
   - "Do we need cyber insurance in Year 1 or can we defer to Year 2?"

---

## Post-Meeting Actions for You

- [ ] Draft or update Terms of Service (COPPA, FERPA, GDPR, CCPA-compliant)
- [ ] Draft Conflict of Interest Policy (if not in place)
- [ ] Coordinate with Finance/Founder on insurance quotes
- [ ] Draft Data Use Agreement (DUA) for schools (if Decision 12 approved)
- [ ] Create data deletion process (annual purge after 7 years)
- [ ] Update Form 990 Schedule O with COI policy disclosure

---

**Who to contact before meeting:** Founder (for current state of privacy/COPPA compliance), Finance (for insurance budget)

**Meeting prep:** Bring GDPR/CCPA/COPPA summaries, sample DUAs, and insurance broker contacts.
