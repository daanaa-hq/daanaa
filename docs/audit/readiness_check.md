# Daanaa Platform — Readiness Check Audit
**Date:** 2026-06-13  
**Auditor:** Claude Code (read-only; no changes made)  
**Scope:** `/home/akbar/meritgiving` — backend (`daanaa_api.py`), frontend (`frontend/src/`), DB (`data/merit_registry.db`), tests (`tests/`)

---

## SECTION 1 — MISSION ALIGNMENT SCAN

### 1. Revenue-based default sort?

**No mission violation on default.** Default sort is `merit_score DESC` (`daanaa_api.py:1006`).

However: `total_revenue` IS in `allowed_sorts` and is publicly requestable via `?sort=total_revenue` (`daanaa_api.py:1086`). A user or upstream link can explicitly request revenue ranking. This is not a default, but it is an affordance that can rank large orgs at the top purely by revenue. This conflicts with the peer-benchmarking principle (P4) if surfaced as a UI option without explanation.

- `daanaa_api.py:1006` — `sort_by = request.args.get('sort', 'merit_score')` — default is merit_score ✓
- `daanaa_api.py:1086` — `allowed_sorts = ['total_revenue', ...]` — total_revenue is an allowed opt-in ⚠️

### 2. Semantic search endpoint status

**WORKING.** Live test against `GET /api/search/semantic?q=food+bank+chicago` returned 10 results in <3s. Embeddings loaded from `org_embeddings` table (~546K vectors). Primary embedding server is llama-server on port 11436 (Vulkan1 / mxbai-embed-large). Fallback to Ollama on port 11434.

- If port 11436 is down, `_embed_query()` falls back to Ollama (`daanaa_api.py:257–276`).
- If both fail, endpoint returns `503 {"error": "embedding service unavailable"}` — explicit, not silent.
- Note: semantic search responses are NOT filtered by `_DEDUCTIBILITY_FILTER` (`daanaa_api.py:3330`). Revoked or non-deductible orgs could surface in semantic results if their EINs are in `org_embeddings`.

### 3. NTEE major group label completeness (A–Z)

**Two letters missing from `frontend/src/data/ntee.ts`:**

| Missing | IRS Definition | DB orgs |
|---------|---------------|---------|
| `Y`     | Mutual & Membership Benefit Organizations | 30,739 |
| `Z`     | Unknown / Unclassified | 6,181 |

Present: A B C D E F G H I J K L M N O P Q R S T U V W X (24 of 26).

Y-coded orgs (pension, insurance, credit unions) and Z-coded (unclassified) are in the DB but have no named category in the filter UI. They can appear in search results but cannot be browsed by category.

### 4. Four-tier data labeling (IRS public / AI-generated / org-verified / community)

The system uses **three** distinct source labels, not four. "Community" is not implemented as a data tier.

| Label | Renders where |
|-------|--------------|
| `irs_soi` / `nccs` / `propublica` (IRS public) | `OrganizationDetail.tsx:142–144` — `DataFreshnessBadge` component |
| `ai_ntee` / `ai_haiku` / `ai_web` / `ai_generated` (AI-generated) | `OrganizationDetail.tsx:1076–1077` — β badge on mission; `ComparePage.tsx:134` |
| `claimed` / org-verified | `OrgClaimEditor.tsx` — claim flow writes `mission_source='claimed'`; rendered at `OrganizationDetail.tsx:534` |
| Community tier | **NOT IMPLEMENTED** — no `community` source label exists anywhere in codebase |

**Missing:** No "community-verified" or "community-contributed" label tier exists in the DB schema or frontend.

### 5. Hardcoded metrics visible to users (not derived live from DB)

