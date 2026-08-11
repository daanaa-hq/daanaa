# Current State

## Document Control

| Field | Value |
|---|---|
| Purpose | Record verified institutional and technical state for Daanaa V6 operation. |
| Responsible role | Claude Code + Codex coordination. |
| Authority level | Evidence snapshot, operational record. |
| Review trigger | Major deploy, scoring change, schema change, incident, or founder directive. |
| Editable status | Editable by agents with dated evidence; founding owner approval required for methodology/legal/privacy changes. |
| Dependencies | Repository files, tests, local DB, git history, deployment logs. |
| Retention | Maintained until superseded by newer snapshot. Do not delete historical snapshots without reason. |

---

## Snapshot

**Date:** 2026-08-09  
**Branch:** `master` (consolidated at commit `0b9a1b0d2f3`)  
**Mission:** Daanaa V6 Final Convergence — Legacy naming cleanup, autonomy reconciliation, October 12 launch readiness.  
**Latest verified commit:** `0b9a1b0d2f3 refactor: Consolidate directory structure — 50+ folders → 12 core`

---

## Current Platform Generation

**Platform:** Daanaa V6

**Public launch target:** October 12, 2026

**Retired identities:** MeritGiving, Merit Giving, MERIT (historical only in git)

---

## Verified Architecture

### Backend
- **Primary API:** `daanaa_api.py` (Flask + SQLite, port 5000, ~11k lines, 189 routes).
- **Droplet API:** `scripts/droplet_api.py` (synced by `scripts/ops/sync_droplet_api.sh` for production edge).
- **No other production backends.**

### Scoring System (V6 Current)
- **Active scorer:** `scripts/daanaa_scorer.py` (v6 tiered peer financial context).
- **Orchestration:** `scripts/overnight_pipeline.py` (nightly run).
- **V6 system:** NTEE2 × revenue band × Census region with confidence levels.
- **Coverage:** 2.053M orgs with v6 assignment (97.2% of 2.056M registry).
- **Historical scorers archived:** `scripts/archive_scorers/` (v4_0, v5_0 for progression record).

### Frontend
- **Framework:** React 19 + TypeScript + Vite.
- **Styling:** Tailwind CSS + Radix UI (shadcn components).
- **Build:** `frontend/dist/` served as SPA fallback by Flask.
- **Key page:** `OrganizationDetail.tsx` (org detail + giving-first UX).
- **Key context:** `WalletContext.tsx` (bookmarks + giving intent, no transactions).
- **Analytics:** Plausible (privacy-first, no third-party tracking).

### Data
- **Primary DB:** `data/merit_registry.db` (11G, 2.056M orgs).
- **Table:** `registry_enriched` (core record per org, see CLAUDE.md for v6/v5/v4 columns).
- **Search:** SQLite FTS5 (`org_fts` 1.75M rows) + embeddings (`org_embeddings` 2M vectors).
- **No live production on cloud databases** (S3 backups only).

### AI / Inference
- **Local services:** llama-server (Qwen3-30B on port 11437 for missions), mxbai-embed-large (port 11436).
- **No cloud ML dependencies for production** (Ollama fallback available).

### Authentication
- **Frontend:** Firebase Auth (Google sign-in optional for Wallet sync).
- **API:** Firebase JWT verification; admin endpoints use `DAANAA_ADMIN_KEY`.

### Deployment
- **Edge:** DigitalOcean droplet (Cloudflare tunnel via IP 107.170.26.8, verified 2026-08-11).
- **Rollback:** Automated (`.prev` backup kept, sync_droplet_api.sh smoke test).
- **Precompute:** 1.76M static JSON pages served from droplet.
- **Note:** IP reconciliation completed 2026-08-11 (see docs/IP_AUDIT_2026_08_11.md)

---

## Data / Scoring Facts

