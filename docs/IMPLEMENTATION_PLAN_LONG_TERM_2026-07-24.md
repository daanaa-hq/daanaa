# Long-Term Implementation Plan — Comprehensive Deployment

**Date:** 2026-07-24  
**Goal:** Build 212-endpoint API architecture right for long-term scalability  
**Timeline:** 12-16 hours intensive (can be split across 2-3 days)  
**Compliance:** STEWARDSHIP + PRIVACY-INVARIANTS + audit requirements

---

## Phase 1: Architecture & Compliance Review (2 hours)

### 1.1 Understand Endpoint Organization
- ✅ **daanaa_api.py:** 212 endpoints (home server, full-featured, high computation)
- ✅ **scripts/droplet_api.py:** 45 endpoints (production droplet, read-only, fast)
- ✅ **Gap:** 167 missing endpoints (need proxy routes)

### 1.2 Database Architecture (Non-Negotiable)
```
Home Database (merit_registry.db)
├── registry_enriched (org data)
├── v4_scores (computed rankings)
├── org_embeddings (semantic vectors)
└── volunteer_hours, volunteer_interest (user data)

Droplet Database (search.db)
├── org_fts (precomputed full-text index)
├── registry_enriched (org catalog)
└── zip_codes (reference data)

Constraint: Droplet CANNOT reference v4_scores/org_embeddings
Solution: Proxy missing endpoints to home backend
```

### 1.3 Compliance Gates (HARD REQUIREMENTS)
```
PRIVACY-INVARIANTS:
  1. No email/volunteer-email in logs
  2. Interest signals use sendBeacon (untracked)
  3. Volunteer data ISOLATED from giving data
  4. No third-party trackers in email links
  
STEWARDSHIP (Principle 2 - Privacy):
  1. Donor privacy protected (no tracking)
  2. Email notifications only for actions they initiated
  3. No exposure of giving activity
  
STEWARDSHIP (Principle 3 - Evidence-based):
  1. Interest signals = anonymous workflow signals
  2. No inference about donors from volunteer data
  
DATA CLASSIFICATION:
  - Volunteer email: Tier 2 (sensitive PII)
  - Nonprofit email: Tier 1 (organizational)
  - Interest count: Tier 0 (public aggregate)
  - Volunteer hours: Tier 2 (with consent)
  - Giving wallet: Tier 2 (private, never exposed)
```

---

## Phase 2: Code Organization (3 hours)

### 2.1 Refactor for Maintainability
```
Current: daanaa_api.py (12K+ lines, monolithic)
Problem: Hard to sync with droplet_api.py, difficult to maintain

Proposed: Modular structure
src/api/
├── core.py                          # Shared logic
├── endpoints/
│   ├── search.py                   # (native on droplet)
│   ├── organizations.py            # (native on droplet)
│   ├── interest.py                 # (proxy to home)
│   ├── claim.py                    # (proxy to home)
│   ├── email.py                    # (proxy to home)
│   ├── volunteer.py                # (proxy to home)
│   ├── portal.py                   # (proxy to home)
│   ├── admin.py                    # (proxy to home)
│   └── research.py                 # (proxy to home)
├── middleware/
│   ├── auth.py                     # Firebase auth validation
│   ├── audit.py                    # Audit logging (compliant)
│   └── proxy.py                    # Smart proxy routing
└── config.py                       # Environment-specific settings

scripts/
├── droplet_api.py                  # Production (imports from src/)
└── daanaa_api.py                   # Local (imports from src/)
```

### 2.2 Deployment Manifest (Source of Truth)
```yaml
# deployment_manifest.yaml
version: "1.0"
last_updated: 2026-07-24

environments:
  production_droplet:
    api_file: scripts/droplet_api.py
    database: /data/precompute/v1/search.db
    role: read_only_catalog
    
  home_server:
    api_file: daanaa_api.py
    database: data/merit_registry.db
    role: full_featured

endpoints:
  # Format: path: {type: native|proxy, deployed: bool, compliance: [invariant IDs]}
  
  /api/search:
    type: native
    deployed: true
    priority: critical
    
  /api/interest:
    type: proxy
    deployed: false
    priority: critical_for_pilot
    compliance: [privacy_invariants_2, privacy_invariants_5]
    requires: [audit_logging, Firebase_auth]
    
  /api/claim/*:
    type: proxy
    deployed: false
    priority: critical_for_pilot
    compliance: [stewardship_3, stewardship_7]
    requires: [Firebase_auth, audit_logging, EIN_verification]
    
  /api/email/*:
    type: proxy
    deployed: false
    priority: critical_for_pilot
    compliance: [privacy_invariants_1, privacy_invariants_2]
    requires: [NO_EMAIL_LOGGING, sendBeacon_only]
    
  /api/volunteer/*:
    type: proxy
    deployed: false
    priority: high_for_pilot
    compliance: [privacy_invariants_3, privacy_invariants_4]
    requires: [data_isolation, audit_logging]
```

