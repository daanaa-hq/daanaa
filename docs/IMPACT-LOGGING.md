# Impact Logging Specification

**Status:** Design (pre-implementation)  
**Author:** Claude Code  
**Stewardship Principles:** P2 (Privacy), P3 (Evidence-based), P4 (Fairness), P5 (Respect), P8 (Independence)  
**Privacy Guarantee:** No donor tracking. No giving network exposure. All events are org-level, anonymized, voluntary.

---

## 1. Vision

Daanaa measures its impact on the nonprofit sector through three voluntary, privacy-respecting channels:

1. **Donation Attribution** — Donors confirm "Daanaa helped me find this org" after giving
2. **Volunteer Impact** — Nonprofits report volunteer hours; we value at industry standard rates
3. **Partnership Savings** — (Future) Track cost reductions from Daanaa partnerships

Result: A transparent, evidence-based impact dashboard showing **real outcomes**, not speculative metrics.

---

## 2. Core Design Principles

### Privacy First
- No donor ID, no giving amounts, no network graph
- Org-level aggregation only
- Timestamps only (no user tracking)
- Voluntary participation (opt-in, not default)
- Impact events are **decoupled from identity**

### Evidence-Based
- All values derive from real events (donations confirmed, hours attested)
- Methodology transparent (e.g., "volunteer hours × $28.50/hour BLS rate")
- Known limitations disclosed (e.g., "self-reported by nonprofits")

### Honest About Impact
- Show what we know, not what we guess
- Never make causal claims without evidence
- Attribution is "Daanaa helped facilitate" not "Daanaa caused this donation"

---

## 3. Database Schema

```sql
-- Core impact event log (immutable, append-only)
CREATE TABLE impact_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  org_ein TEXT NOT NULL,
  impact_type TEXT NOT NULL,
    -- 'donation_attributed' | 'volunteer_hours' | 'partnership_savings'
  amount FLOAT NOT NULL,
    -- For donation: $ amount. For volunteer: hours. For savings: $ amount.
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  source TEXT,
    -- 'user_click' | 'nonprofit_claim' | 'system_auto'
  verified BOOLEAN DEFAULT 0,
    -- 0 = self-reported (pending). 1 = verified (nonprofit attestation or audit).
  notes TEXT,
    -- Optional context (e.g., "5 hours at May 15 event")
  FOREIGN KEY (org_ein) REFERENCES registry_enriched(EIN)
);

-- Daily snapshot (for dashboard performance)
CREATE TABLE impact_summary (
  summary_date DATE PRIMARY KEY,
  total_donation_attributed FLOAT DEFAULT 0,
    -- Sum of all donation_attributed amounts
  count_donations_attributed INTEGER DEFAULT 0,
    -- Number of "Daanaa helped" confirmations
  total_volunteer_hours FLOAT DEFAULT 0,
    -- Sum of all volunteer hours reported
  count_volunteer_reports INTEGER DEFAULT 0,
  total_volunteer_value FLOAT DEFAULT 0,
    -- volunteer_hours × $28.50 (BLS avg service rate)
  total_partnership_savings FLOAT DEFAULT 0,
    -- Sum of partnership discount values
  count_partner_transactions INTEGER DEFAULT 0,
  unique_orgs_impacted INTEGER DEFAULT 0,
    -- Count distinct EINs with impact events this day
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Aggregate by organization (for org detail pages)
CREATE TABLE impact_by_org (
  org_ein TEXT PRIMARY KEY,
  donation_attributed FLOAT DEFAULT 0,
  donation_count INTEGER DEFAULT 0,
  volunteer_hours FLOAT DEFAULT 0,
  volunteer_reports INTEGER DEFAULT 0,
  volunteer_value FLOAT DEFAULT 0,
  partnership_savings FLOAT DEFAULT 0,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. User Journeys

### 4.1 Donation Attribution Flow

**Precondition:** User has just donated to an org via their own website (not through Daanaa).

**Journey:**
```
1. User visits daanaa.org/org/[EIN] (e.g., from their browser history)
2. Page displays a banner:
   "Just donated? We love that! If Daanaa helped you find this org, click below 👇"
   [Button: "Yes, Daanaa helped"]
3. User clicks → Record impact event
   - org_ein = target org
   - impact_type = 'donation_attributed'
   - source = 'user_click'
   - verified = 0 (self-reported)
4. Show confirmation: "Thanks! Your click helps us measure impact."
5. Banner disappears for 24h (sessionStorage)
```

**Backend:**
- POST `/api/impact/log-donation-attribution` (no auth required)
- Payload: `{ ein: string }`
- Response: `{ success: true, message: "..." }`
- Rate limit: 1 per org per user per 24h (via IP + EIN cookie)

---

### 4.2 Volunteer Hours Flow

**Precondition:** Nonprofit admin has access to claims portal.

**Journey:**
```
1. Nonprofit admin logs into daanaa.org/claim/[token]/portal
2. In "Confirmed Attendance" section, adds volunteer entry:
   - Volunteer name (optional, for their records)
   - Hours: [5]
   - Date: [May 15, 2026]
   - Description: [Optional, e.g., "Event setup & coordination"]
