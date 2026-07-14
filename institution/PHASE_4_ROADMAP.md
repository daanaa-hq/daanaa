# Phase 4+ Roadmap: Nonprofit Institutional Platform

**Vision:** Transform Daanaa from discovery directory → institutional platform where nonprofits build their presence, tell their stories, get verified, and access services.

**Timeline:** Concurrent development, phased rollout

---

## Phase 4: Nonprofit Voice Amplification (This Week)

**Goal:** Let nonprofits author content (not just claim fields).

**What Gets Built:**
1. **Impact Stories** — Nonprofits post 200-500 word narratives about work
   - Story templates (annual highlights, case study, mission deep-dive)
   - Rich text editor + markdown
   - Versioning (Daanaa shows current; archives old)
   - Source attribution: "Written by [Org Name] on [Date]"

2. **Program Descriptions** — Detailed descriptions of what they do
   - Program name, focus area, who they serve, outcomes
   - Links to external program pages (verified live)
   - Volunteer opportunities per program

3. **Volunteer Needs** — Structured volunteer interest (beyond discovery)
   - Specific roles (mentoring, board service, technical, admin)
   - Time commitment required
   - Skills needed
   - Application link (org controls)

4. **Leadership Profiles** — Board + staff leadership pages
   - Name, title, bio (org-authored)
   - External link (e.g., LinkedIn, website bio)
   - Expertise tags
   - Verify person works there (via email domain or org website)

**Data Model:**
```sql
CREATE TABLE nonprofit_content (
  id INTEGER PRIMARY KEY,
  ein TEXT,
  content_type TEXT ('impact_story', 'program', 'volunteer_need', 'leadership'),
  title TEXT,
  body TEXT,
  published_at TIMESTAMP,
  author_email TEXT,
  verified_at TIMESTAMP,
  version INTEGER,
  status TEXT ('draft', 'published', 'archived')
);

CREATE TABLE nonprofit_content_versions (
  id INTEGER PRIMARY KEY,
  content_id INTEGER,
  version INTEGER,
  body TEXT,
  archived_at TIMESTAMP
);
```

**API Endpoints:**
- `POST /api/nonprofit/content` — Create/publish content (requires org auth)
- `GET /api/nonprofit/:ein/content` — Read all published content for org
- `PUT /api/nonprofit/content/:id` — Edit (creates new version)
- `GET /api/nonprofit/:ein/content/:type` — Filter by type

**UI:**
- Nonprofit dashboard gets "Content" section (stories, programs, people)
- Org detail page shows content (with version history link)
- Search: filter by content type (e.g., "orgs with volunteer needs")

**Stewardship Angle:**
- Source tracking: every story is attributed to org + date
- Nonprofits have voice, not us (P5: no shame, let orgs tell truth)
- Versioning = transparency (audit trail of changes)

---

## Phase 5: Trust Signal Verification (2 Weeks)

**Goal:** Move from context (scores) to verdict (verified trustworthiness).

**What Gets Built:**

1. **Verification Checklist** — Org can claim and Daanaa verifies
   - Website live + domain matches EIN
   - 990 filed recently (within 2 years)
   - Leadership listed in public records
   - Donation link works + leads to org
   - Social media presence (optional)
   - Impact story published (org-authored)
   - Volunteer page active
   
2. **Trust Badges** — Visual indicators (not rankings)
   - ✓ Website verified
   - ✓ 990 current
   - ✓ Donation link verified
   - ✓ Org-authored story
   - ✓ Leadership listed
   - 🔄 Under review
   - ⚠️ Needs attention (outdated 990, website down, etc)

3. **Verification Timelines** — Show when things were last checked
   - "Website verified 7 days ago"
   - "Latest 990 filed Jan 2024"
   - "Impact story published 30 days ago"

4. **Verification History** — Nonprofit sees timeline of checks
   - "May 15: Website verified"
   - "May 14: 990 data updated from IRS"
   - "May 13: Donation link working"

**Data Model:**
```sql
CREATE TABLE nonprofit_verification (
  id INTEGER PRIMARY KEY,
  ein TEXT,
  check_type TEXT ('website', '990', 'donation_link', 'leadership', 'story'),
  status TEXT ('pass', 'fail', 'pending', 'expired'),
  verified_at TIMESTAMP,
  expires_at TIMESTAMP,
  notes TEXT,
  automated BOOLEAN  -- true if Daanaa checked, false if org claims
);
```

**API Endpoints:**
- `GET /api/nonprofit/:ein/verification` — All checks + timeline
- `POST /api/nonprofit/:ein/verification/request` — Ask for recheck
- `GET /api/nonprofit/:ein/badges` — Just the badge list