---

## Phase 3: Implement Missing Endpoints (4 hours)

### 3.1 Critical for Pilot (60 endpoints)
```python
# Proxy routes to add to scripts/droplet_api.py

# ===== INTEREST SIGNALS =====
@app.route('/api/interest', methods=['GET', 'POST', 'DELETE'])
@app.route('/api/volunteer-interest/<ein>', methods=['GET', 'POST', 'DELETE'])
def interest_proxy(ein=None):
    """Volunteer interest signals (anonymous, privacy-compliant)."""
    # COMPLIANCE: Privacy invariant #2 - use sendBeacon, never log email
    return _live_proxy(request.path)

# ===== CLAIM/OWNERSHIP =====
@app.route('/api/claim/<path:subpath>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@app.route('/api/claim', methods=['GET', 'POST'])
def claim_proxy(subpath=None):
    """Event ownership verification (requires Firebase auth + EIN validation)."""
    # COMPLIANCE: Stewardship #3 - evidence-based, #7 - independence
    # REQUIREMENT: Must audit all verification attempts
    return _live_proxy(request.path)

# ===== EMAIL/OUTREACH =====
@app.route('/api/email/<path:subpath>', methods=['GET', 'POST', 'PATCH'])
@app.route('/api/email', methods=['GET'])
def email_proxy(subpath=None):
    """Email notifications (NO EMAIL LOGGING, privacy-first)."""
    # COMPLIANCE: Privacy invariant #1 - NO logging, sendBeacon only
    # CRITICAL: Never log volunteer_email or email content
    return _live_proxy(request.path)

# ===== VOLUNTEER MANAGEMENT =====
@app.route('/api/volunteer/<path:subpath>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@app.route('/api/volunteer', methods=['GET'])
def volunteer_proxy(subpath=None):
    """Volunteer profiles and hour tracking (DATA ISOLATED from giving)."""
    # COMPLIANCE: Privacy invariant #3 - NO cross-linking with wallet
    # REQUIREMENT: Volunteer data ≠ giving wallet data (strict separation)
    return _live_proxy(request.path)

# ===== NONPROFIT PORTAL =====
@app.route('/api/portal/<path:subpath>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@app.route('/api/portal', methods=['GET', 'POST'])
def portal_proxy(subpath=None):
    """Nonprofit event/volunteer management dashboard."""
    return _live_proxy(request.path)
```

### 3.2 Audit Logging (Compliant)
```python
# Must log without exposing PII

def audit_event(event_type, data):
    """Log event for compliance, never expose PII."""
    # ✓ DO log: event_type, timestamp, user_auth_level, result
    # ✓ DO log: EIN (public), nonprofit name (public)
    # ✗ DO NOT log: email addresses, email content, passwords
    # ✗ DO NOT log: volunteer names, volunteer hours details
    
    safe_record = {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "user_auth": request.headers.get('Authorization', 'unauthenticated'),
        "ein": data.get('ein'),  # OK - public
        # DO NOT include: volunteer_email, email_content, etc.
    }
    
    db.execute(
        "INSERT INTO audit_log (event, record) VALUES (?, ?)",
        (event_type, json.dumps(safe_record))
    )
```

---

## Phase 4: Testing (3 hours)

