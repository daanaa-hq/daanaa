# Data Model — Sprint 1 (Aug 1–15)

**Scope:** Minimum viable schema for donor search + nonprofit claiming

---

## Tables (New & Updated)

### 1. `registry_enriched` (Existing, Extended)

**Purpose:** Master nonprofit data + scores

**New columns (if not already present):**
```sql
ALTER TABLE registry_enriched ADD COLUMN (
  merit_score_v5 INT,                    -- 0-100 peer percentile
  merit_archetype_v5 VARCHAR(50),        -- Donation-Funded / Fee-for-Service / Endowment-Funded
  merit_band_v5_label VARCHAR(50),       -- Micro / Professional / Established
  merit_health_signal_v5 VARCHAR(20),    -- HEALTHY / STABLE / CAUTION
  is_hidden_gem BOOLEAN DEFAULT FALSE,   -- Small, healthy, overlooked
  donate_url VARCHAR(255),               -- Verified donation link
  donate_confidence INT,                 -- 0-100 confidence
  website VARCHAR(255),                  -- Nonprofit website
  INDEX (merit_archetype_v5),
  INDEX (merit_band_v5_label),
  INDEX (is_hidden_gem)
);
```

**Why:**
- Financial context already computed (v5 scorer)
- Hidden gem status already flagged
- Donation link already verified (pipeline exists)
- Website already scraped

---

### 2. `org_claims` (New)

**Purpose:** Track nonprofit profile claims

```sql
CREATE TABLE org_claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_ein VARCHAR(50) UNIQUE NOT NULL,
  org_name VARCHAR(255),
  claimer_email VARCHAR(255) NOT NULL,
  claimer_name VARCHAR(255),
  website_verified BOOLEAN DEFAULT FALSE,
  irs_verified BOOLEAN DEFAULT FALSE,
  email_domain_verified BOOLEAN DEFAULT FALSE,
  
  -- Profile fields (optional at claim, required to publish)
  mission_statement TEXT,
  donation_link VARCHAR(255),
  
  -- Volunteer & Board (Sprint 2, but schema ready)
  looking_for_volunteers BOOLEAN DEFAULT FALSE,
  volunteer_skills_needed JSON,           -- ["grant-writing", "fundraising"]
  volunteer_notes TEXT,
  looking_for_board_members BOOLEAN DEFAULT FALSE,
  board_notes TEXT,
  
  -- Metadata
  status ENUM('pending', 'approved', 'flagged', 'rejected') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  approved_at TIMESTAMP,
  approved_by VARCHAR(255),               -- Agent or human reviewer
  rejection_reason TEXT,
  
  INDEX (org_ein),
  INDEX (status, created_at),
  INDEX (claimer_email)
);
```

**Why:**
- Track claim lifecycle (pending → approved)
- Store verification state (email domain, IRS, website)
- Audit trail (who approved, when)
- Foundation for volunteer matching (Sprint 2)

---

### 3. `wallet_data` (New, Optional Server-Side Backup)

**Purpose:** Store wallet data server-side (optional; primary is localStorage + Google account)

```sql
CREATE TABLE wallet_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  donor_email VARCHAR(255) UNIQUE NOT NULL,  -- Google account email (consent required)
  donor_name VARCHAR(255),
  
  bookmarks JSON,                  -- ["ein_1", "ein_2", "ein_3"]
  giving_intent JSON,              -- [{"ein": "ein_1", "status": "interested", "timestamp": "..."}]
  
  -- Sprint 2 additions (schema ready, not used in Sprint 1)
  volunteer_interests JSON,        -- [{"ein": "ein_1", "skills": [...], "hours": "..."}]
  board_interests JSON,            -- [{"ein": "ein_2", "experience": "nonprofit-board"}]
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  UNIQUE KEY (donor_email),
  INDEX (last_updated)
);
```

**Why:**
- Server-side backup (if donor loses localStorage)
- Sync point for Google account login
- Foundation for Sprint 2 volunteer signals
- Privacy: only stored if donor explicitly logs in

---

### 4. `volunteer_signals` (New, Sprint 2)

**Purpose:** Aggregate volunteer interest