| Location | Hardcoded value | Status |
|----------|----------------|--------|
| `frontend/src/pages/Home.tsx:45` | `stats?.total_organizations ?? 1_600_000` | Fallback only — live stat fetched first from `/api/stats`; hardcoded is the loading placeholder ✓ |
| `frontend/src/pages/Home.tsx:726` | `'1,600,000+'` | Rendered if stats fail to load — users see this stale number on API timeout ⚠️ |
| `frontend/src/pages/ForVendors.tsx:418–419` | `{ value: '1.6M', label: 'nonprofits in the directory' }` and `{ value: '97%', label: 'currently buying at retail' }` | **Fully hardcoded** — never fetched from API ❌ |
| `frontend/src/components/WelcomeSlideshow.tsx:25` | `"1.6 million tax-deductible nonprofits"` | Hardcoded in copy ⚠️ |
| `frontend/src/pages/Directory.tsx:142` | `"1.6 million+ tax-deductible 501(c)(3)"` | Hardcoded in meta description ⚠️ |
| `frontend/src/pages/MeetInvisible.tsx:101` | `"1.6 million tax-deductible nonprofits"` | Hardcoded ⚠️ |
| `frontend/src/pages/MeetInvisible.tsx:138` | `"1.6 million nonprofits doing the work"` | Hardcoded ⚠️ |
| `frontend/src/pages/ForVendors.tsx:152,393,484,511` | `"1.6M Daanaa members"` (×4) | Hardcoded — describes nonprofits as "members" which is aspirational ⚠️ |

**Most critical:** `ForVendors.tsx:419` — `97%` stat ("currently buying at retail") is presented as fact with no source citation and is never derived from the database. No methodology page backs it up.

---

## SECTION 2 — WHAT IS ACTUALLY BUILT

| Feature | Status | Evidence |
|---------|--------|---------|
| IRS BMF search (name, EIN, cause, location) | **EXISTS** | `/api/organizations` with `q`, `ntee`, `state`, `cause` params; FTS5 on `org_fts`; EIN prefix match (`daanaa_api.py:1015–1036`) |
| Filters on search results | **EXISTS** | NTEE, subcategory, state, revenue range, min percentile, tier, hidden gem, has website, recent (`daanaa_api.py:988–1007`); `FilterSheet.tsx` in frontend |
| Org profile page with data-source labels | **EXISTS** | `OrganizationDetail.tsx` — `DataFreshnessBadge` shows source + tax year; AI badge on mission; ProPublica/IRS attribution |
| Activity signal layer (filing freshness: green/yellow/red) | **PARTIAL** | `TrustBadge.tsx:69–70` — current = ≥2022, stale = 2020–2021, missing = unavailable. No explicit green/yellow/red color coding. Shown as text status in tier criteria, not a colored signal. |
| NTEE confidence scoring | **MISSING** | No `ntee_confidence` column in schema, no confidence score attached to NTEE assignments, not surfaced anywhere in frontend. |
| Stewardship badge calculation | **MISSING** | `TrustBadge.tsx` component exists but renders financial health / visibility tier criteria only. No "stewardship badge" distinct from tier system. `scripts/agents/stewardship_audit.py` exists but its output is not wired to DB or API. |
| Civic wallet (read-only, manual donation log) | **EXISTS** | `Wallet.tsx` — localStorage-first; Firebase-synced when signed in. Records giving intent. Explicitly not a payment tool (`Wallet.tsx:405`). |
| Google auth / secure sessions | **EXISTS** | `AuthContext.tsx`, `firebase.ts`, `GoogleSignInButton.tsx` — Firebase Auth with Google + magic link providers. JWT verified server-side via public key (`daanaa_api.py` — `_require_firebase_user()`). |
| Give button (should be MISSING in Phase 0) | **PRESENT — FLAG** | `OrganizationDetail.tsx:427–444` — "Save to Wallet" button renders as the give CTA. CTA label is "Save to Wallet" (not "Donate") and routes to localStorage record, not payment. No money moves. However the button is labeled the give moment and appears prominently on every org page. Confirm this is acceptable vs. Phase 0 definition. |
| Nonprofit claim flow | **EXISTS** | `/claim/verify`, `/claim/edit`, `/claim/success` routes; `ClaimVerify.tsx`, `OrgClaimEditor.tsx`; admin review via `/api/admin/claims` (`daanaa_api.py:2097`) |
| Volunteer intent capture | **EXISTS (placeholder functional)** | `VolunteerInterest.tsx` component renders on org detail; collects name/email/message; `SupportIntent.tsx` also present |
| Board intent capture | **MISSING** | No board-member intent capture component exists. `boardSize: 0` placeholder in `OrganizationDetail.tsx:265` is never surfaced to users. |

---

## SECTION 3 — DATA INTEGRITY

### 1. Record counts

