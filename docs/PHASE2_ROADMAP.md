# Phase 2 Implementation Roadmap

## Dashboard Feature (Disabled for Phase 1 Launch)

**Current State:** Feature routes removed, API endpoint disabled (501), UI buttons removed

### What's Missing:

1. **Authentication Flow:** `POST /nonprofit/claim/<ein>/portal-token`
   - Requires: verified claim status + claim ownership proof
   - Issue: **No claim ownership verification system yet** (P0 BLOCKER)

2. **Portal UI:** `/nonprofit/dashboard/<ein>`
   - Org stats: total revenue, peer rank, mission quality score
   - Settings: profile edit, donation link management
   - Volunteer tracking: hours approved, pending approvals
   - Letter generation: donor list, template preview

3. **Backend Endpoints:**
   - `GET /api/nonprofit/<ein>/dashboard` (org stats + health signals)
   - `POST /api/nonprofit/<ein>/volunteer-bulk` (bulk approve hours)
   - `POST /api/nonprofit/<ein>/letters/generate` (IRS §170(f)(8) compliance)

### Dependencies:

- ✅ Claim system exists (in `org_claims` table, versioned attestations)
- ❌ **Claim ownership verification** (missing — can't prove "you own this EIN")
- ❌ Donation letter generation (needs attorney review first)
- ❌ Volunteer event data (zero rows currently)

### Implementation Effort:

**40 hours** (blocked on claim verification, P0 blocker for dashboard)

**Next step:** Implement claim ownership verification:
- Email domain matching (org website + claimed email domain)
- Form 990 Schedule O name match
- PIN-based verification (letter mailed to org address)

---

## Volunteer Events & Attestation (P1)

**Current State:** Empty (0 rows in `volunteer_events` table)

### What's Missing:

1. **Event ingestion:** `POST /nonprofit/volunteer/submit`
   - Nonprofit enters: event date, hours, volunteer name, role
   - System generates unique claim code (e.g., VOL-XYZ123)
   - Sends code to volunteer (email or SMS)

2. **Volunteer claim flow:** `GET /volunteer/submit?code=XYZ123`
   - Volunteer verifies identity (email/phone)
   - Claims hours (writes to `org_volunteer_attestations`)
   - Nonprofit gets notification for bulk approval

3. **Nonprofit approval:** Dashboard shows pending attestations
   - Bulk approve/reject with notes
   - Generates attestation certificates (optional)

### Database Schema:

Already exists:
- `volunteer_events` (empty)
- `org_volunteer_attestations` (empty)
- `volunteer_hours_index` (for search/filter)

### Implementation Effort:

**20 hours** (straightforward data collection + email flow)

---

## Guild & Member Benefits (P1)

**Current State:** Empty (no guild data loaded, pages show "No partners")

### What's Missing:

1. **Guild data model:** Load partner orgs + benefits per tier
   - Free tier: nonprofit listed, basic badge
   - Pro: featured in /partners, expanded profile
   - Enterprise: custom landing page, API access

2. **Frontend Pages:**
   - `/member/benefits` — what your guild offers
   - `/guild/:slug` — guild overview + member list
   - Badge system in org cards

3. **Database Tables:**
   - `guild` — vendor/partner orgs
   - `guild_membership` — org ↔ guild relationship
   - `guild_benefits` — tier-based features

### Implementation Effort:

**15 hours** (data modeling + UI components + seed data)

---

## Donation Letter Generation (P2, Legal Blocker)

**Status:** Waiting on attorney review of IRS §170(f)(8) compliance

### What's Needed:

1. **Legal clearance:**
   - Form 990 Schedule O attestation approach
   - Daanaa's role in letter generation (guidance vs. certification)
   - Liability indemnification language

2. **Technical implementation:**
   - Letter template (HTML + PDF export)
   - Donor data handling (never stored in Daanaa)
   - Tax year + filing date validation
   - Nonprofit's letterhead option

3. **Before shipping:**
   - Attorney sign-off on template
   - Nonprofit acceptance of liability
   - Donor privacy statement

### Effort:

**Blocked** (awaiting legal review + attorney memo)

**Estimated:** 15 hours (after legal gates clear)

---

## Priority Queue for Phase 2

| Priority | Feature | Effort | Blocker | Notes |
|----------|---------|--------|---------|-------|
| **P0** | Claim ownership verification | 20h | ❌ Gates dashboard | Implement PIN/domain/Schedule O matching |
| **P1** | Volunteer events data collection | 20h | ✅ None | Straightforward ingestion + approval |
| **P1** | Guild/benefits data loading | 15h | ✅ None | Vendor relationship management |
| **P2** | Donation letter generation | 15h | ⚠️ Legal review | IRS §170(f)(8) compliance gate |

---

## Test Plan (Post-Phase 1)

- [ ] Claim verification: test all three ownership proof methods
- [ ] Volunteer flow: e2e from nonprofit entry → volunteer claim → approval
- [ ] Guild membership: load 10 pilot partners, verify UI rendering
- [ ] Letter generation: legal review + nonprofit acceptance workflow

---

**Last Updated:** 2026-07-04 09:30 UTC  
**Author:** Claude Code audit session  
**Status:** Ready for Phase 2 sprint planning
