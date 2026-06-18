# Sprint 1 Architecture — System Design

**Scope:** How everything connects (frontend, backend, agents, database, infrastructure)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DAANAA PLATFORM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  DONOR SIDE      │         │  NONPROFIT SIDE  │             │
│  │  (React SPA)     │         │  (React SPA)     │             │
│  ├──────────────────┤         ├──────────────────┤             │
│  │ Search Page      │         │ Claim Form       │             │
│  │ Detail Page      │         │ Admin Dashboard  │             │
│  │ Wallet Page      │         │ Profile Editor   │             │
│  │ (localStorage)   │         │ (Google OAuth)   │             │
│  └────────┬─────────┘         └────────┬─────────┘             │
│           │                            │                        │
│           └────────────────┬───────────┘                        │
│                            │                                    │
│                    ┌───────▼─────────┐                         │
│                    │   FastAPI       │                         │
│                    │   Backend       │                         │
│                    ├─────────────────┤                         │
│                    │ /api/orgs       │                         │
│                    │ /api/claims     │                         │
│                    │ /api/wallet     │                         │
│                    │ /api/auth       │                         │
│                    └───────┬─────────┘                         │
│                            │                                    │
│        ┌───────────────────┼───────────────────┐               │
│        │                   │                   │               │
│   ┌────▼────┐    ┌────────▼────────┐   ┌──────▼───┐           │
│   │ Agents  │    │   PostgreSQL    │   │Elasticsearch│        │
│   ├────────┤    │   Database      │   │   Index   │          │
│   │Claim   │    ├─────────────────┤   └──────────┘           │
│   │Onboard │    │ registry        │                          │
│   │Supprt  │    │ org_claims      │                          │
│   │Triage  │    │ wallet_data     │                          │
│   └────────┘    │ volunteer_      │                          │
│                 │   signals       │                          │
│                 └────────────────┘                           │
│                                                               │
│                   LOCAL INFERENCE                            │
│                   ├─ Qwen2.5 (port 11437)                   │
│                   └─ mxbai-embed (port 11436)               │
│                                                               │
└─────────────────────────────────────────────────────────────────┘

                         INFRASTRUCTURE
                   ┌─────────────────────────────┐
                   │   Home Server (Ryzen 9700X) │
                   │   + R9700 32GB GPU          │
                   │   ├─ FastAPI               │
                   │   ├─ PostgreSQL            │
                   │   ├─ Agents (APScheduler) │
                   │   ├─ Inference (llama.cpp)│
                   └─────────────────────────────┘
                   
                   ┌─────────────────────────────┐
                   │   Droplet (Linode)          │
                   │   ├─ Nginx (reverse proxy) │
                   │   ├─ Frontend (SPA)        │
                   │   └─ API requests → home   │
                   └─────────────────────────────┘
```

---

## Layer-by-Layer Details

### 1. Frontend Layer (React SPA)

**Framework:** React 19 + TypeScript + Vite  
**Build output:** `frontend/dist/`  
**Hosted on:** Droplet (Nginx serves `/`)

**Routes:**
```
/search              → Donor search (Task 4)
/org/{ein}          → Nonprofit detail (Task 5)
/wallet             → Donor wallet (Task 6)
/claim              → Nonprofit claim form (Task 7)
/nonprofits/{ein}   → Nonprofit dashboard (Sprint 2)
```

**State Management:**
- **CompareContext** (existing): holds compare selection
- **Wallet Context** (new): donor bookmarks + intent
- **Auth Context** (new): Google OAuth status

**Local Storage:**
```javascript
{
  wallet: {
    bookmarks: ["ein_1", "ein_2"],
    giving_intent: [
      { ein: "ein_1", status: "interested", timestamp: "..." }
    ]
  }
}
```

**API Calls:**
```javascript
GET /api/orgs?q=&cause=&location=&health=
GET /api/orgs/{ein}
POST /api/wallet/add-bookmark
POST /api/wallet/add-intent
POST /api/claims/submit
GET /api/auth/me (if logged in)
```

---

### 2. Backend Layer (FastAPI)

**Language:** Python 3.11  
**Framework:** FastAPI + SQLAlchemy  
**Port:** 5000 (local) / proxied via Nginx on droplet

**Endpoints (Sprint 1 MVP):**

```python
# Search
GET /api/orgs?q={query}&cause={cause}&location={location}&health={health}&hidden_gem={bool}&page={page}
  → Returns: {results: [...], total, page, per_page}

# Nonprofit Detail
GET /api/orgs/{ein}
  → Returns: full nonprofit profile + financial context + similar orgs