| Table | Count |
|-------|-------|
| Total records (`registry_enriched`) | **2,064,613** |
| Active / non-revoked (visible in browse) | 1,968,366 (estimated; `_DEDUCTIBILITY_FILTER` also requires subsection=3 and deductibility=1) |
| Revoked (`irs_revoked=1`) | **192,889** |
| Scored (`merit_score IS NOT NULL`) | 537,920 |
| With mission text | 2,064,370 (near-universal) |

### 2. Most recent filing date

Tax year range in DB: **FY2002 – FY2025**. Most recent cohort: FY2024 (186,525 orgs). Largest cohort: FY2023 (462,380 orgs). IRS SOI data lags ~18 months so FY2025 is partial.

### 3. Are revoked organizations excluded from search results?

**YES — for `/api/organizations` (browse).** `_DEDUCTIBILITY_FILTER` (`daanaa_api.py:1446–1450`) includes `COALESCE(irs_revoked, 0) != 1`. This filter is applied as the base `WHERE` clause for all browse/directory requests.

**PARTIAL for `/api/search` (fused search).** The fused search endpoint (`daanaa_api.py:3337`) fetches org details via `_fetch_orgs_by_eins()`. That function's SQL must be checked independently — if it doesn't apply `_DEDUCTIBILITY_FILTER`, revoked orgs can surface in keyword/semantic search results.

**NO filter on `/api/search/semantic`.** Results come from vector index (`org_embeddings`), which was built on scored orgs. 63,466 revoked orgs have a merit_score — they could be present in the embedding matrix and returned by semantic search.

**Direct EIN access still works for revoked orgs** (`daanaa_api.py:1444` — by design, per comment). The donate gate `_is_revoked()` blocks the donation CTA for revoked orgs independently.

### 4. Are 990-N filers (sub-$50K) present?

**YES — present in DB but not distinguished.** No `form_type` column exists in `registry_enriched`. 990-N filers are identified indirectly:
- 159,089 orgs have revenue > 0 but < $50K (likely 990-EZ or small 990 filers)
- 1,413,891 orgs have `total_revenue IS NULL OR = 0` (includes 990-N filers, stubs, unscored orgs)
- 990-N filers surface in search results with Spark tier and no financial data; they are not labeled distinctly as "990-N filer."

### 5. Offsite backup of DB?

**Local backup: running.** `scripts/ops/daanaa_backup.sh` crons at 02:30 daily. It dumps critical tables (org_claims, org_activity, feedback, waitlist) every night (retained 30 days) and takes a full online SQLite snapshot every Sunday (retained 2 copies). Files land in `backups/critical/` and `backups/full/`.

**Offsite: not yet active.** The script includes `rclone copy` to `daanaa-backup:daanaa-backups/` but only fires if `rclone listremotes` shows a `daanaa-backup:` remote — which is not configured. Until `rclone` is authorized to the founder's Drive (or an alternative remote), offsite sync is a no-op. A disk failure would still result in loss of the full DB.

- `scripts/ops/daanaa_backup.sh` — backup script (already in cron at 02:30)
- `scripts/backup_db.sh` — alternate full-backup utility with BACKUP_DEST rsync support

---

## SECTION 4 — INFRASTRUCTURE

### 1. Ports in use

| Port | Service | Status |
|------|---------|--------|
| 5000 | gunicorn (4 workers, `daanaa_api.py`) | **RUNNING** |
| 11436 | llama-server (mxbai-embed-large, Vulkan1 / primary) | **RUNNING** |
| 11437 | llama-server (Qwen2.5-32B, mission generation) | **RUNNING** |
| 11434 | Ollama (embedding fallback) | **RUNNING** (localhost only) |
| 5173 | Vite dev server | **NOT RUNNING** (production serves from `frontend/dist/` via Flask) |
| 8081 | Legacy FastAPI | **NOT RUNNING** (archived) |

### 2. Cloudflare Tunnel

**NOT ACTIVE on this machine.** `cloudflared` process not found. The production architecture routes traffic through the droplet (daanaa.org) which proxies select API paths through an SSH tunnel back to this home server. The tunnel (`daanaa-claim-tunnel`) is managed on the droplet side. Direct Cloudflare Tunnel on the home server: absent.

### 3. Startup scripts

