# Development Plan: Student Service Pilot + QA Unblocking
**Status:** Ready to Execute  
**Timeline:** Weeks 1-23 (9-week prep + 14-week pilot)  
**Board Authorization:** Pending (memo ready, simulation approved 7-0)  
**QA Status:** Blocked on 3 Priority 0 issues; authenticated testing not yet functional  

---

## Phase 0: Unblock QA (Days 1-3)

**Goal:** Get authenticated nonprofit testing working so we can validate existing infrastructure before building student service.

### Blocker #1: Test Account Not Linked to Nonprofit (CRITICAL)
**Current State:**
- Firebase login works (test@testnonprofit.org / TestNonprofit2024!)
- Account authenticates but dashboard returns 500
- Volunteer list returns 403 "You do not own this nonprofit"
- Backend expecting nonprofit_accounts claim link

**Fix:**
```sql
-- Verify the link exists and is correct
SELECT * FROM nonprofit_accounts 
WHERE email = 'test@testnonprofit.org';

-- Should return: EIN 123456789 (Test Food Bank), verified=1

-- If missing or wrong, insert/update:
INSERT OR REPLACE INTO nonprofit_accounts 
  (email, ein, verified, created_at)
VALUES 
  ('test@testnonprofit.org', '123456789', 1, datetime('now'));

-- Verify Test Food Bank exists in registry
SELECT * FROM registry_enriched 
WHERE ein = '123456789';
```

**Owner:** You (database admin)  
**Timeline:** 15 minutes  
**Verification:** Firebase login → nonprofit dashboard returns 200 (not 500)  

### Blocker #2: Authenticated Dashboard Returns 500
**Current State:**
- GET `/api/nonprofit/profile` returns 500
- Likely issue: nonprofit_accounts join missing or authorization header malformed

**Fix Steps:**
1. Check backend logs: `tail -f /var/log/daanaa_api.log` during test login
2. Look for SQL error or missing user_id in request
3. Probable causes:
   - nonprofit_accounts table join failing
   - Missing authorization header in frontend
   - Stale token/session

**Owner:** Backend debugging (you or engineer)  
**Timeline:** 1-2 hours  
**Verification:** GET `/api/nonprofit/profile` returns 200 + nonprofit data  

### Blocker #3: Authenticated Volunteer List Returns 403
**Current State:**
- GET `/api/nonprofit/{ein}/volunteer_hours` returns 403 "You do not own this nonprofit"
- Backend checking request user_id against nonprofit_accounts.ein

**Fix:**
1. Verify nonprofit_accounts.ein matches request parameter
2. Check that Firebase token includes correct user ID
3. Ensure authorization middleware extracts user_id correctly from Firebase token

**Owner:** Backend authorization flow  
**Timeline:** 1-2 hours  
**Verification:** GET `/api/nonprofit/123456789/volunteer_hours` returns 200 + volunteer list  

### Blocker #4: Profile Editor Returns 403
**Current State:**
- GET `/api/nonprofit/profile` (edit endpoint) returns 403

**Fix:**
- Same as Blocker #3 (authorization middleware issue)

**Owner:** Backend authorization  
**Timeline:** Included in #3 fix  
**Verification:** GET `/api/nonprofit/profile` (editor) returns 200 + editable fields  

---

## Phase 1: Complete QA (Days 4-7)

**Goal:** Validate all public and authenticated flows work before starting student service development.

### Authenticated QA Tests (now unblocked)
```
✅ Nonprofit dashboard loads
✅ Volunteer hours list displays
✅ Can see volunteer submissions
✅ Profile editor renders
✅ Can edit nonprofit mission/programs
✅ Wallet functions work
✅ Help tooltips display
✅ Mobile viewport works
```

**Owner:** QA team (human testing)  
**Timeline:** 2-3 hours  
**Output:** QA_RUN_2026_07_22_AUTHENTICATED.md with full test results  

### Priority 1 Tests (automation)
- Volunteer end-to-end flow (create → submit → approve → certificate)
- Duplicate hour detection
- Wallet status reconciliation
- Privacy tests (no IP leakage, no PII exposure)

**Owner:** QA engineer  
**Timeline:** 4-6 hours  
**Output:** Updated QA_TEST_2026_07_22.sh with Priority 1 tests  

