# Repository Inventory

Date: 2026-07-13  
Scope root: `/home/akbar/meritgiving`

## Inventory Method

Primary inventory command used `rg --files -uu` with exclusions for generated dependencies, build outputs, caches, logs, archives, and large data paths. This audit does not claim byte-for-byte review of every generated artifact or dependency.

Refined source scope: 3,513 paths.

## Major Subsystems

| Subsystem | Purpose | Evidence Reviewed |
|---|---|---|
| `institution/` | Constitutional memory, stewardship library, state, risks, succession, board/founder records. | Governing docs, charter, library 011, current state, succession, risk register. |
| Root governance files | Agent rules, stewardship commitment, privacy invariants, decisions, lessons. | `AGENTS.md`, `CLAUDE.md`, `STEWARDSHIP.md`, `PRIVACY-INVARIANTS.md`, `DECISIONS.md`, `LESSONS.md`. |
| Backend API | Primary Flask API, claim flow, wallet, public search, admin, concierge, vendor/guild, research endpoints. | `daanaa_api.py`, tests, selected docs. |
| Droplet edge API | Production/static edge behavior, search DB contract, wallet/claim proxy, SPA metadata. | `scripts/droplet_api.py`, deploy lessons, tests. |
| Frontend | React/Vite public app and nonprofit/vendor/admin surfaces. | Charter, privacy, terms, methodology, org detail, wallet, footer, structured data hooks. |
| Data/scoring pipeline | IRS/NCCS/ProPublica ingestion, scoring, search, visibility exports. | `scripts/`, scorer tests, visibility export scripts. |
| Visibility overlay | Static search/AI discoverability layer. | `visibility/README.md`, `visibility/scripts/*`, generated public surface sampled. |
| Tests | Principle, privacy, concierge, search, wallet, donation-link and routing coverage. | Targeted pytest runs and representative test files. |
| Docs | Historical plans, legal drafts, product specs, audit records, runbooks. | Representative docs; stale docs treated as historical unless current authority promotes them. |
| Hidden workflow state | Agent memory, screenshots, planning diffs, workflow checkpoints. | Inventoried and sampled; not treated as authoritative unless backported. |

## Major File Types In Refined Scope

| Extension | Count |
|---|---:|
| `.html` | 1,374 |
| `.md` | 547 |
| `.py` | 439 |
| `.tsx` | 205 |
| `.pyc` | 156 |
| `.sh` | 130 |
| `.json` | 86 |
| `.png` | 85 |
| `.xml` | 83 |
| `.txt` | 46 |
| `.ts` | 45 |
| `.csv` | 37 |
| `.sql` | 10 |
| `.pdf` | 7 |

## Generated Or Excluded Paths

Excluded from detailed file-by-file review:

- `venv/`
- `node_modules/`, `frontend/node_modules/`
- `frontend/dist/`, `dist/`
- `data/`
- `precompute_output/`, `precompute_archive/`
- `logs/`
- `backups/`, `.backups/`
- `.deploy_scratch/`
- `.git/`
- `archive/`
- `merit-platform/`, `nonprofit-explorer/`

Reason: generated dependencies, derived data, runtime state, historical code, or external/reference trees. Their configurations and references were considered when relevant.

## Inaccessible Or Not Fully Verified

- Provider consoles: GitHub organization admin list, Cloudflare, DigitalOcean, Firebase, AWS, Google Drive/rclone, Plausible, Sentry, Twilio, Stripe, Jambonz, n8n, Metabase.
- Live production behavior: not tested beyond repository-local evidence because deployment/live probing was not part of this documentation-only audit.
- Secrets: `.env` and rotated environment files exist in scope but values were not reproduced. Presence of secret-like files should be reviewed separately with redaction.
- Large datasets and databases: source existence and relevant scripts were reviewed; full data contents were not enumerated.

## Scope Honesty Statement

This is a broad institutional audit with representative code and document tracing. It is not a complete static-analysis proof, security penetration test, legal opinion, financial audit, or provider-console audit.

