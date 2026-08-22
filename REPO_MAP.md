# REPO_MAP — navigate in seconds, not tokens

**Purpose:** This repo is large (600+ tracked documents, ~379 scripts, ~40 top-level dirs,
an 11k-line API). This map is the token-saving entry point: load THIS + `CLAUDE.md`, go
straight to the canonical file, and ignore the historical sprawl unless you have a specific
reason. Kept lean on purpose — if it grows into another 250-line doc, it has failed.

Maintained per the Toyota working test (`docs/DESIGN_PHILOSOPHY.md`): one canonical path per
job. Before building anything, find its canonical path here first — do not spawn a parallel
file (that is the muda this map exists to prevent).
For documentation navigation, start with docs/README.md. It distinguishes canonical starting points from historical or ambiguous material; a document in docs/ is not automatically implemented.

---

## 1. Load these first (the only always-relevant files)

| File | What it is |
|------|-----------|
| `CLAUDE.md` | Operating agreement, architecture, gotchas, autonomy rules. The primary. |
| `STEWARDSHIP.md` | Supreme law — the 11 principles. Non-negotiable. |
| `PRIVACY-INVARIANTS.md` | Structural privacy rules (enforced by `privacy_check.sh`). |
| `REPO_MAP.md` | This file — canonical navigation paths to avoid token waste. |
| `governance/DECISIONS.md` | Why non-obvious choices were made (newest on top). |
| `governance/LESSONS.md` | Broke-then-fixed; preventing rules (newest on top). |
| `docs/ROADMAP.md` | Product roadmap; verify status against code and current decisions. |
| `docs/DESIGN_PHILOSOPHY.md` | How we build: Toyota Way + Kondo + openness; the working test. |
**Root .md files:** The files above are entry points, but PRODUCT.md, DESIGN.md, CONTRIBUTING.md, DEPLOYMENT.md, and TEAM_STORY.md remain intentionally root-level because they are referenced by tooling or are standard contributor/product entry points. The docs/ tree contains both active and historical material; use docs/README.md before opening a broad set of files.
Load additional material only when a task explicitly names it. Use grep to find historical docs instead of broad reading.

---

## 2. Backend (canonical: one file)

- **`daanaa_api.py`** — the ONLY backend. Flask + SQLite, port 5000, ~11k lines, 189 routes.
  Navigate by grepping `@app.route` for the endpoint, not by reading top-to-bottom.
  - `merit_api.py` / `app.py` = removed. `api/main.py` = archived. If a doc references them, it is stale.
- **Droplet**: gunicorn serves `/opt/daanaa/droplet_api.py` (synced by `scripts/ops/sync_droplet_api.sh`).
- Admin routes: `/api/admin/*` need `X-Admin-Key`. Flags: `ENABLE_SCORES`, `DAANAA_PROD`.

## 3. Data pipeline — one canonical path per job (grep here before building)

| Job | Canonical path | Never use |
|-----|---------------|-----------|
| Nightly orchestration | `scripts/overnight_pipeline.py` | — |
| Scoring | `scripts/daanaa_scorer.py` (v6 tiered peer context; runs nightly) | `scripts/archive_scorers/` (v4, v5 historical) |
| Continuous link/website discovery | `scripts/discovery_daemon.py` → `website_discovery_comprehensive.py` (`WebsiteDiscovery`, extracts links from a known site) + `charity_navigator_verify.py` (`CharityNavigatorVerifier`, finds site/donate by EIN via **official CN API**) | the ~10 other `*website_discovery*` / `*scraper*` scripts (0-1 refs = debris) |
| Donate-link pipeline | `scripts/donation_link_pipeline.py` | — |
| FTS search index | `scripts/build_fts_index.py` (+ `search_index_delta.py` for new orgs) | — |
| Embeddings | `scripts/build_org_embeddings.py` | — |
| Missions | `scripts/generate_missions.py` (local Qwen, port 11437) | cloud APIs |
| URL normalize | `scripts/website_normalize.py` (8 refs = canonical) | — |

