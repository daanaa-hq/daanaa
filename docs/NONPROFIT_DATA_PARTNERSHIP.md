# Nonprofit Data Partnership Strategy — Daanaa

## Problem Statement

**Current state:** Daanaa indexes public IRS data (990 filings), which is 1–2 years old by the time users see it.
Nonprofits have current data (mission, finances, website, giving URLs) but no frictionless way to share it.

**Impact:** Discovery is accurate but stale. Users may see outdated financials or obsolete mission statements.

**Stewardship constraint:** Must not pressure orgs, must not require paid features, must maintain independence (Principles #1, #7, #9).

---

## Design Principles

### 1. Principle #1: Mission Before Growth
- Updating data improves discovery for donors → aligns with Daanaa's mission
- No hidden paywall, no "premium profile" upsell
- Incentive: better visibility, not money

### 2. Principle #2: Privacy is Structural
- Don't track which org fields were updated when (creates giving-activity inference)
- Don't expose update history to users (prevents social pressure on orgs)
- Store who updated what (for dispute resolution), but never surface it

### 3. Principle #3: Evidence-Based Trust Signals
- Distinguish IRS data (1–2 yrs old, verified by government) from org-claimed data (current, org-verified)
- Never mix them without source labels
- Show "Last updated by [org] on [date]" badges clearly

### 4. Principle #7: Independence Protected
- Any nonprofit can update data (not just paying partners)
- No tiered access, no "featured org" status for updaters
- Algorithm doesn't boost updated orgs (would be pay-to-play)

---

## Solution: Nonprofit Claim Flow + Data Update API

### Phase 1: Claim & Update + Donor Interest Dashboard (MVP)
**Timeline:** 3 weeks  
**Scope:** Nonprofits claim their EIN, update 3–5 key fields (mission, website, donate URL, cause tags), access a free dashboard showing real donor interest

#### UX Flow

**Step 1: Org detail page**
```
┌─────────────────────────────────────┐
│ [Org Detail: ACME Food Bank]        │
├─────────────────────────────────────┤
│ Mission: "Feeding communities since" │
│          "2010" [⚠️ Last updated     │
│                  by IRS, 2024-06-15] │
│                                      │
│ [Is this your org? Update data] ←─── New CTA
└─────────────────────────────────────┘
```

**Step 2: Modal → Claim org (email magic link)**
```
Modal: "Claim your nonprofit's profile"
┌──────────────────────────────────────┐
│ 1. Verify you work for this org      │
│    Email: [your@acmefood.org]        │
│    [Send claim link]                 │
│                                      │
│ ℹ️ We'll email you a one-time link. │
│    No password, no account needed.   │
└──────────────────────────────────────┘
```

**Step 3: Email claim link → One-click form**
```
Email arrives: "Claim ACME Food Bank on Daanaa"
Link: daanaa.org/claim/TOKEN

Page loads:
┌──────────────────────────────────────┐
│ ✓ Verified: your@acmefood.org       │
│                                      │
│ Update ACME Food Bank profile        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Mission statement:                   │
│ [textarea] (current: "Feeding...")   │
│                                      │
│ Website: [input] https://acmefo...   │
│                                      │
│ Primary donation link:               │
│ [input] https://donate.acmefo...     │
│                                      │
│ Cause tags: [multi-select checkboxes]│
│ ☑ Food & Agriculture                 │
│ ☐ Disaster Relief                    │
│ ☐ Community Development              │
│                                      │
│ [Cancel] [Save & Publish]            │
└──────────────────────────────────────┘
```

**Step 4: Confirmation + Dashboard Access**
```
✓ Submitted!
Your updates will appear on your profile in ~1 hour
(Daanaa reviews for spam/abuse; you can edit anytime)

[View your profile] [View your Donor Dashboard]
```

**Step 5: Donor Interest Dashboard** (NEW — the "why should I care?" moment)
```
Dashboard: daanaa.org/dashboard/{TOKEN}
(Token valid as long as email verified; can log back in anytime)

┌─────────────────────────────────────────────────┐
│ ACME Food Bank — Donor Interest Dashboard       │
├─────────────────────────────────────────────────┤
│ This Month's Donor Attention                    │
│                                                  │
│ Bookmarks to Giving Wallet: 42 ↑ (+35% vs last)│
│ • From "Food Justice" cause: 28                 │
│ • From "Community Empowerment": 14              │
│ • Top location: San Francisco (18 bookmarks)    │
│                                                  │
│ Profile Strength:                               │
│ ✅ Mission updated (fresh, today)               │
│ ✅ Website verified (live)                      │
│ ✅ Donate link working                          │
│ ⚠️ Cause tags: 2/5 (add 1-2 more to reach 847   │
│    donors interested in "Nutrition")            │
│                                                  │
│ Anonymized Donor Insights:                      │
│ • Donors bookmarking you are also interested in:│
│   - Nutrition (847 donors) ← recommended        │
│   - Child Health (612 donors)                   │
│   - Rural Development (445 donors)              │
│                                                  │
│ Tips to increase visibility:                    │
│ 📊 Orgs with complete cause tags get 2.3x more │
│    bookmarks. Add "Nutrition" tag to match 847  │
│    interested donors.                           │
│                                                  │
│ 📅 Update your mission every 6 months to stay   │
│    in the "Recently Updated" search feed.       │
│                                                  │
│ [Edit your profile] [Contact support]           │
└─────────────────────────────────────────────────┘
```

**Why this dashboard changes everything:**
- **Proof, not promises**: "42 real donors bookmarked you" vs "trust us, you'll get visibility"
- **Actionable insight**: "Add Nutrition tag to reach 847 donors" is concrete, motivating
- **Recurring engagement**: They log back monthly to see "47 bookmarks this month" — builds habit
- **No tracking**: Completely anonymized (no "Maria from SF bookmarked you"), privacy-first

#### Backend Implementation

**Endpoints:**

```python
# POST /api/claim/request-link
{
  "ein": "123456789",
  "email": "your@acmefood.org"
}
→ 200 { "message": "Check your email" }
→ Sends email with time-limited JWT token (24-hour TTL)

# POST /api/claim/verify-and-update
Headers: Authorization: Bearer {JWT}
Body:
{
  "ein": "123456789",
  "mission": "Updated mission text",
  "website": "https://...",
  "donate_url": "https://...",
  "cause_tags": ["Food", "Community Development"],
  "confirm": true
}
→ 200 { "message": "Updated. Live in ~1 hour", "claim_id": "..." }
→ Creates/updates org_claims row with org_provided_data
→ Queues for human review (anti-spam filter)

# GET /api/org/{ein}/claim-status
→ 200 {
  "ein": "123456789",
  "has_claim": true,
  "claimed_by_email": "your@acmefood.org",
  "last_updated": "2026-06-22T14:30:00Z",
  "fields_updated": ["mission", "donate_url"]
}

# GET /api/org/{ein}?include_sources=true
→ Returns org with source labels:
{
  "ein": "123456789",
  "mission": "Updated mission",
  "mission_source": "org_claimed",
  "mission_claimed_date": "2026-06-22",
  "merit_score": 0.72,
  "merit_score_source": "irs_public_data",
  "merit_score_last_updated": "2024-06-15"
}

# GET /api/nonprofit/dashboard/{claim_token}
→ Nonprofit dashboard (claims their org interest metrics):
{
  "ein": "123456789",
  "org_name": "ACME Food Bank",
  "claim_verified_email": "your@acmefood.org",
  "this_month": {
    "bookmarks_total": 42,
    "bookmarks_prev_month": 31,
    "bookmarks_by_cause": {
      "Food Justice": 28,
      "Community Empowerment": 14
    },
    "bookmarks_by_location": {
      "San Francisco, CA": 18,
      "Oakland, CA": 8,
      "Los Angeles, CA": 6
    }
  },
  "profile_completeness": {
    "mission_status": "✅ fresh",
    "website_status": "✅ verified",
    "donate_url_status": "✅ working",
    "cause_tags_count": 2,
    "cause_tags_recommended": [
      {
        "tag": "Nutrition",
        "interested_donors": 847,
        "reason": "Orgs with this tag + your profile get 2.3x more bookmarks"
      },
      {
        "tag": "Child Health",
        "interested_donors": 612
      }
    ]
  },
  "donor_insights": {
    "donors_also_interested_in": [
      { "tag": "Nutrition", "count": 847 },
      { "tag": "Child Health", "count": 612 },
      { "tag": "Rural Development", "count": 445 }
    ]
  },
  "tips": [
    "Orgs with complete cause tags (5/5) get 2.3x more bookmarks",
    "Update your mission every 6 months to stay in 'Recently Updated' feed"
  ]
}
```

**Database Schema (additions to org_claims table):**

```sql
-- Existing org_claims table extended:
ALTER TABLE org_claims ADD COLUMN (
  org_provided_mission TEXT,
  org_provided_website TEXT,
  org_provided_donate_url TEXT,
  org_provided_cause_tags JSON,
  claimed_email TEXT NOT NULL,
  claimed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_updated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  claim_status TEXT DEFAULT 'pending_review',  -- pending_review, approved, rejected
  review_notes TEXT,
  verification_token TEXT UNIQUE,
  token_expires_at DATETIME
);

-- Index for fast lookups
CREATE INDEX idx_claims_by_email ON org_claims(claimed_email);
CREATE INDEX idx_claims_by_status ON org_claims(claim_status);
```

**Frontend Integration (React):**

```typescript
// 1. Add CTA to org detail page (OrgDetail.tsx)
{claimed && (
  <button onClick={() => setShowClaimModal(true)}>
    Is this your org? Update data
  </button>
)}

// 2. ClaimOrgModal component
export const ClaimOrgModal: React.FC<{ ein: string; onClose: () => void }> = ({ ein, onClose }) => {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState('initial') // initial, sent, verified, updating
  const [token, setToken] = useState('')

  const handleRequest = async () => {
    const res = await fetch('/api/claim/request-link', {
      method: 'POST',
      body: JSON.stringify({ ein, email })
    })
    if (res.ok) setStatus('sent')
  }

  const handleUpdate = async (formData) => {
    const res = await fetch('/api/claim/verify-and-update', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ ein, ...formData, confirm: true })
    })
    if (res.ok) setStatus('success')
  }

  return (
    <Modal onClose={onClose}>
      {status === 'initial' && (
        <div>
          <h2>Claim your nonprofit's profile</h2>
          <input
            type="email"
            placeholder="your@nonprofit.org"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button onClick={handleRequest}>Send claim link</button>
        </div>
      )}
      {status === 'sent' && (
        <div>
          <p>✓ Claim link sent to {email}</p>
          <p>Open the link in your email and fill out the form.</p>
        </div>
      )}
    </Modal>
  )
}

// 3. Update org detail to show claim status
{claim_status === 'approved' && (
  <Badge>
    Updated by org on {last_updated_timestamp}
  </Badge>
)}
```

---

### Phase 2: Quality Gate + Auto-Approval (optional, 4 weeks out)

**Problem:** Reviewing every claim manually doesn't scale.

**Solution:** Automated quality checks + auto-approval for safe updates:

```python
def auto_review_claim(claim):
    """Gate 1: Heuristic spam/abuse detection."""
    violations = []
    
    # Check mission length & language
    if len(claim.mission) > 500:
        violations.append("Mission too long")
    if not mission_is_english(claim.mission):
        violations.append("Mission not English")
    
    # Check URLs (valid syntax, not phishing domains)
    if not is_valid_url(claim.donate_url):
        violations.append("Donate URL invalid")
    if is_phishing_domain(claim.donate_url):
        violations.append("Donate URL suspicious")
    
    # Check cause tags (exist in taxonomy)
    for tag in claim.cause_tags:
        if tag not in CAUSE_TAG_TAXONOMY:
            violations.append(f"Unknown tag: {tag}")
    
    if not violations:
        claim.status = 'approved'
        return True
    else:
        claim.status = 'pending_review'
        claim.review_notes = '; '.join(violations)
        return False
```

**Escalation:** Only violations go to human review queue.

---

### Phase 3: Nonprofit Outreach (6 weeks out)

Once the claim flow is live, **proactively invite top 5K small orgs** to update:

**Email (permission-based, opt-in only):**

```
Subject: ACME Food Bank: Daanaa Discovery Profile

Hi ACME Food Bank,

We found you on Daanaa, a new nonprofit discovery platform 
(daanaa.org). Your profile is based on public IRS data from 2024.

If you'd like to add current info (mission, website, donation link), 
you can claim your profile in 2 minutes:

[Claim your profile]

No account needed. One-time email link. You're in control.

Best,
Daanaa Team
```

**Timing:** 
- Start with 100 test orgs (high-volume, high-impact)
- Monitor for bounces, unsubscribes, opt-out requests
- Scale to 5K if positive response

**Measure:**
- Claim request rate (target: 5–10%)
- Update completion rate (target: 70% of requests)
- Data quality (violations caught by auto-review)

---

## Data Freshness on the Product (Frontend)

### Show age of every data point

```
┌─────────────────────────────────────┐
│ ACME Food Bank                      │
├─────────────────────────────────────┤
│ Mission                             │
│ "Feeding communities since 2010"    │
│ 📅 IRS, 2024-06-15 (1 year old)    │
│ [Update with current mission]       │
│                                      │
│ Financial Health                    │
│ Healthy (96 percentile)             │
│ 📅 IRS, 2024 filing (1 year old)   │
│ [→ View full IRS filing]            │
│                                      │
│ Website                             │
│ acmefood.org                        │
│ 📅 Verified by org, 2026-06-20     │
│                                      │
│ Primary Donation Link               │
│ donate.acmefood.org                 │
│ 📅 Verified by org, 2026-06-20     │
│ ✓ Link works, HTTPS, no redirects  │
└─────────────────────────────────────┘
```

**Key insight:** Users trust fresher data = they understand the IRS baseline is stale.

---

## Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Claim completion rate | 7% of 5K outreach = 350 claims | Modest; most orgs won't claim |
| Update quality (pass auto-review) | 90% | Focus on accessibility, not perfection |
| Dashboard first-view rate | 80% of claimants | Essential: they need to see the value prop |
| Dashboard repeat-visit rate | 40% month-on-month | Shows dashboard provides ongoing value |
| Profile improvement actions | 35% add cause tags after dashboard | Actionable insights drive behavior |
| Data freshness (claimed data avg age) | < 3 months | Shows orgs actively maintain profiles |
| Dispute rate | < 2% | Few false claims or bad updates |
| Repeat update rate | 30% of claimed orgs update again | Indicates adoption |

---

## Anti-Patterns (What NOT to do)

❌ **Gamification** — "Badges for updated profiles" → creates pressure, violates Principle #1  
❌ **Algorithm boost** — Higher search ranking for updated orgs → becomes pay-to-play, violates Principle #7  
❌ **Paid tier** — "Premium profile" with featured placement → commercializes discovery, violates Principle #1  
❌ **Tracking** — "Track how many times your profile was viewed" → creates giving-activity inference, violates Principle #2  
❌ **Auto-publish** — Don't approve updates automatically without review → risk spam/fraud  
❌ **Pressure emails** — Don't guilt nonprofits into claiming ("Your profile is incomplete") → violates Principle #1  

---

## Rollout Sequence

### Week 1–2: Claim flow MVP + Dashboard backend
- [ ] Database schema + org_claims extensions
- [ ] Backend endpoints (`/api/claim/*`, `/api/nonprofit/dashboard/*`)
- [ ] Email magic link + JWT token system
- [ ] Dashboard data aggregation (wallet bookmarks → cause/location breakdown)
- [ ] Cause tag recommendation engine (count donors by tag, suggest high-ROI tags)
- [ ] Frontend ClaimOrgModal + CTA
- [ ] Frontend DonorDashboard component (stats, profile strength, tips)
- [ ] Auto-review quality gate (Phase 1 simple heuristics)
- [ ] Manual review queue (admin endpoint)
- [ ] Test with 10 internal test orgs

### Week 3: Deployment + dashboard polish
- [ ] Deploy to production (droplet)
- [ ] Monitor claim requests, token expiry, email bounce rate
- [ ] Dashboard performance (query optimization for large bookmark tables)
- [ ] Fix any UX friction (modal text, email clarity, dashboard load time)
- [ ] Data freshness badges on org detail pages
- [ ] Test end-to-end: claim → email link → dashboard access → data visible

### Week 5–6: Outreach (optional)
- [ ] Identify 100 test orgs (high-visibility, high-impact)
- [ ] Craft outreach email + permission opt-in
- [ ] Send test batch, monitor response
- [ ] Iterate on email copy based on feedback

### Week 7+: Scale
- [ ] Expand to 5K orgs based on metrics
- [ ] Implement Phase 2 (auto-approval) if volume justifies it
- [ ] Update public methodology docs (explain IRS vs org-claimed data)

---

## Legal & Privacy Notes

- **No capture of updates for targeting:** Don't log "Org X updated mission on Y date" in a way that enables outreach targeting.
- **Claim email is minimal PII:** Store as BLAKE2 hash if possible; delete after verification.
- **Public attribution:** "Last updated by org on [date]" is fine; "Updated by [person's name]" is not.
- **Dispute resolution:** Keep claim history (who updated what) for 90 days, then archive securely.

---

## Decision Gates Before Rollout

Before shipping Claim Flow MVP:
- [ ] User (Akbar): Confirm outreach email strategy (auto-send vs opt-in only)
- [ ] User: Approve "Last updated by org" badge framing (doesn't pressure users)
- [ ] User: Confirm Phase 2 (auto-approve) timeline and criteria
- [ ] Legal review: Verify claim email capture and storage is GDPR/CCPA compliant

Propose: Email outreach is **permission-based opt-in only** (no unsolicited cold emails), and "Last updated by org" is a neutral badge (not a trust endorsement, just a data-freshness marker).