3. Clicks "Confirm Hours" → Sends volunteer thank you email
4. System logs impact event:
   - org_ein = target org
   - impact_type = 'volunteer_hours'
   - amount = 5
   - source = 'nonprofit_claim'
   - verified = 0 (pending audit)
5. Show feedback: "Recorded. Volunteer email sent."
```

**Backend:**
- POST `/api/impact/log-volunteer-hours` (auth required: org claim token)
- Payload: `{ ein: string, hours: number, date: string, description?: string }`
- Response: `{ success: true, event_id: int, email_sent: bool }`

**Volunteer Thank You Email:**
```
Subject: Thank you for volunteering [X hours] with [Org Name]!

Hi [Name],

[Org Name] just confirmed that you volunteered X hours on [Date].

At current industry rates, that's about $[X × $28.50] of value you contributed 
to your community. Your work matters.

(If you'd like, you can mention this to Daanaa:
daanaa.org/thank-you?hours=X&org=[EIN])

— [Org Name] & Daanaa
```

---

### 4.3 Volunteer Self-Attribution (Optional Future)

Allow volunteers to optionally log their own hours + confirm they helped:

```
1. Volunteer receives thank you email from nonprofit
2. Email includes link: daanaa.org/impact/volunteer-thank-you?hours=5&org=710933434
3. Volunteer (no login required) clicks "Thank you, log my hours"
4. System logs second attribution (volunteer-side confirmation)
5. Impact event updated to verified=1 (cross-confirmed)
```

This is optional and can be added later.

---

## 5. Dashboard & Public Impact Display

### Homepage Impact Widget
```
╔════════════════════════════════════════════╗
║  Daanaa Impact (Last 30 Days)             ║
├────────────────────────────────────────────┤
║  $847,200                                  ║
║  in donations attributed                   ║
║  (1,043 donors confirmed Daanaa helped)    ║
║                                            ║
║  4,821 volunteer hours logged              ║
║  (~$137,297 equivalent value)              ║
║                                            ║
║  347 nonprofits served                     ║
╚════════════════════════════════════════════╝
```

### Org Detail Page Impact Section
```
╔════════════════════════════════════════════╗
║  Community Impact                         ║
├────────────────────────────────────────────┤
║  118 donors found us through Daanaa        ║
║  347 volunteer hours logged (91 events)    ║
║  ~$9,851 equivalent volunteer value        ║
║                                            ║
║  ℹ️ Methodology: volunteer hours × $28.50  ║
║                 (BLS average service rate) ║
╚════════════════════════════════════════════╝
```

### Public Impact Dashboard (daanaa.org/impact)
- 30-day, 12-month, all-time views
- Breakdown by impact type (donation, volunteer, savings)
- Top-10 orgs by volunteer hours
- Growth trend chart
- Full methodology documentation
- **Disclaimer:** "Impact reflects volunteer reports and self-attributed donations. Daanaa does not track giving activity or donor networks."

---

## 6. Verification & Fraud Prevention

### Self-Reported Events (Volunteer Hours)
- **Status:** `verified=0` by default
- **Risk:** Nonprofits over-report hours to inflate impact numbers
- **Mitigation (Phase 1):** 
  - All events logged but marked unverified
  - Public dashboard shows separate counts: "Verified" vs "Reported"
  - Transparent disclosure: "Reported by nonprofits, pending audit"
  
**Example dashboard:**
```
Volunteer Hours Reported: 4,821
  └─ Verified (audited): 847
  └─ Pending Audit: 3,974
