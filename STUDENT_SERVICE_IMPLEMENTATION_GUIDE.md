# Student Service Implementation Guide
**Status:** Week 1 Design Complete → Ready for Sprints 1-2 (Weeks 2-6)  
**Target Launch:** Week 10 (Houston Pilot)  
**Architecture:** Extends existing volunteer-hours infrastructure  

---

## Quick Start: What to Build

### Phase 1 Architecture (✅ COMPLETE)

- ✅ Database schema (10 new tables, 2 extended tables)
- ✅ API specification (30+ endpoints)
- ✅ Frontend component structure (18 pages/components)
- ✅ Privacy & COPPA compliance framework
- ✅ Integration points with existing code

### Files Ready to Reference

**Database:**
- `database/migrations/024_student_service_tables.sql`

**API:**
- `STUDENT_SERVICE_API_SPEC.md` (complete endpoint list)

**Frontend:**
- `frontend/src/pages/StudentService/STRUCTURE.md` (component structure)

**Compliance:**
- `DEVELOPMENT_PLAN_STUDENT_SERVICE_WITH_QA_FIXES.md` (legal gates, timelines)

---

## Engineering Sprint 1 (Weeks 2-4)

### Backend: Core API Endpoints

**Owner:** Backend engineer (1 FTE)  
**Duration:** 3 weeks  
**Deliverable:** Full REST API with core features

#### Week 2: Foundation
```
1. Database migration
   - Run: database/migrations/024_student_service_tables.sql
   - Verify: sqlite3 data/merit_registry.db ".tables" | grep student

2. Authentication
   - Extend Firebase integration for students (Google OAuth)
   - Create student login endpoint (/auth/student/login)
   - Validate COPPA age requirements in auth flow

3. API scaffolding
   - Create /api/student/* blueprint routes
   - Create /api/school/* blueprint routes
   - Create /api/nonprofit/student-hours/* endpoints
```

#### Week 3: Discovery & Service Log
```
1. Student opportunities
   - GET /api/student/opportunities (search, filter, paginate)
   - POST /api/student/opportunities/{id}/enroll
   
2. Service log submission
   - GET /api/student/service-log (view submissions)
   - POST /api/student/service-log/submit (create new)
   - PUT /api/student/service-log/{id} (edit unapproved)
   - DELETE /api/student/service-log/{id} (delete unapproved)
   
3. Fraud detection
   - Duplicate detection (same student + org + date)
   - Outlier flagging (hours > 16 in one submission)
   - Database queries optimized with indexes
```

#### Week 4: Approval & Certificates
```
1. Nonprofit supervisor endpoints
   - GET /api/nonprofit/{ein}/student-hours/pending
   - POST /api/nonprofit/{ein}/student-hours/{id}/approve
   - POST /api/nonprofit/{ein}/student-hours/{id}/reject
   
2. Certificate generation
   - GET /api/student/certificate (fetch certificate data)
   - POST /api/student/certificate/generate (create from approved hours)
   - GET /api/verify/{certificate_number} (public verification)
   
3. Student profile & account
   - GET /api/student/profile
   - PUT /api/student/profile (limited fields)
   - POST /api/student/data-export
   - DELETE /api/student/account
```

### Frontend: Core Pages

**Owner:** Frontend engineer (1 FTE) + Designer (0.3 FTE)  
**Duration:** 3 weeks  
**Deliverable:** User-facing discovery, logging, and certificate pages

#### Week 2: Setup & Discover
```
1. Project structure
   - Create frontend/src/pages/StudentService/ directory
   - Setup TypeScript types (student.ts, opportunity.ts, service-log.ts)
   - Create API client wrapper (studentApi.ts)
   - Setup context & hooks structure

2. Discovery page
   - Build OpportunitySearch component
   - Build OpportunityCard component
   - Implement search/filter/sort logic
   - Test with real API data

3. Opportunity details
   - Build OpportunityDetailModal
   - Implement "Enroll" workflow
   - Add to DiscoverPage
```

#### Week 3: Service Log
```
1. Service log pages
   - Build ServiceLogPage component
   - Build ServiceLogForm (submit hours form)
   - Build ServiceLogList (display submissions)
   - Build ServiceLogItem (individual entry with actions)
   
2. Service log forms
   - Date picker (service date)
   - Organization selector (dropdown search)
   - Hours input (validates 0.5-24)
   - Activity description (textarea)
   - Supervisor name (optional)
   
3. Service log interactions
   - Edit unapproved entries (inline form)
   - Delete unapproved entries (with confirmation)
   - Filter by status/organization
   - Status badges (submitted/approved/rejected)
```

