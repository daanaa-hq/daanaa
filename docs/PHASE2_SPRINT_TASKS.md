# Phase 2 Sprint Tasks (Revised)

**Status:** Ready to execute  
**Total Effort:** ~50 hours (revised down from 70h — infrastructure already exists)  
**Start Date:** 2026-07-08 (Week 2, post-launch stabilization)

---

## Sprint 1: Dashboard Re-enablement (10 hours)

**Why first:** Unblocks volunteer hours feature, enables nonprofit engagement

### Task 1.1: Re-enable frontend dashboard routes (2h)
- [ ] Uncomment `NonprofitDashboardPage` import in `App.tsx`
- [ ] Add `/nonprofit/dashboard/:ein` route back
- [ ] Wire up `navigateWithToken(ein, 'dashboard')` in `MyOrgsPage.tsx`
- [ ] Test: navigate from my-orgs → dashboard

**Files:**
- `frontend/src/App.tsx`
- `frontend/src/pages/nonprofit/MyOrgsPage.tsx`
- `frontend/src/pages/nonprofit/NonprofitDashboardPage.tsx` (already exists)

### Task 1.2: Connect portal token API (2h)
- [ ] Update `getPortalToken()` in `frontend/src/data/api.ts` to call `/api/claim/portal-token?ein={ein}`
- [ ] Parse response: `{ein, token, verification_url}`
- [ ] Pass token to dashboard component
- [ ] Test: verify token flows from my-orgs → dashboard

**Verification:**
- Portal token endpoint already exists: `GET /api/claim/portal-token?ein=360822808`
- Returns opaque token for dashboard access

### Task 1.3: Implement dashboard stats page (4h)
- [ ] Create `NonprofitDashboard.tsx` component (or use existing if present)
- [ ] Display:
  - Org name + EIN
  - Total revenue (last 3 years)
  - Peer financial context (percentile + tier)
  - Mission statement (editable)
  - Website URL (linked)
- [ ] Add edit button → `/claim/edit?ein={ein}&token={token}`

**Data sources:**
- Org detail: `/api/org/{ein}` (already returns all needed fields)
- Claim status: Firebase auth (already verified)

### Task 1.4: Test full flow (2h)
- [ ] Nonprofit: sign in with Google
- [ ] View my-orgs
- [ ] Click "manage dashboard" → portal token call
- [ ] Dashboard renders org stats
- [ ] Click "edit profile" → claim editor

---

## Sprint 2: Volunteer Hours Collection (12 hours)

**Why second:** Data collection readiness, powers volunteer engagement  
**Data:** Table exists (`volunteer_events`), zero rows currently

### Task 2.1: Nonprofit volunteer event submission (4h)
- [ ] Create form: date, hours, volunteer name, email/phone, role
- [ ] Endpoint: `POST /api/nonprofit/{ein}/volunteer/submit` (new)
  - Requires: Firebase auth + claim ownership
  - Returns: `{claim_code: "VOL-XYZ123"}`
- [ ] Send volunteer an email: "Here's your claim code: VOL-XYZ123"
- [ ] Nonprofit sees submission confirmation

**Data model:**
- `volunteer_events` table (exists, empty)
- Fields: ein, event_date, hours, volunteer_name, volunteer_email, volunteer_phone, role, claim_code

### Task 2.2: Volunteer claim flow (4h)
- [ ] Frontend: `/volunteer/submit?code=VOL-XYZ123`
- [ ] Form: volunteer verifies email/phone + name
- [ ] Endpoint: `POST /api/volunteer/claim` → writes to `org_volunteer_attestations`
- [ ] Confirmation: "Hours claimed! Your nonprofit will review and approve."

**Data model:**
- `org_volunteer_attestations` table (exists, empty)
- Fields: ein, volunteer_id, hours, event_date, status (pending/approved/rejected), notes

### Task 2.3: Nonprofit approval dashboard (2h)
- [ ] Dashboard shows "Pending Hours Approvals" widget
- [ ] List: volunteer name, hours, date, status
- [ ] Action: bulk approve/reject with optional notes
- [ ] Saves to database + sends email to volunteer

### Task 2.4: Test end-to-end (2h)
- [ ] Nonprofit submits volunteer event
- [ ] Volunteer receives email with claim code
- [ ] Volunteer claims hours via link
- [ ] Nonprofit sees pending approval
- [ ] Nonprofit approves
- [ ] Both parties get confirmation emails

---

## Sprint 3: Guild & Member Benefits (15 hours)

**Why third:** Partner/vendor relationship management

