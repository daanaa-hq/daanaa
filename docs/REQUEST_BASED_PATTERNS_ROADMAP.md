# Request-Based Patterns Across Daanaa — Design Roadmap

**Why:** The CPQ (Configure-Price-Quote-Confirm) workflow aligns with Stewardship principles and creates clearer, more explicit workflows than auto-push or batch processing.

**Principle:** Users actively *request* actions rather than having data auto-pushed or decisions auto-made. Creates audit trails, consent, and control.

---

## Current Implementation

✅ **Wallet Verification (Phase 2, proposed)**
- Volunteer requests verification → nonprofit verifies → hours locked
- Explicit, auditable, privacy-respecting

---

## High-Priority Patterns (Phase 3, Aug–Sep)

### 1. Board Volunteer Matching Requests

**Current problem:** Nonprofit posts "looking for volunteers," volunteers see signal, but flow is unclear. Who reaches out first? No formal request.

**Request-based model:**
```
Nonprofit posts: "Need grant writers (5–10 hrs/month)"
         ↓
Volunteer sees → clicks "I'm interested" → Creates request
         ↓
Request includes: volunteer skills, hours available, message
         ↓
Nonprofit sees "Jane Smith requests to volunteer"
         ↓
Nonprofit can: Accept → schedule interview, Decline → explain, Discuss → message back
         ↓
Status: Pending → Accepted (Jane invited to join) / Declined (with reason)
```

**Data model:**
```sql
CREATE TABLE volunteer_matching_requests (
  id UUID PRIMARY KEY,
  nonprofit_ein VARCHAR(50) NOT NULL,
  volunteer_email VARCHAR(255) NOT NULL,
  
  skills_offered JSON,        -- ["grant-writing", "communications"]
  hours_available VARCHAR(50), -- "5-10", "10-20", etc.
  volunteer_message TEXT,     -- "I've written 50+ grants..."
  
  status ENUM('pending', 'accepted', 'declined', 'withdrawn'),
  created_at TIMESTAMP,
  responded_at TIMESTAMP,
  response_message TEXT,      -- Why accepted/declined
  
  UNIQUE KEY (nonprofit_ein, volunteer_email)
);
```

