# Board Decisions Pending — Session 2026-07-22
**Status:** Accumulating for comprehensive board simulation  
**Format:** Each decision includes context, options, and stewardship alignment  

---

## DECISION 1: Student Account Model (Age-Based Permissions)

**Question:** Should student accounts be student-owned or parent-dependent (especially for <13)?

### Option A: Student-Owned (Current Design)
- Student creates account, volunteer intent comes from student
- Parent receives consent request, approves
- For 13-17: Student agency + parental notification
- For <13: COPPA-compliant but parent approval required

**Pros:**
- Student owns their volunteering journey
- Single permission model for all ages
- Less complexity

**Cons:**
- <13 compliance could be clearer
- Doesn't handle shared custody well
- Teen might volunteer without parent knowledge (though system requires consent)

### Option B: Dependent Accounts (Parent-Owned)
- Parent creates account for child
- Multiple parents/guardians can share access (co-parents, guardians)
- Parent controls child's volunteering enrollment
- Child can log in and view own progress

**Pros:**
- Clear COPPA authority (parent is legal guardian)
- Handles shared custody (both parents access same account)
- Parent explicit intent ("I'm enrolling my child")

**Cons:**
- Reduces student agency (especially 13-17)
- Requires 3 permission models (dependent <13, semi-autonomous 13-17, independent 18+)
- More complex feature set (permission sharing, guardian role management)
- Risk of helicopter parenting (parent can revoke approval)

### Option C: Tiered Model (Hybrid)
- **<13:** Dependent (parent-owned, parent controls)
- **13-17:** Student-owned with parental notification (student controls, parent views read-only)
- **18+:** Student-owned, no parental visibility

**Pros:**
- Age-appropriate autonomy
- COPPA-compliant for minors
- Supports developmental stages

**Cons:**
- Highest complexity (3 permission models)
- Increases scope for Houston pilot
- More QA test cases

### Stewardship Alignment

**P2 - Privacy:** 
- All options OK if parent PII is not exposed to child, child data is minimized for parent
- Need clear boundary on what parent can see

**P10 - Human in Command:** 
- A: Student has command, parent validates
- B: Parent has command, child participates
- C: Command shifts by age

**Decision Impact:**
- Scope (affects feature set for Weeks 2-3)
- Pilot scope (which age groups?)
- QA complexity
- Legal/COPPA review needed

**Decision Needed:** Which model for Houston pilot?

---

## DECISION 2: AI Platform Assistant — Build Now or Post-Pilot?

**Question:** Should we build a voice/text AI agent for Daanaa operations now, or wait until after Houston pilot launch to inform the design?

### The Proposal
- **What:** Scoped AI assistant (not general chatbot) that helps users DO things on Daanaa
- **Features:** Create events, approve hours, find orgs via voice call or text chat
- **Example:** User calls +1-844-DAANAA-1, says "create volunteer event for Saturday," AI guides them through it
- **Differentiation:** No other nonprofit platform has this

### Option A: Build Now (Pre-Pilot)
- Start Week 2, ship Week 4
- Phone integration (Twilio) + action executor
- Available at Houston pilot launch
- Risk: Features we think users need may not match reality
- Benefit: Head-start on differentiation

**Pros:**
- ✅ Differentiator at launch
- ✅ Accessibility (voice for low-tech users)
- ✅ Shows innovation

**Cons:**
- ❌ Takes 4-6 hours (slips other Week 2 priorities)
- ❌ We don't know what Houston schools actually need yet
- ❌ May build wrong thing (feature creep without feedback)
- ❌ Voice auth + permissions add complexity

### Option B: Build Post-Pilot (After Week 14)
- Launch pilot with core student service only
- Get 4 weeks real feedback from Houston schools
- Build voice agent tailored to actual requests
- Risk: Competitors build voice features first
- Benefit: We build what users actually need

**Pros:**
- ✅ Lean startup approach
- ✅ Real feedback loop before building
- ✅ Keeps Week 2-10 focused on core pilot
- ✅ Reduces scope creep
- ✅ Higher chance of product-market fit

**Cons:**
- ❌ Slower to differentiate
- ❌ Competitors might launch voice first
- ❌ Lose first-mover advantage

### Stewardship Alignment

**P1 - Mission before growth:** Either approach works if focused on user value, not hype