### Stewardship Verification
- No production data changed
- No donor/volunteer PII exposed
- Audit trail complete
- Privacy invariants maintained

**Owner:** You (stewardship checkpoint)  
**Timeline:** 1 hour  
**Output:** STEWARDSHIP_QA_CHECKLIST.md signed off  

---

## Phase 2: Board Presentation & Authorization (Week 1)

**Goal:** Get board approval for student service pilot + resource allocation.

### Board Meeting (Friday or next week)
**Materials:**
- ✅ BOARD_MEMO_STUDENT_SERVICE_INITIATIVE.md (Charter-compliant, ready)
- ✅ BOARD_SIMULATION_LIVE_SESSION_2026_07_22.md (7-0 approval, ready)
- ✅ Charter Compliance Audit (all gaps fixed)

**Expected Outcome:**
- 🟢 Unanimous or near-unanimous board approval
- Authorization for 3 FTE dev + 2.5 FTE pilot operations
- Legal review gate (COPPA/FERPA before enrollment)
- Week 9 checkpoint with enrollment floor (30 students)

**Next:** Once approved, engineering sprints begin

---

## Phase 3: Development Sprint 1 (Weeks 1-6)

**Goal:** Build core student service features while extending existing volunteer infrastructure.

### Week 1: Design & Architecture
**Team:** Founder + Product + Engineer  
**Deliverables:**
- UI mockups (opportunity listing, service log, verification flow)
- Database schema changes (student_service_* tables, nullable parent consent fields)
- API endpoint list (student opportunity discovery, service submission, verification)
- Privacy & compliance checklist

**Integration with Existing Code:**
- Extends `volunteer_hours` table (add student_id, student_school, parent_consent)
- Reuses `volunteer_hour_confirmations` (supervisor verification)
- Extends `nonprofit_accounts` (add school_admin_link)
- Uses existing authentication pattern (Firebase for nonprofits, Google OAuth for schools)

**Owner:** Founder (architecture decisions)  
**Timeline:** 3-4 days  

### Week 2: Legal & Privacy Review
**Team:** Legal counsel + Privacy officer  
**Deliverables:**
- COPPA compliance certification (13+ pathway)
- FERPA analysis (school data sharing scope)
- Student consent templates
- Parental consent forms (if under-18)
- Data retention policy
- Youth safety procedures

**Blockers:** None if external counsel engaged immediately  
**Owner:** External legal review (coordinate by day 1)  
**Timeline:** 2-3 weeks (run parallel to engineering)  

### Week 3-4: Engineering Sprint 1
**Team:** 1 senior engineer full-time  
**Features:**
1. Opportunity publishing interface (nonprofit dashboard → add student volunteer opportunities)
2. Student service log (student logs hours: date, org, activity, hours)
3. Nonprofit supervisor verification (one-click approve/reject)
4. Certificate generation (PDF with unique validation number)

**Code Changes:**
- `daanaa_api.py`: Add `/api/student/opportunities`, `/api/student/service_log`, `/api/nonprofit/verify_service`
- `frontend/src/pages/StudentService/`: New pages (Discover, ServiceLog, Certificate)
- Database schema: Add student tables, extend volunteer_hours
- Privacy checks: Verify no student data exposed in public API

**Existing Code Reused:**
- `volunteer_hours_events_api` (use for service tracking)
- `WalletContext` (adapt for student service bookmarks)
- `nonprofit_accounts` pattern (adapt for school admin accounts)
- Authentication flow (Firebase for nonprofits, Google OAuth for schools)

**Owner:** Engineer (solo build)  
**Timeline:** 2-3 weeks  
**Testing:** Unit tests + integration tests (not end-to-end yet; needs QA)  

### Week 5-6: Engineering Sprint 2
**Team:** 1 senior engineer full-time + 0.3 designer  
**Features:**
1. Reporting dashboards (nonprofit: hours by student, by date; school: all students, all orgs)
2. Admin tools (remove/flag service records, dispute resolution)
3. Audit procedures (random verification of 5-10% of submissions)
4. Export/download (student downloads certificate, nonprofit exports hours list)

**Code Changes:**
- `daanaa_api.py`: Add `/api/student/certificate/{id}`, `/api/nonprofit/reports`, `/api/admin/audit`
- `frontend/src/pages/StudentService/`: Dashboard, reporting, export views
- Database: Add audit tables, add reporting views

