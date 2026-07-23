# Board Briefing: Profile Contexts Feature

**Date:** 2026-07-23  
**Status:** Ready for deployment (pending board approval)  
**Decision Required:** Approve for production launch?

---

## What Is Profile Contexts?

A new feature allowing **nonprofit representatives** to create private workspaces for coordinating team giving and volunteer coordination.

### Key Capabilities

| Capability | Details |
|------------|---------|
| **Context Types** | Household, DAF (Donor-Advised Fund), Business, Other |
| **Member Roles** | Lead (full control), Support (invite/remove), Member (view), Viewer (read-only) |
| **Invitations** | Email-based, 14-day expiry, accept/reject workflow |
| **Privacy** | No wallet data exposed, no donation history, UIDs masked for non-leads |
| **Volunteer Integration** | Records volunteer hours, ties intent signals to actions |

---

## Why We're Building It

### Problem
- Nonprofit leaders need to coordinate team giving (board members, major donors, staff)
- No centralized way to track volunteer hours across a team
- Current Daanaa is donor-centric; no org-rep accounts

### Solution
- Private contexts for nonprofits to manage their team
- Volunteer hour tracking + approval workflow
- Volunteer-to-giving funnel (see who volunteered, then gave)

### Strategic Fit
- Moves Daanaa from "discovery platform" → "engagement platform"
- Enables nonprofit-leader features (Phase 2 of roadmap)
- Non-revenue feature (no donor data, no financial exposure)

---

## Technical Details

### What's Built
- ✅ Backend API (7 endpoints, 5 defects fixed)
- ✅ Frontend UI (6 React components, 310+ test cases)
- ✅ Invitation workflow (3-step: invite → pending → accept)
- ✅ Role-based access control (4 levels)
- ✅ Firebase authentication

### Data Safety
- ✅ No wallet/donation history exposed
- ✅ UID masking (non-leads see "user_###")
- ✅ Volunteer hours isolated from donor data
- ✅ Intent signals (volunteer → action tracking) complies with privacy invariants

### Feature Flag
- Default: **DISABLED in production** (`VITE_ENABLE_PROFILE_CONTEXTS=false`)
- Can be toggled on/off without redeployment
- Code ships ready but invisible to users

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| New account type complexity | Medium | Limited to nonprofit reps only, role-based access |
| Data privacy (mixing org data + volunteer) | High | Volunteer data never exposed to donors, separate tables |
| Incomplete volunteer hours data | Low | Honors volunteer data as "signals," not authoritative |
| Adoption (if orgs don't use it) | Low | Feature flag allows easy disable; no core platform impact |

---

## Board Decision Points

**Approve for Production Launch?**

✓ **Yes** → Deploy code (flag disabled), enable for pilot orgs once board approves  
✗ **No** → Hold deployment, request changes  
⏸ **Maybe** → Deploy code (flag disabled), revisit enabling after [specific gate]

---

## Next Steps (If Approved)

1. **Deploy code to production** (feature flag disabled)
2. **Select pilot orgs** (5–10 nonprofit partners for beta)
3. **Enable flag for pilots** (`VITE_ENABLE_PROFILE_CONTEXTS=true` in pilot environment)
4. **Monitor volunteer flows** (track adoption, data quality)
5. **Board gate before broad launch** (review pilot results)

---

## Questions for Board

1. Does this align with nonprofit-leader roadmap strategy?
2. Are we comfortable mixing volunteer + giving data (even isolated)?
3. Should we pilot with specific nonprofit types (e.g., health, education)?
4. Is there a launch timeline you'd prefer?

---

**Recommendation:** Approve for production (code only, flag disabled). Pilot phase allows risk-managed validation before broad launch.
