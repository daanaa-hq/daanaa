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

## DECISION 9: Donor Profile Types — Work/Personal Separation

**Question:** Should donors have separate work and personal giving profiles?

### Context
Donors are individuals who may give in two contexts:
- **Personal:** Individual donations from personal conviction
- **Work:** Corporate/employee-giving programs, matched donations, workplace commitments

### Option A: Single Universal Profile
- One account per donor
- All giving in one wallet/history
- Donor chooses whether giving is personal or work
- Simpler UX, less fragmentation

**Pros:**
- ✅ Simple (one account)
- ✅ Unified impact tracking
- ✅ Lower platform overhead
- ✅ Easier to understand (one identity)

**Cons:**
- ❌ Can't separate work vs. personal giving
- ❌ Corporate programs can't track their giving
- ❌ Employee matching not tracked separately

### Option B: Dual Profiles (Work + Personal)
- Donors can create both a personal AND a work profile
- Separate wallets, separate histories
- Can switch contexts easily
- Work profile linked to employer (for matching)

**Pros:**
- ✅ Separate giving contexts
- ✅ Corporate programs can track giving
- ✅ Employee matching traceable
- ✅ Privacy separation (work vs. personal)
- ✅ Tax clarity (work giving might differ)

**Cons:**
- ❌ More complex UX (which profile?)
- ❌ Duplicate data (same person, two records)
- ❌ Confusion possible (which profile did I use?)
- ❌ Platform overhead (managing two profiles)

### Option C: Work Profile As Optional Addon
- Start with single personal profile (default)
- Add optional "work profile" if donor has employer program
- Bridges A and B (simple default, powerful when needed)

**Pros:**
- ✅ Simple default (no clutter)
- ✅ Powerful for corporates who need it
- ✅ Scalable (add later if demand grows)

**Cons:**
- ❌ Requires setup/onboarding complexity
- ❌ May confuse donors

### Stewardship Check (P2, P5)
- P2: Privacy — work profile could expose employer information
- P5: Don't weaponize — don't use profile separation for marketing/targeting

### Impact on Features
- **Wallet:** Show giving history by profile
- **Notifications:** Control which profile gets email updates
- **Corporate:** Employer can view aggregate (not individual) giving
- **Impact:** Combined impact across profiles, or separate?

### Recommendation: **Option C (Optional Work Addon)** — Simple default, optional complexity for corporate users. Launch with personal-only, add work profiles in 2027 if corporate demand justifies it.

### Decision Needed
- A: Single universal profile (simpler)
- B: Dual profiles by default (more powerful)
- C: Personal default + optional work addon (hybrid)

---

## 9 BOARD DECISIONS READY FOR SIMULATION

1. Student Account Model (parent-dependent vs. student-owned)
2. AI Platform Assistant Timing (now vs. post-pilot)
3. Fraud Detection Policy (auto-flag vs. auto-approve)
4. Geographic Expansion (Houston only vs. selective vs. national)
5. Pricing Model (free vs. paid)
6. Minimum Student Age (13+ vs. 16+ vs. 18+)
7. Volunteer Hour Constraints (flexible vs. moderate vs. strict)
8. Nonprofit Communications (student-centric vs. financial-centric vs. hybrid)
9. Donor Profiles (single vs. dual work/personal vs. optional addon)

**Board Simulation Trigger:** Comprehensive strategic review (all 9 decisions, one session)