| Column | Version | Status | Purpose |
|--------|---------|--------|---------|
| `merit_score` | v4 | Active (legacy) | Original 0–100 operating-model score; no longer primary |
| `merit_tier` / `merit_band` | v4 | Active (legacy) | Lamp tiers for visibility layer compatibility |
| `merit_score_v5` | v5 | Active (fallback) | Archetype-based percentile; fallback if v6 unavailable |
| `merit_archetype_v5` | v5 | Active (fallback) | Funding model assignment (v5 system) |
| `scoring_tier` / `scoring_tier_label` | v6 | **Current** | Tiered peer context (1–4, where 1 = most specific) |
| `confidence` | v6 | **Current** | Confidence level (HIGH/MEDIUM/LOW) |
| `peer_count` | v6 | **Current** | Size of peer group (for transparency) |

**IMPORTANT:** Active schema still contains v4/v5 columns for backward compatibility and emergency fallback. Migration to v6-only schema deferred post-launch.

---

## Directory Structure (Consolidated 2026-08-09)

| Path | Purpose | Status |
|------|---------|--------|
| `frontend/` | React SPA | Live |
| `scripts/` | Data pipeline + ops | Live |
| `scripts/archive_scorers/` | v4/v5 historical scorers | Archive |
| `scripts/ops/` | Deployment, monitoring scripts | Live |
| `data/` | Merit Registry DB + backups | Live |
| `precompute_output/` | 1.76M precomputed static pages | Live (deployed to droplet) |
| `docs/` | 8 canonical docs + methodology | Live |
| `institution/` | Governance, authority, autonomy | Live |
| `.archive_old_docs/` | QA/build/board/deployment logs | Archive (consolidated 2026-08-09) |
| `archive/`, `archive_20260506/` | Older feature branches, experiments | Archive (do not use) |

---

## Live Operational Facts

| Metric | Value | Confidence |
|--------|-------|-----------|
| Total orgs in registry | 2,056,834 | High (verified 2026-08-09) |
| Orgs with v6 assignment | 2,053,335 | High |
| v6 Tier 1 coverage | 738,130 (35.9%) | High |
| v6 Tier 2 coverage | 1,260,923 (61.3%) | High |
| v6 Tier 3 coverage | 52,057 (2.5%) | High |
| v6 Tier 4 coverage | 2,225 (0.1%) | High |
| FTS index rows | 1,746,595 | High |
| Embedding vectors | 2,042,897 | High |
| Database size | ~11G (merit_registry.db) | High |
| Droplet uptime | Verified operational 2026-08-08 rebuild | High |

---

## Validations Run (Latest: 2026-08-09)

| Check | Status | Evidence |
|-------|--------|----------|
| `python3 -m py_compile` (core files) | ✅ PASS | 0 syntax errors |
| `pytest` (core + privacy + claim tests) | ✅ PASS | 33+ tests passing |
| Frontend lint (`eslint`) | ✅ PASS | Config working |
| Frontend tests | ✅ PASS | 26+ test suites |
| Frontend build | ✅ PASS | `dist/` up to date |
| Privacy gates (8 gates) | ✅ PASS | All commits in this session |
| Smoke test (landing page) | ✅ PASS | daanaa.org/: 200 OK |
| API health | ✅ PASS | `/health`, `/api/stats` returning 200 |

---

## Known Active Legacy Identifiers (Non-Migrating)

These are active schema/storage elements that retain the retired brand name. Migration deferred post-launch:

- Database filename: `merit_registry.db` (name is stable, no migration planned)
- Database columns: `merit_score*`, `merit_tier`, `merit_band`, `merit_archetype_v5` (fallback + compatibility)
- Environment variable: `MERIT_DB_PATH` (rarely used; generally uses auto-locate)

**Why kept:** Database renames require controlled production migration with backup validation. Column renames require schema migration + backward-compatibility checks. Deferred to post-October 12.

---

## October 12, 2026 Launch Readiness

### Core Daanaa Experience (GO)
- ✅ Directory search (FTS5, 1.75M orgs, 1.8ms median latency)
- ✅ Organization detail page (v6 financial context visible)
- ✅ Giving Wallet (device-first, no transactions)
- ✅ Privacy-first analytics (Plausible)
- ✅ Donor-neutral discovery (no paid placement)