**UI:**
- Org detail page: "Trust Signals" section showing all badges + timelines
- Dashboard: "Verification Status" with action items
- Search filter: "Recently verified", "Needs attention"

**Stewardship Angle:**
- Verification ≠ endorsement (we show evidence, not opinion) (P3)
- Transparent methodology (show how each badge is earned)
- Nonprofits own the narrative (can dispute, can claim they're working on it)

---

## Phase 6: Donor Learning System (3 Weeks)

**Goal:** Help donors discover orgs aligned with *their* values (privacy-first).

**What Gets Built:**

1. **Giving Preferences** — Wallet-stored donor interests
   - Causes I care about (e.g., homelessness, climate, education)
   - Giving amounts I prefer ($100-$1K, $1K-$10K, etc)
   - Geographic focus (local, national, specific states)
   - Org size preference (small, mid, large)
   - Cause focus depth (beginner, intermediate, expert)
   - Hidden: stored in wallet, never shared, never used for outreach

2. **Smart Recommendations** — "Orgs like ones you bookmarked"
   - "5 orgs in [cause] solving [problem] in [area]"
   - Based on: cause tags, peer group, geography, size
   - No ML profiles or tracking (pure preference matching)
   - User controls all data (export/delete anytime)

3. **Giving Patterns Insights** (Private)
   - "You've bookmarked 15 orgs; here's their peer distribution"
   - "Average org size you bookmark: mid-size ($500K-$2M)"
   - "Your focus areas vs national trends"
   - All private, in wallet, never shared

**Data Model:**
```sql
-- Stored in user's wallet (localStorage + optional sync to Firebase)
{
  preferences: {
    causes: ['homelessness', 'education'],
    budget_range: '$1K-$10K',
    geography: ['CA', 'national'],
    org_size: 'mid',
    expertise_level: 'intermediate'
  },
  bookmarks: [ein, ein, ...],
  giving_intents: [
    { ein, amount, date_created, date_given: null }
  ]
}
```

**API Endpoints:**
- `POST /api/donor/preferences` — Save preferences (wallet-based, client-side first)
- `GET /api/donor/recommendations` — Get smart matches
- `GET /api/donor/insights` — Private analytics of own bookmarks

**UI:**
- Wallet: "Your Preferences" section
- Wallet: "Recommended for You" carousel
- Wallet: "Your Giving Patterns" insights
- Browse page: "Organizations similar to [Bookmarked Org]"

**Stewardship Angle:**
- Privacy-first (nothing leaves the user's device without consent) (P2)
- No surveillance (no behavior tracking, no profiles sold) (P4)
- Donor agency (you control your data, can see what you've learned about yourself)

---

## Phase 7: Institutional Memory for Nonprofits (4 Weeks)

**Goal:** Build longitudinal narratives per org (not just snapshots).

**What Gets Built:**

1. **Org Timeline** — Major events, pivots, milestones
   - Leadership changes (board/staff)
   - Strategic pivots (e.g., "Shifted from direct service to policy")
   - Funding events (major grants, capital campaigns)
   - Program launches/closures
   - 990 data changes (revenue, focus area, etc)
   - Impact milestones (reached X beneficiaries, X% target)
   - External news mentions

2. **Change Detection** — Automatic signals of pivot/growth/decline
   - Revenue trend (flat, growing, declining, volatile)
   - Staff growth
   - Program expansions
   - Focus area shifts (NTEE-level)
   - Leadership turnover

3. **Org Narrative** — Daanaa constructs readable story
   - "Founded 2010 (small community org)"
   - "2015: Expanded from local to regional (3x revenue growth)"
   - "2020: Launched policy advocacy program (mission pivot)"
   - "2023: Reached 50K beneficiaries (milestone)"
   - "Trend: Steady growth, focus shifting toward prevention"

4. **Donor/Volunteer Timeline View**
   - Donors see org's *arc* (where did they start, where are they going)
   - Volunteers see if org is growing (hiring opportunity?)
   - Researchers see evolving focus

**Data Model:**
```sql
CREATE TABLE nonprofit_events (
  id INTEGER PRIMARY KEY,
  ein TEXT,
  event_type TEXT ('leadership_change', 'pivot', 'funding', 'milestone', '990_update', 'news'),
  description TEXT,
  evidence_url TEXT,
  detected_date TIMESTAMP,
  event_date TIMESTAMP,  -- when it actually happened
  source TEXT ('org_claim', 'irs_data', 'news', 'website'),
  significance_score FLOAT (0-100)
);

CREATE TABLE nonprofit_narrative (
  ein TEXT PRIMARY KEY,
  narrative_text TEXT,
  generated_at TIMESTAMP,
  based_on_events INTEGER
);
```

**API Endpoints:**
- `GET /api/nonprofit/:ein/timeline` — All events + timeline
- `GET /api/nonprofit/:ein/narrative` — Generated story
- `POST /api/nonprofit/:ein/event` — Org can add custom event

**UI:**
- Org detail page: "Timeline" section (vertical timeline of major events)
- Org detail page: "Org Story" narrative paragraph
- Search: "Show orgs with revenue growth in last 2 years"
- Browse: "Emerging orgs" (launched in last 5 years, growing)

**Stewardship Angle:**
- Narrative is transparent (source: IRS data, org claim, news)
- Avoids shame (pivots aren't failures; they're adaptation) (P5)
- Gives small orgs *context* (growth matters more than size)

---

## Phase 8: Marketplace for Nonprofit Adjacencies (5 Weeks)

**Goal:** Revenue model that serves nonprofits without touching donations.

**What Gets Built:**

1. **Curated Marketplace** — Directory of services *for* nonprofits
   - Accountants (nonprofit tax specialists)
   - Grant writers
   - Board consultants
   - Fundraisers
   - IT consultants
   - HR/compliance
   - Impact measurement
   - Facility management
   - Insurance brokers

2. **Vendor Vetting** — Alignment with Daanaa values
   - Not-for-profit preferred, B-corp, mission-aligned, or transparent pricing
   - No predatory practices (no high-volume, low-quality services)
   - Verified reviews from nonprofits who used them
   - No influence over Daanaa rankings (P7)

3. **Nonprofit Profiles on Vendors**
   - "I need a grant writer"
   - See 5 options, vetted, with nonprofit reviews
   - Direct contact (org controls outreach)
   - Pricing transparency
   - No commission on deals (we charge vendors, not nonprofits)

4. **Brand Separation**
   - Marketplace runs under "EcoMargins Nonprofit Services"
   - Separate from Daanaa (firewall enforced) (P7)
   - No access to Daanaa giving data
   - No cross-selling to donors (P2)

**Data Model:**
```sql
CREATE TABLE vendors (
  id INTEGER PRIMARY KEY,
  name TEXT,
  service_category TEXT,
  website TEXT,
  contact_email TEXT,
  mission_statement TEXT,
  pricing_transparency BOOLEAN,
  daanaa_vetting_status TEXT ('approved', 'pending', 'rejected'),
  verified_at TIMESTAMP,
  nonprofit_reviews JSON
);
```

**Revenue Model:**
- Vendors pay monthly listing fee (~$100-$500 depending on category)
- Nonprofits search free
- EcoMargins handles vendor relations (separate from Daanaa team)
- Vendors have zero influence over Daanaa (P7 enforced via contract)

**API/UI:**
- Separate app: EcoMargins Nonprofit Services directory
- Link from org dashboard: "Get help with [accounting, grants, board, etc]"
- No tracking of which nonprofits visit vendors (privacy) (P2)

**Stewardship Angle:**
- Revenue model that doesn't compromise independence (P1, P7)
- Serves nonprofits (not donors) (P8: never control funds)
- Vendor relationship is transparent (who's in marketplace, why they're vetted)

---

## Sequencing & Dependencies

```
Week 1:  Phase 4 (Voice) + Phase 5 (Verification) [parallel]
Week 2:  Phase 4 + 5 complete, deploy
Week 3:  Phase 6 (Donor Learning) starts
Week 4:  Phase 7 (Memory) starts
Week 5:  Phase 8 (Marketplace) planning
Week 6+: All features live, iterate
```

## Key Principles (All Phases)

1. **Nonprofit Agency:** Nonprofits author their narrative, not us
2. **Transparency:** Every signal shows source (IRS, org, news, automated)
3. **Privacy:** Donor/nonprofit data never leaves their device without consent
4. **Independence:** No payment, partnership, or vendor influences rankings (P7)
5. **Dignity:** Small orgs treated with same respect as large (P4)
6. **Stewardship:** Every decision explainable in STEWARDSHIP.md terms

---

## Definition of Done (All Phases)

✓ Code complete + tests passing  
✓ Smoke tests on production  
✓ Data model peer-reviewed  
✓ Privacy gates (GATE 1-8) passing  
✓ Stewardship principles cross-checked  
✓ Nonprofit feedback collected (if touching their workflows)  
✓ Documented in architecture / decisions  

