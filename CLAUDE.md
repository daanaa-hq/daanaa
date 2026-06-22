# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@STEWARDSHIP.md

# CLAUDE.md — Daanaa

## Stewardship Commitment — Read before any work

This project operates under a **Founding Stewardship Commitment** (full text: `STEWARDSHIP.md`).
Every AI agent and contributor is bound by these 11 principles:

**Three non-negotiables:**
1. **Trust signals are evidence-based** (scores, badges = real data only)
2. **Donor privacy is structural** (no tracking, no exposure of giving activity)
3. **Independence is protected** (no paid placement, no partner influence)

**Key rules for all work:**
- Never present unverified outputs or experiments as established fact
- Small orgs treated with equal dignity to large ones
- Errors are corrected and documented (never hidden)
- All significant decisions are explainable and traceable
- Anything ranking orgs, shaping asks, or nudging users must check against `STEWARDSHIP.md` + `PRIVACY-INVARIANTS.md`

**Before working:** Read `STEWARDSHIP.md` in full. Flag conflicts immediately.

**Signed:** Claude Code (claude-sonnet-4-6) · AI Engineering Agent · 2026-05-20

---

## How we work (operating agreement)

Senior-engineer bar. The system gets smarter every session. Read this file,
`DECISIONS.md`, and `LESSONS.md` before starting work.

### The bar (every change)
- **Pragmatic tests-first.** New backend endpoints and anything touching privacy,
  scoring, or money ship with a failing-first test. (Not retro-covering the whole
  existing surface — grow the net where it matters.)
- **Strict types at boundaries.** Validate external input where it enters: Zod on the
  React/TS frontend, explicit guards on Flask endpoints. No silent `any`.
- **Small, reviewable diffs.** Prefer mature libraries over hand-rolling; justify each
  new dependency in one line in `DECISIONS.md`. YAGNI — no abstraction until two callers.
- **Boy-scout rule.** Leave touched files better. **Secrets only from env/config**,
  never logged, never in code.

### Autonomy (set 2026-06-01, site is live)
- Local edits, research, reads, builds, local tests → just do them.
- **Deploy to the droplet, push to GitHub, or spend money → stop, show, get approval.**

### Learning loop (do without being asked)
- Non-obvious choice → 2-line entry in `DECISIONS.md` (chose / why / rejected).
- Broke-then-fixed → entry in `LESSONS.md` (symptom / root cause / preventing rule).
- Pattern that worked → `LESSONS.md` with a code pointer.
- Every ~5–10 lessons → propose consolidating them into rules in *this file* (show first).

### Non-negotiables
- **Private by default.** Individual user data never goes raw to an external LLM — local
  inference or anonymized aggregates only. Structurally enforced (`PRIVACY-INVARIANTS.md`
  + `privacy_check.sh` pre-commit), not just convention.
- **Principles gate.** Anything that ranks orgs, shapes the ask, or nudges a user must be
  explainable from public data and must not pressure or imply tracking — check against
  `STEWARDSHIP.md` + `PRIVACY-INVARIANTS.md`.
- **Never handle funds.** Daanaa is a discovery + hand-off layer. We surface direct donate
  links and route to the org's own processor (or an EIN-based donation router) — we are
  never the merchant of record and never hold donor money. Crossing this triggers
  money-transmitter and charitable-solicitation-registration law and breaks the trust model.
- **Human in command.** I propose; you approve anything that writes to the shared repo,
  spends budget, or hits production.

### Definition of done
Tests pass, types clean, docs reflect the change, diff is small and explained, and
`DECISIONS.md`/`LESSONS.md` updated if anything non-obvious happened. If any is missing,
it isn't done — I'll say so.

---

## What this project is

**Daanaa** (daanaa.org) is a civic nonprofit-discovery platform. It indexes 501(c)(3) organizations from IRS and ProPublica public data, assigns each a 0–100 peer financial context score, benchmarks it within its NTEE peer group, and surfaces the results through a searchable directory UI.

---