**P2 - Privacy:** Voice auth creates new surface (who's calling?) — need careful design

**P10 - Human in command:** Users explicitly ask for actions — good, no manipulation

**Risk:** Building for "what we think users need" vs. "what they actually ask for"

### Timeline Impact

**Option A (Build Now):**
- Week 2-4: AI assistant development
- Slips: School admin endpoints, legal review preparation
- Week 10: Launch with both student service + voice assistant

**Option B (Build Later):**
- Week 2-10: Focus entirely on pilot core
- Week 10: Clean launch
- Week 14-16: Add voice based on feedback
- Week 18: Relaunch with voice

### My Recommendation

**Option B (Build Post-Pilot).** Ship the core pilot clean, get real user feedback, build voice assistant that actually solves problems users have. Lean startup methodology = higher success rate.

But this is a strategic board decision (growth vs. focus, first-mover risk, scope).

### Decision Needed
- A: Build AI assistant now (pre-pilot)
- B: Build after pilot (post-launch, feedback-driven)
- C: Hybrid (proof-of-concept now, full build post-pilot)

---

## DECISION 3: Fraud Detection Policy — Auto-Flag vs. Auto-Approve

**Question:** When fraud detection flags a submission, should it auto-reject and require manual review, or auto-approve but flag for async review?

### Option A: Auto-Reject (Conservative)
- Flagged submissions don't count toward hours until admin reviews
- Student sees: "Pending manual review — we flagged this as unusual"
- Admin reviews in dashboard, approves or rejects
- Safety: High (no false positives count)
- UX: Slower (student waits for admin)

**Pros:**
- ✅ Zero false positives (only genuine approvals count)
- ✅ Catches fraud before it's in impact stats
- ✅ Protects nonprofit reputation
- ✅ Meets P10 (human in command)

**Cons:**
- ❌ Frustrating for legitimate high-hour volunteers
- ❌ Adds admin review burden
- ❌ Could discourage students ("why is my submission pending?")

### Option B: Auto-Approve + Async Flag (Fast)
- Flagged submissions auto-approve and count toward hours
- Admin reviews in dashboard async (no hard deadline)
- Can reject retroactively if fraud detected
- Safety: Medium (false positives temporarily count)
- UX: Fast (student gets approval immediately)

**Pros:**
- ✅ Frictionless student experience
- ✅ Legitimate high-hour volunteers don't wait
- ✅ Lower admin burden (review is "nice to have")
- ✅ Meets P5 (no shame language — student doesn't see "flagged")

**Cons:**
- ❌ False positives temporarily inflate impact stats
- ❌ If admin misses review, fraud stays approved
- ❌ Harder to explain to nonprofits later ("why did we count hours we didn't verify?")

### Option C: Tiered (Hybrid)
- Risk 40-60 (medium): Auto-approve + flag for review
- Risk 60-80 (high): Require admin pre-approval
- Risk 80+ (critical): Auto-reject, escalate immediately

**Pros:**
- ✅ Balances fraud prevention + user experience
- ✅ Meets P10 (high-risk items require human review)

**Cons:**
- ❌ More complex admin workflow
- ❌ Requires clear thresholds (board needs to set them)

### Stewardship Alignment

**P5 - Don't weaponize transparency:** Auto-reject could shame students unfairly

**P10 - Human in command:** Either option OK if admin can override, but who reviews and when?

**P6 - Mistakes must be corrected:** If we auto-approve then retract, can we do that gracefully?

### Default (Embedded in Code)

Currently hardcoded: 80+ = critical, 60-80 = high, 40-60 = medium (no auto-action yet, just flagging).

### Decision Needed
- A: Auto-reject (conservative, safe, slower UX)
- B: Auto-approve + async flag (fast, risky)
- C: Tiered by risk score (hybrid)

---

## DECISION 4: Geographic Expansion Scope

**Question:** Is Houston pilot exclusive or open to other cities?

### Option A: Houston-Only (Focused)
- Pilot is just Houston (3-5 schools, 20 nonprofits)
- No marketing to other regions
- Full focus on making Houston work perfectly
- Expansion after pilot success (2027+)

**Pros:**
- ✅ Deep market fit (one city, one ecosystem)
- ✅ Easier operations (local relationships)
- ✅ Can refine based on real feedback
- ✅ Manage growth carefully

**Cons:**
- ❌ Slow growth curve
- ❌ Competitors can expand nationally

### Option B: Houston + Select Cities (Selective)
- Houston primary (3-5 schools)
- Open to 2-3 other strong nonprofit markets (e.g., Austin, San Antonio, Dallas)
- Managed expansion

**Pros:**
- ✅ Test multiple markets simultaneously
- ✅ Learning faster
- ✅ Competitive advantage vs. single-city

**Cons:**
- ❌ Operations more complex
- ❌ Risk of spreading thin

### Option C: National (Open)
- Houston is first, but open applications anywhere
- Let schools/nonprofits self-select
- Organic growth model

**Pros:**
- ✅ Max market opportunity
- ✅ Fast growth

**Cons:**
- ❌ Can't control quality of pilot (messy data)
- ❌ Support burden explodes
- ❌ Hard to validate assumptions

### Recommendation: **Option A (Houston-only)** — Ship clean, learn deep, expand informed.

### Decision Needed
- A: Houston only (focused, deep learning)
- B: Houston + 2-3 other cities (selective)
- C: National/open (organic growth)

---

## DECISION 5: Pricing Model — Who Pays?

**Question:** Is student service free, or do we charge schools/nonprofits?

### Option A: Free (Freemium MVP)
- Students: Free
- Schools: Free
- Nonprofits: Free
- Model: Later figure out revenue (B2B features, premium)

**Pros:**
- ✅ Maximum adoption
- ✅ Can focus on product
- ✅ Network effects (more students = more nonprofits)
- ✅ Aligns with P1 (mission before growth)

**Cons:**
- ❌ No revenue for pilot
- ❌ Harder to justify expansion
- ❌ Scope creep (free = expectations)

### Option B: Free for Students, Paid for Schools/Nonprofits
- Students: Free
- Schools: Pay per student or flat fee
- Nonprofits: Free (they're the cause)
- Revenue: School subscriptions

**Pros:**
- ✅ Students get access (mission)
- ✅ Schools have skin in game
- ✅ Revenue to sustain platform

**Cons:**
- ❌ Schools may not adopt
- ❌ Complicates sales
- ❌ Risk: P1 mission compromise (becomes paid tool)

### Option C: Free for Students, Schools Only (Nonprofits Invited)
- Students: Free
- Schools: Manage platform, track student hours
- Nonprofits: Free but invited (controlled onboarding)
- Revenue: School subscriptions

**Pros:**
- ✅ Schools drive adoption
- ✅ Quality control (invited nonprofits only)
- ✅ Revenue model clear

**Cons:**
- ❌ Nonprofits feel gated
- ❌ Slower nonprofit growth

### Stewardship Check (P1, P8)
- P1: Mission is helping students volunteer — revenue shouldn't corrupt that
- P8: Never handle funds — payment only to *us*, not through us

### Recommendation: **Option A (Free MVP)** — Launch free, build traction, monetize later if at all.

### Decision Needed
- A: Free for everyone (MVP, mission-first)
- B: Free students, paid schools/nonprofits
- C: Free students, school subscriptions

---

## DECISION 6: Minimum Student Age

**Question:** What's the minimum age for student accounts?

### Option A: 13+ (COPPA Boundary)
- 13-17: Parental consent required (Decision 1)
- 18+: Student-owned
- 13-year-olds can volunteer with parent approval

**Pros:**
- ✅ Aligns with COPPA (legal floor)
- ✅ Catches middle schoolers (emerging volunteers)
- ✅ Larger addressable market

**Cons:**
- ❌ Parental consent overhead (13-17 bucket)
- ❌ Houston schools start at 9th grade (age 14) mostly

### Option B: 16+ (Safer Legal)
- 16-17: Possibly with parental notice (lighter touch)
- 18+: Student-owned
- Older teens only

**Pros:**
- ✅ Simpler legal (less COPPA complexity)
- ✅ Aligned with Houston high schools
- ✅ Clearer developmental stage

**Cons:**
- ❌ Exclude middle schoolers + early HS
- ❌ Smaller market

### Option C: 18+ (No Minors)
- Adults only
- Zero legal complexity

**Pros:**
- ✅ Simplest legal
- ✅ No parental consent needed
- ✅ No COPPA worries

**Cons:**
- ❌ Miss high school market entirely
- ❌ Miss college gap year market
- ❌ Contradicts student service mission

### Recommendation: **Option A (13+)** — COPPA-compliant, larger market, supports full student lifecycle.

### Decision Needed
- A: 13+ (COPPA boundary, full market)
- B: 16+ (safer legal, HS focus)
- C: 18+ (simplest legal, adults only)

---

## DECISION 7: Volunteer Hour Constraints

**Question:** What are the min/max hours per submission and per student?

### Option A: Flexible (No Constraints)
- Min: 0.25 hours (15 min, if logged)
- Max: 24 hours/day
- No caps on student total
- Fraud detection catches outliers

**Pros:**
- ✅ Flexible for real-world volunteering
- ✅ Trust the data (fraud detection handles)
- ✅ No artificial constraints

**Cons:**
- ❌ Fraud detection has to catch everything
- ❌ Outliers (200h/month) look real but fraud-y

### Option B: Moderate Constraints
- Min: 1 hour (no micro-submissions)
- Max: 8 hours/day (reasonable day)
- Student max: 40 hours/week (full-time equiv)
- Anything over flagged for review

**Pros:**
- ✅ Reasonable guardrails
- ✅ Catches obvious fraud early
- ✅ Matches real volunteering patterns

**Cons:**
- ❌ Outliers (summer full-time volunteers) rejected
- ❌ Multiple-org students hit 40h limit

### Option C: Strict Constraints
- Min: 2 hours (meaningful commitment)
- Max: 4 hours/session (single shift)
- Student max: 20 hours/week
- Beyond = always flagged

**Pros:**
- ✅ Strictest fraud protection
- ✅ Prevents abuse

**Cons:**
- ❌ Excludes real but unconventional volunteering
- ❌ Too restrictive for passionate volunteers

### Stewardship Check (P4)
- P4: Small orgs deserve fairness — constraints shouldn't exclude smaller ops

### Recommendation: **Option B (Moderate)** — Real constraints that catch obvious fraud but don't exclude legitimate volunteers.

### Decision Needed
- A: Flexible, fraud-detection driven
- B: Moderate guardrails (1h min, 8h max, 40h/week)
- C: Strict guardrails (2h min, 4h max, 20h/week)

---

## DECISION 8: Nonprofit Recruitment & Communications Strategy

**Question:** What's our value proposition to nonprofits, and how do we position Daanaa?

### Context
Nonprofits need to understand *why* Daanaa is worth their time:
- They have existing volunteer systems (or none)
- They're skeptical of new platforms
- They care about: volunteer retention, impact tracking, ease of use

### Option A: Student Volunteer Pipeline (Student-Centric)
- **Pitch:** "Access verified student volunteers for structured service"
- **Benefits to nonprofits:** Reliable, documented hours; younger demographic; student networks
- **Not:** A general volunteer platform for all
- **Messaging:** "Partner with schools to build the next generation of civic leaders"

**Pros:**
- ✅ Clear differentiation (student focus, not broad)
- ✅ Aligns with schools (natural partners)
- ✅ High-quality, verified volunteers

**Cons:**
- ❌ Limits nonprofit pool (only want student volunteers)
- ❌ Seasonal (school year focus)

### Option B: Peer Financial Transparency (Nonprofit-Centric)
- **Pitch:** "Peer financial benchmarking + volunteer impact = donor trust"
- **Benefits to nonprofits:** Easier donor conversations, benchmark against peers, show impact
- **Not:** Just a volunteer tracker
- **Messaging:** "Show donors your financial health in peer context"

**Pros:**
- ✅ Unique to Daanaa (financial context + volunteering)
- ✅ Attracts quality nonprofits (transparent, data-driven)
- ✅ Broader nonprofit pool

**Cons:**
- ❌ Requires nonprofits to share data (privacy concern)
- ❌ More complex value prop

### Option C: Hybrid (Dual Value Prop)
- **To schools:** "Student service-learning + social-emotional learning"
- **To nonprofits:** "Student volunteers + peer financial transparency"
- **Messaging:** Depends on audience
- **But:** Risk of muddled brand (trying to be everything)

**Pros:**
- ✅ Broader appeal

**Cons:**
- ❌ Unfocused messaging
- ❌ Harder to sell

### Stewardship Check (P1, P4)
- P1: Mission before growth — value prop must serve nonprofits, not just Daanaa
- P4: Small orgs deserve fairness — messaging shouldn't advantage large orgs

### Communication Plan
Regardless of option, need:
- Email outreach templates
- Website copy (nonprofits page)
- Presentation for school partnerships
- FAQs on data privacy
- ROI calculator (impact per volunteer)

### Recommendation: **Option A (Student-Centric)** — Clear, differentiated, aligned with schools as natural partners. Financial context is backend benefit, not primary pitch.

### Decision Needed
- A: Student volunteer pipeline (student-centric)
- B: Peer financial transparency (nonprofit-centric)
- C: Hybrid (dual pitch, risk of confusion)

---

## DECISION 9: Donor Account Structure — Head of Household Hierarchy

**Question:** Should donation accounts be organized by Head of Household (with linked co-givers) or single-profile per person?

### Context
Most giving is organized by household or entity, not individual. A family's charitable giving is often decided by one person (head of household) but may include contributions from spouse, business, matching programs, etc.

**The Insight:** Organizing by "Head of Household" aligns how donations actually flow (one decision-maker per entity) and simplifies tax reporting (receipts go to head of household filer).

### Option A: Single Profile (Individual Only)
- One account per person, unrelated accounts
- Each person has their own wallet, history, tax receipt
- No connection between household members
- Simplest UX, no entity concept

**Pros:**
- ✅ Simplest to build
- ✅ Individual privacy (no linked accounts)
- ✅ Single tax receipt per person

**Cons:**
- ❌ Family giving fragmented (wife and husband each have separate account)
- ❌ Head of household can't see household giving (no aggregation)
- ❌ Spouse/co-giver can't track family intent together
- ❌ Tax reporting confusing (multiple receipts for one household donation)
- ❌ Missing family/entity context

### Option B: Head of Household + Co-Givers (Recommended)
- **Primary account:** Head of Household (person who files taxes)
  - Personal giving, business giving if applicable
  - Receives consolidated tax receipt
  - Can see all linked co-giver activity
- **Linked accounts:** Co-givers (spouse filing jointly, family members, business partners, dependents)
  - Can add to household wallet
  - Giving attributed to head of household (tax filing person)
  - Co-givers see giving history; head of household controls final spending
  - Dependents can propose orgs, but giving flows to parent's return
- **Example (Filing Jointly with Dependents):**
  - Akbar (head of household) + Spouse (filing jointly) + Kids (dependents)
  - All give to orgs through single household account
  - Single consolidated tax receipt to Akbar (HoH on joint return)
  - Tax filing simplified: one receipt, one line item on tax return
  - Akbar & spouse can both propose giving; kids propose where to give
  - All coordinated in one wallet

**Pros:**
- ✅ **Aligns donations:** All household/family giving aggregated in one place
- ✅ Tax-simple: Tax receipt goes to head of household (matches 1040 joint filing)
- ✅ Family coordination: Spouse + kids all see giving intent, HoH coordinates decisions
- ✅ Entity-clear: Business giving tracked separately but on same account
- ✅ Matches reality: How families actually give (one decision-maker, one tax filer, multiple participants)
- ✅ Scale handling: Works for families filing jointly, small partnerships, family-owned businesses
- ✅ Dependent support: Kids can see family giving; teaches financial values

**Cons:**
- ❌ More complex (need co-giver linking, permissions)
- ❌ Requires defining head of household (who's primary? could be contentious)
- ⚠️ Privacy: Linked accounts mean shared visibility (intentional for household)

### Option C: Household Entity (Most Complex)
- Each household/entity is one account (not one person)
- Household (or business) is the unit, not individual
- Multiple household members have "roles" (primary, co-signer, viewer)
- Giving is entirely aggregated at household level

**Pros:**
- ✅ Clearest entity model (household/business is the account)
- ✅ Natural tax reporting (entity receives receipt)
- ✅ Works for businesses (LLC, S-Corp, Corp giving directly)

**Cons:**
- ❌ Most complex to build (entity management, role hierarchy)
- ❌ Unusual UX (account is household, not person)
- ❌ Onboarding harder (establish who's head of household?)

### Stewardship Check (P2, P3, P5)
- **P2 (Privacy):** Head of household model requires shared visibility (intentional; spouse should know family giving)
- **P3 (Trust signals):** Tax filing status is objective; head of household is the IRS filer
- **P5 (Don't weaponize):** Use household aggregation for clarity, not targeting or pressure

### Impact on Features
- **Wallet:** Shared by household members, aggregated balance visible to all
- **Tax Receipt:** Single receipt to head of household, itemizes all linked co-givers
- **Giving Intent:** Head of household controls final decision; co-givers propose
- **Co-giver Roles:** 
  - Spouse: Add to wallet, propose orgs, see full history
  - Adult child: Propose giving, view only (no spending power)
  - Business partner: Contribute on behalf of entity
- **Compliance:** Household-level giving tracked; receipts to tax filer (head of household)

### Recommendation: **Option B (Head of Household + Co-Givers)** — Aligns how households actually give, simplifies tax reporting, matches IRS concept of filing household, enables family coordination. More complex than single-profile but matches reality and is worth the build.

### Decision Needed
- A: Single profile per person (simplest, fragmented)
- B: Head of Household + co-givers (recommended, aligns donations)
- C: Household entity account (most complex, most aligned but unusual UX)

---

---

## DECISION 10: Long-Term Revenue Model — Sustainability & Growth

**Question:** Beyond free MVP, what's the sustainable business model?

### Option A: Forever Free (Mission Model)
- Daanaa remains free for students, schools, nonprofits forever
- Revenue: Grants, donations, impact investment
- Sustainability: Fundraising-dependent

**Pros:**
- ✅ Aligns with P1 (mission before growth)
- ✅ Attracts nonprofit talent + board
- ✅ Maximum adoption

**Cons:**
- ❌ Fundraising hamster wheel
- ❌ Vulnerable to funder priorities
- ❌ Hard to scale sustainably

### Option B: Freemium (Nonprofits + Schools Pay for Premium)
- Core free tier (basic tracking)
- Premium for schools ($X/student) or nonprofits ($Y/month)
- Features: advanced analytics, API access, custom reporting

**Pros:**
- ✅ Sustainable revenue stream
- ✅ Orgs have skin in game
- ✅ Premium features can drive adoption

**Cons:**
- ❌ Risk: P1 mission (does paid tier corrupt free tier?)
- ❌ Sales burden (need sales team)
- ❌ May exclude smaller orgs from premium

### Option C: B2B ESG (Enterprise Partnerships)
- Free platform for students/nonprofits
- Revenue: Corporate ESG programs, employee-giving infrastructure
- Sell to: major employers, DAF platforms, corporate foundations

**Pros:**
- ✅ Large revenue potential
- ✅ Leverages existing consulting work
- ✅ Doesn't monetize nonprofits/students

**Cons:**
- ❌ Risk: P7 independence (corporate influence on ranking?)
- ❌ Risk: P1 mission (corporate priority vs. nonprofit needs)
- ⚠️ **CHARTER IMPLICATION:** Could conflict with P7 (independence protected) if not carefully gated

### Option D: Hybrid (Freemium + B2B ESG)
- Free core for nonprofits/students
- Premium add-ons for schools ($X)
- B2B ESG revenue (separate product line)
- Firewall between freemium and B2B

**Pros:**
- ✅ Multiple revenue streams
- ✅ Doesn't rely on one source

**Cons:**
- ❌ Most complex
- ❌ Risk of product schizophrenia
- ⚠️ **CHARTER IMPLICATION:** Firewall must be airtight (P7 + P1)

### Stewardship Check (P1, P7)
- **P1:** Mission before growth — which model keeps nonprofit needs primary?
- **P7:** Independence protected — does paid revenue compromise platform independence?
- **Tension:** B2B ESG could compromise independence if not carefully walled off

### Charter Implication Note
If board chooses B2B ESG (Option C or D), may need to add explicit **P7 Amendment:**
- "B2B revenue streams are structurally walled from core platform decisions"
- "No corporate customer influence over scoring, ranking, or nonprofit visibility"
- "Board has veto power on any corporate partnership"

### Recommendation: **Option D (Hybrid)** — Multiple revenue streams, explicit firewall protecting independence (Charter amendment required to formalize firewall + governance).

### Decision Needed
- A: Forever free (mission-pure, fundraising-dependent)
- B: Freemium (sustainable, education-focused)
- C: B2B ESG (high revenue, independence risk)
- D: Hybrid (diversified, requires Charter amendment on firewall)

---

## DECISION 11: Legal Structure & Liability — Volunteer Safety

**Question:** Who is liable if a volunteer causes damage or harm at a nonprofit?

### Context
Volunteer liability varies by state, but generally:
- Nonprofit is liable if volunteer is "negligent in role"
- Daanaa could be liable if we negligently placed/verified volunteer
- Volunteers typically have limited personal liability (nonprofits indemnify)

### Option A: Nonprofit Bears All Liability (Daanaa Not Liable)
- Nonprofit is sole responsible party
- Daanaa's Terms of Service disclaim all liability
- Requires nonprofit to carry insurance
- No background checks, no verification

**Pros:**
- ✅ Simplest legally
- ✅ No insurance needed
- ✅ Minimal overhead

**Cons:**
- ❌ Nonprofits may refuse (want Daanaa backing)
- ❌ If volunteer is fake/dangerous, negligent placement claim possible
- ❌ Risk: P4 (small orgs can't afford liability insurance)

### Option B: Shared Liability (Nonprofit Primary, Daanaa Secondary)
- Nonprofit is primary liable party
- Daanaa carries errors & omissions insurance
- Daanaa does basic verification (age, identity)
- Nonprofit still liable but has Daanaa coverage as backstop

**Pros:**
- ✅ Fairer to nonprofits (shared responsibility)
- ✅ Daanaa backs our verification work
- ✅ Encourages adoption

**Cons:**
- ❌ Insurance costs (~$10-50K/year)
- ❌ Ongoing verification/compliance overhead
- ❌ Potential negligent-placement claims

### Option C: Daanaa Assumes Liability (Full Insurance + Indemnity)
- Daanaa is liable party
- Daanaa carries comprehensive insurance
- Daanaa background-checks volunteers
- Nonprofits indemnified by Daanaa

**Pros:**
- ✅ Maximum nonprofit appeal (no liability exposure)
- ✅ Highest trust signal
- ✅ P4 compliance (small orgs protected)

**Cons:**
- ❌ Expensive insurance ($50-200K+/year)
- ❌ Background check infrastructure required
- ❌ Significant compliance burden
- ❌ Insurance may reject high-risk claims

### Stewardship Check (P4, P8)
- **P4:** Small orgs deserve fairness — Option A hurts small orgs (can't afford insurance)
- **P8:** Never handle funds — liability isn't "funds" but adjacent risk
- **Tension:** P4 suggests we should absorb some liability, but that's expensive

### Recommendation: **Option B (Shared Liability)** — Fair split (nonprofit primary, Daanaa secondary via insurance). Includes basic verification. Affordable ($20-30K insurance annually).

### Decision Needed
- A: Nonprofit bears all liability (simplest, unfair to small orgs)
- B: Shared liability (fair, moderate cost, basic verification)
- C: Daanaa assumes full liability (most protective, expensive, comprehensive checks)

---

## DECISION 12: Volunteer Verification — Identity & Age Confirmation

**Question:** How do we verify student volunteers are real and meet age requirements?

### Context
Verification affects:
- Fraud detection (fake students submit fake hours)
- Legal compliance (COPPA for <13, age proof for contracts)
- Nonprofit trust (are volunteers real?)
- UX friction (verification overhead)

### Option A: Self-Attestation Only
- Student says "I'm 14, my name is John"
- No verification
- Fraud detection flags anomalies post-hoc
- Nonprofit trusts Daanaa fraud system

**Pros:**
- ✅ Frictionless signup
- ✅ No infrastructure needed
- ✅ Maximum adoption speed

**Cons:**
- ❌ Easy to fake (anyone can claim age)
- ❌ COPPA risk (no age verification for <13)
- ❌ Nonprofits distrust (no verification)
- ❌ Liability risk (negligent placement)

### Option B: School-Mediated Verification
- Student signs up via school (QR code, teacher code)
- School confirms student identity + age
- Daanaa trusts school as verifier
- Requires school participation

**Pros:**
- ✅ Strong verification (school knows students)
- ✅ Natural COPPA solution (school verifies age for <13)
- ✅ Nonprofit trust (verified via school)
- ✅ Minimal Daanaa overhead

**Cons:**
- ❌ Requires school buy-in + setup
- ❌ Excludes homeschooled/independent students
- ❌ Slower initial adoption

### Option C: Third-Party Age Verification (Socure, Mitek, etc.)
- Student provides ID or photo
- Third-party verifies age/identity
- Cost: $0.50-2 per verification
- Friction: ~30 seconds per student

**Pros:**
- ✅ Strong legal protection (third-party verified)
- ✅ COPPA-compliant
- ✅ Scalable (no school dependency)

**Cons:**
- ❌ Cost (~$500-5000/month at scale)
- ❌ UX friction (ID photo required)
- ❌ Privacy concerns (ID data to third party)
- ⚠️ **PRIVACY IMPLICATION:** May violate P2 (Stewardship: minimize data collection)

### Option D: Hybrid (School Primary, Third-Party Fallback)
- Prefer school verification (zero friction, school-verified)
- Fall back to age-verification service if school unavailable
- Best of both worlds

**Pros:**
- ✅ Balances friction and coverage
- ✅ Leverages schools where possible
- ✅ Scales beyond schools

**Cons:**
- ❌ Most complex
- ❌ Two systems to maintain

### Stewardship Check (P2, P4)
- **P2:** Privacy-first — Option C (third-party ID) violates data minimization
- **P4:** Small orgs benefit from verified volunteers
- **Tension:** Verification adds friction; self-attestation is risky

### Recommendation: **Option D (Hybrid)** — School verification primary (leverages natural channel), third-party fallback for non-school students. School verification is frictionless + privacy-first.

### Decision Needed
- A: Self-attestation only (frictionless, risky)
- B: School-mediated verification (strong, school-dependent)
- C: Third-party age verification (strong, privacy risk, cost)
- D: Hybrid school + third-party (balanced, most flexible)

---

## DECISION 13: Data Retention & Privacy Policy — Compliance Scope

**Question:** How long do we keep volunteer records, and what's our compliance scope?

### Context
Different jurisdictions have different requirements:
- **GDPR (EU):** Right to deletion after purpose fulfilled
- **CCPA (California):** Consumer right to deletion
- **COPPA (US <13):** Parental right to review/delete
- **State volunteering laws:** Vary on record retention

### Option A: Permanent Retention (Archive Everything)
- Keep all volunteer records forever
- Enables historical impact tracking
- Useful for research/evaluation
- High data liability

**Pros:**
- ✅ Rich historical data
- ✅ Long-term impact measurement

**Cons:**
- ❌ Violates GDPR (no right to deletion)
- ❌ Violates CCPA (no right to deletion)
- ❌ COPPA risk (parental deletion not possible)
- ❌ Privacy risk (stale data breach exposure)
- ❌ Violates P2 (Stewardship: minimize data retention)

### Option B: Time-Limited Retention (7 Years Then Deletion)
- Keep active records for 7 years (statute of limitations for liability)
- After 7 years: delete all PII, aggregate only
- Honors right to deletion (GDPR/CCPA compliant)
- COPPA-safe (parental deletion always honored)

**Pros:**
- ✅ Legally compliant (GDPR, CCPA, COPPA)
- ✅ Balances accountability + privacy
- ✅ P2-aligned (data minimization by time)
- ✅ Liability safe (retain for legal holds)

**Cons:**
- ❌ Lost long-term historical data after 7 years
- ❌ Aggregation-only limits research

### Option C: Aggressive Deletion (1 Year Retention)
- Keep records only 1 year
- After 1 year: delete all data including aggregates
- Maximum privacy

**Pros:**
- ✅ Strongest privacy (P2-aligned)
- ✅ GDPR/CCPA/COPPA compliant
- ✅ Minimal data liability

**Cons:**
- ❌ Can't track multi-year volunteer growth
- ❌ Can't measure long-term impact
- ❌ Liability risk if deleted too early

### Option D: Hybrid (Active Records 7 Years, Aggregates Indefinite)
- PII deleted after 7 years
- But aggregate statistics (total hours, nonprofit impact) retained forever
- Balances privacy + impact measurement

**Pros:**
- ✅ Legally compliant
- ✅ Enables long-term impact tracking
- ✅ No PII after 7 years
- ✅ P2-aligned (PII minimized)

**Cons:**
- ❌ Somewhat complex (hybrid retention)
- ❌ Aggregate data could theoretically re-identify

### Stewardship Check (P2, P6)
- **P2:** Privacy-first — minimize retention, honor deletion rights
- **P6:** Mistakes must be corrected — need data to correct records

### Charter Amendment Possible
May need to add **P2 Amendment:** "Volunteer data retained for 7 years for legal/compliance, then PII deleted. Aggregates may be retained indefinitely for impact measurement."

### Recommendation: **Option D (Hybrid)** — 7-year PII retention (legal hold), indefinite aggregate retention (impact tracking). Stewardship P2-compliant.

### Decision Needed
- A: Permanent retention (simplest, privacy violation)
- B: 7-year retention (balanced, compliant)
- C: 1-year deletion (maximum privacy, impact trade-off)
- D: Hybrid PII + aggregate (compliance + measurement)

---

## DECISION 14: Board Governance & Conflict of Interest Policy

**Question:** How should the board govern post-launch? How do we handle consulting/ESG conflicts?

### Context
Current situation:
- Founder: Akbar (also consulting/B2B ESG work)
- Board: Several members with nonprofit/corporate affiliations
- Risk: Corporate board members influence platform decisions for ESG goals

### Option A: No Formal Conflict Policy (Trust-Based)
- Board members self-disclose conflicts
- No formal vote recusal process
- Trust that members act in Daanaa's interest
- Lightweight governance

**Pros:**
- ✅ Simplest
- ✅ Fast decision-making
- ✅ No overhead

**Cons:**
- ❌ Violates P7 (independence not formally protected)
- ❌ Risky if corporate board member pushes agenda
- ❌ No formal recusal process

### Option B: Formal Conflict Policy (Legal Standard)
- Written conflict-of-interest policy
- Board members disclose affiliations annually
- Automatic recusal on self-interested votes
- Legal review of major corporate partnerships

**Pros:**
- ✅ Formally protects P7 (independence)
- ✅ Legal defensibility
- ✅ Board clarity

**Cons:**
- ❌ More overhead (disclosure process, legal review)
- ❌ Slows decisions on partnerships

### Option C: Independence Firewall (Strict Model)
- No corporate board members
- Founder's consulting work in separate legal entity
- Strict firewall: consulting work never influences platform
- Board has veto power on corporate partnerships

**Pros:**
- ✅ Maximum independence (P7)
- ✅ Zero ambiguity

**Cons:**
- ❌ Limits board expertise (no corporate insight)
- ❌ Difficult to execute (restructuring)

### Option D: Hybrid (Formal Policy + Corporate Advisory Board)
- Board: nonprofit/civic leaders only (no corporate)
- Formal conflict policy for board members
- Separate Corporate Advisory Board (advisory, no votes)
- Consulting work declared and firewalled

**Pros:**
- ✅ Protects board independence (P7)
- ✅ Still get corporate input (advisory)
- ✅ Balanced approach

**Cons:**
- ❌ More governance structure
- ❌ Advisory board has no real power

### Stewardship Check (P7, P1)
- **P7:** Independence must be protected — formal policy required if corporate board members
- **P1:** Mission before growth — board should prioritize nonprofit mission, not corporate revenue

### Charter Implication Note
If corporate board members or consulting work continues, **P7 Amendment** required:
- "Board has formal conflict-of-interest policy with annual disclosures"
- "Board members recuse from self-interested votes"
- "Corporate partnerships require board supermajority vote"
- "Founder's consulting work never influences platform decisions"

### Recommendation: **Option D (Hybrid)** — Civic board + corporate advisory, formal conflict policy. Protects P7 while leveraging corporate expertise.

### Decision Needed
- A: Trust-based (simplest, risky for independence)
- B: Formal conflict policy (compliant, overhead)
- C: Independence firewall (strictest, restructuring needed)
- D: Hybrid board + advisory + policy (balanced, most governance)

---

## DECISION 15: Insurance & Risk Management — Coverage & Limits

**Question:** What insurance do we need? What's our risk profile and coverage strategy?

### Context
Daanaa touches multiple liability surfaces:
- Volunteer liability (student causes damage at nonprofit)
- Professional liability (we rank orgs, someone claims harm)
- Cyber/data breach (we hold volunteer + donor data)
- Directors & Officers (board members exposed to liability)
- Employment practices liability (discrimination claims)

### Option A: Bare Minimum (General Liability Only)
- General liability: $1M / $2M aggregate
- Cost: ~$2-5K/year
- Coverage: Basic bodily injury, property damage

**Pros:**
- ✅ Cheapest
- ✅ Covers basic accidents

**Cons:**
- ❌ No professional liability (ranking harm claims)
- ❌ No cyber/data breach coverage
- ❌ No D&O protection
- ❌ Likely insufficient if volunteer causes harm

### Option B: Moderate Coverage (General + Professional)
- General liability: $1M / $2M
- Professional liability (errors & omissions): $1M / $2M
- Cost: ~$10-15K/year
- Covers: Accidents + ranking/advice harm

**Pros:**
- ✅ Covers volunteer + professional liability
- ✅ Reasonable cost
- ✅ Adequate for pilot stage

**Cons:**
- ❌ No cyber coverage
- ❌ No D&O protection
- ❌ May be insufficient if major data breach

### Option C: Comprehensive Coverage (Full Insurance Program)
- General liability: $2M / $4M
- Professional liability: $2M / $4M
- Cyber/data breach: $1M limit
- Directors & Officers: $1M / $2M
- Employment practices: $500K
- Cost: ~$30-50K/year
- Covers: Everything

**Pros:**
- ✅ Comprehensive protection
- ✅ Covers all major risk surfaces
- ✅ Board members protected

**Cons:**
- ❌ Expensive ($30-50K/year)
- ❌ May be overkill for pilot stage
- ❌ Increases overhead

### Option D: Progressive Coverage (Grows with Scale)
- Year 1 (Pilot): General + Professional ($10-15K)
- Year 2 (After 10+ schools): Add cyber + D&O ($25-35K)
- Year 3+ (Scale): Full comprehensive ($40-50K+)
- Scales with liability exposure

**Pros:**
- ✅ Matches risk to stage
- ✅ Affordable early, comprehensive later
- ✅ Revisit annually

**Cons:**
- ❌ Gap exposure during growth
- ❌ Requires annual review process

### Stewardship Check (P4, P8)
- **P4:** Small orgs — coverage shows we back our work
- **P8:** Never handle funds — insurance is risk, not funds (OK)

### Recommendation: **Option D (Progressive)** — Start with General + Professional ($12K/year), grow coverage as we scale. Annual review aligns coverage with liability growth.

### Decision Needed
- A: Bare minimum (cheapest, risky)
- B: General + Professional (adequate, moderate cost)
- C: Comprehensive (full protection, expensive)
- D: Progressive scaling (balanced, annual review)

---

## 14 BOARD DECISIONS READY FOR COMPREHENSIVE SIMULATION

**Product & Scope:**
1. Student Account Model (parent-dependent vs. student-owned)
2. AI Platform Assistant Timing (now vs. post-pilot)
3. Fraud Detection Policy (auto-flag vs. auto-approve)
4. Geographic Expansion (Houston only vs. selective vs. national)
5. Pricing Model (free vs. paid)
6. Minimum Student Age (13+ vs. 16+ vs. 18+)
7. Volunteer Hour Constraints (flexible vs. moderate vs. strict)

**Go-to-Market & User Strategy:**
8. Nonprofit Communications (student-centric vs. financial-centric vs. hybrid)
9. Donor Profiles (tax-filing-aligned vs. simplified vs. single)

**Business & Sustainability:**
10. Long-Term Revenue Model (forever free vs. freemium vs. B2B ESG vs. hybrid)
11. Volunteer Liability Structure (nonprofit bears all vs. shared vs. Daanaa assumes)
12. Volunteer Verification (self-attestation vs. school-mediated vs. third-party vs. hybrid)

**Legal & Governance:**
13. Data Retention Policy (permanent vs. 7-year vs. 1-year vs. hybrid PII+aggregates)
14. Board Governance & Conflicts (trust-based vs. formal policy vs. firewall vs. hybrid)
15. Insurance & Risk Management (bare minimum vs. moderate vs. comprehensive vs. progressive)

---

## ⚠️ CHARTER & STEWARDSHIP IMPLICATIONS

Several decisions have **tension with existing Stewardship principles**:

**Decision 10 (Revenue):**
- Option C (B2B ESG) risks **P7 (independence)** — needs formal firewall amendment

**Decision 11 (Liability):**
- Option A (nonprofit bears all) violates **P4 (fairness)** — small orgs can't afford insurance

**Decision 12 (Verification):**
- Option C (third-party ID) violates **P2 (privacy-first)** — collects unnecessary data

**Decision 13 (Data Retention):**
- Option A (permanent) violates **P2 (minimize retention)** — must add retention policy

**Decision 14 (Board Governance):**
- Options A (no policy) violate **P7 (independence)** — need formal conflict policy

**Decision 15 (Insurance):**
- Option A (bare minimum) may violate **P4 (fairness)** if we can't back our work

---

## Board Simulation Structure

**Suggested flow:**
1. Walk through Decisions 1-7 (product/scope)
2. Walk through Decisions 8-9 (user strategy)
3. Walk through Decisions 10-12 (business + legal)
4. Walk through Decisions 13-15 (governance + risk)
5. **Stewardship Review:** For each decision with Charter tension, board decides:
   - Accept recommendation as-is
   - Modify recommendation
   - **Amend Charter** to accommodate decision

**This will be a rich conversation on where principles and pragmatism intersect.** 🎯