```

- **Mitigation (Phase 2, if needed):**
  - Spot-check claims: query for suspicious spikes
  - Cross-reference volunteer thank you emails (did volunteer receive one?)
  - Add volunteer self-attestation (see 4.3 above)
  - Flag orgs with >1000 hours/month for manual review

### Self-Reported Donations (Attribution Clicks)
- **Status:** `verified=0` by default
- **Risk:** Users click "Daanaa helped" without actually donating
- **Mitigation (Phase 1):**
  - Rate-limit: 1 click per user per org per 24h (IP + local storage)
  - Show all donations as "attributed" but note they're self-reported
  - Dashboard: "Donors confirmed Daanaa helped (self-reported)"
  
- **Mitigation (Phase 2, if we add partnerships):**
  - Integrate with donation processors (e.g., PayPal via return URL)
  - Cross-reference: only log attribution if donation detected on same day
  - Nonprofits can attest to donations received

### Audit Trail
- Never delete impact logs (append-only)
- Log corrections as separate events (e.g., `impact_type='volunteer_correction'`)
- Keep full history in database for forensics

---

## 7. API Endpoints

### POST /api/impact/log-donation-attribution
Log a donor's confirmation that Daanaa helped them find an org.

**Request:**
```json
{
  "ein": "710933434"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Thank you! Your click helps us measure impact.",
  "impact_id": 12847
}
```

**Rate limit:** 1 per IP per org per 24h  
**Auth:** None (public)

---

### POST /api/impact/log-volunteer-hours
Log volunteer hours confirmed by a nonprofit.

**Request:**
```json
{
  "ein": "710933434",
  "hours": 5.5,
  "date": "2026-05-15",
  "description": "Event setup and registration"
}
```

**Response (200):**
```json
{
  "success": true,
  "impact_id": 12848,
  "email_sent": true,
  "volunteer_value_estimate": 156.75
}
```

**Auth:** Claim token (nonprofit authenticated)  
**Validation:**
- `hours` > 0 and < 24
- `date` not in future
- `ein` matches org in claim

---

### GET /api/impact/summary
Fetch impact summary for dashboard.

**Query params:**
- `period`: 'day' | 'month' | 'year' | 'all' (default: 'month')
- `org_ein` (optional): filter to single org

**Response (200):**
```json
{
  "period": "month",
  "start_date": "2026-05-17",
  "end_date": "2026-06-17",
  "donation_attributed": 847200,
  "donation_count": 1043,
  "volunteer_hours": 4821,
  "volunteer_reports": 482,
  "volunteer_value": 137297.5,
  "partnership_savings": 0,
  "unique_orgs": 347,
  "verified_fraction": 0.18
}
```

**Auth:** None (public)

---

### GET /api/impact/by-org/:ein
Fetch impact metrics for a specific org.

**Response (200):**
```json
{
  "ein": "710933434",
  "organization_name": "The Beacon of Downtown Houston",
  "donation_attributed": 12500,
  "donation_count": 18,
  "volunteer_hours": 347,
  "volunteer_reports": 91,
  "volunteer_value": 9851.5,
  "verified_fraction": 0.65,
  "last_updated": "2026-06-17T14:22:00Z"
}
```

**Auth:** None (public)

---

## 8. Frontend Components

### DonationAttributionBanner
```tsx
// On org detail page, if not dismissed in past 24h
<DonationAttributionBanner
  org={org}
  onConfirm={(ein) => logDonationAttribution(ein)}
/>
```

Display above the fold, one-time per 24h per org.

### VolunteerHoursForm
```tsx
// In nonprofit claim portal
<VolunteerHoursForm
  claimToken={token}
  orgEin={ein}
  onSubmit={(hours, date, desc) => logVolunteerHours(...)}
/>
```

---

## 9. Backend Implementation

### Daily Summary Refresh (Cron)
```bash
# Every day at 3 AM
0 3 * * * /home/akbar/meritgiving/scripts/refresh_impact_summary.py
```

**Script:**
```python
#!/usr/bin/env python3
"""Refresh impact_summary and impact_by_org tables daily."""
import sqlite3
from datetime import datetime, timedelta

DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"