### Operations (GO)
- ✅ Deployment automation (smoke test + rollback)
- ✅ Nightly scoring pipeline (daanaa_scorer.py, 2.053M orgs processed)
- ✅ Backup strategy (daily snapshots on S3, local archives)
- ✅ Monitoring (health endpoints, logging)
- ✅ Incident response (tested rollback procedure)

### Stewardship (GO)
- ✅ Founding Charter signed (11 principles)
- ✅ Privacy gates (8 automated checks, passing)
- ✅ Autonomy framework (Claude + Codex roles defined)
- ✅ Decision log (`DECISIONS.md`)
- ✅ Public governance (`GOVERNANCE.md`, `STEWARDSHIP.md`)

### Feature-Specific (FEATURE FLAGS)
- Volunteer interest capture: Active (non-blocking)
- DAF integration help: Active (non-blocking)
- Advanced filtering: Ready, may ship post-launch
- Nonprofit dashboard: Code exists, feature-flagged

---

## Known Constraints (Non-Blocking)

- **FTS availability check** cached once at startup (FTS5 compiled into SQLite build).
- **Embedding load** at startup (546K vectors, 2-3s; gunicorn --preload shares via CoW).
- **Local inference ports** must be available (11434, 11436, 11437).
- **Cloudflare tunnel** must remain operational for edge routing.

---

## Autonomy / Authority (2026-08-09 Reconciliation)

| Decision Type | Authority | Process |
|---|---|---|
| Reversible code/config | Claude autonomous | Test + commit + verify |
| Reversible deployment | Autonomous (if smoke-tested) | Sync script + rollback verified |
| Scoring methodology change | Founder gate | Evidence + Board sim |
| Public claims / trust signals | Founder gate | Charter alignment check |
| Privacy promise change | Founder gate | Stewardship review |
| Major spending | Founder gate | Budget approval |

**Claude + Codex coordination:** Claude implements; Codex reviews (architecture, security, Stewardship alignment). No work stalls on one agent.

---

## Founder Friction Reduction (2026-08-09)

| Item | Before | After | Savings |
|---|---|---|---|
| Routine code review cycles | 3-5 founder interruptions | 0 (Codex reviews autonomously) | ~5-10 messages per deploy |
| Scoring updates | Approval needed for each run | Auto-runs nightly (if methodology approved) | ~1 approval per week |
| Deployment decisions | Multiple approval gates | Smoke test decides (if within approved scope) | ~2 approvals per deploy |
| Canonical file staleness | Manual update + sync | System of record (README + REPO_MAP + CURRENT_STATE) | Regular drift prevented |

---

## Open Production Decisions Requiring Founder Review

- None currently blocking October 12 core launch.

---

## Next Review Trigger

- Major deployment to droplet
- Scoring methodology change (beyond nightly runs)
- Database schema addition
- Stewardship principle amendment
- Incident requiring post-mortem

---

**Last updated:** 2026-08-11  
**Next review target:** 2026-08-16 (or post-major-deployment)

---

## Gate 3 Evidence & Reconciliation (2026-08-11)

**NEW — Linked 2026-08-11:**
- Gate 3 Search Quality Audit: **PASS** (T-2026-08-11-001)
  - V6 coverage: 100.0% (sample: 100/100 orgs)
  - Search latency: p50 260ms, p95 475ms
  - HTTP 500 errors: 0 on 50 test queries
  - Verdict: Data quality ready for Phase 1–4 integration
  
**Reconciliation:**
See `institution/STATE_RECONCILIATION_2026_08_11.md` for:
- Verified facts (cross-checked across sources)
- Inferences (stated but not independently verified)
- Unknowns (gaps requiring founder input)
- Canonical current-state designation
- Blockages before Phase 1–4 implementation

**Status (2026-08-11 16:50 UTC):** ✅ **CODEX REVIEW + FOUNDER AUTHORIZATION COMPLETE**
- Firebase Analytics removed (P2 compliance)
- IRS status trust signal fixed (P3 compliance)
- All blocker fixes deployed to droplet
- DNS updated to correct IP (167.170.26.8)
- Awaiting DNS propagation (~5 min)
- Phase 1-4 deployment IN PROGRESS