# Nonprofit Claiming
POST /api/claims/submit
  Body: {org_ein, org_name, website, claimer_email, claimer_name, mission}
  → Triggers Onboarding Agent
  → Returns: {status: "approved"|"flagged", message, profile_url}

# Wallet
GET /api/wallet (requires Google auth)
  → Returns: {bookmarks, giving_intent, total_bookmarked, total_interested}

POST /api/wallet/add-bookmark
  Body: {ein}
  → Stores in localStorage (client) + wallet_data table (server if logged in)

POST /api/wallet/add-intent
  Body: {ein, intent_type: "giving"|"volunteer"|"board"}
  → Stores intent signal

# Authentication
GET /api/auth/me
  → Returns: {logged_in: bool, email: "...", name: "..."}

POST /api/auth/logout
  → Clears Google auth
```

**Response Caching:**
- Search results: 5 min TTL (in-memory cache)
- Nonprofit detail: 10 min TTL
- Wallet: not cached (always fresh)

---

### 3. Database Layer (PostgreSQL)

**Host:** Home server (localhost:5432)  
**Primary:** `merit_registry.db` (existing)  
**Tables (Sprint 1):**
- `registry_enriched` (1M+ nonprofits, existing + new columns)
- `org_claims` (new, nonprofit claims)
- `wallet_data` (new, optional server-side backup)

**Indexes:** (see DATA_MODEL_SPRINT_1.md)

---

### 4. Search Index (Elasticsearch)

**Host:** Home server (port 9200, optional)  
**Alternative:** PostgreSQL full-text search

**If Elasticsearch:**
- Index: `nonprofits` (1M+ docs)
- Fields: name, mission, location, cause, health_signal
- Shards: 1 (for home server)

**Query example:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "mission": "climate" } }
      ],
      "filter": [
        { "term": { "location": "texas" } },
        { "term": { "health_signal": "HEALTHY" } },
        { "term": { "is_hidden_gem": true } }
      ]
    }
  }
}
```

---

### 5. Agents (APScheduler)

**Framework:** APScheduler (local, in-process)  
**Language:** Python

**Agent 1: Nonprofit Onboarding Agent (Sprint 1)**
```
Trigger: POST /api/claims/submit
         ↓
Process: 1. Validate EIN (fuzzy match vs IRS database)
         2. Check email domain (verify or flag)
         3. Check website reachability
         ↓
Decision: Auto-approve? → Create org_claim record + email
          Flagged? → Add to manual review queue
          Rejected? → Return error + reason
          ↓
Output: Email to claimer + entry in org_claims table
```

**Pseudo-code:**
```python
@app.post("/api/claims/submit")
async def submit_claim(claim: ClaimRequest):
    # Step 1: Validate EIN
    irs_match = fuzzy_match_irs(claim.org_ein, claim.org_name)
    if irs_match < 0.8:
        return {"status": "flagged", "reason": "EIN/name mismatch"}
    
    # Step 2: Verify email domain
    email_domain = claim.claimer_email.split("@")[1]
    org_domain = urlparse(claim.website).netloc
    if email_domain != org_domain:
        return {"status": "flagged", "reason": "Email domain doesn't match website"}
    
    # Step 3: Create claim
    org_claim = OrgClaim(
        org_ein=claim.org_ein,
        status="approved",
        approved_by="agent",
        approved_at=now()
    )
    db.add(org_claim)
    db.commit()
    
    # Step 4: Send email
    send_email(claim.claimer_email, "profile_claimed.html")
    
    return {"status": "approved", "profile_url": f"/orgs/{claim.org_ein}"}
```

**Agent 2: Support Triage Agent (Sprint 1)**
```
Trigger: New email arrives at support@daanaa.org
         ↓
Process: 1. Parse email
         2. Classify: nonprofit-claim-q / search-help / bug / volunteer / other
         3. Draft response template
         4. Send to Akbar for approval (human-in-loop)
         ↓
Decision: Human approves → Send
          Human edits → Send edited version
          Human rejects → Mark for Akbar to handle manually
          ↓
Output: Email response + log entry
```

**Pseudo-code:**
```python
async def triage_support_email(email: EmailMessage):
    # Step 1: Classify
    classification = classify_email(email.body)
    # Output: "nonprofit-claim-q", "search-help", etc.
    
    # Step 2: Draft response
    template = RESPONSE_TEMPLATES[classification]
    draft = template.format(sender_name=email.from_name)
    
    # Step 3: Queue for approval
    approval_queue.add({
        "email_id": email.id,
        "from": email.from_email,
        "subject": email.subject,
        "classification": classification,
        "draft_response": draft
    })
    
    # Step 4: Notify Akbar (async)
    notify_akbar("New support email awaiting approval")
    
    # Step 5: Wait for human approval (in separate UI)
    # Human clicks [Approve] or [Edit] in dashboard
    # → Send email + log
```