**Existing Code Reused:**
- Dashboard pattern (reference nonprofit dashboard for UI)
- Export pattern (reference wallet export)
- Admin pattern (reference existing admin endpoints)

**Owner:** Engineer + Designer  
**Timeline:** 2-3 weeks  
**Testing:** Unit + integration + human QA  

---

## Phase 4: Security & Compliance (Weeks 7-9)

### Week 7: Security Review
**Team:** External security consultant  
**Scope:**
- API endpoint authorization (no public exposure of student data)
- Database query injection prevention
- Authentication token handling
- Data encryption in transit and at rest

**Deliverable:** Security audit report + any fixes needed  
**Owner:** Coordinate external security firm  
**Timeline:** 1 week (parallel to development)  

### Week 8: WCAG 2.2 AA Accessibility
**Team:** Accessibility consultant  
**Scope:**
- Screen reader compatibility (student service pages)
- Keyboard navigation (all forms)
- Color contrast (meeting AA standards)
- Mobile viewport (responsive design)

**Deliverable:** WCAG audit report + fixes  
**Owner:** Coordinate accessibility specialist  
**Timeline:** 1 week  

### Week 9: Partner Recruitment & Legal Finalization
**Team:** Partnerships lead + Legal  
**Scope:**
- 3-5 Houston schools/youth orgs (recruitment + agreement signing)
- 20 nonprofits (outreach + training prep)
- Legal review finalized (COPPA/FERPA clearance)
- Nonprofit supervisor training materials drafted

**Deliverable:** 
- Signed school partnership agreements
- Nonprofit list + supervisor assignments
- Legal compliance checklist checked off
- Training slides ready

**Owner:** Partnerships lead (external recruitment)  
**Timeline:** 3 weeks (weeks 7-9)  

### Week 9: Board Checkpoint (Thursday)
**Presentation:**
- Adoption metrics (schools + nonprofits committed)
- Technical readiness (security + accessibility review results)
- Legal status (COPPA/FERPA clearance confirmed)
- Go/no-go recommendation

**Expected Outcome:**
- Board votes to proceed with pilot launch
- Or board pauses for additional work
- Or (unlikely) board discontinues

**Owner:** Founder + Team  
**Timeline:** 2 hours  

---

## Phase 5: Houston Pilot (Weeks 10-22)

### Week 10: Soft Launch & Staff Training
**Activities:**
- Staff training on student safety procedures
- Nonprofit supervisor onboarding (30-min per org)
- School administrator orientation
- Launch checklist verification

**Owner:** Operations manager  
**Timeline:** 1 week  

### Weeks 11-22: Live Pilot (1 Semester = ~14 weeks)
**Activities:**
- Students enroll through participating schools (13+ only)
- Nonprofits publish volunteer opportunities
- Students find opportunities and log hours
- Nonprofit supervisors verify submissions
- Weekly metrics collection (enrollment, hours, completion rate)
- Dispute resolution as needed
- Random audits (5-10% of submissions)
- Bug fixes and UX iterations

**Weekly Reporting:**
- Enrollment trends
- Completion rates
- Verification speed
- Fraud/dispute flags
- System uptime

**Owner:** Operations team + Engineer support  
**Timeline:** 14 weeks  

---

## Phase 6: Post-Pilot Evaluation (Week 23)

### Data Collection & Analysis
**Metrics to Report:**
1. Enrollment (target: 100+ students, 10+ nonprofits, 3+ schools)
2. Completion (target: 70%+ of committed hours verified)
3. Verification quality (target: <2% fraud/error rate)
4. User satisfaction (target: 4+/5 stars from students and nonprofits)
5. Operational cost (target: $3-5 per verified hour)
6. System reliability (target: 99%+ uptime)

### Board Report
**Contents:**
- Pilot outcomes against success metrics
- Risk incidents (if any) and resolutions
- Cost breakdown and scalability assessment
- Partnership opportunities (AmeriCorps, Points of Light, etc.)
- Student and nonprofit feedback
- Recommendation (expand, modify, discontinue, or prepare for certification)

**Owner:** Founder + Operations manager  
**Timeline:** 2 weeks  

