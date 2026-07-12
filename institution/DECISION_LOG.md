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
## DR-2026-07-12-006: Add Explicit Constitutional Hierarchy Doc

- Identifier: DR-2026-07-12-006.
- Date: 2026-07-12.
- Issue: The board resolution established a Mission -> Constitution -> Library -> Policies -> Engineering -> Implementation chain that existed implicitly but was not yet explicit in-repo.
- Context: Phase 2 of the board implementation plan needed a compact authority map so future stewards can resolve conflicts without inferring the hierarchy from scattered documents.
- Sources: `institution/board/2026-07-11_board_resolution.md`, `institution/IMPLEMENTATION_PLAN.md`, `institution/SUCCESSION.md`.
- Options considered: leave authority implicit, duplicate the hierarchy into multiple docs, or create one canonical hierarchy file and add short parent/child headers to the three tier documents.
- Decision: Create `institution/CONSTITUTION_HIERARCHY.md`, add authority headers to `STEWARDSHIP.md`, `institution/CONSTITUTION.md`, and `institution/library/003_stewardship.md`, and index the hierarchy doc in `institution/README.md`.
- Decision owner: Stewardship Systems Agent.
- Expected outcome: authority order is visible at a glance and lower documents can point back to their parent layer.
- Risks accepted: one more governance doc exists; mitigated by keeping it short and referencing the existing hierarchy instead of inventing new policy.
- Review trigger: When the board revisits Phase 2 or if any authority conflict appears in the institutional docs.
- Actual outcome: Completed in this session.
- Lessons: Durable governance works better when the hierarchy is explicit once, then referenced lightly everywhere else.
- Superseding decision: None.

## DR-2026-07-12-007: B-Lite Infrastructure Path for Pre-Launch

- Identifier: DR-2026-07-12-007.
- Date: 2026-07-12.
- Issue: Choose infrastructure investment strategy for pre-launch phase. Platform needs world-class reliability + global reach, but has zero users yet. Over-invest early (Path B, $300/mo) or invest selectively (Path B-Lite, $100/mo now → $230/mo at month 2)?
- Context: Founder approved $100/mo additional budget for quality infrastructure. Long-term sustainability and 100-year institutional horizon are non-negotiable. Three major incidents (INC-001, INC-002, INC-003) proved that corners cut early become expensive later.
- Sources: STANDING_CONSTRAINTS_2026_07.md, INCIDENTS_2026_07.md, CLAUDE.md, founder directive.
- Options considered: Path A (lean $100/mo, add services as traffic demands; risk scaling issues), Path B (full $300/mo upfront; waste money if product fails), Path B-Lite (prove product first at $100/mo, upgrade to $230/mo when credibility/traction signals appear).
- Board simulation summary: Mission (sustainability > growth velocity), Finance (prove before spending), Continuity (avoid tech debt from corner-cutting), Technology (commodity services scale better than custom), all perspectives favored Path B-Lite.
- Stewardship principles applied: P1 (mission before growth; sustainability is the mission here), P9 (decisions must be explainable; this tradeoff is clear), evidence-based (upgrade trigger is measurable: 3+ advisors OR partnership OR 5K users).
- Decision: Launch Phase 1 at $100/mo (Postgres, Redis, S3, Backups, Basic Monitoring). At week 8, upgrade to Phase 2 ($230/mo; add Elasticsearch + Datadog) if any trigger condition is met (credibility signal, partnership, 5K+ users). Otherwise hold at $100/mo.
- Decision owner: Founder (Akbar Khowaja), AI Steward (autonomous execution within budget).
- Expected outcome: Infrastructure ready for 100x scale without rework; prove product before investing in specialized services; sustainable long-term (infrastructure cost justified by revenue/partnerships).
- Risks accepted: (1) Month 1–2 may have slower search (FTS5 vs. Elasticsearch), basic monitoring only. Mitigated: FTS5 handles 10K orgs fine; will upgrade if/when needed. (2) May feel "lean" vs. "world-class" for 8 weeks. Mitigated: institutional governance + research + advisor credibility are the real signals; infrastructure quality follows.
- Review trigger: Week 8 decision gate (upgrade or hold); any incident showing $100/mo insufficient; or founder signals change in revenue model/timeline.
- Actual outcome: Superseded before execution — no money spent, no migration started.
- Lessons: Captured in DR-2026-07-12-008 — the founder's "bounded dataset" fact invalidated the Postgres premise before provisioning.
- Superseding decision: DR-2026-07-12-008.

## DR-2026-07-12-008: Harden Baked-Data Architecture Instead of Postgres Migration

- Identifier: DR-2026-07-12-008.
- Date: 2026-07-12.
- Issue: DR-2026-07-12-007 approved a Postgres + Redis migration path ($100/mo → $230/mo). Founder then surfaced the decisive constraint: the nonprofit public dataset is bounded (~1.7M US 501c3 orgs, will not grow materially) and demanded no rework, thorough thinking, and sustainability.
- Context: The workload is bounded, read-heavy, write-once-nightly, with no server-side per-user state (Wallet is localStorage by design). This is the canonical baked-data case: compute offline, serve static artifacts. The existing architecture (home server bakes precompute + SQLite search.db nightly → lean droplet serves them) is already correct and was hardened by three incidents (INC-001/002/003).
- Sources: Founder directive ("no rework / bounded dataset / think thoroughly"), STANDING_CONSTRAINTS_2026_07.md, INCIDENTS_2026_07.md, project_canonical_org_count memory (1.7M active 501c3).
- Options considered: (a) proceed with Postgres migration per DR-007; (b) harden the existing baked-data architecture with CDN, snapshots, external monitoring, and two free fixes.
- Board simulation summary: Continuity and finance strongly favored (b) — the Postgres migration was the largest rework risk in the plan and solved a scaling problem that cannot occur. Technology confirmed SQLite excels at bounded read-heavy datasets. Mission favored (b): ~$35–50/mo total run cost is sustainable indefinitely on zero revenue, the strongest longevity guarantee.
- Stewardship principles applied: P1 (mission/sustainability before growth theater), P9 (explainable reversal, logged before execution), no-rework directive honored structurally.
- Decision: Cancel Postgres/Redis/Elasticsearch path entirely. Execute instead: (1) SQLite WAL + test-isolation fix on home server (free — kills the pytest database lock), (2) passphrase-free automation SSH key (free — fixes nightly droplet sync), (3) S3 + CloudFront in front of precompute (~$10–15/mo), (4) DigitalOcean droplet snapshots (~$3/mo), (5) external real-page uptime monitoring ($0–10/mo). Postgres is re-considered only if server-side accounts or high-volume writes ever become real requirements; the CDN/static layer built now carries over unchanged in that case.
- Decision owner: Founder (Akbar Khowaja, "Do the best you can"), AI Steward (autonomous execution).
- Expected outcome: Every known infrastructure weakness closed at ~$15–30/mo incremental; zero migration risk; architecture locked in correctly before users arrive.
- Risks accepted: FTS5 search quality ceiling (acceptable at this corpus size; embeddings/synonyms improvements run free on home GPU). Single droplet remains for the query API (mitigated by CDN absorbing page traffic and snapshots enabling fast rebuild).
- Review trigger: Server-side user accounts, high-volume org-claim writes, or sustained traffic the droplet cannot serve.
- Actual outcome: Pending (execution started 2026-07-12).
- Lessons: A single domain fact (bounded dataset) can invalidate an entire infrastructure plan; surface load-bearing constraints before provisioning, not after.
- Superseding decision: None.

