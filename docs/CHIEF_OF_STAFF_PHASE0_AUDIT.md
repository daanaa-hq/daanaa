# Founder Institutional Chief of Staff: Phase 0 Audit

Date: 2026-07-18  
Branch: `feature/founder-institutional-chief-of-staff`  
Scope: local repository and synthetic/local capability inspection only.

## Decision boundary

This cycle is restricted for live Gmail, Calendar, authentication, production
database schema, public deployment, external provider access, and confidential
data. No live account was connected and no external service was called.

The requested private `daanaa-hq` repository is not present at the expected local
path. The in-repo institutional corpus and `/home/akbar/daanaa-ai-stewardship`
were inspected as available references; the provenance discrepancy is recorded
as an unresolved contradiction and must not be silently resolved.

## Current architecture

- Canonical full backend: `daanaa_api.py` (Flask + SQLite).
- Production edge path: `scripts/droplet_api.py` and a lean search database.
- Frontend: React 19 / TypeScript / Vite under `frontend/`; frontend changes remain review-gated.
- Primary local data: `data/merit_registry.db`; legacy databases are not authoritative.
- Search: SQLite FTS5 plus local embeddings; in-process response cache.
- Local inference documented on ports 11436/11437/11434; Ollama currently exposes `mxbai-embed-large:latest` locally.
- Deployment documentation references DigitalOcean, Cloudflare Tunnel, Firebase, and optional providers; live billing and provider state are unverified.

## Authority map and findings

The repository authority order is explicit in `institution/AUTHORITY.md`:
`PURPOSE` → `COVENANT` → `CONSTITUTION` → stewardship commitments → governance →
privacy/decisions/lessons → current state/risk → task records → implementation.
The root `STEWARDSHIP.md` is marked Supreme Law and the Charter is adopted in
its revision log. No protected document was modified.

Material drift found in existing evidence: current-state snapshots are dated
July 10/11 while the working tree is July 18; wallet, analytics, backend routing,
and autonomy descriptions have known historical drift. Search reliability,
backup status, and credential rotation remain open risks in the institutional
register. The new code therefore defaults to conservative refusal and records
provenance rather than guessing.

## Security, privacy, and operations

Existing controls include `privacy_check.sh`, tiered data classification, admin
key boundaries, CSP requirements, local inference preference, and a droplet
rollback/smoke-test path. Unknowns include current production exposure, active
provider billing, live cron state, offsite restore freshness, and credential
rotation. No secrets were read or written.

## Safe foundations implemented in this cycle

`stewardship_core/` provides dependency-free, local-only primitives for:

- authority inventory and conservative resolution;
- contradiction and missing-governance restricted mode;
- Tier 0/1/2 data classes and retention categories;
- prompt-injection detection and redacted operational logging;
- hash-chained append-only audit events;
- local model routing with deterministic/manual-review fallbacks;
- confidence thresholds and protected-data externalization denial.

These are interfaces and local test fixtures, not connected workflows. A
production database migration is intentionally proposed but not applied.

## Proposed boundaries and milestones

1. Validate this core with synthetic tests (completed in this cycle).
2. Add reviewed local stores and migration scripts; founder review required before production application.
3. Build Gmail/Calendar adapters in dry-run mode with minimum scopes; do not authenticate until security review passes and founder completes official login.
4. Add founder review packages and keep sending/event mutation technically disabled.
5. Add institutional-memory persistence only after schema and access-control review.

## Founder decisions required

- Confirm the authoritative private repository path and whether it should be mirrored or referenced.
- Approve any production schema migration and retention implementation.
- Approve official Google OAuth scopes after security prerequisites pass.
- Resolve current backup/restore freshness, provider billing, and credential-rotation unknowns.
- Approve any second-user access, including future-wife access boundaries.

## Rollback

Remove or revert only the new branch commits; no production data, service, or
authoritative governance file is changed by this cycle.