**Stewardship alignment:**
- ✅ P2 (Privacy): Volunteer controls when they express interest
- ✅ P4 (Fairness): Small orgs can directly recruit; no algorithm favors large
- ✅ P5 (Don't weaponize): Explicit requests, not passive notifications

**Timeline:** Phase 3 (Sep 1), pairs with volunteer matching feature

---

### 2. Nonprofit Data Export Requests (Partner API)

**Current problem:** Vendors request org data; unclear approval flow; potential data leakage.

**Request-based model:**
```
Partner/vendor clicks: "Export nonprofit data"
         ↓
Form: Select orgs (by category/state), purpose, retention period
         ↓
Creates request: "Access 500 nonprofits for partnership outreach"
         ↓
Daanaa admin reviews:
  - Purpose aligns with policy (P7 independence, P2 privacy)
  - Retention period reasonable (auto-delete after X days)
  - Vendor not on blocklist
         ↓
Approves → sends data file (encrypted), logs access
Declines → explains why, offers alternative
         ↓
Vendor gets: CSV + access token, sees "Expires on [date]"
```

**Data model:**
```sql
CREATE TABLE vendor_data_requests (
  id UUID PRIMARY KEY,
  vendor_id VARCHAR(50) NOT NULL,
  requested_by_email VARCHAR(255),
  
  scope JSON,                 -- {"category": "L", "state": "CA"} or specific EINs
  purpose VARCHAR(255),       -- "Partnership outreach", "Research", etc.
  retention_days INT,         -- Auto-delete after this period
  
  status ENUM('pending', 'approved', 'declined'),
  created_at TIMESTAMP,
  reviewed_at TIMESTAMP,
  reviewed_by_email VARCHAR(255),  -- Daanaa admin
  decline_reason TEXT,
  
  -- Audit
  accessed_at TIMESTAMP,
  download_count INT,
  
  INDEX (vendor_id, status),
  INDEX (created_at DESC)
);
```

**Stewardship alignment:**
- ✅ P2 (Privacy): Explicit approval before data shared
- ✅ P7 (Independence): Admin checks vendor isn't trying to influence rankings
- ✅ P9 (Decisions explainable): Decline reasons logged

**Timeline:** Phase 4 (Oct–Nov), when vendor network scaling

---

### 3. Nonprofit Claiming Attestations (Enhancement)

**Current model:** Nonprofit submits claim, Daanaa verifies email domain + IRS EIN match.

**Request-based enhancement:**
```
Nonprofit submits: "I am Example Org (EIN 123456789)"
         ↓
Daanaa sends: Email to nonprofit.org email → "Confirm you run this org"
         ↓
Nonprofit clicks link in email
         ↓
Email-verified claim created, status: "verified"
         ↓
Nonprofit can now:
  - Edit mission statement
  - Upload logo
  - Request volunteer matching
  - Claim they need board members
```

**Why CPQ helps:** Makes it clear that nonprofit is *requesting* control of their profile. Email is the approval. Once approved, they can request other features (volunteers, data export, etc.).

**Data model:** Minimal — add to existing `org_claims`:
```sql
ALTER TABLE org_claims ADD COLUMN (
  verification_token VARCHAR(255) UNIQUE,
  verification_email_sent_at TIMESTAMP,
  verification_clicked_at TIMESTAMP,
  claimed_by_email VARCHAR(255) NOT NULL
);
```

**Timeline:** Phase 2 (Aug 15), part of claiming flow

---

### 4. Mission Review Requests (AI Oversight)

**Current:** Daanaa generates missions via AI; nonprofit doesn't see or approve them.

**Request-based model:**
```
Nonprofit sees their auto-generated mission: "Supports education..."
         ↓
If unhappy, clicks "Request mission review"
         ↓
Submits: "Actual mission: We provide STEM tutoring in underserved ZIP codes"
         ↓
Daanaa agent reviews human-submitted mission against IRS 990
         ↓
If approved → updates mission, logs approval
If rejected → explains why (insufficient detail, misalignment), offers suggestions
         ↓
Nonprofit can resubmit after revisions
```

**Data model:**
```sql
CREATE TABLE mission_review_requests (
  id UUID PRIMARY KEY,
  org_ein VARCHAR(50) NOT NULL,
  proposed_mission TEXT,
  submitted_by_email VARCHAR(255),
  
  status ENUM('pending', 'approved', 'rejected'),
  created_at TIMESTAMP,
  reviewed_at TIMESTAMP,
  reviewed_by_agent VARCHAR(255),  -- Which agent reviewed
  feedback TEXT,                    -- Why rejected or suggestions
  
  source ENUM('ai_generated', 'nonprofit_submitted'),
  
  INDEX (org_ein),
  INDEX (status, created_at DESC)
);
```

**Stewardship alignment:**
- ✅ P3 (Trust signals evidence-based): Nonprofit can attest to mission accuracy
- ✅ P6 (Mistakes corrected): Clear feedback loop for corrections
- ✅ P10 (AI is tool): Agent suggests, nonprofit+admin decide

**Timeline:** Phase 2 (Aug 15), low priority; pairs with claiming flow

---

### 5. Score Appeal / Explanation Requests (Future)

**Not a direct request,** but similar transparency model:

```
Nonprofit sees peer financial context score: 42/100
         ↓
Clicks: "Why is my score lower than I expected?"
         ↓
Daanaa explains:
  "Your 2023 revenue ($250K) places you in the Professional band.
   Within that band, you're at the 42nd percentile.
   Comparables in your category (K, food security) had higher reserve months (yours: 3.2 vs. median: 6.4)."
         ↓
Nonprofit can: "Request data review if you believe there's an error"
         ↓
Data review request → Daanaa checks underlying 990 data
```

**Timeline:** Phase 3+ (Sep onwards), lower priority

---

## Summary Table

| Pattern | Status | Timeline | Stewardship Benefit |
|---------|--------|----------|-------------------|
| Wallet verification | Design ready | Phase 2 | P2 (Privacy) |
| Volunteer matching | Design ready | Phase 3 | P2, P4 (Fairness) |
| Data export requests | Design ready | Phase 4 | P2, P7 (Independence) |
| Claiming verification | Minor enhancement | Phase 2 | P3 (Trust) |
| Mission review | Design ready | Phase 2 | P3, P6 (Mistakes) |
| Score appeals | Concept | Phase 3+ | P9 (Explainability) |

---

## Implementation Checklist (All Patterns)

For each request-based pattern, ensure:

- [ ] Explicit user action creates request (not auto-push)
- [ ] Audit table logs request → response → outcome
- [ ] Clear notifications (email + dashboard) for both parties
- [ ] Decline reasons or explanations provided
- [ ] Audit trail exportable (for annual Stewardship review)
- [ ] Privacy controls (data deleted on request, retention limits)
- [ ] No algorithm decides approvals (human or deterministic rule only)
- [ ] Users see their request status at all times

---

## Why This Pattern Matters

**Legacy issue:** Auto-pushing data or auto-deciding feels convenient but creates:
- Silent failures (user doesn't know something happened)
- No audit trail (who decided? why?)
- Privacy concerns (data shared without explicit moment of consent)
- Nonprofit burden (passive notifications they didn't ask for)

**Request model fixes:**
- Explicit → audit trail
- Nonprofit control → explicit consent
- Feedback loop → transparency
- Scales to complex decisions (volunteers, data exports) without feeling pushy

Aligns with **Stewardship P2 (Privacy is core)** and **P9 (Decisions explainable).**

---

## Next Steps

1. **Immediately:** Lock in Wallet CPQ model (Phase 2, Aug 1)
2. **By Phase 3 (Sep 1):** Add volunteer matching requests
3. **By Phase 4 (Oct):** Add vendor data export requests
4. **Ongoing:** Use this template for any future feature involving nonprofit/vendor/volunteer actions
