# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CLAUDE.md — MeritGiving

## Stewardship Commitment — Read before any work

This project operates under a Founding Stewardship Commitment (see `STEWARDSHIP.md`).
Every AI agent, contributor, and system operating on this platform is bound by it.

Before contributing any code, data change, copy edit, or system decision, you must:
1. Have read `STEWARDSHIP.md` in full
2. Operate in alignment with all 11 principles
3. Flag any conflict between a requested task and these principles before proceeding

Key rules for AI agents:
- Trust signals (scores, badges, tiers) must only reflect real, evidence-based data
- Never present unverified outputs or experimental results as established fact
- Donor privacy is non-negotiable — no social pressure mechanics, no exposure of giving activity
- Small orgs must be treated with equal dignity to large ones
- If a data error is found, correct it and document it — do not hide it
- All significant decisions must be explainable and traceable

**Signed:** Claude Code (claude-sonnet-4-6) · AI Engineering Agent · 2026-05-20

---

## What this project is

**Daanaa** (daanaa.org) is a civic nonprofit-discovery platform. It indexes 501(c)(3) organizations from IRS and ProPublica public data, assigns each a 0–100 peer financial context score, benchmarks it within its NTEE peer group, and surfaces the results through a searchable directory UI.

---

## Running the project

### API (Flask + SQLite) — primary backend
```bash
source ~/meritgiving/venv/bin/activate
./restart_api.sh              # production: gunicorn 4-workers, --preload (use this)
python3 merit_api.py          # dev: single-process Flask (no --preload)
```

### Frontend (React/Vite)
```bash
cd frontend
npm install                   # first time only
npm run dev                   # dev server, port 5173
npm run build                 # builds to frontend/dist/
```

### Status check
```bash
./check_merit_status.sh
```

### Health endpoints
- `GET http://localhost:5000/health`
- `GET http://localhost:5000/api/stats`

---

## Architecture

### Which backend is canonical

There are **three** backend files — use `daanaa_api.py` as the entry point (imports from `merit_api.py`):

| File | Framework | Port | Data source | Status |
|------|-----------|------|-------------|--------|
| `daanaa_api.py` | Flask + SQLite | 5000 | `data/merit_registry.db` | **Active entry point** |
| `merit_api.py` | Flask + SQLite | 5000 | `data/merit_registry.db` | Canonical logic — rename pending Phase 3 |
| `api/main.py` | FastAPI + SQLite | varies | `data/merit_registry.db` | Secondary / specialist endpoints |
| `app.py` | FastAPI + flat CSV | 8081 | `data/master_orgs.csv` (in-memory) | Legacy — do not extend |

`app.py` also has broken Flask route decorators appended at lines 337–354 (`@app.route(...)` on a FastAPI object) — these are dead code left by a previous agent pass. Do not edit that tail block.

### Database

Primary: `data/merit_registry.db` — table `registry_enriched`

Key columns of note (beyond the obvious name/location fields):

| Column | Notes |
|--------|-------|
| `merit_score` | 0–100 peer financial context score (NULL = unscored) |
| `merit_tier` / `merit_band` | Human-readable tier label derived from score |
| `ntee1_percentile` | Percentile rank within the NTEE1 peer group |
| `peer_percentile` / `peer_rank` / `peer_total` | Finer peer group stats |
| `mission` / `mission_source` | 1–2 sentence description; source = `ai_ntee`, `ai_generated`, or scraped |
| `cause_tags` | JSON array of categorization tags |
| `is_hidden_gem` | Boolean flag for small but high-performing orgs |
| `donate_url` / `donate_confidence` / `donate_url_status` | Verified donation link pipeline output |
| `website` / `website_status` / `website_final_domain` | Website health check fields |

Other tables in `merit_registry.db`: `org_fts` (FTS5 search index), `org_embeddings` (vector store), `score_snapshots`, `scoring_runs`, `org_claims`, `waitlist`, `irs_bmf`.

Secondary/legacy: `data/meritgiving.db`, `data/merit_state.db` — do not treat as authoritative.

### Frontend (`frontend/`)

