# Current State

## Document Control

| Field | Value |
|---|---|
| Purpose | Record verified institutional and technical discovery state. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Evidence snapshot, not policy. |
| Review trigger | Weekly review, major deploy, schema change, incident, or contradictory evidence. |
| Editable status | Editable by ordinary agents with dated evidence. |
| Dependencies | Repository files, tests, local DB, git history. |
| Retirement condition | Retire only when superseded by a maintained state database or newer snapshot. |

## Snapshot

Date: 2026-07-10  
Branch: `stewardship-system-bootstrap`  
Base state: repository was on `master`, ahead of `origin/master` by 22 commits before branching.  
Latest reviewed commit: `0786209d54b feat: directory surfaces unresolved-location warning + no-data revenue hint (approved)`.

## Verified Architecture

- Backend: Python Flask APIs.
- Primary full API: `daanaa_api.py`.
- Production edge/droplet API: `scripts/droplet_api.py`, serving a lean `search.db` contract and precomputed/static assets.
- Frontend: React 19, TypeScript, Vite, Tailwind CSS, Radix UI, Firebase Auth.
- Data store: SQLite, especially `data/merit_registry.db`.
- Search: SQLite FTS5 (`org_fts`) and embeddings (`org_embeddings`) in local/full environment; droplet uses lean search DB.
- AI/local inference: docs and scripts reference llama-server/Ollama on local ports 11436, 11437, 11434.
- Analytics: first-party `/api/event` exists; frontend also includes Plausible script in `frontend/index.html`.
- Auth: Firebase Auth in frontend; Firebase JWT verification in `daanaa_api.py`; admin endpoints use `DAANAA_ADMIN_KEY`.
- Deployment: DigitalOcean droplet and Cloudflare are documented; `scripts/ops/sync_droplet_api.sh` is the hardened droplet API path.
- Optional/external integrations present in repo: Firebase/Firestore REST, Sentry optional DSN, AWS/S3 enrichment and backups, Plausible, n8n, Metabase, Jambonz, Uptime Kuma, nginx/systemd.

## Verified Data Facts

- `data/merit_registry.db` quick check: `ok`.
- `registry_enriched`: 2,042,897 rows.
- `org_embeddings`: 2,042,897 rows.
- `org_fts`: 1,746,595 rows.
- `org_claims`: 3 rows.
- `waitlist`: 0 rows.
- `data/` contains approximately 124G of local artifacts and backups by `ls -lh`.
- Root contains large score snapshots and generated/deploy artifacts; avoid broad `git add -A`.

## Validations Run

- `python3 -m py_compile daanaa_api.py nonprofit_portal_endpoints.py scripts/droplet_api.py scripts/build_search_db.py scripts/website_normalize.py`: pass.
- `bash -n scripts/ops/sync_droplet_api.sh`: pass.
- `./venv/bin/python3 -m pytest tests/test_principles.py tests/test_website_normalize.py -q`: 33 passed.
- Isolated claim-login test with `/tmp` DB: 5 passed.
- Frontend targeted Jest: 3 suites, 26 tests passed.
- `npm run lint`: failed because ESLint 9 requires `eslint.config.*`; no such config is present.

## Maturity Assessment

Mature or strong:

- Stewardship principles exist and are referenced by agent instructions.
- Decision and lesson logs contain recent, specific incident memory.
- Principle tests cover several privacy, payment, and trust invariants.
- Droplet API deploy script includes wrong-file guard, smoke tests, and rollback.
- Local data pipeline uses substantial public IRS/nonprofit data and cached artifacts.

Unfinished or inconsistent:

- Documentation conflicts over canonical backend, wallet storage, analytics, autonomy, and production routing.
- Frontend lint is currently not a working validation gate.
- Full test-suite status is not verified in this bootstrap.
- Offsite backup status is unresolved from repo evidence.
- TiDB credential rotation is unresolved from repo evidence.
- Root-level `droplet_api.py` and `scripts/droplet_api.py` represent a recurring wrong-file risk.
- Funding, budget, legal, and founder approval state remain mostly unknown.

Unknown:

- Current cash, runway, exact monthly spend, and active paid services.
- Current production deployment state and live cron list.
- Whether Sentry, Plausible, AWS/S3, Google Workspace, Firebase, n8n, Jambonz, or other services are actively paid.
- Whether Claude Code is currently editing the same files.

## Controlled Implementation Update

Date: 2026-07-10

- Authority order is now explicit in `institution/AUTHORITY.md` and referenced by `AGENTS.md`.
- Machine-readable operating state now lives in `institution/state.json`.
- Claude Code-Codex coordination now lives in `institution/HANDOFF_PROTOCOL.md` and `institution/tasks/`.
- Minimum stewardship skill specifications now live in `institution/skills/`.
- Manual weekly review now validates `py_compile`, targeted pytest, frontend lint, targeted frontend tests, frontend build, local services, local model availability, and sampled logs.
- Frontend lint now runs under ESLint 9 with a local flat config; the command passes with warnings and no errors.
- Remaining warning backlog is real technical debt, not a blocked validation gate.
