# Decision Log

## Document Control

| Field | Value |
|---|---|
| Purpose | Preserve material institutional decisions and reasoning. |
| Responsible role | Stewardship Systems Agent; Chief Steward for approvals. |
| Authority level | Durable memory; decisions do not override `CONSTITUTION.md`. |
| Review trigger | Any reversal, incident, major change, or weekly review. |
| Editable status | Append-only for material decisions; corrections should supersede rather than erase. |
| Dependencies | `STEWARDSHIP.md`, `GOVERNANCE.md`, `RISK_REGISTER.md`. |
| Retirement condition | Retire when migrated to a versioned decision-record database. |

## DR-2026-07-10-001: Create Isolated Institutional Layer

- Identifier: DR-2026-07-10-001.
- Date: 2026-07-10.
- Issue: Bootstrap stewardship system without rewriting product.
- Context: Repo has active product code, extensive docs, recent incident memory, and possible parallel Claude Code work.
- Sources: User directive, `CLAUDE.md`, `STEWARDSHIP.md`, `LESSONS.md`, `docs/audit/*`, local DB checks.
- Options considered: modify product architecture, extend existing `meritgiving-ops`, or add isolated `institution/`.
- Board simulation summary: Mission, security, and continuity perspectives favored isolated additive files; technology perspective warned against duplicate state; small nonprofit perspective favored clarity and free access protections.
- Stewardship principles applied: mission before growth, privacy, evidence, explainability, continuity.
- Decision: Add compact `institution/` layer and root `AGENTS.md`; do not touch product code.
- Decision owner: Stewardship Systems Agent, subject to Chief Steward review.
- Expected outcome: Better agent orientation and safer operating loop.
- Risks accepted: Another documentation surface exists; mitigated by concise files and review triggers.
- Review trigger: After two manual weekly reviews or any evidence of confusion.
- Actual outcome: Pending.
- Lessons: Pending.
- Superseding decision: None.

## DR-2026-07-10-002: Manual Weekly Review Before Scheduling

- Identifier: DR-2026-07-10-002.
- Date: 2026-07-10.
- Issue: Whether to schedule weekly institutional review immediately.
- Context: User requested a scheduled weekly review after manual workflow succeeds.
- Sources: User directive; `LESSONS.md` duplicate scheduler incidents.
- Options considered: schedule cron now, create manual script only, or do no automation.
- Board simulation summary: Operations favored a script; security and continuity opposed immediate cron; founder-burden perspective favored manual proof first.
- Decision: Create `scripts/institution_weekly_review.py`; do not schedule it.
- Decision owner: Stewardship Systems Agent.
- Expected outcome: First review can run locally with no external services.
- Risks accepted: Manual process may be forgotten.
- Review trigger: Two successful manual reviews.
- Actual outcome: Pending first run.
- Lessons: Pending.
- Superseding decision: None.

## DR-2026-07-10-003: Use Stricter Approval Rule For Codex Bootstrap

- Identifier: DR-2026-07-10-003.
- Date: 2026-07-10.
- Issue: Existing docs allow autonomous backend deploys; bootstrap directive requires founder approval for production deployment.
- Context: Recent lessons show production outages from wrong droplet API deployments.
- Sources: User directive, `CLAUDE.md`, `LESSONS.md`.
- Options considered: follow old autonomous rule, follow stricter bootstrap rule, or ask immediately.
- Board simulation summary: Security, mission, and continuity perspectives favored stricter rule; technology perspective noted slower fixes; financial perspective saw no cost.
- Decision: For this Codex bootstrap, no production deployment without explicit founder approval.
- Decision owner: Stewardship Systems Agent pending founder confirmation.
- Expected outcome: Reduced production risk.
- Risks accepted: Some urgent backend fixes may wait for approval.
- Review trigger: Founder clarifies delegation model.
- Actual outcome: Pending.
- Lessons: Pending.
- Superseding decision: None.

## DR-2026-07-10-004: Establish Minimum Operating Authority And Handoff Layer

- Identifier: DR-2026-07-10-004.
- Date: 2026-07-10.
- Issue: Bootstrap documents existed, but the authority order, handoff protocol, and machine-readable operating state were not yet operational.
- Context: The controlled implementation directive required a usable stewardship loop without rewriting the product.
- Sources: `AGENTS.md`, `institution/README.md`, `institution/CONSTITUTION.md`, controlled implementation directive.
- Options considered: keep only human-readable docs, add a lightweight machine-readable state plus handoff docs, or build a new database-backed governance system.
- Board simulation summary: mission, continuity, and product perspectives favored the lightweight in-repo state; finance and privacy perspectives rejected adding paid systems or new data collection.
- Stewardship principles applied: continuity, reversibility, no fabricated facts, low-cost operation.
- Decision: Add `institution/AUTHORITY.md`, `institution/state.json`, `institution/HANDOFF_PROTOCOL.md`, minimum skill specs, and task records.
- Decision owner: Stewardship Systems Agent.
- Expected outcome: Daanaa can know its current state, identify a constraint, coordinate product work, and preserve learning in-repo.
- Risks accepted: Another documentation/state surface exists; mitigated by keeping it compact and generated from local evidence.
- Review trigger: Next manual weekly review or conflicting instruction incident.
- Actual outcome: Completed in this cycle.
- Lessons: Small machine-readable state plus one durable handoff protocol is enough for the first loop; broader tooling is unnecessary now.
- Superseding decision: None.

## DR-2026-07-10-005: Restore Frontend Lint As A Working Validation Gate

- Identifier: DR-2026-07-10-005.
- Date: 2026-07-10.
- Issue: `npm run lint` failed immediately because ESLint 9 had no flat config, leaving no working frontend lint gate.
- Context: The first manual weekly review identified the broken lint gate as the highest current constraint that could be improved safely without founder approval.
- Sources: `institution/reviews/2026-07-10-weekly-review.md`, `frontend/package.json`, `npm run lint` output.
- Options considered: leave lint broken, pin ESLint backward, or add a conservative flat config that restores command-level validation without rewriting legacy frontend behavior.
- Board simulation summary: mission, product, continuity, and finance perspectives favored the conservative flat config; the dissenting view warned not to confuse lint restoration with resolving broader documentation and runtime risks.
- Stewardship principles applied: low-risk reversibility, cost control, evidence-first validation, preserve working product behavior.
- Decision: Add `frontend/eslint.config.js` and scope the initial ruleset to restore a working lint command while leaving warning backlog visible for later product debt work.
- Decision owner: Stewardship Systems Agent.
- Expected outcome: `npm run lint` exits successfully and future frontend changes regain a usable baseline gate.
- Risks accepted: Warning backlog remains and some stricter rules are deferred; documented for later follow-up rather than hidden.
- Review trigger: Next frontend quality pass or if warning volume grows materially.
- Actual outcome: Completed; lint passes with warnings and no errors.
- Lessons: For legacy code, restoring a gate first is safer than forcing behavioral rewrites under a stewardship loop task.
- Superseding decision: None.