### Task 3.1: Guild data model (3h)
- [ ] Create tables:
  - `guild` — vendor info (name, slug, website, tier)
  - `guild_membership` — org ↔ guild links
  - `guild_benefits` — features per tier
- [ ] Load pilot data: 10 partners (free/pro/enterprise)
- [ ] Test: query guild memberships for an org

**Tables:**
```sql
CREATE TABLE guild (
  guild_id INTEGER PRIMARY KEY,
  name TEXT UNIQUE,
  slug TEXT UNIQUE,
  website TEXT,
  logo_url TEXT,
  created_at TIMESTAMP
);

CREATE TABLE guild_membership (
  ein TEXT PRIMARY KEY,
  guild_id INTEGER,
  tier TEXT, -- free, pro, enterprise
  joined_at TIMESTAMP,
  FOREIGN KEY(guild_id) REFERENCES guild(guild_id)
);

CREATE TABLE guild_benefits (
  benefit_id INTEGER PRIMARY KEY,
  guild_id INTEGER,
  tier TEXT,
  feature_name TEXT,
  description TEXT,
  FOREIGN KEY(guild_id) REFERENCES guild(guild_id)
);
```

### Task 3.2: Frontend: guild profile display (4h)
- [ ] Add guild section to org detail page
- [ ] Show: guild name, tier, benefits list
- [ ] Badge on org card (if member)
- [ ] Link to `/guild/:slug` page

### Task 3.3: Guild landing pages (4h)
- [ ] `GET /guild/:slug` — guild overview
  - Partner info, member list (first 50)
  - Benefits breakdown by tier
  - "Join as a member" CTA (links to partner signup)
- [ ] Partner can claim their guild page (like orgs claim their profile)

### Task 3.4: Seed data (2h)
- [ ] Load 10 pilot partners (TBD which ones)
- [ ] Assign free tier to all initially
- [ ] Verify UI renders correctly
- [ ] Test: `/guild/daanaa-partners`, `/org/123456789` shows badge

### Task 3.5: Test (2h)
- [ ] Org detail shows guild + benefits
- [ ] Guild page renders member list
- [ ] Badges appear on org cards
- [ ] Partner login + edit guild page

---

## Sprint 4: Donation Letter Generation (Blocked by Legal)

**Status:** ⏸️ BLOCKED — awaiting attorney review of IRS §170(f)(8)

**What's needed:**
1. Attorney sign-off on letter template
2. Nonprofit acceptance of liability (indemnification)
3. Tax year + filing date validation from 990 data
4. PDF export + email delivery

**Effort:** 15h (after legal gates clear)

---

## Priority Queue

| Sprint | Feature | Effort | Status | Start |
|--------|---------|--------|--------|-------|
| **1** | Dashboard re-enablement | 10h | Ready | 2026-07-08 |
| **2** | Volunteer hours collection | 12h | Ready | After S1 |
| **3** | Guild/benefits system | 15h | Ready | Parallel with S2 |
| **4** | Donation letters | 15h | ⏸️ Blocked | Post-legal |

---

## Launch Week Monitoring (Concurrent)

While implementing Phase 2, monitor production:

### Daily (15 min)
- [ ] Check droplet error logs: `tail -f /opt/daanaa/logs/daanaa_api.log`
- [ ] Verify API health: `curl https://daanaa.org/api/stats`
- [ ] Check GPU batch completion: `ps aux | grep mission`

### Weekly (Thursday)
- [ ] Gather metrics:
  - Top 10 searches
  - Bounce rate by page
  - Avg response times (p50, p95, p99)
  - User feedback (email, chat)
- [ ] Review error logs for patterns
- [ ] Check database integrity

### Red Flags to Watch
- 500+ errors in logs → investigate immediately
- /api/stats latency > 3s → check cache
- GPU jobs failing → check llama-server health
- User complaints about specific orgs → check data quality

---

## Definition of Done

Each sprint is done when:
- [ ] All tasks completed and tested
- [ ] Code committed and deployed to droplet
- [ ] No regressions in existing features
- [ ] User can do the main flow (e2e test passes)
- [ ] Documentation updated

---

## Estimated Timeline

- **Sprint 1 (Dashboard):** 2026-07-08 → 2026-07-10 (3 days, 10h)
- **Sprint 2 (Volunteer hours):** 2026-07-11 → 2026-07-15 (5 days, 12h)
- **Sprint 3 (Guild):** 2026-07-15 → 2026-07-19 (5 days, 15h, concurrent with S2)
- **Phase 2 Complete:** 2026-07-19 (end of week)

---

**Last Updated:** 2026-07-04 10:00 UTC  
**Author:** Claude Code  
**Ready to execute:** Yes
