# G1 — Attorney Prep Packet

**Three critical questions + one future-opportunity advisory** to arm your attorney with context before the engagement. Goal: confirm & advise, not educate. Cuts the bill.

**For engagement:** "We have three specific questions blocking our current roadmap (G2 giving paths, G3 services), plus an optional advisory on a future opportunity. These memos provide the operational context so we can spend your time on legal review rather than background."

**Target ask to attorney:** 3–4 hours for critical questions, bundled rate, ~$500–1,200. (Optional Memo 2 advisory adds 30–45 min if you want future guidance.)

---

## Memo 1: Charitable Solicitation State Registration

**Question:** Do our "Give here" CTAs (donate links on org pages, Giving Wallet feature, monthly campaigns) require registration as a charitable solicitor in each state?

### Background

**Daanaa's giving posture:** We do not process donations, hold funds, or touch money. We operate a yellow-pages directory. When a user decides to give:

1. They see the organization's page on daanaa.org
2. They click a verified "Donate" link (points to the org's own site or an EIN-based router like Every.org or GiveWP)
3. The organization's own payment processor or the router collects the gift
4. Daanaa receives $0 from the transaction

**Current features:**
- Organization pages include verified donation links
- Users can bookmark organizations in a device-local "Giving Wallet" (private, encrypted, not synced to Daanaa)
- Monthly newsletters highlight featured organizations + include "explore" CTAs (not hard donation solicitations)

**Planned features (G2+):**
- Partnership with Every.org (they are the processor; we refer traffic)
- Fallback EIN-based giving router (org chooses to use it; we don't control the processor)
- No transaction processing on Daanaa's part

### Legal Gray Area

**Question for attorney:**
1. Do "Give here" CTAs on a directory page constitute charitable solicitation under state definitions?
2. Does the Giving Wallet (device-local bookmarks, non-synced) constitute solicitation data collection?
3. If we integrate Every.org (as a referral partner, not processor), does that trigger registration in states where Every.org operates?
4. What disclaimer language on our site + org pages mitigates registration triggers?
5. Do 50-state registrations become necessary, or can we operate under a "directory service, not solicitor" exemption?

### Why This Matters

- **If registration required:** $500–$2,000 per state setup; $50–$200/state annual fees; 50-state compliance liability
- **If directory exemption applies:** We operate as a search tool, not a solicitor; no state registration needed
- **If Every.org partnership is clean:** Referral traffic is legal; no processor liability

**Likely outcome:** Directory service exemption + clear disclaimers (tested with attorney) = no state registration required. But must confirm.

---

## Memo 2 (OPTIONAL ADVISORY): Donation Letter Service — Future Opportunity

**Question:** Can Daanaa legally generate §170(f)(8) donation acknowledgment letters AS the organization's agent? What authorization does the claiming org need to grant us?

**Status:** NOT on current roadmap. Deferred post-legal, potential paid service for small nonprofits (G3+). We want your preliminary guidance on whether this is even legally feasible before we consider building it.

### Background

**Current model (planned G3 feature):**
- Nonprofit claims their profile on daanaa.org (email verification + governance check)
- They authorize Daanaa to act as their acknowledgment agent
- Donor gives via Every.org or verified donate link
- Daanaa receives an event: `{org_ein, gift_date, gift_amount, donor_email}`
- Daanaa generates a letter with:
  - Org's name, EIN, address (their official data)
  - Donor's name + gift amount + date
  - IRS-compliant no-goods-or-services clause
  - Org's signature block (facsimile or digital signature)

**Letter content (IRS §170(f)(8) requirements):**
- Acknowledgment of a gift
- Whether goods or services were received (in our case: always "none received")
- Description and value of any goods/services (in our case: "$0")
- Contemporaneous written acknowledgment (issued within reasonable time)

**Why this matters:** Nonprofits often lack staff to issue timely acknowledgments. If they fail, donors can't deduct. Letter automation removes a pain point and drives org adoption.

### Legal Gray Area

**Questions for attorney:**
1. Can Daanaa legally act as the org's acknowledgment agent under §170(f)(8)?
2. What authorization language must the claiming organization sign?
3. Can we use a digital signature (e.g., org's PDF signature) or do we need original ink?
4. Are there state-specific acknowledgment requirements that override §170(f)(8)?
5. If we issue the letter, can the organization later dispute it? Who bears liability?
6. Can we store gift data (donor email, amount, date) on our server, or must it pass through?

### Likely Outcome

- **Authorization:** Organization signs a "Letter Service Agreement" authorizing Daanaa as acknowledgment agent
- **Liability:** Organization remains liable; Daanaa issues on their behalf (standard agency relationship)
- **Data:** Daanaa stores gift events (limited PII) on encrypted server; org can audit/correct
- **Signature:** Digital signature acceptable; org provides template, we apply consistently

**Next step:** Attorney drafts the Letter Service Agreement language.

---

## Memo 3: Entity Structure for Grant Funding & Independence

**Question:** Fiscal sponsorship vs. own nonprofit vs. LLC-only — what structure maximizes grant funding + preserves founder independence?

### Current Situation

**As of June 2026:**
- Daanaa operates as EcoMargins LLC (single-member LLC, Akbar is owner)
- No 501(c)(3) yet (formation in progress or pending fiscal sponsor agreement)
- Seeking $500K–$1M in grant funding over 12 months
- Goal: remain founder-controlled and mission-driven long-term

### Fiscal Sponsorship Model (Likely Winner)

**Structure:** Daanaa (LLC) operates under a fiscal sponsor's 501(c)(3) umbrella (e.g., TECHSoup, Tides Foundation, local community foundation).

**Advantages:**
- Grants flow to sponsor's EIN, then distributed to Daanaa
- Daanaa stays as LLC (founder retains full board control)
- Founder can pursue revenue-generating services (letter automation, GPO) without legal friction
- Sponsor handles 990 reporting, tax compliance

**Disadvantages:**
- Sponsor takes 5–10% administrative fee
- Sponsor must approve major expenditures (contractual, but adds a governance layer)
- If sponsor changes policies, Daanaa must adapt or find new sponsor

**Cost:** ~$2,000–$5,000 setup + $500–$2,000/year

### Direct 501(c)(3) Model (Alternative)

**Structure:** Incorporate own nonprofit; Akbar is on board.

**Advantages:**
- Full independence; no sponsor overhead
- Faster grant access (once IRS determination letter arrives)
- Cleaner path to services revenue (nonprofits can be merchants)

**Disadvantages:**
- 4–6 month IRS determination wait (can apply pre-determination with most funders, but riskier)
- Annual Form 990-N filing + state charity registration
- Requires board (typically 3–5 people); founder is one voice

**Cost:** ~$800–$2,000 setup + $200–$500/year + attorney oversight

### Hybrid Model (Possible)

**Structure:** Form 501(c)(3) now + fiscal sponsor as interim (sponsor winds down when IRS letter arrives).

**Advantage:** Grants flow immediately (via sponsor), but you're incorporated & ready for independence in 6 months.

**Cost:** ~$3,000 setup + both sets of compliance initially.

### Daanaa-Specific Recommendation (for attorney to advise)

**Fiscal sponsorship for first 12 months** seems optimal because:
1. Grants flow fast (day 1 of sponsor agreement, not month 4)
2. Founder retains independence (Daanaa LLC, Akbar controls operations)
3. Services revenue can grow alongside (grant-funded platform + earned revenue from nonprofits)
4. Transition to own 501(c)(3) is clean (if desired) after proving the model

**Questions for attorney:**
1. Which fiscal sponsors are best for tech-for-nonprofits (Fast Forward, Tides, TECHSoup)?
2. What's a fair sponsor fee % and approval-rights boundary?
3. Can Daanaa (LLC) operate revenue services while under fiscal sponsor?
4. How long does sponsor agreement review take?
5. What's the cleanest transition path to own 501(c)(3) after 12 months?
6. Are there any IP or founder-control risks in the sponsor agreement?

---

## Memo 4: GPO Formation Requirements (Sketch)

**Question:** If Daanaa launches a nonprofit group purchasing organization (GPO), what are the legal requirements? (Full build deferred to G3; this is just the sketch.)

### Context

**What is a nonprofit GPO?**
A group purchasing organization where multiple nonprofits collectively negotiate discounts with vendors (software, insurance, payment processing, etc.). Member nonprofits pay a small membership fee; GPO takes a margin on vendor deals.

**Why Daanaa wants this:** Claimed nonprofits report that payment processing, software, and insurance are their top 3 overspend categories. A GPO solves real pain + generates revenue to fund the platform.

**Timeline:** Survey phase (G3) → Build decision (month 6) → Launch (month 9–12 if approved).

### Key Legal Questions (For Attorney to Sketch)

1. **Entity structure:** Is GPO a separate 501(c)(3)? A subsidiary of parent nonprofit? A for-profit LLC?
   - **Likely:** Separate 501(c)(3) for tax neutrality + grant eligibility. Daanaa (or sponsor) is founding member.

2. **Vendor agreements:** Can GPO negotiate on behalf of members, or must each member sign their own agreement?
   - **Likely:** GPO negotiates template; members opt-in per vendor.

3. **Antitrust:** Does a GPO of nonprofits trigger antitrust scrutiny?
   - **Likely:** No if membership is open, pricing is transparent, and GPO doesn't restrict member behavior.

4. **Bylaws & governance:** Minimal sketch—member voting, board structure, fee splits, dispute resolution.

5. **Liability:** Is Daanaa liable if a vendor fails to deliver, or is that the member's issue?
   - **Likely:** Each member assumes their own vendor risk; GPO is a facilitator.

### Questions for Attorney

1. What entity structure minimizes legal complexity + maximizes grant eligibility?
2. What bylaws/operating agreement template should we use?
3. What vendor agreement language protects the GPO + members?
4. Are there state-specific GPO regulations we need to navigate?
5. How does a GPO get its own tax ID & independent 501(c)(3)?

**Expected outcome:** 1-page template bylaws + vendor agreement checklist. Full legal build in G3.

---

## Next Actions for Akbar

1. **Review these memos.** Do they match your understanding? Adjust if needed.
2. **Add any operational details** I'm missing (e.g., which states are your priority? Do you have Every.org contact yet?).
3. **Identify attorney.** Recommend: nonprofit + tech specialist. Ask for fixed-fee bundled estimate for all four questions.
4. **Submit to attorney with cover memo:**
   > "We have four discrete legal questions that will unlock $X in grants and $Y in revenue. These memos provide operational context so we can spend your time on legal advice rather than background. Can you confirm/advise all four in a bundled engagement for ~$1,500?"
5. **Timeline:** Aim to complete G1 by end of week 3 of fundraising (July 1), so you can apply for grants requiring legal opinions.

---

## Reference: The Four G1 Questions

1. **Charitable solicitation:** State registration requirements for "Give here" CTAs?
2. **Letter service:** Can we issue §170(f)(8) acknowledgments as org's agent?
3. **Entity structure:** Fiscal sponsorship vs. 501(c)(3) vs. hybrid?
4. **GPO sketch:** Legal framework for nonprofit group purchasing?

All four unlock different workstreams:
- Q1 answer → Unblocks Every.org + giving pages (G2)
- Q2 answer → Unblocks letter service build (G3)
- Q3 answer → Shapes next 12 months of operations + fundraising
- Q4 answer → Unblocks GPO survey + design (G3)

---

**STATUS:** Draft awaiting your review. Finalize language + attorney contact info, then send.