```sql
CREATE TABLE volunteer_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_ein VARCHAR(50) NOT NULL,
  donor_email VARCHAR(255) NOT NULL,
  donor_name VARCHAR(255),
  
  signal_type ENUM('volunteer', 'board') NOT NULL,
  skills JSON,                     -- ["grant-writing", "fundraising"]
  hours_per_month VARCHAR(50),     -- "4-8", "8-16", "16+"
  board_experience VARCHAR(255),   -- "nonprofit-board", "corporate-board", "none"
  donor_message TEXT,              -- Optional: "I specialize in..."
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status ENUM('active', 'withdrawn') DEFAULT 'active',
  contacted_at TIMESTAMP,
  
  INDEX (org_ein, signal_type),
  INDEX (donor_email),
  INDEX (created_at),
  UNIQUE KEY (org_ein, donor_email, signal_type)
);
```

**Why:**
- Aggregate volunteers/board candidates per org
- Track withdraw status (privacy control)
- Metadata (contacted date, message)
- Ready for Sprint 2 launch (Sep 1)

---

### 5. `volunteer_signal_summary` (Materialized View, Sprint 2)

**Purpose:** Pre-compute aggregate counts (used in nonprofit dashboard)

```sql
CREATE VIEW volunteer_signal_summary AS
SELECT 
  org_ein,
  signal_type,
  COUNT(*) as total_interested,
  JSON_OBJECT(
    'grant_writing', COUNT(CASE WHEN skills LIKE '%grant-writing%' THEN 1 END),
    'fundraising', COUNT(CASE WHEN skills LIKE '%fundraising%' THEN 1 END),
    'communications', COUNT(CASE WHEN skills LIKE '%communications%' THEN 1 END),
    'operations', COUNT(CASE WHEN skills LIKE '%operations%' THEN 1 END),
    'board_service', COUNT(CASE WHEN skills LIKE '%board-service%' THEN 1 END),
    'finance', COUNT(CASE WHEN skills LIKE '%finance%' THEN 1 END),
    'tech', COUNT(CASE WHEN skills LIKE '%tech%' THEN 1 END),
    'program_design', COUNT(CASE WHEN skills LIKE '%program-design%' THEN 1 END)
  ) as skills_breakdown,
  COUNT(CASE WHEN hours_per_month = '4-8' THEN 1 END) as hours_4_8,
  COUNT(CASE WHEN hours_per_month = '8-16' THEN 1 END) as hours_8_16,
  COUNT(CASE WHEN hours_per_month = '16+' THEN 1 END) as hours_16_plus
FROM volunteer_signals
WHERE status = 'active'
GROUP BY org_ein, signal_type;
```

**Why:**
- Efficient nonprofit dashboard (pre-computed)
- Breakdown by skill + hours
- Used in Sprint 2, but schema in Sprint 1

---

## API Data Structures

### Search Results (GET /api/orgs)

```json
{
  "results": [
    {
      "ein": "001234567",
      "name": "Save the World Foundation",
      "mission": "Combating climate change through local action",
      "location": "Austin, TX",
      "archetype": "Donation-Funded",
      "revenue_band": "Professional",
      "health_signal": "HEALTHY",
      "percentile_rank": 78,
      "is_hidden_gem": true,
      "website": "https://savetheworld.org",
      "donation_link": "https://savetheworld.org/donate",
      "donation_link_verified": true
    }
  ],
  "total": 1200000,
  "page": 1,
  "per_page": 20,
  "filters_applied": {
    "cause": "environment",
    "location": "texas",
    "health": "healthy",
    "hidden_gem": true
  }
}
```

### Nonprofit Detail (GET /api/orgs/{ein})

```json
{
  "ein": "001234567",
  "name": "Save the World Foundation",
  "mission_full": "We work with local communities across Texas to implement climate resilience programs...",
  "location": "Austin, TX 78704",
  "website": "https://savetheworld.org",
  "founded": 1995,
  
  "financial_context": {
    "archetype": "Donation-Funded",
    "revenue_band": "Professional ($150K–$700K)",
    "total_revenue_fy2024": 450000,
    "health_signal": "HEALTHY",
    "health_explanation": "Revenue growth over 3 years, low debt, strong liquidity",
    "percentile_rank": 78,
    "peer_comparison": "Top 22% of peers in cause category"
  },
  
  "visibility": {
    "is_hidden_gem": true,
    "why_hidden_gem": "Small, financially healthy, overlooked (media mentions <5/year)"
  },
  
  "giving": {
    "donation_link": "https://savetheworld.org/donate",
    "donation_link_verified": true,
    "donation_link_type": "direct (nonprofit-owned)"
  },
  
  "similar_orgs": [
    {
      "ein": "...",
      "name": "Climate Justice Alliance",
      "location": "Austin, TX"
    }
  ]
}
```

