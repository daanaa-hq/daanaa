# CLAUDE.md — MeritGiving

## Stewardship Commitment — Read before any work

This project operates under a Founding Stewardship Commitment (see `STEWARDSHIP.md`).
Every AI agent, contributor, and system operating on this platform is bound by it.

Before contributing any code, data change, copy edit, or system decision, you must:
1. Have read `STEWARDSHIP.md` in full
2. Operate in alignment with all 12 principles
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

Current scorer: `api/merit_scorer_v3_3.py`. Orchestration: `overnight_pipeline.py`. Do not extend `app.py` (legacy).

---

## Key gotchas

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