- React 19, TypeScript, Vite; Tailwind CSS + Radix UI (shadcn-style)
- API base URL: `VITE_API_URL` env var, defaults to `http://localhost:5000` (see `src/api.ts`)
- Built output: `frontend/dist/` — Flask serves this as the SPA fallback on `/<path:path>`
- **Wallet / Giving List** persist exclusively in `localStorage` — no server-side user accounts
- **CompareContext** (`src/contexts/CompareContext.tsx`) is the only React context; holds up to 4 orgs for side-by-side compare
- `VITE_ENABLE_SCORES=false` suppresses score UI (Financial Health sort, tier badges) without changing the backend

### Data pipeline (`scripts/`)

Current scorer: `scripts/merit_scorer_v3_3.py`. Orchestration: `scripts/overnight_pipeline.py`. Do not extend `app.py` (legacy).

Key pipeline scripts:

| Script | Purpose |
|--------|---------|
| `scripts/merit_scorer_v3_3.py` | Compute 0–100 peer financial context scores into `registry_enriched` |
| `scripts/overnight_pipeline.py` | Nightly orchestrator: score → rebuild FTS → refresh stats |
| `scripts/build_fts_index.py` | Rebuild the `org_fts` FTS5 full-text search virtual table |
| `scripts/build_org_embeddings.py` | Generate mxbai-embed-large vectors into `org_embeddings` |
| `scripts/generate_missions.py` | AI mission generation via Qwen2.5-32B (local, port 11437) |
| `scripts/donation_link_pipeline.py` | Discover and verify donate URLs; writes `donate_url` + `donate_confidence` |

### API internals

- **Response cache**: in-process dict with per-namespace TTLs (no Redis). Invalidated only on restart. TTLs: `ntee` 2 h, `org` 10 min, `search` 5 min.
- **Admin endpoints** (`/api/admin/*`): require `X-Admin-Key` header matching `DAANAA_ADMIN_KEY` env var.
- **ENABLE_SCORES** env flag: set `ENABLE_SCORES=false` to null out `merit_score`/`merit_tier`/`merit_band` in all API responses.
- **DAANAA_PROD** env flag: enables HTTPS-only CSP and HSTS headers; absent in dev.
- **Embedding load**: at startup, `_load_embeddings()` reads ~546K org vectors into RAM as a numpy matrix. Uses `--preload` in gunicorn so workers share the allocation via CoW.
- **Search**: FTS5 (`org_fts`) for keyword search, cosine similarity on `org_embeddings` for semantic search. FTS5 availability is checked once and cached in `_fts_available`.

### Local inference services (ML pipeline)

Do not use cloud APIs for batch ML tasks — route through the local server:

| Port | Service | Model | Use |
|------|---------|-------|-----|
| 11437 | llama-server (Vulkan1) | Qwen2.5-32B-Instruct-Q4_K_M | Mission generation |
| 11436 | llama-server (Vulkan1) | mxbai-embed-large | Query & org embeddings (primary) |
| 11434 | Ollama | mxbai-embed-large | Embedding fallback only |

---

## Key gotchas

- **Scorer location**: `scripts/merit_scorer_v3_3.py` — not `api/` (that directory only has `main.py`, a secondary FastAPI specialist endpoint).
- **Root-level debris**: many `fix_*.py`, `app.py.backup.*`, `app.py.broken.*` files exist from iterative development. They are not part of the active codebase — do not import or extend them.
- **`app.py` tail is broken**: lines 337–354 mix Flask decorators into a FastAPI app. Ignore that block entirely.
- **Two databases**: `merit_registry.db` vs `meritgiving.db`. Only `merit_registry.db` feeds the live API.
- **Frontend package name**: `frontend/package.json` still says `"name": "my-app"` — scaffold default, never updated; ignore it.
- **venv**: always activate `~/meritgiving/venv` before running any Python in this project.
- **Ports in use**: API=5000, FastAPI legacy=8081, Vite dev=5173. Check `./check_merit_status.sh` before starting servers.

## Coding discipline

- Before editing any file, read the relevant section first. Before modifying a function, grep for all callers.
- Research before you edit. If the same approach fails twice, stop and ask.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /plan-design-review
- Full review pipeline → invoke /plan-ceo-review then /plan-eng-review
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