### Board Decision Meeting
**Options:**
1. **Expand:** Approve 2-3 new cities (Austin, San Antonio)
2. **Modify:** Expand to under-13 (if legal permits), or reduce scope
3. **Discontinue:** Pilot showed insufficient adoption
4. **Prepare for Certification:** Plan SOC 2 audit + broader rollout

**Expected:** Board chooses Expand or Modify (based on simulation, 90%+ likely)

---

## Resource Plan

### FTE Allocation (Weeks 1-6)
- **Founder:** 0.5 (design decisions, legal coordination, board reporting)
- **Product Manager:** 0.5 (deprioritize insights dashboard → Q4)
- **Engineer:** 1.0 full-time (core features)
- **Designer:** 0.3 (UI, responsive, accessibility planning)
- **Legal/Privacy:** 0.7 external (COPPA, FERPA, student consent templates)
- **Operations:** 0.5 (partner recruitment, pilot operations prep)

**Total:** ~3.5 FTE (dev focus) + 0.5 FTE external

### FTE Allocation (Weeks 7-9)
- Same + Security consultant (0.2 external), Accessibility consultant (0.2 external)
- Total: ~3.5 internal + 0.4 external

### FTE Allocation (Weeks 10-22 Pilot)
- **Founder:** 0.2 (oversight, board updates)
- **Engineer:** 0.5 (support, bug fixes, iterations)
- **Operations:** 1.5 (dispute resolution, audits, metrics collection)
- **Product:** 0.3 (feedback analysis, feature prioritization)

**Total:** ~2.5 FTE

### Cost Estimates
- **Development (weeks 1-6):** 3 FTE × 6 weeks × $10K/week = $180K
- **Compliance/Security (weeks 7-9):** External counsel + security + accessibility = $25K
- **Pilot Operations (weeks 10-22):** 2.5 FTE × 14 weeks × $10K/week = $350K
- **Infrastructure/Tools:** $10K (database, email, certificates, hosting)
- **Contingency:** $35K (5% buffer)

**Total Budget:** ~$600K (one-time)

**Per-Verified-Hour Cost:** $600K / ~5,000 hours (pilot estimate) = ~$120/hour pilot, $3-5/hour at scale

---

## Success Criteria (Board Gate)

### Enrollment Floor (Week 9)
- ✅ At least 2 schools participating
- ✅ At least 10 nonprofits committed
- ✅ At least 50 students enrolled
- ⛔ If below 30: board considers pausing

### Completion Rate (Mid-pilot)
- ✅ Target: 70%+ of students complete committed hours
- ⚠️ If below 50%: indicates friction in UX or nonprofit participation

### Fraud/Error Detection (Continuous)
- ✅ Target: <2% of submissions flagged/rejected
- ⛔ If >5%: indicates verification process failure

### System Uptime (Continuous)
- ✅ Target: 99%+ availability
- ⛔ If <95%: pause enrollment until fixed

### Legal Compliance (Pre-enrollment gate)
- ✅ COPPA/FERPA review complete and clearance obtained
- ⛔ If blocking issues found: delay enrollment

---

## Critical Path (The Actual Sequence That Matters)

```
Day 1-3: Fix QA blockers (parallel to board meeting prep)
  ↓
Day 4-7: Complete QA testing (parallel to legal engagement)
  ↓
Day 8: Board presentation & vote
  ↓
IF APPROVED:
  Week 1: Architecture + legal kickoff
  ↓
  Week 2-3: COPPA/FERPA review (blocking) + engineering sprint 1 (parallel)
  ↓
  Week 3-6: Engineering sprints (core features)
  ↓
  Week 7-9: Security, accessibility, partner recruitment (parallel)
  ↓
  Week 9: Board checkpoint (legal must be done by now)
  ↓
  Week 10: Staff training + soft launch
  ↓
  Week 11-22: Pilot runs
  ↓
  Week 23: Post-pilot evaluation + board decision
```

**Critical dependency:** Legal review must complete before week 10 enrollment. If it slips, enroll at week 11.

---

## Integration with Existing Codebase

### Minimal Changes to Existing Code
The student service feature reuses 80% of existing infrastructure:

- ✅ Volunteer-hours system (extend, don't rebuild)
- ✅ Nonprofit dashboard (pattern for admin UIs)
- ✅ Firebase authentication (pattern for student/school auth)
- ✅ Privacy checks (extend privacy invariants for student data)
- ✅ Audit procedures (reuse audit table patterns)

### New Code Locations
```
frontend/src/pages/StudentService/
  - DiscoverPage.tsx (student opportunity search)
  - ServiceLogPage.tsx (student hour submission)
  - CertificatePage.tsx (student certificate view/download)
  - DashboardPage.tsx (school admin view)

daanaa_api.py
  - /api/student/* endpoints (new routes)
  - /api/school/* endpoints (new routes)
  - Extensions to /api/nonprofit/* (add student opportunity management)

database
  - New tables: student_accounts, student_service_logs, student_certificates
  - Extended tables: volunteer_hours (add student_id, parent_consent)
  - audit_service_records (tracking for fraud detection)
```

### No Breaking Changes
- All existing nonprofit features work as-is
- Volunteer hours system backward compatible
- Public API unchanged for discovery

---

## Next Immediate Steps

### TODAY (If QA blockers are fixed):
- [ ] Fix nonprofit_accounts linking (15 min)
- [ ] Test Firebase login → nonprofit dashboard (10 min)
- [ ] Fix authorized endpoints if still broken (1-2 hours)

### THIS WEEK:
- [ ] Complete authenticated QA tests (3 hours)
- [ ] Board presentation & vote
- [ ] If approved: legal counsel engagement kickoff

### NEXT WEEK (Post-board approval):
- [ ] Week 1 architecture sprint
- [ ] Coordinate external legal review
- [ ] UI design mockups

### WEEKS 2-6:
- [ ] Legal review + compliance documentation (weeks 2-3)
- [ ] Engineering sprints 1 & 2
- [ ] Security & accessibility reviews (weeks 7-9)
- [ ] Partner recruitment (weeks 7-9)

---

## Risk Mitigation

### Biggest Risk: Legal Review Delays
- **Mitigation:** Engage counsel THIS WEEK, not after board approval
- **Timeline:** Run legal review in parallel with board decision
- **Backup:** If COPPA/FERPA clearance not done by week 8, push pilot enrollment to week 11

### Second Risk: Partner Recruitment Slow
- **Mitigation:** Founder relationships in Houston are known/existing; start outreach by week 7
- **Timeline:** 3-5 schools + 20 nonprofits should commit by week 9
- **Backup:** If recruitment stalls at week 8, pause pilot until more partners confirmed

### Third Risk: Engineering Complexity Underestimated
- **Mitigation:** 6-8 week estimate is conservative; start with MVP (discover + log + verify + certificate)
- **Timeline:** Strip out reporting/audit dashboards from sprint 1 if needed
- **Backup:** If engineering slips to week 7, security review must be deferred to week 8-9

### Fourth Risk: Fraud/Verification Proves Hard
- **Mitigation:** Start with small pilot (max 5-10 students per nonprofit); audit frequently
- **Timeline:** Weekly spot-checks during weeks 11-22
- **Backup:** If fraud >5%, pause new student enrollments until process is fixed

---

## Go/No-Go Decision Framework

### GO (Proceed to Full Pilot)
- ✅ Board approves
- ✅ COPPA/FERPA clearance obtained
- ✅ 3+ schools committed
- ✅ 15+ nonprofits committed
- ✅ 50+ students enrolled by week 10
- ✅ Security review passes (no critical issues)

### NO-GO (Pause or Discontinue)
- ⛔ Legal review surfaces blocking compliance issues
- ⛔ Partner recruitment stalls (fewer than 2 schools or 10 nonprofits by week 9)
- ⛔ Security review finds critical vulnerabilities
- ⛔ Student enrollment below 30 by week 15 (board decides)
- ⛔ Fraud incidents >5% of submissions

---

## Sign-Off

This plan is ready to execute immediately upon:
1. ✅ QA blockers fixed (nonprofit account linking + authorized endpoints working)
2. ✅ Board approval (expected 7-0 vote)
3. ✅ Legal counsel engagement (coordinate this week)

**Owner:** Founder  
**Timeline:** 23 weeks total (9-week prep + 14-week pilot)  
**Expected Launch:** Week 10 (early Q4 2026)  
**Expected Completion:** Week 23 (late Q4 2026)  
**Board Decision:** End of Week 23 (expand, modify, or discontinue)
