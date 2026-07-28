# Phase 2 Implementation Plan — Frontend Integration

**Status:** Ready to begin  
**Baseline:** Phase 1 backend complete (16/16 tests passing)  
**Guardrails:** Founder-approved (PHASE2_GUARDRAILS.md)  

---

## Scope Overview

| Component | Scope | Tests | Effort |
|-----------|-------|-------|--------|
| IrsEligibilityContext component | New | Jest | 2h |
| OrganizationDetail.tsx | Update | E2E | 1h |
| SearchResults.tsx | Update | Unit | 1h |
| DirectoryPage.tsx | Update | Unit | 1h |
| DonateActionRow.tsx | Update | Unit/Snapshot | 2h |
| WalletPage.tsx | Update | Unit | 2h |
| HiddenGemsCarousel.tsx | Update | Unit | 1h |
| EventDiscovery.tsx | Update | Unit | 1h |
| PeerContextResponses.tsx | Update | Unit | 1h |
| API integration | Update daanaa_api.py | Unit | 2h |
| **TOTAL** | | | **14 hours** |

---

## Phase 2.1: React Component (`2 hours`)

### File: `frontend/src/components/IrsEligibilityContext.tsx`

```typescript
interface IrsEligibilityContextProps {
  status: 'verified' | 'unverified' | 'revoked' | 'unknown' | 'exception_possible';
  checkedAt?: string;  // ISO date
  sources?: string[];
  explanation?: string;
  recordedAt?: string; // For wallet: when Daanaa recorded this status
  organizationName?: string;
}

// Export components:
<IrsEligibilityBadge status={status} />
<IrsEligibilityWarning status={status} onDonate={() => {}} />
<IrsEligibilityDisclaimer recordedAt={recordedAt} />
```

**Responsibilities:**
- Render badge (status + icon)
- Show detailed explanation on hover
- Wallet disclaimer with recorded date
- Warning modal for unknown/unverified before donate

**Props:**
- status: one of 5 statuses
- checkedAt: when we verified (from API)
- recordedAt: when we recorded (for wallet)
- organizationName: for disclaimer context

**Tests:**
- Badge renders per status ✓
- Explanation appears on hover ✓
- Disclaimer includes recorded date ✓
- Warning modal shows for unknown/unverified ✓
- No false deductibility claims in copy ✓

---

## Phase 2.2: Search & Directory Filtering (`2 hours`)

### Files to Update

**`frontend/src/pages/SearchResults.tsx`**

```typescript
// Filter out revoked orgs from results
const filteredResults = results.filter(org => 
  org.irs_eligibility_status !== 'revoked'
);

// Show warning badge before results
<IrsEligibilityBadge status={org.irs_eligibility_status} />
```

**`frontend/src/pages/DirectoryPage.tsx`**

```typescript
// Same filtering logic
// Directory should exclude revoked organizations
```

**Tests:**
- Revoked orgs filtered from search ✓
- Unverified/unknown/verified shown ✓
- Count accurate after filtering ✓
- Direct URL search still finds revoked (bypass filter) ✓

---

## Phase 2.3: Donate Action & Suppression (`3 hours`)

### File: `frontend/src/components/DonateActionRow.tsx`

**Logic:**
```typescript
function DonateActionRow({ org }) {
  const status = org.irs_eligibility_status;
  
  if (status === 'revoked') {
    return <RevokedWarning org={org} />;
  }
  
  if (['unknown', 'unverified'].includes(status)) {
    return <WarningBeforeDonate org={org} onConfirm={goToDonate} />;
  }
  
  return <NormalDonateButton org={org} />;
}
```

**Revoked Handling:**
- Hide donate button
- Show: "IRS revocation record found"
- Link to org website

**Unknown/Unverified Handling:**
- Show warning modal before donation
- Let donor proceed (agency)
- Link to organization directly

**Tests:**
- Donate hidden for revoked ✓
- Warning appears for unknown/unverified ✓
- Donor can still proceed with warning ✓
- Copy mentions IRS Publication 526 ✓
- No false deductibility claims ✓

---

## Phase 2.4: Wallet Historical Entries (`2 hours`)

### File: `frontend/src/pages/WalletPage.tsx`

**Display per Entry:**
```
Organization: XYZ Charity
Status: Revoked (Sept 15, 2025)
Your Intent: June 1, 2025

---

Daanaa recorded this organization as not revoked on 
2025-06-01T12:00:00Z. This is not a tax receipt, a 
determination of deductibility, or proof that a donation 
occurred. See IRS Publication 526 for rules on charitable 
contributions.

[Visit Organization] [Remove from Wallet]
```

**Implementation:**
- Pull recordedAt from wallet entry (local storage or DB)
- Pull irs_eligibility_status from API
- Show IrsEligibilityDisclaimer component
- Display dates clearly (intent vs recorded vs revoked)

**Tests:**
- Disclaimer shows with recorded date ✓
- Revocation date shown if applicable ✓
- No claim of deductibility ✓
- Historical entries preserved (no retroactive changes) ✓

---

## Phase 2.5: Hidden Gems Filtering (`1 hour`)

### File: `frontend/src/components/HiddenGemsCarousel.tsx`

