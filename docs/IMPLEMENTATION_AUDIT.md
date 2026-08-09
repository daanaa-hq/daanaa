# Implementation Audit — What's Built vs. What's Left

**Date:** Aug 9, 2026  
**Scope:** Master task list (ENGINEERING_TASKS.md) vs. actual codebase  
**Purpose:** Clarify priorities based on what's already implemented

---

## PHASE 1: WHITE PAPER SECTIONS (Aug 9-31)
🚫 **No code audit needed** — this is founder/marketing work

---

## PHASE 2: FREE TIER LAUNCH PREP (Sept 1 – Oct 1)

### ✅ BUILT & READY

**Smoke Tests:**
- ✅ Homepage (`Home.tsx`) — exists, search integrated
- ✅ Search / Directory (`Directory.tsx`) — search queries work, tested
- ✅ Org detail page (`OrganizationDetail.tsx`) — renders full org profile
- ✅ Wallet (`WalletContext.tsx`) — bookmark save/retrieve, volunteer capture

**Org Page Features:**
- ✅ Mission text capitalization (`sentenceCase()` utility)
- ✅ Donation link (`donate_url` in API, "Donate Now" button in OrgInfoHierarchy.tsx)
- ✅ Mobile responsive (Tailwind + responsive grid layout)
- ✅ Server-rendered metadata (og:title, og:description in daanaa_api.py)

**Performance:**
- ✅ Search tested (test_search_quality.py, test_search_reliability.py exist)
- ✅ Database backups (daanaa_backup.sh exists)
- ⏳ Rollback procedure (partially — `.prev` versioning exists, docs incomplete)

### ⏳ NEEDS VALIDATION / MEASUREMENT

**Org Page Polish:**
- ❓ Header density — needs UX audit (is it cluttered?)
- ❓ Lazy-load below-fold — needs measurement (are non-critical sections causing load bloat?)
- ❓ Error handling — needs testing (how do we degrade when APIs fail?)
- ❓ WCAG AA compliance — needs formal audit (contrast, keyboard nav, screen readers)

**Performance Baselines:**
- ⏳ Search latency (p50, p95, p99 benchmarks not documented)
- ⏳ Org page load time baseline (target: < 1s initial)

---

## PHASE 3A: ONE-CLICK GIVING (Oct 1–15) Gate 1

### ✅ BUILT

- ✅ "Donate Now" button on org pages (OrgInfoHierarchy.tsx calls donate_url)
- ✅ Donation link pipeline (`donation_link_pipeline.py`, 3,680+ links verified)
- ✅ Donate URL confidence scoring (donate_confidence in API)

### ⏳ PARTIALLY BUILT

**Wallet Integration:**
- ✅ Wallet stores bookmarks + volunteer intent
- ❓ Donor email/name capture — fields exist in DonationLogger, but not pre-filled on donate URL
- ❓ Intent pre-fill — not implemented (query params to donate URL not populated with donor data)

### ❌ NOT BUILT

- ❌ Completion rate tracking (no measurement of "Donate Now" → completed donation flow)
- ❌ 30% completion baseline (target not measured)

---

## PHASE 3B: NEEDS NETWORK BACKEND (Oct 15 – Nov 30) Gate 2

### ❌ NOT BUILT — CRITICAL BLOCKER

**Database Layer:**
- ❌ Needs table schema (NOT in registry.db)
- ❌ Need intake flow (voice/text/document upload)
- ❌ AI draft generation (Qwen integration started, not wired to Needs)
- ❌ Nonprofit approval workflow
- ❌ Freshness automation (30/60 day re-confirms)

**Frontend:**
- ❌ Nonprofit Needs management dashboard
- ❌ Recurring frequency toggle
- ❌ Measure recurring adoption

**API:**
- ❌ `/api/nonprofits/{ein}/needs` endpoints
- ❌ Nonprofit claim → Need intake routing

---

## PHASE 3C: NEEDS NETWORK FRONTEND (Dec 1) + Launch

### ❌ NOT BUILT — DEPENDS ON PHASE 3B

- ❌ Donor discovery of Needs UI (search, filter by type/cause/location)
- ❌ Nonprofit Needs management dashboard
- ❌ Wallet integration for Needs (save Need interest)
- ❌ Freshness UI ("Last confirmed X days ago")

---

## PHASE 3D: ADVANCED FEATURES (Jan–Feb)

### ⏳ PARTIALLY BUILT

**DAF Routing (Gate 3):**
- ✅ /giving-via-daf help page (live, EIN-based routing)
- ✅ Org detail links to DAF routing
- ❓ Wallet DAF provider storage (field exists, may not be persisted)
- ❓ DAF detection + "Route to my DAF" button (logic incomplete)
- ❌ Measurement (% of users using DAF route)

**Employer Match:**
- ❓ Employer field in wallet (mentioned in components)
- ❌ Employer match detection + badge
- ❌ Employer match portal routing
- ❌ Measurement

### ❌ NOT BUILT