### 4.1 End-to-End Workflow Tests
```
Test: Volunteer Interest → Email → Nonprofit Claim
1. POST /api/interest (volunteer shows interest)
   ✓ Endpoint responds
   ✓ Interest recorded (no email logged)
   ✓ Audit log shows attempt (no PII)
   
2. Email triggered to nonprofit
   ✓ Email sent (async, no response wait)
   ✓ Email contains claim link
   ✓ NO volunteer email in logs
   
3. POST /api/claim/start (nonprofit initiates)
   ✓ Firebase auth required
   ✓ EIN verification initiated
   ✓ Audit log records attempt
   
4. Nonprofit verifies ownership
   ✓ Email verification succeeds
   ✓ EIN marked as claimed
   ✓ Audit log records verification
   
5. GET /api/claim/my-orgs (nonprofit dashboard)
   ✓ Returns claimed events
   ✓ Shows pending volunteer hours
   ✓ All data isolated from giving wallet
```

### 4.2 Compliance Tests
```
Test: Privacy Invariant Compliance
1. Interest signals
   ✓ No volunteer email in logs
   ✓ sendBeacon used (verify HTTP 200 with no content)
   ✓ No tracking pixels in emails
   
2. Data isolation
   ✓ Volunteer hours table separate from wallet
   ✓ No cross-query between volunteer_hours and giving_wallet
   ✓ Volunteer consent required to expose hours
   
3. Audit logging
   ✓ All claim attempts logged
   ✓ All auth failures logged
   ✓ NO PII in any log entry
```

---

## Phase 5: Deployment (2 hours)

### 5.1 Safe Deployment Strategy
```bash
1. Backup droplet_api.py to S3
2. Add proxy routes (60 endpoints)
3. Deploy via sync_droplet_api.sh
4. Run verification script (check all endpoints)
5. Run smoke tests (interest→claim workflow)
6. Run compliance check (privacy_check.sh passes)
7. Run audit review (log format verified)
8. Enable for pilot orgs only (feature flags)
```

### 5.2 Rollback Plan
```
If any test fails:
1. Restore backup from S3
2. Restart droplet API
3. Run verification again
4. Document failure + root cause
5. Fix in development, re-test, re-deploy
```

---

## Phase 6: Documentation (2 hours)

### 6.1 Architecture Documentation
- [ ] API routing diagram
- [ ] Database schema diagram
- [ ] Privacy compliance checklist
- [ ] Deployment runbook
- [ ] Monitoring & alerting setup

### 6.2 Operational Runbooks
- [ ] How to add a new endpoint
- [ ] How to verify compliance
- [ ] How to troubleshoot proxy latency
- [ ] How to audit logs for security issues

---

## Success Criteria

### Must Have ✅
- [ ] All 212 endpoints accounted for (native or proxied)
- [ ] Privacy invariants verified (privacy_check.sh passes)
- [ ] Audit logging compliant (no PII in logs)
- [ ] Interest→email→claim workflow end-to-end tested
- [ ] Data isolation verified (volunteer ≠ giving data)

### Should Have 📋
- [ ] Deployment manifest YAML complete
- [ ] Modular code structure in place
- [ ] Documentation complete
- [ ] Monitoring + alerting configured

### Nice to Have 🎯
- [ ] Performance tested (proxy latency < 200ms)
- [ ] Load tested (handles 1000 concurrent interests/day)
- [ ] Scaling plan for multiple droplets

---

## Timeline Options

**Option A: Intensive (12 hours in one day)**
- Start: 2026-07-24 10:00 AM
- End: 2026-07-24 10:00 PM
- Done: All endpoints live, tested, deployed

**Option B: Distributed (3-4 hours per day)**
- Day 1: Phases 1-2 (architecture, code org)
- Day 2: Phase 3 (implement endpoints)
- Day 3: Phases 4-5 (test, deploy)
- Day 4: Phase 6 (documentation)

**Recommendation:** Option A intensive session
- Build momentum with parallel work
- All knowledge in context
- Full testing before going live
- Cleaner git history (one comprehensive commit)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Database conflicts | Test with both DB paths before deploy |
| Privacy leak in logs | Compliance tests verify no PII |
| Broken workflows | E2E tests cover all critical paths |
| Proxy latency | Performance tests validate <200ms |
| Rollback needed | S3 backup + verification script |

---

## Next Steps

1. **Approve this plan** ← You are here
2. **Start Phase 1** (2 hours) - Review architecture + compliance
3. **Parallelize Phase 2-3** (7 hours) - Code org + endpoint implementation
4. **Run Phase 4-5** (5 hours) - Test + deploy
5. **Document Phase 6** (2 hours) - Write runbooks

**Ready to begin?**

