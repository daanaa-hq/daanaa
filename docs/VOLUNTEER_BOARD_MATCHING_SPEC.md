# Volunteer & Board Service Matching Feature

**Phase:** Launch Phase (Aug 15) or Phase 2 (Sep+) — TBD  
**Priority:** High (supports small org capacity building)  
**Alignment:** Stewardship P1 (mission), P4 (fairness to small orgs), P2 (privacy)

---

## Feature Overview

Donors signal interest in **volunteering** or **board service** at nonprofits they discover. Nonprofits see **aggregate counts** + **donor contact info** for interested people, enabling direct recruitment without intermediation.

**Core principle:** Empower small orgs to compete on mission + community, not just brand.

---

## Data Model

### Donor Side (Wallet)

**New fields in `wallet` (localStorage + server-sync via Google account):**

```json
{
  "bookmarks": ["ein_1", "ein_2"],
  "giving_intent": [
    {
      "ein": "ein_1",
      "status": "interested",
      "last_updated": "2026-08-15"
    }
  ],
  "volunteer_interests": [
    {
      "ein": "ein_1",
      "skills": ["grant-writing", "fundraising"],
      "hours_per_month": "4-8",
      "status": "interested",
      "timestamp": "2026-08-15T14:32:00Z"
    }
  ],
  "board_interests": [
    {
      "ein": "ein_2",
      "experience": "nonprofit-board",
      "status": "interested",
      "timestamp": "2026-08-15T15:00:00Z"
    }
  ]
}
```

### Nonprofit Side (Database)

**New table: `volunteer_signals`**

```sql
CREATE TABLE volunteer_signals (
  id PRIMARY KEY,
  org_ein VARCHAR(50),
  donor_email VARCHAR(255),          -- Google account email
  donor_name VARCHAR(255),           -- If available from Google profile
  signal_type ENUM('volunteer', 'board'),
  skills JSON,                       -- ["grant-writing", "data-analysis"]
  hours_per_month VARCHAR(50),       -- "4-8", "8-16", "16+"
  experience VARCHAR(255),           -- "nonprofit-board", "corporate-board", "none"
  message TEXT,                      -- Optional: "I specialize in..."
  created_at TIMESTAMP,
  status ENUM('active', 'withdrawn'),
  INDEX (org_ein, signal_type)
);
```

**Updates to `org_claims`:**

```sql
ALTER TABLE org_claims ADD COLUMN (
  looking_for_volunteers BOOLEAN DEFAULT FALSE,
  looking_for_board_members BOOLEAN DEFAULT FALSE
);
```

---

## Volunteer Skills Checklist

**Common nonprofit volunteer needs** (small orgs check what they need; donors check what they offer):

### Grant Writing
- Grant research & prospect identification
- Proposal writing
- Budget development
- Grant reporting

### Fundraising & Development
- Individual donor cultivation
- Major gifts strategy
- Corporate sponsorships
- Fundraising event planning

### Communications & Marketing
- Social media management
- Website/digital content
- Press releases & media outreach
- Messaging & brand strategy

### Operations & Administration
- Accounting/bookkeeping
- HR & compliance
- Data management & analysis
- Office/logistics management

### Board Governance
- Strategic planning
- Governance & compliance
- Fundraising strategy
- Committee leadership

### Program Design & Delivery
- Program development
- Evaluation & impact measurement
- Community engagement
- Teaching/training

### Finance
- Financial planning
- Budget management
- Audit & compliance
- Investment strategy

### Technology
- Website development
- Database/CRM setup
- IT infrastructure
- Cybersecurity

**Implementation:** Multi-select checkboxes (donors select what they can offer; nonprofits select what they need).

---

## User Flows

### Flow 1: Donor Signals Interest

**Nonprofit Detail Page:**

```
[Nonprofit Name]
[Giving Info]

═══════════════════════════════════════

🤝 HELP THIS ORGANIZATION

[💰 Add to Giving Wallet]  (existing)

OR

[👥 Volunteer Here]
   ↓ Opens modal:
   
   What can you help with? (check all that apply)
   ☐ Grant Writing
   ☐ Fundraising
   ☐ Communications
   ☐ Operations
   ☐ Board Service
   ☐ Finance
   ☐ Tech
   ☐ Program Design
   
   How much time? (select one)
   ○ 4-8 hours/month
   ○ 8-16 hours/month
   ○ 16+ hours/month
   
   Optional message:
   [textarea: "I have 10 years of nonprofit grant writing..."]
   
   [Submit] [Cancel]
   
   ✅ Added to your Wallet! Org will be able to reach out.

[🪑 Board Service]
   ↓ Similar modal:
   
   Board experience? (select one)
   ○ Nonprofit board (currently/previously)
   ○ Corporate/other board
   ○ First-time board interest
   
   [Submit] [Cancel]
```