#### Week 4: Certificate & Polish
```
1. Certificate page
   - Build CertificatePage component
   - Build CertificateViewer component
   - Display certificate details (hours, orgs, issue date)
   - Build PDF download button
   
2. Profile page
   - Build ProfilePage component
   - Build StudentProfileForm (limited editable fields)
   - Build EnrollmentSummary (stats card)
   - Add privacy notice explaining data handling
   
3. Polish & testing
   - Form validation (all inputs)
   - Error messaging (clear, actionable)
   - Loading states (spinners)
   - Empty states (no opportunities, no logs, etc)
   - Mobile responsiveness
```

---

## Engineering Sprint 2 (Weeks 5-6)

### Backend: Advanced Features

**Owner:** Backend engineer (1 FTE)  
**Duration:** 2 weeks  
**Deliverable:** Disputes, school admin endpoints, audit trail

#### Week 5: Disputes & Mediation
```
1. Dispute workflow
   - POST /api/student/disputes (file dispute)
   - GET /api/student/disputes (view disputes)
   - GET /api/school/{ein}/disputes (school admin view)
   - POST /api/school/{ein}/disputes/{id}/resolve (school mediation)
   
2. School admin endpoints
   - POST /api/school/{ein}/students/enroll (enroll student)
   - GET /api/school/{ein}/students (view all students)
   - Dispute resolution flow
   
3. Nonprofit opportunity management
   - POST /api/nonprofit/{ein}/opportunities (create opportunity)
   - GET /api/nonprofit/{ein}/opportunities (view opportunities)
   - PATCH /api/nonprofit/{ein}/opportunities/{id} (edit opportunity)
```

#### Week 6: Audit & Admin
```
1. Audit trail
   - Implement student_audit_log inserts (all actions)
   - Hash IP addresses (never store full IP)
   - Implement GET /api/admin/student-service/audit-log
   
2. Fraud detection
   - GET /api/admin/student-service/flagged-records
   - Duplicate detection logic
   - Outlier detection (hours > 16)
   - Admin review & flagging endpoints
   
3. Certificate revocation
   - POST /api/admin/student-service/certificate/{id}/revoke
   - Revocation notifications (to student)
   - Archive revoked records
```

### Frontend: Advanced Pages

**Owner:** Frontend engineer (1 FTE)  
**Duration:** 2 weeks  
**Deliverable:** Disputes, data management, full admin integration

#### Week 5: Disputes & Account
```
1. Dispute page
   - Build DisputePage component
   - Build DisputeForm component
   - Build DisputeTimeline (shows resolution progress)
   - Implement dispute filing workflow
   - Show school admin's decision/notes
   
2. Data management page
   - Build DataManagementPage component
   - Export data as JSON (GDPR/CCPA)
   - Delete account with confirmation modal
   - Add privacy/retention policy explanations
```

#### Week 6: Polish & QA
```
1. Complete frontend
   - All pages functional
   - All API integrations working
   - Error handling (show error messages)
   - Loading states (spinners, skeletons)
   - Empty states (no data, no results)
   
2. Firebase integration
   - Student login flow (Google OAuth)
   - Firebase token handling
   - Auto-logout on token expiration
   
3. QA & polish
   - Mobile responsiveness (test on actual devices)
   - Accessibility review (WCAG 2.2 AA)
   - Performance (Lighthouse audit)
   - Cross-browser testing
```

---

## Key Integration Points with Existing Code

### 1. Volunteer Hours Table Extension

**Existing:** `volunteer_hours` table already has:
- `id`, `nonprofit_ein`, `hours`, `submitted_at`, `status`
- `volunteer_name`, `volunteer_email`

**Extend with:**
```sql
ALTER TABLE volunteer_hours 
ADD COLUMN student_id TEXT REFERENCES student_accounts(student_id);
ADD COLUMN student_school_ein TEXT REFERENCES registry_enriched(ein);
ADD COLUMN parental_consent_given BOOLEAN DEFAULT 0;
```

**Effect:** Existing nonprofit volunteer endpoints work as-is; queries can filter by student_id to show only student submissions

---

### 2. Nonprofit Accounts Integration

