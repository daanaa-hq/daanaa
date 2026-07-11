# Institution Directory

## Document Control

| Field | Value |
|---|---|
| Purpose | Map the institutional stewardship, governance, memory, risk, budget, funding, user-insight, and continuity files. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Directory index; does not override `CONSTITUTION.md`. |
| Review trigger | Any file added, retired, or promoted to operating policy. |
| Editable status | Editable by ordinary agents. |
| Dependencies | Root `AGENTS.md`, `CLAUDE.md`, `STEWARDSHIP.md`, `PRIVACY-INVARIANTS.md`. |
| Retirement condition | Retire only if the institutional memory system moves to a maintained database or successor directory. |

## Files

- `PURPOSE.md` - mission and identity.
- `COVENANT.md` - universal stewardship commitments.
- `CONSTITUTION.md` - protected rules and authority boundaries.
- `AUTHORITY.md` - explicit order of authority and conflict-handling rule.
- `STEWARDSHIP.md` - operating loop, evidence ladder, and decision review.
- `GOVERNANCE.md` - decision tiers, board simulation, and approval gates.
- `CURRENT_STATE.md` - repository and platform discovery state as of 2026-07-10.
- `state.json` - machine-readable operating state for the current loop.
- `FOUNDER_REQUESTS.md` - structured founder input queue.
- `HYPOTHESES.md` - assumption registry.
- `DECISION_LOG.md` - durable institutional decision records.
- `RISK_REGISTER.md` - mission, security, privacy, reliability, cost, and continuity risks.
- `BUDGET_STATE.md` - known and unknown cost state.
- `FUNDING_PIPELINE.md` - funding opportunities and verification status.
- `USER_INSIGHTS.md` - user-signal and friction register.
- `CONTINUOUS_IMPROVEMENT.md` - improvement loop and retrospective triggers.
- `SUCCESSION.md` - founder-dependence reduction and continuity.
- `skills/INVENTORY.md` - proposed skill inventory and current minimum skill set.
- `skills/` - minimum reusable stewardship skill specifications.
- `HANDOFF_PROTOCOL.md` - durable Claude Code-Codex coordination rules.
- `tasks/` - durable task ownership and handoff records stored in-repo.
- `reviews/` - generated weekly institutional reviews.
- `briefs/` - generated founder briefs.

## Manual Review Command

Run the first operating loop manually:

```bash
python3 scripts/institution_weekly_review.py
```

Do not schedule it until at least two manual runs produce useful, accurate briefs without creating founder burden.

## Protected And Operational Files

Protected governing files:

- `PURPOSE.md`
- `COVENANT.md`
- `CONSTITUTION.md`

Operational files editable by ordinary agents within authority limits:

- `AUTHORITY.md`
- `CURRENT_STATE.md`
- `state.json`
- `FOUNDER_REQUESTS.md`
- `HYPOTHESES.md`
- `DECISION_LOG.md`
- `RISK_REGISTER.md`
- `BUDGET_STATE.md`
- `FUNDING_PIPELINE.md`
- `USER_INSIGHTS.md`
- `CONTINUOUS_IMPROVEMENT.md`
- `HANDOFF_PROTOCOL.md`
- `tasks/`
- `skills/`