**What happens:**
- Signal stored in donor's Wallet (localStorage + Google account)
- Server records signal in `volunteer_signals` table
- Nonprofit can contact donor if they've claimed profile

---

### Flow 2: Nonprofit Claims Profile

**Nonprofit Claim Form (existing) + NEW sections:**

```
Step 1: Basic Info (existing)
Step 2: Donation Link (existing)
Step 3: HOW CAN PEOPLE HELP? (NEW)

Are you looking for volunteers?
☐ Yes, we need volunteers
  └─ Check the skills you need:
     ☐ Grant Writing
     ☐ Fundraising
     ☐ Communications
     ☐ Operations
     ☐ Board Service
     ☐ Finance
     ☐ Tech
     ☐ Program Design

Are you looking for board members?
☐ Yes, we need board members

Optional: Tell volunteers about your needs
[textarea: "We need board members with nonprofit governance experience..."]

[Continue] [Skip]
```

**Result:**
- `looking_for_volunteers` = true/false
- `volunteer_skills_needed` = selected skills
- `looking_for_board_members` = true/false
- Data used for nonprofit dashboard + matching

---

### Flow 3: Nonprofit Sees Interested Volunteers

**Nonprofit Admin Dashboard:**

```
[Nonprofit Admin]

VOLUNTEER & BOARD INTEREST
═══════════════════════════════════════

👥 VOLUNTEER INTERESTS: 47 people interested

Top skills requested:
- Grant Writing (18 people)
- Fundraising (12 people)
- Communications (10 people)

[View All Interested] → Opens list:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sarah M. | Grant Writing, Fundraising | 8-16 hrs/month
Message: "I've worked in nonprofit development for 8 years..."
[Send Message] [Add to Notes]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
James K. | Communications, Social Media | 4-8 hrs/month
No message provided
[Send Message] [Add to Notes]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🪑 BOARD INTEREST: 3 people interested

- Lisa P. | Nonprofit board experience
- Marcus T. | First-time board interest
- Elena R. | Corporate board experience

[View All Interested] [Contact Interested People]

═════════════════════════════════════════

ACTIONS:
[📧 Send bulk message to all] 
[📥 Export contact list]
[📊 View by skill]
```

---

## Messaging System

### Nonprofit → Donor Message Flow

**Nonprofit Dashboard:**

```
[View All Interested Volunteers]
→ List of volunteers
→ Click volunteer name
→ [Send Message] button

Modal opens:
---

To: Sarah M. (sarahm@email.com)
RE: Volunteer opportunity at [Org Name]

[Compose message...]

Your message:
"Hi Sarah, we saw your interest in grant writing and fundraising.
We're currently working on foundation strategies and would love to
talk about how you might help. Would you be available for a brief call?"

[Send Message]

---

What happens:
1. Email sent to donor (FROM nonprofit email address)
2. Donor replies to nonprofit directly
3. Nonprofit owns relationship (no intermediation from Daanaa)
```

---

## Privacy & Consent

### Data Handling

**Stored securely:**
- Donor email + name (only if Google account linked)
- Donor skills + hours (donor-provided)
- Message from donor (optional)

**NOT stored:**
- Donation transaction data
- Giving history
- Other wallet contents (only volunteer signals)

**Donor controls:**
- Can withdraw volunteer interest anytime
- Signals deleted from nonprofit view if withdrawn
- Can see which orgs contacted them
- Can opt-out of messaging

**Nonprofit sees:**
- Aggregate counts only (no names by default)
- Drill down to individual names + emails + skills only if opted in
- Can see message content from volunteers

### Stewardship Alignment

✅ **P2 (Privacy):** Email is only shared with orgs nonprofit explicitly claimed  
✅ **P4 (Small org fairness):** Small orgs get talent matching capability  
✅ **P5 (No manipulation):** Transparent about volunteer interests, no artificial scarcity  
✅ **P7 (Independence):** No algorithmic matching, no influence — direct connection  

---

## Implementation Roadmap

### Phase 1a: Nonprofit Claiming (Aug 1–10)
- [ ] Add checkboxes to claim form (looking for volunteers/board)
- [ ] Add skills selection to claim form
- [ ] Store in `org_claims`
- [ ] QA with 10 test nonprofits

