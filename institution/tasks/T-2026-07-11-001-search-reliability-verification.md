# T-2026-07-11-001 Search Reliability Verification

## Document Control

| Field | Value |
|---|---|
| Purpose | Record ownership, scope, validation, and handoff for the next stewardship-loop constraint. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Task record subordinate to `HANDOFF_PROTOCOL.md` and `AUTHORITY.md`. |
| Review trigger | Search schema-drift verification completed, disproven, or reprioritized. |
| Editable status | Editable by ordinary agents with append-only history for material updates. |
| Dependencies | `institution/HANDOFF_PROTOCOL.md`, `institution/RISK_REGISTER.md`, `institution/reviews/2026-07-11-weekly-review.md`. |
| Retirement condition | Retire when the search reliability risk is closed or absorbed into a broader product task. |

- Identifier: T-2026-07-11-001
- Date opened: 2026-07-11
- Owner: Codex stewardship layer
- Scope: Verify whether recent `/api/search` schema-drift errors still reproduce on the current backend and add targeted regression coverage if they do.
- Affected paths: `daanaa_api.py`, `tests/`, `institution/RISK_REGISTER.md`, `institution/reviews/`
- Higher-authority constraints checked: preserve product behavior; no spending; no deployment; no protected-principle change.
- Status: proposed
- Validation plan: reproduce or falsify the logged `/api/search` failure locally, add or update a regression test, run the targeted backend tests, then update `RISK_REGISTER.md` and the next weekly review evidence.
- Review notes: 2026-07-11 manual review promoted R-013 above founder-only operational unknowns because recent sampled logs still show `/api/search` exceptions on `v4.peer_cell_size`.
- Handoff target: Claude Code or product engineering owner for backend verification and test coverage.
- Merge or close-out note: do not close R-013 on inference alone; either prove the log evidence is stale or add the regression guard that blocks recurrence.