**Suggestion Engine (Gate 4):**
- ❌ Wallet suggestion logic (read giving history → generate suggestions)
- ❌ "You gave to X, orgs like X also need help" UI
- ❌ Suggestion delivery (email, in-app, frequency control)
- ❌ Measurement (do suggestions → clicks → donations?)

---

## SUMMARY: WHAT'S BLOCKING THE ROADMAP

### 🔴 **CRITICAL BLOCKERS** (Blocks Phase 3B–3D)

1. **Needs Network Database Schema**
   - No `needs` table, no `need_intakes`, no `need_approvals`
   - This blocks: nonprofit intake, freshness automation, donor discovery
   - Effort: 3-4 days (schema design + API routes + data validation)

2. **Nonprofit Claim → Need Intake Routing**
   - How does a nonprofit claiming their profile lead to submitting Needs?
   - Currently: claim flow exists, but no linkage to Needs
   - Effort: 2-3 days (wire claim approval → Need intake redirect)

---

### 🟡 **IMPORTANT (Blocks Launch Polish)**

3. **Completion Rate Tracking (One-Click Giving)**
   - "Donate Now" button exists, but no measurement of completion
   - Can't optimize donation flow without baseline
   - Effort: 2-3 days (instrument donate URL, track callbacks)

4. **Org Page Performance Baselines**
   - Search latency not documented
   - Org page load time not baseline'd
   - Effort: 1 day (measure + log benchmarks)

5. **Donor Data Pre-fill**
   - Wallet captures email/name, but not sent to donate URL
   - Missing: query param generation (email, name, amount suggestions)
   - Effort: 1-2 days (add to donate URL generation)

---

### 🟢 **NICE-TO-HAVE (Can Skip for MVP)**

6. **DAF Detection & Routing**
   - Help page exists, org links work
   - Missing: wallet-based DAF provider detection + auto-route
   - Effort: 3-4 days
   - Impact: ~5-10% of donors (DAF users)

7. **Employer Match Detection**
   - Infrastructure exists (DonationLogger mentions it)
   - Missing: employment data source + match portal links
   - Effort: 4-5 days
   - Impact: ~3-5% of donors initially

8. **Suggestion Engine**
   - No foundation (no cohort similarity logic)
   - Effort: 5-7 days (build recommendation algorithm)
   - Impact: TBD (needs measurement)

---

## PRIORITIZATION RECOMMENDATION

### **IMMEDIATE (This Week — Aug 9-15)**

✅ **DONE:**
- Phase 3 measurement infrastructure (Firebase Analytics)

⏳ **DO NEXT:**
1. **Org page performance audit** (1 day)
   - Measure: search p95, org page load time
   - Document baselines
   - Check WCAG AA compliance

2. **Needs network database design** (2-3 days)
   - Schema: needs, need_intakes, need_approvals, need_freshness_log
   - API routes: POST /api/nonprofits/{ein}/needs, GET /api/needs, etc.
   - Start backend build

### **NEAR-TERM (Next 2 Weeks — Aug 16-31)**

3. **Nonprofit claim → Need intake routing** (2-3 days)
   - When nonprofit claims org → offer "Add a Need"
   - Route to Need intake form

4. **Completion rate tracking** (2-3 days)
   - Instrument Donate Now clicks
   - Track donation completions via callback URL
   - Baseline: before/after comparison

5. **Donor data pre-fill** (1-2 days)
   - Generate donate URLs with email, name, suggested amount
   - Test with 5 partner orgs

### **DEFER (Sept+)**

6. DAF detection (Sept, 3-4 days)
7. Employer match (Sept, 4-5 days)
8. Suggestion engine (Oct, 5-7 days)

---

## FILES TO REVIEW

- `/home/akbar/meritgiving/data/merit_registry.db` — confirm no Needs table
- `/home/akbar/meritgiving/daanaa_api.py` — see org detail endpoint structure
- `/home/akbar/meritgiving/frontend/src/pages/OrganizationDetail.tsx` — see metadata injection
- `/home/akbar/meritgiving/scripts/donation_link_pipeline.py` — see donation link discovery
- `/home/akbar/meritgiving/frontend/src/contexts/WalletContext.tsx` — see wallet persistence

---

## NEXT STEP FOR YOU

**Which track do you want to focus on?**

A. **Measurement** (Phase 3 Gate A.1 — prove AtAGlance helps small orgs)
   - Your call on Firebase auth + baseline metrics
   - 1-2 weeks to decision gate

B. **Performance & Polish** (Phase 2 readiness)
   - Org page latency baselines
   - WCAG AA audit
   - Rollback procedure docs
   - 3-4 days to launch-ready

C. **Needs Network** (Phase 3B foundation)
   - Database schema design
   - Backend routes
   - Nonprofit intake flow
   - 1 week to have MVP ready

**Recommend:** Do B + A in parallel (performance audit takes 1 day, then measurement runs Aug 10-16). Save C for Sept.

What's your call?