| Script | Purpose |
|--------|---------|
| `restart_api.sh` | Production: gunicorn 4-workers with `--preload`, binds 0.0.0.0:5000 |
| `restart_merit_api.sh` | Legacy/dev restart script |
| `check_merit_status.sh` | Health check — ports, DB, cloudflared, API health endpoint |
| `check_api_connection.sh` | Connectivity probe |
| `deploy_api_frontend.sh` | Build frontend + deploy |
| `run_overnight.sh` | Nightly orchestrator wrapper |
| `run_master_loop.sh` | Data pipeline loop |

### 4. Last deployment date

Most recent git commit: `139d0956ceb` — `feat(droplet): proxy /api/wallet to home server via existing SSH tunnel` (current session). The prior deployable commit was `6d66c3cb053` — `feat(nav): add ForVendors and GuildReferral routes`. No timestamp visible without git log `--date` flag, but the branch is `master` and commits are continuous.

### 5. Failing tests

**6 tests failing** (98 passing):

| Test | Failure | Severity |
|------|---------|----------|
| `test_principles.py::test_no_wallet_write_route` | `/api/wallet` GET/PUT/DELETE routes exist on server; test assumes wallet is localStorage-only. Routes are Firebase-auth-gated but test's regex match doesn't know that. | **STALE TEST** — test predates wallet sync feature; needs update to allow auth-gated routes |
| `test_no_public_donation_fields.py::test_org_list_has_no_donation_fields` | Test hits temp DB with no `registry_enriched` table → `sqlite3.OperationalError` | **TEST ENVIRONMENT BUG** — conftest uses blank temp DB; test needs table fixture |
| `test_no_public_donation_fields.py::test_org_detail_has_no_donation_fields` | Same — no table | Same |
| `test_no_public_donation_fields.py::test_similar_has_no_donation_fields` | Same | Same |
| `test_no_public_donation_fields.py::test_research_lamp_tiers_has_no_donation_fields` | Same | Same |
| `test_no_public_donation_fields.py::test_direct_link_filter_is_gone` | Same | Same |

**Root cause of 5 failures:** `conftest.py` sets `DB_PATH` to a blank temp file. Tests that issue real SQL against `registry_enriched` crash because the table doesn't exist. The table schema is never seeded in the test fixture. Live API (against real DB) has no donate leak confirmed via manual `curl`.

---

## SECTION 5 — OPEN RISKS

### Mission violations

- **RISK-M1** — `daanaa_api.py:1086`: `total_revenue` is in `allowed_sorts` for `/api/organizations`. Any client can request `?sort=total_revenue&order=desc` and receive a revenue-ranked list. No UI currently does this, but the parameter is undocumented and unguarded. Should either be removed or restricted to admin-key requests.
- **RISK-M2** — `frontend/src/pages/ForVendors.tsx:419`: `"97%"` stat ("currently buying at retail") is fully hardcoded with no source, no citation, and no methodology link. P3 (trust signals must be evidence-based) requires this either be sourced or removed.
- **RISK-M3** — `/api/search/semantic` does not apply `_DEDUCTIBILITY_FILTER`. Revoked orgs with embeddings can appear in semantic search results with no donation-eligibility check. `daanaa_api.py:3330`.

### Data honesty risks

- **RISK-D1** — `frontend/src/pages/Home.tsx:726` and all `WelcomeSlideshow.tsx:25`, `Directory.tsx:142`, `MeetInvisible.tsx:101,138`, `ForVendors.tsx:393,418,484,511`: "1.6 million" is hardcoded in numerous places. Actual DB count is 2,064,613. The frontend displays a lower number than exists, and the number is static rather than live.
- **RISK-D2** — No `form_type` column exists in `registry_enriched`. 990-N filers (epostcard, <$50K gross receipts) are not distinguished from full 990 filers in any public-facing label. Users cannot tell which organizations file epostcards vs full annual reports.
- **RISK-D3** — 1,413,891 orgs (68% of the registry) have no revenue data. They receive a Spark tier. No disclosure is shown to users explaining what it means for an org to have no financial data — the tier label ("minimal public information") is the only signal.
- **RISK-D4** — `latest_tax_year` max is 2025, but IRS SOI data for 2025 is incomplete (only 186K orgs). Orgs with a 2025 year may have partial filings presented alongside complete older filings without a recency caveat.
- **RISK-D5** — NTEE categories Y and Z exist in the DB (36,920 orgs) but are absent from `frontend/src/data/ntee.ts`. These orgs cannot be browsed by category and receive no NTEE label in the UI.