---

### 6. Infrastructure (Home Server + Droplet)

**Home Server (Ryzen 9700X + R9700 32GB GPU):**
- FastAPI (port 5000)
- PostgreSQL (port 5432)
- Elasticsearch (port 9200, optional)
- APScheduler agents
- Inference: Qwen2.5 (11437) + mxbai-embed (11436)

**Droplet (Linode, 1 CPU / 2GB RAM):**
- Nginx (reverse proxy)
- React SPA (frontend build)
- SSL certificates
- Redirect API calls to home server (SSH tunnel)

**SSH Tunnel (home → droplet):**
```bash
ssh -N -L 5000:localhost:5000 root@droplet_ip
# Droplet Nginx config:
# location /api { proxy_pass http://localhost:5000; }
```

---

## Data Flow Examples

### Example 1: Donor Searches + Adds to Wallet

```
1. Donor goes to daanaa.org/search
2. Types "climate" → frontend calls GET /api/orgs?q=climate
3. Backend queries Elasticsearch → returns 100 results
4. Donor clicks nonprofit → frontend loads GET /api/orgs/ein_123
5. Donor clicks [+ Add to Wallet]
   → POST /api/wallet/add-bookmark {ein: "ein_123"}
   → Stored in localStorage (client)
   → If logged in: also stored in wallet_data table (server)
6. Donor clicks [Interested in Giving]
   → POST /api/wallet/add-intent {ein: "ein_123", intent: "giving"}
   → Stored in localStorage + server
7. Wallet page shows: 1 bookmarked, 1 interested
```

### Example 2: Nonprofit Claims Profile

```
1. Nonprofit goes to daanaa.org/claim
2. Fills form: org_ein="001234567", website="https://nonprofit.org", email="ceo@nonprofit.org"
3. Clicks [Claim Profile]
   → POST /api/claims/submit
   → Onboarding Agent receives request
   → Validates EIN (fuzzy match) ✓
   → Checks email domain (nonprofit.org ✓ matches website)
   → Checks website reachable (✓)
   → Creates org_claim record (status="approved")
   → Sends welcome email: "Your profile is claimed!"
4. Nonprofit sees profile at daanaa.org/orgs/001234567
5. Can edit profile + see stats (Sprint 2)
```

### Example 3: Support Email → Triage Agent

```
1. Nonprofit emails support@daanaa.org: "How do I claim my profile?"
2. Support Triage Agent:
   → Parses email
   → Classifies: "nonprofit-claim-q"
   → Drafts: "Hi [Name], to claim your profile..."
   → Queues for approval
   → Notifies Akbar
3. Akbar sees in admin dashboard:
   → Email from: nonprofit@org.org
   → Classification: nonprofit-claim-q
   → Draft response: [text]
   → [Approve] [Edit] [Reject]
4. Akbar clicks [Approve]
   → Email sent to nonprofit
   → Logged in support ticket system
```

---

## Deployment Pipeline (Sprint 1)

### Step 1: Local Development
- Engineer builds locally on home server
- Tests with `pytest` + manual QA
- Pushes to GitHub

### Step 2: Staging
- Pull latest from main
- Run migrations
- Test full flow (search → claim → wallet)

### Step 3: Production (Aug 15)
- Deploy frontend to droplet (`npm run build`)
- Deploy backend to home server (restart FastAPI)
- Update Nginx on droplet
- Test from production URLs

### Rollback
- Keep previous version in git tag
- 1-click rollback: checkout tag + restart services

---

## Monitoring & Alerting (Sprint 1 Minimal)

**Uptime:**
- `/health` endpoint (returns 200 if all systems operational)
- Check every 5 min

**Logs:**
- FastAPI: stdout to file (`logs/api.log`)
- Agents: stdout to file (`logs/agents.log`)
- Nginx: access + error logs

**Alerts:**
- API returns 500 → email Akbar
- Database connection lost → email Akbar
- Search index stale → email Akbar

---

## Security (Sprint 1 Baseline)

**HTTPS:** Yes (Cloudflare SSL on droplet)  
**Google OAuth:** For wallet sync (optional, not required)  
**API Rate Limiting:** 100 req/min per IP  
**Database:** No PII except Google email (if logged in)  
**Secrets:** Environment variables only (`.env` file, not in git)

---

**Owner:** System Architect  
**Status:** Ready to implement  
**Next:** Engineer builds Sprint 1 per SPRINT_1_TASK_BREAKDOWN.md

---

*Created: Jun 18, 2026*  
*Last updated: Jun 18, 2026*
