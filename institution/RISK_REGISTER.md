# Risk Register

## Document Control

| Field | Value |
|---|---|
| Purpose | Track material mission, privacy, security, reliability, cost, legal, and continuity risks. |
| Responsible role | Stewardship Systems Agent; owners assigned per risk. |
| Authority level | Risk memory; not approval to act. |
| Review trigger | Weekly review, incident, new integration, new paid service, or public launch step. |
| Editable status | Editable by ordinary agents; closed risks retain rationale. |
| Dependencies | `CURRENT_STATE.md`, `FOUNDER_REQUESTS.md`, `BUDGET_STATE.md`. |
| Retirement condition | Retire when migrated to an issue tracker or risk database. |

| ID | Risk | Category | Evidence | Severity | Owner | Status | Next action |
|---|---|---|---|---|---|---|---|
| R-001 | Conflicting docs on canonical backend and production routing can cause wrong-file deploys. | Reliability | `LESSONS.md` records root `droplet_api.py` shipped twice; `scripts/droplet_api.py` is lean edge. | High | Product Engineering | Open | Keep product-code changes out of bootstrap; clarify in founder brief. |
| R-002 | Frontend lint warning backlog still weakens lint signal quality even though the command now runs. | Quality | `frontend/eslint.config.js` restores ESLint 9 execution, but 27 warnings remain. | Medium | Product Engineering | Open | Reduce warning backlog in later product-quality work without hiding it. |
| R-003 | TiDB credential rotation remains unverified. | Security | `SECURITY_NOTES.md` marks rotation as owner action. | High | Founder | Open | Confirm rotation or retire TiDB paths. |
| R-004 | Offsite backup is unverified. | Continuity | Local full restore passed on 2026-07-14 from `full_20260712.db.gz`; offsite Google Drive / `rclone daanaa-backup:` restore remains unverified. | High | Operations | Open | Run non-destructive offsite list check and offsite restore drill; record result in `institution/reviews/`. |
| R-005 | Approval/autonomy model conflict can cause unsafe production actions. | Governance | `CLAUDE.md` permits backend deploys; bootstrap directive requires founder approval. | High | Chief Steward | Open | Founder confirms delegation model. |
| R-006 | Analytics/privacy docs conflict. | Privacy | `PRIVACY-INVARIANTS.md` says no third-party analytics/Sentry; code includes Plausible script and optional Sentry. | Medium | Security/Privacy | Open | Reconcile policy with actual allowed telemetry. |
| R-007 | Large generated artifacts and backups increase accidental commit and disk-risk surface. | Cost/Reliability | Root and `data/` contain large snapshots and backups. | Medium | Operations | Open | Audit `.gitignore` and storage retention separately. |
| R-008 | Public hardcoded stats and unsourced claims may conflict with evidence-based trust. | Mission/Data honesty | Prior readiness check flagged hardcoded counts and a vendor `97%` claim. | Medium | Product/Growth | Open | Product copy audit before further outreach. |
| R-009 | Import-time DB initialization makes tests sensitive to locks. | Quality/Reliability | Claim-login tests failed when app import touched locked DB; passed with explicit `/tmp` DB. | Medium | Product Engineering | Open | Move init work behind app factory or enforce test DB env. |
| R-010 | Current monthly spend and runway are unknown. | Financial stewardship | Billing data not in repo. | High | Founder/Finance | Open | Founder request FR-2026-07-10-001. |
| R-011 | Current GPU, CPU, and cloud-usage telemetry are not available in a durable local source. | Cost/Operations | Repo and local process checks show services, but no maintained utilization record was found. | Medium | Operations | Open | Keep usage unknown in `state.json`; add local metrics source only after manual need is proven. |
| R-012 | Claude Code and Codex coordination was not previously durable in-repo. | Governance/Continuity | Parallel product work is likely; hidden local state would create merge and ownership risk. | Medium | Product Engineering | Open | Use `institution/HANDOFF_PROTOCOL.md` and `institution/tasks/` for explicit ownership. |
| R-013 | Recent backend search traffic has hit schema-drift errors in local logs. | Reliability | Sampled `logs/daanaa_api.log` shows `/api/search` failures on missing `v4.peer_cell_size`; regression coverage added in `tests/test_search_reliability.py`. | High | Product Engineering | Open | Confirm whether this is already fixed in code and whether production still sees the error before changing stewardship priorities. |