### Wallet (GET /api/wallet)

```json
{
  "donor_email": "jane@example.com",
  "bookmarks": [
    {
      "ein": "001234567",
      "name": "Save the World Foundation",
      "mission_excerpt": "Local climate action...",
      "added_at": "2026-08-10T14:32:00Z",
      "status": "bookmarked"
    }
  ],
  "giving_intent": [
    {
      "ein": "001234567",
      "name": "Save the World Foundation",
      "status": "interested",
      "added_at": "2026-08-10T14:35:00Z"
    }
  ],
  "total_bookmarked": 12,
  "total_interested": 5
}
```

### Claim Form Submit (POST /api/claims/submit)

```json
{
  "org_ein": "001234567",
  "org_name": "Save the World Foundation",
  "website": "https://savetheworld.org",
  "claimer_email": "director@savetheworld.org",
  "claimer_name": "Jane Smith",
  "mission_statement": "We work with local communities..."
}
```

**Response (Success):**
```json
{
  "status": "approved",
  "message": "Profile claimed successfully! Your nonprofit is now visible to donors.",
  "profile_url": "https://daanaa.org/orgs/001234567",
  "next_steps": "Update your profile with more details or claim a badge"
}
```

**Response (Flagged):**
```json
{
  "status": "flagged",
  "message": "We need to verify your organization. You'll receive an email within 24 hours.",
  "reason": "Email domain doesn't match nonprofit website"
}
```

---

## Indexing Strategy

### Elasticsearch Mapping (for search)

```json
{
  "mappings": {
    "properties": {
      "ein": { "type": "keyword" },
      "name": { "type": "text", "analyzer": "standard" },
      "mission": { "type": "text", "analyzer": "standard" },
      "location": { "type": "geo_point" },
      "archetype": { "type": "keyword" },
      "revenue_band": { "type": "keyword" },
      "health_signal": { "type": "keyword" },
      "is_hidden_gem": { "type": "boolean" },
      "ntee_category": { "type": "keyword" },
      "created_at": { "type": "date" }
    }
  }
}
```

**Why:** Fast full-text search + filtering on 1M+ records.

---

## Data Integrity & Privacy

### Constraints (Privacy-First)

```sql
-- Wallet data only stored with explicit consent
ALTER TABLE wallet_data 
ADD CONSTRAINT donor_email_not_null CHECK (donor_email IS NOT NULL);

-- Volunteer signals only created when donor signals explicitly
ALTER TABLE volunteer_signals 
ADD CONSTRAINT signal_has_timestamp CHECK (created_at IS NOT NULL);

-- Claims can only be approved by agent or human
ALTER TABLE org_claims 
ADD CONSTRAINT approved_by_required_if_approved CHECK (
  (status = 'approved' AND approved_by IS NOT NULL) OR status != 'approved'
);
```

### Data Retention Policy

- **Wallet data:** Deleted if donor account inactive 1 year
- **Volunteer signals:** Deleted if status = withdrawn (immediately)
- **Org claims:** Archived (never deleted, audit trail)

---

## Migration Path (Sep 1 → Sprint 2)

When adding volunteer matching (Sep 1):
1. `org_claims` already has `looking_for_volunteers` + `volunteer_skills_needed` columns → no migration needed
2. `wallet_data` already has `volunteer_interests` + `board_interests` → no migration needed
3. Create `volunteer_signals` table (new)
4. Create `volunteer_signal_summary` view (new)
5. Populate `volunteer_signals` from any existing volunteer intent data

**Zero data loss.** Schema ready for Sprint 2 on day 1 of Sprint 1.

---

## Performance Targets (Sprint 1)

| Operation | Target | How |
|-----------|--------|-----|
| Search 1M orgs | <500ms | Elasticsearch index |
| Nonprofit detail | <200ms | Direct DB query + cache |
| Wallet load | <100ms | localStorage (client) |
| Claim submission | <2s | Async validation + agent |

---

**Owner:** Database Architecture  
**Status:** Ready to migrate  
**Next:** Engineer implements schema + indexes Aug 1

---

*Created: Jun 18, 2026*  
*Last updated: Jun 18, 2026*