**Logic:**
```typescript
// Filter: only show hidden gems that are not revoked
const validGems = gems.filter(org => 
  org.irs_eligibility_status !== 'revoked'
);
```

**Tests:**
- Revoked orgs excluded from carousel ✓
- Count accurate ✓

---

## Phase 2.6: API Integration (`2 hours`)

### File: `daanaa_api.py`

**In Flask route handlers:**

```python
from scripts.irs_eligibility_helper import (
    initialize_helper,
    get_eligibility_fields,
    should_show_profile_publicly,
    should_show_donate_prompt
)

# At app startup:
initialize_helper(
    db_path="data/merit_registry.db",
    manifest_path="data/irs_authority/v6_eligibility/eligibility_manifest.json"
)

# In route handlers:
@app.route('/api/org/<ein>')
def get_org(ein):
    org = fetch_org(ein)
    
    # Add eligibility fields (additive)
    org.update(get_eligibility_fields(ein))
    
    return jsonify(org)

@app.route('/api/search')
def search():
    results = do_search()
    
    # Filter if needed (search shows all, UI filters)
    # OR filter here: results = [r for r in results if should_show_profile_publicly(r['EIN'])]
    
    # Add eligibility to each result
    for result in results:
        result.update(get_eligibility_fields(result['EIN']))
    
    return jsonify(results)
```

**Tests:**
- Eligibility fields added to responses ✓
- Status values correct (verified/revoked/etc) ✓
- Checked_at populated ✓
- Sources and explanation present ✓

---

## Phase 2.7: Testing (`1 hour`)

### Frontend Tests (Jest)

```bash
# Component tests
npm test -- IrsEligibilityContext.test.tsx

# Page tests
npm test -- SearchResults.test.tsx
npm test -- OrganizationDetail.test.tsx
npm test -- WalletPage.test.tsx

# E2E (optional, Cypress)
npm run cypress -- run (if available)
```

**Test Checklist:**
- Badge renders per status ✓
- Copy accuracy (no false claims) ✓
- Revoked orgs filtered from search ✓
- Donate button hidden for revoked ✓
- Warning modal appears for unknown/unverified ✓
- Wallet shows disclaimer + dates ✓
- Direct URLs still work ✓
- Scores visible regardless of eligibility ✓

### Backend Tests (pytest)

```bash
# Tests already pass from Phase 1
venv/bin/python -m pytest tests/test_v6_irs_eligibility.py -v
```

---

## Pre-Deployment Checklist

### Code Review (Diff Check)
- [ ] All 8 components changed reviewed
- [ ] No false deductibility claims in copy
- [ ] Revoked suppression correct
- [ ] Wallet disclaimer displays
- [ ] Direct URLs work
- [ ] Financial scores unaffected

### Testing
- [ ] Backend: 16/16 tests passing
- [ ] Frontend: All Jest tests passing
- [ ] No console errors in browser
- [ ] No TypeScript type errors (`npm run type-check`)

### Daily Gate
- [ ] Run: `bash scripts/v6_daily_operations_automated.sh`
- [ ] Preflight: PASS
- [ ] Validation: PASS
- [ ] Revocation: PASS
- [ ] IRS eligibility: PASS
- [ ] Integrity: PASS

### Final Approval
- [ ] Founder review of diff
- [ ] Founder review of copy/wording
- [ ] Founder approval to proceed
- [ ] Staging deploy for QA
- [ ] Production deploy (if QA passes)

---

## Rollback Plan

If issues found after deployment:

1. **Minor (copy/styling):** Update frontend only
2. **Major (logic/filtering):** 
   - Disable eligibility feature flag (if available)
   - Revert to Phase 1 (helper only, no UI changes)
   - Investigate root cause
   - Re-deploy with fix

**Safe revert:** All Phase 2 changes are additive. Removing `irs_eligibility_*` fields from API responses and skipping eligibility checks in UI returns to pre-Phase-2 state.

---

## Success Criteria

✅ **Complete when:**
- All 8 components updated with Phase 2 logic
- Frontend tests passing
- Backend tests passing
- Daily gate passing
- Copy review passed
- Founder approval obtained
- Final deployment completed

✅ **Working correctly when:**
- Revoked orgs hidden from search/directory
- Direct URLs still accessible
- Donate button suppressed for revoked
- Donate button shows warning for unknown/unverified
- Wallet shows disclaimer + dates
- No false deductibility claims anywhere
- Financial scores still visible
- Hidden gems exclude revoked

---

## Timeline

Assuming 14 hours of work + testing + review:

- **Day 1:** Components + Search/Directory (6h)
- **Day 2:** Donate action + Wallet (5h)
- **Day 3:** API + Testing + Review (6h)
- **Ready:** Diff for founder review before merge

---

## Ready to Proceed?

Phase 2 implementation plan complete. Awaiting:

1. ✓ Guardrails approved (PHASE2_GUARDRAILS.md)
2. → Explicit go-ahead to start Phase 2 frontend work
3. → Founder approval of diffs before build/deploy

**All Phase 1 deliverables:**
- ✅ Helper created and tested
- ✅ All 5 statuses working
- ✅ 16/16 tests passing
- ✅ IRS RP 2018-32 compliant
- ✅ Legal wording approved

**Next:** Begin Phase 2 frontend implementation
