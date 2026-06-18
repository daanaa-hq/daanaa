# Sprint 1 Engineer Onboarding

**Start Date:** Aug 1, 2026  
**Duration:** 15 days (Aug 1–15)  
**Role:** Full-stack contract engineer  
**Team:** You (engineer) + Akbar (strategy/decisions)  
**Goal:** Build Daanaa public soft launch (Aug 15)

---

## Before You Start (Jul 15–Aug 1)

**Setup checklist (you do this):**
- [ ] Get access to GitHub repo
- [ ] Clone repo locally + install dependencies
- [ ] Set up local dev environment (Python 3.11, Node 19+, SQLite)
- [ ] Read CLAUDE.md + STEWARDSHIP.md (non-negotiable)
- [ ] Skim the 5 Sprint 1 docs (architecture, tasks, testing, data model)
- [ ] Set up local Elasticsearch or FTS (test search index)

**Setup checklist (Akbar will do):**
- [ ] Slack/email channel for standup + questions
- [ ] Sandbox nonprofits list (50 target organizations, you'll get emails Aug 10)
- [ ] Admin credentials (database, local servers)

---

## Your First Week (Aug 1–5)

### What You're Building

**Phase 1a: Backend Foundation**

Three core pieces to launch discovery:
1. **API service** (FastAPI) with 6 endpoints
2. **Search index** (Elasticsearch or FTS on 1M+ nonprofits)
3. **Nonprofit Onboarding Agent** (validates claims, auto-approves, flags suspicious)

### Daily Standup (9am, 15 min)

**Format:** [What shipped] / [What's building] / [Blockers]

**Example:**
> "Shipped: API scaffold + auth flow + 3 core search endpoints.
> Building: Elasticsearch index ingestion + fuzzy EIN matching.
> Blocker: Need access to IRS BMF CSV for EIN fuzzy match. Who has that?"

**Slack channel:** [TBD]

---

## Task Breakdown (Complete These in Order)

### **Task 1: API Architecture Setup (2 days)**

**Deliverable:** Bare-bones FastAPI server with routes defined

**Steps:**

1. Create FastAPI project scaffold
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary
   mkdir -p app/routes
   ```

2. Define database connection (SQLite local, PostgreSQL on home server)
   ```python
   # app/database.py
   from sqlalchemy import create_engine
   
   # Local SQLite for dev
   LOCAL_DB = "sqlite:///data/merit_registry.db"
   engine = create_engine(LOCAL_DB)
   ```

3. Define core models (ORM classes for registry_enriched, org_claims, wallet_data)
   ```python
   # app/models.py
   from sqlalchemy import Column, String, Integer, Float, JSON, DateTime
   from sqlalchemy.ext.declarative import declarative_base
   
   Base = declarative_base()
   
   class RegistryEnriched(Base):
       __tablename__ = "registry_enriched"
       ein = Column(String, primary_key=True)
       name = Column(String)
       mission = Column(String)
       location = Column(String)
       cause_tags = Column(JSON)
       merit_score_v5 = Column(Float)
       merit_health_signal_v5 = Column(String)  # HEALTHY, STABLE, CAUTION
       is_hidden_gem = Column(Integer)
       donate_url = Column(String)
   
   class OrgClaim(Base):
       __tablename__ = "org_claims"
       id = Column(Integer, primary_key=True)
       org_ein = Column(String)
       claimer_email = Column(String)
       claimer_name = Column(String)
       status = Column(String)  # approved, flagged, rejected
       approved_at = Column(DateTime)
       approved_by = Column(String)  # "agent" or "human"
   ```

4. Create route stubs (just return `{"status": "ok"}` for now)
   ```python
   # app/main.py
   from fastapi import FastAPI
   from app.routes import search, claims, wallet
   
   app = FastAPI()
   
   app.include_router(search.router, prefix="/api")
   app.include_router(claims.router, prefix="/api")
   app.include_router(wallet.router, prefix="/api")
   
   @app.get("/health")
   async def health():
       return {"status": "ok"}
   ```

5. Test locally
   ```bash
   uvicorn app.main:app --reload --port 5000
   # GET http://localhost:5000/health → {"status": "ok"}
   ```

6. Commit
   ```bash
   git add app/
   git commit -m "feat: API scaffold + database models + route stubs"
   ```

**Checkpoint:** API starts, returns health check. DB models defined.

---

### **Task 2: Search Index (Elasticsearch or FTS) (2 days)**

**Deliverable:** 1M+ nonprofits indexed, searchable by keyword + filters

**Steps:**

1. **Option A: PostgreSQL Full-Text Search (simpler)**
   
   Create FTS index on registry_enriched:
   ```python
   # scripts/build_fts_index.py
   from sqlalchemy import text
   
   # Create FTS virtual table
   engine.execute(text("""
       CREATE VIRTUAL TABLE org_fts USING fts5(
           ein UNINDEXED,
           name,
           mission,
           location,
           cause_tags
       );
   """))
   
   # Populate from registry_enriched
   engine.execute(text("""
       INSERT INTO org_fts (ein, name, mission, location, cause_tags)
       SELECT ein, name, mission, location, cause_tags
       FROM registry_enriched;
   """))
   ```

2. **Option B: Elasticsearch (more powerful)**
   
   ```python
   # app/search.py
   from elasticsearch import Elasticsearch
   
   es = Elasticsearch(["http://localhost:9200"])
   
   # Index definition
   mapping = {
       "properties": {
           "ein": {"type": "keyword"},
           "name": {"type": "text"},
           "mission": {"type": "text"},
           "location": {"type": "keyword"},
           "cause_tags": {"type": "keyword"},
           "merit_score_v5": {"type": "float"},
           "merit_health_signal_v5": {"type": "keyword"},
           "is_hidden_gem": {"type": "boolean"}
       }
   }
   
   es.indices.create(index="nonprofits", body={"mappings": mapping})
   ```

3. Bulk ingest 1M orgs (batch insert, ~10K at a time)
   ```python
   # scripts/bulk_index.py
   from app.database import SessionLocal
   from app.search import es
   
   db = SessionLocal()
   batch = []
   for org in db.query(RegistryEnriched).all():
       batch.append(org.to_dict())
       if len(batch) >= 10000:
           es.bulk(bulk_data_generator(batch))
           batch = []
   ```

4. Test search query
   ```python
   # Test: search for "climate" in mission
   results = es.search(index="nonprofits", body={
       "query": {"match": {"mission": "climate"}},
       "size": 20
   })
   ```

5. Commit
   ```bash
   git add scripts/bulk_index.py app/search.py
   git commit -m "feat: search index — Elasticsearch bulk ingest (1M orgs)"
   ```

**Checkpoint:** 1M orgs indexed. Search returns results for test queries.

---

### **Task 3: Nonprofit Onboarding Agent MVP (2 days)**

**Deliverable:** Endpoint that validates nonprofit claims, auto-approves or flags for review

**Steps:**

1. Create agent logic (EIN fuzzy match + email domain check + website validation)
   ```python
   # app/agents/onboarding_agent.py
   from fuzzywuzzy import fuzz
   from urllib.parse import urlparse
   import requests
   
   def validate_ein_fuzzy(irs_ein, provided_ein, org_name, threshold=80):
       """Fuzzy match EIN (allow typos). Return score 0-100."""
       score = fuzz.ratio(provided_ein, irs_ein)
       # If exact match on name too, boost score
       if org_name in irs_data.get(provided_ein, {}).get("name", ""):
           score = min(100, score + 10)
       return score >= threshold
   
   def validate_email_domain(email, website):
       """Check if email domain matches website domain."""
       email_domain = email.split("@")[1].lower()
       website_domain = urlparse(website).netloc.lower()
       return email_domain == website_domain
   
   def validate_website_reachable(url):
       """Quick check that website responds (HEAD request, 2–3 sec timeout)."""
       try:
           resp = requests.head(url, timeout=3, allow_redirects=True)
           return resp.status_code < 400
       except:
           return False
   
   def process_claim(claim_request):
       """Main agent logic."""
       # Step 1: Validate EIN
       irs_match = validate_ein_fuzzy(
           claim_request.org_ein,
           claim_request.org_name
       )
       if not irs_match:
           return {"status": "flagged", "reason": "EIN/name mismatch"}
       
       # Step 2: Check email domain
       domain_match = validate_email_domain(
           claim_request.claimer_email,
           claim_request.website
       )
       if not domain_match:
           return {"status": "flagged", "reason": "Email domain mismatch"}
       
       # Step 3: Check website reachable
       site_ok = validate_website_reachable(claim_request.website)
       if not site_ok:
           return {"status": "flagged", "reason": "Website unreachable"}
       
       # Step 4: Auto-approve
       return {"status": "approved"}
   ```

2. Create claims endpoint
   ```python
   # app/routes/claims.py
   from fastapi import APIRouter, HTTPException
   from app.models import OrgClaim
   from app.agents.onboarding_agent import process_claim
   
   router = APIRouter()
   
   @router.post("/claims/submit")
   async def submit_claim(claim_request: ClaimRequest):
       """Nonprofit claims their profile."""
       # Run agent
       result = process_claim(claim_request)
       
       # Create record
       org_claim = OrgClaim(
           org_ein=claim_request.org_ein,
           claimer_email=claim_request.claimer_email,
           claimer_name=claim_request.claimer_name,
           status=result["status"],
           approved_by="agent" if result["status"] == "approved" else None
       )
       db.add(org_claim)
       db.commit()
       
       # Send email confirmation
       if result["status"] == "approved":
           send_email(
               claim_request.claimer_email,
               "Your profile is claimed!"
           )
       else:
           send_email(
               claim_request.claimer_email,
               f"Your claim needs review: {result['reason']}"
           )
       
       return result
   ```

3. Write tests
   ```python
   # tests/test_onboarding_agent.py
   def test_fuzzy_match_ein():
       assert validate_ein_fuzzy("001234567", "001234568", "Save the World") == True
       assert validate_ein_fuzzy("001234567", "999999999", "Different Org") == False
   
   def test_email_domain_match():
       assert validate_email_domain("ceo@nonprofit.org", "https://nonprofit.org") == True
       assert validate_email_domain("ceo@gmail.com", "https://nonprofit.org") == False
   ```

4. Commit
   ```bash
   git add app/agents/ app/routes/claims.py tests/test_onboarding_agent.py
   git commit -m "feat: nonprofit onboarding agent — fuzzy EIN + email domain + website validation"
   ```

**Checkpoint:** Agent validates 5 test claims. 80%+ auto-approve rate for good data.

---

## Second Week (Aug 5–12)

### **Task 4: Search Page (React Frontend) (2 days)**

Build the frontend `/search` route with live search, filters, results grid.

**Spec:** `SPRINT_1_ARCHITECTURE.md` → Frontend Layer → Routes

**Deliverable:** Functional search UI connected to `/api/orgs` endpoint

---

### **Task 5: Nonprofit Detail Page (2.5 days)**

Build `/org/{ein}` detail page with financial context, health signals, similar orgs.

**Spec:** `SPRINT_1_ARCHITECTURE.md` → Data Flow Example 1

---

### **Task 6: Wallet Page (1.5 days)**

Build `/wallet` page showing bookmarks + giving intent, localStorage persistence.

---

### **Task 7: Nonprofit Claim Form (1.5 days)**

Build `/claim` form with multi-step submission → triggers agent.

---

## Third Week (Aug 12–15)

### **Task 8–12: Integration, Testing, Bug Fixes (4 days)**

Integrate API with frontend, run test suite, fix bugs, verify performance, QA against SPRINT_1_TESTING_STRATEGY.md.

---

## Decision-Making Protocol

**You decide:** Technical implementation, architecture choices, testing approach, code style  
**Akbar decides:** Feature scope, nonprofit language/copy, partner impact, deadline extensions  
**Together:** If a technical choice affects product fairness/privacy (use STEWARDSHIP.md P2/P4/P7 as tie-breaker)

**Escalation:** If you hit a blocker that requires a product decision, flag it in standup. Akbar responds same day.

---

## Definitions of Done

**Daily:**
- Standup attended (9am, 15 min)
- Code changes have tests
- Commit message is clear (what changed, why)

**Task-level:**
- Tests pass locally + in CI
- Code compiles/runs without errors
- No console warnings/errors
- Commit pushed to branch

**Sprint-level (Aug 15):**
- All 12 tasks complete
- Manual QA checklist (SPRINT_1_TESTING_STRATEGY.md) 100% done
- Zero critical bugs
- Performance targets met (<500ms search, <200ms detail)
- Ready for production deploy

---

## Resources

**Codebase:**
- GitHub repo: [URL]
- Local path: `/home/akbar/meritgiving`
- API port: 5000
- Frontend port: 5173

**Documentation:**
- CLAUDE.md — rules + conventions
- SPRINT_1_ARCHITECTURE.md — system design
- SPRINT_1_TASK_BREAKDOWN.md — task details
- DATA_MODEL_SPRINT_1.md — database schema
- SPRINT_1_TESTING_STRATEGY.md — testing plan

**People:**
- Akbar (strategy, decisions) — akbar.khowaja@gmail.com
- You (engineering) — [Your contact]
- Slack: [Channel]

---

**Owner:** Engineer + Akbar  
**Status:** Pre-start (Aug 1 begins)  
**Success:** Aug 15 public soft launch on schedule