**Rule:** ~379 scripts exist; most are one-off/experimental. A capability almost always has a
canonical owner above. Grep before writing a new script. (See LESSONS.md 2026-07-21 — a CN
scraper was built that duplicated `charity_navigator_verify.py`.)

## 4. Frontend (`frontend/src/`)

- **Pages** (`pages/*.tsx`, 55): key ones — `OrganizationDetail.tsx` (org page, giving-first),
  `WalletPage.tsx`, `Directory.tsx`, `Home.tsx`, `NonprofitDashboard.tsx`, `ResearchDashboard.tsx`.
- **Contexts** (`contexts/`): `WalletContext.tsx` = **the moat** (funding/volunteering intent,
  the DRY home for wallet actions + behavior events). Also `AuthContext`, `CompareContext`,
  `ThemeContext`. (`GivingListContext` = dead compat shim.)
- **Key utils**: `utils/analytics.ts` (`trackEvent` → self-hosted Plausible, the observe/PDCA
  instrument), `utils/actionRow.ts` (`getActionRowLinks`), `utils/env.ts` (`getApiBase`).
- API base: `VITE_API_URL` (`src/data/api.ts`). Built to `frontend/dist/`, served as SPA fallback.
- **`package.json` name is `my-app`** — scaffold default, ignore it.

## 5. Databases (`data/`)

- **`data/merit_registry.db`** (15G) — the ONLY live DB. Table `registry_enriched` (see CLAUDE.md
  for columns). Also `org_fts`, `org_embeddings`, `org_claims`, `waitlist`. BMF = `data/bmf.csv` (no table).
- `meritgiving.db` / `merit_state.db` = legacy, not authoritative.

## 6. Deploy (canonical: the daanaa-deploy skill routing)

| Change | Command | ~time |
|--------|---------|-------|
| `droplet_api.py` only | `scripts/ops/sync_droplet_api.sh` | 1 min |
| Frontend SPA only | `scripts/ops/safe_deploy_droplet.sh --frontend-only` | 5 min |
| API + frontend code | `scripts/ops/safe_deploy_droplet.sh --code-only` | 5 min |
| Data (scores/links) | `scripts/ops/safe_deploy_droplet.sh` (full) | 2-4 h |

All paths smoke-test + auto-rollback. Never ship `merit_registry.db` to the droplet.

## 7. Directories — active vs historical

**Active (core system):**
- `frontend/` — React app, TypeScript, Vite build
- `scripts/` — Data pipeline, ML ops, discovery, batch jobs
- `data/` — Canonical databases (merit_registry.db), CSV sources, precomputed vectors
- `docs/` — Architecture, methodology, operations, projects
- `tests/` — Unit/integration tests
- `governance/` — Constitutional docs, decisions, audits, policies
- `institution/` — Charter, library, organizational records
- `ops/` — Deployment scripts, systemd configs, monitoring
- `migrations/` — Database schema migrations (canonical)
- `precompute_output/` — Generated static files served by droplet

**Reference / historical / development (do not assume inactive without verification):**
- `archive/` — Superseded docs, session reports, old implementations (organized by era)
- `backups/` — Database backups (data protection, don't read)
- `infrastructure/` — Deprecated infra configs (cloud vendor experiments)
- `config/` — Configuration and workflow material; verify each file before changing or retiring it
- `logs/` — Operational logs
- `newsletters/` — Content archives
- `reports/` — Generated audit/analysis reports
- `research_articles/` — Bookmark collection
- `venv/` / `node_modules/` — Dependencies (do not explore)

---

## Token-saving rules (the point of this file)

1. **Load `CLAUDE.md` + this map, then go to the one canonical file.** Don't broad-read.
2. **Use docs/README.md to classify the 600+ documentation files** unless a task names one.
3. **Grep the canonical path (section 3) before building** — the capability almost certainly exists.
4. **Don't re-derive settled decisions** — check `DECISIONS.md` / memory first.
5. Keep this map lean. Update the canonical-path table when a canonical owner changes; don't append status logs here.
