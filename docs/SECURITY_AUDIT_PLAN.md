# Security Audit Plan: Profile Contexts & Event System

**Requested:** 2026-07-23  
**Timeline:** 2 weeks (parallel to pilot rollout)  
**Status:** Non-blocking (pilot can start while audit runs)

---

## Scope

### Profile Contexts
- [ ] Firebase UID masking verification (non-leads see "user_###")
- [ ] Cross-context authorization checks (no data leakage between contexts)
- [ ] Role-based access control enforcement (Lead/Support/Member/Viewer boundaries)
- [ ] Invitation token expiry & invalidation (14-day window)
- [ ] Wallet/donation data isolation (verify no exposure)

### Event Discovery & Claiming
- [ ] Event claiming workflow (email verification security)
- [ ] Nonprofit authentication (EIN-based ownership)
- [ ] Volunteer hour submission validation
- [ ] Audit log integrity (tamper detection)
- [ ] Intent signal privacy (no donor tracking)

### API Integration
- [ ] Firebase token validation on all protected routes
- [ ] Authorization header enforcement
- [ ] Input validation (Zod schemas on all endpoints)
- [ ] Error message information leakage (no sensitive details)
- [ ] Rate limiting / DDoS protection

### Data Privacy
- [ ] No wallet data in volunteer context tables
- [ ] No donation history exposed via event APIs
- [ ] Audit logs don't contain sensitive personally identifiable information
- [ ] Database query access control (no raw SQL injection vectors)

---

## Methodology

1. **Code Review** (3 days)
   - Read all new API endpoints in daanaa_api.py
   - Verify Zod validators on request bodies
   - Check authorization decorators on protected routes

2. **Data Flow Analysis** (2 days)
   - Trace how volunteer data flows from submission → audit log
   - Verify wallet data is never joined with event/volunteer tables
   - Check database queries for injection vulnerabilities

3. **Integration Testing** (5 days)
   - Test UID masking: non-lead users can't see full UIDs
   - Test cross-context isolation: Context A member can't see Context B data
   - Test role hierarchy: Member can't invite new members, Support can
   - Test invitation expiry: 14-day token expires, becomes invalid

4. **Penetration Testing** (3 days)
   - Attempt to forge Firebase tokens
   - Attempt unauthorized role escalation
   - Attempt to bypass volunteer hour approval
   - Attempt to access other org's claimed events

5. **Report & Remediation** (2 days)
   - Document findings (severity levels)
   - Prioritize fixes
   - Implement critical/high issues before broad launch
   - Log findings in DECISIONS.md

---

## Success Criteria

✅ **PASS:** No critical or high-severity findings  
✅ **PASS:** All PII properly masked/isolated  
✅ **PASS:** Authorization boundaries enforced  
✅ **PASS:** No data leakage between contexts/orgs  

🟡 **MAYBE:** Medium-severity findings logged, fix timeline agreed  
❌ **FAIL:** Critical findings → hold broad launch until fixed  

---

## Blockers for Broad Launch

**Critical (must fix):**
- Any data leakage to unauthorized users
- Any bypass of role-based access control
- Any ability to escalate privileges

**High (should fix before launch):**
- Information leakage in error messages
- Weak token validation
- Missing input validation

**Medium (can defer):**
- Minor UI/UX security concerns
- Edge case authorization scenarios
- Performance-related security (rate limiting tuning)

---

## Timeline

| Week | Phase | Status |
|------|-------|--------|
| Week 1 (Jul 23–30) | Code review + data flow analysis | **IN PROGRESS** |
| Week 1–2 (Jul 30–Aug 6) | Integration + penetration testing | **PENDING** |
| Week 2 (Aug 6–13) | Report + critical fixes | **PENDING** |

**Parallel:** Pilot rollout can begin immediately (non-blocking)

---

## Escalation

If critical findings discovered:
1. Disable feature flag immediately
2. Notify board
3. Fix and re-test before re-enabling
4. Document in DECISIONS.md

---

## Owned By

Security team / Akbar (founder sign-off)

**Next checkpoint:** 2026-07-30 (code review + data flow findings)
