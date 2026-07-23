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

**Board Simulation Trigger:** When 3+ decisions pending OR end of autonomous build phase