**Existing:** `nonprofit_accounts` table for nonprofit staff login

**Extend with:**
```sql
ALTER TABLE nonprofit_accounts 
ADD COLUMN parent_school_ein TEXT REFERENCES registry_enriched(ein);
```

**Effect:** Nonprofit supervisors can supervise student hours from school-affiliated organizations

---

### 3. Firebase Authentication

**Existing:** Firebase used for nonprofit login (email/password)

**Extend with:**
- Google OAuth for students (same Firebase project)
- Student-specific custom claims (school_ein, age_group)
- Separate authentication flow (student/nonprofit/school routes)

**Code location:** Check `daanaa_api.py` lines 205-220 for existing Firebase verification logic

---

### 4. Privacy Checks Integration

**Existing:** `privacy_check.sh` runs pre-commit to block credential leaks

**Ensure new code:**
- Never logs full IP addresses
- Never logs student names/emails in plain text audit logs
- Never exposes student data in public API endpoints

---

## Testing Strategy

### Unit Tests (Write as you code)

**Backend:**
- Test each endpoint with valid/invalid inputs
- Test fraud detection (duplicates, outliers)
- Test authorization (supervisor can only approve own nonprofit's hours)
- Test data validation (hours, dates, emails)

**Frontend:**
- Test component rendering (with mocked API)
- Test form validation (hours input, date picker)
- Test filtering/sorting logic
- Test error states (API errors, validation errors)

### Integration Tests (End-to-end workflows)

**Critical paths:**
1. Discover → Enroll → Log → Approve → Certificate
2. Log → Reject → Dispute → School mediation → Resolve
3. Export data / Delete account

**Test with real API + database**

### Manual QA (Week 7)

**Student perspective:**
- Can login with Google OAuth
- Can find opportunities (search/filter works)
- Can log hours (form validates, submits)
- Can see status of submissions (approved/rejected/pending)
- Can download certificate
- Can file dispute if rejected
- Can export/delete data

**Nonprofit perspective:**
- Can see pending student hours
- Can approve/reject hours
- Can add supervisor notes
- Can publish opportunities

**School perspective:**
- Can enroll students
- Can mediate disputes
- Can view all students' progress
- Can access reports

---

## Deployment Strategy

### Week 7: Security & Compliance Review

**Before any deployment:**
- [ ] Security review (IP hashing, auth, authorization)
- [ ] WCAG 2.2 AA accessibility audit
- [ ] Privacy audit (no PII exposure, COPPA compliance)
- [ ] Load testing (handle 1000+ concurrent requests)

### Week 8: Staging Deployment

- Deploy to staging environment
- Run full QA test suite
- Test with real Firebase project
- Performance testing (API response times)

### Week 9: Production Deployment

- Zero-downtime deployment (feature flag: `ENABLE_STUDENT_SERVICE=false`)
- Gradual rollout (10% → 25% → 50% → 100% of traffic)
- Monitor error rates, latency, CPU/memory
- Have rollback plan ready

---

## Code Style & Standards

### Backend (Python/Flask)

Follow existing style in `daanaa_api.py`:
- Type hints for all function parameters/returns
- Docstrings for all endpoints (method, params, response)
- Snake_case for database columns and Python variables
- kebab-case for HTTP routes

### Frontend (TypeScript/React)

Follow existing style in `frontend/src/`:
- TypeScript interfaces for all data types
- PascalCase for components
- camelCase for functions/hooks/variables
- Tailwind CSS for styling (no custom CSS unless necessary)
- Radix UI for accessible components

### Database

Follow existing patterns:
- UPPERCASE for SQL keywords
- snake_case for table/column names
- TEXT for strings, DATE for dates, REAL for decimals
- NOT NULL for required fields
- Foreign keys with CHECK constraints
- Indexes on frequently queried columns

---

## Environment Variables

Add to `.env` or deployment config:

```bash
# Student service feature flag (off by default during pilot prep)
ENABLE_STUDENT_SERVICE=false

# Fraud detection thresholds
STUDENT_MAX_HOURS_PER_SUBMISSION=16
STUDENT_DUPLICATE_WINDOW_DAYS=0  # Same day only
STUDENT_OUTLIER_THRESHOLD_HOURS=16

# COPPA minimum age
COPPA_MINIMUM_AGE=13

# Certificate settings
CERTIFICATE_PDF_STORAGE=/data/certificates/  # Local storage only
CERTIFICATE_EXPIRATION_DAYS=730  # 2 years

# Dispute resolution timeline
DISPUTE_REVIEW_SLA_HOURS=72  # School reviews within 3 days
```

---

## Progress Tracking

### Week 2 Completion Checklist
- [ ] Database migration runs without errors
- [ ] Student Firebase auth working
- [ ] GET /api/student/opportunities endpoint returns data
- [ ] DiscoverPage component renders
- [ ] OpportunityCard component displays correctly

### Week 3 Completion Checklist
- [ ] POST /api/student/service-log/submit creates records
- [ ] Service log filtering by status works
- [ ] ServiceLogPage component functional
- [ ] Edit/delete unapproved logs work
- [ ] Fraud detection (duplicates) working

### Week 4 Completion Checklist
- [ ] Nonprofit approval endpoints working
- [ ] Certificates generate correctly
- [ ] CertificatePage renders certificate
- [ ] ProfilePage editable
- [ ] PDF download works

### Week 5 Completion Checklist
- [ ] Disputes can be filed and resolved
- [ ] School admin dashboard functional
- [ ] Data export/delete working
- [ ] Audit log recording all actions

### Week 6 Completion Checklist
- [ ] All frontend pages functional
- [ ] All API endpoints tested
- [ ] Mobile responsive (tested on devices)
- [ ] Accessibility audit passed
- [ ] Performance acceptable (API < 200ms)

---

## Common Pitfalls to Avoid

### 1. ⚠️ Don't Expose Student Data Publicly
- Verify endpoints (daanaa.org/verify) must NOT include student name/email
- Public API must never list student accounts
- Opportunity endpoints must not require authentication (discovery is public)

### 2. ⚠️ Don't Persist IP Addresses
- Log IP for fraud detection only
- Hash IP in audit trail (never store plain text)
- Delete raw IP logs after 7 days

### 3. ⚠️ Don't Let Nonprofits Contact Students Directly
- All supervisor-student communication goes through school admin
- Nonprofits can only contact supervisors, not students
- School is the intermediary

### 4. ⚠️ Don't Assume Parental Consent for All Students
- Check date of birth first
- Apply COPPA rules if under 13
- Collect parental consent before enrollment if required

### 5. ⚠️ Don't Create Duplicate Code
- Extend existing volunteer-hours endpoints where possible
- Reuse nonprofit supervisor approval logic
- Use existing authentication/authorization patterns

---

## Emergency Contacts

**If you get blocked:**
- Database issues → Check CLAUDE.md for database path
- API routing issues → Check daanaa_api.py line 8549+ for existing patterns
- Firebase issues → Check GOOGLE_APPLICATION_CREDENTIALS env var
- Frontend build issues → Check frontend/package.json for dependencies

---

## Questions to Ask Before Coding

1. **Should student service hours share `volunteer_hours` table or create separate `student_service_logs`?**
   - Answer: Both. New table for student-specific data; volunteer_hours extended for supervisor approval workflow

2. **How do we handle students who volunteer at multiple nonprofits?**
   - Answer: Multiple rows in student_service_logs, one per org. Certificate aggregates all.

3. **Can students edit submitted (but unapproved) hours?**
   - Answer: Yes. Can edit/delete while status='submitted'. Cannot edit after approval.

4. **What happens if a nonprofit supervisor approves false hours?**
   - Answer: Audit trail shows who approved. Random audits (5-10%) catch fraud. Student can dispute.

5. **How do we generate certificates?**
   - Answer: Automatically after pilot ends (week 22). Or manually on-demand. PDF generated locally, never CDN.

---

## Success Criteria for Complete Feature

- ✅ Students can discover opportunities
- ✅ Students can log hours
- ✅ Nonprofits can approve/reject hours
- ✅ Students get verified certificates
- ✅ Disputes can be filed and mediated
- ✅ All student data is private (not public)
- ✅ No student PII exposed in public endpoints
- ✅ Audit trail records all actions
- ✅ Mobile responsive and accessible (WCAG 2.2 AA)
- ✅ Performance acceptable (<200ms API response)
- ✅ Zero privacy/security issues in review
- ✅ Fraud detection working (duplicates, outliers)

---

**Ready to build?** Start with Week 1 → Week 2 → Week 3 progression.

Questions? See DEVELOPMENT_PLAN_STUDENT_SERVICE_WITH_QA_FIXES.md for full timeline and resources.