### Security concerns

- **RISK-S1** — `test_principles.py::test_no_wallet_write_route` is FAILING. This test was designed to enforce P2 (donor privacy structural enforcement). The test is now wrong (wallet sync is intentional and auth-gated), but the test failing means this principle assertion is effectively unmonitored. A future developer reading "6 tests fail" may not realize this test's intent.
- **RISK-S2** — Admin endpoints mix two protection patterns: `@require_admin_key` decorator (most routes) vs inline `require_admin()` calls (guild routes). `require_admin()` is called inside route bodies (`daanaa_api.py:2814, 2826, 2856, 2881, 2985, 2995, 3197, 3207`). If the function is ever accidentally removed or stubbed, those guild admin routes would lose protection without a decorator-level safeguard. Both patterns appear correct currently, but the inconsistency is a maintenance risk.
- **RISK-S3** — `daanaa_api.py:2575`: Inside the claim flow, `SELECT organization_name, mission, donate_url FROM registry_enriched WHERE EIN=?` retrieves `donate_url` and returns it to the claimant at `current_donate_url` key. This is intentional (claim flow only), but it bypasses the `_strip_scores()` scrub that protects all other public endpoints. If the claim endpoint's JSON structure ever leaks to public, donate URLs would be exposed.
- **RISK-S4** — No HTTPS enforcement at the home server level. `DAANAA_PROD` env flag enables HTTPS-only CSP/HSTS headers, but the home gunicorn server binds on plain HTTP port 5000. Production security depends entirely on the droplet's nginx + Cloudflare proxy chain. If the proxy is bypassed (e.g., via LAN access to 192.168.1.73:5000), all traffic is unencrypted.

### Single points of failure

- **RISK-F1** — **Offsite database backup not yet active.** `scripts/ops/daanaa_backup.sh` runs nightly at 02:30 (critical tables daily, full snapshot Sundays), but the `rclone daanaa-backup:` remote is not configured, so the offsite push step silently skips. A disk failure would still result in total data loss. **Fix:** authorize rclone to Google Drive and run `rclone config` to create the `daanaa-backup:` remote.
- **RISK-F2** — **Embedding matrix in RAM only.** At startup, `_load_embeddings()` reads ~546K org vectors (~2 GB) into process memory. If the API process crashes and restarts, semantic search is unavailable until the matrix reloads from DB. With gunicorn `--preload`, workers share the matrix via CoW — but a full restart requires a full reload. No warm-standby exists.
- **RISK-F3** — **Single SQLite writer.** `merit_registry.db` is SQLite. The nightly pipeline, the scoring run, FTS rebuild, and the live API all compete for the same write lock. DB lock contention errors appear in `scripts/web_finder_agent.py` (fixed with retry logic). Under heavy pipeline load, the live API may experience intermittent write timeouts.
- **RISK-F4** — **No monitoring/alerting.** `scripts/ops/daanaa_watchdog.py` and `daanaa_morning_digest.py` exist and probe `daanaa.org/health`, but there is no continuous uptime monitor, no PagerDuty/webhook, and no alert if the embedding servers (ports 11436/11437) go down. Semantic search would silently degrade to FTS-only without notification.

---

## SUMMARY

| Category | Total findings | Critical | Mission violations |
|----------|---------------|----------|--------------------|
| Mission alignment | 3 (M1–M3) | 1 (M3: revoked orgs in semantic) | **2** (M1: revenue sort exposed; M2: unsourced 97% stat) |
| Data honesty | 5 (D1–D5) | 1 (D1: hardcoded counts wrong) | 0 |
| Security | 4 (S1–S4) | 1 (S1: P2 test broken) | 0 |
| Single points of failure | 4 (F1–F4) | 1 (F1: no offsite backup) | 0 |
| **Total** | **16** | **4** | **2** |

**Failing tests:** 6 (5 from test environment setup bug; 1 from stale principle assertion).

**Platform is functional** for its core use case (search, browse, org profiles, claim flow, wallet). The 4 critical findings (revoked orgs in semantic search, no offsite backup, unsourced "97%" stat, broken P2 test) should be resolved before any public outreach campaign.