### Phase 1b: Donor Signals (Aug 10–15)
- [ ] Add volunteer/board buttons to nonprofit detail page
- [ ] Modal with skills checklist + hours + optional message
- [ ] Store in Wallet + `volunteer_signals` table
- [ ] Test with 50 beta users

### Phase 1c: Nonprofit Dashboard (Aug 15–20)
- [ ] Create nonprofit admin view showing interested volunteers/board
- [ ] Aggregate counts by skill
- [ ] [View All] list with donor names + skills + hours
- [ ] Basic message composition

### Phase 2a: Messaging (Sep+)
- [ ] Full messaging thread in nonprofit dashboard
- [ ] Email notifications
- [ ] Bulk message composer
- [ ] Withdrawal/blocking

### Phase 2b: Analytics (Oct+)
- [ ] Track: Did orgs contact volunteers?
- [ ] Track: Do volunteer relationships convert to actual service?
- [ ] Feedback loop to improve skill categories

---

## Database Schema

```sql
-- New volunteer signals table
CREATE TABLE volunteer_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_ein VARCHAR(50) NOT NULL,
  donor_email VARCHAR(255) NOT NULL,
  donor_name VARCHAR(255),
  signal_type ENUM('volunteer', 'board') NOT NULL,
  skills JSON,                    -- ["grant-writing", "fundraising"]
  hours_per_month VARCHAR(50),    -- "4-8", "8-16", "16+"
  board_experience VARCHAR(255),  -- "nonprofit-board", "corporate-board", "none"
  donor_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status ENUM('active', 'withdrawn') DEFAULT 'active',
  contacted_at TIMESTAMP,
  INDEX idx_org_signal (org_ein, signal_type),
  INDEX idx_donor_email (donor_email)
);

-- Updates to org_claims
ALTER TABLE org_claims ADD COLUMN (
  looking_for_volunteers BOOLEAN DEFAULT FALSE,
  volunteer_skills_needed JSON,    -- ["grant-writing", "fundraising"]
  volunteer_notes TEXT,
  looking_for_board_members BOOLEAN DEFAULT FALSE,
  board_notes TEXT,
  volunteer_contacts_viewed INT DEFAULT 0
);

-- Aggregate view (materialized or computed)
CREATE VIEW volunteer_interest_summary AS
SELECT 
  org_ein,
  signal_type,
  COUNT(*) as total_interested,
  JSON_OBJECT(
    'grant-writing', COUNT(CASE WHEN skills LIKE '%grant-writing%' THEN 1 END),
    'fundraising', COUNT(CASE WHEN skills LIKE '%fundraising%' THEN 1 END),
    -- ... more skills
  ) as skills_breakdown
FROM volunteer_signals
WHERE status = 'active'
GROUP BY org_ein, signal_type;
```

---

## Launch Decision

### Launch with Public (Aug 15)?
**YES, if:**
- Simple MVP (donor signals + nonprofit view, basic messaging in Phase 2)
- Builds narrative: "Daanaa helps nonprofits find not just donors, but volunteers and board members"
- Strong fit for DRK/Knight/Omidyar pitch: "We're building complete nonprofit capacity infrastructure"

**NO, launch Phase 2 (Sep) if:**
- Need full messaging system first
- Want to focus on giving wallet launch

**Recommendation:** **Launch donor + nonprofit side (Phase 1a/1b)** as Aug 15. Hold **nonprofit messaging dashboard (Phase 1c)** for Sep 1 with full polish.

---

## Copy & Messaging

### For Nonprofits
"Help your community find ways to support you. Tell us what you need — whether it's grant writing, fundraising, board service, or operations help. People interested in volunteering will be able to reach out directly."

### For Donors
"Want to help beyond giving? Signal your interest in volunteering or board service. Nonprofits you support can contact you directly. You stay in control."

### For G0 Pitch
"Daanaa is infrastructure for complete nonprofit support — not just giving, but talent matching. We surface volunteer and board opportunities for small, overlooked organizations. That levels the playing field."

---

## Success Metrics (By Dec 31)

- [ ] 20%+ of nonprofits opt into volunteer interest
- [ ] 100+ donors signal volunteer interest
- [ ] 10+ volunteer relationships initiated through platform
- [ ] Avg nonprofit receives 15+ volunteer signals in first 3 months
- [ ] Small orgs (<$500K revenue) see 2x volunteer signal rate vs large orgs (fairness proof)

---

**Owner:** Volunteer & Board Matching Feature  
**Status:** Design complete — Ready for implementation roadmap  
**Questions:** Message any blockers to Akbar  

---

*Created: Jun 18, 2026*  
*Last updated: Jun 18, 2026*
