# Legal Compliance Matrix
## Board Meeting July 22, 2026

**Purpose:** Map all 15 decisions against federal, state, and international regulatory requirements. Identify compliance gaps and mitigation strategies.

---

## Regulatory Framework Overview

| Regulation | Applies To | Trigger | Your Risk |
|-----------|-----------|---------|-----------|
| **COPPA** (Children's Online Privacy Protection Act) | Services directed to <13 | Any user under 13 | Parental consent required; $43K+ fines per violation |
| **FERPA** (Family Educational Rights and Privacy Act) | Schools + ed records | Receive student data from schools | Must sign Data Use Agreement; access controls required |
| **GDPR** (General Data Protection Regulation) | EU residents' data | Any EU volunteers/donors | Consent, deletion rights; €20M or 4% revenue fine |
| **CCPA** (California Consumer Privacy Act) | California residents' data | Any CA volunteers/donors | Deletion rights, opt-out; $7,500 per violation |
| **State Liability Laws** (varies) | Volunteer liability | Volunteer causes harm | State-specific negligent supervision/placement rules |
| **IRS 7-Year Retention** | Tax/charitable records | Receive donations or are 501(c)(3) | Audit risk if records deleted <7 years |
| **Employment Law** (FLSA) | Student volunteers | <18 volunteers | Minimum age, max hours, hazard restrictions |

---

## Decision-by-Decision Compliance Analysis

### DECISION 1: Student Account Model

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **COPPA** | Parental consent for <13 users (verifiable, not just email) | Parent-dependent or tiered (school-verified) | ✅ Compliant if paired with Decision 12 (verification) |
| **COPPA** | Can't direct service to <13 without parental consent | Student-owned without verification | ❌ NOT COMPLIANT (if open to <13) |
| **FERPA** | Schools can share student records if trust us | Tiered (school-verified) | ✅ Compliant if DUA signed |

**Mitigation:**
- Draft COPPA-compliant Terms of Service (separate for <13 vs 13+)
- If parent-dependent for <13: draft parental consent form + verification process
- If school-tiered: draft FERPA Data Use Agreement

---

### DECISION 2: AI Platform Assistant Timing

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **GDPR** (if EU users) | AI outputs must be explainable + no bias | Post-pilot (after testing) | ✅ Compliant (defer to when model matured) |
| **COPPA** | AI recommendations for <13 need parental consent | Post-pilot | ✅ Compliant (delay reduces risk) |

**Mitigation:** Defer to post-pilot reduces regulatory testing burden in Year 1.

---

### DECISION 3: Fraud Detection Policy

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **GDPR** (automated decision) | Automated decisions need human review + explanation | Tiered (admin review of flags) | ✅ Compliant (human oversight) |
| **COPPA** | No automated exclusion of <13 users | Tiered review (not auto-reject) | ✅ Compliant |

**Mitigation:** Implement admin review queue (don't auto-reject based on scores).

---

### DECISION 4: Geographic Expansion

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **State varying laws** | Volunteer age/hours vary by state | Selective (start Houston) | ✅ Compliant (one state first) |
| **State liability laws** (negligent supervision) | State courts vary on volunteer liability | Selective + liability insurance | ✅ Compliant if insured |

**Mitigation:** Hire local counsel in each new state before expansion.

---

### DECISION 5: Pricing Model

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **IRS UBI** (Unrelated Business Income) | Premium fees to schools/nonprofits = taxable UBI | Freemium | ⚠️ Requires UBI tax analysis (not violation, just taxable) |
| **COPPA** | Can't gate <13 users behind paywall | Freemium (schools pay, students free) | ✅ Compliant |

**Mitigation:** If freemium approved, obtain IRS UBI ruling (tax memo needed).

---

### DECISION 6: Minimum Student Age

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **COPPA** | If open to <13, parental consent non-negotiable | 16+ minimum | ✅ Fully compliant (avoids COPPA) |
| **COPPA** | If open to 13+, parental/school consent required | 13+ with school verification | ✅ Compliant (school = parental proxy) |
| **FLSA** (Federal minimum wage) | 13–14 have hour restrictions; 16+ fewer restrictions | 16+ minimum | ✅ Compliant (max hours/week clear) |

**Mitigation:** If 13+ approved, MUST pair with Decision 1 (parent-dependent or school-verified).

---

### DECISION 7: Volunteer Hour Constraints

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **FLSA** | 13–14 year-olds: max 3h/school day, 8h/non-school day | Moderate (8h/day) | ✅ Compliant (8h applies to 16+, not <14) |
| **State laws (vary)** | Some states limit youth volunteer hours more strictly | Moderate (8h/day) | ⚠️ Must verify per state (state-by-state variation) |

**Mitigation:** Implement hour checks per state; block submissions exceeding state limits.

---

### DECISION 8: Nonprofit Communications

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **FTC endorsement guides** | Testimonials/endorsements must be truthful | Student-centric (authentic stories) | ✅ Compliant if stories are real |
| **Lanham Act** | Can't make false claims about orgs | Student-centric (focus on stories, not rankings) | ✅ Compliant |

**Mitigation:** No false claims in messaging (e.g., don't say "top-rated" without data).

---

### DECISION 9: Donor Profiles

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **GDPR** (if EU) | Separate data for different purposes (work vs. personal giving) | Dual profiles | ✅ Compliant (data minimization) |
| **Tax reporting** (IRS) | Separate receipts for work vs. personal giving | Dual profiles (separate receipts) | ✅ Compliant |

**Mitigation:** Issue separate tax receipts per profile (work profile gets work deduction, personal profile gets personal deduction).

---

### DECISION 10: Revenue Model (Long-Term)

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **IRS UBI** | Non-nonprofit revenue = taxable Unrelated Business Income | Hybrid (separate LLC) | ✅ Compliant (separate entity avoids UBI) |
| **IRS 501(c)(3)** | No private inurement (profit can't go to insiders) | Hybrid (check LLC structure) | ⚠️ Requires formal structure + oversight |
| **State charitable solicitation** | If fundraising for 501(c)(3), register in states | Hybrid (varies by state) | ⚠️ May need multi-state registration |

**Mitigation:**
- If hybrid approved, establish separate LLC (founder owns or 501(c)(3) owns)
- Formal cost allocation between 501(c)(3) and LLC
- IRS determination letter for UBI structure

---

### DECISION 11: Volunteer Liability

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **Negligent supervision** (state law) | Org liable if we negligently place volunteer | Shared liability (we verify volunteers) | ✅ Compliant if verification robust |
| **Negligent placement** (state law) | We liable if we negligently screen/place volunteer | Shared liability + insurance | ✅ Compliant (insured defense) |
| **Insurance** | E&O insurance covers our negligence | Shared liability + E&O required | ✅ Compliant |

**Mitigation:** Robust verification (Decision 12) is critical to negligent placement defense.

---

### DECISION 12: Volunteer Verification

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **COPPA** (if <13 users) | Age verification required for <13 users | School-verified or third-party ID | ✅ Compliant (strong verification) |
| **FERPA** (if school-verified) | Schools can share basic info if trust us | Hybrid (school primary) | ✅ Compliant (must sign DUA) |
| **Background check laws** (vary by state) | Some states have specific requirements for volunteer screening | Hybrid (no background checks, only age/ID) | ✅ Compliant (not a background check requirement) |

**Mitigation:**
- Draft FERPA Data Use Agreement (DUA) for schools
- If third-party ID used, vet vendor (SOC 2, GDPR compliance)
- Define "reasonable verification" standard (meets negligent placement defense)

---

### DECISION 13: Data Retention & Privacy Policy

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **GDPR** (EU residents) | Right to deletion ("right to be forgotten") | 7-year PII deletion + indefinite aggregates | ✅ Compliant (deletion honored) |
| **CCPA** (CA residents) | Right to deletion | 7-year PII deletion | ✅ Compliant |
| **COPPA** (parental rights) | Parents can delete child's data on request | 7-year PII deletion | ✅ Compliant (within 30 days) |
| **IRS** (tax records) | 7-year retention for audit defense | 7-year PII retention | ✅ Compliant (IRS requirements met) |

**Mitigation:**
- Implement automated 7-year deletion (batch purge annually)
- Deletion request process (respond within 30 days per GDPR/CCPA/COPPA)
- Aggregates retained indefinite (no PII = no privacy risk)

---

### DECISION 14: Board Governance & Conflicts of Interest

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **State nonprofit law** | Board must have conflict-of-interest policy | Formal policy + advisory board | ✅ Compliant |
| **IRS Form 990** | Must disclose COI policy (Schedule O) | Formal policy | ✅ Compliant (reportable) |
| **Fiduciary duty** (state law) | Board members must avoid self-dealing | Formal policy + annual disclosures | ✅ Compliant |

**Mitigation:**
- Draft formal Conflict of Interest Policy
- Annual conflict disclosure from all board members
- Automatic recusal on self-interested votes
- Document in Form 990 Schedule O

---

### DECISION 15: Insurance & Risk Management

| Regulation | Requirement | Your Decision | Compliance Status |
|-----------|---|---|---|
| **Negligent liability** (state) | We need E&O insurance if we negligently place/rank | E&O insurance required | ✅ Compliant (insured) |
| **Cyber liability** (GDPR fines) | Data breach can result in $1M+ fines; insurance helps | Cyber insurance Year 2 | ⚠️ Year 1 uninsured; Year 2+ compliant |
| **Directors & Officers** | Board members exposed to personal liability | D&O insurance | ✅ Recommended (not required, but protective) |

**Mitigation:**
- Year 1: General + Professional ($10–15K)
- Year 2: Add Cyber ($15–20K) as data grows
- D&O optional but protective ($10K)

---

## Compliance Gap Analysis

**Red Flags (Stop & Fix):**

| Issue | Decision | Mitigation |
|-------|----------|-----------|
| ❌ COPPA violation (open to <13 without consent) | Decision 1 + 6 | Require parent-dependent or school-verified accounts |
| ❌ FERPA violation (share school data without DUA) | Decision 12 | Sign DUA before accessing school data |
| ❌ GDPR violation (no deletion right) | Decision 13 | Implement 7-year deletion policy |
| ❌ Fiduciary violation (no COI policy) | Decision 14 | Draft formal policy; annual disclosures |
| ❌ Uninsured negligence (no E&O) | Decision 11 + 15 | Get E&O quote; budget $10–15K Year 1 |

**Amber Flags (Mitigate):**

| Issue | Decision | Mitigation |
|-------|----------|-----------|
| ⚠️ UBI tax exposure (freemium revenue) | Decision 5 + 10 | Obtain IRS UBI ruling; separate LLC if B2B |
| ⚠️ State liability variation (expand to new states) | Decision 4 | Hire local counsel; verify volunteer age/hours per state |
| ⚠️ Cyber insurance gap (Year 1 uninsured) | Decision 15 | Defer cyber insurance to Year 2; accept breach risk Y1 |
| ⚠️ Verification standard (meets negligent placement defense) | Decision 12 | Define & document "reasonable verification"; legal approval |

---

## Compliance Checklist (Post-Board Decision)

**Within 7 days:**
- [ ] Legal drafts COPPA Terms of Service (separate <13 vs 13+ versions)
- [ ] Legal drafts FERPA Data Use Agreement (if school verification approved)
- [ ] Finance coordinates IRS UBI ruling (if freemium approved)
- [ ] Finance gets E&O + GL insurance quotes
- [ ] IT Security drafts incident response plan

**Within 30 days:**
- [ ] Data retention policy formalized & published
- [ ] Deletion request process implemented
- [ ] Formal Conflict of Interest Policy drafted
- [ ] Board members sign annual conflict disclosures
- [ ] GDPR/CCPA/COPPA compliance audit (external, if possible)

**Within 60 days:**
- [ ] Insurance policies approved & bound
- [ ] DUAs signed with pilot schools
- [ ] IT Security audit (encryption, backups, access controls)
- [ ] Form 990 Schedule O updated (if COI policy approved)

**Within 6 months:**
- [ ] Penetration testing (external security firm)
- [ ] GDPR Data Processing Agreement (if EU users exist)
- [ ] State-specific volunteer liability law review (if expanding)

---

## Summary: Compliance is Achievable

**Key insight:** None of the 15 decisions create unavoidable compliance violations. All red flags have clear mitigations:

- **COPPA:** Parent-dependent or school-verified accounts
- **FERPA:** Sign DUA, limit data access
- **GDPR/CCPA:** 7-year PII deletion + indefinite aggregates
- **Liability:** Robust verification + insurance

**Cost:** $45–75K Year 1 (IT security, legal review, insurance). Worthwhile for long-term trust + legal safety.

---

**Next step:** Board votes on 15 decisions. Post-vote, legal team executes compliance checklist (above).
