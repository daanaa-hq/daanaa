# CLAUDE.md — MeritGiving

## What this project is

**MERIT** is a civic nonprofit-discovery platform. It indexes 501(c)(3) organizations from IRS and ProPublica public data, assigns each a 0–100 MERIT score, benchmarks it within its NTEE peer group, and surfaces the results through a searchable directory UI.

---

## Running the project

### API (Flask + SQLite) — primary backend
```bash
source ~/meritgiving/venv/bin/activate
python3 merit_api.py          # port 5000
# or use the restart script:
./restart_merit_api.sh
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

There are **three** backend files — use `merit_api.py` as the canonical one:

| File | Framework | Port | Data source | Status |
|------|-----------|------|-------------|--------|
| `merit_api.py` | Flask + SQLite | 5000 | `data/merit_registry.db` | **Active / canonical** |
| `api/main.py` | FastAPI + SQLite | varies | `data/merit_registry.db` | Secondary / specialist endpoints |
| `app.py` | FastAPI + flat CSV | 8081 | `data/master_orgs.csv` (in-memory) | Legacy — do not extend |

`app.py` also has broken Flask route decorators appended at lines 337–354 (`@app.route(...)` on a FastAPI object) — these are dead code left by a previous agent pass. Do not edit that tail block.

### Database

Primary: `data/merit_registry.db` — table `registry_enriched`

Key columns: `EIN`, `organization_name`, `NTEE1`, `CITY`, `STATE`, `total_revenue`, `ntee1_percentile`, `source`

Secondary/legacy: `data/meritgiving.db`, `data/merit_state.db` — do not treat as authoritative.

### Frontend (`frontend/`)

- React 19, TypeScript, Vite
- Tailwind CSS + Radix UI components (shadcn-style)
- Pages: `src/pages/Home.tsx`, `Directory.tsx`, `OrganizationDetail.tsx`
- API calls go to `http://localhost:5000` (see `src/api.ts`)
- Built output: `frontend/dist/` (served by `deploy_api_frontend.sh`)

### Data pipeline (`scripts/` + `api/`)

Pipeline stages:

1. **Ingest** — `ingest_bmf_master.py`, `xml_batch_parser.py` (IRS BMF + 990 XML)
2. **Score** — `merit_scorer_v3_3.py` is the latest scorer (ignore v1–v3.2)
3. **Enrich** — `enrich_propublica.py`, `enrich_v2.py` (ProPublica API cache)
4. **Percentiles** — `build_percentiles.py`, `compute_percentiles.py`
5. **Export** — `export_merit_csv.py`, `rebuild_master.py`
6. **Orchestrate** — `overnight_pipeline.py`, `autodev/orchestrator.py`

---

## Data sources

| Source | Location |
|--------|----------|
| IRS BMF (Business Master File) | `data/bmf/`, `data/irs_bmf.csv` |
| IRS 990 XML filings | `data/xml/` (by year) |
| ProPublica Nonprofit Explorer | `data/propublica_cache/` (per-EIN JSON) |
| Master org registry (flat) | `data/master_orgs.csv` |
| NTEE lookup | `ntee_map.json` (root), `data/ntee_complete_lookup.json` |

---

## MERIT scoring

Scores are 0–100, computed per NTEE peer group:

| Range | Badge |
|-------|-------|
| 90–100 | Exceptional Impact |
| 75–89 | High Impact |
| 60–74 | Solid Performer |
| 40–59 | Developing |
| < 40 | Needs Data |

The current scorer is `api/merit_scorer_v3_3.py`. Previous versions (`v1`, `v2`, `v3`, `v3.1`, `v3.3`) are present for reference but should not be used for new scoring runs.

---

## Key gotchas

- **Root-level debris**: many `fix_*.py`, `app.py.backup.*`, `app.py.broken.*` files exist from iterative development. They are not part of the active codebase — do not import or extend them.
- **`app.py` tail is broken**: lines 337–354 mix Flask decorators into a FastAPI app. Ignore that block entirely.
- **Two databases**: `merit_registry.db` vs `meritgiving.db`. Only `merit_registry.db` feeds the live API.
- **Frontend package name**: `frontend/package.json` still says `"name": "my-app"` — scaffold default, never updated; ignore it.
- **venv**: always activate `~/meritgiving/venv` before running any Python in this project.
- **Ports in use**: API=5000, FastAPI legacy=8081, Vite dev=5173. Check `./check_merit_status.sh` before starting servers.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
