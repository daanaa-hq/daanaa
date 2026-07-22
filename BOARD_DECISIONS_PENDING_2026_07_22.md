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

## DECISION 2: [To Be Added]

---

**Board Simulation Trigger:** When 3+ decisions pending OR end of autonomous build phase