## Running the project

### API (Flask + SQLite) — primary backend
```bash
source ~/meritgiving/venv/bin/activate
./restart_api.sh              # production: gunicorn 4-workers, --preload (use this)
python3 daanaa_api.py         # dev: single-process Flask (no --preload)
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

**`daanaa_api.py` is the only backend** (Flask + SQLite, port 5000, ~2,700 lines, all
routes). The old `merit_api.py` and `app.py` were removed in the daanaa rename; the
dormant FastAPI specialist (`api/main.py`) was archived to `archive/api_fastapi_20260609/`
on 2026-06-09 (its endpoints sorted by revenue, violating the no-size-ranking principle).
If any doc or script still references `merit_api.py`, it is stale — fix it on sight
(a dead cron watchdog and the principle test suite both broke this way).

### Database

Primary: `data/merit_registry.db` — table `registry_enriched`

Key columns of note (beyond the obvious name/location fields):

| Column | Notes |
|--------|-------|
| `merit_score` | (v4) 0–100 peer financial context score within operating model + band |
| `merit_tier` / `merit_band` | (v4) Lamp tiers (Beacon/Torch/Candle/Spark); still active for visibility layer |
| `merit_score_v5` | (v5) 0–100 financial context percentile rank within archetype + revenue band |
| `merit_archetype_v5` / `merit_archetype_v5_label` | (v5) Funding model: Donation-Funded, Fee-for-Service, Endowment-Funded |
| `merit_band_v5_label` | (v5) Revenue band: Micro (<$150K), Professional ($150K–$700K), Established (>$700K) |
| `merit_health_signal_v5` | (v5) Financial health: HEALTHY, STABLE, or CAUTION |
| `merit_peer_group_v5` / `merit_peer_count_v5` | (v5) Peer cell size and ranking within cell |
| `ntee1_percentile` | Percentile rank within the NTEE1 peer group |
| `peer_percentile` / `peer_rank` / `peer_total` | Finer peer group stats |
| `mission` / `mission_source` | 1–2 sentence description; source = `ai_ntee`, `ai_generated`, or scraped |
| `cause_tags` | JSON array of categorization tags |
| `is_hidden_gem` | Boolean flag for small but high-performing orgs |
| `donate_url` / `donate_confidence` / `donate_url_status` | Verified donation link pipeline output |
| `website` / `website_status` / `website_final_domain` | Website health check fields |
| `street_address` | Backfilled from `data/bmf.csv` (95.7% coverage) by `scripts/backfill_street_addresses.py` |

Other tables in `merit_registry.db`: `org_fts` (FTS5 search index), `org_embeddings` (vector store), `score_snapshots`, `scoring_runs`, `org_claims` (claim flow + versioned attestations — see `docs/CLAIM-ATTESTATIONS.md`), `waitlist`. (There is no `irs_bmf` table — the BMF lives at `data/bmf.csv`.)

Secondary/legacy: `data/meritgiving.db`, `data/merit_state.db` — do not treat as authoritative.

### Frontend (`frontend/`)

- React 19, TypeScript, Vite; Tailwind CSS + Radix UI (shadcn-style)
- API base URL: `VITE_API_URL` env var, defaults to `http://localhost:5000` (see `src/data/api.ts`)
- Built output: `frontend/dist/` — Flask serves this as the SPA fallback on `/<path:path>`
- **Wallet** (`WalletPage.tsx`) persists in `localStorage` via `WalletContext` — bookmarks + giving intent only, no transactions; `ImpactWallet.tsx` and `Wallet.tsx` deleted (dead)
- **GivingListContext** (`src/contexts/GivingListContext.tsx`) still exists as a compatibility shim for `useGivingList` hook — the GivingList page itself is removed
- **CompareContext** (`src/contexts/CompareContext.tsx`) holds up to 4 orgs for side-by-side compare
- `VITE_ENABLE_SCORES=false` suppresses score UI (Financial Health sort, tier badges) without changing the backend

### Data pipeline (`scripts/`)