def refresh_impact_summary():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    # Aggregate all impact events from yesterday
    stats = c.execute("""
        SELECT
            COUNT(CASE WHEN impact_type='donation_attributed' THEN 1 END) as donation_count,
            SUM(CASE WHEN impact_type='donation_attributed' THEN amount ELSE 0 END) as donation_total,
            COUNT(CASE WHEN impact_type='volunteer_hours' THEN 1 END) as volunteer_count,
            SUM(CASE WHEN impact_type='volunteer_hours' THEN amount ELSE 0 END) as volunteer_hours,
            COUNT(CASE WHEN impact_type='partnership_savings' THEN 1 END) as savings_count,
            SUM(CASE WHEN impact_type='partnership_savings' THEN amount ELSE 0 END) as savings_total,
            COUNT(DISTINCT org_ein) as unique_orgs,
            SUM(CASE WHEN verified=1 THEN 1 ELSE 0 END) as verified_count,
            COUNT(*) as total_count
        FROM impact_logs
        WHERE DATE(created_at) = ?
    """, (yesterday,)).fetchone()
    
    # Insert/update summary
    c.execute("""
        INSERT OR REPLACE INTO impact_summary
        (summary_date, total_donation_attributed, count_donations_attributed,
         total_volunteer_hours, count_volunteer_reports, total_volunteer_value,
         total_partnership_savings, count_partner_transactions, unique_orgs_impacted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        yesterday,
        stats[1] or 0,  # donation_total
        stats[0] or 0,  # donation_count
        stats[3] or 0,  # volunteer_hours
        stats[2] or 0,  # volunteer_count
        (stats[3] or 0) * 28.50,  # volunteer_value
        stats[5] or 0,  # savings_total
        stats[4] or 0,  # savings_count
        stats[6] or 0,  # unique_orgs
    ))
    
    # Refresh org-level aggregates
    c.execute("""
        INSERT OR REPLACE INTO impact_by_org
        SELECT
            org_ein,
            SUM(CASE WHEN impact_type='donation_attributed' THEN amount ELSE 0 END),
            COUNT(CASE WHEN impact_type='donation_attributed' THEN 1 END),
            SUM(CASE WHEN impact_type='volunteer_hours' THEN amount ELSE 0 END),
            COUNT(CASE WHEN impact_type='volunteer_hours' THEN 1 END),
            SUM(CASE WHEN impact_type='volunteer_hours' THEN amount ELSE 0 END) * 28.50,
            SUM(CASE WHEN impact_type='partnership_savings' THEN amount ELSE 0 END),
            CURRENT_TIMESTAMP
        FROM impact_logs
        GROUP BY org_ein
    """)
    
    conn.commit()
    conn.close()
    print(f"Impact summary refreshed for {yesterday}")

if __name__ == "__main__":
    refresh_impact_summary()
```

---

## 10. Stewardship Compliance Checklist

- ✅ **P2 (Privacy):** No donor tracking, no giving network. Events are org-level, anonymous.
- ✅ **P3 (Evidence-based):** All metrics tied to real events (confirmed clicks, attested hours).
- ✅ **P4 (Fairness):** Small org volunteers counted equally. No bias toward scale.
- ✅ **P5 (Respect):** All claims voluntary. No shaming, additive framing only.
- ✅ **P6 (Mistakes corrected):** Full audit trail, allow corrections via new events.
- ✅ **P8 (Independence):** No funds handled, no payment processor integration.
- ✅ **P9 (Explainable):** All methodology public. Dashboard shows source & confidence.

---

## 11. Implementation Roadmap

### Phase 1 (MVP) — Weeks 1-2
- [ ] Create impact_logs, impact_summary, impact_by_org tables
- [ ] Implement POST /api/impact/log-donation-attribution
- [ ] Add DonationAttributionBanner to org detail page
- [ ] Add simple impact widget to homepage (30-day totals)
- [ ] Write daily refresh cron job
- [ ] Deploy & monitor

### Phase 2 (Volunteer) — Weeks 3-4
- [ ] Implement POST /api/impact/log-volunteer-hours
- [ ] Add VolunteerHoursForm to nonprofit claim portal
- [ ] Send volunteer thank you emails
- [ ] Update org detail impact section
- [ ] Add verification status to dashboard ("Verified" vs "Pending Audit")
- [ ] Deploy

### Phase 3 (Public Dashboard) — Week 5
- [ ] Build /impact page with 30-day/12-month/all-time views
- [ ] Add trend chart (revenue of impact over time)
- [ ] Document methodology transparently
- [ ] Add audit disclaimer
- [ ] SEO & linking

### Phase 4 (Future) — TBD
- [ ] Volunteer self-attribution (daanaa.org/thank-you?hours=X&org=Y)
- [ ] Partnership savings auto-logging (when discount applied)
- [ ] Leaderboard by org (opt-in)
- [ ] Impact badges for orgs (e.g., "500+ volunteer hours this year")

---

## 12. Open Questions (To Resolve)

1. **Industry rates:** Should volunteer hours use BLS ($28.50) or sector-specific rates?
   - Recommendation: Start with BLS, offer nonprofit override in future
   
2. **Public leaderboard:** Show top 10 orgs by impact? Risk: gaming the metric.
   - Recommendation: Defer to Phase 4, keep feedback channel open
   
3. **Fraud detection:** Should nonprofits pass verification before counting?
   - Recommendation: Start unverified (transparent), add spot-checks in Phase 2
   
4. **Cross-device donation tracking:** If user donates on mobile, clicks on desktop?
   - Recommendation: Accept as inherent limitation. Privacy > precision.
   
5. **Integration with donation processors:** PayPal/Stripe return URLs for verified donations?
   - Recommendation: Out of scope for MVP. Future partnership layer.

---

## 13. Success Metrics

- **Adoption:** % of org detail page visitors who see & interact with donation banner
- **Accuracy:** Volunteer self-attestation rate (Phase 3 validation)
- **Trust:** User feedback on impact transparency
- **Growth:** Daily/monthly growth in logged hours & donations
- **No privacy incidents:** Zero complaints about tracking or data sharing

---

## References

- STEWARDSHIP.md (P2, P3, P4, P5, P8, P9)
- PRIVACY-INVARIANTS.md
- Existing claim portal: `/claim/[token]/portal`
- Org detail: `/org/[ein]`