**Financial context system:** v5 (Donation-Funded/Fee-for-Service/Endowment-Funded,
3 revenue bands, health signals) drives all user-facing financial context. v4 (9
operating models) and lamp tiers remain for backwards compatibility and the
visibility layer. The research page documents v5; org detail pages show v5 context.

Production scorer: `scripts/merit_scorer_v4_0.py` (runs nightly via
`overnight_pipeline.py`). v5 columns are pre-computed and stable in the database
(411K+ orgs scored; coverage bounded by financial data availability, not partial
run). Dry-run revealed v5 only assigns 3 archetypes (NTEE mapping constraint);
re-scoring would not add missing archetypes or expand coverage.

Legacy scorers (v2_0, v3_3, _db, _tier_b/_c, agent2) archived to
`archive/legacy_scorers_20260609/` — never run those.

Key pipeline scripts:

| Script | Purpose |
|--------|---------|
| `scripts/merit_scorer_v4_0.py` | Compute peer financial context scores + v4 tiers (validated by `validate_v4_scores.py`) |
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

- **Scorer location**: `scripts/merit_scorer_v4_0.py` — legacy scorers live in `archive/legacy_scorers_20260609/`, never run them.
- **Root-level debris**: stray `fix_*.py` and backup files from iterative development are not part of the active codebase — do not import or extend them.
- **Two databases**: `merit_registry.db` vs `meritgiving.db`. Only `merit_registry.db` feeds the live API.
- **Frontend package name**: `frontend/package.json` still says `"name": "my-app"` — scaffold default, never updated; ignore it.
- **venv**: always activate `~/meritgiving/venv` before running any Python in this project.
- **Ports in use**: API=5000, FastAPI legacy=8081, Vite dev=5173. Check `./check_merit_status.sh` before starting servers.

## Coding discipline

- Before editing any file, read the relevant section first. Before modifying a function, grep for all callers.
- Research before you edit. If the same approach fails twice, stop and ask.

---

## Tool Permissions (Principle of Least Privilege)

**Stewardship Principle #9 applied:** Decisions should be explainable. Tool permissions are scoped to prevent accidental
misuse and enforce structural guardrails on sensitive operations.

### Bash
- ✅ **Allowed:** `git *`, `npm *`, `python3 *`, `ssh *`, `curl *`, file utilities (`ls`, `grep`, `find`, `cat`)
- ❌ **Blocked:** `rm -rf`, `sudo`, `chmod`, `pkill`, `killall`, any unquoted `system()` calls
- **Why:** Prevents destructive operations on shared code or infrastructure

### Edit / Write
- ✅ **Allowed:** `src/`, `frontend/`, `scripts/`, `docs/`, `tests/`, `data/`
- ❌ **Blocked:** `.env*`, `secrets.*`, `config/production.*`, `PRIVATE*`, `*credentials*`, `.ssh/`, `Makefile` auth sections
- **Why:** Prevents accidental credential commits; secrets stay in env/config only

### Read
- ✅ **Allowed:** All codebase files, `data/`, `docs/`, `scripts/`, project architecture
- ❌ **Blocked:** `/etc/`, `/root/`, `/home/*/.ssh/`, system config files outside the project
- **Why:** Boundaries protect system-level secrets from leaking into project context

### Privacy-Check Hook
- **Enforced at every commit** by `/home/akbar/meritgiving/privacy_check.sh`
- Blocks: token patterns, log leakage, env var fallbacks, exfiltration vectors, data source mismatches
- See `privacy_check.sh` for full rules aligned with STEWARDSHIP.md Principles #2 and #3

### Approval Gates (Autonomy Rule)
These operations **require explicit approval** before execution:
- Writing to shared repo (`git push`, `git commit` on branches)
- Deploying to production (`safe_deploy_droplet.sh`, droplet API restart)
- Spending budget (cloud APIs, services)
- Anything touching the database schema or migration

**Pattern:** I show the proposed change, you approve it before it ships.

---

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
